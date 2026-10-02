"""Der Rechenkern muss ohne Zeichen-Stack importierbar sein.

Grund (02.10.2026): Das Produkt „Praktikumsrechner“ soll den Rechenkern per
Pyodide im Browser laufen lassen — ohne Server. matplotlib und RDKit gibt es
dort nicht bzw. nur schwer; ein einziger Import davon im Rechenweg legt den
ganzen Rechner lahm. Deshalb: in einem frischen Prozess importieren und
nachsehen, was mitgezogen wurde.
"""

import subprocess
import sys

import pytest

RECHENKERN = [
    "chemdraw_tool.ph_calc",
    "chemdraw_tool.solution",
    "chemdraw_tool.calibration",
    "chemdraw_tool.calculator",
    "chemdraw_tool.calculator.titration",
    "chemdraw_tool.calculator.photometry",
    "chemdraw_tool.calculator.stats",
    "chemdraw_tool.calculator.fat_values",
]
VERBOTEN = ["matplotlib", "rdkit", "mcp", "requests"]


@pytest.mark.parametrize("modul", RECHENKERN)
def test_rechenkern_zieht_keinen_zeichen_stack(modul):
    code = (
        "import importlib, sys\n"
        f"importlib.import_module({modul!r})\n"
        f"print(','.join(m for m in {VERBOTEN!r} if m in sys.modules))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert out == "", f"{modul} zieht {out} mit"
