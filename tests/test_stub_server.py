"""Die Attrappe des Routing-Laufs muss dem Modell dieselbe Wahl zeigen wie der echte Server.

Gemessen 14.11.2026: Alle Tools tragen ein outputSchema. Die Attrappe antwortete nur
mit Text, und Claude Code machte aus jeder Antwort den Fehler „has an output schema
but did not return structured content“ — das Modell sah nach jedem Aufruf einen
Fehler und rief im zweiten Zug nach (Datenblatt → generate_molecule).
"""

import asyncio
import importlib.util
import json
from pathlib import Path

from mcp import types

from chemdraw_tool.server import create_server

STUB = Path(__file__).resolve().parents[1] / "evals" / "tool-routing" / "stub_server.py"


def _stub():
    spec = importlib.util.spec_from_file_location("stub_server", STUB)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_attrappe_zeigt_name_beschreibung_und_eingabeschema_des_echten_servers():
    stub = _stub()
    echt = {t.name: t for t in asyncio.run(create_server("mvp").list_tools())}
    angeboten = {t.name: t for t in asyncio.run(stub._tools(None, None)).tools}
    assert angeboten.keys() == echt.keys()
    for name, tool in angeboten.items():
        assert tool.description == echt[name].description
        assert tool.input_schema == echt[name].input_schema


def test_attrappe_verspricht_kein_strukturiertes_ergebnis_das_sie_nicht_liefert():
    stub = _stub()
    for tool in asyncio.run(stub._tools(None, None)).tools:
        assert tool.output_schema is None, tool.name


def test_datenblatt_der_attrappe_hat_die_form_des_echten_servers():
    stub = _stub()
    params = types.CallToolRequestParams(name="lookup_molecule_data", arguments={"name": "Ibuprofen"})
    result = asyncio.run(stub._call(None, params))
    payload = json.loads(result.content[0].text)
    assert payload["type"] == "database"
    assert {s["type"] for s in payload["sources"]} >= {"PubChem", "GHS"}
