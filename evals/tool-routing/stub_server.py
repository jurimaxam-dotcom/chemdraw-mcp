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

server = Server("chemdraw", instructions=echt.instructions)


@server.list_tools()
async def _tools() -> list[types.Tool]:
    return await echt.list_tools()


@server.call_tool()
async def _call(name: str, arguments: dict) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"(Attrappe) {name} aufgerufen")]


async def main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
