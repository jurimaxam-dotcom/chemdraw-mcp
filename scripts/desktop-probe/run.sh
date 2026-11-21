#!/usr/bin/env bash
# Desktop-Probe: Claude Desktop per XCUIAutomation prüfen (Testfassung, 14.11.2026).
#   scripts/desktop-probe/run.sh A [tool …] neuer Prompt je Panel-Tool (Modell, Rechte, Panel)
#   scripts/desktop-probe/run.sh A --modell "<Name>" [tool …]   anderes Modell als der Standard Opus 5.5
#   scripts/desktop-probe/run.sh B [tool …] Checkpoints am vorhandenen Chat, kein neuer Prompt
# Reserviert die Lease claude-desktop im konfigurierten Arbeitsverzeichnis und gibt sie am Ende frei. Während des
# Laufs gehört der Bildschirm dem Test: ein Wechsel in eine andere App macht Checkpoints rot.
set -uo pipefail
STUFE="${1:-}"; shift || true
# Standardmodell für Stufe A ist Opus 5.5 (Stufe B schickt keinen Prompt und stellt nichts um).
# Ein explizites --modell überschreibt den Standard.
MODELL=""; [ "$STUFE" = A ] && MODELL="Opus 5.5"
if [ "${1:-}" = "--modell" ]; then MODELL="$2"; shift 2; fi
TOOLS=("$@"); TOOL="${TOOLS[*]:-}"; TOOL="${TOOL// /+}"
case "$STUFE" in A|B) ;; *) echo "usage: run.sh A|B [tool …]" >&2; exit 2;; esac
HIER="$(cd "$(dirname "$0")" && pwd)"
LEASE_DIR="${CHEMDRAW_DESKTOP_LEASE_DIR:-$(git -C "$HIER" config --get chemdraw.desktopLeaseDir || true)}"
TISCH="$HOME/.claude/bin/tisch"
STEMPEL="$(date +%Y-%m-%d_%H%M%S)"
OUT="$HIER/out/$STEMPEL-$STUFE${MODELL:+-${MODELL// /_}}${TOOL:+-$TOOL}"
mkdir -p "$OUT"

# Lease: ein Fahrer für Claude Desktop. Fremde Lease = Hände weg.
MINUTEN=$([ "$STUFE" = A ] && echo 45 || echo 20)
if [ -x "$TISCH" ] || [ -n "$LEASE_DIR" ]; then
  if [ ! -x "$TISCH" ] || [ ! -d "$LEASE_DIR" ]; then
    echo "Set CHEMDRAW_DESKTOP_LEASE_DIR to the shared lease directory and check the lease tool." >&2
    exit 3
  fi
  if ! (cd "$LEASE_DIR" && "$TISCH" reserviere claude-desktop --minuten "$MINUTEN"); then
    echo "✘ Lease claude-desktop nicht frei — kein Lauf." >&2; exit 3
  fi
  trap '(cd "$LEASE_DIR" && "$TISCH" gib-frei claude-desktop >/dev/null 2>&1)' EXIT
else
  echo "No lease tool configured. Running locally." >&2
fi

cd "$HIER"
# xcodegen verlangt, dass der Testplan schon liegt; die echte Fassung folgt gleich darunter.
[ -f DesktopProbe.xctestplan ] || echo '{"configurations":[],"defaultOptions":{},"testTargets":[],"version":1}' > DesktopProbe.xctestplan
xcodegen generate --quiet || exit 1
# Testplan: Bildschirmaufnahme und Anhänge auch bei Erfolg behalten. Die Ziel-ID kommt aus dem
# frisch erzeugten Projekt.
ZIEL_ID="$(grep -m1 -B0 'DesktopProbeUITests \*/ = {' DesktopProbe.xcodeproj/project.pbxproj | awk '{print $1}')"
cat > DesktopProbe.xctestplan <<JSON
{
  "configurations" : [ { "id" : "5E0E3F0A-0000-4000-8000-000000000001", "name" : "Standard", "options" : { } } ],
  "defaultOptions" : {
    "preferredScreenCaptureFormat" : "screenRecording",
    "uiTestingScreenshotsLifetime" : "keepAlways",
    "userAttachmentLifetime" : "keepAlways"
  },
  "testTargets" : [ { "target" : { "containerPath" : "container:DesktopProbe.xcodeproj", "identifier" : "$ZIEL_ID", "name" : "DesktopProbeUITests" } } ],
  "version" : 1
}
JSON

NUR=()
if [ ${#TOOLS[@]} -eq 0 ]; then NUR=(-only-testing:"DesktopProbeUITests/Stufe$STUFE")
else for t in "${TOOLS[@]}"; do NUR+=(-only-testing:"DesktopProbeUITests/Stufe$STUFE/test_$t"); done; fi
open -a Claude; sleep 2
T0=$(date +%s)
TEST_RUNNER_PROBE_MODELL="$MODELL" xcodebuild test -project DesktopProbe.xcodeproj -scheme DesktopProbe -destination 'platform=macOS' \
  "${NUR[@]}" -resultBundlePath "$OUT/ergebnis.xcresult" > "$OUT/xcodebuild.log" 2>&1
RC=$?
T1=$(date +%s)
xcrun xcresulttool export attachments --path "$OUT/ergebnis.xcresult" --output-path "$OUT/anhaenge" >/dev/null 2>&1
python3 "$HIER/bericht.py" "$OUT" "$STUFE" "$((T1 - T0))"
BRC=$?
echo "xcodebuild rc=$RC · Ordner: $OUT"
exit $BRC
