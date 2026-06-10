#!/usr/bin/env bash
# Regenerates assets/mechanism-demo.gif from the built UI (english labels).
# Run after UI or mechanism-template changes: ./scripts/gen_mechanism_gif.sh
set -euo pipefail
cd "$(dirname "$0")/.."

uv run python -c "
import json
from chemdraw_tool.server import generate_mechanism
m = generate_mechanism('fischer_ester', ['CC(=O)O', 'CCO'], current_step=1)
with open('/tmp/mech_payload.json', 'w') as f:
    json.dump(m.model_dump(), f)
"

(cd chemdraw_tool/ui && node gen_mechanism_frames.mjs "file://$(pwd)/chemdraw_tool/ui/dist/index.html")

ffmpeg -y -framerate 0.75 -i /tmp/mech_frame_%02d.png \
  -vf "fps=10,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  assets/mechanism-demo.gif
echo "assets/mechanism-demo.gif aktualisiert"
