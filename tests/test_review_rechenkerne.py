"""Rechenkern-Befunde aus dem Review 09.11.2026 (jeder Fall einmal rot gesehen)."""

import pytest

from chemdraw_tool import ph_calc, pk, spectro
from chemdraw_tool import server as s
from chemdraw_tool.calculator import stats, titration


def test_unsorted_pka_list_is_refused_for_the_ph_number_too():
    """[7.2, 2.15, 12.35] ergab für 0,1 M H₃PO₄ pH 3,35 statt 1,63 — ohne Warnung."""
    with pytest.raises(ValueError, match="ascending"):
        s.calculate_ph("weak_acid", concentration=0.1, pka_values=[7.2, 2.15, 12.35])


# Zweiseitig, α = 0,05 — veröffentlichte Tabellenwerte (z. B. ASTM E178 / Grubbs & Beck 1972).
@pytest.mark.parametrize("n, expected", [(25, 2.822), (30, 2.908), (40, 3.036), (50, 3.128), (100, 3.384)])
def test_grubbs_critical_value_keeps_rising_above_the_table(n, expected):
    assert stats._lookup_grubbs_critical(n) == pytest.approx(expected, abs=0.003)


@pytest.mark.parametrize("n", range(4, 21))
def test_grubbs_formula_reproduces_the_table(n):
    assert stats._grubbs_critical_exact(n) == pytest.approx(stats._GRUBBS_CRITICAL[n], abs=0.002)


def test_grubbs_does_not_reject_too_easily_in_a_long_series():
    values = [100 + 0.1 * ((i % 5) - 2) for i in range(29)] + [100.45]
    assert stats.grubbs_test(values)["is_outlier"] is False


def test_blank_at_or_above_the_reading_is_named():
    with pytest.raises(ValueError, match="blank"):
        titration.calculate_titer([100], [0.1], 0.1, 1.0, 100.0)
    with pytest.raises(ValueError, match="blank"):
        titration.calculate_gehalt_titration([100], [0.05], 0.1, 1.0)


def test_contradicting_pka_and_pkb_are_refused():
    with pytest.raises(ValueError, match="14"):
        ph_calc.weak_base_ph(0.1, pkb=4.75, pka=5.0)
    assert ph_calc.weak_base_ph(0.1, pkb=4.75, pka=9.25)["ph"] == pytest.approx(11.12, abs=0.02)


def test_buffer_recipe_says_when_henderson_hasselbalch_misses_the_target():
    """pKa 2,15 bei 0,01 M: das HH-Rezept landet bei pH 2,61 statt 2,15."""
    r = ph_calc.buffer_recipe(target_ph=2.15, pka=2.15, total_concentration=0.01, volume_ml=100)
    assert any("2.6" in n for n in r["notes"])
    acetate = ph_calc.buffer_recipe(target_ph=4.76, pka=4.76, total_concentration=0.1, volume_ml=100)
    assert acetate["notes"] == []


@pytest.mark.parametrize("kwargs", [{"vd": 0, "cl": 5}, {"cl": 5, "ke": 0}, {"vd": 40, "t_half": 0}])
def test_pk_zero_inputs_get_a_message_not_a_division_error(kwargs):
    with pytest.raises(ValueError):
        pk.resolve(**kwargs)


@pytest.mark.parametrize(
    "smiles, present, absent",
    [
        ("CC(=O)OC(C)=O", "C=O (anhydride)", "C=O (ester)"),
        ("CNC(=O)OC", None, "C=O (ester)"),
        ("CC(=O)Oc1ccccc1C(=O)O", "C=O (ester)", None),
        ("CCOC(C)=O", "C–O (ester)", None),
        ("COC=O", "C=O (ester)", None),
    ],
    ids=["anhydrid", "carbamat", "aspirin", "ethylacetat", "methylformiat"],
)
def test_ester_band_only_for_esters(smiles, present, absent):
    groups = [b["group"] for b in spectro.expected_ir_bands(smiles)]
    if present:
        assert present in groups
    if absent:
        assert absent not in groups


def test_signal_count_stays_topological_and_names_the_vinyl_case():
    """Zählweise ist eine didaktische Festlegung (Jay-Entscheid offen, 09.11.2026):
    =CH₂ bleibt ein Signal, der Limitation-Text nennt den Fall."""
    result = spectro.proton_signals("CC=C")
    assert result["count"] == 3
    assert "terminal alkene" in result["limitation"]
