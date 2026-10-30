#!/usr/bin/env python3
"""Tool-Wahl-Lauf über Claude Code (`claude -p`) — ohne API-Schlüssel.

Gleiche Fälle wie promptfoo (`cases.yaml`), aber das Modell ist das, was Jay in
Claude Code/Desktop benutzt, und es sieht den Server so, wie er sich beim Verbinden
meldet (die Tools des gewählten Profils + `instructions`). Der Server ist eine Attrappe
(`stub_server.py`): es wird nichts ausgeführt, nur gemessen, WELCHES Tool gerufen wird.
Die eingebauten Claude-Code-Tools sind abgeschaltet (`--tools ""`), sonst wählt das
Modell statt eines Tools Bash.

    uv run python evals/tool-routing/run_claude.py              # alle Fälle
    uv run python evals/tool-routing/run_claude.py bare-name-de # einzelne Fälle
    MODEL=sonnet uv run python evals/tool-routing/run_claude.py # anderes Modell

Exit 0 = alle Fälle grün, 1 = mindestens ein Fall rot.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HIER = Path(__file__).parent
REPO = HIER.parent.parent
PREFIX = "mcp__chemdraw__"


def gerufene_tools(prompt: str, config: str, modell: str | None, cwd: str) -> tuple[list[str], str]:
    cmd = [
        "claude", "-p", prompt,
        "--mcp-config", config, "--strict-mcp-config", "--tools", os.environ.get("BUILTIN_TOOLS", ""),
        # Ohne Isolation leaken Jays Hooks und CLAUDE.md (CWD-Wächter, Antwortstil) in die Wahl
        "--setting-sources", "project", "--disable-slash-commands",
        "--output-format", "stream-json", "--verbose",
        "--max-turns", "2", "--no-session-persistence",
    ]
    if modell:
        cmd += ["--model", modell]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=cwd).stdout
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
    if text.startswith("Failed to authenticate"):
        # Kein Messwert: ein abgelaufener Login darf nicht als „Modell wählt kein Tool" erscheinen
        raise SystemExit(f"ABBRUCH (kein Ergebnis, kein roter Fall): {text}\nAnmelden: `claude` im Terminal starten und /login ausführen.")
    return namen, text


def select_cases(cases: list[dict], offered: set[str], selection: set[str]) -> list[dict]:
    """Explizite Auswahl validieren, sonst nur angebotene Werkzeuge messen."""
    by_id = {case["id"]: case for case in cases}
    unknown = selection - by_id.keys()
    if unknown:
        raise ValueError("Unbekannte Fall-IDs: " + ", ".join(sorted(unknown)))
    disabled = {name for name in selection if by_id[name]["expect"] not in offered}
    if disabled:
        raise ValueError("Im gewählten Profil deaktivierte Fälle: " + ", ".join(sorted(disabled)))
    selected = [
        case for case in cases
        if case["expect"] in offered and (not selection or case["id"] in selection)
    ]
    if not selected:
        raise ValueError("Keine passenden Eval-Fälle für die angebotenen Tools.")
    return selected


def main() -> int:
    from chemdraw_tool.server import mcp

    fälle = yaml.safe_load((HIER / "cases.yaml").read_text())["cases"]
    offered = {tool.name for tool in asyncio.run(mcp.list_tools())}
    try:
        fälle = select_cases(fälle, offered, set(sys.argv[1:]))
    except ValueError as error:
        print(f"ABBRUCH: {error}", file=sys.stderr)
        return 2
    config = json.dumps({"mcpServers": {"chemdraw": {
        "command": "uv",
        "args": ["run", "--directory", str(REPO), "python", str(HIER / "stub_server.py")],
        "env": {"CHEMDRAW_PROFILE": os.environ.get("CHEMDRAW_PROFILE", "mvp")},
    }}})
    # Eigener Ordner (0700) statt des geteilten Temp-Ordners: `--setting-sources project`
    # liest .claude/settings.json aus dem CWD — in /tmp könnte ein Mitnutzer dort
    # Hooks hinterlegen (Sicherheitsscan F2).
    arbeit = tempfile.mkdtemp(prefix="tool-routing-")
    try:
        config_pfad = Path(arbeit) / "mcp.json"
        config_pfad.write_text(config)
        return _messen(fälle, str(config_pfad), arbeit)
    finally:
        shutil.rmtree(arbeit, ignore_errors=True)


def _messen(fälle: list[dict], config: str, cwd: str) -> int:
    modell = os.environ.get("MODEL")

    def lauf(fall: dict) -> tuple[dict, list[str], str]:
        return (fall, *gerufene_tools(fall["prompt"].strip(), config, modell, cwd))

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
