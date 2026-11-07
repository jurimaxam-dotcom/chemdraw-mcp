#!/usr/bin/env bash
# Echter MCP-Handshake gegen den REGISTRIERTEN Startbefehl.
#
# Warum ausserhalb des Auto-Gates: Die 60 Testdateien laufen alle in-process
# (`from chemdraw_tool.server import mcp`). Sie koennen zwei Fehlerarten
# prinzipiell nicht sehen — und ausgerechnet die haben in diesem Projekt Zeit
# gekostet:
#
#   PATH-Fehler    — Claude Desktop startet MCP-Server mit dem minimalen
#                    GUI-/launchd-PATH. Steht in der Config ein blankes "uv",
#                    startet der Server dort kommentarlos nicht, waehrend jeder
#                    In-Process-Test gruen bleibt.
#   Stale-Prozess  — der Host haelt den Serverprozess am Leben; nach einer
#                    Code-Aenderung mischen sich alte Module mit neuen Dateien
#                    (die kryptischen RDKit-/Boost-Signaturfehler).
#
# Dieses Skript spricht deshalb echtes stdio-MCP mit jedem Befehl, der wirklich
# in der Claude-Desktop-Config steht (beide Konnektoren, je mit ihrem Profil),
# und zaehlt am Ergebnis nach:
#   * wie viele Tools der Client sieht
#   * wie viele davon ein App-Panel mitbringen (meta.ui.resourceUri)
#
# Die Sollzahlen stehen NICHT hier drin, sondern werden je Profil aus dem
# Python-Server abgeleitet — sonst luegt das Skript ab dem naechsten neuen Tool.
#
# Nicht im Auto-Gate (./test.sh), weil der erste npx-Lauf den Inspector aus dem
# Netz holt. Von Hand fahren nach: Aenderungen an server.py, neuem/entferntem
# Tool, Dependency-Bump, Neuinstallation, oder wenn im Desktop "das Tool tut
# nichts" gemeldet wird.
#
# Aufruf:  ./scripts/handshake.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

INSPECTOR="@modelcontextprotocol/inspector@2.2.0"

# --- Werkzeuge da? ------------------------------------------------------------
missing=0
if ! command -v uv >/dev/null 2>&1; then
  echo "FEHLT: uv (Python-Paketmanager) — https://docs.astral.sh/uv/"; missing=1
fi
if ! command -v npx >/dev/null 2>&1; then
  echo "FEHLT: npx (kommt mit Node.js 20+) — https://nodejs.org/"
  echo "       Der MCP-Inspector wird per npx geholt; ohne npx kein Handshake."
  missing=1
fi
if [ "$missing" -ne 0 ]; then
  echo ""
  echo "Handshake abgebrochen (siehe oben)."
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- 1. Registrierte Konnektoren aus der Claude-Desktop-Config lesen ----------
# Ueber die Logik des Installers, nicht ueber einen zweiten hartkodierten Pfad:
# desktop_config.py kennt Konnektornamen, Profile und den plattformabhaengigen
# Config-Pfad. Seit Welle 3 gibt es zwei Konnektoren (chemdraw = mvp,
# chemdraw-pharma = full); eine Installation von davor heisst chemdraw-tool und
# wird mit Warnung ebenfalls geprueft — der Desktop startet sie ja genauso.
# Ausgabe: erste Zeile = Herkunft (config|fallback|broken <TAB> Detail), danach
# je Konnektor eine Zeile "name <TAB> profil <TAB> argv-Elemente mit TAB getrennt".
uv run python - >"$TMP/cmd.txt" <<'PY'
import json
import sys

from chemdraw_tool.desktop_config import (
    CONNECTORS,
    LEGACY_SERVER_NAMES,
    claude_config_path,
)

path = claude_config_path()
servers = {}
if path.is_file():
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"broken\t{path}: {exc}")
        sys.exit(0)
    servers = config.get("mcpServers") or {}

found = []
for name in (*CONNECTORS, *LEGACY_SERVER_NAMES):
    entry = servers.get(name)
    if isinstance(entry, dict) and entry.get("command"):
        profile = (entry.get("env") or {}).get("CHEMDRAW_PROFILE", "mvp")
        argv = [entry["command"], *(entry.get("args") or [])]
        found.append((name, profile, argv))

if found:
    print(f"config\t{path}")
    for name, profile, argv in found:
        print("\t".join([name, profile, *argv]))
else:
    print(f"fallback\t{path}")
    print("\t".join(["chemdraw", "mvp", "uv", "run", "chemdraw-tool-server"]))
PY

origin="$(head -1 "$TMP/cmd.txt" | cut -f1)"
origin_detail="$(head -1 "$TMP/cmd.txt" | cut -f2-)"

if [ "$origin" = "broken" ]; then
  echo "❌ Claude-Desktop-Config ist kein gueltiges JSON: $origin_detail"
  echo "   Erst reparieren — der Desktop laedt sie sonst genauso wenig."
  exit 1
fi

if [ "$origin" = "config" ]; then
  echo "Registrierte Konnektoren in der Claude-Desktop-Config ($origin_detail):"
else
  echo "⚠ Kein Eintrag in $origin_detail — Fallback auf 'uv run chemdraw-tool-server'."
  echo "  Getestet wird damit NICHT der Weg, den Claude Desktop geht."
  echo "  Eintragen mit:  ./install.sh   (oder: uv run chemdraw-install)"
fi

# --- 2. Je Konnektor: Soll aus dem Profil ableiten, Handshake, nachzaehlen ---
# Panel-Kriterium ist meta.ui.resourceUri — dasselbe, was Claude Desktop
# auswertet und was der Inspector mit --app-info als hasApp meldet.
# Die Sollzahlen stehen NICHT hier drin, sondern kommen aus create_server(<profil>)
# — sonst luegt das Skript ab dem naechsten neuen Tool.
failed=0
checked=0
while IFS=$'\t' read -r name profile rest; do
  [ -n "$name" ] || continue
  # Bash 3.2 (macOS-Default) kennt kein mapfile — deshalb die Leseschleife.
  CMD=()
  while IFS= read -r -d $'\t' element; do CMD+=("$element"); done <<<"${rest}"$'\t'
  echo ""
  echo "== $name (Profil $profile) =="
  if [ "$name" = "chemdraw-tool" ]; then
    echo "⚠ Eintrag aus der Zeit vor Welle 3 — ./install.sh ersetzt ihn durch chemdraw + chemdraw-pharma."
  fi
  printf '  Startbefehl: %s\n' "${CMD[*]}"

  # "tail -1", weil Bibliotheken beim ersten Start gern etwas dazwischenrufen
  # (matplotlib baut z.B. seinen Font-Cache) — die Zahlen stehen zuletzt.
  expected="$(uv run python -c '
import asyncio
import sys

from chemdraw_tool.server import create_server

tools = asyncio.run(create_server(sys.argv[1]).list_tools())
panels = sum(1 for t in tools if ((t.meta or {}).get("ui") or {}).get("resourceUri"))
print(len(tools), panels)
' "$profile" | tail -1)"
  expected_total="$(echo "$expected" | cut -d" " -f1)"
  expected_panels="$(echo "$expected" | cut -d" " -f2)"
  echo "  Erwartet laut Python-Server: $expected_total Tools, davon $expected_panels mit Panel."

  # --- Echter stdio-Handshake ------------------------------------------------
  # Argumentreihenfolge ist NICHT die aus der Inspector-Doku gewohnte:
  # inspector-cli trennt an "--" und liest VOR dem Trenner das Zielkommando,
  # DAHINTER die eigenen Optionen. Ohne diese Form frisst der Zielbefehl
  # "--method"/"--app-info" bzw. uv verschluckt sein eigenes "--directory".
  # --app-info liefert mit --method tools/list eine NDJSON-Zeile je Tool
  # (hasApp true/false) — Gesamtzahl und Panel-Zahl in EINEM Lauf.
  # Das Profil geht wie beim Desktop (env im Config-Eintrag) an den Kindprozess —
  # beim Inspector nur per -e: eine exportierte Variable reicht er NICHT durch
  # (gemessen 07.11.2026: full-Eintrag lieferte 16 statt 23 Tools).
  echo "  Handshake laeuft (initialize → tools/list, Inspector via npx) …"
  set +e
  npx -y "$INSPECTOR" --cli "${CMD[@]}" -- -e "CHEMDRAW_PROFILE=$profile" --method tools/list --app-info \
    >"$TMP/out-$name.ndjson" 2>"$TMP/err-$name.log"
  rc=$?
  set -e

  if [ "$rc" -ne 0 ] || [ ! -s "$TMP/out-$name.ndjson" ]; then
    echo ""
    echo "❌ Handshake fehlgeschlagen (Exit $rc, $(wc -l <"$TMP/out-$name.ndjson" | tr -d ' ') Zeilen Ausgabe)."
    echo "   Genau dieser Fall bleibt In-Process-Tests verborgen: der registrierte"
    echo "   Befehl startet keinen sprechfaehigen Server."
    # Die eigentliche Fehlerzeile des Inspectors zuerst — npm-Hinweise ("new
    # version available") stehen sonst dahinter und verdecken sie.
    if grep -q '{"error"' "$TMP/err-$name.log"; then
      echo "   Meldung des Inspectors:"
      grep '{"error"' "$TMP/err-$name.log" | head -3 | sed 's/^/   | /'
    fi
    echo "   Letzte Ausgabe des Servers:"
    tail -20 "$TMP/err-$name.log" | sed 's/^/   | /'
    failed=1
    continue
  fi

  # --- Nachzaehlen -----------------------------------------------------------
  # Auswertung in Python statt grep -c: grep liefert bei null Treffern Exit 1 und
  # wuerde das Skript ueber set -e wortlos beenden.
  actual="$(uv run python - "$TMP/out-$name.ndjson" <<'PY'
import json
import sys

total = panels = 0
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    record = json.loads(line)
    total += 1
    if record.get("hasApp"):
        panels += 1
print(total, panels)
PY
)"
  actual="$(echo "$actual" | tail -1)"
  actual_total="$(echo "$actual" | cut -d" " -f1)"
  actual_panels="$(echo "$actual" | cut -d" " -f2)"
  echo "  Gemeldet vom laufenden Server: $actual_total Tools, davon $actual_panels mit Panel."

  if [ "$actual_total" != "$expected_total" ] || [ "$actual_panels" != "$expected_panels" ]; then
    echo "❌ $name: Abweichung zwischen Quellcode und laufendem Server:"
    echo "   Tools mit Panel : erwartet $expected_panels, gemeldet $actual_panels"
    echo "   Tools gesamt    : erwartet $expected_total, gemeldet $actual_total"
    echo ""
    echo "   Wahrscheinlichste Ursachen:"
    echo "   * der Startbefehl zeigt auf ein anderes Verzeichnis/eine andere"
    echo "     Installation als dieses Repo (Befehl oben pruefen)"
    echo "   * ein Panel-Tool ohne meta=_UI_META (Panel bleibt zu)"
    echo "   * veralteter Prozess/Cache — Claude Desktop neu starten"
    failed=1
    continue
  fi
  echo "✅ $name: $actual_total Tools, $actual_panels mit Panel — der registrierte Befehl spricht MCP."
  checked=$((checked + 1))
done < <(tail -n +2 "$TMP/cmd.txt")

echo ""
if [ "$failed" -ne 0 ]; then
  echo "❌ Handshake rot (siehe oben)."
  exit 1
fi
echo "✅ Handshake gruen: $checked Konnektor(en) geprueft."
