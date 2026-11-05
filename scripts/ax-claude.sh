#!/usr/bin/env bash
# Desktop-Steuerung für Codex-Handtests (AX-Klicks in Claude Desktop). Quelle und Binary liegen im
# privaten Schwester-Repo chemdraw-vermarktung (Etappe F, 05.11.2026); dieser Wrapper ruft sie auf.
# usage: scripts/ax-claude.sh <befehl> [argumente…]   (z. B. preflight, capture-plan, dump, click …)
# Anderer Ort des Schwester-Repos: CHEMDRAW_VERMARKTUNG=<pfad>. Kein automatischer Clone.
set -euo pipefail
REPO="${CHEMDRAW_VERMARKTUNG:-$HOME/Documents/projects/chemdraw-vermarktung}"
SRC="$REPO/ax-claude.swift"
BIN="$REPO/out/.bin/ax-claude"
if [ ! -f "$SRC" ]; then
  echo "✘ $SRC fehlt — Schwester-Repo chemdraw-vermarktung (privat) dort erwartet; sonst CHEMDRAW_VERMARKTUNG=<pfad> setzen." >&2
  exit 1
fi
if [ ! -x "$BIN" ] || [ "$SRC" -nt "$BIN" ]; then
  mkdir -p "$(dirname "$BIN")"
  swiftc -O "$SRC" -o "$BIN"
fi
exec "$BIN" "$@"
