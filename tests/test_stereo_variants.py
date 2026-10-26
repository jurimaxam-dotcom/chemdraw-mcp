"""Stereo-Varianten zeigen (Grundlagen, Etappe 3).

Ein Stoff mit offenen Stereoelementen (Ibuprofen aus PubChem, ein getipptes
SMILES ohne @) bekommt im Panel „Show variants“: alle Stereoisomere als
Vorschaubilder mit R/S- bzw. E/Z-Label, ein Klick zeichnet das gewählte mit
Keilen. Höchstens 3 offene Elemente = 8 Bilder.
"""

from unittest.mock import patch

import pytest
from rdkit import Chem

from chemdraw_tool.generator import MAX_STEREO_VARIANTS, stereo_variants
from chemdraw_tool.server import generate_molecule

IBUPROFEN = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
TARTARIC = "OC(C(O)C(=O)O)C(=O)O"


def _labels(smiles: str) -> list[str]:
    return [v["descriptor"] for v in stereo_variants(Chem.MolFromSmiles(smiles))]


# --- Aufzählen ----------------------------------------------------------------


def test_one_center_gives_r_and_s():
    assert sorted(_labels(IBUPROFEN)) == ["(R)", "(S)"]


def test_double_bond_gives_e_and_z():
    assert sorted(_labels("CC=CC")) == ["(E)", "(Z)"]


def test_three_centers_give_eight():
    # 2,3,4-Trihydroxypentansäure: drei verschiedene Zentren.
    assert len(_labels("OC(=O)C(O)C(O)C(O)C")) == 8 == MAX_STEREO_VARIANTS


def test_meso_form_is_counted_once():
    # Weinsäure: (R,R), (S,S), meso — drei, nicht vier.
    assert len(_labels(TARTARIC)) == 3


def test_more_than_three_open_elements_give_nothing():
    # Glucose offenkettig: vier offene Zentren = 16, über der Grenze.
    assert _labels("OCC(O)C(O)C(O)C(O)C=O") == []


def test_fully_specified_molecule_has_no_variants():
    assert _labels("C[C@H](N)C(=O)O") == []


def test_only_open_centers_vary():
    # Ein Zentrum fest (S), eines offen: zwei Varianten, beide behalten das feste.
    mol = Chem.MolFromSmiles("C[C@H](O)C(C)N")
    variants = stereo_variants(mol)
    assert len(variants) == 2
    for v in variants:
        # Das feste Zentrum passt nur mit gleicher Konfiguration.
        assert Chem.MolFromSmiles(v["smiles"]).HasSubstructMatch(mol, useChirality=True)
    flipped = Chem.MolFromSmiles("C[C@@H](O)C(C)N")
    assert not any(
        Chem.MolFromSmiles(v["smiles"]).HasSubstructMatch(flipped, useChirality=True)
        for v in variants
    )


def test_input_molecule_stays_untouched():
    mol = Chem.MolFromSmiles(IBUPROFEN)
    before = Chem.MolToSmiles(mol)
    stereo_variants(mol)
    assert Chem.MolToSmiles(mol) == before


def test_variant_smiles_are_fully_specified():
    for v in stereo_variants(Chem.MolFromSmiles(TARTARIC)):
        assert "@" in v["smiles"]


# --- Tool: generate_molecule(stereo_variants=True) ----------------------------


@pytest.fixture
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.OUTPUT_DIR", tmp_path / "mol")
    with patch("chemdraw_tool.server._enrich_properties", return_value={}):
        yield tmp_path


def _resolve(text):
    if text == "ibuprofen":
        return IBUPROFEN, Chem.MolFromSmiles(IBUPROFEN)
    return text, Chem.MolFromSmiles(text)


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_tool_returns_a_pick_list_and_draws_nothing(_, _isolate):
    result = generate_molecule("ibuprofen", stereo_variants=True)
    assert result.type == "ambiguous"
    assert sorted(c.label for c in result.candidates) == ["(R)-ibuprofen", "(S)-ibuprofen"]
    assert all(c.svg.startswith("<?xml") and "@" in c.smiles for c in result.candidates)
    assert "2 stereoisomers" in result.message
    assert result.files == {}
    assert not (_isolate / "mol").exists()


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_smiles_input_labels_with_the_descriptor_only(_, _isolate):
    result = generate_molecule("CC=CC", stereo_variants=True)
    assert sorted(c.label for c in result.candidates) == ["(E)", "(Z)"]


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_too_many_open_elements_is_a_clear_error(_, _isolate):
    with pytest.raises(ValueError, match="at most 3"):
        generate_molecule("OCC(O)C(O)C(O)C(O)C=O", stereo_variants=True)


@patch("chemdraw_tool.server.resolve", side_effect=_resolve)
def test_nothing_open_is_a_clear_error(_, _isolate):
    with pytest.raises(ValueError, match="no unspecified"):
        generate_molecule("C[C@H](N)C(=O)O", stereo_variants=True)
