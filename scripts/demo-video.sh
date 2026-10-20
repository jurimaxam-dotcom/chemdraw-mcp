#!/usr/bin/env bash
# Demo-Medien aus dem echten Panel (Host-Nachbau + echter Server, kein Mockup von Claude Desktop):
#   assets/demo-<szene>.gif          README (640 px breit)
#   <out>/<szene>-9x16.mp4           Shorts/Reels/TikTok (1080×1920, Panel mittig)
#   <out>/<szene>-1x1.mp4            Bluesky/X (1080×1080)
# usage: ./scripts/demo-video.sh [ausgabeordner]   (Netz nötig: Namensauflösung + PubChem)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-$(mktemp -d)/chemdraw-demo}"
SZENEN=(molecule compare reaction)

(cd chemdraw_tool/ui && node src/host/demo.record.mjs "$OUT" "${SZENEN[@]}")

for s in "${SZENEN[@]}"; do
  ffmpeg -loglevel error -y -i "$OUT/$s.webm" \
    -vf "fps=15,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" \
    "assets/demo-$s.gif"
  # Hochformat: Panel auf 1080 Breite, oben/unten Rand in der Panel-Hintergrundfarbe
  ffmpeg -loglevel error -y -i "$OUT/$s.webm" \
    -vf "scale=1080:-2:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0xfafbf9,format=yuv420p" \
    -c:v libx264 -crf 20 -movflags +faststart "$OUT/$s-9x16.mp4"
  ffmpeg -loglevel error -y -i "$OUT/$s.webm" \
    -vf "scale=1080:-2:flags=lanczos,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:color=0xfafbf9,format=yuv420p" \
    -c:v libx264 -crf 20 -movflags +faststart "$OUT/$s-1x1.mp4"
  echo "✔ $s: assets/demo-$s.gif · $OUT/$s-9x16.mp4 · $OUT/$s-1x1.mp4"
done
