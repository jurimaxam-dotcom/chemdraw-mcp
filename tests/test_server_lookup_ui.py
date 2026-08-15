"""Tests for lookup_molecule_data tool — DatabaseView payload."""

from unittest.mock import patch

from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.payloads import DatabasePayload
from chemdraw_tool.server import lookup_molecule_data


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


@patch("chemdraw_tool.server.pubchem_safety")
@patch("chemdraw_tool.server.pubchem_synonyms")
@patch("chemdraw_tool.server.pubchem_properties")
@patch("chemdraw_tool.server.resolve")
def test_lookup_molecule_data_returns_database_payload(
    mock_resolve, mock_props, mock_synonyms, mock_safety
):
    """lookup_molecule_data must return a DatabasePayload with PubChem + GHS sources."""
    mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    mock_resolve.return_value = ("CC(=O)Oc1ccccc1C(=O)O", mol)
    mock_props.return_value = {
        "CID": 2244,
        "IUPACName": "2-(acetyloxy)benzoic acid",
        "MolecularFormula": "C9H8O4",
        "MolecularWeight": 180.16,
        "XLogP": 1.2,
        "TPSA": 63.6,
        "HBondDonorCount": 1,
        "HBondAcceptorCount": 4,
        "InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
    }
    mock_synonyms.return_value = ("50-78-2", ["Aspirin", "Acetylsalicylic acid"])
    mock_safety.return_value = [
        {"name": "GHS-Gefahrensymbol", "value": "GHS07"},
        {"name": "H-Sätze", "value": "H302, H317, H332"},
    ]

    result = lookup_molecule_data("Aspirin")

    assert isinstance(result, DatabasePayload)
    assert result.type == "database"
    assert "<svg" in result.molecule_svg.lower()
    assert len(result.sources) == 2


@patch("chemdraw_tool.server.pubchem_safety")
@patch("chemdraw_tool.server.pubchem_synonyms")
@patch("chemdraw_tool.server.pubchem_properties")
@patch("chemdraw_tool.server.resolve")
def test_pubchem_source_rows(mock_resolve, mock_props, mock_synonyms, mock_safety):
    """PubChem source rows must include all mapped properties and CAS."""
    mol = _make_mol("c1ccccc1")
    mock_resolve.return_value = ("c1ccccc1", mol)
    mock_props.return_value = {
        "CID": 241,
        "IUPACName": "benzene",
        "MolecularFormula": "C6H6",
        "MolecularWeight": 78.11,
        "XLogP": 2.1,
        "TPSA": 0.0,
        "HBondDonorCount": 1,
        "HBondAcceptorCount": 2,
        "InChIKey": "UHOVQNZJYSORNB-UHFFFAOYSA-N",
    }
    mock_synonyms.return_value = ("71-43-2", [])
    mock_safety.return_value = []

    result = lookup_molecule_data("Benzol")

    pubchem_src = result.sources[0]
    assert pubchem_src.type == "PubChem"
    assert "241" in pubchem_src.source
    assert pubchem_src.url == "https://pubchem.ncbi.nlm.nih.gov/compound/241"

    row_keys = [r.key for r in pubchem_src.rows]
    assert "CID" in row_keys
    assert "IUPAC-Name" in row_keys
    assert "Summenformel" in row_keys
    assert "Molmasse" in row_keys
    assert "LogP" in row_keys
    assert "TPSA" in row_keys
    assert "H-Brücken-Donoren" in row_keys
    assert "H-Brücken-Akzeptoren" in row_keys
    assert "InChIKey" in row_keys
    assert "CAS-Nr." in row_keys

    row_map = {r.key: r.val for r in pubchem_src.rows}
    assert row_map["Summenformel"] == "C6H6"
    assert row_map["Molmasse"] == "78.11 g/mol"
    assert row_map["CAS-Nr."] == "71-43-2"
    assert row_map["H-Brücken-Donoren"] == "1"
    assert row_map["H-Brücken-Akzeptoren"] == "2"


@patch("chemdraw_tool.server.pubchem_safety")
@patch("chemdraw_tool.server.pubchem_synonyms")
@patch("chemdraw_tool.server.pubchem_properties")
@patch("chemdraw_tool.server.resolve")
def test_ghs_source_rows(mock_resolve, mock_props, mock_synonyms, mock_safety):
    """GHS source must contain safety rows when available."""
    mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    mock_resolve.return_value = ("CC(=O)Oc1ccccc1C(=O)O", mol)
    mock_props.return_value = {"CID": 2244}
    mock_synonyms.return_value = (None, [])
    mock_safety.return_value = [
        {"name": "GHS-Gefahrensymbol", "value": "GHS07"},
        {"name": "Signalwort", "value": "Achtung"},
        {"name": "H-Sätze", "value": "H302"},
        {"name": "P-Sätze", "value": ""},  # empty — should be excluded
    ]

    result = lookup_molecule_data("Aspirin")

    assert len(result.sources) == 2
    ghs_src = result.sources[1]
    assert ghs_src.type == "GHS"
    assert "Safety" in ghs_src.url
    assert "2244" in ghs_src.url

    row_keys = [r.key for r in ghs_src.rows]
    assert "GHS-Gefahrensymbol" in row_keys
    assert "Signalwort" in row_keys
    assert "H-Sätze" in row_keys
    # empty value must be excluded
    assert "P-Sätze" not in row_keys


@patch("chemdraw_tool.server.pubchem_safety")
@patch("chemdraw_tool.server.pubchem_synonyms")
@patch("chemdraw_tool.server.pubchem_properties")
@patch("chemdraw_tool.server.resolve")
def test_no_ghs_when_no_cid_in_props(
    mock_resolve, mock_props, mock_synonyms, mock_safety
):
    """When CID is not in pubchem_properties, only PubChem source present (no GHS)."""
    mol = _make_mol("CCO")
    mock_resolve.return_value = ("CCO", mol)
    mock_props.return_value = {}
    mock_synonyms.return_value = (None, [])

    result = lookup_molecule_data("unknown-compound")

    assert len(result.sources) == 1
    assert result.sources[0].type == "PubChem"
    mock_safety.assert_not_called()


# --- Umschalter Struktur <-> Daten (15.08.2026) ------------------------------
#
# Das Datenblatt-Panel zeichnet die Struktur laengst; ihm fehlten nur die
# Atomkoordinaten, damit derselbe Hover wie im Molekuel-Panel funktioniert.
# Die Daten kommen aus dem Mol-Objekt, das hier ohnehin schon vorliegt —
# kein zusaetzlicher Netzabruf, keine zweite Aufloesung des Namens.


@patch("chemdraw_tool.server.pubchem_safety")
@patch("chemdraw_tool.server.pubchem_synonyms")
@patch("chemdraw_tool.server.pubchem_properties")
@patch("chemdraw_tool.server.resolve")
def test_payload_carries_atoms_for_the_hover(
    mock_resolve, mock_props, mock_synonyms, mock_safety
):
    """Ohne Atomliste zeigt das Datenblatt-Panel keinen Tooltip."""
    mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    mock_resolve.return_value = ("CC(=O)Oc1ccccc1C(=O)O", mol)
    mock_props.return_value = {}
    mock_synonyms.return_value = ("50-78-2", ["Aspirin"])
    mock_safety.return_value = []

    result = lookup_molecule_data("Aspirin")

    # Aspirin ohne Wasserstoffe: 13 Schweratome.
    assert len(result.atoms) == 13, "Atomliste fehlt oder ist unvollstaendig"
    assert {a.el for a in result.atoms} == {"C", "O"}
    assert any(a.hCount > 0 for a in result.atoms)


@patch("chemdraw_tool.server.pubchem_safety")
@patch("chemdraw_tool.server.pubchem_synonyms")
@patch("chemdraw_tool.server.pubchem_properties")
@patch("chemdraw_tool.server.resolve")
def test_payload_carries_functional_groups(
    mock_resolve, mock_props, mock_synonyms, mock_safety
):
    """Gruppen-Highlights teilen sich die Komponente mit dem Molekuel-Panel."""
    mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    mock_resolve.return_value = ("CC(=O)Oc1ccccc1C(=O)O", mol)
    mock_props.return_value = {}
    mock_synonyms.return_value = ("50-78-2", ["Aspirin"])
    mock_safety.return_value = []

    result = lookup_molecule_data("Aspirin")

    names = {g.name for g in result.functionalGroups}
    assert "Ester" in names and "Aromat" in names, f"Gruppen fehlen: {names}"


@patch("chemdraw_tool.server.pubchem_safety")
@patch("chemdraw_tool.server.pubchem_synonyms")
@patch("chemdraw_tool.server.pubchem_properties")
@patch("chemdraw_tool.server.resolve")
def test_payload_names_its_compound(
    mock_resolve, mock_props, mock_synonyms, mock_safety
):
    """Der Umschalter zurueck zur Struktur braucht Namen und SMILES."""
    mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    mock_resolve.return_value = ("CC(=O)Oc1ccccc1C(=O)O", mol)
    mock_props.return_value = {}
    mock_synonyms.return_value = ("50-78-2", ["Aspirin"])
    mock_safety.return_value = []

    result = lookup_molecule_data("Aspirin")

    assert result.name == "Aspirin"
    assert result.smiles == "CC(=O)Oc1ccccc1C(=O)O"
