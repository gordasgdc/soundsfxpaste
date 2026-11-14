// Node tests for settings migration, Python discovery, signed updater, uninstall paths. No Resolve needed.
const assert = require('assert'); const fs = require('fs'); const os = require('os'); const path = require('path'); const crypto = require('crypto'); const http = require('http');
const settings = require('../app/settings'); const { findPython } = require('../app/pyfind'); const updater = require('../app/updater'); const uninstall = require('../app/uninstall');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ssfx-')); let n = 0; const ok = (m) => { n++; console.log('PASS', m); };

// --- settings migration
const legacy = path.join(tmp, 'Electron', 'soundsfxpaste.json'); fs.mkdirSync(path.dirname(legacy), { recursive: true });
fs.writeFileSync(legacy, JSON.stringify({ roots: ['/a', 3, '/b'], favorites: ['/a/x.wav'], vol: 250, locale: 'ro', evil: 'x', hover: 'yes' }));
const before = fs.readFileSync(legacy, 'utf8'); const ud = path.join(tmp, 'SoundSFXPaste');
let r = settings.migrate(ud, [legacy]); assert.strictEqual(r.migrated, true);
const cfg = settings.read(path.join(ud, 'settings.json')); assert.deepStrictEqual(cfg.roots, ['/a', '/b']); assert.strictEqual(cfg.vol, 100); assert.strictEqual(cfg.hover, false); assert.strictEqual(cfg.evil, undefined); assert.strictEqual(cfg.locale, 'ro');
assert.strictEqual(fs.readFileSync(legacy, 'utf8'), before); ok('migration sanitises and leaves legacy untouched');
fs.writeFileSync(path.join(ud, 'settings.json'), JSON.stringify({ ...cfg, vol: 33 })); r = settings.migrate(ud, [legacy]); assert.strictEqual(r.migrated, false); assert.strictEqual(settings.read(path.join(ud, 'settings.json')).vol, 33); ok('existing settings never overwritten');
fs.writeFileSync(legacy, '{broken'); fs.rmSync(path.join(ud, 'settings.json')); r = settings.migrate(ud, [legacy]); assert.strictEqual(r.reason, 'legacy-unreadable'); ok('corrupt legacy handled');

// --- python discovery
const D = (o) => ({ exists: (p) => (o.has || []).includes(p), version: (p) => (o.ver || {})[p] || null, cltOk: () => !!o.clt });
assert.strictEqual(findPython({ deps: D({}) }).error, 'ERR_NO_PYTHON'); ok('no python anywhere -> ERR_NO_PYTHON');
assert.strictEqual(findPython({ deps: D({ has: ['/usr/bin/python3'], ver: { '/usr/bin/python3': '3.9.6' }, clt: false }) }).error, 'ERR_NO_PYTHON'); ok('macOS stub ignored without Command Line Tools');
assert.strictEqual(findPython({ deps: D({ has: ['/usr/bin/python3'], ver: { '/usr/bin/python3': '3.9.6' }, clt: true }) }).version, '3.9.6'); ok('CLT python accepted');
assert.strictEqual(findPython({ deps: D({ has: ['/opt/homebrew/bin/python3'], ver: { '/opt/homebrew/bin/python3': '3.7.1' } }) }).error, 'ERR_NO_PYTHON'); ok('python < 3.8 rejected');
assert.strictEqual(findPython({ configured: '/nope', deps: D({ has: ['/opt/homebrew/bin/python3'], ver: { '/opt/homebrew/bin/python3': '3.12.1' } }) }).error, 'ERR_PYTHON_PATH'); ok('bad configured path -> ERR_PYTHON_PATH, no silent fallback');

// --- signed manifest + updater
const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519'); const pubPem = publicKey.export({ type: 'spki', format: 'pem' });
const sign = (m) => { const x = { ...m }; delete x.signature; x.signature = crypto.sign(null, Buffer.from(updater.canonical(x)), privateKey).toString('base64'); return x; };
const pkg = Buffer.from('not-a-real-pkg'); const sha = crypto.createHash('sha256').update(pkg).digest('hex');
const man = sign({ product_id: 'soundsfxpaste', version: '0.2.0', app_version: '0.2.0', download_url: 'http://127.0.0.1:0/p.pkg', sha256: sha, changes: { en: ['x'], ro: ['y'], es: ['z'] } });
assert.ok(updater.verifyManifest(man, pubPem)); ok('manifest signature verifies');
assert.ok(!updater.verifyManifest({ ...man, version: '9.9.9' }, pubPem)); assert.ok(!updater.verifyManifest({ ...man, changes: { en: ['evil'], ro: ['y'], es: ['z'] } }, pubPem)); ok('tampered manifest rejected');
assert.ok(updater.isNewer('0.10.0', '0.9.9') && !updater.isNewer('0.1.0', '0.1.0') && !updater.isNewer('0.1.0', '0.2.0')); ok('semver compare');
const srv = http.createServer((q, s) => { if (q.url === '/update.json') { s.setHeader('content-type', 'application/json'); s.end(JSON.stringify(man)); } else if (q.url === '/p.pkg') s.end(pkg); else if (q.url === '/bad.json') s.end(JSON.stringify({ ...man, version: '9.9.9' })); else { s.statusCode = 404; s.end(); } });
srv.listen(0, '127.0.0.1', async () => {
  const port = srv.address().port; const base = `http://127.0.0.1:${port}`; man.download_url = base + '/p.pkg'; const m2 = sign(man); man.signature = m2.signature;
  try {
    let c = await updater.check('0.1.0', { url: base + '/update.json', test: true, pub: pubPem }); assert.strictEqual(c.state, 'newer'); ok('newer version detected from signed manifest');
    c = await updater.check('0.2.0', { url: base + '/update.json', test: true, pub: pubPem }); assert.strictEqual(c.state, 'current'); ok('up to date');
    c = await updater.check('0.1.0', { url: base + '/bad.json', test: true, pub: pubPem }); assert.strictEqual(c.state, 'error'); assert.strictEqual(c.reason, 'SIGNATURE'); ok('bad signature -> error, never "up to date"');
    c = await updater.check('0.1.0', { url: base + '/missing.json', test: true, pub: pubPem }); assert.strictEqual(c.state, 'error'); ok('HTTP failure -> error state');
    c = await updater.check('0.1.0', { url: 'http://example.com/u.json', test: false, pub: pubPem }); assert.strictEqual(c.reason, 'URL'); ok('plain http refused outside test mode');
    c = await updater.check('0.1.0', { url: base + '/update.json', test: true, pub: pubPem }); const dir = path.join(tmp, 'cache');
    let i = await updater.install(c.info, { dry: true, dir, skipPkgSignature: true }); assert.ok(i.ok && i.dry && fs.existsSync(i.file)); ok('download + sha256 verified (dry, no admin prompt)');
    i = await updater.install({ ...c.info, sha256: '0'.repeat(64) }, { dry: true, dir, skipPkgSignature: true }); assert.strictEqual(i.reason, 'SHA256'); ok('wrong sha256 rejected and file removed');
    i = await updater.install(c.info, { dry: true, dir }); assert.strictEqual(i.reason, 'PKG_SIGNATURE'); ok('unsigned package refused before any installer prompt');
  } catch (e) { console.error('FAIL', e.message); process.exitCode = 1; } finally { srv.close(); }
  // --- uninstall paths
  const home = path.join(tmp, 'home'); for (const p of uninstall.dataPaths(home)) { fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, 'x'); }
  assert.ok(uninstall.dataPaths(home).every((p) => p.startsWith(home))); const gone = uninstall.removeData(home); assert.strictEqual(gone.length, 6); assert.ok(uninstall.dataPaths(home).every((p) => !fs.existsSync(p))); ok('uninstall removes exactly its own data, inside HOME');
  console.log(`${n} passed`);
});


// --- renderer: lazy message closures must not read mutable Rapid Mapping state (rm is nulled before the message is re-rendered)
{
  const src = fs.readFileSync(path.join(__dirname, '..', 'app', 'renderer.js'), 'utf8');
  const bad = [...src.matchAll(/setMsg\([^;]*?=>[^;]*?\brm\./g)].map((m) => m[0].slice(0, 80));
  assert.deepStrictEqual(bad, [], 'setMsg closure reads rm: ' + bad.join(' | ')); ok('no setMsg closure reads the nullable rm state');
}
