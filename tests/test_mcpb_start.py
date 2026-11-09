"""Bundle-Start ohne uv-Laufzeitauflösung (02.10.2026) und mit Hash-Prüfung (30.10.2026).

Befund im Desktop-Log: 11 von 38 Starts scheiterten am ~55-s-Timeout von Claude
Desktop. Ein Teil davon: `uv tool run` baut seine Wegwerf-Umgebung nach jedem
geleerten Cache neu (≈50 MB Download). run.sh installiert deshalb EINMAL in ein
eigenes Verzeichnis (übersteht `uv cache clean`, fasst eine globale
Installation nicht an) und startet danach direkt, ohne uv.

Sicherheitsscan B4: die Installation läuft über `uv pip install --require-hashes`
gegen requirements.lock aus dem Bundle, uv selbst kommt nie per `curl | sh`,
sondern in fester Version mit geprüfter SHA-256.

Getestet mit einem nachgebauten uv, damit nichts aus dem Netz kommt. Das Bundle
wird je Test nach tmp kopiert, weil run.sh requirements.lock neben sich erwartet.
"""

import hashlib
import platform
import re
import shutil
import stat
import subprocess
import tarfile
from pathlib import Path

SERVER_DIR = Path(__file__).parent.parent / "mcpb" / "server"
RUN_SH = SERVER_DIR / "run.sh"

STUB = r"""#!/bin/sh
echo "$*" >> "$STUB_LOG"
if [ "$1" = "venv" ]; then
  for a in "$@"; do ziel="$a"; done
  mkdir -p "$ziel/bin"
  printf '#!/bin/sh\n' > "$ziel/bin/python"; chmod +x "$ziel/bin/python"
  exit 0
fi
if [ "$1 $2" = "pip install" ]; then
  [ -n "$STUB_FAIL_INSTALL" ] && exit 1
  echo "install-start" >> "$STUB_LOG"
  [ -n "$STUB_PIDFILE" ] && echo $$ > "$STUB_PIDFILE"
  sleep "${STUB_INSTALL_SLEEP:-0}"
  py=""; reqs=""; vor=""
  for a in "$@"; do
    [ "$vor" = "--python" ] && py="$a"
    [ "$vor" = "-r" ] && reqs="$a"
    vor="$a"
  done
  spec="$(sed -n 's/^chemdraw-mcp\(==[^ ]*\).*/\1/p' "$reqs")"
  bin="$(dirname "$py")"
  printf '#!/bin/sh\necho "SERVER %s${CHEMDRAW_PROFILE:+ profile=$CHEMDRAW_PROFILE}"\n' "$spec" > "$bin/chemdraw-mcp"
  chmod +x "$bin/chemdraw-mcp"
  echo "install-end" >> "$STUB_LOG"
  exit 0
fi
exit 0
"""


def _bundle(tmp_path: Path, version: str, reqs: bool = True) -> Path:
    """Kopie von mcpb/server wie im gebauten Bundle (mit requirements.lock)."""
    server = tmp_path / "bundle" / "server"
    if not server.exists():
        shutil.copytree(SERVER_DIR, server)
    lock = server / "requirements.lock"
    if reqs:
        lock.write_text(f"chemdraw-mcp=={version} \\\n    --hash=sha256:{'a' * 64}\n")
    elif lock.exists():
        lock.unlink()
    return server / "run.sh"


def _stub(tmp_path: Path) -> Path:
    stub = tmp_path / "uv"
    stub.write_text(STUB)
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    return stub


def _env(tmp_path: Path, version: str = "9.9.1", **extra: str) -> dict[str, str]:
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path / "home"),
        "CHEMDRAW_MCP_UV": str(_stub(tmp_path)),
        "CHEMDRAW_MCP_VERSION": version,
        "STUB_LOG": str(tmp_path / "calls.log"),
    }
    env.update(extra)
    return env


def _run(tmp_path: Path, version: str = "9.9.1", reqs: bool = True, **extra: str):
    run_sh = _bundle(tmp_path, version, reqs=reqs)
    return subprocess.run(
        ["/bin/sh", str(run_sh)],
        env=_env(tmp_path, version, **extra),
        capture_output=True,
        text=True,
        timeout=20,
    )


def _start(
    tmp_path: Path, version: str, fail_install: bool = False
) -> tuple[str, list[str]]:
    extra = {"STUB_FAIL_INSTALL": "1"} if fail_install else {}
    out = _run(tmp_path, version, **extra).stdout.strip()
    log = tmp_path / "calls.log"
    calls = log.read_text().splitlines() if log.exists() else []
    return out, calls


def _base(tmp_path: Path) -> Path:
    return tmp_path / "home" / ".local" / "share" / "chemdraw-mcp-bundle"


def test_erster_start_installiert_einmal_und_startet_direkt(tmp_path):
    out, calls = _start(tmp_path, "9.9.1")
    assert out == "SERVER ==9.9.1"
    assert sum(c.startswith("pip install") for c in calls) == 1
    assert not any(c.startswith("tool ") for c in calls)


def test_installation_prueft_hashes_aus_dem_bundle(tmp_path):
    """`uv tool install --constraints` ignoriert Hashes (gemessen 30.10.2026) —
    nur `uv pip install --require-hashes -r` prüft sie."""
    _, calls = _start(tmp_path, "9.9.1")
    install = next(c for c in calls if c.startswith("pip install"))
    assert "--require-hashes" in install
    assert f"-r {tmp_path / 'bundle' / 'server' / 'requirements.lock'}" in install


def test_zweiter_start_ruft_uv_gar_nicht_mehr(tmp_path):
    _start(tmp_path, "9.9.1")
    (tmp_path / "calls.log").unlink()
    out, calls = _start(tmp_path, "9.9.1")
    assert out == "SERVER ==9.9.1"
    assert calls == [], f"uv wurde trotz fertiger Installation gerufen: {calls}"


def _altern(tmp_path, version: str, tage: int) -> None:
    import os
    import time

    stempel = _base(tmp_path) / f"env-{version}" / ".chemdraw-mcp-installiert"
    alt = time.time() - tage * 86400
    os.utime(stempel, (alt, alt))


def test_neue_bundle_version_installiert_neu_und_raeumt_die_lange_ungenutzte_weg(tmp_path):
    _start(tmp_path, "9.9.1")
    _altern(tmp_path, "9.9.1", tage=45)
    out, calls = _start(tmp_path, "9.9.2")
    assert out == "SERVER ==9.9.2"
    assert not (_base(tmp_path) / "env-9.9.1").exists()


def test_zweites_bundle_in_anderer_version_behaelt_seine_umgebung(tmp_path):
    """Basis- und Pharma-Bundle teilen ein Verzeichnis. Aktualisiert der Nutzer nur
    eines, löschte dessen Installation die Umgebung des anderen — das installierte beim
    nächsten Start neu und löschte zurück (Review 09.11.2026)."""
    _start(tmp_path, "9.9.1")
    _start(tmp_path, "9.9.2")
    assert (_base(tmp_path) / "env-9.9.1").exists(), "Umgebung des anderen Bundles gelöscht"
    (tmp_path / "calls.log").unlink()
    out, calls = _start(tmp_path, "9.9.1")
    assert out == "SERVER ==9.9.1"
    assert calls == [], f"das ältere Bundle musste neu installieren: {calls}"


def test_start_haelt_die_eigene_umgebung_als_genutzt_fest(tmp_path):
    """Genutzt heißt gestartet, nicht installiert: sonst gälte eine täglich
    gestartete Umgebung nach 30 Tagen als verwaist."""
    _start(tmp_path, "9.9.1")
    _altern(tmp_path, "9.9.1", tage=45)
    _start(tmp_path, "9.9.1")
    _start(tmp_path, "9.9.2")
    assert (_base(tmp_path) / "env-9.9.1").exists()


def test_eigenes_verzeichnis_statt_globalem(tmp_path):
    _start(tmp_path, "9.9.1")
    home = tmp_path / "home"
    assert not (home / ".local" / "share" / "uv" / "tools" / "chemdraw-mcp").exists()
    assert (_base(tmp_path) / "env-9.9.1" / "bin" / "chemdraw-mcp").exists()


def test_scheitert_die_installation_bricht_der_start_ab(tmp_path):
    """Früher fiel run.sh auf `uv tool run` zurück — das löst ohne Hashes auf (B4)."""
    r = _run(tmp_path, "9.9.1", STUB_FAIL_INSTALL="1")
    assert r.returncode != 0
    assert "SERVER" not in r.stdout
    assert "Installation von chemdraw-mcp 9.9.1 fehlgeschlagen" in r.stderr
    assert "tool run" not in (tmp_path / "calls.log").read_text()
    assert not (_base(tmp_path) / "env-9.9.1").exists(), "halbe Umgebung blieb liegen"


def test_ohne_requirements_lock_kein_ungeprueftes_install(tmp_path):
    r = _run(tmp_path, "9.9.1", reqs=False)
    assert r.returncode != 0
    assert "requirements.lock fehlt" in r.stderr
    log = tmp_path / "calls.log"
    assert not log.exists() or "pip install" not in log.read_text()


def test_parallele_kaltstarts_installieren_nur_einmal(tmp_path):
    """Desktop startet zwei Instanzen gleichzeitig (Chat + Cowork/Code). Ohne
    Sperre riss die zweite Installation der ersten die Umgebung unter dem
    laufenden Server weg (gemessen 02.10.: 'python: realpath … No such file')."""
    run_sh = _bundle(tmp_path, "9.9.1")
    env = _env(tmp_path, STUB_INSTALL_SLEEP="1")
    procs = [
        subprocess.Popen(
            ["/bin/sh", str(run_sh)], env=env, stdout=subprocess.PIPE, text=True
        )
        for _ in range(3)
    ]
    outs = [p.communicate(timeout=60)[0].strip() for p in procs]
    assert outs == ["SERVER ==9.9.1"] * 3
    marken = [
        z
        for z in (tmp_path / "calls.log").read_text().splitlines()
        if z.startswith("install-")
    ]
    assert marken == ["install-start", "install-end"], (
        f"Installationen überlappen: {marken}"
    )


def test_installation_fragt_pypi_frisch(tmp_path):
    """Direkt nach einem Release kennt uvs zwischengespeicherter Index die neue
    Version noch nicht: 'there is no version of chemdraw-mcp==0.4.3' (Desktop-Log
    02.10.2026, 0.4.3-Bundle)."""
    _, calls = _start(tmp_path, "9.9.1")
    install = next(c for c in calls if c.startswith("pip install"))
    assert "--refresh-package chemdraw-mcp" in install


# --- uv in fester Version mit Prüfsumme statt `curl | sh` (B4) --------------------


def _triple() -> str:
    arch = {
        "arm64": "aarch64",
        "aarch64": "aarch64",
        "x86_64": "x86_64",
        "amd64": "x86_64",
    }[platform.machine()]
    os_ = {"Darwin": "apple-darwin", "Linux": "unknown-linux-gnu"}[platform.system()]
    return f"{arch}-{os_}"


def _uv_download(tmp_path: Path, pruefsumme_kaputt: bool) -> dict[str, str]:
    """Release-Asset mit dem Stub als uv, lokal per file:// ausgeliefert."""
    run_sh = _bundle(tmp_path, "9.9.1")
    checksums = run_sh.parent / "uv-checksums.txt"
    version = next(
        z.split()[1]
        for z in checksums.read_text().splitlines()
        if z.startswith("version ")
    )
    asset = f"uv-{_triple()}.tar.gz"
    ablage = tmp_path / "dl" / version
    ablage.mkdir(parents=True)
    with tarfile.open(ablage / asset, "w:gz") as tar:
        tar.add(_stub(tmp_path), arcname=f"uv-{_triple()}/uv")
    sha = hashlib.sha256((ablage / asset).read_bytes()).hexdigest()
    if pruefsumme_kaputt:
        sha = sha[:-1] + ("0" if sha[-1] != "0" else "1")
    zeilen = [z for z in checksums.read_text().splitlines() if not z.endswith(asset)]
    checksums.write_text("\n".join(zeilen + [f"{sha}  {asset}"]) + "\n")
    return {
        "CHEMDRAW_MCP_UV": "-",
        "CHEMDRAW_UV_DOWNLOAD_BASE": (tmp_path / "dl").as_uri(),
    }


def test_fehlt_uv_wird_die_gepruefte_version_geladen(tmp_path):
    extra = _uv_download(tmp_path, pruefsumme_kaputt=False)
    r = _run(tmp_path, "9.9.1", **extra)
    assert r.stdout.strip() == "SERVER ==9.9.1", r.stderr
    assert list((_base(tmp_path) / "uv").glob("uv-*/uv")), "geprüftes uv nicht abgelegt"
    assert "pip install" in (tmp_path / "calls.log").read_text()


def test_falsche_uv_pruefsumme_bricht_den_start_ab(tmp_path):
    extra = _uv_download(tmp_path, pruefsumme_kaputt=True)
    r = _run(tmp_path, "9.9.1", **extra)
    assert r.returncode != 0
    assert "SERVER" not in r.stdout
    assert "Prüfsumme" in r.stderr and "stimmt nicht" in r.stderr
    assert not (tmp_path / "calls.log").exists(), "ungeprüftes uv wurde ausgeführt"
    assert not list((_base(tmp_path) / "uv").glob("uv-*")), (
        "ungeprüftes uv blieb liegen"
    )


def test_kein_curl_pipe_sh_mehr():
    for datei in (
        RUN_SH,
        SERVER_DIR / "uv-holen.sh",
        SERVER_DIR.parent.parent / "install.sh",
    ):
        code = [
            z for z in datei.read_text().splitlines() if not z.lstrip().startswith("#")
        ]
        assert not [z for z in code if re.search(r"curl[^|]*\|\s*(ba)?sh", z)], datei


# --- verwaiste Startsperre (02.10.2026, 21:08 bei Jay) ----------------------------
# Desktop bricht einen Start mitten in der Installation ab (TERM) oder killt ihn hart.
# Die Sperre blieb liegen; der nächste Start wartete bis zu 10 min darauf.


def _lock(tmp_path: Path) -> Path:
    return _base(tmp_path) / ".install.lock"


def _warte_bis(bedingung, sekunden: float = 10.0) -> bool:
    import time

    ende = time.monotonic() + sekunden
    while time.monotonic() < ende:
        if bedingung():
            return True
        time.sleep(0.05)
    return False


def _toter_pid() -> int:
    p = subprocess.Popen(["/bin/sh", "-c", "exit 0"])
    p.wait()
    return p.pid


def test_abbruch_mitten_in_der_installation_gibt_die_sperre_frei(tmp_path):
    import signal

    pidfile = tmp_path / "uv.pid"
    env = _env(tmp_path, STUB_INSTALL_SLEEP="30", STUB_PIDFILE=str(pidfile))
    log = tmp_path / "calls.log"
    p = subprocess.Popen(
        ["/bin/sh", str(_bundle(tmp_path, "9.9.1"))],
        env=env,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert _warte_bis(
            lambda: log.exists() and "install-start" in log.read_text()
        ), "Installation startete nicht"
        assert _lock(tmp_path).exists()
        p.send_signal(signal.SIGTERM)
        p.wait(timeout=5)
    finally:
        if p.poll() is None:
            p.kill()
    assert not _lock(tmp_path).exists(), "Sperre blieb nach TERM liegen"
    # Läuft uv verwaist weiter, schreibt es in die Umgebung, die der nächste Start
    # gerade neu anlegt — der Fehler vom 02.10.2026 auf neuem Weg.
    uv_pid = int(pidfile.read_text())
    assert _warte_bis(lambda: not _lebt(uv_pid), 3), (
        "uv pip install lief nach TERM verwaist weiter"
    )


def _lebt(pid: int) -> bool:
    import os

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def test_tote_pid_in_der_sperre_wird_sofort_uebernommen(tmp_path):
    """kill -9 lässt keinen trap laufen: nur die PID in der Sperre verrät, dass sie verwaist ist."""
    lock = _lock(tmp_path)
    lock.mkdir(parents=True)
    (lock / "pid").write_text(f"{_toter_pid()}\n")
    out = subprocess.run(
        ["/bin/sh", str(_bundle(tmp_path, "9.9.1"))],
        env=_env(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    assert out == "SERVER ==9.9.1"


def test_lebende_pid_in_der_sperre_wird_respektiert(tmp_path):
    lock = _lock(tmp_path)
    lock.mkdir(parents=True)
    halter = subprocess.Popen(["/bin/sleep", "30"])
    try:
        (lock / "pid").write_text(f"{halter.pid}\n")
        p = subprocess.Popen(
            ["/bin/sh", str(_bundle(tmp_path, "9.9.1"))],
            env=_env(tmp_path),
            stdout=subprocess.PIPE,
            text=True,
        )
        try:
            p.wait(timeout=2)
            raise AssertionError("Start hat eine Sperre mit lebender PID übernommen")
        except subprocess.TimeoutExpired:
            pass
        finally:
            p.kill()
            p.wait()
    finally:
        halter.kill()
        halter.wait()
    log = tmp_path / "calls.log"
    assert not log.exists() or "pip install" not in log.read_text()


def test_manifest_beschreibung_nennt_die_aktuelle_toolzahl():
    """Der Installationsdialog in Desktop zeigt `long_description`; eine veraltete
    Toolzahl dort („six tools“ bei 16 registrierten) fiel in der Bundle-Abnahme 0.7.0 auf.
    Die Zahl kommt aus dem Standardprofil, nicht aus Handarbeit."""
    import json

    from chemdraw_tool.server import create_server

    manifest = json.loads(
        (Path(__file__).resolve().parents[1] / "mcpb" / "manifest.json").read_text()
    )
    n = len(create_server("mvp")._tool_manager.list_tools())
    text = manifest["long_description"]
    assert (
        re.search(r"\b(six|seven|eight|nine|ten|eleven|twelve)\s+tools\b", text) is None
    ), text
    assert f"{n} tools" in text, (n, text)


# --- Zwei Konnektoren als zwei Extensions (Welle 3) ---------------------------
# Claude Desktop leitet die Extension-ID aus `author` + `name` ab
# (local.mcpb.<author>.<name>). Zwei Bundles aus demselben Server: `chemdraw-mcp`
# (mvp) und `chemdraw-mcp-pharma` (full), beide mit festem Profil in
# `server.mcp_config.env`, damit nie zwei Konnektoren dieselben Tools zeigen.

MANIFEST = Path(__file__).resolve().parents[1] / "mcpb" / "manifest.json"
MANIFEST_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mcpb_manifest.py"


def _variant(profile: str) -> dict:
    import json
    import sys

    result = subprocess.run(
        [sys.executable, str(MANIFEST_SCRIPT), profile],
        capture_output=True,
        text=True,
        check=True,
        cwd=MANIFEST.parents[1],
    )
    return json.loads(result.stdout)


def test_basis_manifest_pinnt_das_mvp_profil():
    import json

    manifest = json.loads(MANIFEST.read_text())
    assert manifest["name"] == "chemdraw-mcp"
    assert manifest["server"]["mcp_config"]["env"] == {"CHEMDRAW_PROFILE": "mvp"}


def test_mvp_variante_ist_das_basis_manifest():
    import json

    assert _variant("mvp") == json.loads(MANIFEST.read_text())


def test_pharma_variante_hat_eigene_id_und_festes_vollprofil():
    import json

    from chemdraw_tool.server import create_server

    base = json.loads(MANIFEST.read_text())
    pharma = _variant("full")
    assert pharma["name"] == "chemdraw-mcp-pharma"
    assert pharma["name"] != base["name"], (
        "gleiche ID hieße: eine Extension überschreibt die andere"
    )
    assert pharma["server"]["mcp_config"]["env"] == {"CHEMDRAW_PROFILE": "full"}
    assert pharma["display_name"] != base["display_name"]
    assert pharma["author"] == base["author"]
    assert pharma["server"]["entry_point"] == base["server"]["entry_point"], (
        "derselbe Starter"
    )
    assert pharma["version"] == base["version"]
    n = len(create_server("full")._tool_manager.list_tools())
    assert f"{n} tools" in pharma["long_description"], (n, pharma["long_description"])
    assert "16 tools" not in pharma["long_description"].split(f"{n} tools")[0]


def test_unbekanntes_profil_bricht_den_manifestbau_ab():
    import sys

    result = subprocess.run(
        [sys.executable, str(MANIFEST_SCRIPT), "pharma"],
        capture_output=True,
        text=True,
        cwd=MANIFEST.parents[1],
    )
    assert result.returncode != 0
    assert "full" in result.stderr


def test_run_sh_reicht_das_profil_an_den_server_durch(tmp_path):
    """Das Bundle setzt CHEMDRAW_PROFILE in mcp_config.env; run.sh darf es auf
    dem Weg zum Server weder verlieren noch überschreiben."""
    out = _run(tmp_path, "9.9.1", CHEMDRAW_PROFILE="full").stdout.strip()
    assert out == "SERVER ==9.9.1 profile=full"
