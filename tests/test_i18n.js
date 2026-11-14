// node tests/test_i18n.js  — RO/EN/ES key parity + placeholder parity
global.window = {}; const I = require('../app/i18n.js'); let bad = 0;
const ph = (s) => (s.match(/\{\w+\}/g) || []).sort().join();
for (const l of ['ro', 'es']) for (const k of Object.keys(I.en)) {
  if (!(k in I[l])) { console.log(`MISSING ${l}.${k}`); bad++; } else if (ph(I.en[k]) !== ph(I[l][k])) { console.log(`PLACEHOLDER ${l}.${k}`); bad++; }
}
for (const l of ['ro', 'es']) for (const k of Object.keys(I[l])) if (!(k in I.en)) { console.log(`EXTRA ${l}.${k}`); bad++; }
console.log(bad ? `FAIL ${bad}` : `OK ${Object.keys(I.en).length} keys x 3 languages`); process.exit(bad ? 1 : 0);
