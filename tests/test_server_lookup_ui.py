"""Tests for lookup_molecule_data tool — DatabaseView payload."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool import databases
from chemdraw_tool.payloads import DatabasePayload
from chemdraw_tool.server import lookup_molecule_data

FIXTURES = Path(__file__).parent / "__fixtures__"
_NO_GHS = {"status": "empty", "record_title": "", "sources": []}


def _ghs_fixture(name: str) -> dict:
    data = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return {"status": "ok", **databases.parse_ghs(data)}


@pytest.fixture(autouse=True)
def _kein_smiles_rueckweg(monkeypatch):
    """Das Datenblatt holt den Datensatz per InChIKey (die Tests mocken das).
    Liefert der Mock nichts, faellt _pubchem_record auf den SMILES-Weg zurueck —
    der darf hier nicht ans echte Netz."""
    from chemdraw_tool import server

    monkeypatch.setattr(server, "pubchem_properties_by_smiles", lambda smiles: None)
    monkeypatch.setattr(server, "pubchem_synonyms_by_smiles", lambda smiles: (None, []))


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


@patch("chemdraw_tool.server.pubchem_ghs")
@patch("chemdraw_tool.server.pubchem_synonyms_by_inchikey")
@patch("chemdraw_tool.server.pubchem_properties_by_inchikey")
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
    mock_safety.return_value = _NO_GHS

    result = lookup_molecule_data("Aspirin")

    assert isinstance(result, DatabasePayload)
    assert result.type == "database"
    assert "<svg" in result.molecule_svg.lower()
    assert len(result.sources) == 2


@patch("chemdraw_tool.server.pubchem_ghs")
@patch("chemdraw_tool.server.pubchem_synonyms_by_inchikey")
@patch("chemdraw_tool.server.pubchem_properties_by_inchikey")
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
    mock_safety.return_value = _NO_GHS

    result = lookup_molecule_data("Benzol")

    pubchem_src = result.sources[0]
    assert pubchem_src.type == "PubChem"
    assert "241" in pubchem_src.source
    assert pubchem_src.url == "https://pubchem.ncbi.nlm.nih.gov/compound/241"

    row_keys = [r.key for r in pubchem_src.rows]
    assert "CID" in row_keys
    assert "IUPAC name" in row_keys
    assert "Molecular formula" in row_keys
    assert "Molar mass" in row_keys
    assert "XLogP" in row_keys
    assert "TPSA" in row_keys
    assert "H-bond donors" in row_keys
    assert "H-bond acceptors" in row_keys
    assert "InChIKey" in row_keys
    assert "CAS No." in row_keys

    row_map = {r.key: r.val for r in pubchem_src.rows}
    assert row_map["Molecular formula"] == "C6H6"
    assert row_map["Molar mass"] == "78.11 g/mol"
    assert row_map["CAS No."] == "71-43-2"
    assert row_map["H-bond donors"] == "1"
    assert row_map["H-bond acceptors"] == "2"


def _sheet(mock_resolve, mock_props, mock_synonyms, mock_safety, ghs, title, smiles):
    mol = _make_mol(smiles)
    mock_resolve.return_value = (smiles, mol)
    mock_props.return_value = {"CID": 1, "Title": title}
    mock_synonyms.return_value = (None, [])
    mock_safety.return_value = ghs
    return lookup_molecule_data(title)


@patch("chemdraw_tool.server.pubchem_ghs")
@patch("chemdraw_tool.server.pubchem_synonyms_by_inchikey")
@patch("chemdraw_tool.server.pubchem_properties_by_inchikey")
@patch("chemdraw_tool.server.resolve")
def test_ghs_source_groups_caffeine(mock_resolve, mock_props, mock_synonyms, mock_safety):
    """Eine GHS-Quelle (ein Reiter), darin eine Gruppe je PubChem-Referenz."""
    result = _sheet(
        mock_resolve, mock_props, mock_synonyms, mock_safety,
        _ghs_fixture("pubchem_ghs_2519_caffeine.json"), "Caffeine",
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    )

    ghs = [s for s in result.sources if s.type == "GHS"]
    assert len(ghs) == 1, "genau ein GHS-Reiter, sonst sind Quellen unanwählbar"
    ghs_src = ghs[0]
    assert ghs_src.status == "ok"
    assert "Safety" in ghs_src.url
    ids = [g.id for g in ghs_src.groups]
    assert ids == ["ghs-272", "ghs-51", "ghs-262", "ghs-65"]
    assert len(set(ids)) == len(ids)
    lead = ghs_src.groups[0]
    assert lead.lead is True
    assert lead.source.startswith("EU harmonised")
    assert lead.signal == "Warning"
    assert [h.code for h in lead.hazards] == ["H302"]
    assert lead.hazards[0].percent is None
    echa = ghs_src.groups[1]
    assert echa.hazards[0].percent == 98.9
    assert echa.not_classified.percent == 0.6
    assert [g.lead for g in ghs_src.groups[1:]] == [False, False, False]


@patch("chemdraw_tool.server.pubchem_ghs")
@patch("chemdraw_tool.server.pubchem_synonyms_by_inchikey")
@patch("chemdraw_tool.server.pubchem_properties_by_inchikey")
@patch("chemdraw_tool.server.resolve")
def test_ghs_source_groups_nacl_negative(mock_resolve, mock_props, mock_synonyms, mock_safety):
    """Der falsch verknüpfte EU-Eintrag (Azofarbstoff) darf nie vorn stehen."""
    result = _sheet(
        mock_resolve, mock_props, mock_synonyms, mock_safety,
        _ghs_fixture("pubchem_ghs_5234_sodium_chloride.json"), "Sodium chloride",
        "[Na+].[Cl-]",
    )
    ghs_src = next(s for s in result.sources if s.type == "GHS")
    lead, other = ghs_src.groups
    assert lead.id == "ghs-52" and lead.lead
    assert lead.signal == "Warning"
    assert lead.not_classified.percent == 89.2
    assert other.id == "ghs-97" and not other.lead
    assert other.note.startswith("record name differs: product-by-process")


@pytest.mark.parametrize(
    "status, needle",
    [("empty", "no GHS classification"), ("error", "could not be retrieved")],
)
@patch("chemdraw_tool.server.pubchem_ghs")
@patch("chemdraw_tool.server.pubchem_synonyms_by_inchikey")
@patch("chemdraw_tool.server.pubchem_properties_by_inchikey")
@patch("chemdraw_tool.server.resolve")
def test_ghs_empty_and_error_are_told_apart(
    mock_resolve, mock_props, mock_synonyms, mock_safety, status, needle
):
    result = _sheet(
        mock_resolve, mock_props, mock_synonyms, mock_safety,
        {"status": status, "record_title": "", "sources": []}, "Aspirin",
        "CC(=O)Oc1ccccc1C(=O)O",
    )
    ghs_src = next(s for s in result.sources if s.type == "GHS")
    assert ghs_src.status == status
    assert ghs_src.groups == []
    assert needle in ghs_src.note


@patch("chemdraw_tool.server.pubchem_ghs")
@patch("chemdraw_tool.server.pubchem_synonyms_by_inchikey")
@patch("chemdraw_tool.server.pubchem_properties_by_inchikey")
@patch("chemdraw_tool.server.resolve")
def test_no_ghs_when_no_cid_in_props(
    mock_resolve, mock_props, mock_synonyms, mock_safety
):
    """When the PubChem record has no CID, only the PubChem source is present (no GHS)."""
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


@patch("chemdraw_tool.server.pubchem_ghs")
@patch("chemdraw_tool.server.pubchem_synonyms_by_inchikey")
@patch("chemdraw_tool.server.pubchem_properties_by_inchikey")
@patch("chemdraw_tool.server.resolve")
def test_payload_carries_atoms_for_the_hover(
    mock_resolve, mock_props, mock_synonyms, mock_safety
):
    """Ohne Atomliste zeigt das Datenblatt-Panel keinen Tooltip."""
    mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    mock_resolve.return_value = ("CC(=O)Oc1ccccc1C(=O)O", mol)
    mock_props.return_value = {}
    mock_synonyms.return_value = ("50-78-2", ["Aspirin"])
    mock_safety.return_value = _NO_GHS

    result = lookup_molecule_data("Aspirin")

    # Aspirin ohne Wasserstoffe: 13 Schweratome.
    assert len(result.atoms) == 13, "Atomliste fehlt oder ist unvollstaendig"
    assert {a.el for a in result.atoms} == {"C", "O"}
    assert any(a.hCount > 0 for a in result.atoms)


@patch("chemdraw_tool.server.pubchem_ghs")
@patch("chemdraw_tool.server.pubchem_synonyms_by_inchikey")
@patch("chemdraw_tool.server.pubchem_properties_by_inchikey")
@patch("chemdraw_tool.server.resolve")
def test_payload_carries_functional_groups(
    mock_resolve, mock_props, mock_synonyms, mock_safety
):
    """Gruppen-Highlights teilen sich die Komponente mit dem Molekuel-Panel."""
    mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    mock_resolve.return_value = ("CC(=O)Oc1ccccc1C(=O)O", mol)
    mock_props.return_value = {}
    mock_synonyms.return_value = ("50-78-2", ["Aspirin"])
    mock_safety.return_value = _NO_GHS

    result = lookup_molecule_data("Aspirin")

    names = {g.name for g in result.functionalGroups}
    assert "Ester" in names and "Aromat" in names, f"Gruppen fehlen: {names}"


@patch("chemdraw_tool.server.pubchem_ghs")
@patch("chemdraw_tool.server.pubchem_synonyms_by_inchikey")
@patch("chemdraw_tool.server.pubchem_properties_by_inchikey")
@patch("chemdraw_tool.server.resolve")
def test_payload_names_its_compound(
    mock_resolve, mock_props, mock_synonyms, mock_safety
):
    """Der Umschalter zurueck zur Struktur braucht Namen und SMILES."""
    mol = _make_mol("CC(=O)Oc1ccccc1C(=O)O")
    mock_resolve.return_value = ("CC(=O)Oc1ccccc1C(=O)O", mol)
    mock_props.return_value = {}
    mock_synonyms.return_value = ("50-78-2", ["Aspirin"])
    mock_safety.return_value = _NO_GHS

    result = lookup_molecule_data("Aspirin")

    assert result.name == "Aspirin"
    assert result.smiles == "CC(=O)Oc1ccccc1C(=O)O"
