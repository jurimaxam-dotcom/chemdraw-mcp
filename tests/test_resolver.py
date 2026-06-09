from unittest.mock import Mock, patch

import pytest

from chemdraw_tool.resolver import is_smiles, resolve, resolve_name, validate_smiles


def test_is_smiles_recognizes_smiles_with_parens():
    assert is_smiles("CC(=O)Oc1ccccc1C(=O)O") is True


def test_is_smiles_recognizes_simple_ring():
    assert is_smiles("c1ccccc1") is True


def test_is_smiles_recognizes_complex():
    assert is_smiles("CN1C=NC2=C1C(=O)N(C(=O)N2C)C") is True


def test_is_smiles_rejects_plain_name():
    assert is_smiles("Aspirin") is False


def test_is_smiles_rejects_german_name():
    assert is_smiles("Sulfanilsäure") is False


def test_is_smiles_rejects_single_word():
    assert is_smiles("Histidin") is False


def test_validate_smiles_benzene():
    mol = validate_smiles("c1ccccc1")
    assert mol is not None


def test_validate_smiles_aspirin():
    mol = validate_smiles("CC(=O)Oc1ccccc1C(=O)O")
    assert mol is not None


def test_validate_smiles_invalid():
    mol = validate_smiles("definitely_not_a_molecule_XYZ")
    assert mol is None


@patch("chemdraw_tool.resolver.requests.get")
def test_resolve_name_returns_smiles(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 2244, "SMILES": "CC(=O)OC1=CC=CC=C1C(=O)O"}]
        }
    }
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp
    smiles = resolve_name("Aspirin")
    assert smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"


@patch("chemdraw_tool.resolver.requests.get")
def test_resolve_name_calls_pubchem(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "PropertyTable": {"Properties": [{"CID": 1, "SMILES": "O"}]}
    }
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp
    resolve_name("Water")
    url = mock_get.call_args[0][0]
    assert "Water" in url
    assert "pubchem" in url


def test_resolve_smiles_input():
    smiles, mol = resolve("c1ccccc1")
    assert smiles == "c1ccccc1"
    assert mol is not None


@patch("chemdraw_tool.resolver.requests.get")
def test_resolve_name_input(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 2244, "SMILES": "CC(=O)OC1=CC=CC=C1C(=O)O"}]
        }
    }
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp
    smiles, mol = resolve("Aspirin")
    assert smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
    assert mol is not None


def test_resolve_invalid_smiles_raises():
    with pytest.raises(ValueError, match="Could not resolve"):
        resolve("C(C)(C)(C)(C)(C)")


def test_is_smiles_rejects_stereo_prefix_names():
    assert is_smiles("(R)-Limonene") is False
    assert is_smiles("(S)-Ibuprofen") is False
    assert is_smiles("(E)-Stilbene") is False
    assert is_smiles("(Z)-Butene") is False
    assert is_smiles("(+)-Camphor") is False
    assert is_smiles("(-)-Menthol") is False
    assert is_smiles("(±)-Naproxen") is False


def test_is_smiles_still_accepts_valid_smiles_with_parens():
    assert is_smiles("C(=O)O") is True
    assert is_smiles("C(C)C") is True
    assert is_smiles("[C@@H](O)(F)Cl") is True


@patch("chemdraw_tool.resolver.requests.get")
def test_resolve_falls_back_to_name_on_invalid_smiles_parse(mock_get):
    """If is_smiles says True but RDKit can't parse it, try name resolution."""
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 22311, "SMILES": "CC1=CCC(CC1)C(=C)C"}]
        }
    }
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp
    smiles, mol = resolve("(R)-Limonene")
    assert mol is not None
    assert "C" in smiles
