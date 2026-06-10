from unittest.mock import Mock, patch

import pytest
from rdkit import Chem

from chemdraw_tool.resolver import (
    _opsin_lookup,
    is_smiles,
    resolve,
    resolve_name,
    validate_smiles,
)


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
    # "Aspirin", nicht "Water": OPSIN kennt water und löst es offline,
    # bevor der PubChem-Pfad (den dieser Test prüft) erreicht wird.
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "PropertyTable": {"Properties": [{"CID": 2244, "SMILES": "O"}]}
    }
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp
    resolve_name("Aspirin")
    url = mock_get.call_args[0][0]
    assert "Aspirin" in url
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


# --- Kurze valide SMILES ohne Sonderzeichen (Regression: Screenshot 2026-06-10) ---
# "O" ging als NAME an PubChem → molekularer Sauerstoff O=O statt Wasser;
# "CO" → Cobalt [Co] statt Methanol. Der Tool-Docstring verspricht
# "SMILES strings are always safe" → resolve() muss parse-first arbeiten.


@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_water_smiles_offline(mock_pubchem):
    """'O' ist valides SMILES (Wasser) und darf NIE ins Netz gehen."""
    smiles, mol = resolve("O")
    mock_pubchem.assert_not_called()
    assert smiles == "O"
    assert mol.GetNumAtoms() == 1
    assert mol.GetAtomWithIdx(0).GetSymbol() == "O"


@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_methanol_smiles_offline(mock_pubchem):
    """'CO' ist valides SMILES (Methanol), nicht der Name von Cobalt."""
    smiles, mol = resolve("CO")
    mock_pubchem.assert_not_called()
    assert smiles == "CO"
    symbols = sorted(a.GetSymbol() for a in mol.GetAtoms())
    assert symbols == ["C", "O"]


@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_name_path_still_works_for_real_names(mock_pubchem):
    """'Aspirin' parsed nicht als SMILES → Namens-Pfad bleibt intakt."""
    mock_pubchem.return_value = "CC(=O)Oc1ccccc1C(=O)O"
    smiles, mol = resolve("Aspirin")
    mock_pubchem.assert_called_once()
    assert mol.GetNumAtoms() == 13


# --- OPSIN: systematische IUPAC-Namen offline (py2opsin; braucht eine JRE) ---
# PubChem/NCI sind index-basiert und scheitern an systematischen Namen, die in
# keiner DB stehen. OPSIN parst Nomenklatur regelbasiert und offline — er steht
# deshalb VOR den Netz-Lookups in der Kaskade.


def test_opsin_lookup_parses_systematic_name():
    smiles = _opsin_lookup("propan-2-ol")
    assert smiles is not None
    assert Chem.CanonSmiles(smiles) == Chem.CanonSmiles("CC(C)O")


def test_opsin_lookup_trivial_name_returns_none():
    """Markennamen kennt OPSIN nicht → None, Kaskade geht weiter."""
    assert _opsin_lookup("Tylenol") is None


@patch("chemdraw_tool.resolver._java_runtime_available", return_value=False)
def test_opsin_lookup_without_java_returns_none(mock_java):
    """Ohne JRE degradiert OPSIN still — kein Crash, Netz-Kaskade übernimmt."""
    assert _opsin_lookup("propan-2-ol") is None


@patch("chemdraw_tool.resolver._nci_cir_lookup")
@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_systematic_iupac_name_offline(mock_pubchem, mock_nci):
    """Systematische Namen dürfen NIE ins Netz gehen — OPSIN löst offline."""
    smiles, mol = resolve("2-methylbutan-2-ol")
    mock_pubchem.assert_not_called()
    mock_nci.assert_not_called()
    symbols = sorted(a.GetSymbol() for a in mol.GetAtoms())
    assert symbols == ["C", "C", "C", "C", "C", "O"]


@patch("chemdraw_tool.resolver._nci_cir_lookup")
@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_systematic_stereo_name_offline(mock_pubchem, mock_nci):
    """(2S)-Stereodeskriptor übersteht OPSIN→RDKit: L-Tryptophan per InChIKey."""
    smiles, mol = resolve("(2S)-2-amino-3-(1H-indol-3-yl)propanoic acid")
    mock_pubchem.assert_not_called()
    assert Chem.MolToInchiKey(mol) == "QIVBCDIJIAJPQS-VIFPVBQESA-N"
