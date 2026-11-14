// Local diagnostic log (~/Library/Logs/SoundSFXPaste.log). Same format as bridge/log.py. No secrets, no file contents.
const fs = require('fs'); const os = require('os'); const path = require('path');
const MAX = 5 * 1024 * 1024;
const file = () => process.env.SSFX_LOG || path.join(os.homedir(), 'Library', 'Logs', 'SoundSFXPaste.log');
function write(level, cat, msg) {
  const p = file();
  try {
    fs.mkdirSync(path.dirname(p), { recursive: true });
    if (fs.existsSync(p) && fs.statSync(p).size > MAX) fs.renameSync(p, p + '.1');
    const d = new Date(), z = (n) => String(n).padStart(2, '0');
    const ts = `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())} ${z(d.getHours())}:${z(d.getMinutes())}:${z(d.getSeconds())}`;
    fs.appendFileSync(p, `${ts} ${level} [${cat}] ${String(msg).replace(/\s+/g, ' ').slice(0, 400)}\n`);
  } catch { /* logging must never break the panel */ }
}
module.exports = { write, file };
