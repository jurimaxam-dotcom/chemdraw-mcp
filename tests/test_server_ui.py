"""Tests for UI resource registration and structured tool payloads."""

from pathlib import Path
from unittest.mock import patch

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.payloads import BatchPayload, MoleculePayload, ReactionPayload
from chemdraw_tool.server import (
    _RESOURCE_URI,
    _UI_DIST,
    batch_generate,
    generate_molecule,
    generate_reaction,
)


@pytest.fixture(autouse=True)
def _isolate_output_dirs(tmp_path, monkeypatch):
    """Redirect all CDXML output to a temp directory."""
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path / "mol")
    monkeypatch.setattr("chemdraw_tool.server.REACTION_DIR", tmp_path / "rxn")


def test_ui_dist_exists():
    """The built UI HTML file must exist."""
    dist = Path(__file__).parent.parent / "chemdraw_tool" / "ui" / "dist" / "index.html"
    assert dist.exists(), f"UI dist not found at {dist}"
    content = dist.read_text()
    assert "<!doctype" in content.lower() or "<html" in content.lower()


def test_resource_uri_is_set():
    """Resource URI constant must be defined."""
    assert _RESOURCE_URI == "ui://chem-app/index.html"


def test_ui_dist_path_matches():
    """_UI_DIST must point to the actual dist file."""
    assert _UI_DIST.exists()
    assert _UI_DIST.name == "index.html"


def _make_mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


@patch("chemdraw_tool.server.resolve")
@patch("chemdraw_tool.server.pubchem_properties_by_smiles")
@patch("chemdraw_tool.server.pubchem_synonyms_by_smiles")
def test_generate_molecule_returns_payload(mock_synonyms, mock_props, mock_resolve):
    """generate_molecule must return a MoleculePayload."""
    mol = _make_mol("c1ccccc1")
    mock_resolve.return_value = ("c1ccccc1", mol)
    mock_props.return_value = {"MolecularFormula": "C6H6", "MolecularWeight": 78.11}
    mock_synonyms.return_value = ("71-43-2", [])

    result = generate_molecule("Benzol")

    assert isinstance(result, MoleculePayload)
    assert result.type == "molecule"
    assert "<svg" in result.svg.lower()
    assert result.name == "Benzol"
    # Neue Spec (ChemDraw-Entkopplung): Default PNG+SVG, kein CDXML.
    assert set(result.files) == {"png", "svg"}
    assert result.cdxml_path == ""
    assert result.properties["formula"] == "C6H6"
    assert result.properties["cas"] == "71-43-2"
    assert len(result.atoms) == 6  # benzene ring


@patch("chemdraw_tool.server.resolve")
def test_generate_reaction_returns_payload(mock_resolve):
    """generate_reaction must return a ReactionPayload."""
    mol_r = _make_mol("CC")
    mol_p = _make_mol("C=C")
    mock_resolve.side_effect = [("CC", mol_r), ("C=C", mol_p)]

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
    assert set(result.files) == {"png", "svg"}
    assert result.cdxml_path == ""


@patch("chemdraw_tool.server.resolve")
def test_batch_generate_returns_payload(mock_resolve):
    """batch_generate must return a BatchPayload."""
    mol1 = _make_mol("c1ccccc1")
    mol2 = _make_mol("CC")
    mock_resolve.side_effect = [("c1ccccc1", mol1), ("CC", mol2)]

    result = batch_generate(molecules=["Benzol", "Ethan"])

    assert isinstance(result, BatchPayload)
    assert result.type == "batch"
    assert len(result.molecules) == 2
    assert all(m.type == "molecule" for m in result.molecules)
    assert all(set(m.files) == {"png", "svg"} for m in result.molecules)
    assert result.cdxml_paths == []


def test_every_panel_tool_carries_the_ui_meta():
    """Ohne meta=_UI_META öffnet Claude Desktop KEIN App-Panel — das Tool
    'funktioniert' dann scheinbar nicht, obwohl Dateien geschrieben werden
    (generate_spectrum-Bug, 2026-06-11). Jedes Tool mit eigener View in
    App.jsx muss das Meta tragen."""
    from chemdraw_tool.server import mcp

    panel_tools = (
        "generate_molecule",
        "generate_reaction",
        "batch_generate",
        "generate_mechanism",
        "generate_spectrum",
        "calculate_validation",
        "lookup_molecule_data",
        "export_anki_deck",
    )
    for name in panel_tools:
        tool = mcp._tool_manager.get_tool(name)
        assert tool.meta == {"ui": {"resourceUri": _RESOURCE_URI}}, (
            f"{name} ist ohne UI-Meta registriert — Panel bleibt zu"
        )
