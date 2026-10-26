"""Beschriftung unter den Stoffen einer Reaktion (Befund Desktop-Test 26.10.).

Bei SMILES-Eingabe stand der Eingabetext ([H][H], O=O, O) unter dem Molekül.
Jetzt steht dort die Summenformel mit tiefgestellten Ziffern (H₂, O₂, H₂O) —
im Panel als Unicode, im CDXML als ChemDraw-Tiefstellung (face="32").
Ein Name bleibt ein Name.
"""

from unittest.mock import patch

import pytest
from lxml import etree
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.layout import reaction_to_cdxml
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


# Wie resolve(): SMILES kommt unverändert zurück, ein Name als kanonisches SMILES.
_NAMES = {"ethanol": "CCO", "acetic acid": "CC(=O)O", "ethyl acetate": "CCOC(C)=O"}


def _resolve(text):
    if text in _NAMES:
        return _NAMES[text], _mol(_NAMES[text])
    return text, _mol(text)


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_smiles_input_is_labelled_with_its_formula(_):
    result = generate_reaction(reactants=["[H][H]", "O=O"], products=["O"])
    assert [m.name for m in result.reactants + result.products] == ["H₂", "O₂", "H₂O"]


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_names_stay_names(_):
    result = generate_reaction(
        reactants=["acetic acid", "ethanol"], products=["ethyl acetate", "O"]
    )
    assert [m.name for m in result.reactants + result.products] == [
        "acetic acid",
        "ethanol",
        "ethyl acetate",
        "H₂O",
    ]


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_request_keeps_the_raw_input(_):
    # Der Knopf „Apply coefficients“ wiederholt den Aufruf — mit dem SMILES,
    # nicht mit der Formel (H₂O ist kein gültiger Eingabewert).
    result = generate_reaction(reactants=["[H][H]", "O=O"], products=["O"])
    assert result.request["reactants"] == ["[H][H]", "O=O"]


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_cdxml_labels_use_formula_subscripts(_, tmp_path):
    result = generate_reaction(
        reactants=["[H][H]", "O=O"], products=["O"], formats=["cdxml"]
    )
    cdxml = open(result.cdxml_path, encoding="utf-8").read()
    assert "[H][H]" not in cdxml
    assert "₂" not in cdxml
    # Wasser: H, tiefgestellte 2, O — drei Läufe in einer Beschriftung.
    water = [
        t for t in etree.fromstring(cdxml.encode()).iter("t") if t.findtext("s") == "H"
    ][-1]
    assert [(s.text, s.get("face")) for s in water] == [
        ("H", None),
        ("2", "32"),
        ("O", None),
    ]


def test_cdxml_label_without_digits_is_one_run():
    cdxml = reaction_to_cdxml(
        [_mol("CCO")], [_mol("CC=O")], reactant_names=["ethanol"], product_names=[""]
    )
    assert '<s font="3" size="8">ethanol</s>' in cdxml
