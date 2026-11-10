"""Reaktions-Panel: große Strukturen behalten den Bindungsmaßstab.

Befund 10.11.2026: ein Porphyrin (≈40 Schweratome) passt nicht auf RDKits
250×200-Zeichenfläche je Stoff; RDKit verwirft dann `fixedBondLength` und
zeichnet auf ~0,5 verkleinert — N-Labels 4,5 px hoch, unlesbar, noch bevor
das Panel irgendetwas skalierte. Kleine Stoffe passen und dürfen sich um kein
Byte ändern.
"""

from __future__ import annotations

import re

from rdkit import Chem

from chemdraw_tool.generator import generate_2d
from chemdraw_tool.svg_renderer import (
    REACTION_ENTRY_HEIGHT,
    REACTION_ENTRY_WIDTH,
    render_reaction_entry,
    render_svg,
)


def _max_glyph_height(svg: str, colour: str) -> float:
    heights = []
    for m in re.finditer(r"<path class='atom-\d+' d='([^']*)' fill='" + colour + "'", svg):
        ys = [float(y) for y in re.findall(r"(?:[MLQ,] ?)-?[\d.]+ (-?[\d.]+)", m.group(1))]
        if ys:
            heights.append(max(ys) - min(ys))
    return max(heights, default=0.0)


def test_large_reaction_entry_keeps_fixed_bond_scale():
    # Protoporphyrin IX als SMILES (offline)
    mol = Chem.MolFromSmiles("CC1=C(CCC(=O)O)C2=CC3=C(CCC(=O)O)C(C)=C(N3)C=C4C(C)=C(C=C)C(=N4)C=C5C(C=C)=C(C)C(=N5)C=C1N2")
    svg = render_reaction_entry(generate_2d(mol))
    # Großbuchstaben-Glyphe bei Bindungslänge 25 px: ≈ 10,6 px (Aspirin-O: 10,9).
    assert _max_glyph_height(svg, "#0000FF") >= 10, "N-Label auf der Zeichenfläche verkleinert"


def test_small_reaction_entries_unchanged_byte_for_byte():
    for smiles in ("[H][H]", "O=O", "O", "CC(=O)O", "CCO", "CC(=O)OCC", "O=C=O",
                   "CC(=O)Oc1ccccc1C(=O)O"):
        mol = generate_2d(Chem.MolFromSmiles(smiles))
        assert render_reaction_entry(mol) == render_svg(
            mol, REACTION_ENTRY_WIDTH, REACTION_ENTRY_HEIGHT
        ), smiles
