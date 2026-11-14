#!/bin/bash
# Public-tree gate: no old identifiers, personal paths, keys or private library names. Usage: scripts/scan_public.sh [dir]
D="${1:-$(cd "$(dirname "$0")/.." && pwd)}"; bad=0
pat='s[i]ck|/Users/|/Volumes/|5\. Sound|BEGIN PRIVATE KEY-----|Co-Authored-By'
hits=$(grep -rIniE "$pat" --exclude-dir=.git --exclude-dir=node_modules --exclude=scan_public.sh --exclude=PROJECT_STATE.md --exclude=PLAN_PUBLICARE.md "$D" | grep -v "grep -rIq" || true)
[ -n "$hits" ] && { echo "$hits" | cut -c1-200; bad=1; }
find "$D" \( -name '*.pem' -o -name '*.p12' -o -name '*.p8' -o -name '*.key' -o -name '__pycache__' -o -name '.DS_Store' \) -not -path '*/.git/*' | grep . && bad=1
[ $bad = 0 ] && echo "SCAN OK" || { echo "SCAN FAILED"; exit 1; }
