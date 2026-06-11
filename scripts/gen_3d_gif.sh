#!/usr/bin/env bash
# Regenerates assets/3d-demo.gif from the built UI: one full 360° rotation
# of the morphine conformer. Run after UI or generate_3d changes:
# ./scripts/gen_3d_gif.sh
set -euo pipefail
cd "$(dirname "$0")/.."

uv run python -c "
import json
from chemdraw_tool.server import generate_3d
m = generate_3d('morphine', label='Morphine').model_dump()
m.pop('files', None)  # Footer mit lokalem SDF-Pfad gehört nicht ins README
with open('/tmp/mol3d_payload.json', 'w') as f:
    json.dump(m, f)
"

(cd chemdraw_tool/ui && node gen_3d_frames.mjs "file://$(pwd)/dist/index.html")

ffmpeg -y -framerate 12 -i /tmp/mol3d_frame_%02d.png \
  -vf "scale=560:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  assets/3d-demo.gif
echo "assets/3d-demo.gif aktualisiert"
