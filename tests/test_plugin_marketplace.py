"""Claude-Code-Plugin-Marketplace und Install-Links im README (Distribution 07.11.2026).

Drei Stellen beschreiben denselben Start (`uvx chempane`): die `.mcp.json`
des Plugins, der VS-Code-Link und der Cursor-Deeplink. Die Links sind kodiert,
ein Tippfehler darin fällt beim Lesen nicht auf, sondern erst beim Nutzer, dem
VS Code oder Cursor einen kaputten Server anbietet. Darum hier dekodiert.

Das Format selbst prüft `claude plugin validate --strict .` (braucht die
Claude-Code-CLI, deshalb nicht im Gate).
"""

import base64
import json
import re
import struct
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
PLUGIN = ROOT / "plugins" / "chemdraw-mcp"
CHEMPANE_PLUGIN = ROOT / "plugins" / "chempane"
START = {"command": "uvx", "args": ["chempane"]}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_marketplace_listet_die_plugins_aus_den_unterordnern():
    market = _json(ROOT / ".claude-plugin" / "marketplace.json")
    assert market["name"] == "chemdraw-mcp"
    assert market["owner"] == {"name": "jurimaxam-dotcom"}
    by_name = {e["name"]: e for e in market["plugins"]}
    assert set(by_name) == {"chempane", "chemdraw-mcp"}
    for name, pfad in (("chempane", CHEMPANE_PLUGIN), ("chemdraw-mcp", PLUGIN)):
        # Unterordner statt "./": sonst landet das ganze Repo im Plugin-Cache.
        assert by_name[name]["source"] == f"./plugins/{name}"
        # Eintragsname = Manifestname, sonst findet `install <name>@…` das Plugin nicht.
        assert _json(pfad / ".claude-plugin" / "plugin.json")["name"] == name


def test_chempane_plugin_erfuellt_directory_anforderungen():
    manifest = _json(CHEMPANE_PLUGIN / ".claude-plugin" / "plugin.json")
    version = manifest["version"]
    assert manifest["displayName"] == "chempane"
    icon_rel = manifest["icon"]
    assert not icon_rel.startswith("..")
    icon_path = (CHEMPANE_PLUGIN / icon_rel).resolve()
    assert icon_path.is_relative_to(CHEMPANE_PLUGIN.resolve())
    raw = icon_path.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", raw[16:24])
    assert width == height
    assert 512 <= width <= 2048
    assert len(raw) < 2 * 1024 * 1024

    hosts = set(manifest["network"]["hosts"])
    erwartete_hosts = {
        "pubchem.ncbi.nlm.nih.gov",
        "cactus.nci.nih.gov",
        "www.ebi.ac.uk",
        "rest.kegg.jp",
        "rest.uniprot.org",
        "models.rcsb.org",
        "alphafold.ebi.ac.uk",
        "pypi.org",
        "files.pythonhosted.org",
    }
    assert erwartete_hosts <= hosts

    server = _json(CHEMPANE_PLUGIN / ".mcp.json")["mcpServers"]["chempane"]
    assert server["command"] == "uvx"
    assert server["args"] == [f"chempane=={version}"]
    assert server["env"] == {"CHEMPANE_PROFILE": "mvp"}
    readme = (CHEMPANE_PLUGIN / "README.md").read_text(encoding="utf-8")
    ohne_code = re.sub(r"```.*?```", "", readme, flags=re.S)
    assert len(ohne_code.split()) >= 40
    for host in erwartete_hosts:
        assert host in readme, host
    assert (CHEMPANE_PLUGIN / "LICENSE").is_file()


def test_plugin_startet_den_server_per_uvx():
    server = _json(PLUGIN / ".mcp.json")["mcpServers"]["chempane"]
    assert {k: server[k] for k in START} == START
    assert server["env"] == {"CHEMPANE_PROFILE": "mvp"}


def _link(muster: str) -> str:
    treffer = re.findall(muster, README)
    assert len(treffer) == 1, f"erwartet genau einen Link für {muster!r}, gefunden {treffer}"
    return treffer[0]


def test_vscode_link_dekodiert_zur_startkonfiguration():
    link = _link(r"https://vscode\.dev/redirect\?url=[^)\s]+")
    innen = unquote(parse_qs(urlparse(link).query)["url"][0])
    assert innen.startswith("vscode:mcp/install?"), innen
    config = json.loads(unquote(innen.removeprefix("vscode:mcp/install?")))
    assert config == {"name": "chempane", **START}


def test_cursor_deeplink_traegt_dieselbe_konfiguration():
    link = _link(r"cursor://anysphere\.cursor-deeplink/mcp/install\?[^`\s]+")
    query = parse_qs(urlparse(link).query)
    assert query["name"] == ["chempane"]
    assert json.loads(base64.b64decode(query["config"][0])) == START
    # Auf GitHub ist cursor:// nicht klickbar, deshalb steht die Config auch im Klartext da.
    assert '{"command":"uvx","args":["chempane"]}' in README


def test_readme_nennt_claude_code_und_codex_befehle():
    for befehl in (
        "claude plugin marketplace add chempane/chempane",
        "claude plugin install chemdraw-mcp@chemdraw-mcp",
        "codex mcp add chempane -- uvx chempane",
    ):
        assert befehl in README, befehl
