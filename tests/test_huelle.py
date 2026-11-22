"""Etappe 3 der Umbenennung: das alte PyPI-Paket chemdraw-mcp wird eine Hülle.

Gemessen am 22.11.2026 (Plan, Etappe 0):
- Befund 3: Ohne eigene [project.scripts] entfernt `uv tool upgrade chemdraw-mcp` das ganze
  Tool — der absolute Startbefehl in der Desktop-Config zeigt dann ins Leere.
- Befund 10: Liefern Hülle und chempane dieselben Moduldateien, löscht `pip install -U
  chemdraw-mcp` sie still (pip deinstalliert die alte Fassung samt RECORD nach der neuen).

Deshalb: chempane liefert das Modul chempane, die Hülle nur einen dünnen Shim chemdraw_tool
(drei Einstiegspunkte, die nach chempane weiterleiten) und die vier alten Befehle.
"""

import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HUELLE = ROOT / "huelle" / "chemdraw-mcp"
SHIM_FILES = {
    "chemdraw_tool/__init__.py",
    "chemdraw_tool/server.py",
    "chemdraw_tool/doctor.py",
    "chemdraw_tool/desktop_config.py",
}
OLD_SCRIPTS = {
    "chemdraw-mcp": "chemdraw_tool.server:main",
    "chemdraw-tool-server": "chemdraw_tool.server:main",
    "chemdraw-doctor": "chemdraw_tool.doctor:main",
    "chemdraw-install": "chemdraw_tool.desktop_config:main",
}


def _project(path: Path) -> dict:
    return tomllib.load((path / "pyproject.toml").open("rb"))["project"]


def test_huelle_is_the_old_distribution_and_follows_the_main_version():
    huelle, main = _project(HUELLE), _project(ROOT)
    assert huelle["name"] == "chemdraw-mcp"
    assert huelle["version"] == main["version"], "beide Pakete erscheinen im selben Release"
    assert huelle["dependencies"] == [f"chempane>={main['version']}"]


def test_huelle_carries_the_four_old_commands():
    assert _project(HUELLE)["scripts"] == OLD_SCRIPTS


def test_shim_entry_points_lead_to_chempane():
    """Jeder Einstiegspunkt der Hülle ist die main-Funktion des neuen Pakets."""
    code = (
        "import chemdraw_tool.server as s, chemdraw_tool.doctor as d, chemdraw_tool.desktop_config as c\n"
        "import chempane.server, chempane.doctor, chempane.desktop_config\n"
        "assert s.main is chempane.server.main\n"
        "assert d.main is chempane.doctor.main\n"
        "assert c.main is chempane.desktop_config.main\n"
    )
    subprocess.run([sys.executable, "-c", code], cwd=HUELLE, check=True, capture_output=True, text=True)


@pytest.fixture(scope="module")
def huelle_wheel(tmp_path_factory) -> zipfile.ZipFile:
    out = tmp_path_factory.mktemp("huelle")
    subprocess.run(
        # Wie publish.yml: ohne --wheel baut uv erst das sdist und daraus das Wheel — so fällt
        # auf, wenn das sdist kaputt ist (Symlinks auf ../../LICENSE zeigten aus dem Tarball).
        ["uv", "build", "--out-dir", str(out), str(HUELLE)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    wheels = list(out.glob("*.whl"))
    assert len(wheels) == 1, wheels
    return zipfile.ZipFile(wheels[0])


def test_huelle_wheel_holds_only_the_shim(huelle_wheel):
    code = {n for n in huelle_wheel.namelist() if ".dist-info/" not in n}
    assert code == SHIM_FILES, "die Hülle darf keine Datei von chempane mitliefern (Befund 10)"


def test_huelle_wheel_declares_its_dependency_and_commands(huelle_wheel):
    names = huelle_wheel.namelist()
    meta = huelle_wheel.read(next(n for n in names if n.endswith(".dist-info/METADATA"))).decode()
    entry = huelle_wheel.read(next(n for n in names if n.endswith(".dist-info/entry_points.txt"))).decode()
    assert f"Requires-Dist: chempane>={_project(ROOT)['version']}" in meta
    assert "renamed to chempane" in meta.lower(), "PyPI-Seite der Hülle nennt den neuen Namen"
    for name, target in OLD_SCRIPTS.items():
        assert f"{name} = {target}" in entry


def test_main_wheel_and_sdist_do_not_contain_the_huelle(tmp_path):
    import tarfile

    subprocess.run(
        ["uv", "build", "--out-dir", str(tmp_path)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    wheel = next(tmp_path.glob("*.whl"))
    assert not any(n.startswith(("huelle/", "chemdraw_tool/")) for n in zipfile.ZipFile(wheel).namelist())
    sdist = next(tmp_path.glob("*.tar.gz"))
    with tarfile.open(sdist) as tar:
        assert not any("/huelle/" in n or "/chemdraw_tool/" in n for n in tar.getnames())


def test_huelle_license_files_are_copies_of_the_root_files():
    """Echte Dateien statt Symlinks (sdist), inhaltsgleich mit der Wurzel."""
    for name in ("LICENSE", "NOTICE"):
        path = HUELLE / name
        assert not path.is_symlink(), name
        assert path.read_bytes() == (ROOT / name).read_bytes(), f"{name} der Hülle weicht ab"
