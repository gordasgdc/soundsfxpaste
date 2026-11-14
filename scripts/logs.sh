#!/bin/bash
# Usage: scripts/logs.sh [--follow]   Shows ~/Library/Logs/SoundSFXPaste.log
LOG="$HOME/Library/Logs/SoundSFXPaste.log"
[ -f "$LOG" ] || { echo "no log yet: $LOG"; exit 0; }
if [ "${1:-}" = "--follow" ]; then tail -n 40 -f "$LOG"; else tail -n 80 "$LOG"; fi
