"""Die Desktop-Config-Logik muss im installierten Paket liegen, nicht in scripts/.

Das Wheel enthält nur `chemdraw_tool` (pyproject: packages = ["chemdraw_tool"]).
Lag die Logik in `scripts/`, konnte `chemdraw-doctor` bei einer PyPI-Installation
genau die Checks nicht ausführen, für die er gebaut wurde — uv-Auflösung und
Desktop-Eintrag —, und ein per `uvx` installierter Nutzer hatte überhaupt keinen
Weg, sich einzutragen. Beides betrifft ausgerechnet den Installationsweg, über
den das Projekt in der MCP-Registry gefunden wird.
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_desktop_config_lives_in_the_installed_package():
    """Importierbar ohne Repo-Wurzel im Pfad — sonst fehlt es im Wheel."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from chemdraw_tool.desktop_config import "
            "claude_config_path, resolve_uv_command, build_server_entry, install; "
            "print('ok')",
        ],
        capture_output=True,
        text=True,
        cwd=REPO.parent,  # NICHT im Repo: scripts/ ist so garantiert unerreichbar
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_pypi_users_get_an_install_command():
    """Ohne Repo-Clone braucht es einen Console-Script-Einstieg."""
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]
    assert "chemdraw-install" in scripts
    assert scripts["chemdraw-install"].startswith("chemdraw_tool.")


def test_doctor_does_not_depend_on_the_scripts_directory():
    """Der Doctor darf seine Helfer nicht aus scripts/ ziehen."""
    source = (REPO / "chemdraw_tool" / "doctor.py").read_text(encoding="utf-8")
    assert "from scripts" not in source
    assert "install_claude_config" not in source


def test_installed_package_entry_does_not_point_at_site_packages(tmp_path):
    """Aus dem Wheel heraus gibt es kein Projektverzeichnis.

    `uv --directory <site-packages> run …` wäre Unsinn: dort liegt kein Projekt.
    Ein aus dem Paket heraus geschriebener Eintrag muss deshalb das installierte
    Console-Script direkt starten.
    """
    from chemdraw_tool.desktop_config import build_installed_entry

    launcher = tmp_path / "chemdraw-mcp"
    launcher.write_text("#!/bin/sh\n")
    launcher.chmod(0o755)

    entry = build_installed_entry(launcher=str(launcher))

    assert entry["command"] == str(launcher)
    assert entry.get("args", []) == []
    assert "--directory" not in entry.get("args", [])
