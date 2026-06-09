from unittest.mock import patch

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.payloads import BatchPayload, ReactionPayload
from chemdraw_tool.server import batch_generate, generate_reaction


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Kein Schreiben ins echte ~/ChemDraw-Output, kein Live-PubChem."""
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path / "mol")
    monkeypatch.setattr("chemdraw_tool.server.REACTION_DIR", tmp_path / "rxn")
    with patch("chemdraw_tool.server._enrich_properties", return_value={}):
        yield


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


@patch("chemdraw_tool.server.resolve")
def test_generate_reaction_returns_payload(mock_resolve):
    mol_cc = _make_mol("CC")
    mol_c2 = _make_mol("C=C")
    mock_resolve.side_effect = [("CC", mol_cc), ("C=C", mol_c2)]

    result = generate_reaction(
        reactants=["Ethan"],
        products=["Ethen"],
        conditions="Kat., Δ",
        name="Dehydrierung",
    )
    assert isinstance(result, ReactionPayload)
    assert result.type == "reaction"
    assert result.name == "Dehydrierung"
    assert result.conditions == "Kat., Δ"
    assert len(result.reactants) == 1
    assert len(result.products) == 1
    # Neue Spec (ChemDraw-Entkopplung): Default sind PNG+SVG, kein CDXML.
    assert set(result.files) == {"png", "svg"}
    assert result.cdxml_path == ""


@patch("chemdraw_tool.server.resolve")
def test_batch_generate_returns_payload(mock_resolve):
    mol1 = _make_mol("c1ccccc1")
    mol2 = _make_mol("CC")
    mock_resolve.side_effect = [("c1ccccc1", mol1), ("CC", mol2)]

    result = batch_generate(molecules=["Benzol", "Ethan"])
    assert isinstance(result, BatchPayload)
    assert result.type == "batch"
    assert len(result.molecules) == 2
    assert all(m.type == "molecule" for m in result.molecules)
    assert result.molecules[0].name == "Benzol"
    assert result.molecules[1].name == "Ethan"
    # Neue Spec: Bilddateien pro Molekül, CDXML nur auf Anforderung.
    assert all(set(m.files) == {"png", "svg"} for m in result.molecules)
    assert result.cdxml_paths == []
