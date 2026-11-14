#!/bin/bash
# Builds, signs (Developer ID Installer), notarizes and staples SoundSFXPaste-<version>.pkg.
# Usage: scripts/build_pkg.sh [--no-notarize]. Output dir: $SSFX_DIST (default: ./dist).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
VER="$(node -p "require('$HERE/app/package.json').version")"
DIST="${SSFX_DIST:-$(cd "$(dirname "$0")/.." && pwd)/dist}"
mkdir -p "$DIST"
ID="Developer ID Installer: DUMITRU CRISTINEL GORDAS (8AR6XP8MG7)"
PROFILE="${SSFX_NOTARY_PROFILE:-gdc-notary}"
STAGE="$DIST/stage-$VER"; PLUG="Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins/SoundSFXPaste"
mkdir -p "$DIST"; rm -rf "$STAGE"; mkdir -p "$STAGE/root/$PLUG/bridge" "$STAGE/scripts"
rsync -a --exclude node_modules "$HERE/app/" "$STAGE/root/$PLUG/"
rsync -a --exclude __pycache__ "$HERE/bridge/" "$STAGE/root/$PLUG/bridge/"
cp "$HERE/LICENSE" "$HERE/NOTICE.md" "$STAGE/root/$PLUG/"
# keep the previous package for rollback
for old in "$DIST"/SoundSFXPaste-*.pkg; do [ -e "$old" ] && [ "$old" != "$DIST/SoundSFXPaste-$VER.pkg" ] && mkdir -p "$DIST/previous" && mv "$old" "$DIST/previous/"; done || true
pkgbuild --root "$STAGE/root" --identifier com.gordas.soundsfxpaste.pkg --version "$VER" --install-location "/" "$STAGE/component.pkg" >/dev/null
cat > "$STAGE/dist.xml" <<XML
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
  <title>SoundSFXPaste $VER</title>
  <license file="license.txt" mime-type="text/plain"/>
  <options customize="never" require-scripts="false" hostArchitectures="arm64,x86_64"/>
  <domains enable_anywhere="false" enable_localSystem="true"/>
  <choices-outline><line choice="default"/></choices-outline>
  <choice id="default" title="SoundSFXPaste"><pkg-ref id="com.gordas.soundsfxpaste.pkg"/></choice>
  <pkg-ref id="com.gordas.soundsfxpaste.pkg" version="$VER">component.pkg</pkg-ref>
</installer-gui-script>
XML
mkdir -p "$STAGE/res"; cp "$HERE/LICENSE" "$STAGE/res/license.txt"
OUT="$DIST/SoundSFXPaste-$VER.pkg"; rm -f "$OUT"
productbuild --distribution "$STAGE/dist.xml" --resources "$STAGE/res" --package-path "$STAGE" --sign "$ID" "$OUT" >/dev/null
"$HERE/scripts/verify_pkg.sh" "$OUT" "$VER"
pkgutil --check-signature "$OUT" | sed -n 1,6p
if [ "${1:-}" != "--no-notarize" ]; then
  xcrun notarytool submit "$OUT" --keychain-profile "$PROFILE" --wait | tee "$DIST/notary-$VER.log" | tail -6
  grep -q "status: Accepted" "$DIST/notary-$VER.log"
  xcrun stapler staple "$OUT" && xcrun stapler validate "$OUT"
  spctl -a -t install -vv "$OUT" 2>&1 | head -3
fi
shasum -a 256 "$OUT" | tee "$OUT.sha256"; echo "pkg: $OUT"
