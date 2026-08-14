#!/usr/bin/env bash
# Registry-Release in EINEM Befehl: Login, Publish, Verifikation.
#
# Warum das Skript existiert: Der Login ist ein interaktiver Device-Flow, sein
# Code läuft nach wenigen Minuten ab, und das anschließende `publish` vergisst
# man leicht — genau so lieferte die Registry von Juni bis August 2026 die
# veraltete Version aus. Hier autorisiert man einmal, den Rest macht das Skript.
#
# Reihenfolge ist Pflicht: erst PyPI, dann Registry. Die Registry validiert beim
# Publish, dass die in server.json referenzierte PyPI-Version wirklich existiert.
#
# Dauerhafte Alternative ohne jede Interaktion: der OIDC-Job in
# docs/registry-publish.md, der beim Release automatisch läuft.
set -euo pipefail

cd "$(dirname "$0")/.."

VERSION=$(python3 -c "import json;print(json.load(open('server.json'))['version'])")
echo "== Registry-Release für chemdraw-mcp $VERSION =="
echo

echo "-- 1/4  Ist $VERSION auf PyPI? (sonst lehnt die Registry ab) --"
if ! curl -sf -o /dev/null "https://pypi.org/pypi/chemdraw-mcp/$VERSION/json"; then
  echo "ABBRUCH: chemdraw-mcp $VERSION ist nicht auf PyPI."
  echo "         Erst das GitHub-Release erzeugen (gh release create v$VERSION),"
  echo "         das löst den PyPI-Upload aus. Dann dieses Skript erneut."
  exit 1
fi
echo "ok — PyPI kennt $VERSION"
echo

echo "-- 2/4  GitHub-Login (Browser öffnet sich, Code eingeben) --"
mcp-publisher login github
echo

echo "-- 3/4  Publish --"
mcp-publisher publish
echo

echo "-- 4/4  Verifikation: liefert die Registry wirklich $VERSION aus? --"
LATEST=$(curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=jurimaxam" \
  | python3 -c "import json,sys; print(next((s['server']['version'] for s in json.load(sys.stdin)['servers'] if s['_meta']['io.modelcontextprotocol.registry/official']['isLatest']), 'keine'))")

if [ "$LATEST" = "$VERSION" ]; then
  echo "✅ Registry liefert $LATEST aus — fertig."
else
  echo "❌ Registry meldet weiterhin $LATEST statt $VERSION."
  echo "   Der Publish lief durch, der Eintrag steht aber nicht — nicht als"
  echo "   erledigt abhaken. Häufigste Ursache: der mcp-name-Marker im"
  echo "   PyPI-README fehlt, dann verweigert die Registry die Zuordnung."
  exit 1
fi
