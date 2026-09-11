"""Eine Version, vier Traeger — und die Registry lehnt ab, wenn sie auseinanderlaufen.

server.json wird beim Registry-Publish gegen PyPI validiert, das Bundle pinnt die
PyPI-Version beim Start. Ein vergessener Bump an einer der Stellen faellt erst
beim Release auf (siehe docs/registry-publish.md) — hier faellt er im Gate auf.
"""

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version() -> str:
    return tomllib.load((ROOT / "pyproject.toml").open("rb"))["project"]["version"]


def test_server_json_carries_the_package_version():
    data = json.loads((ROOT / "server.json").read_text())
    assert data["version"] == _pyproject_version()
    assert data["packages"][0]["version"] == _pyproject_version()


def test_bundle_sources_take_the_version_from_pyproject():
    """Das Bundle traegt den Platzhalter; build-mcpb.sh setzt die Version ein."""
    manifest = json.loads((ROOT / "mcpb" / "manifest.json").read_text())
    assert manifest["version"] == "@@VERSION@@"
    run_sh = (ROOT / "mcpb" / "server" / "run.sh").read_text()
    assert "chemdraw-mcp==$VERSION" in run_sh
    assert re.search(r'VERSION="\$\{CHEMDRAW_MCP_VERSION:-@@VERSION@@\}"', run_sh)


def test_bundle_launcher_never_relies_on_path():
    """Claude Desktop startet mit minimalem GUI-PATH: das Kommando muss absolut sein."""
    manifest = json.loads((ROOT / "mcpb" / "manifest.json").read_text())
    command = manifest["server"]["mcp_config"]["command"]
    assert command.startswith("/"), command


def test_changelog_has_a_section_for_the_current_version():
    changelog = (ROOT / "CHANGELOG.md").read_text()
    assert f"## [{_pyproject_version()}]" in changelog
