"""Tests for calculator statistics functions."""

import pytest

from chemdraw_tool.calculator.stats import (
    descriptive_stats,
    f_test,
    one_sample_t_test,
    welch_t_test,
)


def test_descriptive_stats_basic():
    values = [82.4, 82.5, 82.4, 82.4]
    result = descriptive_stats(values)
    assert result["mean"] == pytest.approx(82.425, abs=0.001)
    assert result["std_abs"] == pytest.approx(0.05, abs=0.01)
    assert result["variance"] == pytest.approx(0.0025, abs=0.001)
    assert result["std_rel"] == pytest.approx(0.0607, abs=0.01)


def test_descriptive_stats_single_value():
    result = descriptive_stats([99.5])
    assert result["mean"] == pytest.approx(99.5)
    assert result["std_abs"] == 0.0
    assert result["variance"] == 0.0


def test_descriptive_stats_recovery():
    values = [82.4, 82.5, 82.4, 82.4]
    result = descriptive_stats(values, true_value=82.5)
    assert result["recovery"] == pytest.approx(99.909, abs=0.01)
    assert result["rel_deviation"] == pytest.approx(0.0909, abs=0.01)


def test_one_sample_t_test_pass():
    values = [82.4, 82.5, 82.4, 82.4]
    result = one_sample_t_test(values, mu=82.5)
    assert result["t_value"] == pytest.approx(3.0, abs=0.1)
    assert result["t_critical"] == pytest.approx(3.182, abs=0.01)
    assert result["passed"] is True  # t < t_crit


def test_one_sample_t_test_fail():
    values = [80.0, 80.1, 79.9, 80.0]
    result = one_sample_t_test(values, mu=82.5)
    assert result["passed"] is False


def test_f_test_equal_variance():
    s1_values = [82.4, 82.5, 82.4, 82.4]
    s2_values = [82.6, 82.3, 82.5, 82.4]
    result = f_test(s1_values, s2_values)
    assert result["passed"] is True  # variances are similar


def test_welch_t_test_equal_means():
    s1 = [82.4, 82.5, 82.4, 82.4]
    s2 = [82.6, 82.3, 82.5, 82.4]
    result = welch_t_test(s1, s2)
    assert result["passed"] is True  # means are similar


def test_descriptive_stats_empty_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        descriptive_stats([])


def test_one_sample_t_test_empty_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        one_sample_t_test([], mu=100.0)


def test_f_test_empty_raises():
    with pytest.raises(ValueError, match="at least one value"):
        f_test([], [82.4, 82.5])


def test_welch_t_test_empty_raises():
    with pytest.raises(ValueError, match="at least one value"):
        welch_t_test([82.4], [])
