#!/usr/bin/env bash
# Auto-Gate: die komplette Test-Pipeline in EINEM Befehl. Grün = alles ok.
#
# Das ist das "Sinnesorgan" des autonomen Build-Test-Fix-Loops: ein einziger
# verlässlicher grün/rot-Befehl, gegen den iteriert wird. Backend (pytest) +
# Frontend (node:test unit + headless-Chromium e2e).
#
# Fehlt eine Abhängigkeit, bricht das Gate mit einer KLAREN Meldung ab statt mit
# einem kryptischen Fehler — saubere Gate-Fehler sind für den Loop essenziell.
set -euo pipefail

cd "$(dirname "$0")"
UI_DIR="chemdraw_tool/ui"

# --- Dependency-Guard ---------------------------------------------------------
missing=0
if ! command -v uv >/dev/null 2>&1; then
  echo "FEHLT: uv (Python-Paketmanager) — https://docs.astral.sh/uv/"; missing=1
fi
if [ ! -d "$UI_DIR/node_modules" ]; then
  echo "FEHLT: node_modules — Setup:  (cd $UI_DIR && npm install)"; missing=1
fi
if [ ! -d "$HOME/Library/Caches/ms-playwright" ] && [ ! -d "$HOME/.cache/ms-playwright" ]; then
  echo "FEHLT: Playwright-Chromium — Setup:  (cd $UI_DIR && npx playwright install chromium)"; missing=1
fi
if [ "$missing" -ne 0 ]; then
  echo ""
  echo "Setup unvollständig (siehe oben). Gate abgebrochen."
  exit 1
fi

# --- Gate ---------------------------------------------------------------------
echo "== Backend (pytest: tests/ + scripts/) =="
uv run pytest -q

echo ""
echo "== Frontend (node:test unit + headless-Chromium e2e) =="
npm --prefix "$UI_DIR" test

echo ""
echo "✅ Auto-Gate grün: Backend- + Frontend-Tests bestanden."
