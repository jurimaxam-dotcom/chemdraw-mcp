#!/usr/bin/env python3
"""Manifest je Konnektor-Bundle: `mvp` = mcpb/manifest.json, `full` = Pharma-Variante.

Claude Desktop leitet die Extension-ID aus author + name ab
(local.mcpb.<author>.<name>). Zwei Bundles aus demselben Starter (server/run.sh,
dieselbe Installation unter chemdraw-mcp-bundle/env-<version>): `chemdraw-mcp`
mit dem Standardprofil und `chemdraw-mcp-pharma` mit dem Vollprofil, beide mit
festem Profil in server.mcp_config.env (und demselben
user_config-Häkchen für den SMILES-Abgleich). Eine Quelle (die Basisdatei), damit
Version, Autor, Lizenz und Starter nie auseinanderlaufen.

Aufruf:  python scripts/mcpb_manifest.py mvp|full   → JSON auf stdout
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "mcpb" / "manifest.json"

PHARMA = {
    "name": "chemdraw-mcp-pharma",
    "display_name": "ChemDraw MCP Pharma (unofficial)",
    "description": (
        "The full profile of ChemDraw MCP: structures, reactions and lab graphics plus "
        "pharmacy calculators, calibration and pharmacology curves, as PNG/SVG files "
        "with an interactive panel."
    ),
    "long_description": (
        "The second connector of chemdraw-mcp. It runs the full profile: 25 tools in "
        "five areas (draw, lab graphics, look up, calculate, Anki) — everything the "
        "default ChemDraw MCP extension has, plus the substrate-scope figure, the "
        "calibration curve with LOD/LOQ, plasma-concentration and dose-response "
        "curves, and calculators for solutions, content determination (Ph. Eur.) and "
        "pharmacokinetics. Install it next to the default extension and pick one "
        "connector per chat; both share one installation. The bundle is a launcher: "
        "on first start it installs chemdraw-mcp from PyPI with uv, every file "
        "checked against hashes pinned at release time (a pinned, checksum-verified "
        "uv is downloaded if none is installed). Structure rendering runs locally; "
        "name resolution and data sheets use online databases. A SMILES or InChI you "
        "type is not sent to them unless you turn on the SMILES lookup setting; data "
        "sheets ask by its InChIKey. Not affiliated with Revvity/ChemDraw."
    ),
}


def manifest(profile: str) -> dict:
    base = json.loads(BASE.read_text(encoding="utf-8"))
    if profile == "mvp":
        return base
    if profile != "full":
        raise ValueError(f"profile must be 'mvp' or 'full', was {profile!r}")
    variant = json.loads(json.dumps(base))
    variant.update(PHARMA)
    # Nur das Profil tauschen: der Rest von env (E12: das SMILES-Häkchen) gilt für beide.
    variant["server"]["mcp_config"]["env"]["CHEMDRAW_PROFILE"] = "full"
    return variant


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        data = manifest(argv[1])
    except ValueError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
