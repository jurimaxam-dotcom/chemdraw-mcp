#!/usr/bin/env python3
"""Tool-Wahl-Lauf über Claude Code (`claude -p`) — ohne API-Schlüssel.

Gleiche Fälle wie promptfoo (`cases.yaml`), aber das Modell ist das, was Jay in
Claude Code/Desktop benutzt, und es sieht den Server so, wie er sich beim Verbinden
meldet (alle 20 Tools + `instructions`). Der Server ist eine Attrappe
(`stub_server.py`): es wird nichts ausgeführt, nur gemessen, WELCHES Tool gerufen wird.
Die eingebauten Claude-Code-Tools sind abgeschaltet (`--tools ""`), sonst wählt das
Modell statt eines Tools Bash.

    uv run python evals/tool-routing/run_claude.py              # alle Fälle
    uv run python evals/tool-routing/run_claude.py bare-name-de # einzelne Fälle
    MODEL=sonnet uv run python evals/tool-routing/run_claude.py # anderes Modell

Exit 0 = alle Fälle grün, 1 = mindestens ein Fall rot.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HIER = Path(__file__).parent
REPO = HIER.parent.parent
PREFIX = "mcp__chemdraw__"


def gerufene_tools(prompt: str, config: str, modell: str | None) -> tuple[list[str], str]:
    cmd = [
        "claude", "-p", prompt,
        "--mcp-config", config, "--strict-mcp-config", "--tools", "",
        # Ohne Isolation leaken Jays Hooks und CLAUDE.md (CWD-Wächter, Antwortstil) in die Wahl
        "--setting-sources", "project", "--disable-slash-commands",
        "--output-format", "stream-json", "--verbose",
        "--max-turns", "2", "--no-session-persistence",
    ]
    if modell:
        cmd += ["--model", modell]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=tempfile.gettempdir()).stdout
    namen: list[str] = []
    text = ""
    for zeile in out.splitlines():
        try:
            e = json.loads(zeile)
        except ValueError:
            continue
        if e.get("type") == "assistant":
            for b in e["message"]["content"]:
                if b.get("type") == "tool_use":
                    namen.append(b["name"].removeprefix(PREFIX))
                elif b.get("type") == "text" and not text:
                    text = b["text"]
    return namen, text


def main() -> int:
    fälle = yaml.safe_load((HIER / "cases.yaml").read_text())["cases"]
    wahl = set(sys.argv[1:])
    if wahl:
        fälle = [f for f in fälle if f["id"] in wahl]
    config = json.dumps({"mcpServers": {"chemdraw": {
        "command": "uv",
        "args": ["run", "--directory", str(REPO), "python", str(HIER / "stub_server.py")],
    }}})
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write(config)
    modell = os.environ.get("MODEL")

    def lauf(fall: dict) -> tuple[dict, list[str], str]:
        return (fall, *gerufene_tools(fall["prompt"].strip(), f.name, modell))

    rot = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for fall, tools, text in pool.map(lauf, fälle):
            fehlt = fall["expect"] not in tools
            falsch = [t for t in fall.get("forbidden", []) if t in tools]
            ok = not fehlt and not falsch
            rot += not ok
            print(f"{'✔' if ok else '✘'} {fall['id']:<28} gerufen: {tools or '—'}")
            if not ok:
                if not tools:
                    print(f"    Modell schrieb stattdessen: {' '.join(text.split())[:200]}")
                print(f"    erwartet {fall['expect']}, verboten {falsch or '—'}\n    warum: {' '.join(fall['why'].split())}")
    print(f"\n{len(fälle) - rot}/{len(fälle)} grün")
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main())
