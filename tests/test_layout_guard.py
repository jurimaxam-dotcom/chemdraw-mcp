"""Layout-Wächter: wo RDKit die Atome hinlegt, ist eingefroren — getrennt vom Renderer.

Die Golden-SVGs (test_render_golden.py) bekommen seit 05.11.2026 feste
Koordinaten und prüfen nur noch, WIE gezeichnet wird. Dieser Test prüft das
andere Halbe: WO `generate_2d` die Atome hinlegt, für eine kleine Molekülauswahl.
Ein rdkit-Update, das Strukturen dreht oder spiegelt (2026.9 spiegelt Aspirin
und Glucose), ändert das Bild, das Nutzer bekommen — es soll auffallen, nicht
durchrutschen.

Bewusst ein direkter Koordinatenvergleich, nicht spiegelungsinvariant: eine
Spiegelung ist für Nutzer sichtbar.

Rot heißt: Layout hat sich geändert. Dann ansehen und bewusst
bestätigen, im selben Commit wie der Versionssprung:
    UPDATE_LAYOUT=1 uv run pytest tests/test_layout_guard.py
und die Bilder vorher/nachher anschauen (Commit-Nachricht nennt, was sich
gedreht hat). Niemals bestätigen, ohne hingesehen zu haben.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from rdkit import Chem

from chemdraw_tool.generator import generate_2d

REFERENCE = Path(__file__).parent / "__fixtures__" / "layout.reference.json"
TOLERANCE = 0.02  # Å-Einheiten von Compute2DCoords; Rundung zwischen Plattformen

# Ring, Kette, Zucker mit Stereo, kondensierter Heterozyklus, Piperidin —
# gemessen 05.11.: unter rdkit 2026.9 ändern sich Aspirin, Ibuprofen, Benzol,
# Glucose; Koffein, Methylphenidat, Ethanol bleiben.
PROBES = {
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "benzene": "c1ccccc1",
    "glucose": "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
    "caffeine": "Cn1cnc2c1c(=O)n(C)c(=O)n2C",
    "methylphenidate": "COC(=O)C(c1ccccc1)C1CCCCN1",
    "ethanol": "CCO",
}


def _layout(smiles: str) -> list[list[float]]:
    conf = generate_2d(Chem.MolFromSmiles(smiles)).GetConformer()
    return [
        [round(conf.GetAtomPosition(i).x, 3), round(conf.GetAtomPosition(i).y, 3)]
        for i in range(conf.GetNumAtoms())
    ]


def _write_reference() -> None:
    import rdkit

    data = {
        "rdkit": rdkit.__version__,
        "probes": {name: {"smiles": s, "coords": _layout(s)} for name, s in PROBES.items()},
    }
    REFERENCE.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")


if os.environ.get("UPDATE_LAYOUT") == "1":
    _write_reference()


def test_reference_covers_exactly_the_probes():
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    assert sorted(ref["probes"]) == sorted(PROBES)
    for name, smiles in PROBES.items():
        assert ref["probes"][name]["smiles"] == smiles


@pytest.mark.parametrize("name", sorted(PROBES))
def test_2d_layout_matches_the_frozen_reference(name: str):
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    expected = ref["probes"][name]["coords"]
    actual = _layout(PROBES[name])
    assert len(actual) == len(expected), f"{name}: Atomanzahl {len(actual)} ≠ {len(expected)}"
    worst = max(
        max(abs(a - e) for a, e in zip(pa, pe)) for pa, pe in zip(actual, expected)
    )
    assert worst <= TOLERANCE, (
        f"{name}: 2D-Layout weicht um bis zu {worst:.3f} ab (Referenz aus rdkit "
        f"{ref['rdkit']}). Ein rdkit-Update dreht/spiegelt die Zeichnung, die Nutzer "
        "bekommen. Bild ansehen, dann bewusst bestätigen: "
        "UPDATE_LAYOUT=1 uv run pytest tests/test_layout_guard.py"
    )
