"""Koeffizienten in die Gleichung übernehmen (Grundlagen, Etappe 2).

Der Bilanz-Badge schlägt Koeffizienten vor; der Knopf „Apply coefficients“
ruft generate_reaction mit `coefficients` erneut auf. Dann zeigt die
Zeichnung „2 H₂ + O₂ → 2 H₂O“, und die Bilanz zählt mit den Koeffizienten.
Ohne den Parameter bleibt alles wie bisher.
"""

from unittest.mock import patch

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.image_export import render_reaction_svg
from chemdraw_tool.layout import reaction_to_cdxml
from chemdraw_tool.reaction_balance import check_balance
from chemdraw_tool.server import generate_reaction


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path / "mol")
    monkeypatch.setattr("chemdraw_tool.server.REACTION_DIR", tmp_path / "rxn")
    with patch("chemdraw_tool.server._enrich_properties", return_value={}):
        yield


def _mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


def _resolve(text):
    return text, _mol(text)


# --- Bilanz -----------------------------------------------------------------


def test_balance_counts_with_coefficients():
    left, right = [_mol("[H][H]"), _mol("O=O")], [_mol("O")]
    assert not check_balance(left, right).balanced
    result = check_balance(left, right, coefficients=[2, 1, 2])
    assert result.balanced
    assert result.suggestedCoefficients is None


def test_wrong_coefficients_stay_unbalanced_and_still_suggest():
    left, right = [_mol("[H][H]"), _mol("O=O")], [_mol("O")]
    result = check_balance(left, right, coefficients=[1, 1, 2])
    assert not result.balanced
    assert result.suggestedCoefficients == [2, 1, 2]


# --- Zeichnung --------------------------------------------------------------


def test_svg_shows_coefficient_only_when_above_one():
    left, right = [_mol("[H][H]"), _mol("O=O")], [_mol("O")]
    plain = render_reaction_svg(left, right)
    drawn = render_reaction_svg(left, right, coefficients=[2, 1, 2])
    assert drawn != plain
    # Koeffizient 1 schreibt niemand hin — die Zeichnung bleibt bytegleich.
    assert render_reaction_svg(left, right, coefficients=[1, 1, 1]) == plain


def test_cdxml_writes_coefficients_as_text():
    left, right = [_mol("[H][H]"), _mol("O=O")], [_mol("O")]
    cdxml = reaction_to_cdxml(left, right, coefficients=[2, 1, 2])
    assert cdxml.count(">2</s>") == 2
    assert reaction_to_cdxml(left, right, coefficients=[1, 1, 1]) == reaction_to_cdxml(
        left, right
    )


# --- Tool -------------------------------------------------------------------


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_tool_applies_coefficients(_):
    result = generate_reaction(
        reactants=["[H][H]", "O=O"], products=["O"], coefficients=[2, 1, 2]
    )
    assert result.balance.balanced
    assert [m.coefficient for m in result.reactants + result.products] == [2, 1, 2]
    assert result.coefficients == [2, 1, 2]


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_payload_echoes_the_call_so_the_panel_can_repeat_it(_):
    result = generate_reaction(
        reactants=["[H][H]", "O=O"],
        products=["O"],
        conditions="Pt, H2",
        conditions_below="Δ",
        arrow="forward",
        name="Knallgas",
    )
    assert result.request == {
        "reactants": ["[H][H]", "O=O"],
        "products": ["O"],
        "conditions": "Pt, H2",
        "conditions_below": "Δ",
        "arrow": "forward",
        "name": "Knallgas",
        "abbreviate_groups": False,
        "render_style": "",
    }
    assert result.coefficients == []


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_coefficients_get_their_own_file(_, tmp_path):
    plain = generate_reaction(reactants=["[H][H]", "O=O"], products=["O"])
    applied = generate_reaction(
        reactants=["[H][H]", "O=O"], products=["O"], coefficients=[2, 1, 2]
    )
    assert plain.files["svg"] != applied.files["svg"]


@pytest.mark.parametrize("bad", [[2, 1], [2, 1, 2, 1], [0, 1, 2], [-2, 1, 2]])
@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_rejects_bad_coefficients(_, bad):
    with pytest.raises(ValueError, match="coefficients"):
        generate_reaction(reactants=["[H][H]", "O=O"], products=["O"], coefficients=bad)


def test_description_keeps_coefficients_the_users_choice():
    # Jay 26.10.: Ausgleichen entscheidet der Nutzer — per Knopf oder Bitte.
    doc = generate_reaction.__doc__ or ""
    assert "only when the user" in doc
    assert "Apply coefficients" in doc
