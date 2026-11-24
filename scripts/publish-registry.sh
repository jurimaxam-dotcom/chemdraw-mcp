#!/usr/bin/env bash
# Prüft den Registry-Stand nach dem automatischen Release-Publish.
# Org-Namensräume werden im Release-Workflow per github-oidc publiziert.
# Persönliche Namensräume behalten den Device-Login als Rückfallweg.
# Erst PyPI, dann Registry; Name, Paket und Version kommen aus server.json.
set -euo pipefail

cd "$(dirname "$0")/.."

VERSION=$(python3 -c "import json;print(json.load(open('server.json'))['version'])")
NAME=$(python3 -c "import json;print(json.load(open('server.json'))['name'])")
PACKAGE=$(python3 -c "import json;print(json.load(open('server.json'))['packages'][0]['identifier'])")
ENCODED=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1], safe=''))" "$NAME")
URL="https://registry.modelcontextprotocol.io/v0.1/servers/$ENCODED/versions/latest"

echo "== Registry-Release für $NAME $VERSION =="
if ! curl -sf -o /dev/null "https://pypi.org/pypi/$PACKAGE/$VERSION/json"; then
  echo "ABBRUCH: $PACKAGE $VERSION ist noch nicht auf PyPI."
  exit 1
fi

verify() {
  curl -fsS "$URL" | python3 -c '
import json,sys
entry=json.load(sys.stdin)
server=entry["server"]
latest=entry.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {}).get("isLatest", False)
sys.exit(0 if server["name"] == sys.argv[1] and server["version"] == sys.argv[2] and latest else 1)
' "$NAME" "$VERSION"
}

# Der Release-Workflow publiziert den Org-Namensraum per github-oidc.
# Ein bereits publizierter Stand braucht keinen zweiten Login/Upload.
if verify; then
  echo "Registry liefert $NAME $VERSION aus (isLatest=true)."
  exit 0
fi

if [[ "$NAME" == io.github.chempane/* ]]; then
  echo "ABBRUCH: Registry-Stand fehlt. Den registry-Job des Release-Workflows prüfen/erneut starten."
  echo "Org-Namensräume brauchen github-oidc; persönlicher Device-Login reicht nicht."
  exit 1
fi

mcp-publisher login github
mcp-publisher publish
verify
echo "Registry liefert $NAME $VERSION aus (isLatest=true)."
