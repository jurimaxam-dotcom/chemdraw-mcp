#!/usr/bin/env python3
"""Entwicklungsstarter: derselbe Server über Streamable HTTP, nur auf 127.0.0.1.

Zweck: Hosts, die nur HTTP sprechen — der Deep-Link des MCP Inspector
(`npm --prefix chemdraw_tool/ui run test:inspector`) und `basic-host` aus ext-apps.
Bewusst KEIN Einstiegspunkt des Wheels und kein Modus von `chemdraw-tool-server`:
der Server schreibt Dateien und hat mit `export_anki_deck` ein destruktives Tool,
HTTP ohne Anmeldung ist deshalb kein Produktmerkmal. Die Adresse ist fest Loopback.

    uv run python scripts/dev_http.py            # http://127.0.0.1:8791/mcp (8765 gehört AnkiConnect)
    PORT=9000 uv run python scripts/dev_http.py
"""

import os

from chemdraw_tool.server import create_server

if __name__ == "__main__":
    create_server(os.environ.get("CHEMDRAW_PROFILE", "mvp")).run(
        transport="streamable-http", host="127.0.0.1", port=int(os.environ.get("PORT", "8791"))
    )
