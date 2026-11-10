"""Fischer- und Haworth-Projektion (Grundlagen, Etappe 4).

Die Seiten werden ohne CIP und ohne 3D bestimmt: aus dem Chiralitätstag in
einer festen Nachbarreihenfolge, verglichen mit einer Referenz (D-Glycerin-
aldehyd für Fischer, β-D-Glucopyranose für Haworth). Die Fälle sind die
Lehrbuchbilder, gegen die der Prototyp gemessen wurde (plans/anhang/).
"""

import re

import pytest
from rdkit import Chem

from chemdraw_tool.projection import (
    fischer_rows,
    fischer_svg,
    haworth_ring,
    haworth_svg,
    projection_note,
)

D_GLUCOSE = "O=C[C@H](O)[C@@H](O)[C@H](O)[C@H](O)CO"  # OPSIN „D-glucose“
D_GLUCOSE_PUBCHEM = "C([C@H]([C@H]([C@@H]([C@H](C=O)O)O)O)O)O"
D_GALACTOSE = "C([C@H]([C@@H]([C@@H]([C@H](C=O)O)O)O)O)O"
D_RIBOSE = "C([C@H]([C@H]([C@H](C=O)O)O)O)O"
D_FRUCTOSE = "C([C@H]([C@H]([C@@H](C(=O)CO)O)O)O)O"
L_ALANINE = "C[C@@H](C(=O)O)N"
L_SERINE = "C([C@@H](C(=O)O)N)O"
D_ALANINE = "C[C@H](C(=O)O)N"
L_ALANINE_ZWITTERION = "C[C@@H](C(=O)[O-])[NH3+]"
L_ASPARTIC_ACID = "N[C@@H](CC(=O)O)C(=O)O"  # auch eine Kette mit zwei COOH-Enden
L_HISTIDINE = "N[C@@H](Cc1c[nH]cn1)C(=O)O"

BETA_GLCP = "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@@H]1O"
ALPHA_GLCP = "OC[C@H]1O[C@H](O)[C@H](O)[C@@H](O)[C@@H]1O"
BETA_GALP = "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@H]1O"
BETA_RIBF = "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H]1O"
BETA_FRUF = "OC[C@]1(O)[C@@H](O)[C@H](O)[C@H](O1)CO"  # OPSIN, C2 = R
GLCP_OPEN_ANOMER = "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O"  # PubChem „D-glucopyranose“

NOT_PROJECTABLE = {
    "ethanol": "CCO",
    "ibuprofen": "CC(C)Cc1ccc(cc1)[C@H](C)C(=O)O",
    "methylphenidate": "COC(=O)[C@@H](c1ccccc1)[C@H]1CCCCN1",
    "glycine": "NCC(=O)O",
    "glucose ohne Stereo": "O=CC(O)C(O)C(O)C(O)CO",
    "sucrose": (
        "C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O[C@]2([C@H]([C@@H]"
        "([C@H](O2)CO)O)O)CO)O)O)O)O"
    ),
    "proline": "OC(=O)[C@@H]1CCCN1",
    "isoleucine": "CC[C@H](C)[C@H](N)C(=O)O",
    "methyl glucoside": "CO[C@@H]1O[C@H](CO)[C@@H](O)[C@H](O)[C@H]1O",
}


def mol(smiles):
    return Chem.MolFromSmiles(smiles)


def sides(rows):
    """Nur die Stereozentren als 'R'/'L' (Seite des Heteroatoms)."""
    out = []
    for row in rows:
        if row["kind"] != "center":
            continue
        out.append("R" if row["right"] != "H" else "L")
    return "".join(out)


# --- Fischer --------------------------------------------------------------


@pytest.mark.parametrize(
    "smiles, expected",
    [
        (D_GLUCOSE, "RLRR"),
        (D_GLUCOSE_PUBCHEM, "RLRR"),
        (D_GALACTOSE, "RLLR"),
        (D_RIBOSE, "RRR"),
        (D_FRUCTOSE, "LRR"),
    ],
)
def test_fischer_sugars_match_the_textbook(smiles, expected):
    assert sides(fischer_rows(mol(smiles))) == expected


def test_fischer_glucose_rows_top_to_bottom():
    rows = fischer_rows(mol(D_GLUCOSE))
    assert rows[0] == {"kind": "end", "label": "CHO"}
    assert rows[1] == {"kind": "center", "left": "H", "right": "OH"}
    assert rows[2] == {"kind": "center", "left": "HO", "right": "H"}
    assert rows[-1] == {"kind": "end", "label": "CH2OH"}


def test_fischer_ketose_has_carbonyl_at_c2():
    rows = fischer_rows(mol(D_FRUCTOSE))
    assert rows[0] == {"kind": "end", "label": "CH2OH"}
    assert rows[1] == {"kind": "carbonyl"}


@pytest.mark.parametrize(
    "smiles, left, right, bottom",
    [
        (L_ALANINE, "H2N", "H", "CH3"),
        (L_SERINE, "H2N", "H", "CH2OH"),
        (D_ALANINE, "H", "NH2", "CH3"),
        (L_ASPARTIC_ACID, "H2N", "H", "CH2COOH"),
        (L_HISTIDINE, "H2N", "H", "CH2-imidazolyl"),
    ],
)
def test_fischer_amino_acids(smiles, left, right, bottom):
    rows = fischer_rows(mol(smiles))
    assert rows == [
        {"kind": "end", "label": "COOH"},
        {"kind": "center", "left": left, "right": right},
        {"kind": "end", "label": bottom},
    ]


def test_fischer_zwitterion_keeps_its_charges():
    rows = fischer_rows(mol(L_ALANINE_ZWITTERION))
    assert rows[0] == {"kind": "end", "label": "COO-"}
    assert rows[1] == {"kind": "center", "left": "H3N+", "right": "H"}


def test_fischer_needs_an_open_chain():
    assert fischer_rows(mol(BETA_GLCP)) is None


@pytest.mark.parametrize("name", sorted(NOT_PROJECTABLE))
def test_nothing_else_gets_a_projection(name):
    m = mol(NOT_PROJECTABLE[name])
    assert fischer_rows(m) is None
    assert haworth_ring(m) is None
    assert fischer_svg(m) == ""
    assert haworth_svg(m) == ""


def test_fischer_svg_draws_labels_on_the_right_sides():
    svg = fischer_svg(mol(D_GLUCOSE))
    assert svg.startswith("<svg")
    assert "viewBox=" in svg
    # Kein Keil, keine RDKit-Atompfade: reine Textbeschriftung
    assert "rdkit" not in svg
    labels = re.findall(r"<text[^>]*>(.*?)</text>", svg)
    flat = [re.sub(r"<[^>]+>", "", t) for t in labels]
    assert flat.count("OH") == 3 and flat.count("HO") == 1
    assert flat[0] == "CHO"


# --- Haworth --------------------------------------------------------------


def ups(ring):
    return [pos["up"] for pos in ring[1:]]


@pytest.mark.parametrize(
    "smiles, expected_up",
    [
        (BETA_GLCP, ["OH", "H", "OH", "H", "CH2OH"]),
        (ALPHA_GLCP, ["H", "H", "OH", "H", "CH2OH"]),
        (BETA_GALP, ["OH", "H", "OH", "OH", "CH2OH"]),
        (BETA_RIBF, ["OH", "H", "H", "CH2OH"]),
        (BETA_FRUF, ["OH", "OH", "H", "CH2OH"]),
    ],
)
def test_haworth_matches_the_textbook(smiles, expected_up):
    assert ups(haworth_ring(mol(smiles))) == expected_up


def test_haworth_alpha_anomer_against_cip():
    """Gegenprobe ohne die eigene Regel: α-D-Glcp hat C1 = S, β = R."""
    from rdkit.Chem import rdCIPLabeler

    for smiles, cip, up in [(ALPHA_GLCP, "S", "H"), (BETA_GLCP, "R", "OH")]:
        m = mol(smiles)
        rdCIPLabeler.AssignCIPLabels(m)
        ring = haworth_ring(m)
        c1 = m.GetAtomWithIdx(ring[1]["idx"])
        assert c1.GetProp("_CIPCode") == cip
        assert ring[1]["up"] == up


def test_haworth_ring_starts_at_the_ring_oxygen():
    ring = haworth_ring(mol(BETA_GLCP))
    assert ring[0]["label"] == "O"
    assert len(ring) == 6
    assert len(haworth_ring(mol(BETA_RIBF))) == 5


def test_haworth_open_anomer_is_wavy():
    ring = haworth_ring(mol(GLCP_OPEN_ANOMER))
    assert ring[1].get("wavy") == "OH"
    assert ups(ring)[1:] == ["H", "OH", "H", "CH2OH"]


def test_haworth_needs_a_ring():
    assert haworth_ring(mol(D_GLUCOSE)) is None


def test_haworth_svg_has_a_thick_front_edge():
    svg = haworth_svg(mol(BETA_GLCP))
    assert svg.startswith("<svg")
    widths = {float(w) for w in re.findall(r"stroke-width:([\d.]+)px", svg)}
    assert len(widths) >= 2 and max(widths) > 3 * min(widths)


# --- Hinweis für Ringzucker ------------------------------------------------


def test_ring_sugar_gets_a_note_about_the_open_chain_form():
    note = projection_note(mol(BETA_GLCP))
    assert "open-chain" in note
    assert projection_note(mol(D_GLUCOSE)) == ""
    assert projection_note(mol("CCO")) == ""


# --- Anbindung an generate_molecule ---------------------------------------


@pytest.fixture
def server(tmp_path, monkeypatch):
    from chemdraw_tool import server as srv

    for const in ("OUTPUT_DIR", "REACTION_DIR", "PLOT_DIR", "ANKI_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())
    monkeypatch.setattr(srv, "_enrich_properties", lambda smiles: {})
    monkeypatch.setattr(srv, "_pubchem_record", lambda smiles: ({}, None))
    return srv


def test_open_chain_sugar_announces_fischer_only(server):
    payload = server.generate_molecule(D_GLUCOSE)
    assert "fischer" in payload.views and "haworth" not in payload.views
    assert payload.projectionNote == ""
    view = server.generate_molecule(**payload.viewRequest, view="fischer")
    assert view.viewSvg == fischer_svg(mol(D_GLUCOSE))
    assert view.viewAtoms == [] and view.files == {}


def test_ring_sugar_announces_haworth_and_a_note(server):
    payload = server.generate_molecule(BETA_GLCP)
    # Seit E17 (10.11.2026) zeigt Fischer die offene Form — vorher kein Knopf.
    assert "haworth" in payload.views and "fischer" in payload.views
    assert "open-chain" in payload.projectionNote
    view = server.generate_molecule(**payload.viewRequest, view="haworth")
    assert view.viewSvg.startswith("<svg")


def test_other_molecules_have_no_projection(server):
    payload = server.generate_molecule(NOT_PROJECTABLE["methylphenidate"])
    assert payload.views == ["all_h"]
    assert payload.projectionNote == ""


def test_model_may_open_the_panel_on_a_projection(server, monkeypatch):
    """Befund Desktop 26.10.: das Modell setzte view=haworth selbst. Dann
    soll ein vollständiges Panel kommen, das auf Haworth startet — mit Titel,
    Knöpfen und Hinweis, ohne PubChem und ohne Dateien."""

    def no_network(_smiles):
        raise AssertionError("view-Aufruf darf nicht ins Netz")

    monkeypatch.setattr(server, "_enrich_properties", no_network)
    payload = server.generate_molecule(
        BETA_GLCP, label="β-D-Glucopyranose", view="haworth"
    )
    assert payload.name == "β-D-Glucopyranose"
    assert payload.initialView == "haworth"
    assert payload.viewSvg == haworth_svg(mol(BETA_GLCP))
    assert payload.svg.startswith("<") and payload.atoms
    # Seit E5 (09.11.2026) bietet ein Pyranosering zusätzlich den Sessel an,
    # seit E17 (10.11.2026) Fischer für die offene Form.
    assert payload.views == ["all_h", "fischer", "haworth", "chair"]
    assert "open-chain" in payload.projectionNote
    assert payload.properties["formula"] == "C6H12O6"
    assert payload.files == {}


def test_unknown_or_missing_view_is_an_error(server):
    with pytest.raises(ValueError, match="view"):
        server.generate_molecule(NOT_PROJECTABLE["ethanol"], view="fischer")
    with pytest.raises(ValueError, match="view"):
        server.generate_molecule(D_GLUCOSE, view="newman")


def test_a_broken_projection_never_breaks_the_drawing(server, monkeypatch):
    def boom(_mol):
        raise RuntimeError("kaputt")

    monkeypatch.setattr("chemdraw_tool.projection.fischer_rows", boom)
    payload = server.generate_molecule(D_GLUCOSE)
    assert payload.svg.startswith("<")
    assert "fischer" not in payload.views


# --- Fischer für Ringzucker über die offene Form (E17, 10.11.2026) ------------
# Befund: Der Hinweis riet zu „D-glucose“, das bei PubChem die Pyranose ist —
# wieder ohne Fischer-Knopf; nur „aldehydo-D-glucose“ ging. Jetzt leitet das
# Panel die offene Kette lokal her (Halbacetal öffnen: anomeres C → C=O,
# Ring-O → OH, alle anderen Zentren bleiben). Referenz-Keys: PubChem
# (aldehydo-D-mannose CID 161658, die übrigen = Konstanten oben).
D_MANNOSE = "C([C@H]([C@H]([C@@H]([C@@H](C=O)O)O)O)O)O"
ALPHA_MANP = "C([C@@H]1[C@H]([C@@H]([C@@H]([C@H](O1)O)O)O)O)O"  # PubChem CID 185698
BETA_FRUP = "C1[C@H]([C@H]([C@@H]([C@](O1)(CO)O)O)O)O"  # PubChem CID 24310
FRUP_OPEN_ANOMER = "C1[C@H]([C@H]([C@@H](C(O1)(CO)O)O)O)O"  # PubChem „D-fructose“


def key(smiles_or_mol):
    m = mol(smiles_or_mol) if isinstance(smiles_or_mol, str) else smiles_or_mol
    return Chem.MolToInchiKey(m)


@pytest.mark.parametrize(
    "ring, open_chain",
    [
        (BETA_GLCP, D_GLUCOSE),
        (ALPHA_GLCP, D_GLUCOSE),
        (GLCP_OPEN_ANOMER, D_GLUCOSE),
        (BETA_GALP, D_GALACTOSE),
        (ALPHA_MANP, D_MANNOSE),
        (BETA_RIBF, D_RIBOSE),
        (BETA_FRUF, D_FRUCTOSE),
        (BETA_FRUP, D_FRUCTOSE),
        (FRUP_OPEN_ANOMER, D_FRUCTOSE),
    ],
)
def test_ring_sugar_opens_to_its_open_chain_form(ring, open_chain):
    from chemdraw_tool.projection import open_chain_form

    opened = open_chain_form(mol(ring))
    assert opened is not None and key(opened) == key(open_chain)
    assert fischer_rows(opened) == fischer_rows(mol(open_chain))


@pytest.mark.parametrize("name", ["methyl glucoside", "sucrose", "glucose ohne Stereo", "ethanol"])
def test_glycosides_and_others_have_no_open_chain_form(name):
    from chemdraw_tool.projection import open_chain_form

    assert open_chain_form(mol(NOT_PROJECTABLE[name])) is None


def test_ring_sugar_offers_fischer_of_the_open_chain(server):
    from chemdraw_tool.projection import open_chain_form

    payload = server.generate_molecule(BETA_GLCP)
    assert payload.views == ["all_h", "fischer", "haworth", "chair"]
    view = server.generate_molecule(**payload.viewRequest, view="fischer")
    assert view.viewSvg.startswith("<svg") and "open-chain form" in view.viewSvg
    # dieselben Zeilen wie die echte offene Kette
    open_svg = fischer_svg(open_chain_form(mol(BETA_GLCP)))
    drawing = open_svg.split("'>", 1)[1].removesuffix("</svg>")
    assert drawing in view.viewSvg
    # Identität bleibt die Pyranose
    assert view.properties["formula"] == "C6H12O6"
    assert view.viewRequest["name_or_smiles"] == payload.viewRequest["name_or_smiles"]


def test_note_no_longer_sends_the_user_to_a_name_without_fischer():
    note = projection_note(mol(BETA_GLCP))
    assert "'D-glucose'" not in note
    assert "open-chain" in note and "anomer" in note
