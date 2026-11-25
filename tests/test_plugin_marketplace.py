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
CHEMPANE_PLUGIN = ROOT / "plugins" / "chempane"
START = {"command": "uvx", "args": ["chempane"]}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_marketplace_listet_die_plugins_aus_den_unterordnern():
    market = _json(ROOT / ".claude-plugin" / "marketplace.json")
    assert market["name"] == "chempane"
    assert market["owner"] == {"name": "chempane"}
    by_name = {e["name"]: e for e in market["plugins"]}
    assert set(by_name) == {"chempane"}
    # Unterordner statt "./": sonst landet das ganze Repo im Plugin-Cache.
    assert by_name["chempane"]["source"] == "./plugins/chempane"
    # Eintragsname = Manifestname, sonst findet `install <name>@…` das Plugin nicht.
    assert _json(CHEMPANE_PLUGIN / ".claude-plugin" / "plugin.json")["name"] == "chempane"
    assert not (ROOT / "plugins" / "chemdraw-mcp").exists()


def test_chempane_plugin_erfuellt_directory_anforderungen():
    manifest = _json(CHEMPANE_PLUGIN / ".claude-plugin" / "plugin.json")
    # Der Anzeigename trägt das Suchwort; `name` bleibt die dauerhafte Kennung.
    assert manifest["displayName"] == "chempane: Chemistry Drawing"
    # Die Suche im Directory ist nicht dokumentiert: das Suchwort steht deshalb in jedem Feld, das sie lesen könnte.
    assert manifest["description"].startswith("Chemistry in Claude: ")
    assert {"chemistry", "molecule", "chemical-structure", "rdkit", "smiles"} <= set(manifest["keywords"])
    # Ohne Verified-Status blockt das Portal zusätzliche Felder wie `network`.
    assert "network" not in manifest
    assert manifest["documentationUrl"] == "https://github.com/chempane/chempane/blob/main/docs/remote-connector.md"
    assert manifest["termsOfServiceUrl"] == "https://github.com/chempane/chempane/blob/main/docs/remote-terms.md"
    assert manifest["supportUrl"] == "https://github.com/chempane/chempane/issues"
    assert manifest["privacyPolicyUrl"] == "https://mcp.chempane.com/privacy"
    market = _json(ROOT / ".claude-plugin" / "marketplace.json")["plugins"][0]
    assert market["description"] == manifest["description"]
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
    # Portal-Scanner extrahiert druckbare Zeichen aus dem Bild und prüft sie auf Shell-Muster.
    printable_concat = bytes(c for c in raw if 32 <= c < 127).decode("ascii")
    printable_spaced = re.sub(rb"[^ -~]+", b" ", raw).decode("ascii")
    shell_pat = re.compile(
        r"(?:curl|wget|fetch|iwr|irm|iex|bash|zsh|dash|ksh|pwsh|powershell|ncat|eval|exec|base64|chmod|http|ftp|\bnc\b|\$\(|sh)",
        re.I,
    )
    assert not shell_pat.search(printable_concat), shell_pat.findall(printable_concat)
    assert not shell_pat.search(printable_spaced), shell_pat.findall(printable_spaced)

    # Remote-MCP-Server statt lokalem uvx (lokale MCP-Server sind nur für Verified-Orgs erlaubt).
    server = _json(CHEMPANE_PLUGIN / ".mcp.json")["mcpServers"]["chempane"]
    assert server == {
        "type": "http",
        "url": "https://mcp.chempane.com/mcp",
    }
    readme = (CHEMPANE_PLUGIN / "README.md").read_text(encoding="utf-8")
    ohne_code = re.sub(r"```.*?```", "", readme, flags=re.S)
    assert len(ohne_code.split()) >= 40
    for eintrag in (
        "https://mcp.chempane.com/mcp",
        "https://mcp.chempane.com/privacy",
        "pubchem.ncbi.nlm.nih.gov",
        "cactus.nci.nih.gov",
        "claude plugin marketplace add chempane/chempane",
        "claude plugin install chempane@chempane",
    ):
        assert eintrag in readme, eintrag
    assert "uvx chempane==" not in readme
    # Das Plugin-README beschreibt nur das Remote-Plugin (keine Aufforderung zum lokalen Server-Install
    # und keine Werkzeuge, die das gehostete Plugin nicht enthält — sonst Portal-Blocker).
    for verboten in ("Local server", "install the local server", "3D conformers", "Anki decks"):
        assert verboten not in readme, verboten
    assert (CHEMPANE_PLUGIN / "LICENSE").is_file()


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
        "claude plugin install chempane@chempane",
        "codex mcp add chempane -- uvx chempane",
    ):
        assert befehl in README, befehl
