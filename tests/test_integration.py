
from lxml import etree

from chemdraw_tool.cdxml_writer import write_cdxml
from chemdraw_tool.generator import generate_2d
from chemdraw_tool.layout import reaction_to_cdxml, write_reaction_cdxml
from chemdraw_tool.resolver import resolve


def test_end_to_end_smiles_to_cdxml(tmp_path):
    smiles, mol = resolve("c1ccccc1")
    mol = generate_2d(mol)
    filepath = tmp_path / "benzol.cdxml"
    write_cdxml(mol, str(filepath), name="Benzol")
    assert filepath.exists()
    root = etree.parse(str(filepath)).getroot()
    assert root.tag == "CDXML"
    nodes = root.findall(".//n")
    assert len(nodes) == 6
    bonds = root.findall(".//b")
    assert len(bonds) == 6
    texts = root.findall(".//t/s")
    assert any(s.text == "Benzol" for s in texts)


def test_end_to_end_complex_molecule(tmp_path):
    smiles, mol = resolve("CC(=O)Oc1ccccc1C(=O)O")
    mol = generate_2d(mol)
    filepath = tmp_path / "aspirin.cdxml"
    write_cdxml(mol, str(filepath), name="Aspirin")
    assert filepath.exists()
    root = etree.parse(str(filepath)).getroot()
    nodes = root.findall(".//n")
    assert len(nodes) == 13
    oxygen_nodes = [n for n in nodes if n.get("Element") == "8"]
    assert len(oxygen_nodes) == 4


def test_end_to_end_simple_reaction():
    smiles_r1, mol_r1 = resolve("CCO")
    smiles_r2, mol_r2 = resolve("CC(=O)O")
    smiles_p1, mol_p1 = resolve("CC(=O)OCC")
    smiles_p2, mol_p2 = resolve("O")

    mol_r1 = generate_2d(mol_r1)
    mol_r2 = generate_2d(mol_r2)
    mol_p1 = generate_2d(mol_p1)
    mol_p2 = generate_2d(mol_p2)

    xml_str = reaction_to_cdxml(
        reactants=[mol_r1, mol_r2],
        products=[mol_p1, mol_p2],
        conditions="H₂SO₄, Δ",
        name="Veresterung",
    )
    root = etree.fromstring(xml_str.encode())
    assert root.tag == "CDXML"
    fragments = root.findall(".//fragment")
    assert len(fragments) == 4
    arrows = root.findall(".//arrow")
    assert len(arrows) == 1
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts if s.text]
    assert any("H₂SO₄" in v for v in text_values)
    assert any("Veresterung" in v for v in text_values)


def test_end_to_end_reaction_writes_file(tmp_path):
    smiles, mol_r = resolve("c1ccccc1")
    smiles, mol_p = resolve("c1ccc(O)cc1")
    mol_r = generate_2d(mol_r)
    mol_p = generate_2d(mol_p)

    filepath = tmp_path / "hydroxylierung.cdxml"
    write_reaction_cdxml(
        [mol_r],
        [mol_p],
        str(filepath),
        conditions="KMnO₄",
        name="Hydroxylierung",
    )
    assert filepath.exists()
    root = etree.parse(str(filepath)).getroot()
    assert root.tag == "CDXML"
    assert len(root.findall(".//fragment")) == 2
