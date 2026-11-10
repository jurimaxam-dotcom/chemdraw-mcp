"""Metall-Tetrapyrrole als Lehrbuchbild (E11, 10.11.2026).

PubChem liefert Häm, Sirohäm & Co. als Dianion-Makrozyklus plus Metall als
EIGENES Fragment (`….[Fe+2]`). Gezeichnet stand das Eisen lose über dem Ring,
die Pyrrole waren zu Dreiecken verzerrt. Jetzt:

- `generate_2d` legt den Makrozyklus unverzerrt hin und das Metall in die
  Ringmitte — der Graph (Atome, Bindungen, Ladungen) bleibt der der Quelle;
- die vier N–Metall-Bindungen entstehen erst beim ZEICHNEN
  (`coordination_drawing`), damit Formel, InChIKey, SMILES, Stereo-Hinweise
  und funktionelle Gruppen exakt die der Quelle bleiben.

Alle SMILES sind am 10.11.2026 über `resolve()` gemessen (PubChem); die Tests
laufen ohne Netz.
"""

from __future__ import annotations

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors

from chemdraw_tool.generator import (
    central_metal,
    coordination_drawing,
    find_unspecified_stereo,
    generate_2d,
    tetrapyrrole_core,
)

SMILES = {
    "heme": "CC1=C(C2=CC3=C(C(=C([N-]3)C=C4C(=C(C(=N4)C=C5C(=C(C(=N5)C=C1[N-]2)C)C=C)C)C=C)C)CCC(=O)O)CCC(=O)O.[Fe+2]",
    "hemin": "CC1=C(C2=CC3=C(C(=C([N-]3)C=C4C(=C(C(=N4)C=C5C(=C(C(=N5)C=C1[N-]2)C)C=C)C)C=C)C)CCC(=O)O)CCC(=O)O.[Cl-].[Fe+3]",
    "siroheme": "C[C@@]1([C@@H](C2=NC1=CC3=NC(=CC4=C(C(=C([N-]4)C=C5C(=C(C(=C2)[N-]5)CC(=O)O)CCC(=O)O)CCC(=O)O)CC(=O)O)[C@@]([C@@H]3CCC(=O)O)(C)CC(=O)O)CCC(=O)O)CC(=O)O.[Fe+2]",
    "12,18-didecarboxysiroheme": "CC1=C2C=C3[C@H]([C@](C(=N3)C=C4[C@H]([C@](C(=CC5=NC(=CC(=C1CCC(=O)[O-])[N-]2)C(=C5C)CCC(=O)[O-])[N-]4)(C)CC(=O)[O-])CCC(=O)[O-])(C)CC(=O)[O-])CCC(=O)[O-].[Fe]",
    "Fe-coproporphyrin III": "CC1=C(C2=CC3=NC(=CC4=C(C(=C([N-]4)C=C5C(=C(C(=N5)C=C1[N-]2)C)CCC(=O)O)C)CCC(=O)O)C(=C3CCC(=O)O)C)CCC(=O)O.[Fe+2]",
    "heme d1": "[H+].[H+].[H+].[H+].CC1=C(C2=CC3=C(C(=C([N-]3)C=C4C(C(=O)C(=N4)C=C5C(C(=O)C(=N5)C=C1[N-]2)(C)CC(=O)[O-])(C)CC(=O)[O-])C)/C=C/C(=O)[O-])CCC(=O)[O-].[Fe+2]",
    "zinc protoporphyrin": "CC1=C(C2=CC3=NC(=CC4=C(C(=C([N-]4)C=C5C(=C(C(=N5)C=C1[N-]2)C)C=C)C)C=C)C(=C3CCC(=O)O)C)CCC(=O)O.[Zn+2]",
    "copper phthalocyanine": "C1=CC=C2C(=C1)C3=NC4=NC(=NC5=C6C=CC=CC6=C([N-]5)N=C7C8=CC=CC=C8C(=N7)N=C2[N-]3)C9=CC=CC=C94.[Cu+2]",
    "chlorophyll a": "CCC1=C(C2=NC1=CC3=C(C4=C([N-]3)C(=C5[C@H]([C@@H](C(=N5)C=C6C(=C(C(=C2)[N-]6)C=C)C)C)CCC(=O)OC/C=C(\\C)/CCC[C@H](C)CCC[C@H](C)CCCC(C)C)[C@H](C4=O)C(=O)OC)C)C.[Mg+2]",
    "bacteriochlorophyll a": "CC[C@@H]1[C@H](C2=CC3=C(C(=C([N-]3)C=C4[C@H]([C@@H](C(=N4)C5=C6C(=C(C(=CC1=N2)[N-]6)C)C(=O)[C@@H]5C(=O)OC)CCC(=O)OC/C=C(\\C)/CCC[C@H](C)CCC[C@H](C)CCCC(C)C)C)C)C(=O)C)C.[Mg+2]",
    "cyanocobalamin": "CC1=CC2=C(C=C1C)[N+](=CN2)[C@@H]3[C@@H]([C@@H]([C@H](O3)CO)OP(=O)(O)O[C@H](C)CNC(=O)CC[C@@]4([C@H]([C@@H]5[C@]6([C@@]([C@@H](C(=N6)/C(=C\\7/[C@@]([C@@H](/C(=C/C8=N/C(=C(\\C4=N5)/C)/[C@H](C8(C)C)CCC(=N)[O-])/N7)CCC(=N)[O-])(C)CC(=O)N)/C)CCC(=N)[O-])(C)CC(=O)N)C)CC(=O)N)C)O.[C]#N.[Co+2]",
    # metallfrei: nur das Layout darf besser werden
    "protoporphyrin IX": "CC1=C(C2=CC3=NC(=CC4=NC(=CC5=C(C(=C(N5)C=C1N2)C=C)C)C(=C4CCC(=O)O)C)C(=C3C)CCC(=O)O)C=C",
    "coproporphyrin III": "CC1=C(C2=CC3=C(C(=C(N3)C=C4C(=C(C(=N4)C=C5C(=C(C(=N5)C=C1N2)C)CCC(=O)O)C)CCC(=O)O)C)CCC(=O)O)CCC(=O)O",
    # Gegenproben: keine Tetrapyrrole
    "ferrocene": "C1=C[CH]C=C1.C1=C[CH]C=C1.[Fe]",
    "cisplatin": "N.N.Cl[Pt]Cl",
    "Fe-EDTA": "C(CN(CC(=O)[O-])CC(=O)[O-])N(CC(=O)[O-])CC(=O)[O-].[Fe+3]",
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
}

# Bild wird zum Lehrbuchbild: Metall mittig, vier Bindungen.
TEXTBOOK = (
    "heme",
    "hemin",
    "siroheme",
    "12,18-didecarboxysiroheme",
    "Fe-coproporphyrin III",
    "heme d1",
    "zinc protoporphyrin",
    "copper phthalocyanine",
)
# Regel erkennt den Komplex, das Layout fällt aber durch die Qualitätsprüfung
# — Bild bleibt wie vorher statt schlechter. Bakteriochlorophyll, Cobalamin:
# Bindungen kreuzen sich. Chlorophyll a: der fünfte Ring wird verzerrt
# (Bindungen 0,80 und 2,06 statt 1,5; gemessen 10.11.2026).
TOO_HARD = ("chlorophyll a", "bacteriochlorophyll a", "cyanocobalamin")
METAL_FREE = ("protoporphyrin IX", "coproporphyrin III")
UNRELATED = ("ferrocene", "cisplatin", "Fe-EDTA", "aspirin")


def _mol(name: str) -> Chem.Mol:
    return Chem.MolFromSmiles(SMILES[name])


def _positions(mol):
    return [tuple(round(v, 4) for v in p) for p in mol.GetConformer().GetPositions()]


def _default_layout(mol):
    ref = Chem.Mol(mol)
    AllChem.Compute2DCoords(ref)
    return _positions(ref)


def _metal_and_nitrogens(mol):
    ns, _ = tetrapyrrole_core(mol)
    return central_metal(mol, ns), ns


# --- Erkennung ----------------------------------------------------------------


@pytest.mark.parametrize("name", TEXTBOOK + TOO_HARD)
def test_rule_finds_the_metal_in_the_macrocycle(name):
    mol = _mol(name)
    found = tetrapyrrole_core(mol)
    assert found is not None
    ns, _ = found
    assert len(ns) == 4
    assert all(mol.GetAtomWithIdx(n).GetSymbol() == "N" for n in ns)
    metal = central_metal(mol, ns)
    assert metal is not None
    assert mol.GetAtomWithIdx(metal).GetSymbol() in {"Fe", "Zn", "Cu", "Mg", "Co"}


@pytest.mark.parametrize("name", METAL_FREE)
def test_metal_free_macrocycle_is_found_but_gets_no_metal(name):
    mol = _mol(name)
    ns, _ = tetrapyrrole_core(mol)
    assert central_metal(mol, ns) is None


@pytest.mark.parametrize("name", UNRELATED)
def test_rule_ignores_what_is_no_tetrapyrrole(name):
    assert tetrapyrrole_core(_mol(name)) is None


def test_alkali_counter_ion_never_lands_in_the_ring():
    """Natriumsalz eines Porphyrins: Na⁺ ist Gegenion, kein Zentralatom."""
    ppix = SMILES["protoporphyrin IX"]
    for salt in (ppix + ".[Na+]", ppix.replace("CCC(=O)O", "CCC(=O)[O-]") + ".[Na+].[Na+]"):
        mol = Chem.MolFromSmiles(salt)
        ns, _ = tetrapyrrole_core(mol)
        assert central_metal(mol, ns) is None


def test_two_metals_or_a_foreign_ligand_on_the_metal_do_not_count():
    two = Chem.MolFromSmiles(SMILES["heme"] + ".[Zn+2]")
    ns, _ = tetrapyrrole_core(two)
    assert central_metal(two, ns) is None
    # Metall schon an etwas anderes als die vier N gebunden: kein Eingriff
    bound = Chem.MolFromSmiles(SMILES["heme"].replace(".[Fe+2]", ".Cl[Fe+3]"))
    ns, _ = tetrapyrrole_core(bound)
    assert central_metal(bound, ns) is None


def test_open_chain_tetrapyrrole_is_no_macrocycle():
    """Bilirubin: vier Pyrrole in Kette, kein Ring um eine Mitte."""
    bilirubin = Chem.MolFromSmiles(
        "CC1=C(NC(=O)C1=C)C=C2C(=C(C(=N2)CC3=C(C(=C(N3)C=C4C(=C(C(=O)N4)C=C)C)C)CCC(=O)O)CCC(=O)O)C"
    )
    assert tetrapyrrole_core(bilirubin) is None


# --- Layout -------------------------------------------------------------------


@pytest.mark.parametrize("name", TEXTBOOK)
def test_metal_sits_in_the_middle_of_the_four_nitrogens(name):
    mol = generate_2d(_mol(name))
    metal, ns = _metal_and_nitrogens(mol)
    conf = mol.GetConformer()
    m = conf.GetAtomPosition(metal)
    dists = [(conf.GetAtomPosition(n) - m).Length() for n in ns]
    cx = sum(conf.GetAtomPosition(n).x for n in ns) / 4
    cy = sum(conf.GetAtomPosition(n).y for n in ns) / 4
    assert abs(m.x - cx) < 0.15 and abs(m.y - cy) < 0.15
    # Quadrat, nicht Raute: alle vier N gleich weit vom Metall
    assert max(dists) - min(dists) < 0.25 * min(dists)


@pytest.mark.parametrize("name", TEXTBOOK + METAL_FREE)
def test_macrocycle_keeps_the_project_bond_length(name):
    """CoordGen legt Bindungen auf 1,0, das Projekt auf 1,5 — Reaktion,
    Vergleich und CDXML mischen sonst zwei Maßstäbe."""
    mol = generate_2d(_mol(name))
    conf = mol.GetConformer()
    lengths = sorted(
        (conf.GetAtomPosition(b.GetBeginAtomIdx()) - conf.GetAtomPosition(b.GetEndAtomIdx())).Length()
        for b in mol.GetBonds()
    )
    assert abs(lengths[len(lengths) // 2] - 1.5) < 0.05


@pytest.mark.parametrize("name", METAL_FREE)
def test_metal_free_macrocycle_gets_the_macrocycle_layout(name):
    """Vorher: Pyrrole zu Dreiecken gestaucht. Jetzt regelmäßige Fünfringe."""
    mol = generate_2d(_mol(name))
    assert _positions(mol) != _default_layout(_mol(name))
    ns, _ = tetrapyrrole_core(mol)
    conf = mol.GetConformer()
    for ring in mol.GetRingInfo().AtomRings():
        if len(ring) == 5 and set(ring) & set(ns):
            for a, b in zip(ring, ring[1:] + ring[:1]):
                d = (conf.GetAtomPosition(a) - conf.GetAtomPosition(b)).Length()
                assert 1.3 < d < 1.7


@pytest.mark.parametrize("name", TOO_HARD + UNRELATED)
def test_everything_else_keeps_its_old_layout(name):
    mol = _mol(name)
    assert _positions(generate_2d(mol)) == _default_layout(mol)


# --- Identität ----------------------------------------------------------------


def _identity(mol):
    # Ohne Konformer: InChI liest E/Z sonst aus den 2D-Koordinaten (Ring-
    # doppelbindungen im 16-Ring) — das täte jedes Layout, auch das alte.
    # Der InChIKey im Payload kommt aus dem SMILES der Quelle, nie von hier.
    mol = Chem.Mol(mol)
    mol.RemoveAllConformers()
    return (
        mol.GetNumAtoms(),
        mol.GetNumBonds(),
        [a.GetFormalCharge() for a in mol.GetAtoms()],
        rdMolDescriptors.CalcMolFormula(mol),
        round(Descriptors.MolWt(mol), 6),
        Chem.MolToSmiles(mol),
        Chem.MolToInchiKey(mol),
    )


@pytest.mark.parametrize("name", [n for n in TEXTBOOK if n != "heme d1"] + list(METAL_FREE))
def test_generate_2d_changes_coordinates_only(name):
    """Die Koordinationsbindungen sind eine Zeichenhilfe, kein neuer Stoff."""
    assert _identity(generate_2d(_mol(name))) == _identity(_mol(name))


def test_loose_protons_go_back_onto_the_carboxylates():
    """Häm d1 kommt als vier [H⁺] + Tetracarboxylat. Gezeichnet würden vier
    schwebende H⁺; zurück auf die Carboxylate gesetzt ist es dieselbe
    Summenformel, dieselbe Masse, dieselbe Nettoladung — die Säure, wie sie
    im Lehrbuch steht. Das SMILES im Payload bleibt das der Quelle."""
    src = _mol("heme d1")
    mol = generate_2d(src)
    assert not [a for a in mol.GetAtoms() if a.GetAtomicNum() == 1 and a.GetDegree() == 0]
    assert rdMolDescriptors.CalcMolFormula(mol) == rdMolDescriptors.CalcMolFormula(src)
    assert round(Descriptors.MolWt(mol), 6) == round(Descriptors.MolWt(src), 6)
    assert Chem.GetFormalCharge(mol) == Chem.GetFormalCharge(src)
    assert sum(a.GetFormalCharge() == -1 and a.GetSymbol() == "O" for a in mol.GetAtoms()) == 0


def test_loose_protons_stay_when_they_have_no_carboxylate():
    """Ohne passende Carboxylate wird nichts umgehängt."""
    src = Chem.MolFromSmiles("[H+]." + SMILES["heme"])
    mol = generate_2d(src)
    assert _identity(mol) == _identity(src)


@pytest.mark.parametrize("name", ("siroheme", "chlorophyll a"))
def test_stereo_warnings_and_cip_labels_stay(name):
    from rdkit.Chem import rdCIPLabeler

    src, mol = _mol(name), generate_2d(_mol(name))
    assert find_unspecified_stereo(mol) == find_unspecified_stereo(src)
    drawn = coordination_drawing(mol)
    labels = []
    for m in (Chem.Mol(src), Chem.Mol(drawn)):
        rdCIPLabeler.AssignCIPLabels(m)
        labels.append({a.GetIdx(): a.GetProp("_CIPCode") for a in m.GetAtoms() if a.HasProp("_CIPCode")})
    assert labels[0] == labels[1]


# --- Zeichnung ----------------------------------------------------------------


def _added_bonds(mol, drawn):
    return [
        b for b in drawn.GetBonds() if mol.GetBondBetweenAtoms(b.GetBeginAtomIdx(), b.GetEndAtomIdx()) is None
    ]


def test_heme_is_drawn_as_the_textbook_complex():
    """Zwei N⁻ binden kovalent (Strich), die zwei Imin-N koordinativ (Pfeil);
    damit verschwinden die Ladungen an N und Fe — eine gültige Lewis-Formel
    desselben Stoffs, Nettoladung unverändert."""
    mol = generate_2d(_mol("heme"))
    drawn = coordination_drawing(mol)
    added = _added_bonds(mol, drawn)
    assert len(added) == 4
    kinds = sorted(str(b.GetBondType()) for b in added)
    assert kinds == ["DATIVE", "DATIVE", "SINGLE", "SINGLE"]
    assert all(a.GetFormalCharge() == 0 for a in drawn.GetAtoms())
    assert Chem.GetFormalCharge(drawn) == Chem.GetFormalCharge(mol)
    assert drawn.GetNumAtoms() == mol.GetNumAtoms()
    assert rdMolDescriptors.CalcMolFormula(drawn) == rdMolDescriptors.CalcMolFormula(mol)


def test_charges_that_do_not_pair_up_stay_visible():
    """Hämin: Fe³⁺ + zwei N⁻ → Fe⁺ neben Cl⁻. Neutrales Co/Fe-Record: nur Pfeile."""
    drawn = coordination_drawing(generate_2d(_mol("hemin")))
    fe = next(a for a in drawn.GetAtoms() if a.GetSymbol() == "Fe")
    assert fe.GetFormalCharge() == 1
    mol = generate_2d(_mol("12,18-didecarboxysiroheme"))
    drawn = coordination_drawing(mol)
    assert sorted(str(b.GetBondType()) for b in _added_bonds(mol, drawn)) == ["DATIVE"] * 4


@pytest.mark.parametrize("name", TOO_HARD + UNRELATED + METAL_FREE)
def test_no_lines_without_the_textbook_geometry(name):
    mol = generate_2d(_mol(name))
    assert coordination_drawing(mol) is mol


def test_existing_metal_bonds_are_not_doubled():
    drawn = coordination_drawing(generate_2d(_mol("heme")))
    again = coordination_drawing(drawn)
    assert again.GetNumBonds() == drawn.GetNumBonds()


def test_drawing_copes_with_explicit_hydrogens():
    mol = generate_2d(_mol("heme"))
    mol_h = Chem.AddHs(mol, addCoords=True)
    assert len(_added_bonds(mol_h, coordination_drawing(mol_h))) == 4


def test_panel_and_file_draw_the_same_metal_bonds():
    """UI-Vorschau und Datei-Export gehen beide durch coordination_drawing —
    RDKits SVG markiert jede Bindung mit den Atomen, die sie verbindet."""
    from chemdraw_tool.image_export import render_molecule_svg
    from chemdraw_tool.svg_renderer import render_svg

    mol = generate_2d(_mol("siroheme"))
    metal, ns = _metal_and_nitrogens(mol)
    for svg in (render_svg(mol, fill_container=True), render_molecule_svg(mol)):
        for n in ns:
            pair = (f"atom-{min(n, metal)} atom-{max(n, metal)}")
            assert pair in svg, pair


def test_atom_overlay_matches_the_drawing():
    """Tooltips sitzen über den gezeichneten Atomen: Atomliste und Zeichnung
    kommen aus demselben Zeichen-Mol, das Eisen liegt mitten zwischen den N."""
    from chemdraw_tool.svg_renderer import extract_atom_data

    mol = generate_2d(_mol("heme"))
    metal, ns = _metal_and_nitrogens(mol)
    atoms = extract_atom_data(mol)
    assert len(atoms) == mol.GetNumAtoms()
    cx = sum(atoms[n]["x"] for n in ns) / 4
    cy = sum(atoms[n]["y"] for n in ns) / 4
    assert abs(atoms[metal]["x"] - cx) < 3 and abs(atoms[metal]["y"] - cy) < 3
    # Ladung im Tooltip ist die der Quelle
    assert atoms[metal]["charge"] == 2


def test_other_views_do_not_crash(tmp_path):
    """All-H, abgekürzte Gruppen, Stereo-Annotation, CDXML, 3D, Gruppen."""
    from chemdraw_tool.cdxml_writer import write_cdxml
    from chemdraw_tool.render_style import condense_groups
    from chemdraw_tool.structure3d import atoms_and_bonds, embed_3d
    from chemdraw_tool.svg_renderer import extract_functional_groups, render_svg
    from chemdraw_tool.validator import validate_roundtrip

    for name in ("heme", "siroheme"):
        src = _mol(name)
        mol = generate_2d(src)
        assert "<svg" in render_svg(Chem.AddHs(mol, addCoords=True), fill_container=True)
        assert "<svg" in render_svg(condense_groups(mol), fill_container=True)
        assert "<svg" in render_svg(mol, annotate_stereo=True)
        assert extract_functional_groups(mol) == extract_functional_groups(src)
        content = write_cdxml(mol, str(tmp_path / f"{name}.cdxml"), name=name)
        assert validate_roundtrip(mol, content).valid
        atoms3d, _ = atoms_and_bonds(embed_3d(src))
        assert atoms3d


def test_reaction_comparison_and_scope_draw_the_metal_bonds_too():
    """Auch in Reaktion und Vergleich sitzt das Metall verbunden in der
    Ringmitte. Geprüft über die
    Gleichheit mit einem Bild, dessen Bindungen schon vorher gesetzt sind."""
    from chemdraw_tool.image_export import render_comparison_svg, render_reaction_svg
    from chemdraw_tool.scope import ScopeItem, render_scope_svg

    sh = generate_2d(_mol("siroheme"))
    dd = generate_2d(_mol("heme d1"))
    sh_d, dd_d = coordination_drawing(sh), coordination_drawing(dd)
    assert render_reaction_svg([sh], [dd]) == render_reaction_svg([sh_d], [dd_d])
    # Vergleich: die Hervorhebung kommt aus der MCS der Quell-Mols, ein
    # Bytevergleich mit vorab gebundenen Mols misst also etwas anderes.
    svg = render_comparison_svg([sh, dd])
    metal, ns = _metal_and_nitrogens(sh)
    for n in ns:
        assert f"atom-{min(n, metal)} atom-{max(n, metal)}" in svg
    assert render_scope_svg([ScopeItem(sh, "a"), ScopeItem(dd, "b")]) == render_scope_svg(
        [ScopeItem(sh_d, "a"), ScopeItem(dd_d, "b")]
    )


def test_a_failing_drawing_helper_falls_back_to_the_old_picture(monkeypatch):
    """Nur neun Strukturen sind gemessen. Wirft die Lewis-Umformung bei einer
    unbekannten, bleibt es beim alten Bild statt beim Absturz."""
    from chemdraw_tool import generator

    def broken(*_args, **_kwargs):
        raise ValueError("Sanitize kaputt")

    monkeypatch.setattr(generator, "_with_metal_bonds", broken)
    src = _mol("heme")
    assert _positions(generate_2d(src)) == _default_layout(src)
    laid_out = Chem.Mol(src)
    AllChem.Compute2DCoords(laid_out)
    assert coordination_drawing(laid_out) is laid_out


@pytest.mark.parametrize("name", ("siroheme", "heme"))
def test_abbreviated_groups_keep_the_metal_bonds(name):
    """Abgekürzte Gruppen sind Dummy-Atome (Ordnungszahl 0) — die zählen
    nicht als zweites Metall."""
    from chemdraw_tool.render_style import condense_groups

    mol = generate_2d(_mol(name))
    condensed = condense_groups(mol)
    assert any(a.GetAtomicNum() == 0 for a in condensed.GetAtoms())
    assert len(_added_bonds(condensed, coordination_drawing(condensed))) == 4


def test_heme_d1_keeps_its_inchikey():
    """Protonen umgehängt, Stoff derselbe: InChIKey wie die Quelle, und wie
    die von Hand protonierte Säure (E-Doppelbindung festgehalten)."""
    src = _mol("heme d1")
    acid = Chem.MolFromSmiles(
        "CC1=C(C2=CC3=C(C(=C([N-]3)C=C4C(C(=O)C(=N4)C=C5C(C(=O)C(=N5)C=C1[N-]2)(C)CC(=O)O)(C)CC(=O)O)C)/C=C/C(=O)O)CCC(=O)O.[Fe+2]"
    )
    mol = Chem.Mol(generate_2d(src))
    mol.RemoveAllConformers()
    assert Chem.MolToInchiKey(mol) == Chem.MolToInchiKey(src) == Chem.MolToInchiKey(acid)
    assert Chem.MolToSmiles(mol) == Chem.MolToSmiles(acid)


def test_comparison_counts_the_shared_metal_as_common():
    """Vergleich von vier Fe-Tetrapyrrolen: das Eisen haben alle vier — es darf nicht als
    Unterschied rot markiert werden (vorher: eigenes Fragment, nie im MCS)."""
    from chemdraw_tool import image_export

    names = ("siroheme", "heme d1", "hemin", "heme")
    mols = [generate_2d(_mol(n)) for n in names]
    atom_hl, _ = image_export._comparison_highlights(mols)
    for mol, highlighted in zip(mols, atom_hl):
        metal, _ = _metal_and_nitrogens(mol)
        assert metal not in highlighted
    # ein Metall, das nicht alle tragen, bleibt Unterschied
    mixed = [generate_2d(_mol("heme")), generate_2d(_mol("zinc protoporphyrin"))]
    atom_hl, _ = image_export._comparison_highlights(mixed)
    assert any(mixed[0].GetAtomWithIdx(i).GetSymbol() == "Fe" for i in atom_hl[0])


# --- Metallfreies Porphin achsparallel (E17, 10.11.2026) ----------------------
# Befund: Porphin wirkte „verzerrt“ neben dem sauberen Phthalocyanin. Gemessen:
# Bindungen 1,50–1,51, N-Quadrat exakt, nichts kreuzt — aber CoordGen legt den
# metallfreien Kern um 11,5° gedreht, Häm (0,7°) und Phthalocyanin (0,1°)
# achsparallel. Jetzt steht jedes Makrozyklus-Bild mit den Pyrrolen oben,
# unten, links und rechts; unter 2° bleibt das Bild unverändert.
PORPHINE = "C1=CC2=CC3=CC=C(N3)C=C4C=CC(=N4)C=C5C=CC(=N5)C=C1N2"  # PubChem CID 66868


def _n_tilt(mol):
    import math

    ns, _ = tetrapyrrole_core(mol)
    conf = mol.GetConformer()
    pts = [conf.GetAtomPosition(n) for n in ns]
    cx, cy = sum(p.x for p in pts) / 4, sum(p.y for p in pts) / 4
    tilts = []
    for p in pts:
        a = math.degrees(math.atan2(p.y - cy, p.x - cx)) % 90
        tilts.append(min(a, 90 - a))
    return max(tilts)


@pytest.mark.parametrize("smiles", [PORPHINE, SMILES["protoporphyrin IX"], SMILES["coproporphyrin III"]])
def test_metal_free_porphyrin_is_axis_aligned(smiles):
    mol = Chem.MolFromSmiles(smiles)
    drawn = generate_2d(mol)
    assert _n_tilt(drawn) < 1.0
    # Identität: dieselbe wie ohne Drehung (eine InChI aus 2D-Koordinaten liest
    # Ring-Doppelbindungen als E/Z — das war vorher schon so) und dasselbe SMILES.
    from chemdraw_tool import generator

    unrotated = generator._macrocycle_layout(mol, align=False)
    assert Chem.MolToInchiKey(drawn) == Chem.MolToInchiKey(unrotated)
    assert Chem.MolToSmiles(drawn) == Chem.MolToSmiles(mol)


@pytest.mark.parametrize("name", ["heme", "copper phthalocyanine"])
def test_already_aligned_macrocycles_keep_their_coordinates(name):
    from chemdraw_tool import generator

    mol = _mol(name)
    drawn = generate_2d(mol)
    unrotated = generator._macrocycle_layout(mol, align=False)
    assert _positions(drawn) == _positions(unrotated)
