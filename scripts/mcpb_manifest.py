#!/usr/bin/env python3
"""Manifest je Konnektor-Bundle: `mvp` = mcpb/manifest.json, `pharma` = Pharma-Variante.

Claude Desktop leitet die Extension-ID aus author + name ab
(local.mcpb.<author>.<name>). Zwei Bundles aus demselben Starter (server/run.sh,
dieselbe Installation unter chemdraw-mcp-bundle/env-<version>): `chemdraw-mcp`
mit dem Standardprofil und `chemdraw-mcp-pharma` mit dem Profil `pharma` (seit
16.11.2026 nur die Zusatz-Tools; vorher das Vollprofil, und mit beiden
Extensions sah das Modell 18 Tools doppelt). Beide mit festem Profil in
server.mcp_config.env (und demselben user_config-Häkchen für den
SMILES-Abgleich). Eine Quelle (die Basisdatei), damit Version, Autor, Lizenz
und Starter nie auseinanderlaufen. Ein Bündel für `full` gibt es nicht: die
zwei zusammen ergeben es.

Aufruf:  python scripts/mcpb_manifest.py mvp|pharma   → JSON auf stdout
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
        "Pharmacy add-on to ChemDraw MCP: calculators for solutions, content "
        "determination and pharmacokinetics, plus calibration, pharmacology and "
        "substrate-scope figures as PNG/SVG files with an interactive panel."
    ),
    "long_description": (
        "The second connector of chemdraw-mcp. It adds 7 tools to the default "
        "ChemDraw MCP extension and repeats none of them: the substrate-scope figure "
        "(generate_scope_table), the calibration curve with LOD/LOQ "
        "(generate_calibration_curve), plasma-concentration and dose-response curves "
        "(generate_pk_curve, generate_dose_response), and calculators for solutions "
        "(calculate_solution), content determination per Ph. Eur. (calculate_content) "
        "and pharmacokinetics (calculate_pharmacokinetics). Structures, reactions, "
        "spectra, pH and Anki decks come from the default extension — enable both; "
        "together they offer every tool, and they share one installation. The bundle "
        "is a launcher: on first start it installs chemdraw-mcp from PyPI with uv, "
        "every file checked against hashes pinned at release time (a pinned, "
        "checksum-verified uv is downloaded if none is installed). Rendering and "
        "calculations run locally; name resolution uses online databases. A SMILES "
        "or InChI you type is not sent to them unless you turn on the SMILES lookup "
        "setting. Not affiliated with Revvity/ChemDraw."
    ),
}


def manifest(profile: str) -> dict:
    base = json.loads(BASE.read_text(encoding="utf-8"))
    if profile == "mvp":
        return base
    if profile != "pharma":
        raise ValueError(f"profile must be 'mvp' or 'pharma', was {profile!r}")
    variant = json.loads(json.dumps(base))
    variant.update(PHARMA)
    # Nur das Profil tauschen: der Rest von env (E12: das SMILES-Häkchen) gilt für beide.
    variant["server"]["mcp_config"]["env"]["CHEMPANE_PROFILE"] = "pharma"
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
