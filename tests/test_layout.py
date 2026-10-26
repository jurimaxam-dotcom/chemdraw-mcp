import pytest
from lxml import etree
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.layout import reaction_to_cdxml


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


def test_returns_valid_xml():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C")],
    )
    root = etree.fromstring(xml_str.encode())
    assert root.tag == "CDXML"


def test_has_correct_fragment_count():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC"), _make_mol("O")],
        products=[_make_mol("CCO")],
    )
    root = etree.fromstring(xml_str.encode())
    fragments = root.findall(".//fragment")
    assert len(fragments) == 3


def test_has_arrow_element():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C")],
    )
    root = etree.fromstring(xml_str.encode())
    arrows = root.findall(".//arrow")
    assert len(arrows) == 1


def test_arrow_head_right_of_tail():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C")],
    )
    root = etree.fromstring(xml_str.encode())
    arrow = root.findall(".//arrow")[0]
    tail = [float(x) for x in arrow.get("Tail3D").split()]
    head = [float(x) for x in arrow.get("Head3D").split()]
    assert head[0] > tail[0]


def test_has_plus_signs_between_reactants():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC"), _make_mol("O")],
        products=[_make_mol("CCO")],
    )
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts if s.text]
    assert any("+" in v for v in text_values)


def test_has_plus_signs_between_products():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C"), _make_mol("O")],
    )
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts if s.text]
    assert any("+" in v for v in text_values)


def test_no_plus_sign_for_single_reactant():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C")],
    )
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts if s.text]
    assert not any("+" in v for v in text_values)


def test_conditions_text_present():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C")],
        conditions="HCl, 0-5 °C",
    )
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts if s.text]
    assert any("HCl" in v for v in text_values)


def test_no_conditions_text_when_empty():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C")],
        conditions="",
    )
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts if s.text]
    assert not any(v.strip() and v != "+" for v in text_values)


def test_name_label_present():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C")],
        name="Dehydrierung",
    )
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts if s.text]
    assert "Dehydrierung" in text_values


def test_molecule_labels_in_cdxml():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC"), _make_mol("O")],
        products=[_make_mol("CCO")],
        reactant_names=["Ethan", "Wasser"],
        product_names=["Ethanol"],
    )
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts if s.text]
    assert "Ethan" in text_values
    assert "Wasser" in text_values
    assert "Ethanol" in text_values


def test_no_molecule_labels_when_names_omitted():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C")],
    )
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts if s.text]
    assert not any(v not in ("+",) and v.strip() for v in text_values)


def test_reactants_left_of_products():
    xml_str = reaction_to_cdxml(
        reactants=[_make_mol("CC")],
        products=[_make_mol("C=C")],
    )
    root = etree.fromstring(xml_str.encode())
    fragments = root.findall(".//fragment")
    assert len(fragments) == 2

    def fragment_center_x(frag):
        nodes = frag.findall("n")
        xs = [float(n.get("p").split()[0]) for n in nodes]
        return sum(xs) / len(xs)

    reactant_x = fragment_center_x(fragments[0])
    product_x = fragment_center_x(fragments[1])
    assert reactant_x < product_x


# ---------------------------------------------------------------------------
# Etappe 3: Pfeiltyp als echtes ChemDraw-Attribut, Text unter dem Pfeil
# ---------------------------------------------------------------------------

# Belegt an ChemDraw-eigenen Dateien: RDKits Testdaten
# Code/GraphMol/test_data/CDXML/chemdraw_template6.cdxml (Gleichgewicht, über
# <graphic ArrowType="Equilibrium" SupersededBy=…>) und chemdraw_template1.cdxml
# (Retro, <graphic ArrowType="RetroSynthetic" SupersededBy=…>).
EXPECTED_ARROW_ATTRS = {
    "forward": {"ArrowheadHead": "Full", "ArrowheadType": "Solid", "ArrowheadTail": None,
                "ArrowShaftSpacing": None},
    "equilibrium": {"ArrowheadHead": "HalfLeft", "ArrowheadTail": "HalfLeft",
                    "ArrowheadType": "Solid", "ArrowShaftSpacing": "300"},
    "retro": {"ArrowheadHead": "Full", "ArrowheadType": "Angle", "ArrowheadTail": None,
              "ArrowShaftSpacing": "600"},
}


def _rxn(**kw):
    return reaction_to_cdxml(
        reactants=[_make_mol("CCO"), _make_mol("CC(=O)O")],
        products=[_make_mol("CCOC(C)=O"), _make_mol("O")],
        **kw,
    )


def _page_texts(xml_str):
    """Freie Texte auf der Seite (nicht die Atomlabels in Fragmenten):
    [(y, Gesamttext, [(Lauftext, face)])]."""
    root = etree.fromstring(xml_str.encode())
    out = []
    for t in root.find("page").findall("t"):
        runs = [(s.text or "", s.get("face")) for s in t.findall("s")]
        out.append((float(t.get("p").split()[1]), "".join(r for r, _ in runs), runs))
    return out


@pytest.mark.parametrize("arrow", sorted(EXPECTED_ARROW_ATTRS))
def test_arrow_type_is_a_chemdraw_attribute(arrow):
    root = etree.fromstring(_rxn(arrow=arrow).encode())
    (el,) = root.findall(".//arrow")
    for attr, value in EXPECTED_ARROW_ATTRS[arrow].items():
        assert el.get(attr) == value, (arrow, attr, el.get(attr))


def test_default_cdxml_is_byte_identical_to_explicit_forward():
    assert _rxn(conditions="Δ") == _rxn(conditions="Δ", arrow="forward", conditions_below="")


def test_unknown_arrow_is_rejected_in_cdxml():
    with pytest.raises(ValueError, match="arrow"):
        _rxn(arrow="resonance")


@pytest.mark.parametrize("arrow", sorted(EXPECTED_ARROW_ATTRS))
def test_rdkit_still_reads_the_cdxml(arrow):
    """RDKits ChemDraw-Leser (aus Revvitys CDX-Bibliothek) muss die Datei mit
    jedem Pfeiltyp noch öffnen und alle vier Moleküle finden."""
    from rdkit import Chem

    mols = Chem.MolsFromCDXML(_rxn(arrow=arrow, conditions="H2SO4", conditions_below="Δ"))
    assert len(mols) == 4


def test_conditions_above_and_below_the_arrow():
    xml_str = _rxn(conditions="H2SO4 (cat.)", conditions_below="80 °C, 2 h", arrow="equilibrium")
    root = etree.fromstring(xml_str.encode())
    arrow_y = float(root.find(".//arrow").get("Head3D").split()[1])
    texts = {text: y for y, text, _ in _page_texts(xml_str)}
    assert texts["H2SO4 (cat.)"] < arrow_y < texts["80 °C, 2 h"]


def test_only_below_text():
    xml_str = _rxn(conditions="", conditions_below="Δ")
    root = etree.fromstring(xml_str.encode())
    arrow_y = float(root.find(".//arrow").get("Head3D").split()[1])
    free = [(y, text) for y, text, _ in _page_texts(xml_str) if text != "+"]
    assert free == [(pytest.approx(free[0][0]), "Δ")]
    assert free[0][0] > arrow_y


def test_formula_digits_become_chemdraw_subscripts():
    """ChemDraw stellt per face="32" tief (RDKit-Testdatei chemdraw_template6:
    Ti(OiPr)<s face="32">4</s>) — kein Unicode-Ersatz im CDXML."""
    xml_str = _rxn(conditions="H2SO4, 80 °C", conditions_below="CH2Cl2")
    runs = {text: r for _, text, r in _page_texts(xml_str)}
    assert runs["H2SO4, 80 °C"] == [
        ("H", None), ("2", "32"), ("SO", None), ("4", "32"), (", 80 °C", None),
    ]
    assert runs["CH2Cl2"] == [("CH", None), ("2", "32"), ("Cl", None), ("2", "32")]


def test_multiline_above_grows_upwards():
    """ChemDraw setzt `p` auf die Grundlinie der ERSTEN Zeile. Mehrzeiliger
    Obertext muss deshalb höher ansetzen, sonst läuft er in den Pfeil."""
    one = {t: y for y, t, _ in _page_texts(_rxn(conditions="Δ"))}["Δ"]
    two = {t: y for y, t, _ in _page_texts(_rxn(conditions="H2SO4\nΔ"))}["H2SO4\nΔ"]
    assert two < one
