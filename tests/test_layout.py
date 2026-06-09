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
