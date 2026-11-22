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
    "chempane.ph_calc",
    "chempane.solution",
    "chempane.calibration",
    "chempane.calculator",
    "chempane.calculator.titration",
    "chempane.calculator.photometry",
    "chempane.calculator.stats",
    "chempane.calculator.fat_values",
    "chempane.aufgaben.titration",
    "chempane.aufgaben.ph",
    "chempane.aufgaben.mechanismus",
    "chempane.aufgaben.loeslichkeit",
    "chempane.pk",
    "chempane.aufgaben.loesungen",
    "chempane.aufgaben.pharmakokinetik",
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
