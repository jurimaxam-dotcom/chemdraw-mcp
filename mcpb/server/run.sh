#!/bin/sh
# Startet chemdraw-mcp aus dem .mcpb-Bundle heraus.
#
# Das Bundle enthält keine Laufzeit: RDKit ist eine native Erweiterung, ein
# vollständig eingepacktes Bundle wäre je Plattform weit über 100 MB. Stattdessen
# installiert uv das Paket beim ersten Start von PyPI in ein eigenes Verzeichnis,
# jede Datei gegen die Hashes in requirements.lock geprüft; danach startet der
# Server direkt und offline, ohne uv. Claude Desktop startet MCP-Server mit
# minimalem GUI-PATH — deshalb wird uv hier an den bekannten Orten gesucht und
# notfalls in fester, per SHA-256 geprüfter Version geladen (uv-holen.sh).
set -eu

VERSION="${CHEMDRAW_MCP_VERSION:-@@VERSION@@}"

log() { printf 'chemdraw-mcp bundle: %s\n' "$*" >&2; }

SKRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQS="$SKRIPT_DIR/requirements.lock"
UV_HOLEN_DIR="$SKRIPT_DIR"
. "$SKRIPT_DIR/uv-holen.sh"

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

# Eigene Umgebung je Version statt `uv tool install` (30.10.2026, Sicherheitsscan
# B4): `uv tool install` ignoriert Hashes in --constraints und
# --with-requirements (gemessen: falscher Hash installiert trotzdem). Nur
# `uv pip install --require-hashes` prüft jede Datei gegen requirements.lock,
# das der Release-Job aus uv.lock erzeugt — alle Abhängigkeiten exakt so, wie
# sie getestet wurden, und chemdraw-mcp selbst mit den Hashes der PyPI-Dateien.
# Das Verzeichnis übersteht `uv cache clean` und lässt eine globale
# `uv tool install chemdraw-mcp` des Nutzers unangetastet (02.10.2026).
BASE="${XDG_DATA_HOME:-$HOME/.local/share}/chemdraw-mcp-bundle"
UMGEBUNG="$BASE/env-$VERSION"
SERVER="$UMGEBUNG/bin/chemdraw-mcp"
STEMPEL="$UMGEBUNG/.chemdraw-mcp-installiert"

installiert() { [ -x "$SERVER" ] && [ "$(cat "$STEMPEL" 2>/dev/null)" = "$VERSION" ]; }

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

if [ ! -f "$REQS" ]; then
  gib_frei
  log "FEHLER: $REQS fehlt — das Bundle ist unvollständig gebaut (scripts/build-mcpb.sh)."
  exit 1
fi

# uv erst hier: der Normalstart oben braucht es nicht. Vorhandenes uv hat Vorrang;
# sonst eine feste Version mit geprüfter SHA-256 (uv-holen.sh), nie `curl | sh`.
# CHEMDRAW_MCP_UV=- ignoriert ein vorhandenes uv und lädt immer die geprüfte Version.
UV="${CHEMDRAW_MCP_UV:-$(find_uv || true)}"
[ "$UV" = "-" ] && UV=""
if [ -z "$UV" ]; then
  log "uv nicht gefunden — lade die geprüfte Version nach $BASE/uv"
  if ! UV="$(hole_uv "$BASE/uv")"; then
    gib_frei
    log "FEHLER: uv konnte nicht sicher installiert werden. Bitte uv installieren: https://docs.astral.sh/uv/"
    exit 1
  fi
fi

installiere() {
  # Jeder uv-Aufruf läuft im Hintergrund mit eigenem trap: ein TERM an diese
  # Subshell muss uv mitnehmen. Sonst schriebe ein verwaistes `uv pip install`
  # in die Umgebung, die der nächste Start gerade neu anlegt (02.10.2026).
  uvpid=""
  trap '[ -n "$uvpid" ] && kill "$uvpid" 2>/dev/null; exit 143' TERM INT HUP
  rm -rf "$UMGEBUNG"
  # Python 3.12 fest: dafür hat jede gelockte Abhängigkeit (RDKit!) Wheels. Fehlt
  # es, lädt uv ein verwaltetes Python und prüft dessen Hash selbst.
  "$UV" venv --quiet --python 3.12 "$UMGEBUNG" &
  uvpid=$!
  wait "$uvpid" || return 1
  # --refresh-package: Direkt nach einem Release kennt uvs zwischengespeicherter
  # PyPI-Index die neue Version noch nicht ("there is no version of
  # chemdraw-mcp==0.4.3", Desktop-Log 02.10.2026).
  "$UV" pip install --quiet --python "$UMGEBUNG/bin/python" \
    --require-hashes --refresh-package chemdraw-mcp -r "$REQS" &
  uvpid=$!
  wait "$uvpid" || return 1
  uvpid=""
  [ -x "$SERVER" ] && printf '%s\n' "$VERSION" > "$STEMPEL"
}

log "installiere chemdraw-mcp $VERSION über $UV (einmalig, Hashes geprüft; danach startet es ohne uv und offline)"
installiere >&2 &
KIND=$!
if wait "$KIND" && installiert; then
  KIND=""
  # Ältere Versionen und die frühere `uv tool`-Ablage (bis 0.6.0) aufräumen.
  for alt in "$BASE"/env-*; do
    [ "$alt" = "$UMGEBUNG" ] || rm -rf "$alt"
  done
  rm -rf "$BASE/tools" "$BASE/bin"
  gib_frei
  exec "$SERVER"
fi
KIND=""
rm -rf "$UMGEBUNG"
gib_frei

# Kein Rückfall auf `uv tool run`: der würde ohne Hashes auflösen (B4).
log "FEHLER: Installation von chemdraw-mcp $VERSION fehlgeschlagen (Netz? Hash-Abweichung?). Details stehen oben."
exit 1
