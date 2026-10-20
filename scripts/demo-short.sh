#!/usr/bin/env bash
# Demo-Short 9:16 aus dem echten Panel: Aufnahme (demo.record.mjs --clicks) → Montage
# (Remotion, chemdraw_tool/ui/video) → <out>/chemdraw-short.mp4 (1080×1920, 30 fps, ohne Ton)
# plus Kontrollbilder <out>/check-<s>s.png bei 1, 4, 8 und 12 s.
# usage: ./scripts/demo-short.sh [ausgabeordner]   (Netz nötig: Namensauflösung, PubChem;
#        beim ersten Lauf lädt Remotion seine Headless-Chrome-Version)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-$(mktemp -d)/chemdraw-short}"
mkdir -p "$OUT/public"
VIDEO_DIR=chemdraw_tool/ui/video

[ -d "$VIDEO_DIR/node_modules" ] || npm --prefix "$VIDEO_DIR" ci

(cd chemdraw_tool/ui && node src/host/demo.record.mjs "$OUT/raw" --clicks molecule)

# Playwright-webm hat keinen Dauer-Header: für Remotion vorher nach H.264 wandeln
ffmpeg -loglevel error -y -i "$OUT/raw/molecule.webm" -c:v libx264 -pix_fmt yuv420p -crf 16 -r 30 \
  -movflags +faststart "$OUT/public/molecule.mp4"

node -e '
const fs = require("fs");
const log = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
fs.writeFileSync(process.argv[2], JSON.stringify({ video: "molecule.mp4", log }));
' "$OUT/raw/molecule.clicks.json" "$OUT/props.json"

(cd "$VIDEO_DIR" && npx remotion render src/index.ts Short "$OUT/chemdraw-short.mp4" \
  --props="$OUT/props.json" --public-dir="$OUT/public" --codec=h264 --crf=18 --log=error)

for s in 1 4 8 12; do
  ffmpeg -loglevel error -y -ss "$s" -i "$OUT/chemdraw-short.mp4" -frames:v 1 "$OUT/check-${s}s.png"
done
echo "✔ $OUT/chemdraw-short.mp4"
echo "  Kontrollbilder: $OUT/check-{1,4,8,12}s.png"
