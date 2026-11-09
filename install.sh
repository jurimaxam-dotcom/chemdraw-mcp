#!/usr/bin/env bash
# Ein-Befehl-Installer (macOS/Linux): richtet den chemdraw-tool MCP-Server für
# Claude Desktop ein — ohne dass man uv, Python oder die Config-Datei manuell
# anfassen muss.
#
#   1. stellt sicher, dass uv da ist (sonst feste Version, SHA-256 geprüft)
#   2. uv sync  (lädt Python + RDKit & Co. plattformkorrekt)
#   3. trägt beide Konnektoren (chemdraw = mvp, chemdraw-pharma = full) idempotent
#      in claude_desktop_config.json ein (mit Backup; ersetzt das alte chemdraw-tool)
#   4. Smoke-Test (Import) + Hinweis zum Neustart
#
# Re-Run ist gefahrlos: alles idempotent, bestehende MCP-Server bleiben erhalten.
set -euo pipefail

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo "== ChemDraw-Tool Installer =="
echo "Project: $PROJECT_DIR"
echo ""

# --- 1. uv -------------------------------------------------------------------
# Kein `curl … | sh` mehr (Sicherheitsscan B4): fehlt uv, kommt eine feste
# Version mit geprüfter SHA-256 — dieselbe Logik wie im Bundle-Starter.
if ! command -v uv >/dev/null 2>&1; then
  echo "→ uv (Python package manager) not found — downloading the verified version …"
  UV_HOLEN_DIR="$PROJECT_DIR/mcpb/server"
  # shellcheck source=mcpb/server/uv-holen.sh
  . "$UV_HOLEN_DIR/uv-holen.sh"
  if ! UV_GEHOLT="$(hole_uv "${XDG_DATA_HOME:-$HOME/.local/share}/chemdraw-mcp-bundle/uv")"; then
    echo "✗ uv installation failed. Please install it manually: https://docs.astral.sh/uv/"
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
echo "→ Installing dependencies (uv sync --locked) …"
# --locked: exakt uv.lock (mit Hashes), nie neu auflösen.
uv sync --locked --quiet
echo "✓ Dependencies ready."

# --- 3. Claude-Desktop-Config ------------------------------------------------
echo ""
echo "→ Registering both connectors in Claude Desktop …"
uv run python scripts/install_claude_config.py \
  --project-dir "$PROJECT_DIR" --uv-command "$UV_BIN"

# --- 4. Smoke-Test -----------------------------------------------------------
echo ""
echo "→ Smoke test (server import) …"
if uv run python -c "import chemdraw_tool.server" 2>/dev/null; then
  echo "✓ Server imports cleanly."
else
  echo "✗ Server import failed — check with 'uv run python -c \"import chemdraw_tool.server\"'."
  exit 1
fi

echo ""
echo "✅ Done. Restart Claude Desktop, pick the connector chemdraw (or chemdraw-pharma) in the chat, then try e.g.: \"Draw aspirin\"."
