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

from chemdraw_tool.server import mcp as echt


async def _tools(_ctx, _params) -> types.ListToolsResult:
    return types.ListToolsResult(tools=await echt.list_tools())


async def _call(_ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    text = f"(Attrappe) {params.name} aufgerufen"
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
