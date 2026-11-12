"""`evals/panel-beispiele.json` muss zu den Panel-Tools des Standardprofils passen.

Die Datei speist zwei Läufe außerhalb des Gates, die den Handtest in Claude Desktop
ersetzen, wo es geht: `test:inspector` (Panel hinter dem offiziellen MCP Inspector)
und `run_claude.py --echt` (Claude Code ruft den echten Server). Fehlt dort ein
Panel-Tool, wird es still nie geprüft — deshalb hält dieser Test die Liste ohne
Netz synchron, so wie `test_eval_cases.py` die Routing-Fälle.
"""

import asyncio
import json
from pathlib import Path

from chemdraw_tool.server import create_server

DATEI = Path(__file__).resolve().parents[1] / "evals" / "panel-beispiele.json"


def _beispiele() -> dict:
    return json.loads(DATEI.read_text(encoding="utf-8"))


def _panel_tools() -> dict:
    tools = asyncio.run(create_server("mvp").list_tools())
    return {t.name: t for t in tools if ((t.meta or {}).get("ui") or {}).get("resourceUri")}


def test_jedes_panel_tool_hat_ein_beispiel_und_kein_fremdes():
    assert set(_beispiele()) == set(_panel_tools())


def test_beispiel_hat_argumente_und_prompt_oder_einen_grund_zum_auslassen():
    for name, b in _beispiele().items():
        if "auslassen" in b:
            assert b["auslassen"].strip(), f"{name}: leerer Grund"
            assert "args" not in b and "prompt" not in b, f"{name}: ausgelassen, aber mit Beispiel"
            continue
        assert b["prompt"].strip(), f"{name}: Prompt fehlt"
        assert b["bereit"].strip(), f"{name}: CSS-Selektor `bereit` fehlt"
        pflicht = set(_panel_tools()[name].input_schema.get("required") or [])
        assert pflicht <= set(b["args"]), f"{name}: Pflichtfelder fehlen: {pflicht - set(b['args'])}"


def test_schreibende_fremdwirkung_bleibt_draussen():
    # export_anki_deck ändert Notizen in einem laufenden Anki — nie aus einem Testlauf
    assert "auslassen" in _beispiele()["export_anki_deck"]
