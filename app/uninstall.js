// Native uninstall: user data (testable), then the plugin folder via the system admin prompt.
const fs = require('fs'); const path = require('path'); const os = require('os');
function dataPaths(home = os.homedir()) {
  const L = path.join(home, 'Library');
  return [path.join(L, 'Application Support', 'SoundSFXPaste'), path.join(L, 'Logs', 'SoundSFXPaste.log'), path.join(L, 'Logs', 'SoundSFXPaste.log.1'),
    path.join(L, 'Caches', 'SoundSFXPaste'), path.join(L, 'Saved Application State', 'com.gordas.soundsfxpaste.savedState'), path.join(L, 'HTTPStorages', 'SoundSFXPaste')];
}
function removeData(home) { const done = []; for (const p of dataPaths(home)) { try { if (fs.existsSync(p)) { fs.rmSync(p, { recursive: true, force: true }); done.push(p); } } catch { /* keep going */ } } return done; }
module.exports = { dataPaths, removeData };
