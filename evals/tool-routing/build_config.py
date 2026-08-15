#!/usr/bin/env python3
"""Baut aus cases.yaml + tools.json eine fertige promptfoo-Konfiguration.

Handgepflegtes YAML fuer 22 Faelle x 20 Tools waere sofort veraltet. Diese
Datei ist der Generator: sie liest die Faelle, haengt die echten
Tool-Definitionen an und schreibt `promptfooconfig.yaml`.

    uv run python evals/tool-routing/export_tools.py > evals/tool-routing/tools.json
    uv run python evals/tool-routing/build_config.py
    npx promptfoo@latest eval -c evals/tool-routing/promptfooconfig.yaml

Warum `contains` statt des eingebauten `tool-call-f1`-Scorers: dessen
Dokumentation zeigt die Tools nur im `tools:`-Block, und ob er sie auch aus
einem MCP-Block liest, war nicht verifizierbar. Der Provider gibt den
`tool_use`-Block als String zurueck, deshalb pruefen wir darauf direkt — das
ist belegt und haelt auch, wenn sich der Scorer aendert.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
MODEL = "claude-opus-5"


def main() -> int:
    cases = yaml.safe_load((HERE / "cases.yaml").read_text(encoding="utf-8"))["cases"]
    tools_file = HERE / "tools.json"
    if not tools_file.exists():
        raise SystemExit(
            "tools.json fehlt — erst 'uv run python evals/tool-routing/"
            "export_tools.py > evals/tool-routing/tools.json' laufen lassen."
        )
    tools = json.loads(tools_file.read_text(encoding="utf-8"))

    tests = []
    for case in cases:
        asserts = [
            {
                "type": "contains",
                "value": f'"name":"{case["expect"]}"',
                "metric": "richtiges-Tool",
            }
        ]
        for forbidden in case["forbidden"]:
            asserts.append(
                {
                    "type": "not-contains",
                    "value": f'"name":"{forbidden}"',
                    "metric": "kein-Fehlgriff",
                }
            )
        tests.append(
            {
                "description": f'{case["id"]}: {case["why"].strip().splitlines()[0]}',
                "vars": {"frage": case["prompt"].strip()},
                "assert": asserts,
            }
        )

    config = {
        "description": (
            "chemdraw-mcp — Prompt zu Tool. Alle 20 Tools sind angeboten, "
            "damit ein Fehlgriff ueberhaupt moeglich ist."
        ),
        "providers": [
            {
                "id": f"anthropic:messages:{MODEL}",
                "config": {"tools": tools, "max_tokens": 1024},
            }
        ],
        "prompts": ["{{frage}}"],
        "tests": tests,
    }

    out = HERE / "promptfooconfig.yaml"
    out.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"{out.name} geschrieben: {len(tests)} Faelle, {len(tools)} Tools angeboten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
