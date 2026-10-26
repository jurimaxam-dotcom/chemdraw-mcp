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


# --- Etappe 3: Pfeiltyp + Bedingungen unter dem Pfeil ----------------------


def _fischer_mols():
    return [
        ("CCO", _make_mol("CCO")),
        ("CC(=O)O", _make_mol("CC(=O)O")),
        ("CCOC(C)=O", _make_mol("CCOC(C)=O")),
        ("O", _make_mol("O")),
    ]


@patch("chemdraw_tool.server.resolve")
def test_reaction_payload_carries_arrow_and_below_text(mock_resolve):
    mock_resolve.side_effect = _fischer_mols()
    result = generate_reaction(
        reactants=["ethanol", "acetic acid"],
        products=["ethyl acetate", "water"],
        conditions="H2SO4 (cat.)",
        conditions_below="reflux, 2 h",
        arrow="equilibrium",
        formats=["png", "svg", "cdxml"],
    )
    assert result.arrow == "equilibrium"
    # Formeln tiefgestellt, Zeiten nicht — einmal im Server für alle Ausgaben.
    assert result.conditions == "H₂SO₄ (cat.)"
    assert result.conditions_below == "reflux, 2 h"
    svg = open(result.files["svg"], encoding="utf-8").read()
    assert "H₂SO₄ (cat.)" in svg and "reflux, 2 h" in svg
    cdxml = open(result.cdxml_path, encoding="utf-8").read()
    assert 'ArrowheadTail="HalfLeft"' in cdxml
    assert 'face="32"' in cdxml


@patch("chemdraw_tool.server.resolve")
def test_reaction_payload_defaults(mock_resolve):
    mock_resolve.side_effect = [("CC", _make_mol("CC")), ("C=C", _make_mol("C=C"))]
    result = generate_reaction(reactants=["Ethan"], products=["Ethen"])
    assert result.arrow == "forward"
    assert result.conditions_below == ""


def test_generate_reaction_rejects_unknown_arrow():
    """Das Literal steht im Schema; der Aufruf über den MCP-Weg prüft es.
    Direktaufruf: spätestens der Renderer lehnt ab, bevor Dateien entstehen."""
    with patch("chemdraw_tool.server.resolve") as mock_resolve:
        mock_resolve.side_effect = [("CC", _make_mol("CC")), ("C=C", _make_mol("C=C"))]
        with pytest.raises(ValueError, match="arrow"):
            generate_reaction(reactants=["Ethan"], products=["Ethen"], arrow="resonance")


@patch("chemdraw_tool.server.resolve")
def test_default_filename_unchanged_and_new_options_get_their_own(mock_resolve, tmp_path):
    """Ohne Titel: Standardwerte behalten den bisherigen Dateinamen (der
    Fingerabdruck läuft nur über die alten Eingaben), ein anderer Pfeil oder
    Untertext ergibt eine eigene Datei statt die vorige zu überschreiben."""
    from chemdraw_tool.server import _default_slug

    def run(**kw):
        mock_resolve.side_effect = [("CC", _make_mol("CC")), ("C=C", _make_mol("C=C"))]
        return generate_reaction(reactants=["CC"], products=["C=C"], conditions="Δ", **kw)

    plain = run()
    expected = _default_slug("reaktion", ["CC"], ["C=C"], "Δ")
    assert plain.files["png"].endswith(f"{expected}.png")
    assert run(arrow="forward", conditions_below="").files["png"] == plain.files["png"]
    eq = run(arrow="equilibrium").files["png"]
    below = run(conditions_below="2 h").files["png"]
    assert len({plain.files["png"], eq, below}) == 3
