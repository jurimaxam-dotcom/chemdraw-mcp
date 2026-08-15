#!/usr/bin/env python3
"""Kippt die echten Tool-Definitionen des Servers nach JSON.

Fuer den Eval-Lauf muessen dem Modell ALLE Tools angeboten werden, nicht nur
das jeweils erwartete — sonst kann es gar nicht danebengreifen und der Test ist
tautologisch gruen. Genau diese Falle ist der haeufigste Fehler in
Tool-Auswahl-Suiten.

Ausgabe ist das Anthropic-Format ({name, description, input_schema}), weil der
promptfoo-Anthropic-Provider es unveraendert durchreicht.

    uv run python evals/tool-routing/export_tools.py > evals/tool-routing/tools.json
"""

from __future__ import annotations

import asyncio
import json
import sys


async def _collect() -> list[dict]:
    from chemdraw_tool.server import mcp

    tools = await mcp.list_tools()
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema,
        }
        for t in tools
    ]


def main() -> int:
    tools = asyncio.run(_collect())
    json.dump(tools, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    print(f"{len(tools)} Tools exportiert", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
