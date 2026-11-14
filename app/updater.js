// Signed-manifest updater. Manifest is verified (Ed25519) BEFORE anything is downloaded; the package is verified
// (sha256 + Developer ID Installer signature, Team ID) BEFORE the system installer prompt. Never opens a browser.
const crypto = require('crypto'); const fs = require('fs'); const path = require('path'); const os = require('os');
const { spawnSync } = require('child_process');
const PRODUCT = 'soundsfxpaste'; const TEAM = '8AR6XP8MG7';
const PUB = `-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEAaKy6wf4FZsEBlY+aFp/B2HtJTJvke3WCY6oDS3pydz4=\n-----END PUBLIC KEY-----\n`;
const DEFAULT_URL = 'https://gordas.dev/soundsfxpaste/update.json';
const sortDeep = (v) => (Array.isArray(v) ? v.map(sortDeep) : v && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map((k) => [k, sortDeep(v[k])])) : v);
const canonical = (m) => { const { signature, ...rest } = m; return JSON.stringify(sortDeep(rest)); };
function verifyManifest(m, pub = PUB) { try { return crypto.verify(null, Buffer.from(canonical(m)), pub, Buffer.from(String(m.signature || ''), 'base64')); } catch { return false; } }
function isNewer(a, b) { const p = (v) => String(v).split('.').map((n) => parseInt(n, 10) || 0); const x = p(a), y = p(b); for (let i = 0; i < 3; i++) { if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) > (y[i] || 0); } return false; }
const allowedUrl = (u, test) => /^https:\/\//.test(u) || (test && /^http:\/\/127\.0\.0\.1[:/]/.test(u));
/** state: newer | current | error. "could not verify" is NEVER reported as "up to date". */
async function check(current, { url, test = false, pub = PUB, fetchFn = fetch } = {}) {
  const u = url || DEFAULT_URL; if (!allowedUrl(u, test)) return { state: 'error', reason: 'URL' };
  let m; try { const ctl = new AbortController(); const t = setTimeout(() => ctl.abort(), 8000); const r = await fetchFn(u, { signal: ctl.signal, cache: 'no-store' }); clearTimeout(t); if (!r.ok) return { state: 'error', reason: 'HTTP ' + r.status }; m = await r.json(); } catch (e) { return { state: 'error', reason: 'NETWORK' }; }
  if (!verifyManifest(m, pub)) return { state: 'error', reason: 'SIGNATURE' };
  if (m.product_id !== PRODUCT || !allowedUrl(m.download_url || '', test) || !/^[0-9a-f]{64}$/.test(m.sha256 || '')) return { state: 'error', reason: 'MANIFEST' };
  const v = m.app_version || m.version; return isNewer(v, current) ? { state: 'newer', info: m } : { state: 'current', info: m };
}
function pkgSignatureOk(pkg, run = spawnSync) {
  const r = run('/usr/sbin/pkgutil', ['--check-signature', pkg], { encoding: 'utf8', timeout: 20000 }); const o = (r.stdout || '') + (r.stderr || '');
  return r.status === 0 && /Developer ID Installer/.test(o) && o.includes(`(${TEAM})`);
}
async function download(info, { dir = path.join(os.homedir(), 'Library', 'Caches', 'SoundSFXPaste'), fetchFn = fetch } = {}) {
  fs.mkdirSync(dir, { recursive: true }); const out = path.join(dir, `SoundSFXPaste-${info.app_version || info.version}.pkg`);
  const r = await fetchFn(info.download_url); if (!r.ok) return { ok: false, reason: 'HTTP ' + r.status };
  const buf = Buffer.from(await r.arrayBuffer()); fs.writeFileSync(out, buf);
  if (crypto.createHash('sha256').update(buf).digest('hex') !== info.sha256) { fs.rmSync(out, { force: true }); return { ok: false, reason: 'SHA256' }; }
  return { ok: true, file: out };
}
/** dry=true stops before the admin prompt (used by tests). */
async function install(info, { dry = false, ...o } = {}) {
  const d = await download(info, o); if (!d.ok) return d;
  if (!o.skipPkgSignature && !pkgSignatureOk(d.file)) { fs.rmSync(d.file, { force: true }); return { ok: false, reason: 'PKG_SIGNATURE' }; }
  if (dry) return { ok: true, file: d.file, dry: true };
  const sh = `/usr/sbin/installer -pkg ${JSON.stringify(d.file)} -target /`;
  const r = spawnSync('/usr/bin/osascript', ['-e', `do shell script ${JSON.stringify(sh)} with administrator privileges`], { encoding: 'utf8', timeout: 300000 });
  return r.status === 0 ? { ok: true, file: d.file } : { ok: false, reason: 'INSTALLER' };
}
module.exports = { check, install, download, verifyManifest, canonical, isNewer, pkgSignatureOk, DEFAULT_URL };
