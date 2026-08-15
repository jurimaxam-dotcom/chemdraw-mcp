"""`predict_spectrum`: was im Spektrum zu erwarten ist, als Text."""

import pytest

from chemdraw_tool.server import predict_spectrum


def test_ir_bands_come_as_a_readable_table():
    out = predict_spectrum("ir_bands", structure="CC(=O)Oc1ccccc1C(=O)O")
    assert out.startswith("#")
    assert "cm⁻¹" in out
    assert "C=O (ester)" in out
    assert "C=O (carboxylic acid)" in out


def test_ir_bands_explain_what_distinguishes_them():
    out = predict_spectrum("ir_bands", structure="CC=O")
    assert "Fermi" in out or "aldehyde" in out.lower()


def test_ir_bands_mention_that_ranges_shift():
    """Konjugation verschiebt die Carbonylbande — ohne den Hinweis wirkt die
    Tabelle absoluter, als sie ist."""
    out = predict_spectrum("ir_bands", structure="CC(=O)C")
    assert "conjugation" in out.lower()


def test_assign_wavenumber_lists_the_candidates():
    out = predict_spectrum("assign_wavenumber", wavenumber=1715)
    assert "C=O" in out


def test_assign_wavenumber_outside_the_range_explains_itself():
    out = predict_spectrum("assign_wavenumber", wavenumber=120)
    assert "fingerprint" in out.lower() or "400" in out


def test_nmr_signals_reports_count_and_ratio():
    out = predict_spectrum("nmr_signals", structure="CCO")
    assert "3 signal" in out
    assert "3:2:1" in out


def test_nmr_output_carries_the_diastereotopic_limitation():
    """Die Grenze muss beim Nutzer ankommen, nicht nur im Docstring stehen."""
    out = predict_spectrum("nmr_signals", structure="CC(O)CC")
    assert "Diastereotope" in out or "diastereotope" in out.lower()


def test_nmr_output_says_it_gives_no_shifts():
    out = predict_spectrum("nmr_signals", structure="CCO")
    assert "ppm" in out


def test_missing_structure_says_so():
    with pytest.raises(ValueError, match="structure"):
        predict_spectrum("ir_bands")


def test_missing_wavenumber_says_so():
    with pytest.raises(ValueError, match="wavenumber"):
        predict_spectrum("assign_wavenumber")


def test_unknown_topic_fails_audibly():
    with pytest.raises(ValueError, match="topic"):
        predict_spectrum("hellsehen", structure="CCO")


def test_unparseable_structure_is_rejected():
    with pytest.raises(ValueError, match="parse|not"):
        predict_spectrum("nmr_signals", structure="Q%%%")
