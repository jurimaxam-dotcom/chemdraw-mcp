"""Tests für die kuratierte Anki-Deck-Bibliothek.

Bewusst klein (2 Decks) und GEPRÜFT: Jede kuratierte Struktur wird gegen
ihre erwartete Summenformel verifiziert — ein falsch getippter SMILES fällt
hier auf, nicht erst beim Lernen. Inhalte sind ausschließlich
Lehrbuch-Klassiker (Analgetika-Strukturen, Ph.Eur.-Identitätsreaktionen).
"""

import pytest
from rdkit import Chem
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

from chemdraw_tool.curated_decks import (
    CURATED_DECKS,
    VERIFIED_STRUCTURES,
    get_curated_deck,
)


def test_exactly_two_curated_decks():
    """Die Bibliothek bleibt klein — Wachstum ist eine bewusste Entscheidung."""
    assert set(CURATED_DECKS) == {"analgesics-structures", "pheur-identity-basics"}


def test_every_curated_structure_matches_its_formula():
    """Der Kurations-Gate: SMILES ↔ Summenformel."""
    assert len(VERIFIED_STRUCTURES) >= 6
    for smiles, formula in VERIFIED_STRUCTURES.items():
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, f"SMILES parst nicht: {smiles}"
        assert CalcMolFormula(mol) == formula, f"Formel-Mismatch für {smiles}"


def test_decks_build_cards():
    for deck_id in CURATED_DECKS:
        name, cards = get_curated_deck(deck_id)
        assert name
        assert len(cards) >= 6
        for card in cards:
            assert card.front.text
            assert card.back.text or card.back.structure or card.back.reaction


def test_unknown_deck_id_lists_available():
    with pytest.raises(ValueError, match="analgesics-structures"):
        get_curated_deck("does-not-exist")


def test_analgesics_deck_uses_verified_structures():
    _, cards = get_curated_deck("analgesics-structures")
    for card in cards:
        if card.front.structure:
            assert card.front.structure in VERIFIED_STRUCTURES
