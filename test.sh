#!/usr/bin/env bash
# Auto-Gate: die komplette Test-Pipeline in EINEM Befehl. Grün = alles ok.
#
# Das ist das "Sinnesorgan" des autonomen Build-Test-Fix-Loops: ein einziger
# verlässlicher grün/rot-Befehl, gegen den iteriert wird. Lint (ruff) + Backend
# (pytest) + UI-Bundle-Frische + Frontend (node:test unit + headless-Chromium e2e).
#
# Zwei Fehlerarten sind hier teurer als ein echter Testfehler:
#   falsch-rot  — kaputte Umgebung sieht aus wie kaputter Code; der Loop
#                 "repariert" dann funktionierenden Code. Deshalb der
#                 Dependency-Guard mit KLARER Meldung statt kryptischem Stacktrace.
#   falsch-grün — Tests bestehen, ausgeliefert wird trotzdem etwas anderes.
#                 Deshalb der UI-Bundle-Schritt (der Server liefert dist/, nicht src/).
#
# NICHT im Gate, aber es gibt es:  ./scripts/handshake.sh
# Das ist der einzige ECHTE MCP-Handshake (initialize → tools/list) gegen den in
# Claude Desktop registrierten Startbefehl. Alles hier läuft in-process und kann
# deshalb weder den PATH-Fehler (blankes "uv" im minimalen GUI-PATH) noch den
# Stale-Prozess-Fehler sehen. Es bleibt draußen, weil der erste npx-Lauf den
# Inspector aus dem Netz holt — von Hand fahren nach Änderungen an server.py,
# nach neuem/entferntem Tool, nach Dependency-Bumps und nach Neuinstallation.
set -euo pipefail

cd "$(dirname "$0")"
UI_DIR="chemdraw_tool/ui"

# SHA-Werkzeug: macOS bringt shasum, viele Linux-Images nur sha256sum.
# Als Array, damit die Argumente nicht vom Word-Splitting abhängen.
if command -v shasum >/dev/null 2>&1; then SHA=(shasum -a 256); else SHA=(sha256sum); fi

# Fingerabdruck über ALLE Dateien in dist/ (nach Pfad sortiert, damit die
# Traversierungsreihenfolge nichts verändert). Das "|| true" fängt ein fehlendes
# dist/ ab: sonst würde find≠0 über pipefail+set -e das Gate WORTLOS abbrechen —
# genau die kryptische Rot-Meldung, die hier nie wieder vorkommen soll.
dist_fingerprint() {
  { find "$UI_DIR/dist" -type f -exec "${SHA[@]}" {} + 2>/dev/null || true; } \
    | LC_ALL=C sort | "${SHA[@]}"
}

# --- Dependency-Guard ---------------------------------------------------------
missing=0
if ! command -v uv >/dev/null 2>&1; then
  echo "FEHLT: uv (Python-Paketmanager) — https://docs.astral.sh/uv/"; missing=1
fi
if ! command -v node >/dev/null 2>&1; then
  echo "FEHLT: node (Node.js 20+) — https://nodejs.org/"; missing=1
fi
if [ ! -d "$UI_DIR/node_modules" ]; then
  echo "FEHLT: node_modules — Setup:  (cd $UI_DIR && npm install)"; missing=1
elif command -v node >/dev/null 2>&1; then
  # Browser-Check: NICHT den Cache-Ordner prüfen, sondern den konkret benötigten
  # Build starten. Vorfall 14.08.2026: ~/Library/Caches/ms-playwright existierte,
  # aber der von Playwright 1.60.0 verlangte chromium_headless_shell-1223 fehlte —
  # das Gate starb mit genau dem Playwright-Stacktrace, den dieser Guard abfangen
  # soll. Ein echter Start ist der einzige Check, der das ausschließt: er startet
  # exakt den Browser, den svgToPng.e2e.mjs startet (chromium.launch() ⇒
  # headless-shell-Build), braucht kein Netz und kostet ~1 s.
  if ! browser_err=$(cd "$UI_DIR" && node --input-type=module -e \
        "try { const { chromium } = await import('playwright'); const b = await chromium.launch(); await b.close(); }
         catch (e) { console.error(String((e && e.message) || e).split(/\r?\n/)[0]); process.exit(1); }" 2>&1); then
    echo "FEHLT: startbarer Playwright-Chromium — Setup:  (cd $UI_DIR && npx playwright install chromium)"
    echo "       Playwright meldet:"
    printf '%s\n' "$browser_err" | head -4 | sed 's/^/       | /'
    missing=1
  fi
fi
if [ "$missing" -ne 0 ]; then
  echo ""
  echo "Setup unvollständig (siehe oben). Gate abgebrochen."
  exit 1
fi

# --- Gate ---------------------------------------------------------------------
echo "== Lint (ruff) =="
uv run ruff check .

echo ""
echo "== Backend (pytest: tests/ + scripts/) =="
uv run pytest -q

echo ""
echo "== UI-Bundle (dist/ aktuell?) =="
# Der MCP-Server liefert das gebaute Bundle chemdraw_tool/ui/dist/index.html aus,
# nicht src/. Ohne diesen Schritt kann man App.jsx ändern, ein grünes Gate bekommen
# und trotzdem das alte Bundle ausliefern — falsch-grün. Der Check baut neu und
# vergleicht die dist-Bytes davor/danach. Belegt reproduzierbar: zwei aufeinander-
# folgende Vite-Builds sind hier byte-identisch (Content-Hashes, keine Timestamps),
# der Vergleich flackert also nicht. Verglichen wird gegen den ARBEITSBAUM, nicht
# gegen HEAD — so ist ein bereits neu gebautes, noch nicht committetes dist grün.
dist_before=$(dist_fingerprint)
if ! build_out=$(npm --prefix "$UI_DIR" run build 2>&1); then
  printf '%s\n' "$build_out"
  echo ""
  echo "❌ UI-Build fehlgeschlagen (siehe oben)."
  exit 1
fi
dist_after=$(dist_fingerprint)
if [ "$dist_before" != "$dist_after" ]; then
  echo ""
  echo "❌ Bundle veraltet: dist/ fehlte oder passt nicht zu src/."
  echo "   Ausgeliefert wird dist/ — ein grünes Gate mit altem Bundle wäre falsch-grün."
  echo "   Fix:  npm --prefix $UI_DIR run build   ausführen und dist committen."
  echo "   (Der frische Build liegt bereits im Arbeitsbaum — es reicht, ihn zu committen.)"
  exit 1
fi
echo "dist/ ist aktuell (Neubau ändert kein Byte)."

echo ""
echo "== Frontend (node:test unit + headless-Chromium e2e) =="
npm --prefix "$UI_DIR" test

echo ""
echo "✅ Auto-Gate grün: Lint, Backend-Tests, UI-Bundle und Frontend-Tests bestanden."
