#!/bin/bash
# Isolated install of SoundSFXPaste as a Resolve Workflow Integration plugin. Never touches other plugin folders (e.g. an old panel).
# Usage: scripts/install_mac.sh [--uninstall]
set -euo pipefail
DEST="${SSFX_PLUGINS_DIR:-/Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins}/SoundSFXPaste"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
[ "${1:-}" = "--uninstall" ] && { rm -rf "$DEST"; echo "removed $DEST"; exit 0; }
mkdir -p "$DEST/bridge"
rsync -rlD --delete --exclude node_modules --exclude bridge "$HERE/app/" "$DEST/"
rsync -rlD --delete --exclude __pycache__ "$HERE/bridge/" "$DEST/bridge/"
echo "installed -> $DEST"; echo "Enable: Resolve > Preferences > General > External scripting using: Local; then Workspace > Workflow Integrations > SoundSFXPaste"
