"""Regressionsschutz für den PYTHON-Renderer — die Lücke, die der e2e-Test lässt.

Der committete Pixel-Snapshot (`ui/src/utils/__fixtures__/aspirin.expected.png`)
prüft die JS-Rasterung eines eingefrorenen SVG. Er sagt nichts darüber, ob
`svg_renderer`/`image_export` heute noch dasselbe SVG erzeugen — die Fixture
`aspirin.fill.svg` ist ein alter Capture (stroke-width 2.5, aus der Zeit vor
BOND_LINE_WIDTH = 1.5). Eine Änderung am Default-Rendering wäre also durch das
Gate gerutscht.

Diese Datei schließt das: die Default-Ausgabe wird gegen eingefrorene Bytes
verglichen.

WANN DIE GOLDEN-DATEIEN NEU ERZEUGT WERDEN DÜRFEN: nur bei einer ABSICHTLICHEN
Rendering-Änderung oder einem RDKit-Update — und dann bewusst, mit Sichtprüfung
des Ergebnisses. Niemals, um einen roten Test verschwinden zu lassen; genau
dafür ist er da. Erzeugen mit:
    uv run python -c "from tests.test_render_golden import _write_goldens; _write_goldens()"
"""

from __future__ import annotations

from pathlib import Path

import pytest
from rdkit import Chem

from chemdraw_tool.generator import generate_2d
from chemdraw_tool.image_export import render_molecule_svg
from chemdraw_tool.svg_renderer import render_svg

FIXTURES = Path(__file__).parent / "__fixtures__"

# Aspirin: klein genug für eine lesbare Golden-Datei, aber mit Ring, Doppel-
# bindungen, Heteroatomen und Atomlabels — die Merkmale, an denen sich eine
# Rendering-Änderung zeigt.
PROBE_SMILES = "CC(=O)Oc1ccccc1C(=O)O"

def _normalise(svg: str) -> str:
    """Entfernt, was sich ohne Rendering-Änderung unterscheiden darf."""
    return svg.replace("\r\n", "\n").strip()


def _probe_mol():
    return generate_2d(Chem.MolFromSmiles(PROBE_SMILES))


def _render_ui_preview() -> str:
    return render_svg(_probe_mol(), fill_container=True)


def _render_export() -> str:
    return render_molecule_svg(_probe_mol(), legend="Aspirin")


CASES = {
    "aspirin.ui-preview.golden.svg": _render_ui_preview,
    "aspirin.export.golden.svg": _render_export,
}


def _write_goldens() -> None:
    """Nur von Hand aufrufen — siehe Modul-Docstring."""
    FIXTURES.mkdir(exist_ok=True)
    for filename, render in CASES.items():
        (FIXTURES / filename).write_text(_normalise(render()), encoding="utf-8")
        print(f"geschrieben: {filename}")


@pytest.mark.parametrize("filename", sorted(CASES))
def test_default_rendering_matches_the_frozen_output(filename: str):
    golden = FIXTURES / filename
    assert golden.is_file(), (
        f"Golden-Datei fehlt: {golden}. Siehe Modul-Docstring zum Erzeugen."
    )
    assert _normalise(CASES[filename]()) == golden.read_text(encoding="utf-8"), (
        "Das Default-Rendering hat sich geändert. Wenn das Absicht war: Ergebnis "
        "ansehen und die Golden-Datei bewusst neu erzeugen. Wenn nicht: der Test "
        "hat gerade eine ungewollte Änderung gefangen."
    )


def test_the_golden_is_a_real_structure_drawing():
    """Schutz gegen eine leere oder kaputte Golden-Datei, die alles durchwinkt."""
    svg = (FIXTURES / "aspirin.export.golden.svg").read_text(encoding="utf-8")
    assert svg.count("<path") > 10, "zu wenige Striche für eine Strukturformel"
    assert "stroke-width" in svg


def test_probe_smiles_still_parses():
    """Wäre das SMILES kaputt, verglichen die Tests oben zwei Fehlerbilder."""
    assert Chem.MolFromSmiles(PROBE_SMILES) is not None
