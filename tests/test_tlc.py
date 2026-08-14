"""Tests für chemdraw_tool/tlc.py — DC-Platten aus Rf-Werten.

Zwilling von spectrum.py: aus Zahlen wird eine schematische, beschriftete
Protokoll-Grafik (matplotlib → PNG/SVG). Kern ist die pure Funktion
build_plate(lanes) → PlateGeometry, die Rf-Werte in Plattenkoordinaten
umrechnet; das Rendering setzt nur Achsen/Labels obendrauf.

Fachliche Festlegungen, die hier festgenagelt werden:
* Rf = Laufstrecke Substanz / Laufstrecke Front ⇒ 0 ≤ Rf ≤ 1. Werte
  außerhalb sind ein Eingabefehler, KEIN Fall für stilles Clampen.
* Die Platte wird von unten gelesen: Start unten (Rf 0), Front oben (Rf 1).
* Mehrere Bahnen nebeneinander, je Bahn beliebig viele Flecken (Co-Spot).
"""

import pytest

from chemdraw_tool.tlc import (
    FRONT_Y,
    START_Y,
    build_plate,
    default_figsize,
    render_tlc_png,
    render_tlc_svg,
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# Der Standardfall aus dem Praktikum: Veresterung, drei Bahnen.
ESTER_LANES = [
    {"name": "Edukt", "spots": [{"rf": 0.30, "label": "Säure"}]},
    {"name": "Reaktion", "spots": [{"rf": 0.65, "label": "Ester"}]},
    {
        "name": "Co-Spot",
        "spots": [{"rf": 0.30}, {"rf": 0.65}],
    },
]


# ---------------------------------------------------------------------------
# Validierung — Rf ist ein Verhältnis
# ---------------------------------------------------------------------------


def test_no_lanes_raises():
    with pytest.raises(ValueError, match="[Bb]ahn"):
        build_plate([])


def test_lane_without_name_raises():
    with pytest.raises(ValueError, match="[Nn]ame"):
        build_plate([{"name": "", "spots": [{"rf": 0.5}]}])


@pytest.mark.parametrize("bad_rf", [1.2, -0.1, 42])
def test_rf_outside_0_to_1_raises(bad_rf):
    """Kein stilles Beschneiden: ein Rf > 1 ist ein Messfehler des Nutzers."""
    with pytest.raises(ValueError, match="Rf"):
        build_plate([{"name": "A", "spots": [{"rf": bad_rf}]}])


def test_rf_error_names_lane_and_value():
    with pytest.raises(ValueError) as err:
        build_plate(
            [
                {"name": "Edukt", "spots": [{"rf": 0.3}]},
                {"name": "Reaktion", "spots": [{"rf": 1.4}]},
            ]
        )
    assert "Reaktion" in str(err.value)
    assert "1.4" in str(err.value)


def test_rf_bounds_are_inclusive():
    """Rf 0 (bleibt am Start) und Rf 1 (läuft mit der Front) sind gültig."""
    geo = build_plate([{"name": "A", "spots": [{"rf": 0.0}, {"rf": 1.0}]}])
    assert [s.y for s in geo.spots] == [START_Y, FRONT_Y]


def test_intensity_outside_0_to_1_raises():
    with pytest.raises(ValueError, match="[Ii]ntensit"):
        build_plate([{"name": "A", "spots": [{"rf": 0.5, "intensity": 3}]}])


def test_intensity_defaults_to_full():
    geo = build_plate([{"name": "A", "spots": [{"rf": 0.5}]}])
    assert geo.spots[0].intensity == 1.0


# ---------------------------------------------------------------------------
# Geometrie — unten Start, oben Front
# ---------------------------------------------------------------------------


def test_plate_is_read_from_bottom():
    """Rf 0.8 sitzt weit oben, Rf 0.2 knapp über dem Start."""
    geo = build_plate([{"name": "A", "spots": [{"rf": 0.2}, {"rf": 0.8}]}])
    low, high = geo.spots
    assert high.y > low.y
    assert low.y == pytest.approx(START_Y + 0.2 * (FRONT_Y - START_Y))
    assert high.y == pytest.approx(START_Y + 0.8 * (FRONT_Y - START_Y))


def test_lanes_sit_side_by_side_in_input_order():
    geo = build_plate(ESTER_LANES)
    assert geo.lanes == ["Edukt", "Reaktion", "Co-Spot"]
    assert geo.lane_x == sorted(geo.lane_x)
    assert len(set(geo.lane_x)) == 3


def test_co_spot_lane_keeps_both_spots_on_one_x():
    geo = build_plate(ESTER_LANES)
    co = [s for s in geo.spots if s.lane == "Co-Spot"]
    assert len(co) == 2
    assert co[0].x == co[1].x
    assert {round(s.rf, 2) for s in co} == {0.30, 0.65}


def test_lane_without_spots_is_still_drawn():
    """Leerbahn (Blindwert) ist zulässig — sie hat nur keine Flecken."""
    geo = build_plate([{"name": "Blank", "spots": []}, {"name": "A", "spots": [{"rf": 0.4}]}])
    assert geo.lanes == ["Blank", "A"]
    assert [s.lane for s in geo.spots] == ["A"]


def test_figure_grows_with_lane_count():
    """Feste Bahnbreite: 6 Bahnen quetschen die Beschriftung nicht zusammen."""
    narrow = default_figsize(2)
    wide = default_figsize(6)
    assert wide[0] > narrow[0]
    assert wide[1] == narrow[1]


# ---------------------------------------------------------------------------
# Label-Platzierung — Rf am Fleck ablesbar
# ---------------------------------------------------------------------------


def test_spot_label_sits_above_by_default():
    geo = build_plate([{"name": "A", "spots": [{"rf": 0.5, "label": "X"}]}])
    assert geo.spots[0].label_above is True


def test_label_near_the_front_ducks_below_the_spot():
    """Ein Fleck knapp unter der Front (Rf 0.98) hat oberhalb keinen Platz —
    dort liegen Frontlinie und deren Beschriftung."""
    geo = build_plate([{"name": "A", "spots": [{"rf": 0.98, "label": "X"}]}])
    assert geo.spots[0].label_above is False


def test_close_spots_in_one_lane_alternate_label_side():
    """Zwei dicht benachbarte Flecken (Co-Spot bei 0.44/0.50): die Texte
    dürfen nicht übereinander liegen — der untere weicht nach unten aus."""
    geo = build_plate([{"name": "Co", "spots": [{"rf": 0.44}, {"rf": 0.50}]}])
    sides = {round(s.rf, 2): s.label_above for s in geo.spots}
    assert sides[0.44] is False
    assert sides[0.50] is True


# ---------------------------------------------------------------------------
# Rendering (PNG/SVG)
# ---------------------------------------------------------------------------


def test_render_png_has_magic_bytes():
    png = render_tlc_png(ESTER_LANES, title="Veresterung")
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC


def test_render_svg_is_svg():
    svg = render_tlc_svg(ESTER_LANES, title="Veresterung")
    assert "<svg" in svg


def test_svg_shows_lane_names_and_title():
    svg = render_tlc_svg(ESTER_LANES, title="Veresterung")
    for lane in ("Edukt", "Reaktion", "Co-Spot"):
        assert lane in svg, lane
    assert "Veresterung" in svg


def test_svg_shows_rf_values_at_the_spots():
    """Ohne ablesbare Rf-Werte ist die Skizze im Protokoll wertlos."""
    svg = render_tlc_svg(ESTER_LANES)
    assert "0.65" in svg
    assert "0.30" in svg


def test_svg_shows_spot_labels():
    svg = render_tlc_svg(ESTER_LANES)
    assert "Säure" in svg
    assert "Ester" in svg


def test_svg_marks_start_line_and_solvent_front():
    svg = render_tlc_svg(ESTER_LANES)
    assert "Start" in svg
    assert "Front" in svg


def test_svg_carries_mobile_phase_and_detection():
    """Laufmittel und Detektion gehören ins Protokoll — also auf die Skizze."""
    svg = render_tlc_svg(
        ESTER_LANES,
        solvent="Toluol/Ethylacetat 8:2",
        detection="UV 254 nm",
    )
    assert "Toluol/Ethylacetat 8:2" in svg
    assert "UV 254 nm" in svg


def test_rf_axis_spans_only_start_to_front():
    """Die Rf-Skala existiert nur zwischen Start (0) und Front (1) — die
    Achse darf nicht in die Plattenränder hinein weiterlaufen."""
    from chemdraw_tool.tlc import build_figure

    fig = build_figure(ESTER_LANES)
    assert fig.axes[0].spines["left"].get_bounds() == (START_Y, FRONT_Y)


def test_weak_spot_is_drawn_fainter_than_strong_one():
    from chemdraw_tool.tlc import build_figure

    fig = build_figure(
        [{"name": "A", "spots": [{"rf": 0.3, "intensity": 0.2}, {"rf": 0.7}]}]
    )
    alphas = [p.get_alpha() for p in fig.axes[0].patches if p.get_alpha() is not None]
    assert len(alphas) >= 2
    assert min(alphas) < max(alphas)


def test_english_axis_label_like_the_spectrum_module():
    """Default-Beschriftung englisch (internationales Tool); title/solvent/
    detection bleiben frei lokalisierbar."""
    svg = render_tlc_svg(ESTER_LANES)
    assert "TLC" in svg
