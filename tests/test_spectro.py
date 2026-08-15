"""Was man im Spektrum erwarten sollte — aus der Struktur abgeleitet.

Zwei Richtungen, beide Prüfungsstoff:
* Struktur → erwartete IR-Banden und Anzahl der ¹H-Signale
* gemessene Wellenzahl → welche Gruppe kommt infrage

Bewusst deterministisch: Bandenlagen aus einer kuratierten Tabelle, Signalzahl
aus der topologischen Äquivalenz der Protonen. Keine Verschiebungen in ppm —
die kämen nur aus einem ML-Modell und wären geraten.
"""

import pytest

from chemdraw_tool.spectro import (
    assign_wavenumber,
    expected_ir_bands,
    proton_signals,
)

# --- IR aus der Struktur ----------------------------------------------------


def test_carboxylic_acid_shows_its_two_giveaway_bands():
    bands = expected_ir_bands("CC(=O)O")
    labels = " ".join(b["group"] for b in bands)
    assert "O–H" in labels or "O-H" in labels
    assert "C=O" in labels


def test_ester_carbonyl_sits_higher_than_a_ketone():
    """Die Lage der Carbonylbande unterscheidet die Stoffklassen — genau das
    wird geprüft."""
    ester = [b for b in expected_ir_bands("CC(=O)OC") if "C=O" in b["group"]][0]
    ketone = [b for b in expected_ir_bands("CC(=O)C") if "C=O" in b["group"]][0]
    assert ester["low"] > ketone["low"]


def test_nitrile_is_found():
    assert any("C≡N" in b["group"] for b in expected_ir_bands("CC#N"))


def test_aromatic_ring_is_reported():
    bands = expected_ir_bands("c1ccccc1")
    assert any("aromatic" in b["group"].lower() for b in bands)


def test_alkane_without_functional_groups_still_shows_ch():
    bands = expected_ir_bands("CCCC")
    assert any("C–H" in b["group"] or "C-H" in b["group"] for b in bands)


def test_every_band_carries_range_intensity_and_shape():
    """Ohne Intensität und Form ist eine Bandenlage nicht zuzuordnen."""
    for band in expected_ir_bands("CC(=O)O"):
        assert band["low"] < band["high"]
        assert band["intensity"]
        assert band["shape"]


def test_bands_come_sorted_from_high_to_low_wavenumber():
    """Wie im Spektrum gelesen wird."""
    bands = expected_ir_bands("CC(=O)Oc1ccccc1C(=O)O")
    highs = [b["high"] for b in bands]
    assert highs == sorted(highs, reverse=True)


def test_unparseable_structure_fails_with_a_useful_message():
    with pytest.raises(ValueError, match="not|parse"):
        expected_ir_bands("Q%%%")


# --- Wellenzahl zuordnen ----------------------------------------------------


def test_wavenumber_1715_suggests_a_carbonyl():
    hits = assign_wavenumber(1715)
    assert any("C=O" in h["group"] for h in hits)


def test_wavenumber_3300_offers_the_competing_assignments():
    """3300 ist mehrdeutig — O–H, N–H und Alkin-C–H. Alle drei nennen."""
    groups = " ".join(h["group"] for h in assign_wavenumber(3300))
    assert "O" in groups and "N" in groups


def test_assignment_is_ordered_by_how_central_the_band_sits():
    """Der Treffer, dessen Bereich die Zahl am besten trifft, kommt zuerst."""
    hits = assign_wavenumber(1740)
    assert "C=O" in hits[0]["group"]


def test_wavenumber_outside_the_ir_range_says_so():
    assert assign_wavenumber(50) == []


# --- ¹H-Signale -------------------------------------------------------------


@pytest.mark.parametrize(
    "smiles,signals,integrals",
    [
        ("CCO", 3, [3, 2, 1]),  # Ethanol
        ("Cc1ccccc1", 4, [3, 2, 2, 1]),  # Toluol
        ("CC(C)(C)O", 2, [9, 1]),  # tert-Butanol
        ("CCOC(C)=O", 3, [3, 3, 2]),  # Essigsäureethylester
        ("c1ccccc1", 1, [6]),  # Benzol
    ],
)
def test_proton_signal_counts_match_the_textbook(smiles, signals, integrals):
    r = proton_signals(smiles)
    assert r["count"] == signals
    assert sorted(r["integrals"], reverse=True) == sorted(integrals, reverse=True)


def test_molecule_without_hydrogens_reports_zero():
    r = proton_signals("O=C=O")
    assert r["count"] == 0
    assert "no" in r["explanation"].lower() or "0" in r["explanation"]


def test_result_names_the_diastereotopic_limitation():
    """Die Grenze gehört in die Ausgabe, nicht nur in die Doku — sonst wirkt
    das Ergebnis genauer, als es ist."""
    r = proton_signals("CC(O)CC")
    assert "diastereotop" in r["limitation"].lower()


def test_integrals_sum_to_the_hydrogen_count():
    r = proton_signals("CCO")
    assert sum(r["integrals"]) == 6
