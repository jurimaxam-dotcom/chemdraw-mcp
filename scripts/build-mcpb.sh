#!/usr/bin/env bash
# Baut das Claude-Desktop-Bundle (.mcpb) aus mcpb/ nach dist/.
#
# Das Bundle ist ein Starter, keine Laufzeit: mcpb/server/run.sh holt beim ersten
# Start das PyPI-Paket in GENAU der Version aus pyproject.toml per uv. Deshalb
# wird die Version hier aus pyproject.toml in manifest.json und run.sh
# eingesetzt — eine Stelle, die den Wert trägt, statt vier, die auseinanderlaufen.
#
# Voraussetzung: npx (Node 20+). Ergebnis: dist/chemdraw-mcp-<version>.mcpb
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=$(python3 -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

cp -R mcpb/. "$STAGE/"
sed -i.bak "s/@@VERSION@@/$VERSION/g" "$STAGE/manifest.json" "$STAGE/server/run.sh"
rm -f "$STAGE"/manifest.json.bak "$STAGE"/server/run.sh.bak
chmod +x "$STAGE/server/run.sh"

mkdir -p dist
OUT="$PWD/dist/chemdraw-mcp-$VERSION.mcpb"
(cd "$STAGE" && npx -y @anthropic-ai/mcpb@2.1.2 validate manifest.json && npx -y @anthropic-ai/mcpb@2.1.2 pack . "$OUT")
echo "Bundle: $OUT ($(du -h "$OUT" | cut -f1))"
