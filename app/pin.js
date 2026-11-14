// "Keep on top": the panel is a plain BrowserWindow we create ourselves, so alwaysOnTop is allowed by the host.
// scope 'all'     = floats above every app (global).
// scope 'resolve' = floats only while Resolve or this panel is the frontmost app; drops to normal level otherwise.
const { execFile } = require('child_process');
const HOST = new Set(['com.blackmagic-design.DaVinciResolve', 'com.blackmagic-design.DaVinciResolveStudio', 'com.blackmagic-design.DaVinciResolveLite']);
function wantTop(enabled, scope, front, self) {
  if (!enabled) return false;
  if (scope === 'all') return true;
  return !front || front === self || HOST.has(front); // unknown frontmost => keep floating (never hide the panel by mistake)
}
function frontBundle(run = execFile) {
  return new Promise((res) => run('/usr/bin/lsappinfo', ['front'], { timeout: 1500 }, (e, out) => {
    const asn = !e && /ASN:[0-9a-fx-]+:/.exec(String(out)); if (!asn) return res(null);
    run('/usr/bin/lsappinfo', ['info', '-only', 'bundleid', asn[0]], { timeout: 1500 }, (e2, o2) => { const m = !e2 && /"?bundleid"?="([^"]+)"/i.exec(String(o2)); res(m ? m[1] : null); });
  }));
}
function controller(win, { self = 'com.github.Electron', log = () => {}, poll = 500 } = {}) {
  let enabled = false, scope = 'resolve', timer = null, last = null;
  const apply = (top) => { if (top === last || win.isDestroyed()) return; last = top; win.setAlwaysOnTop(top, 'floating'); if (top) win.setVisibleOnAllWorkspaces(false); log('INFO', 'pin', `top=${top} scope=${scope}`); };
  const tick = async () => { apply(wantTop(enabled, scope, await frontBundle(), self)); };
  const sync = () => { clearInterval(timer); timer = null; if (!enabled) return apply(false); if (scope === 'all') return apply(true); tick(); timer = setInterval(tick, poll); };
  return { set(e, s) { enabled = !!e; scope = s === 'all' ? 'all' : 'resolve'; last = null; sync(); }, stop() { clearInterval(timer); } };
}
module.exports = { wantTop, frontBundle, controller, HOST };
