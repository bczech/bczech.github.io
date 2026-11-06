#!/usr/bin/env bash
# Render assets/og-card.html to img/og-card.png (1200x630) with headless Chrome.
# Run from portfolio/:  bash scripts/make_og_card.sh
set -euo pipefail
cd "$(dirname "$0")/.."
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --force-device-scale-factor=1 --window-size=1200,630 --virtual-time-budget=4000 \
  --screenshot="$PWD/img/og-card.png" "file://$PWD/assets/og-card.html" 2>/dev/null
echo "wrote img/og-card.png"
