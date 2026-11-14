// Own settings space with verified migration. The legacy file is only ever COPIED (never modified or deleted).
const fs = require('fs'); const path = require('path');
const DEFAULTS = { roots: [], favorites: [], recent: [], vol: 80, dens: 45, hover: false, pin: true, pinScope: 'resolve', warn: 10, locale: undefined, pythonPath: undefined };
const SCHEMA = 1;
function sanitize(raw) {
  const o = {}; const r = raw && typeof raw === 'object' ? raw : {};
  const arr = (v) => (Array.isArray(v) ? v.filter((x) => typeof x === 'string').slice(0, 5000) : []);
  o.roots = arr(r.roots); o.favorites = arr(r.favorites); o.recent = arr(r.recent).slice(0, 60);
  const num = (v, d, a, b) => (Number.isFinite(v) ? Math.max(a, Math.min(b, v)) : d);
  o.vol = num(r.vol, 80, 0, 100); o.dens = num(r.dens, 45, 0, 100); o.warn = num(r.warn, 10, 1, 600);
  o.hover = r.hover === true; o.pin = r.pin !== false; o.pinScope = r.pinScope === 'all' ? 'all' : 'resolve';
  if (['en', 'ro', 'es'].includes(r.locale)) o.locale = r.locale;
  if (typeof r.pythonPath === 'string' && r.pythonPath) o.pythonPath = r.pythonPath;
  o.schema = SCHEMA; return o;
}
function read(file) { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; } }
/** Returns {migrated, from, reason}. Never throws. */
function migrate(userDir, legacyFiles) {
  const cfg = path.join(userDir, 'settings.json');
  try {
    fs.mkdirSync(userDir, { recursive: true });
    const cur = read(cfg);
    if (cur) { if (cur.schema !== SCHEMA) fs.writeFileSync(cfg, JSON.stringify(sanitize(cur))); return { migrated: false, reason: cur.schema === SCHEMA ? 'current' : 'upgraded' }; }
    for (const lf of legacyFiles) {
      if (!fs.existsSync(lf)) continue; const old = read(lf);
      if (!old) return { migrated: false, reason: 'legacy-unreadable', from: lf };
      const next = sanitize(old); const tmp = cfg + '.tmp'; fs.writeFileSync(tmp, JSON.stringify(next));
      if (JSON.stringify(read(tmp)) !== JSON.stringify(next)) { fs.rmSync(tmp, { force: true }); return { migrated: false, reason: 'verify-failed', from: lf }; }
      fs.renameSync(tmp, cfg); return { migrated: true, from: lf };
    }
    return { migrated: false, reason: 'none' };
  } catch (e) { return { migrated: false, reason: 'error:' + e.code }; }
}
module.exports = { DEFAULTS, SCHEMA, sanitize, migrate, read };
