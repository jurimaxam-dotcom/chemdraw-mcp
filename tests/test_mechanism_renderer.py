"""Tests for SVG Bezier arrow rendering."""

import re

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.mechanism import CurvedArrow, MechanismStep
from chemdraw_tool.mechanism_renderer import render_step_svg


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles, sanitize=False)
    Chem.SanitizeMol(mol, sanitizeOps=Chem.SANITIZE_ALL ^ Chem.SANITIZE_PROPERTIES)
    AllChem.Compute2DCoords(mol)
    return mol


def test_render_step_svg_produces_valid_svg():
    mols = [_make_mol("[OH-:3]"), _make_mol("[CH3:1][Br:2]")]
    step = MechanismStep(
        label="Edukte",
        molecules=["[OH-:3]", "[CH3:1][Br:2]"],
        arrows=[],
    )
    svg = render_step_svg(step, mols)
    assert "<svg" in svg.lower()
    assert "</svg>" in svg.lower()


def test_render_step_svg_contains_arrow_path():
    mols = [_make_mol("[O-:3].[CH3:1].[Br-:2]")]
    step = MechanismStep(
        label="Übergangszustand",
        molecules=["[O-:3].[CH3:1].[Br-:2]"],
        arrows=[
            CurvedArrow(
                source=(3, "lone_pair"),
                target=(1, "atom"),
                style="full",
            ),
        ],
        is_transition_state=True,
        partial_bonds=[(3, 1)],
    )
    svg = render_step_svg(step, mols)
    assert "path" in svg.lower()


def test_render_step_svg_transition_state_has_dashed_line():
    mols = [_make_mol("[O-:3].[CH3:1].[Br-:2]")]
    step = MechanismStep(
        label="TS",
        molecules=["[O-:3].[CH3:1].[Br-:2]"],
        arrows=[],
        is_transition_state=True,
        partial_bonds=[(3, 1)],
    )
    svg = render_step_svg(step, mols)
    assert "stroke-dasharray" in svg


def test_render_step_svg_no_arrows_no_paths():
    mols = [_make_mol("[CH3:1][Br:2]")]
    step = MechanismStep(
        label="Edukte",
        molecules=["[CH3:1][Br:2]"],
        arrows=[],
    )
    svg = render_step_svg(step, mols)
    path_count = len(re.findall(r"<path[^>]*class=['\"]arrow", svg))
    assert path_count == 0


def test_render_step_svg_multi_molecule():
    mols = [_make_mol("[OH-:3]"), _make_mol("[CH3:1][Br:2]")]
    step = MechanismStep(
        label="Edukte",
        molecules=["[OH-:3]", "[CH3:1][Br:2]"],
        arrows=[],
    )
    svg = render_step_svg(step, mols)
    assert "<svg" in svg.lower()


def test_render_step_svg_has_exactly_one_viewbox():
    """RDKit emits a viewBox; the renderer must replace it, not add a second."""
    mols = [_make_mol("[OH-:3]"), _make_mol("[CH3:1][Br:2]")]
    step = MechanismStep(
        label="Edukte",
        molecules=["[OH-:3]", "[CH3:1][Br:2]"],
        arrows=[],
    )
    svg = render_step_svg(step, mols)
    assert svg.lower().count("viewbox") == 1


def test_bindungslaenge_in_pixeln_ist_in_allen_schritten_gleich():
    """Galerie 02.10.2026: RDKit passte jeden Schritt in dieselbe Leinwand ein — das
    dreiteilige Produkt-Bild (HO–CH3 + Br⁻ weit daneben) bekam winzige Atome, der
    Einzelschritt riesige. Gleiche Bindungslänge macht die Overview-Kacheln vergleichbar."""
    from chemdraw_tool.mechanism_renderer import _render_mols_svg

    def px(smiles_list, a, b):
        mols = [_make_mol(s) for s in smiles_list]
        _, coords = _render_mols_svg(mols)
        (x1, y1), (x2, y2) = coords[a], coords[b]
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    einzeln = px(["[CH3:1][Br:2]"], 1, 2)
    mit_nachbar = px(["[OH:3][CH3:1]", "[Br-:2]"], 3, 1)
    assert mit_nachbar == pytest.approx(einzeln, rel=0.05)


def test_teilbindung_endet_vor_den_atombeschriftungen():
    """Galerie 02.10.2026: die gestrichelte Teilbindung lief mitten durch „O⁻“, „CH₃“ und „Br⁻“.
    Läuft über die echte Pipeline (SN2-Vorlage → stabilize_sequence), nicht über ein Handmolekül."""
    from chemdraw_tool.mechanism_coords import stabilize_sequence
    from chemdraw_tool.mechanism_renderer import _render_mols_svg
    from chemdraw_tool.templates import get_template

    template = get_template("sn2")
    stabil = stabilize_sequence([s.molecules for s in template.steps], gaps=[s.mol_gap for s in template.steps])
    ts = next(s for s in template.steps if s.is_transition_state)
    mols = stabil[template.steps.index(ts)]
    _, coords = _render_mols_svg(mols)
    (ax, ay), (bx, by) = coords[3], coords[1]
    zentren = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
    m = re.search(r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)"[^>]*stroke-dasharray', render_step_svg(ts, mols))
    x1, y1, x2, y2 = map(float, m.groups())
    strich = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    assert strich <= zentren - 20, f"Strich {strich:.0f}px bei Atomabstand {zentren:.0f}px — läuft durch die Beschriftung"


def test_unify_frames_gibt_allen_schritten_dieselbe_viewbox():
    """Fischer-Schritt 3 wirkte kleiner als Schritt 2: gleiche Bindungslänge in viewBox-Einheiten,
    aber breitere viewBox — wer jedes Bild auf dieselbe Breite zieht, verkleinert ihn."""
    from chemdraw_tool.mechanism_renderer import unify_frames

    schmal = render_step_svg(MechanismStep(label="a", molecules=[], arrows=[]), [_make_mol("[CH3:1][Br:2]")])
    breit = render_step_svg(
        MechanismStep(label="b", molecules=[], arrows=[]), [_make_mol("[OH-:3]"), _make_mol("CCCCCC[CH2:1][Br:2]")]
    )
    vb = [re.search(r"viewBox='([^']*)'", s).group(1) for s in unify_frames([schmal, breit])]
    assert vb[0] == vb[1]
    assert all(s.lower().count("viewbox") == 1 for s in unify_frames([schmal, breit]))


def test_beschriftungsboxen_kommen_aus_den_glyphenpfaden():
    """Pfeilenden richten sich nach der echten Beschriftung: „HO“ ist breiter als „O“."""
    from chemdraw_tool.mechanism_renderer import geometry_of

    svg = render_step_svg(MechanismStep(label="a", molecules=[], arrows=[]), [_make_mol("[CH3:1][OH:2]")])
    geo = geometry_of(svg)
    x0, y0, x1, y1 = geo["boxes"]["2"]
    assert x1 - x0 > y1 - y0, "OH-Box sollte breiter als hoch sein"


def test_pfeil_kann_auf_eine_bindung_zeigen():
    """Fischer, Wasserabspaltung: das freie Paar von O2 bildet die C=O⁺H-Bindung zurück — die
    Spitze gehört an die Mitte der entstehenden Bindung, nicht an ein Atom (Design (g)3)."""
    import math

    from chemdraw_tool.mechanism import CurvedArrow
    from chemdraw_tool.mechanism_renderer import geometry_of

    step = MechanismStep(label="a", molecules=[], arrows=[
        CurvedArrow(source=(2, "lone_pair"), target=(1, "bond_to", 2), style="full"),
    ])
    geo = geometry_of(render_step_svg(step, [_make_mol("[CH3:5][CH:1]=[OH+:2]")]))
    (a,) = geo["arrows"]
    assert a["tgt_bond"] == [1, 2]
    c1, o2 = geo["centres"]["1"], geo["centres"]["2"]
    mitte = ((c1[0] + o2[0]) / 2, (c1[1] + o2[1]) / 2)
    assert math.dist(a["tip"], mitte) <= 0.35 * geo["bond_px"]
