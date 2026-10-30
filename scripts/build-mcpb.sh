#!/usr/bin/env bash
# Baut das Claude-Desktop-Bundle (.mcpb) aus mcpb/ nach dist/.
#
# Das Bundle ist ein Starter, keine Laufzeit: mcpb/server/run.sh holt beim ersten
# Start das PyPI-Paket in GENAU der Version aus pyproject.toml per uv. Deshalb
# wird die Version hier aus pyproject.toml in manifest.json und run.sh
# eingesetzt — eine Stelle, die den Wert trägt, statt vier, die auseinanderlaufen.
#
# Dazu kommt server/requirements.lock (Sicherheitsscan B4): alle Abhängigkeiten
# exakt aus uv.lock mit Hashes, plus chemdraw-mcp selbst mit den SHA-256 der
# Dateien, die auf PyPI liegen. run.sh installiert nur mit --require-hashes.
# Deshalb muss die Version schon auf PyPI sein (Release-Job: nach `publish`).
#
# Voraussetzung: npx (Node 20+), uv. Ergebnis: dist/chemdraw-mcp-<version>.mcpb
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=$(python3 -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

cp -R mcpb/. "$STAGE/"
sed -i.bak "s/@@VERSION@@/$VERSION/g" "$STAGE/manifest.json" "$STAGE/server/run.sh"
rm -f "$STAGE"/manifest.json.bak "$STAGE"/server/run.sh.bak
chmod +x "$STAGE/server/run.sh"

REQS="$STAGE/server/requirements.lock"
uv export --frozen --format requirements-txt --no-default-groups --no-emit-project \
  --no-header --output-file "$REQS" >/dev/null
# PyPI braucht nach dem Upload ein paar Sekunden — bis zu 5 min warten.
for _ in $(seq 1 30); do
  if HASHES=$(curl -sf "https://pypi.org/pypi/chemdraw-mcp/$VERSION/json" | python3 -c "
import json, sys
urls = json.load(sys.stdin)['urls']
assert urls, 'keine Dateien'
print(' '.join('--hash=sha256:' + u['digests']['sha256'] for u in urls))
"); then
    break
  fi
  HASHES=""
  sleep 10
done
if [ -z "$HASHES" ]; then
  echo "FEHLER: chemdraw-mcp $VERSION ist nicht auf PyPI — ohne Hashes kein Bundle." >&2
  exit 1
fi
printf 'chemdraw-mcp==%s %s\n' "$VERSION" "$HASHES" >> "$REQS"

mkdir -p dist
OUT="$PWD/dist/chemdraw-mcp-$VERSION.mcpb"
(cd "$STAGE" && npx -y @anthropic-ai/mcpb@2.1.2 validate manifest.json && npx -y @anthropic-ai/mcpb@2.1.2 pack . "$OUT")
echo "Bundle: $OUT ($(du -h "$OUT" | cut -f1))"
