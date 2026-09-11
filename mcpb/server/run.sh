#!/bin/sh
# Startet chemdraw-mcp aus dem .mcpb-Bundle heraus.
#
# Das Bundle enthält keine Laufzeit: RDKit ist eine native Erweiterung, ein
# vollständig eingepacktes Bundle wäre je Plattform weit über 100 MB. Stattdessen
# holt uv das Paket beim ersten Start von PyPI und cached es; danach startet der
# Server offline. Claude Desktop startet MCP-Server mit minimalem GUI-PATH —
# deshalb wird uv hier an den bekannten Orten gesucht und notfalls installiert.
set -eu

VERSION="${CHEMDRAW_MCP_VERSION:-@@VERSION@@}"

log() { printf 'chemdraw-mcp bundle: %s\n' "$*" >&2; }

find_uv() {
  for candidate in \
    "$HOME/.local/bin/uv" \
    /opt/homebrew/bin/uv \
    /usr/local/bin/uv \
    "$HOME/.cargo/bin/uv" \
    /usr/bin/uv
  do
    if [ -x "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  if command -v uv >/dev/null 2>&1; then
    command -v uv
    return 0
  fi
  return 1
}

UV="$(find_uv || true)"
if [ -z "$UV" ]; then
  log "uv nicht gefunden — installiere es nach ~/.local/bin (astral.sh) …"
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh >&2
  else
    log "FEHLER: weder uv noch curl vorhanden. Bitte uv installieren: https://docs.astral.sh/uv/"
    exit 1
  fi
  UV="$(find_uv || true)"
  if [ -z "$UV" ]; then
    log "FEHLER: uv-Installation fehlgeschlagen."
    exit 1
  fi
fi

log "starte chemdraw-mcp $VERSION über $UV (erster Start lädt das Paket, danach offline)"
exec "$UV" tool run --from "chemdraw-mcp==$VERSION" chemdraw-mcp
