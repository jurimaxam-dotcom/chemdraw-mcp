"""Claude-Code-Plugin-Marketplace und Install-Links im README (Distribution 07.11.2026).

Drei Stellen beschreiben denselben Start (`uvx chemdraw-mcp`): die `.mcp.json`
des Plugins, der VS-Code-Link und der Cursor-Deeplink. Die Links sind kodiert,
ein Tippfehler darin fällt beim Lesen nicht auf, sondern erst beim Nutzer, dem
VS Code oder Cursor einen kaputten Server anbietet. Darum hier dekodiert.

Das Format selbst prüft `claude plugin validate --strict .` (braucht die
Claude-Code-CLI, deshalb nicht im Gate).
"""

import base64
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
PLUGIN = ROOT / "plugins" / "chemdraw-mcp"
START = {"command": "uvx", "args": ["chemdraw-mcp"]}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_marketplace_listet_das_plugin_aus_dem_unterordner():
    market = _json(ROOT / ".claude-plugin" / "marketplace.json")
    assert market["name"] == "chemdraw-mcp"
    assert market["owner"] == {"name": "jurimaxam-dotcom"}
    [eintrag] = market["plugins"]
    # Unterordner statt "./": sonst landet das ganze Repo im Plugin-Cache.
    assert eintrag["source"] == "./plugins/chemdraw-mcp"
    # Eintragsname = Manifestname, sonst findet `install <name>@…` das Plugin nicht.
    assert eintrag["name"] == _json(PLUGIN / ".claude-plugin" / "plugin.json")["name"] == "chemdraw-mcp"


def test_plugin_startet_den_server_per_uvx():
    server = _json(PLUGIN / ".mcp.json")["mcpServers"]["chemdraw"]
    assert {k: server[k] for k in START} == START
    assert server["env"] == {"CHEMDRAW_PROFILE": "mvp"}


def _link(muster: str) -> str:
    treffer = re.findall(muster, README)
    assert len(treffer) == 1, f"erwartet genau einen Link für {muster!r}, gefunden {treffer}"
    return treffer[0]


def test_vscode_link_dekodiert_zur_startkonfiguration():
    link = _link(r"https://vscode\.dev/redirect\?url=[^)\s]+")
    innen = unquote(parse_qs(urlparse(link).query)["url"][0])
    assert innen.startswith("vscode:mcp/install?"), innen
    config = json.loads(unquote(innen.removeprefix("vscode:mcp/install?")))
    assert config == {"name": "chemdraw-mcp", **START}


def test_cursor_deeplink_traegt_dieselbe_konfiguration():
    link = _link(r"cursor://anysphere\.cursor-deeplink/mcp/install\?[^`\s]+")
    query = parse_qs(urlparse(link).query)
    assert query["name"] == ["chemdraw-mcp"]
    assert json.loads(base64.b64decode(query["config"][0])) == START
    # Auf GitHub ist cursor:// nicht klickbar, deshalb steht die Config auch im Klartext da.
    assert '{"command":"uvx","args":["chemdraw-mcp"]}' in README


def test_readme_nennt_claude_code_und_codex_befehle():
    for befehl in (
        "claude plugin marketplace add jurimaxam-dotcom/chemdraw-mcp",
        "claude plugin install chemdraw-mcp@chemdraw-mcp",
        "codex mcp add chemdraw -- uvx chemdraw-mcp",
    ):
        assert befehl in README, befehl
