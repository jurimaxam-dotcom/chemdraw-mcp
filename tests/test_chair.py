"""Sesselkonformation als Zusatzansicht von generate_molecule (Etappe E5).

Die Seite (oben/unten) kommt aus derselben Zeile wie bei Haworth — dem
Chiralitätstag in fester Nachbarreihenfolge, verglichen mit der
β-D-Glucopyranose-Referenz. Nie über CIP-Buchstaben: cis-1,4 ist
pseudoasymmetrisch (r/s). Axial/äquatorial folgt aus der Seite und dem
gewählten Sessel.

Die Stereo-SMILES sind am 09.11.2026 mit RDKit gegengeprüft: CIP (cis-1,2
und cis-1,3 meso = R,S; trans = R,R), InChI (/m nur bei den chiralen) und
eine ETKDG-Einbettung, in der die Seite jedes Substituenten gegen sein H am
selben Ringatom gemessen wurde (cis = beide auf derselben Seite).
"""

import re

import pytest
from rdkit import Chem

from chemdraw_tool.projection import chair_problem, chair_ring, chair_svg

BETA_GLCP = "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@@H]1O"
ALPHA_GLCP = "OC[C@H]1O[C@H](O)[C@H](O)[C@@H](O)[C@@H]1O"
L_BETA_GLCP = "OC[C@@H]1O[C@H](O)[C@@H](O)[C@H](O)[C@H]1O"  # Spiegelbild
METHYLCYCLOHEXANE = "CC1CCCCC1"
CIS_12 = "C[C@@H]1CCCC[C@@H]1C"
TRANS_12 = "C[C@@H]1CCCC[C@H]1C"
CIS_13 = "C[C@@H]1CCC[C@H](C)C1"
TRANS_13 = "C[C@@H]1CCC[C@@H](C)C1"
CIS_14 = "C[C@H]1CC[C@@H](C)CC1"
TRANS_14 = "C[C@H]1CC[C@H](C)CC1"
MENTHOL = "CC(C)[C@@H]1CC[C@@H](C)C[C@H]1O"  # (1R,2S,5R)-(−)-Menthol
TBU_CIS_14 = "CC(C)(C)[C@H]1CC[C@@H](C)CC1"  # tBu sperrt den Ring


def mol(smiles):
    return Chem.MolFromSmiles(smiles)


def placement_of(m):
    """{Substituenten-Atomindex: 'ax'/'eq'} für alle Schwer-Substituenten."""
    out = {}
    for pos in chair_ring(m)["positions"]:
        for key, kind in (("axialAtom", "ax"), ("equatorialAtom", "eq")):
            idx = pos.get(key)
            # AddHs hängt die H hinten an: Indizes ab NumAtoms sind H.
            if idx is not None and idx < m.GetNumAtoms():
                out[idx] = kind
    return out


def placement(smiles):
    return placement_of(mol(smiles))


def ring_substituent_kinds(smiles):
    """Ax/eq der Substituenten in Ring-Reihenfolge des SMILES (Atomindex)."""
    p = placement(smiles)
    return [p[i] for i in sorted(p)]


# --- Prüfung der Stereo-SMILES selbst ---------------------------------------


@pytest.mark.parametrize(
    "smiles, meso",
    [(CIS_12, True), (TRANS_12, False), (CIS_13, True), (TRANS_13, False)],
)
def test_cis_trans_smiles_are_what_their_names_say(smiles, meso):
    cip = [
        c
        for _, c in Chem.FindMolChiralCenters(
            mol(smiles), includeUnassigned=True, useLegacyImplementation=False
        )
    ]
    assert (sorted(cip) == ["R", "S"]) == meso


def test_cis_and_trans_14_differ_only_in_pseudoasymmetry():
    cis, trans = Chem.MolToInchi(mol(CIS_14)), Chem.MolToInchi(mol(TRANS_14))
    assert cis != trans
    assert "/t7-,8+" in cis and "/t7-,8-" in trans


# --- Zuordnung ---------------------------------------------------------------


@pytest.mark.parametrize(
    "smiles, expected",
    [
        # β-D-Glcp: alle fünf Substituenten äquatorial (Atome 1, 5, 7, 9, 11)
        (BETA_GLCP, ["eq"] * 5),
        # α-D-Glcp: nur das anomere OH (Atom 5) axial
        (ALPHA_GLCP, ["eq", "ax", "eq", "eq", "eq"]),
        (METHYLCYCLOHEXANE, ["eq"]),
        (TRANS_12, ["eq", "eq"]),
        (CIS_12, ["eq", "ax"]),
        (CIS_13, ["eq", "eq"]),
        (TRANS_13, ["eq", "ax"]),
        (TRANS_14, ["eq", "eq"]),
        (CIS_14, ["eq", "ax"]),
        (MENTHOL, ["eq", "eq", "eq"]),
    ],
)
def test_chair_places_substituents_like_the_textbook(smiles, expected):
    kinds = ring_substituent_kinds(smiles)
    if expected.count("ax") == 1 and len(expected) == 2 and smiles != ALPHA_GLCP:
        # Bei cis-1,2 / trans-1,3 / cis-1,4 sind beide Sessel gleich gut:
        # genau einer axial, welcher ist Geschmack.
        assert sorted(kinds) == ["ax", "eq"]
    else:
        assert kinds == expected


def test_the_bulky_group_decides_the_chair():
    # cis-1-tert-Butyl-4-methyl: tBu äquatorial, also Methyl axial
    p = placement(TBU_CIS_14)
    assert p[1] == "eq" and p[8] == "ax"


def test_d_glucose_is_4c1_and_l_glucose_1c4():
    assert chair_ring(mol(BETA_GLCP))["conformer"] == "4C1"
    assert chair_ring(mol(L_BETA_GLCP))["conformer"] == "1C4"
    # Das Spiegelbild ist im eigenen Sessel wieder ganz äquatorial.
    assert set(ring_substituent_kinds(L_BETA_GLCP)) == {"eq"}


def test_pyranose_ring_oxygen_sits_at_position_zero():
    ring = chair_ring(mol(BETA_GLCP))
    first = ring["positions"][0]
    assert first == {"idx": 3, "label": "O"}
    # C1 (anomer) folgt direkt danach
    assert ring["positions"][1]["idx"] == 4


def test_reversing_the_ring_traversal_changes_nothing():
    """Laufrichtung und Referenz gehören zusammen: dieselben Moleküle in
    anderer Atomreihenfolge geschrieben ergeben dieselbe Zuordnung."""
    for a, b in [
        (TRANS_14, "C[C@@H]1CC[C@@H](C)CC1"),
        (MENTHOL, Chem.MolToSmiles(mol(MENTHOL), rootedAtAtom=9)),
        (TRANS_12, Chem.MolToSmiles(mol(TRANS_12), rootedAtAtom=3)),
    ]:
        assert Chem.MolToInchi(mol(a)) == Chem.MolToInchi(mol(b))
        assert sorted(placement(a).values()) == sorted(placement(b).values())


def test_untagged_ring_atom_puts_its_substituent_equatorial():
    for smiles in ("CC1CCC(C)CC1", "OC1CCCCC1", "OCC1OC(O)C(O)C(O)C1O"):
        assert set(ring_substituent_kinds(smiles)) == {"eq"}, smiles


def test_geminal_without_stereo_puts_the_bulkier_group_equatorial():
    # 1-Methylcyclohexanol: Methyl (1,74) schlägt OH (0,87)
    m = "CC1(O)CCCCC1"
    assert placement(m) == {0: "eq", 2: "ax"}


def test_substituent_labels_follow_haworth():
    ring = chair_ring(mol(BETA_GLCP))
    labels = sorted(pos["equatorial"] for pos in ring["positions"][1:])
    assert labels == ["CH2OH", "OH", "OH", "OH", "OH"]
    menthol = chair_ring(mol(MENTHOL))
    eq = {pos.get("equatorial") for pos in menthol["positions"]}
    assert {"CH3", "CH(CH3)2", "OH"} <= eq


# --- Ablehnen ----------------------------------------------------------------


@pytest.mark.parametrize(
    "smiles, reason",
    [
        ("CCO", "no six-membered ring"),
        ("C1CCCC1", "no six-membered ring"),
        ("c1ccccc1C", "double bond or aromatic"),
        ("O=C1CCCCC1", "double bond or aromatic"),
        ("C1=CCCCC1", "double bond or aromatic"),
        ("C1CCC2CCCCC2C1", "fused or spiro"),
        ("C1CCC2(CC1)CCCC2", "fused or spiro"),
        ("C1CCC(CC1)C1CCCCC1", "more than one ring"),
        ("C1CCNCC1", "only carbocycles"),
        ("CC1CCCCC1[Si](C)(C)C", "cannot label"),
    ],
)
def test_unsuitable_molecules_are_rejected_with_a_reason(smiles, reason):
    m = mol(smiles)
    assert reason in chair_problem(m)
    assert chair_ring(m) is None
    assert chair_svg(m) == ""


def test_suitable_molecules_have_no_problem():
    for smiles in (BETA_GLCP, METHYLCYCLOHEXANE, MENTHOL, "C1CCCCC1"):
        assert chair_problem(mol(smiles)) == ""


# --- Zeichnung ---------------------------------------------------------------


def _paths(svg):
    return [
        tuple(map(float, re.findall(r"-?[\d.]+", d)))
        for d in re.findall(r"d='M ([^']+)'", svg)
    ]


def test_chair_svg_has_six_ring_bonds_in_three_parallel_pairs():
    svg = chair_svg(mol("C1CCCCC1"))
    assert svg.startswith("<svg") and "viewBox=" in svg
    bonds = _paths(svg)
    assert len(bonds) == 6  # Cyclohexan: nur der Ring, keine H

    def slope(b):
        x1, y1, x2, y2 = b
        return round((y2 - y1) / (x2 - x1), 3)

    # Gegenüberliegende Ringbindungen sind parallel (Bindung k und k+3).
    for k in range(3):
        assert slope(bonds[k]) == pytest.approx(slope(bonds[k + 3]), abs=0.02)


def test_chair_svg_draws_axial_bonds_vertical():
    svg = chair_svg(mol(ALPHA_GLCP))
    vertical = [b for b in _paths(svg)[6:] if abs(b[0] - b[2]) < 0.05]
    # Je Ringkohlenstoff ein axialer Strich (fünf C), H inklusive
    assert len(vertical) == 5
    texts = [
        re.sub(r"<[^>]+>", "", t) for t in re.findall(r"<text[^>]*>(.*?)</text>", svg)
    ]
    assert texts.count("O") == 1
    assert sum(t in ("OH", "HO") for t in texts) == 4


def test_chair_svg_labels_do_not_overlap():
    from chemdraw_tool.projection import _chair_label_boxes

    for smiles in (BETA_GLCP, ALPHA_GLCP, MENTHOL, CIS_12, TRANS_13, CIS_14):
        boxes = _chair_label_boxes(mol(smiles))
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                overlap = a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
                assert not overlap, (smiles, a, b)


@pytest.mark.parametrize(
    "smiles",
    [
        BETA_GLCP,
        ALPHA_GLCP,
        L_BETA_GLCP,
        METHYLCYCLOHEXANE,
        TRANS_12,
        CIS_12,
        CIS_13,
        TRANS_13,
        TRANS_14,
        CIS_14,
        MENTHOL,
        TBU_CIS_14,
    ],
)
def test_no_label_touches_a_bond_or_another_label(smiles):
    """Befund Auftraggeber 10.11.2026: in β-/α-Glcp lief die Ringbindung
    C5–O durch das „OH" von CH2OH. Kein Beschriftungsrechteck (mit
    Helvetica-Breiten, nicht der knappen Schätzung) schneidet eine fremde
    Strecke oder eine andere Beschriftung."""
    from chemdraw_tool.projection import chair_collisions

    assert chair_collisions(mol(smiles)) == 0


def test_label_width_is_not_underestimated():
    from chemdraw_tool.projection import _chair_text_width

    # Helvetica 16 px: C 11,6 · H 11,6 · O 12,4; Ziffer tiefgestellt 11 px · 0,556
    assert _chair_text_width("CH2OH") >= 52


# --- Anbindung an generate_molecule ---------------------------------------


@pytest.fixture
def server(tmp_path, monkeypatch):
    from chemdraw_tool import server as srv

    for const in ("OUTPUT_DIR", "REACTION_DIR", "PLOT_DIR", "ANKI_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())
    monkeypatch.setattr(srv, "_enrich_properties", lambda smiles: {})
    monkeypatch.setattr(srv, "_pubchem_record", lambda smiles: ({}, None))
    return srv


def test_cyclohexane_derivative_announces_the_chair(server):
    payload = server.generate_molecule(MENTHOL)
    assert "chair" in payload.views
    view = server.generate_molecule(**payload.viewRequest, view="chair")
    # Panel-Vorschau und PNG-Export lesen dasselbe SVG (wie Fischer/Haworth)
    assert view.viewSvg == chair_svg(mol(MENTHOL))
    assert view.viewAtoms == [] and view.files == {}


@pytest.mark.parametrize(
    "smiles, expected", [(CIS_14, ["ax", "eq"]), (TRANS_14, ["eq", "eq"])]
)
def test_pseudoasymmetric_tags_survive_the_server_path(server, smiles, expected):
    """resolve() und generate_2d liegen dazwischen — cis/trans-1,4 trägt nur
    r/s und darf dort nicht verloren gehen."""
    payload = server.generate_molecule(smiles, view="chair")
    assert payload.initialView == "chair"
    assert payload.viewSvg == chair_svg(mol(smiles))
    assert payload.stereoNote == ""
    resolved = mol(payload.viewRequest["name_or_smiles"])
    kinds = [kind for _, kind in sorted(placement_of(resolved).items())]
    assert sorted(kinds) == sorted(expected)


def test_stereoless_disubstituted_ring_warns(server):
    """PubChem liefert für cis- und trans-1,4-Dimethylcyclohexan dieselbe
    stereolose Struktur; der Sessel stellt beide Methyle äquatorial und das
    Payload sagt, dass die Konfiguration offen ist."""
    payload = server.generate_molecule("CC1CCC(C)CC1", view="chair")
    assert payload.viewSvg
    assert len(payload.stereoWarnings) == 2
    assert "unspecified" in payload.stereoNote


def test_ring_sugar_offers_haworth_and_chair(server):
    payload = server.generate_molecule(BETA_GLCP)
    # Fischer seit E17 (10.11.2026): die offene Form des Ringzuckers.
    assert payload.views == ["all_h", "fischer", "haworth", "chair"]


def test_unsuitable_chair_request_names_the_reason(server):
    with pytest.raises(ValueError, match="aromatic"):
        server.generate_molecule("Cc1ccccc1", view="chair")
    with pytest.raises(ValueError, match="chair"):
        server.generate_molecule("CCO", view="newman")
