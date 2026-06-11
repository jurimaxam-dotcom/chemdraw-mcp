"""Tests für chemdraw_tool/ph_plots.py — Titrationskurven + Speziesverteilung.

Spec (2026-06-11): Gemeinsame Mathematik (α-Fraktionen über pH, exakte
Ladungsbilanz statt Näherungsformeln) für zwei Plots im Spektren-Stil:

- titration_curve: schwache (auch mehrprotonige) Säure mit starker Base —
  pH gegen Titrantvolumen, mit Äquivalenzvolumina je Protolysestufe.
- Speziesverteilung: α der Protonierungsspezies gegen pH.

Referenzwerte Essigsäure (pKa 4.76, 0.1 M, 25 mL, Titrant 0.1 M NaOH):
Start-pH ≈ 2.88, Halb-ÄP = pKa, ÄP-pH ≈ 8.73 (Lehrbuch-Näherungen,
Toleranz 0.1 — die Ladungsbilanz ist genauer als die Formeln).
"""

import pytest

from chemdraw_tool.ph_plots import (
    alpha_fractions,
    build_species_figure,
    render_species_png,
    render_species_svg,
    render_titration_png,
    render_titration_svg,
    titration_curve,
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

ACETIC = dict(pka_values=[4.76], c_acid=0.1, v_acid_ml=25.0, c_titrant=0.1)


# ---------------------------------------------------------------------------
# α-Fraktionen
# ---------------------------------------------------------------------------


def test_alpha_fractions_sum_to_one():
    for pka in ([4.76], [2.15, 7.2], [2.15, 7.2, 12.35]):
        for ph in (0.5, 4.0, 7.0, 10.0, 13.5):
            assert sum(alpha_fractions(pka, ph)) == pytest.approx(1.0)


def test_alpha_crossover_at_pka():
    """Bei pH = pKa sind protonierte und deprotonierte Form gleich häufig."""
    a = alpha_fractions([4.76], 4.76)
    assert a[0] == pytest.approx(a[1])
    assert a[0] == pytest.approx(0.5, abs=1e-6)


def test_alpha_limits():
    """Weit unter pKa dominiert HA, weit darüber A⁻."""
    assert alpha_fractions([4.76], 1.0)[0] > 0.999
    assert alpha_fractions([4.76], 9.0)[1] > 0.999


# ---------------------------------------------------------------------------
# Titrationskurve
# ---------------------------------------------------------------------------


def test_titration_start_ph_weak_acid():
    curve = titration_curve(**ACETIC)
    assert curve.volumes_ml[0] == 0.0
    assert curve.ph[0] == pytest.approx(2.88, abs=0.1)


def test_titration_half_equivalence_ph_is_pka():
    curve = titration_curve(**ACETIC)
    idx = min(
        range(len(curve.volumes_ml)),
        key=lambda i: abs(curve.volumes_ml[i] - 12.5),
    )
    assert curve.ph[idx] == pytest.approx(4.76, abs=0.1)


def test_titration_equivalence_point():
    curve = titration_curve(**ACETIC)
    assert curve.eq_volumes_ml == [pytest.approx(25.0)]
    idx = min(
        range(len(curve.volumes_ml)),
        key=lambda i: abs(curve.volumes_ml[i] - 25.0),
    )
    assert curve.ph[idx] == pytest.approx(8.73, abs=0.15)


def test_titration_curve_is_monotonically_increasing():
    curve = titration_curve(**ACETIC)
    assert all(b >= a for a, b in zip(curve.ph, curve.ph[1:]))


def test_diprotic_acid_has_two_equivalence_volumes():
    curve = titration_curve(
        pka_values=[2.15, 7.2], c_acid=0.1, v_acid_ml=20.0, c_titrant=0.1
    )
    assert curve.eq_volumes_ml == [pytest.approx(20.0), pytest.approx(40.0)]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def test_render_titration_png_and_svg():
    png = render_titration_png(**ACETIC, title="Acetic acid / NaOH")
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC
    svg = render_titration_svg(**ACETIC, title="Acetic acid / NaOH")
    assert "<svg" in svg
    assert "Acetic acid / NaOH" in svg
    assert "pH" in svg


def test_render_titration_indicator_band():
    plain = render_titration_svg(**ACETIC)
    banded = render_titration_svg(
        **ACETIC, indicator={"name": "Phenolphthalein", "ph_range": [8.2, 10.0]}
    )
    assert "Phenolphthalein" in banded
    assert "Phenolphthalein" not in plain


def test_render_species_png_and_svg():
    png = render_species_png([2.15, 7.2, 12.35], title="Phosphoric acid")
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC
    svg = render_species_svg([2.15, 7.2, 12.35], title="Phosphoric acid")
    assert "<svg" in svg
    assert "Phosphoric acid" in svg


def test_species_figure_has_one_curve_per_species():
    fig = build_species_figure([2.15, 7.2, 12.35])
    # Nur Kurven mit Legenden-Label zählen — die pKa-axvlines sind auch lines.
    curves = [l for l in fig.axes[0].lines if not l.get_label().startswith("_")]
    assert len(curves) == 4  # n pKa ⇒ n+1 Spezies


def test_species_custom_labels_appear_in_legend():
    fig = build_species_figure([4.76], labels=["CH₃COOH", "CH₃COO⁻"])
    legend_texts = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
    assert legend_texts == ["CH₃COOH", "CH₃COO⁻"]
