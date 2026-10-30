#!/usr/bin/env bash
# Hebt die feste uv-Version des Bundle-Starters (mcpb/server/uv-checksums.txt).
#
#   ./scripts/uv-pruefsummen.sh 0.14.0
#
# Holt die .sha256-Dateien der vier unterstützten Release-Assets von GitHub,
# lädt jedes Asset einmal und prüft es dagegen, dann schreibt es die Datei neu.
# Danach: uv run pytest tests/test_mcpb_start.py, Bundle bauen, Handshake —
# siehe docs/uv-version.md.
set -euo pipefail
cd "$(dirname "$0")/.."

V="${1:?Version angeben, z.B. 0.14.0}"
BASIS="https://github.com/astral-sh/uv/releases/download/$V"
TRIPLES="aarch64-apple-darwin x86_64-apple-darwin aarch64-unknown-linux-gnu x86_64-unknown-linux-gnu"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

ZEILEN=""
for t in $TRIPLES; do
  a="uv-$t.tar.gz"
  sha=$(curl -fsSL "$BASIS/$a.sha256" | cut -d' ' -f1)
  curl -fsSL -o "$TMP/$a" "$BASIS/$a"
  ist=$(shasum -a 256 "$TMP/$a" | cut -d' ' -f1)
  [ "$ist" = "$sha" ] || { echo "FEHLER: $a: .sha256 sagt $sha, Datei hat $ist" >&2; exit 1; }
  ZEILEN+="$sha  $a"$'\n'
done

cat > mcpb/server/uv-checksums.txt <<EOF
# Feste uv-Version für Bundle-Start und install.sh, SHA-256 der Release-Assets
# (github.com/astral-sh/uv/releases). Anheben: scripts/uv-pruefsummen.sh <version>,
# siehe docs/uv-version.md. Sicherheitsscan B4.
version $V
EOF
printf '%s' "$ZEILEN" >> mcpb/server/uv-checksums.txt
echo "mcpb/server/uv-checksums.txt → uv $V"
