"""Kürzel-Labels liegen ganz in der viewBox des Panel-SVG.

Bildschau E16 (10.11.2026): `_crop_svg_to_content` schneidet auf Atommitten
± 22 px zu. „CO₂H“ ragt weiter hinaus — am Rand stand „CO2“ bzw. „O2C“, das
H war abgeschnitten. Gilt für jeden Panel-Pfad über render_svg.
"""

from __future__ import annotations

import re

import pytest
from rdkit import Chem

from chemdraw_tool.generator import generate_2d
from chemdraw_tool.render_style import condense_groups
from chemdraw_tool.svg_renderer import render_reaction_entry, render_svg


def _outside(svg: str) -> list[tuple[float, float]]:
    vx, vy, vw, vh = (float(v) for v in re.search(r"viewBox='([^']*)'", svg).group(1).split())
    pts = []
    for m in re.finditer(r"<path class='atom-\d+' d='([^']*)' fill='#[0-9A-F]{6}'", svg):
        for x, y in re.findall(r"(-?[\d.]+) (-?[\d.]+)", m.group(1)):
            if not (vx <= float(x) <= vx + vw and vy <= float(y) <= vy + vh):
                pts.append((float(x), float(y)))
    return pts


# Häm b als SMILES (offline): zwei Propionsäuren, die als CO₂H am Rand stehen.
HEME_B = "CC1=C(C2=CC3=NC(=CC4=C(C(=C([N-]4)C=C5C(=C(C(=N5)C=C1[N-]2)C)C=C)C)C=C)C(=C3CCC(=O)O)C)CCC(=O)O.[Fe+2]"


def _porphyrin():
    return generate_2d(Chem.MolFromSmiles(HEME_B))


@pytest.mark.parametrize(
    "render",
    [
        lambda: render_svg(condense_groups(generate_2d(Chem.MolFromSmiles(
            "CC(=O)Oc1ccccc1C(=O)O"))), fill_container=True),
        lambda: render_svg(condense_groups(generate_2d(Chem.MolFromSmiles(
            "O=C(c1ccccc1)CC1CCN(C(=O)OC(C)(C)C)CC1"))), fill_container=True),
        lambda: render_reaction_entry(condense_groups(_porphyrin())),
    ],
    ids=["aspirin", "boc_ph", "porphyrin_reaction"],
)
def test_abbreviation_labels_inside_viewbox(render):
    outside = _outside(render())
    assert not outside, f"{len(outside)} Glyphenpunkte außerhalb der viewBox, z. B. {outside[:3]}"
