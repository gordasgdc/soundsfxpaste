#!/bin/bash
# Run AFTER publication (needs the public URLs). Usage: scripts/verify_live_update.sh <version>
set -euo pipefail
VER="${1:?version}"
URL="$(grep -o "DEFAULT_URL = '[^']*'" "$(dirname "$0")/../app/updater.js" | cut -d"'" -f2)"
VERIFIER="${SSFX_VERIFY_TOOL:?set SSFX_VERIFY_TOOL to your update-flow verifier script}"
exec "$VERIFIER" "$URL" "$VER" \
  "https://github.com/gordasgdc/soundsfxpaste/releases/download/v$VER/SoundSFXPaste-$VER.pkg" \
  "https://gordas.dev/soundsfxpaste/"
