#!/usr/bin/env python3
"""Attrappen-Server für den Tool-Wahl-Lauf über `claude -p`.

Bietet dem Modell die ECHTEN Tool-Definitionen und die echten `instructions` des
Servers an (beides entscheidet über die Wahl), führt aber nichts aus: jeder Aufruf
wird nur quittiert. So schreibt der Lauf nichts nach ~/ChemDraw-Output und braucht
weder Netz noch RDKit-Rechenzeit.
"""

from __future__ import annotations

import asyncio

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from chemdraw_tool.payloads import DatabasePayload, DatabaseRow, DatabaseSource
from chemdraw_tool.result_budget import _compact
from chemdraw_tool.server import mcp as echt


async def _tools(_ctx, _params) -> types.ListToolsResult:
    # Ohne outputSchema: die Attrappe liefert kein structuredContent, und Claude Code
    # machte sonst aus jeder Quittung einen Fehler („has an output schema but did not
    # return structured content“, gemessen 14.11.2026). Das Modell sieht vom Schema
    # ohnehin nur Name, Beschreibung und Eingabeschema — die bleiben echt.
    tools = [t.model_copy(update={"output_schema": None}) for t in await echt.list_tools()]
    return types.ListToolsResult(tools=tools)


# Eine nackte Quittung liest das Modell als „es kam nichts“: beim Datenblatt rief es
# danach lookup und generate_molecule hinterher (lookup-data-sheet, drei Läufe rot am
# 13.11.2026). Wo der echte Server Inhalt liefert, den das Modell als Antwort braucht,
# liefert die Attrappe deshalb erfundene Werte in der echten Form: dasselbe Payload-Modell,
# derselbe kompakte JSON-Textblock wie `result_budget` (kein Prosatext, den der echte
# Server nie schickt — sonst wäre das Messgerät passend gemacht).
def _datenblatt() -> str:
    zeilen = [("CAS", "0-00-0"), ("InChIKey", "ATTRAPPE-ATTRAPPE-N"), ("Molecular formula", "C0H0"),
              ("Molar mass", "0.00 g/mol"), ("XLogP", "0.0"), ("Melting point", "0 °C")]
    quelle = DatabaseSource(type="PubChem", source="PubChem (Attrappe)", url="https://example.invalid/",
                            rows=[DatabaseRow(key=k, val=v) for k, v in zeilen])
    ghs = DatabaseSource(type="GHS", source="PubChem GHS (Attrappe)", url="https://example.invalid/",
                         status="empty", note="No GHS classification on record.")
    payload = DatabasePayload(name="(Attrappe)", molecule_svg="<svg/>", sources=[quelle, ghs])
    return _compact(payload.model_dump())


_ANTWORTEN = {"lookup_molecule_data": _datenblatt()}


async def _call(_ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    text = _ANTWORTEN.get(params.name, f"(Attrappe) {params.name} aufgerufen")
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)])


# mcp 2: Handler gehen in den Konstruktor, die Dekoratoren gibt es nicht mehr.
server = Server(
    "chemdraw",
    instructions=echt.instructions,
    on_list_tools=_tools,
    on_call_tool=_call,
)


async def main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
