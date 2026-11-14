
// ---- pin.js
{
  const { wantTop } = require('../app/pin'); const R = 'com.blackmagic-design.DaVinciResolve', S = 'com.github.Electron';
  const t = (n, c) => { if (!c) { console.error('FAIL ' + n); process.exitCode = 1; } else console.log('PASS ' + n); };
  t('pin off never floats', wantTop(false, 'all', R, S) === false);
  t('scope all floats over other apps', wantTop(true, 'all', 'com.apple.Safari', S) === true);
  t('scope resolve floats over Resolve', wantTop(true, 'resolve', R, S) === true);
  t('scope resolve floats when panel is front', wantTop(true, 'resolve', S, S) === true);
  t('scope resolve drops for other apps', wantTop(true, 'resolve', 'com.apple.Safari', S) === false);
  t('unknown frontmost keeps floating', wantTop(true, 'resolve', null, S) === true);
}
