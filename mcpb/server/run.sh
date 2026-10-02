#!/bin/sh
# Startet chemdraw-mcp aus dem .mcpb-Bundle heraus.
#
# Das Bundle enthält keine Laufzeit: RDKit ist eine native Erweiterung, ein
# vollständig eingepacktes Bundle wäre je Plattform weit über 100 MB. Stattdessen
# installiert uv das Paket beim ersten Start von PyPI in ein eigenes Verzeichnis;
# danach startet der Server direkt und offline, ohne uv. Claude Desktop startet MCP-Server mit minimalem GUI-PATH —
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

UV="${CHEMDRAW_MCP_UV:-$(find_uv || true)}"
if [ -z "$UV" ]; then
  log "uv nicht gefunden — installiere es nach ~/.local/bin (astral.sh) …"
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh >&2
  else
    log "FEHLER: weder uv noch curl vorhanden. Bitte uv installieren: https://docs.astral.sh/uv/"
    exit 1
  fi
  UV="${CHEMDRAW_MCP_UV:-$(find_uv || true)}"
  if [ -z "$UV" ]; then
    log "FEHLER: uv-Installation fehlgeschlagen."
    exit 1
  fi
fi

# Feste Installation statt `uv tool run` (02.10.2026): Die Wegwerf-Umgebung von
# `uv tool run` liegt im uv-Cache und wird nach jedem `uv cache clean` neu
# gebaut (≈50 MB Download) — im Desktop-Log scheiterten so Starts am ~55-s-
# Timeout. Ein eigenes Tool-Verzeichnis übersteht das Cache-Leeren und lässt
# eine globale `uv tool install chemdraw-mcp` des Nutzers unangetastet.
BASE="${XDG_DATA_HOME:-$HOME/.local/share}/chemdraw-mcp-bundle"
export UV_TOOL_DIR="$BASE/tools"
export UV_TOOL_BIN_DIR="$BASE/bin"
SERVER="$UV_TOOL_DIR/chemdraw-mcp/bin/chemdraw-mcp"
RECEIPT="$UV_TOOL_DIR/chemdraw-mcp/uv-receipt.toml"

installiert() { [ -x "$SERVER" ] && grep -q "\"==$VERSION\"" "$RECEIPT" 2>/dev/null; }

if installiert; then
  exec "$SERVER"
fi

# Sperre: Desktop startet zwei Instanzen gleichzeitig (Chat + Cowork/Code). Ohne
# sie riss die zweite --force-Installation der ersten die Umgebung unter dem
# laufenden Server weg (02.10.2026). mkdir ist atomar und braucht kein flock.
# Verwaist die Sperre (Desktop bricht den Start ab, 02.10.2026 21:08), erkennt der
# Nächste das an der PID in der Sperre: tot heißt sofort übernehmen.
mkdir -p "$BASE"
LOCK="$BASE/.install.lock"
HALTE_ICH=0
KIND=""

gib_frei() {
  if [ "$HALTE_ICH" = 1 ]; then
    rm -f "$LOCK/pid" 2>/dev/null || true
    rmdir "$LOCK" 2>/dev/null || true
    HALTE_ICH=0
  fi
}

# TERM/INT/HUP: laufende Installation beenden, Sperre freigeben. Die Installation
# läuft im Hintergrund und `wait` unten, weil sh einen trap sonst erst nach dem
# Vordergrundbefehl ausführt — also nach der fertigen Installation.
bei_abbruch() {
  [ -n "$KIND" ] && kill "$KIND" 2>/dev/null || true
  gib_frei
  exit 143
}
trap bei_abbruch TERM INT HUP

# Sperre eines toten Halters oder (ohne PID) eines abgestürzten Starts
# (älter als 10 min) wegräumen. mv ist atomar: nur einer von zwei gleichzeitigen
# Aufräumern gewinnt.
sperre_verwaist() {
  pid="$(cat "$LOCK/pid" 2>/dev/null || true)"
  if [ -n "$pid" ]; then
    ! kill -0 "$pid" 2>/dev/null
  else
    [ -n "$(find "$LOCK" -maxdepth 0 -mmin +10 2>/dev/null)" ]
  fi
}

versuche=0
while ! mkdir "$LOCK" 2>/dev/null; do
  if sperre_verwaist; then
    if mv "$LOCK" "$LOCK.alt.$$" 2>/dev/null; then
      rm -rf "$LOCK.alt.$$"
    fi
    continue
  fi
  versuche=$((versuche + 1))
  if [ "$versuche" -gt 900 ]; then  # 180 s — dann ohne Sperre weiter
    log "Installationssperre hängt — fahre ohne fort"
    break
  fi
  sleep 0.2
done
if [ -d "$LOCK" ] && [ "$versuche" -le 900 ]; then
  printf '%s\n' "$$" > "$LOCK/pid"
  HALTE_ICH=1
fi

if installiert; then  # ein paralleler Start war schneller
  gib_frei
  exec "$SERVER"
fi

log "installiere chemdraw-mcp $VERSION über $UV (einmalig, danach startet es ohne uv und offline)"
# --refresh-package: Direkt nach einem Release kennt uvs zwischengespeicherter
# PyPI-Index die neue Version noch nicht ("there is no version of
# chemdraw-mcp==0.4.3", Desktop-Log 02.10.2026). Nur auf dem Installationsweg —
# der Normalstart ruft uv gar nicht auf.
"$UV" tool install --force --quiet --refresh-package chemdraw-mcp "chemdraw-mcp==$VERSION" >&2 &
KIND=$!
if wait "$KIND" && installiert; then
  KIND=""
  gib_frei
  exec "$SERVER"
fi
KIND=""
gib_frei

log "feste Installation fehlgeschlagen — starte über uv tool run"
exec "$UV" tool run --refresh-package chemdraw-mcp --from "chemdraw-mcp==$VERSION" chemdraw-mcp
