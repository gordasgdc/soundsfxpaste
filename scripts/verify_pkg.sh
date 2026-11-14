#!/bin/bash
# Gate for the publishable package: expands it and checks version, no test/simulation switches, RO/EN/ES messages, no private paths.
# Usage: scripts/verify_pkg.sh <pkg> <version>
set -euo pipefail
PKG="$1"; VER="$2"; T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
pkgutil --expand-full "$PKG" "$T/x" >/dev/null
P="$(find "$T/x" -type d -name SoundSFXPaste | head -1)"; fail=0
chk() { if eval "$2"; then echo "  OK   $1"; else echo "  FAIL $1"; fail=1; fi; }
chk "version $VER in package.json and manifest.xml" "grep -q '\"version\": \"$VER\"' '$P/package.json' && grep -q '<Version>$VER</Version>' '$P/manifest.xml'"
chk "no SSFX_SIM_REFUSE / SSFX_ALLOW_TEST / SSFX_UPDATE_URL anywhere in payload" "! grep -rIq -e SSFX_SIM_REFUSE -e SSFX_ALLOW_TEST -e SSFX_UPDATE_URL '$P'"
chk "RO message" "grep -q 'Resolve nu a plasat sunetul. Verifică pista și poziția din panou, apoi încearcă din nou.' '$P/i18n.js'"
chk "EN message" "grep -q 'Resolve did not place the sound. Check the track and position in the panel, then try again.' '$P/i18n.js'"
chk "ES message" "grep -q 'Resolve no colocó el sonido. Revisa la pista y la posición en el panel, y vuelve a intentarlo.' '$P/i18n.js'"
chk "credit line in 3 languages" "[ \$(grep -c 'Dumitru Cristinel Gordas (GDC)' '$P/i18n.js') -ge 3 ]"
chk "LICENSE and NOTICE shipped" "[ -f '$P/LICENSE' ] && [ -f '$P/NOTICE.md' ]"
chk "no private paths or user names" "! grep -rIq -e /Users/ -e gordasgdc '$P'"
chk "no __pycache__, no node binaries" "[ -z \"\$(find '$P' -name __pycache__ -o -name '*.node')\" ]"
exit $fail
