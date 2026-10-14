"""Fehlertexte der Tools müssen beim Nutzer ankommen.

Seit mcp 2.1 ersetzt das SDK jede unerwartete Exception durch ein pauschales
"Error executing tool <name>" — nur `ToolError` behält seinen Text. Die
Fehlermeldungen dieses Servers sind aber Bedienhinweise ("Name nicht gefunden",
"offline", "Quellen gestört"): ohne sie weiß der Nutzer nicht, was hilft.
Geprüft wird über einen echten MCP-Client in-process, also genau das, was ein
Host als `CallToolResult` zu sehen bekommt.
"""

import asyncio

import pytest
from mcp import Client

from chemdraw_tool import server as srv
from chemdraw_tool.resolver import NameResolutionError


def _call(profile: str, tool: str, arguments: dict):
    async def run():
        async with Client(srv.create_server(profile)) as client:
            return await client.call_tool(tool, arguments)

    return asyncio.run(run())


def _text(result) -> str:
    return "\n".join(getattr(block, "text", "") for block in result.content)


@pytest.mark.parametrize("kind", ["not_found", "offline", "sources_down", "partial"])
def test_resolver_message_reaches_the_client(monkeypatch, kind):
    message = f"Kein Treffer für 'Xyzzolin' ({kind}) — Schreibweise prüfen."

    def fail(_name):
        raise NameResolutionError(message, name="Xyzzolin", kind=kind, attempts=[])

    monkeypatch.setattr(srv, "resolve", fail)
    result = _call("mvp", "generate_molecule", {"name_or_smiles": "Xyzzolin"})

    assert result.is_error
    assert message in _text(result)


def test_plain_value_error_text_reaches_the_client():
    """Eigene Eingabeprüfungen im Tool (raise ValueError) zählen genauso."""
    result = _call("full", "compare_molecules", {"structures": ["CCO"]})

    assert result.is_error
    assert "compare_molecules braucht 2 bis 4 Strukturen." in _text(result)


def test_unexpected_crash_stays_generic(monkeypatch):
    """Gegenprobe: ein echter Absturz verrät seinen Text weiterhin nicht."""

    def crash(_name):
        raise RuntimeError("interner Pfad /geheim")

    monkeypatch.setattr(srv, "resolve", crash)
    result = _call("mvp", "generate_molecule", {"name_or_smiles": "CCO"})

    assert result.is_error
    assert "/geheim" not in _text(result)
