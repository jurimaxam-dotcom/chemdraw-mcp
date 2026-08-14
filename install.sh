#!/usr/bin/env bash
# Ein-Befehl-Installer (macOS/Linux): richtet den chemdraw-tool MCP-Server für
# Claude Desktop ein — ohne dass man uv, Python oder die Config-Datei manuell
# anfassen muss.
#
#   1. stellt sicher, dass uv da ist (installiert es sonst)
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
if ! command -v uv >/dev/null 2>&1; then
  echo "→ uv (Python-Paketmanager) nicht gefunden — installiere via astral.sh …"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # uv landet in ~/.local/bin bzw. ~/.cargo/bin — für diese Session in den PATH.
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if ! command -v uv >/dev/null 2>&1; then
    echo "✗ uv-Installation fehlgeschlagen. Bitte manuell: https://docs.astral.sh/uv/"
    exit 1
  fi
fi
# Absolutpfad merken: der PATH-Export oben gilt nur für diese Shell — Claude
# Desktop startet MCP-Server mit minimalem GUI-PATH und fände ein blankes "uv"
# nicht. Der Config-Schreiber bekommt deshalb genau dieses Binary.
UV_BIN="$(command -v uv)"
echo "✓ uv: $UV_BIN"

# --- 2. Dependencies ---------------------------------------------------------
echo ""
echo "→ Dependencies installieren (uv sync) …"
uv sync --quiet
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
