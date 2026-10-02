#!/bin/sh
# Baut den Praktikumsrechner als selbstständige statische Seite nach web/dist/.
#
# DSGVO (Recherche 02.10.2026, LG München I 3 O 17493/20): Schriften und Pyodide
# kommen vom eigenen Host, nicht von Google Fonts oder jsDelivr — sonst geht die
# IP jedes Besuchers an Dritte. Heruntergeladen wird hier, beim Bauen, nicht im
# Browser des Besuchers. web/dist/ ist nicht versioniert (gitignore).
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/web/dist"
PYODIDE_VERSION="314.0.7"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/chemdraw-web"
mkdir -p "$CACHE" "$OUT/vendor/fonts" "$OUT/py/chemdraw_tool/aufgaben"

# 1. Seite und Rechenkern (dieselben Dateien wie im Repo — keine Kopie im Git)
cp "$ROOT/web/praktikumsrechner/index.html" "$OUT/index.html"
for f in __init__.py ph_core.py; do cp "$ROOT/chemdraw_tool/$f" "$OUT/py/chemdraw_tool/$f"; done
for f in __init__.py basis.py titration.py ph.py mechanismus.py loeslichkeit.py loesungen.py; do
  cp "$ROOT/chemdraw_tool/aufgaben/$f" "$OUT/py/chemdraw_tool/aufgaben/$f"
done

# 2. Pyodide-Core (≈ 6,8 MB, einmal geladen und zwischengespeichert)
TAR="$CACHE/pyodide-core-$PYODIDE_VERSION.tar.bz2"
[ -f "$TAR" ] || curl -fsSL -o "$TAR" \
  "https://github.com/pyodide/pyodide/releases/download/$PYODIDE_VERSION/pyodide-core-$PYODIDE_VERSION.tar.bz2"
mkdir -p "$OUT/vendor/pyodide"
tar -xjf "$TAR" -C "$OUT/vendor/pyodide" --strip-components=1

# 3. IBM Plex (OFL), nur die Schnitte, die die Seite nutzt
for spec in ibm-plex-sans:400 ibm-plex-sans:500 ibm-plex-sans:600 ibm-plex-mono:400 ibm-plex-mono:500 \
            ibm-plex-sans-condensed:600 ibm-plex-sans-condensed:700; do
  fam="${spec%%:*}"; w="${spec##*:}"; file="$fam-latin-$w-normal.woff2"
  [ -f "$CACHE/$file" ] || curl -fsSL -o "$CACHE/$file" "https://cdn.jsdelivr.net/npm/@fontsource/$fam@5/files/$file"
  cp "$CACHE/$file" "$OUT/vendor/fonts/$file"
done

echo "web/dist gebaut: $(du -sh "$OUT" | cut -f1), $(find "$OUT" -type f | wc -l | tr -d ' ') Dateien"
