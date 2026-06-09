"""Visual UI test — generates payload, renders in headless browser, takes screenshot.

Usage:
    uv run python tests/screenshot_ui.py mechanism sn2
    uv run python tests/screenshot_ui.py mechanism fischer_ester
    uv run python tests/screenshot_ui.py molecule aspirin
    uv run python tests/screenshot_ui.py reaction

Screenshots land in /tmp/chem-ui-<type>.png
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

UI_DIR = Path(__file__).resolve().parent.parent / "chemdraw_tool" / "ui"
SCREENSHOT_DIR = Path("/tmp")


def _generate_payload(payload_type: str, args: list[str]) -> dict:
    if payload_type == "mechanism":
        from chemdraw_tool.server import generate_mechanism

        reaction_type = args[0] if args else "sn2"
        substrates = args[1:] if len(args) > 1 else _default_substrates(reaction_type)
        result = generate_mechanism(reaction_type=reaction_type, substrates=substrates)
        return result.model_dump()

    if payload_type == "molecule":
        from chemdraw_tool.server import generate_molecule

        name = args[0] if args else "aspirin"
        result = generate_molecule(name_or_smiles=name)
        return result.model_dump()

    if payload_type == "reaction":
        from chemdraw_tool.server import generate_reaction

        result = generate_reaction(
            reactants=["ethanol", "acetic acid"],
            products=["ethyl acetate", "water"],
            conditions="H2SO4, heat",
        )
        return result.model_dump()

    raise ValueError(f"Unbekannter Typ: {payload_type}")


def _default_substrates(reaction_type: str) -> list[str]:
    defaults = {
        "sn2": ["CCBr", "[OH-]"],
        "sn1": ["CC(C)(C)Br", "O"],
        "fischer_ester": ["CC(=O)O", "CO"],
    }
    return defaults.get(reaction_type, ["CCBr", "[OH-]"])


def _start_server(directory: Path, port: int) -> HTTPServer:
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(directory), **kw)

        def log_message(self, *_a):
            pass

    server = HTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def screenshot(payload_type: str, args: list[str]) -> Path:
    from playwright.sync_api import sync_playwright

    payload = _generate_payload(payload_type, args)
    port = 18923
    server = _start_server(UI_DIR, port)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            color_scheme = "dark" if os.environ.get("CHEM_UI_DARK") else "light"
            page = browser.new_page(
                viewport={"width": 640, "height": 800}, color_scheme=color_scheme
            )
            page.goto(f"http://127.0.0.1:{port}/test-harness.html")
            page.wait_for_selector("#ui", state="attached")
            time.sleep(1)

            page.evaluate(f"""() => {{
                const iframe = document.getElementById('ui');
                iframe.contentWindow.postMessage({{
                    jsonrpc: '2.0',
                    method: 'ontoolresult',
                    params: {{ structuredContent: {json.dumps(payload)} }}
                }}, '*');
            }}""")
            time.sleep(1.5)

            out = SCREENSHOT_DIR / f"chem-ui-{payload_type}.png"
            page.screenshot(path=str(out))
            browser.close()
    finally:
        server.shutdown()

    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    ptype = sys.argv[1]
    pargs = sys.argv[2:]
    path = screenshot(ptype, pargs)
    print(f"Screenshot: {path}")
