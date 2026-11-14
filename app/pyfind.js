// Find a working Python 3. Never executes the macOS /usr/bin/python3 stub unless the Command Line Tools exist
// (running the stub pops an installer dialog). `deps` is injectable for tests.
const fs = require('fs'); const { spawnSync } = require('child_process');
const real = {
  exists: (p) => fs.existsSync(p),
  version: (exe) => { const r = spawnSync(exe, ['-c', "import sys;print('%d.%d.%d'%sys.version_info[:3])"], { timeout: 5000, encoding: 'utf8' }); return r.status === 0 ? r.stdout.trim() : null; },
  cltOk: () => spawnSync('/usr/bin/xcode-select', ['-p'], { timeout: 3000 }).status === 0
};
const MIN = [3, 8];
const okVer = (v) => { const [a, b] = v.split('.').map(Number); return a > MIN[0] || (a === MIN[0] && b >= MIN[1]); };
function findPython({ configured, env = process.env, deps = real } = {}) {
  if (configured) {
    if (!deps.exists(configured)) return { error: 'ERR_PYTHON_PATH', tried: configured };
    const v = deps.version(configured); return v && okVer(v) ? { path: configured, version: v } : { error: 'ERR_PYTHON_PATH', tried: configured, version: v };
  }
  const cands = [env.SSFX_PYTHON, '/Library/Frameworks/Python.framework/Versions/Current/bin/python3', '/opt/homebrew/bin/python3', '/usr/local/bin/python3'];
  if (deps.cltOk()) cands.push('/usr/bin/python3');
  for (const c of cands.filter(Boolean)) { if (!deps.exists(c)) continue; const v = deps.version(c); if (v && okVer(v)) return { path: c, version: v }; }
  return { error: 'ERR_NO_PYTHON' };
}
module.exports = { findPython, okVer };
