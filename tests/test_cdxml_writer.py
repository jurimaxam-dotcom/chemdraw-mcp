from lxml import etree
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.cdxml_writer import mol_to_cdxml


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


def test_returns_valid_xml():
    mol = _make_mol("c1ccccc1")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    assert root.tag == "CDXML"


def test_has_page_element():
    mol = _make_mol("c1ccccc1")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    pages = root.findall(".//page")
    assert len(pages) == 1


def test_benzene_has_6_atoms():
    mol = _make_mol("c1ccccc1")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    nodes = root.findall(".//n")
    assert len(nodes) == 6


def test_benzene_has_6_bonds():
    mol = _make_mol("c1ccccc1")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    bonds = root.findall(".//b")
    assert len(bonds) == 6


def test_oxygen_gets_element_attribute():
    mol = _make_mol("CO")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    nodes = root.findall(".//n")
    elements = [n.get("Element") for n in nodes if n.get("Element")]
    assert "8" in elements


def test_double_bond_gets_order_attribute():
    mol = _make_mol("C=O")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    bonds = root.findall(".//b")
    orders = [b.get("Order") for b in bonds]
    assert "2" in orders


def test_single_bond_has_no_order_attribute():
    mol = _make_mol("CC")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    bonds = root.findall(".//b")
    assert all(b.get("Order") is None for b in bonds)


def test_atoms_have_positions():
    mol = _make_mol("CC")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    nodes = root.findall(".//n")
    for node in nodes:
        p = node.get("p")
        assert p is not None
        parts = p.split()
        assert len(parts) == 2
        float(parts[0])
        float(parts[1])


# --- 4b tests ---
from chemdraw_tool.cdxml_writer import write_cdxml


def test_write_cdxml_creates_file(tmp_path):
    mol = _make_mol("c1ccccc1")
    filepath = tmp_path / "test.cdxml"
    write_cdxml(mol, str(filepath))
    assert filepath.exists()


def test_write_cdxml_content_is_valid_xml(tmp_path):
    mol = _make_mol("c1ccccc1")
    filepath = tmp_path / "test.cdxml"
    write_cdxml(mol, str(filepath))
    root = etree.parse(str(filepath)).getroot()
    assert root.tag == "CDXML"


def test_name_label_in_cdxml():
    mol = _make_mol("c1ccccc1")
    xml_str = mol_to_cdxml(mol, name="Benzol")
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t/s")
    text_values = [s.text for s in texts]
    assert "Benzol" in text_values


def test_no_label_when_name_empty():
    mol = _make_mol("c1ccccc1")
    xml_str = mol_to_cdxml(mol, name="")
    root = etree.fromstring(xml_str.encode())
    texts = root.findall(".//t")
    assert len(texts) == 0


# --- _create_fragment tests ---
from chemdraw_tool.cdxml_writer import _create_fragment


def test_create_fragment_returns_element_and_metadata():
    mol = _make_mol("CC")
    fragment, next_id, bounds = _create_fragment(
        mol, fragment_id=1, node_id_start=2, center_x=100.0, center_y=200.0
    )
    assert fragment.tag == "fragment"
    assert fragment.get("id") == "1"
    nodes = fragment.findall("n")
    assert len(nodes) == 2
    bonds = fragment.findall("b")
    assert len(bonds) == 1
    assert next_id > 2
    assert len(bounds) == 4


def test_create_fragment_centers_at_position():
    mol = _make_mol("CC")
    fragment, _, bounds = _create_fragment(
        mol, fragment_id=1, node_id_start=2, center_x=100.0, center_y=200.0
    )
    min_x, min_y, max_x, max_y = bounds
    center_x = (min_x + max_x) / 2
    center_y_actual = (min_y + max_y) / 2
    assert abs(center_x - 100.0) < 1.0
    assert abs(center_y_actual - 200.0) < 1.0


# --- ACS settings & colortable tests ---
from chemdraw_tool.cdxml_writer import ACS_SETTINGS, ELEMENT_COLORS


def test_acs_settings_in_root():
    mol = _make_mol("C")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    for key, value in ACS_SETTINGS.items():
        assert root.get(key) == value


def test_colortable_present():
    mol = _make_mol("C")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    colortable = root.findall("colortable")
    assert len(colortable) == 1
    colors = colortable[0].findall("color")
    assert len(colors) >= 2


def test_fonttable_present():
    mol = _make_mol("C")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    fonttable = root.findall("fonttable")
    assert len(fonttable) == 1
    fonts = fonttable[0].findall("font")
    assert len(fonts) >= 1
    assert fonts[0].get("name") == "Arial"


def test_oxygen_colored_red():
    mol = _make_mol("CO")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    nodes = root.findall(".//n")
    oxygen_nodes = [n for n in nodes if n.get("Element") == "8"]
    assert len(oxygen_nodes) == 1
    assert oxygen_nodes[0].get("color") == str(ELEMENT_COLORS[8])


def test_nitrogen_colored_blue():
    mol = _make_mol("CN")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    nodes = root.findall(".//n")
    nitrogen_nodes = [n for n in nodes if n.get("Element") == "7"]
    assert len(nitrogen_nodes) == 1
    assert nitrogen_nodes[0].get("color") == str(ELEMENT_COLORS[7])


def test_carbon_has_no_color():
    mol = _make_mol("CC")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    nodes = root.findall(".//n")
    for n in nodes:
        assert n.get("color") is None


def test_sulfur_colored():
    mol = _make_mol("CS")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    nodes = root.findall(".//n")
    sulfur_nodes = [n for n in nodes if n.get("Element") == "16"]
    assert len(sulfur_nodes) == 1
    assert sulfur_nodes[0].get("color") == str(ELEMENT_COLORS[16])


# --- stereo bond tests ---


def test_l_alanine_has_wedge_bond():
    mol = _make_mol("C[C@@H](N)C(=O)O")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    displays = [b.get("Display") for b in root.findall(".//b")]
    assert "WedgeBegin" in displays


def test_d_alanine_has_hashed_wedge():
    mol = _make_mol("C[C@H](N)C(=O)O")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    displays = [b.get("Display") for b in root.findall(".//b")]
    assert "WedgedHashBegin" in displays


def test_achiral_molecule_has_no_display_attribute():
    mol = _make_mol("CCO")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    bonds = root.findall(".//b")
    assert all(b.get("Display") is None for b in bonds)


def test_stereo_bond_exists_for_chiral_center():
    mol = _make_mol("CC[C@H](C)Br")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    displays = [b.get("Display") for b in root.findall(".//b")]
    stereo_displays = [d for d in displays if d in ("WedgeBegin", "WedgedHashBegin")]
    assert len(stereo_displays) >= 1


# --- aromatic bond tests (Kekulé export) ---


def test_benzene_exports_alternating_single_double_bonds():
    mol = _make_mol("c1ccccc1")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    bonds = root.findall(".//b")
    orders = [b.get("Order") for b in bonds]
    double_count = sum(1 for o in orders if o == "2")
    single_count = sum(1 for o in orders if o is None)
    assert double_count == 3
    assert single_count == 3


def test_pyridine_exports_kekulized():
    mol = _make_mol("c1ccncc1")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    bonds = root.findall(".//b")
    orders = [b.get("Order") for b in bonds]
    assert sum(1 for o in orders if o == "2") == 3


def test_naphthalene_exports_kekulized():
    mol = _make_mol("c1ccc2ccccc2c1")
    xml_str = mol_to_cdxml(mol)
    root = etree.fromstring(xml_str.encode())
    bonds = root.findall(".//b")
    orders = [b.get("Order") for b in bonds]
    assert sum(1 for o in orders if o == "2") == 5
