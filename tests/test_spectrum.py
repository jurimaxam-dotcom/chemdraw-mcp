"""Tests für chemdraw_tool/spectrum.py — schematische Spektren aus Peaklisten.

Spec (2026-06-10): Ein Modul deckt alle Spektrentypen ab. Kern ist die pure
Funktion build_curve(spectrum_type, peaks) → (x, y), die pro Typ die richtige
Achsenkonvention und Peakform liefert; das Rendering (PNG/SVG via matplotlib)
setzt nur noch Achsen/Labels obendrauf.

Intensitäten sind relativ: positive Typen werden auf max=1 normiert
(Transmission: 100 % − 95 %·s), signierte Typen (ord/cd) auf max|i|=1.
"""

import pytest

from chemdraw_tool.spectrum import (
    SPECTRUM_TYPES,
    build_curve,
    render_spectrum_png,
    render_spectrum_svg,
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

ALL_TYPES = (
    "ir",
    "nir",
    "raman",
    "uv_vis",
    "fluorescence",
    "ord",
    "cd",
    "nmr_1h",
    "nmr_13c",
    "ms",
)


# ---------------------------------------------------------------------------
# Typ-Registry & Validierung
# ---------------------------------------------------------------------------


def test_registry_contains_all_types():
    assert set(SPECTRUM_TYPES) == set(ALL_TYPES)


def test_unknown_type_raises_with_allowed_list():
    with pytest.raises(ValueError, match="ir"):
        build_curve("xrd", [{"position": 10, "intensity": 1}])


def test_empty_peaks_raises():
    with pytest.raises(ValueError, match="[Pp]eak"):
        build_curve("ir", [])


def test_all_zero_intensities_raises():
    with pytest.raises(ValueError, match="[Ii]ntensit"):
        build_curve("uv_vis", [{"position": 250, "intensity": 0}])


# ---------------------------------------------------------------------------
# Achsenkonventionen (invertierte x-Achse beim Rendern)
# ---------------------------------------------------------------------------


def test_axis_inversion_per_type():
    inverted = {"ir", "nir", "nmr_1h", "nmr_13c"}
    for key, cfg in SPECTRUM_TYPES.items():
        assert cfg.invert_x == (key in inverted), key


# ---------------------------------------------------------------------------
# Kurvenformen
# ---------------------------------------------------------------------------


def _y_at(x, y, pos):
    """y-Wert am Stützpunkt, der pos am nächsten liegt."""
    idx = min(range(len(x)), key=lambda i: abs(x[i] - pos))
    return y[idx]


def test_ir_transmission_dips_from_100_baseline():
    x, y = build_curve("ir", [{"position": 1700, "intensity": 1}])
    # Baseline fern vom Peak ≈ 100 % Transmission, am Peak tiefer Einbruch.
    assert _y_at(x, y, 3800) > 99
    assert _y_at(x, y, 1700) < 20
    assert min(y) >= 0


def test_ir_default_range_covers_4000_to_400():
    x, _ = build_curve("ir", [{"position": 1700, "intensity": 1}])
    assert min(x) <= 400
    assert max(x) >= 4000


def test_uv_vis_absorption_peaks_up_normalized():
    x, y = build_curve(
        "uv_vis",
        [{"position": 260, "intensity": 0.5}, {"position": 320, "intensity": 1}],
    )
    assert _y_at(x, y, 320) == pytest.approx(1.0, abs=0.05)
    assert 0.4 < _y_at(x, y, 260) < 0.7
    assert min(y) >= 0


def test_range_extends_to_cover_outlying_peaks():
    # UV/Vis-Default endet bei 800 nm — ein Peak bei 900 muss sichtbar sein.
    x, _ = build_curve("uv_vis", [{"position": 900, "intensity": 1}])
    assert max(x) > 920


def test_nmr_peaks_narrow_and_up():
    x, y = build_curve("nmr_1h", [{"position": 7.3, "intensity": 1}])
    assert _y_at(x, y, 7.3) == pytest.approx(1.0, abs=0.05)
    # 0,5 ppm neben dem Peak ist die Linie praktisch auf der Basislinie.
    assert _y_at(x, y, 6.8) < 0.05


def test_ord_cotton_effect_changes_sign_at_position():
    x, y = build_curve("ord", [{"position": 350, "intensity": 1, "width": 25}])
    assert _y_at(x, y, 350) == pytest.approx(0.0, abs=0.05)
    assert _y_at(x, y, 375) > 0.3  # positiver Ast langwellig
    assert _y_at(x, y, 325) < -0.3  # negativer Ast kurzwellig


def test_cd_negative_band_stays_negative():
    x, y = build_curve("cd", [{"position": 280, "intensity": -1}])
    assert _y_at(x, y, 280) == pytest.approx(-1.0, abs=0.05)
    assert max(y) <= 0.05


def test_ms_returns_bars_normalized_to_base_peak_100():
    peaks = [
        {"position": 43, "intensity": 60},
        {"position": 180, "intensity": 100},
    ]
    x, y = build_curve("ms", peaks)
    assert list(x) == [43, 180]
    assert max(y) == pytest.approx(100.0)
    assert _y_at(x, y, 43) == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# Rendering (PNG/SVG)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spectrum_type", ALL_TYPES)
def test_render_png_and_svg_for_every_type(spectrum_type):
    peaks = (
        [{"position": 43, "intensity": 60}, {"position": 180, "intensity": 100}]
        if spectrum_type == "ms"
        else [{"position": _typical_position(spectrum_type), "intensity": 1}]
    )
    png = render_spectrum_png(spectrum_type, peaks, title="Test")
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC
    svg = render_spectrum_svg(spectrum_type, peaks, title="Test")
    assert "<svg" in svg


def _typical_position(spectrum_type: str) -> float:
    return {
        "ir": 1700,
        "nir": 5200,
        "raman": 1000,
        "uv_vis": 260,
        "fluorescence": 450,
        "ord": 350,
        "cd": 280,
        "nmr_1h": 7.3,
        "nmr_13c": 128,
        "ms": 100,
    }[spectrum_type]


def test_svg_contains_english_axis_labels_and_title():
    """Englische Default-Labels (internationales Tool); der freie title-Param
    bleibt lokalisierbar."""
    svg = render_spectrum_svg("ir", [{"position": 1700, "intensity": 1}], title="Aspirin")
    assert "Wavenumber" in svg
    assert "Transmission" in svg
    assert "Aspirin" in svg


def test_svg_contains_peak_label():
    svg = render_spectrum_svg(
        "ir", [{"position": 1700, "intensity": 1, "label": "C=O"}]
    )
    assert "C=O" in svg
