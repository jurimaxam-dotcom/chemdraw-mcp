"""Bundle-Start ohne uv-Laufzeitauflösung (02.10.2026).

Befund im Desktop-Log: 11 von 38 Starts scheiterten am ~55-s-Timeout von Claude
Desktop. Ein Teil davon: `uv tool run` baut seine Wegwerf-Umgebung nach jedem
geleerten Cache neu (≈50 MB Download). run.sh installiert deshalb EINMAL in ein
eigenes Tool-Verzeichnis (übersteht `uv cache clean`, fasst eine globale
Installation nicht an) und startet danach direkt, ohne uv.

Getestet mit einem nachgebauten uv, damit nichts aus dem Netz kommt.
"""

import os
import stat
import subprocess
from pathlib import Path

RUN_SH = Path(__file__).parent.parent / "mcpb" / "server" / "run.sh"

STUB = r"""#!/bin/sh
echo "$*" >> "$STUB_LOG"
if [ "$1 $2" = "tool install" ]; then
  [ -n "$STUB_FAIL_INSTALL" ] && exit 1
  spec=""; for a in "$@"; do case "$a" in chemdraw-mcp==*) spec="${a#chemdraw-mcp}";; esac; done
  mkdir -p "$UV_TOOL_DIR/chemdraw-mcp/bin"
  printf '[tool]\nrequirements = [{ name = "chemdraw-mcp", specifier = "%s" }]\n' "$spec" > "$UV_TOOL_DIR/chemdraw-mcp/uv-receipt.toml"
  printf '#!/bin/sh\necho "SERVER %s"\n' "$spec" > "$UV_TOOL_DIR/chemdraw-mcp/bin/chemdraw-mcp"
  chmod +x "$UV_TOOL_DIR/chemdraw-mcp/bin/chemdraw-mcp"
  exit 0
fi
if [ "$1 $2" = "tool run" ]; then echo "SERVER via tool run"; exit 0; fi
exit 0
"""


def _start(tmp_path: Path, version: str, fail_install: bool = False) -> tuple[str, list[str]]:
    stub = tmp_path / "uv"
    stub.write_text(STUB)
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "calls.log"
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path / "home"),
        "CHEMDRAW_MCP_UV": str(stub),
        "CHEMDRAW_MCP_VERSION": version,
        "STUB_LOG": str(log),
    }
    if fail_install:
        env["STUB_FAIL_INSTALL"] = "1"
    out = subprocess.run(
        ["/bin/sh", str(RUN_SH)], env=env, capture_output=True, text=True, timeout=20
    ).stdout.strip()
    calls = log.read_text().splitlines() if log.exists() else []
    return out, calls


def test_erster_start_installiert_einmal_und_startet_direkt(tmp_path):
    out, calls = _start(tmp_path, "9.9.1")
    assert out == "SERVER ==9.9.1"
    assert sum(c.startswith("tool install") for c in calls) == 1
    assert not any(c.startswith("tool run") for c in calls)


def test_zweiter_start_ruft_uv_gar_nicht_mehr(tmp_path):
    _start(tmp_path, "9.9.1")
    (tmp_path / "calls.log").unlink()
    out, calls = _start(tmp_path, "9.9.1")
    assert out == "SERVER ==9.9.1"
    assert calls == [], f"uv wurde trotz fertiger Installation gerufen: {calls}"


def test_neue_bundle_version_installiert_neu(tmp_path):
    _start(tmp_path, "9.9.1")
    out, calls = _start(tmp_path, "9.9.2")
    assert out == "SERVER ==9.9.2"


def test_eigenes_tool_verzeichnis_statt_globalem(tmp_path):
    _start(tmp_path, "9.9.1")
    home = tmp_path / "home"
    assert not (home / ".local" / "share" / "uv" / "tools" / "chemdraw-mcp").exists()
    assert list(home.rglob("chemdraw-mcp/uv-receipt.toml")), "keine Installation im Bundle-Verzeichnis"


def test_scheitert_die_installation_bleibt_tool_run(tmp_path):
    out, calls = _start(tmp_path, "9.9.1", fail_install=True)
    assert out == "SERVER via tool run"
