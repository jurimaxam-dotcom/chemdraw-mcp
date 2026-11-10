"""Jede Farbe, die RDKit ins Panel-SVG schreibt, braucht eine Dunkel-Umfärbung.

Befund 10.11.2026 (dunkles Schema): Abkürzungs-Labels („Boc“, „Ph“,
„CO2H“) standen fast schwarz auf dunklem Grund. RDKit zeichnet Dummy-Atome
(die Träger der Kürzel) in #191919 — die Umfärbung in styles.css kannte nur
#000000 und die Heteroatomfarben. Gemessen wird am echten Panel-SVG gegen die
echten Selektoren beider Dunkel-Blöcke (Media-Query und data-theme="dark").
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from rdkit import Chem

from chemdraw_tool.generator import generate_2d
from chemdraw_tool.render_style import condense_groups
from chemdraw_tool.svg_renderer import render_svg

CSS = (Path(__file__).parent.parent / "chemdraw_tool" / "ui" / "src" / "styles.css").read_text()

# Zwei Dunkel-Varianten: Systemschema (Media-Query) und Host-Schalter data-theme.
_PREFIXES = {
    "media": ':root:not([data-theme="light"]) svg:not(.plot-svg svg, .scope-svg svg)',
    "data-theme": ':root[data-theme="dark"] svg:not(.plot-svg svg, .scope-svg svg)',
}

PROBES = {
    # Boc und Ph als Kürzel.
    "boc_ph": "O=C(c1ccccc1)CC1CCN(C(=O)OC(C)(C)C)CC1",
    # Aspirin: CO2H und OAc.
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
}


def _colours(svg: str) -> tuple[set[str], set[str]]:
    strokes = set(re.findall(r"stroke:(#[0-9A-Fa-f]{6})", svg))
    fills = set(re.findall(r"fill='(#[0-9A-Fa-f]{6})'", svg))
    return strokes, fills


def _has_rule(prefix: str, selector: str) -> bool:
    return f"{prefix} {selector}" in CSS


def test_prefixes_exist_at_all():
    # Gegenprobe: ohne die Präfixe prüfte der Test nichts.
    for prefix in _PREFIXES.values():
        assert _has_rule(prefix, 'path[style*="stroke:#000000"]'), prefix


@pytest.mark.parametrize("probe", sorted(PROBES))
@pytest.mark.parametrize("variant", sorted(_PREFIXES))
def test_every_panel_colour_is_recoloured_in_dark(probe, variant):
    mol = generate_2d(Chem.MolFromSmiles(PROBES[probe]))
    for drawn in (mol, condense_groups(mol)):
        svg = render_svg(drawn, fill_container=True)
        strokes, fills = _colours(svg)
        prefix = _PREFIXES[variant]
        missing = [f"stroke {c}" for c in sorted(strokes)
                   if not _has_rule(prefix, f'path[style*="stroke:{c}"]')]
        missing += [f"fill {c}" for c in sorted(fills)
                    if not _has_rule(prefix, f'path[fill="{c}"]')]
        assert not missing, f"{probe} ({variant}): keine Dunkel-Umfärbung für {missing}"
