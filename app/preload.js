const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('ssfx', {
  init: () => ipcRenderer.invoke('ssfx:init'),
  chooseFolder: () => ipcRenderer.invoke('ssfx:chooseFolder'),
  saveCfg: (p) => ipcRenderer.invoke('ssfx:saveCfg', p),
  version: () => ipcRenderer.invoke('ssfx:version'),
  log: (l, c, m) => ipcRenderer.send('ssfx:log', l, c, m),
  openLog: () => ipcRenderer.invoke('ssfx:openLog'),
  checkUpdate: () => ipcRenderer.invoke('ssfx:update:check'),
  installUpdate: (info) => ipcRenderer.invoke('ssfx:update:install', info),
  pin: (on) => ipcRenderer.invoke('ssfx:pin', on),
  uninstall: () => ipcRenderer.invoke('ssfx:uninstall'),
  startDrag: (file) => ipcRenderer.send('ssfx:drag', file)
});
