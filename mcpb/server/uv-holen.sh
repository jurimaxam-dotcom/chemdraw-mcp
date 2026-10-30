# Lädt uv in fester Version und prüft die SHA-256 gegen uv-checksums.txt
# (Sicherheitsscan B4: ersetzt `curl https://astral.sh/uv/install.sh | sh`).
# Wird von run.sh (Bundle) und install.sh gesourct; POSIX-sh.
#
#   hole_uv <zielbasis>   → druckt den Pfad des geprüften uv, Exit ≠ 0 bei Fehler
#
# Die Prüfsummen liegen eingecheckt neben diesem Skript und werden nie zur
# Laufzeit aus dem Netz geholt. CHEMDRAW_UV_DOWNLOAD_BASE ersetzt die
# GitHub-Adresse (Tests: file://).

UV_HOLEN_DIR="${UV_HOLEN_DIR:-$(cd "$(dirname "$0")" && pwd)}"

_uv_log() { printf 'chemdraw-mcp uv: %s\n' "$*" >&2; }

_uv_triple() {
  case "$(uname -s)" in
    Darwin) os=apple-darwin ;;
    Linux) os=unknown-linux-gnu ;;
    *) return 1 ;;
  esac
  case "$(uname -m)" in
    arm64 | aarch64) arch=aarch64 ;;
    x86_64 | amd64) arch=x86_64 ;;
    *) return 1 ;;
  esac
  printf '%s-%s' "$arch" "$os"
}

_uv_sha256() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  else
    return 1
  fi
}

hole_uv() {
  ziel_basis="$1"
  pruefsummen="$UV_HOLEN_DIR/uv-checksums.txt"
  uv_version="$(awk '$1 == "version" { print $2 }' "$pruefsummen")"
  if ! triple="$(_uv_triple)"; then
    _uv_log "FEHLER: keine uv-Version für $(uname -s)/$(uname -m) hinterlegt. Bitte uv selbst installieren: https://docs.astral.sh/uv/"
    return 1
  fi
  asset="uv-$triple.tar.gz"
  erwartet="$(awk -v a="$asset" '$2 == a { print $1 }' "$pruefsummen")"
  ziel="$ziel_basis/uv-$uv_version"
  if [ -x "$ziel/uv" ]; then
    printf '%s' "$ziel/uv"
    return 0
  fi
  if [ -z "$erwartet" ]; then
    _uv_log "FEHLER: keine Prüfsumme für $asset in $pruefsummen."
    return 1
  fi
  if ! command -v curl >/dev/null 2>&1; then
    _uv_log "FEHLER: weder uv noch curl vorhanden. Bitte uv installieren: https://docs.astral.sh/uv/"
    return 1
  fi
  basis="${CHEMDRAW_UV_DOWNLOAD_BASE:-https://github.com/astral-sh/uv/releases/download}"
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/chemdraw-uv.XXXXXX")" || return 1
  _uv_log "lade uv $uv_version ($asset) …"
  if ! curl --proto '=https,file' -fsSL -o "$tmp/$asset" "$basis/$uv_version/$asset"; then
    rm -rf "$tmp"
    _uv_log "FEHLER: Download von uv $uv_version fehlgeschlagen ($basis)."
    return 1
  fi
  ist="$(_uv_sha256 "$tmp/$asset" || true)"
  if [ -z "$ist" ] || [ "$ist" != "$erwartet" ]; then
    rm -rf "$tmp"
    _uv_log "FEHLER: Prüfsumme von $asset stimmt nicht — Abbruch, nichts installiert."
    _uv_log "  erwartet: $erwartet"
    _uv_log "  erhalten: ${ist:-(kein sha256-Werkzeug)}"
    return 1
  fi
  if ! tar -xzf "$tmp/$asset" -C "$tmp" || [ ! -x "$tmp/uv-$triple/uv" ]; then
    rm -rf "$tmp"
    _uv_log "FEHLER: $asset ließ sich nicht entpacken."
    return 1
  fi
  mkdir -p "$ziel_basis"
  rm -rf "$ziel.neu.$$"
  mkdir "$ziel.neu.$$"
  cp "$tmp/uv-$triple/uv" "$ziel.neu.$$/uv"
  rm -rf "$tmp"
  # mv eines Ordners ist atomar; ein paralleler Start, der schneller war, gewinnt.
  if [ -e "$ziel" ] || ! mv "$ziel.neu.$$" "$ziel" 2>/dev/null; then
    rm -rf "$ziel.neu.$$"
  fi
  [ -x "$ziel/uv" ] || return 1
  _uv_log "uv $uv_version geprüft (sha256 $erwartet)"
  printf '%s' "$ziel/uv"
}
