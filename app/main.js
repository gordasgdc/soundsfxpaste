// SoundSFXPaste — Electron main. Sandboxed renderer, context isolation, no nodeIntegration.
const { app, BrowserWindow, ipcMain, dialog, nativeImage, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { spawn, spawnSync } = require('child_process');
const diag = require('./diag'); const settings = require('./settings'); const { findPython } = require('./pyfind');
const updater = require('./updater'); const uninstall = require('./uninstall');
const VERSION = require('./package.json').version;

// Own settings space (never the shared "Electron" folder). Must run before 'ready'.
app.setName('SoundSFXPaste');
const USER_DIR = path.join(app.getPath('appData'), 'SoundSFXPaste');
app.setPath('userData', USER_DIR);
const CFG = path.join(USER_DIR, 'settings.json');
const LEGACY = path.join(app.getPath('appData'), 'Electron', 'soundsfxpaste.json');

function migrate() {
  const r = settings.migrate(USER_DIR, [LEGACY]);
  diag.write('INFO', 'settings', `migrate ${JSON.stringify(r)}`);
}
const loadCfg = () => settings.read(CFG) || {};
const saveCfg = (c) => { try { fs.mkdirSync(USER_DIR, { recursive: true }); fs.writeFileSync(CFG + '.tmp', JSON.stringify(c)); fs.renameSync(CFG + '.tmp', CFG); } catch (e) { diag.write('ERROR', 'settings', 'save ' + e.code); } };

const token = crypto.randomBytes(24).toString('base64url');
let py = null, bridgePort = null, win = null;
const BRIDGE = [path.join(__dirname, 'bridge', 'server.py'), path.join(__dirname, '..', 'bridge', 'server.py')].find((p) => fs.existsSync(p));

function startBridge(exe) {
  return new Promise((resolve, reject) => {
    py = spawn(exe, [BRIDGE, '0'], { env: { ...process.env, SSFX_TOKEN: token } });
    let buf = '';
    py.stdout.on('data', (d) => { buf += d; const m = buf.match(/\{"port": (\d+)\}/); if (m && !bridgePort) { bridgePort = Number(m[1]); resolve(bridgePort); } });
    py.stderr.on('data', (d) => diag.write('ERROR', 'bridge-stderr', String(d)));
    py.on('error', (e) => reject(new Error('ERR_PYTHON_PATH')));
    py.on('exit', () => { py = null; if (!bridgePort) reject(new Error('ERR_BRIDGE_EXIT')); });
    setTimeout(() => !bridgePort && reject(new Error('ERR_BRIDGE_TIMEOUT')), 8000);
  });
}

ipcMain.handle('ssfx:init', async () => {
  const cfg = loadCfg(); const base = { cfg, locale: cfg.locale || app.getLocale().slice(0, 2), settingsDir: USER_DIR, version: VERSION, logFile: diag.file() };
  if (!bridgePort) {
    const p = findPython({ configured: cfg.pythonPath });
    if (p.error) { diag.write('ERROR', 'python', `${p.error} tried=${p.tried || '-'} ver=${p.version || '-'}`); return { ...base, error: p.error, pyTried: p.tried }; }
    base.python = p;
    try { await startBridge(p.path); diag.write('INFO', 'python', `bridge up python=${p.version}`); } catch (e) { diag.write('ERROR', 'bridge', String(e.message || e)); return { ...base, error: String(e.message || e) }; }
  }
  return { ...base, port: bridgePort, token };
});
ipcMain.handle('ssfx:chooseFolder', async () => {
  const r = await dialog.showOpenDialog(win, { properties: ['openDirectory'] });
  return r.canceled ? null : r.filePaths[0];
});
ipcMain.handle('ssfx:version', () => VERSION);
ipcMain.on('ssfx:log', (_e, level, cat, msg) => diag.write(String(level).slice(0, 5), String(cat).slice(0, 20), msg));
ipcMain.handle('ssfx:openLog', () => { shell.showItemInFolder(diag.file()); return true; });
ipcMain.handle('ssfx:update:check', async () => { const r = await updater.check(VERSION); diag.write(r.state === 'error' ? 'WARN' : 'INFO', 'update', `${r.state} ${r.reason || ''}`); return r; });
ipcMain.handle('ssfx:update:install', async (_e, info) => { const r = await updater.install(info); diag.write(r.ok ? 'INFO' : 'ERROR', 'update', `install ok=${r.ok} ${r.reason || ''}`); return r; });
ipcMain.handle('ssfx:uninstall', async () => {
  const gone = uninstall.removeData(); diag.write('INFO', 'uninstall', `data removed ${gone.length}`);
  const sh = `rm -rf ${JSON.stringify(__dirname)}`;
  const r = spawnSync('/usr/bin/osascript', ['-e', `do shell script ${JSON.stringify(sh)} with administrator privileges`], { encoding: 'utf8', timeout: 120000 });
  setTimeout(() => app.quit(), 300); return { ok: r.status === 0, dataRemoved: gone.length };
});
ipcMain.handle('ssfx:saveCfg', (_e, patch) => { saveCfg({ ...loadCfg(), ...patch }); return true; });

// Native file drag from a card to the Resolve timeline/media pool. Only files inside the user's library folders.
const ICON = nativeImage.createFromDataURL('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAMUlEQVR42mP8z8BQz0AEYBxVSF+FjP8ZGP4TUsiIqpAYK0YVMhCpkIFYhQzEKmQgViEARQ4gEeWCLmYAAAAASUVORK5CYII=');
ipcMain.on('ssfx:drag', (e, file) => {
  const roots = (loadCfg().roots || []).map((r) => fs.realpathSync(r));
  let real; try { real = fs.realpathSync(file); } catch { return; }
  if (roots.some((r) => real === r || real.startsWith(r + path.sep))) e.sender.startDrag({ file: real, icon: ICON });
});

let pinCtl = null; const pin = require('./pin');
ipcMain.handle('ssfx:pin', (_e, on) => { const c = loadCfg(); saveCfg({ ...c, pin: !!on }); if (pinCtl) pinCtl.set(!!on, c.pinScope); diag.write('INFO', 'pin', `user pin=${!!on}`); return !!on; });
function createWindow() {
  migrate();
  win = new BrowserWindow({
    width: 1040, height: 740, minWidth: 380, minHeight: 480, backgroundColor: '#060b19', title: 'SoundSFXPaste',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), sandbox: true, contextIsolation: true, nodeIntegration: false }
  });
  pinCtl = pin.controller(win, { log: diag.write }); const c0 = loadCfg(); pinCtl.set(c0.pin !== false, c0.pinScope);
  win.on('close', () => { pinCtl.stop(); app.quit(); });
  win.loadFile('index.html');
}
app.on('ready', () => { diag.write('INFO', 'app', `start v${VERSION} electron=${process.versions.electron}`); createWindow(); });
app.on('will-quit', () => { if (py) { py.kill(); py = null; } });
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
