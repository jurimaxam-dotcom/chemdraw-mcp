import re

from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.svg_renderer import (
    database_payload,
    extract_atom_data,
    molecule_payload,
    reaction_payload,
    render_svg,
)


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


def test_render_svg_returns_svg_string():
    mol = _make_mol("CCO")
    svg = render_svg(mol)
    assert svg.startswith("<?xml") or svg.startswith("<svg")
    assert "</svg>" in svg


def test_render_svg_contains_heteroatom_colors():
    """RDKit with default palette renders O atoms in red (#FF0000 or similar)."""
    mol = _make_mol("CCO")
    svg = render_svg(mol)
    # RDKit draws heteroatom bonds/labels with non-black stroke colors.
    # For oxygen this is red (#FF0000). Verify at least one such color is present.
    import re

    stroke_colors = re.findall(r"stroke:(#[0-9A-Fa-f]{6})", svg)
    non_black = [c for c in stroke_colors if c.upper() not in ("#000000", "#FFFFFF")]
    assert len(non_black) > 0, (
        f"Expected a non-black heteroatom stroke color (e.g. #FF0000 for O), "
        f"got stroke colors: {set(stroke_colors)}"
    )


def test_extract_atom_data_returns_list():
    mol = _make_mol("CCO")
    atoms = extract_atom_data(mol)
    assert isinstance(atoms, list)
    assert len(atoms) == mol.GetNumAtoms()


def test_extract_atom_data_fields():
    mol = _make_mol("CCO")
    atoms = extract_atom_data(mol)
    atom = atoms[0]
    assert "idx" in atom
    assert "el" in atom
    assert "x" in atom
    assert "y" in atom
    assert "hCount" in atom
    assert "charge" in atom


def test_extract_atom_data_oxygen_element():
    mol = _make_mol("CCO")
    atoms = extract_atom_data(mol)
    elements = [a["el"] for a in atoms]
    assert "O" in elements


def test_extract_atom_data_coordinates_are_svg_space():
    mol = _make_mol("CCO")
    atoms = extract_atom_data(mol, width=350, height=300)
    for atom in atoms:
        assert 0 <= atom["x"] <= 350
        assert 0 <= atom["y"] <= 300


def test_molecule_payload_structure():
    mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    payload = molecule_payload(
        mol,
        name="Aspirin",
        subtitle="Acetylsalicylsäure",
        properties={"formula": "C9H8O4", "mw": "180.16 g/mol"},
    )
    assert payload["type"] == "molecule"
    assert "<svg" in payload["svg"] or "<?xml" in payload["svg"]
    assert isinstance(payload["atoms"], list)
    assert payload["name"] == "Aspirin"
    assert payload["subtitle"] == "Acetylsalicylsäure"
    assert payload["properties"]["formula"] == "C9H8O4"


def test_molecule_payload_without_optional_fields():
    mol = _make_mol("CCO")
    payload = molecule_payload(mol, name="Ethanol")
    assert payload["type"] == "molecule"
    assert payload["subtitle"] == ""
    assert payload["properties"] == {}


def test_reaction_payload_structure():
    r1 = _make_mol("c1ccc(O)c(C(=O)O)c1")
    p1 = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    payload = reaction_payload(
        reactants=[(r1, "Salicylsäure")],
        products=[(p1, "Aspirin")],
        conditions="H2SO4",
        name="Veresterung",
    )
    assert payload["type"] == "reaction"
    assert payload["name"] == "Veresterung"
    assert payload["conditions"] == "H2SO4"
    assert len(payload["reactants"]) == 1
    assert (
        "<svg" in payload["reactants"][0]["svg"]
        or "<?xml" in payload["reactants"][0]["svg"]
    )
    assert payload["reactants"][0]["name"] == "Salicylsäure"
    assert len(payload["products"]) == 1


def test_database_payload_structure():
    mol = _make_mol("CCO")
    sources = [
        {
            "type": "PubChem",
            "source": "PubChem CID 702",
            "url": "https://pubchem.ncbi.nlm.nih.gov/compound/702",
            "rows": [{"key": "CID", "val": "702"}],
        }
    ]
    payload = database_payload(mol, sources)
    assert payload["type"] == "database"
    assert "<svg" in payload["molecule_svg"] or "<?xml" in payload["molecule_svg"]
    assert len(payload["sources"]) == 1
    assert payload["sources"][0]["type"] == "PubChem"


# --- consistent scale tests ---


def _viewbox_size(svg: str) -> tuple[float, float]:
    m = re.search(r"viewBox=['\"]([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)['\"]", svg)
    assert m, f"No viewBox found in SVG: {svg[:300]}"
    return float(m.group(3)), float(m.group(4))


def test_small_molecule_renders_small():
    """H2O2 should render small (~50-100px wide), not fill the canvas."""
    mol = _make_mol("OO")
    svg = render_svg(mol)
    w, _ = _viewbox_size(svg)
    assert w < 150, f"H2O2 viewBox width should be <150, got {w}"


def test_large_molecule_renders_large():
    """Cholesterol should render with a wide viewBox (>200px)."""
    mol = _make_mol("CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C")
    svg = render_svg(mol)
    w, _ = _viewbox_size(svg)
    assert w > 200, f"Cholesterol viewBox width should be >200, got {w}"


def test_molecules_use_consistent_bond_scale():
    """H2O2 must render smaller than cholesterol — both with same bond pixel scale."""
    h2o2 = _make_mol("OO")
    cholesterol = _make_mol("CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C")
    svg1 = render_svg(h2o2)
    svg2 = render_svg(cholesterol)
    w1, _ = _viewbox_size(svg1)
    w2, _ = _viewbox_size(svg2)
    ratio = w2 / w1
    assert ratio > 3, (
        f"Cholesterol should be >3x wider than H2O2, got {ratio:.2f} "
        f"(H2O2={w1:.0f}, Cholesterol={w2:.0f})"
    )


def test_svg_has_absolute_dimensions():
    """SVG should expose absolute width/height attributes for proportional layout."""
    mol = _make_mol("CCO")
    svg = render_svg(mol)
    assert re.search(r"\bwidth=['\"]\d+(\.\d+)?(px)?['\"]", svg), (
        f"SVG should have absolute pixel width, got: {svg[:300]}"
    )


def test_ui_preview_supports_stereo_annotation():
    """Datei-Export und UI-Vorschau müssen dieselbe Annotation zeigen."""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    from chemdraw_tool.svg_renderer import render_svg

    mol = Chem.MolFromSmiles("C[C@H](N)C(=O)O")
    AllChem.Compute2DCoords(mol)
    assert "CIP_Code" in render_svg(mol, annotate_stereo=True)
    assert "CIP_Code" not in render_svg(mol)
