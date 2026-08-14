"""Tests for UI resource registration and structured tool payloads."""

from pathlib import Path
from typing import get_type_hints
from unittest.mock import patch

import pytest
from pydantic import BaseModel
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


_UI_META_EXPECTED = {"ui": {"resourceUri": _RESOURCE_URI}}

# Untergrenze, KEINE Sollmenge: geprüft wird die aus der Registrierung
# abgeleitete Menge (siehe _panel_payload_type). Diese Liste schlägt nur an,
# wenn die Ableitung selbst blind wird — etwa nach einem FastMCP-Update.
_KNOWN_PANEL_TOOLS = frozenset(
    {
        "generate_molecule",
        "generate_reaction",
        "batch_generate",
        "generate_mechanism",
        "generate_spectrum",
        "calculate_validation",
        "lookup_molecule_data",
        "export_anki_deck",
        "generate_titration_curve",
        "generate_species_distribution",
        "compare_molecules",
        "generate_3d",
        "export_curated_deck",
    }
)


def _panel_payload_type(tool) -> str | None:
    """Diskriminator-`type` des Rückgabe-Payloads, sonst None.

    Bewusst OHNE Blick auf `tool.meta`: würde die Panel-Erkennung am Meta
    hängen, prüfte sich der Test selbst — ein Tool ohne Meta gälte einfach
    als Nicht-Panel-Tool und bliebe unsichtbar. Kriterium ist deshalb die
    Rückgabe-Annotation: ein Payload-Modell mit `type`-Default ist genau
    das, was App.jsx per switch auswertet.
    """
    try:
        ret = get_type_hints(tool.fn).get("return")
    except Exception:  # pragma: no cover — kaputte Annotation
        return None
    if not (isinstance(ret, type) and issubclass(ret, BaseModel)):
        return None
    field = ret.model_fields.get("type")
    default = getattr(field, "default", None)
    return default if isinstance(default, str) and default else None


def _panel_tools_without_meta(manager) -> list[str]:
    """Namen aller Panel-Tools, denen das UI-Meta fehlt."""
    return sorted(
        tool.name
        for tool in manager.list_tools()
        if _panel_payload_type(tool) and tool.meta != _UI_META_EXPECTED
    )


def test_every_panel_tool_carries_the_ui_meta():
    """Ohne meta=_UI_META öffnet Claude Desktop KEIN App-Panel — das Tool
    'funktioniert' dann scheinbar nicht, obwohl Dateien geschrieben werden
    (generate_spectrum-Bug, 2026-06-11). Die Menge der Panel-Tools kommt aus
    der FastMCP-Registrierung, nicht aus einer gepflegten Konstante: ein neu
    hinzugefügtes Panel-Tool ohne Meta fällt so von selbst auf."""
    from chemdraw_tool.server import mcp

    manager = mcp._tool_manager
    detected = {t.name for t in manager.list_tools() if _panel_payload_type(t)}
    assert _KNOWN_PANEL_TOOLS <= detected, (
        "Panel-Erkennung greift nicht mehr für "
        f"{sorted(_KNOWN_PANEL_TOOLS - detected)} — der Test prüfte sonst ins Leere"
    )
    assert not _panel_tools_without_meta(manager), (
        f"{_panel_tools_without_meta(manager)} sind ohne UI-Meta registriert — "
        "Panel bleibt zu"
    )


def test_panel_meta_check_notices_a_newly_registered_tool():
    """Schärfebeweis für den Test darüber: ein NEU registriertes Panel-Tool
    ohne Meta muss auffallen, ohne dass jemand eine Liste pflegt."""
    from chemdraw_tool.server import mcp

    manager = mcp._tool_manager

    def brandneues_panel_tool() -> MoleculePayload:
        """Attrappe — registriert ohne meta=_UI_META."""
        return MoleculePayload()

    manager.add_tool(brandneues_panel_tool, structured_output=True)
    try:
        assert "brandneues_panel_tool" in _panel_tools_without_meta(manager)
    finally:
        manager._tools.pop("brandneues_panel_tool", None)

    # Aufräumen bewiesen: ohne die Attrappe ist die Registrierung wieder sauber
    assert not _panel_tools_without_meta(manager)


def test_generate_molecule_with_stereo_annotation(tmp_path, monkeypatch):
    """annotate_stereo annotiert Datei-Export UND Chat-Vorschau (Parität)."""
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path)
    payload = generate_molecule("C[C@H](N)C(=O)O", annotate_stereo=True)
    assert "CIP_Code" in payload.svg
    svg_file = Path(payload.files["svg"]).read_text()
    assert "CIP_Code" in svg_file
