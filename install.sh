#!/usr/bin/env bash
# Ein-Befehl-Installer (macOS/Linux): richtet den chemdraw-tool MCP-Server für
# Claude Desktop ein — ohne dass man uv, Python oder die Config-Datei manuell
# anfassen muss.
#
#   1. stellt sicher, dass uv da ist (sonst feste Version, SHA-256 geprüft)
#   2. uv sync  (lädt Python + RDKit & Co. plattformkorrekt)
#   3. trägt den Server idempotent in claude_desktop_config.json ein (mit Backup)
#   4. Smoke-Test (Import) + Hinweis zum Neustart
#
# Re-Run ist gefahrlos: alles idempotent, bestehende MCP-Server bleiben erhalten.
set -euo pipefail

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo "== ChemDraw-Tool Installer =="
echo "Projekt: $PROJECT_DIR"
echo ""

# --- 1. uv -------------------------------------------------------------------
# Kein `curl … | sh` mehr (Sicherheitsscan B4): fehlt uv, kommt eine feste
# Version mit geprüfter SHA-256 — dieselbe Logik wie im Bundle-Starter.
if ! command -v uv >/dev/null 2>&1; then
  echo "→ uv (Python-Paketmanager) nicht gefunden — lade die geprüfte Version …"
  UV_HOLEN_DIR="$PROJECT_DIR/mcpb/server"
  # shellcheck source=mcpb/server/uv-holen.sh
  . "$UV_HOLEN_DIR/uv-holen.sh"
  if ! UV_GEHOLT="$(hole_uv "${XDG_DATA_HOME:-$HOME/.local/share}/chemdraw-mcp-bundle/uv")"; then
    echo "✗ uv-Installation fehlgeschlagen. Bitte manuell: https://docs.astral.sh/uv/"
    exit 1
  fi
  export PATH="$(dirname "$UV_GEHOLT"):$PATH"
fi
# Absolutpfad merken: der PATH-Export oben gilt nur für diese Shell — Claude
# Desktop startet MCP-Server mit minimalem GUI-PATH und fände ein blankes "uv"
# nicht. Der Config-Schreiber bekommt deshalb genau dieses Binary.
UV_BIN="$(command -v uv)"
echo "✓ uv: $UV_BIN"

# --- 2. Dependencies ---------------------------------------------------------
echo ""
echo "→ Dependencies installieren (uv sync --locked) …"
# --locked: exakt uv.lock (mit Hashes), nie neu auflösen.
uv sync --locked --quiet
echo "✓ Dependencies bereit."

# --- 3. Claude-Desktop-Config ------------------------------------------------
echo ""
echo "→ Server in Claude Desktop registrieren …"
uv run python scripts/install_claude_config.py \
  --project-dir "$PROJECT_DIR" --uv-command "$UV_BIN"

# --- 4. Smoke-Test -----------------------------------------------------------
echo ""
echo "→ Smoke-Test (Server-Import) …"
if uv run python -c "import chemdraw_tool.server" 2>/dev/null; then
  echo "✓ Server importiert sauber."
else
  echo "✗ Server-Import fehlgeschlagen — bitte 'uv run python -c \"import chemdraw_tool.server\"' prüfen."
  exit 1
fi

echo ""
echo "✅ Fertig. Claude Desktop neu starten, dann im Chat z.B.: \"Zeichne Aspirin\"."
