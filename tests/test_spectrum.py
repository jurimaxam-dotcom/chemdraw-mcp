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


def test_close_peak_labels_are_staggered_vertically():
    """x-nahe Peaks (750/700) mit Labels: die Annotations müssen vertikal
    gestaffelt sein, sonst schreiben sie ineinander (Methylphenidat-IR,
    2026-06-11: zweimal 'mono-subst. Aromat' übereinander)."""
    from chemdraw_tool.spectrum import _build_figure

    fig = _build_figure(
        "ir",
        [
            {"position": 750, "intensity": 60, "width": 25, "label": "A"},
            {"position": 700, "intensity": 65, "width": 25, "label": "B"},
        ],
        "",
        (12, 8),
    )
    offsets = [t.xyann[1] for t in fig.axes[0].texts]
    assert len(offsets) == 2
    assert offsets[0] != offsets[1], "x-nahe Labels haben identischen y-Offset"


def test_distant_peak_labels_keep_the_baseline_offset():
    """Weit auseinanderliegende Peaks brauchen KEINE Staffelung: kein Offset
    tiefer als die Basis. (Der Floor-Clamp darf Labels tiefer Apexe ANHEBEN —
    der 1700er mit intensity 90 sitzt bei ~5 % — aber nie absenken.)"""
    from chemdraw_tool.spectrum import LABEL_BASE_BELOW, _build_figure

    fig = _build_figure(
        "ir",
        [
            {"position": 1700, "intensity": 90, "width": 25, "label": "A"},
            {"position": 3300, "intensity": 40, "width": 60, "label": "B"},
        ],
        "",
        (12, 8),
    )
    offsets = [t.xyann[1] for t in fig.axes[0].texts]
    assert all(off >= LABEL_BASE_BELOW for off in offsets), offsets
    # Der hohe Apex (3300er, ~62 %) bleibt exakt auf dem Basis-Offset.
    assert LABEL_BASE_BELOW in offsets, offsets


def test_label_stagger_rotates_instead_of_escalating():
    """Eine Kette naher Peaks darf den Versatz nicht unbegrenzt aufstapeln —
    sonst rutscht das letzte Label aus dem Plot (12-Peak-IR: 'C=O Ester'
    landete unter der x-Achse). Maximal 3 Ebenen, dann von vorn."""
    from chemdraw_tool.spectrum import (
        LABEL_BASE_BELOW,
        LABEL_STACK_STEP,
        _build_figure,
    )

    fig = _build_figure(
        "ir",
        [
            {"position": 1450, "intensity": 50, "width": 20, "label": "A"},
            {"position": 1495, "intensity": 35, "width": 20, "label": "B"},
            {"position": 1600, "intensity": 40, "width": 20, "label": "C"},
            {"position": 1735, "intensity": 90, "width": 25, "label": "D"},
        ],
        "",
        (12, 8),
    )
    offsets = [t.xyann[1] for t in fig.axes[0].texts]
    deepest_allowed = LABEL_BASE_BELOW - 2 * LABEL_STACK_STEP
    assert min(offsets) >= deepest_allowed, f"Label eskaliert aus dem Plot: {offsets}"


def test_no_label_below_the_plot_floor():
    """Geometrie-Check am realen 12-Peak-IR (Methylphenidat): KEIN Label darf
    unter die Plot-Unterkante rutschen — 'C=O Ester' (Apex bei 3 %) tat genau
    das, sobald die Nachbarkette ihm eine tiefe Staffelungs-Stufe zuwies."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    from chemdraw_tool.spectrum import _build_figure

    peaks = [
        {"position": 3320, "intensity": 30, "width": 60, "label": "N-H"},
        {"position": 3030, "intensity": 25, "width": 30, "label": "=C-H arom."},
        {"position": 2950, "intensity": 55, "width": 40, "label": "C-H aliph."},
        {"position": 2860, "intensity": 45, "width": 30, "label": "C-H"},
        {"position": 1735, "intensity": 90, "width": 25, "label": "C=O Ester"},
        {"position": 1600, "intensity": 40, "width": 20, "label": "C=C arom."},
        {"position": 1495, "intensity": 35, "width": 20, "label": "C=C arom."},
        {"position": 1450, "intensity": 50, "width": 20, "label": "CH2/CH3"},
        {"position": 1250, "intensity": 75, "width": 30, "label": "C-O"},
        {"position": 1160, "intensity": 70, "width": 30, "label": "C-O"},
        {"position": 750, "intensity": 60, "width": 25, "label": "mono-subst. Aromat"},
        {"position": 700, "intensity": 65, "width": 25, "label": "mono-subst. Aromat"},
    ]
    fig = _build_figure("ir", peaks, "", (12, 8))
    FigureCanvasAgg(fig)
    fig.canvas.draw()
    ax = fig.axes[0]
    floor_px = ax.transData.transform((1700.0, ax.get_ylim()[0]))[1]
    for t in ax.texts:
        bottom_px = t.get_window_extent().y0
        assert bottom_px >= floor_px, (
            f"Label {t.get_text()!r} ragt unter die Plot-Unterkante"
        )


# ---------------------------------------------------------------------------
# Befunde aus dem echten Aufruf (Welle 2, 30.10.2026)
# ---------------------------------------------------------------------------


def test_overlapping_strong_ir_bands_never_clip_to_zero():
    """Aspirin-Lehrbuchfall: C=O-Ester 1750 und C=O-Säure 1690 cm⁻¹.

    Die Absorptionen wurden addiert und bei 0 % abgeschnitten — beide Banden
    lagen als flacher Boden auf der Achse, die Beschriftungen übereinander.
    Transmission multipliziert sich (T = T₁·T₂), deshalb erreicht sie nie 0.
    """
    x, y = build_curve(
        "ir",
        [{"position": 1750, "intensity": 1}, {"position": 1690, "intensity": 0.9}],
    )
    assert min(y) > 0.1
    # Zwei getrennte Minima mit einem Buckel dazwischen.
    assert _y_at(x, y, 1720) > _y_at(x, y, 1750)
    assert _y_at(x, y, 1720) > _y_at(x, y, 1690)


def test_single_ir_band_keeps_its_depth():
    """Ein einzelner Peak mit s=1 fällt weiter auf 5 % — wie vor dem Fix."""
    x, y = build_curve("ir", [{"position": 1700, "intensity": 1}])
    assert _y_at(x, y, 1700) == pytest.approx(5.0, abs=0.01)


@pytest.mark.parametrize("spectrum_type, peaks", [
    ("xrd", [{"position": 10, "intensity": 1}]),
    ("ir", []),
    ("uv_vis", [{"position": 250, "intensity": 0}]),
])
def test_error_messages_are_english(spectrum_type, peaks):
    """Nutzertexte sind englisch (Projektkonvention); Befund 30.10.2026."""
    with pytest.raises(ValueError) as error:
        build_curve(spectrum_type, peaks)
    message = str(error.value)
    for german in ("benötigt", "Spektrentyp", "erlaubt", "mindestens", "Alle"):
        assert german not in message


# --- Kollisionsvermeidung der Bandenlabels (E17, 10.11.2026) -----------------
# Zwei tiefe IR-Banden bei 1750 und 1690 cm⁻¹: der Boden-Clamp zog beide
# Labels auf dieselbe Höhe, die 3-Ebenen-Staffelung half nicht — „1750“ und
# „1690“ standen übereinander. Jetzt werden sich tatsächlich überschneidende
# Labels nebeneinander gelegt und per Führungslinie an ihre Bande gebunden.
# Ohne Überschneidung bleibt das Bild byteweise wie bisher.


def _label_overlaps(spectrum_type, peaks):
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    from chemdraw_tool import spectrum as sp

    fig = sp._build_figure(spectrum_type, peaks, "", (10.0, 6.5))
    FigureCanvasAgg(fig)
    renderer = fig.canvas.get_renderer()
    from matplotlib.text import Text

    def text_box(ann):  # nur der Text — die Annotation-Box schlösse die Führungslinie ein
        ann.update_positions(renderer)
        return Text.get_window_extent(ann, renderer)

    boxes = [text_box(t) for t in fig.axes[0].texts]
    axes_box = fig.axes[0].get_window_extent(renderer)
    inside = all(axes_box.x0 - 1 <= b.x0 and b.x1 <= axes_box.x1 + 1 for b in boxes)
    return sum(a.overlaps(b) for i, a in enumerate(boxes) for b in boxes[i + 1 :]), inside


CROWDED = {
    "ir_1750_1690": ("ir", [{"position": 1750, "intensity": 0.9, "label": "1750"},
                            {"position": 1690, "intensity": 0.9, "label": "1690"}]),
    "ir_long_labels": ("ir", [{"position": 1750, "intensity": 0.9, "label": "C=O stretch 1750 cm-1"},
                              {"position": 1500, "intensity": 0.9, "label": "C=C aromatic 1500 cm-1"}]),
    "ir_four_close": ("ir", [{"position": p, "intensity": 0.8, "label": f"band {p}"}
                             for p in (1750, 1720, 1690, 1660)]),
    "nmr_five_close": ("nmr_1h", [{"position": p, "intensity": 1.0, "label": f"H{k} {p} ppm"}
                                  for k, p in enumerate((7.3, 7.25, 7.2, 7.15, 7.1))]),
}


@pytest.mark.parametrize("case", sorted(CROWDED))
def test_crowded_band_labels_do_not_overlap(case):
    overlaps, inside = _label_overlaps(*CROWDED[case])
    assert overlaps == 0
    assert inside


@pytest.mark.parametrize(
    "spectrum_type, peaks",
    [
        ("ir", [{"position": 3300, "intensity": 0.6, "label": "O-H"},
                {"position": 1715, "intensity": 0.9, "label": "C=O"},
                {"position": 1200, "intensity": 0.7, "label": "C-O"}]),
        ("nmr_1h", [{"position": 7.26, "intensity": 1, "label": "ArH"},
                    {"position": 2.1, "intensity": 0.5, "label": "CH3"}]),
    ],
)
def test_uncrowded_spectrum_is_byte_identical_without_avoidance(spectrum_type, peaks, monkeypatch):
    import re

    import matplotlib

    from chemdraw_tool import spectrum as sp

    monkeypatch.setitem(matplotlib.rcParams, "svg.hashsalt", "e17")  # feste Pfad-IDs

    def svg():  # matplotlib stempelt die Uhrzeit ins SVG
        return re.sub(r"<dc:date>[^<]*</dc:date>", "", sp.render_spectrum_svg(spectrum_type, peaks))

    png, before = sp.render_spectrum_png(spectrum_type, peaks), svg()
    monkeypatch.setattr(sp, "_spread_overlapping_labels", lambda *a, **k: None)
    assert sp.render_spectrum_png(spectrum_type, peaks) == png
    assert svg() == before


# --- Desktop-Fall 14.11.2026: zwei starke C=O-Banden 1750/1690 cm⁻¹ ---------
# Die gespreizte Reihe lag in der Bande: „Ester-C=O“ und „Säure-C=O“ standen
# 4 pt auseinander, und beide Wände der Doppelbande liefen durch die Schrift.
# Gemessen wird jede Etikett-Box gegen die andere (mit Mindestabstand) und
# gegen die gezeichnete Kurve.
ASPIRIN_CO = [
    {"position": 1750, "intensity": 1, "label": "Ester-C=O"},
    {"position": 1690, "intensity": 1, "label": "Säure-C=O"},
]


def _label_and_curve_boxes(spectrum_type, peaks):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.text import Text

    from chemdraw_tool import spectrum as sp

    fig = sp._build_figure(spectrum_type, peaks, "", (10.0, 6.5))
    FigureCanvasAgg(fig)
    renderer = fig.canvas.get_renderer()
    ax = fig.axes[0]
    boxes = []
    for ann in ax.texts:
        ann.update_positions(renderer)
        boxes.append(Text.get_window_extent(ann, renderer))
    line = ax.lines[0]
    curve = ax.transData.transform(line.get_xydata())
    return boxes, curve


def test_close_ir_band_labels_keep_a_gap_and_stay_off_the_curve():
    boxes, curve = _label_and_curve_boxes("ir", ASPIRIN_CO)
    assert len(boxes) == 2
    left, right = sorted(boxes, key=lambda b: b.x0)
    # Sichtbare Luft (≥ 10 px bei 100 dpi), nicht nur „berührt sich nicht“.
    assert right.x0 - left.x1 >= 10, (left, right)
    for box in boxes:
        inside = [
            (x, y) for x, y in curve
            if box.x0 - 2 <= x <= box.x1 + 2 and box.y0 - 2 <= y <= box.y1 + 2
        ]
        assert not inside, f"Kurve läuft durch das Etikett {box}: {inside[:3]}"


# --- Formeln und Titel (Befunde 22.11.2026: Paracetamol-¹H-NMR, Chinin-Fluoreszenz) ---


def _title_and_labels(spectrum_type, title, labels=()):
    from chemdraw_tool.spectrum import _build_figure

    x = _typical_position(spectrum_type)
    peaks = [{"position": x, "intensity": 1, "label": lab} for lab in labels] or [
        {"position": x, "intensity": 1}
    ]
    fig = _build_figure(spectrum_type, peaks, title, (10.0, 6.5))
    ax = fig.axes[0]
    return ax.get_title(), [t.get_text() for t in ax.texts]


@pytest.mark.parametrize(
    ("raw", "shown"),
    [
        ("Quinine in 0.05 M H2SO4", "Quinine in 0.05 M H₂SO₄"),
        ("Acetanilide in CDCl3", "Acetanilide in CDCl₃"),
        ("Ca(OH)2 suspension", "Ca(OH)₂ suspension"),
        ("Paracetamol (DMSO-d6)", "Paracetamol (DMSO-d₆)"),
    ],
)
def test_formulas_in_the_title_are_subscripted(raw, shown):
    title, _ = _title_and_labels("fluorescence", raw)
    assert title.endswith(shown), title


@pytest.mark.parametrize(
    ("raw", "shown"),
    [("CH3", "CH₃"), ("OCH3", "OCH₃"), ("NH2", "NH₂"), ("C=O", "C=O")],
)
def test_formulas_in_peak_labels_are_subscripted(raw, shown):
    _, labels = _title_and_labels("nmr_1h", "", [raw])
    assert labels == [shown]


@pytest.mark.parametrize(
    "raw",
    # Atomnummern und Banden-Namen sind keine Summenformeln.
    ["C2", "H-3", "S1", "band 2", "C=O str.", "1650 cm⁻¹", "$CH_3$ custom"],
)
def test_non_formulas_stay_as_typed(raw):
    _, labels = _title_and_labels("ir", "", [raw])
    assert labels == [raw]


@pytest.mark.parametrize(
    ("spectrum_type", "title"),
    [
        ("nmr_1h", "Paracetamol 1H NMR (DMSO-d6)"),
        ("nmr_1h", "¹H-NMR of ethanol"),
        ("nmr_13c", "Ethanol 13C NMR"),
        ("ir", "IR of aspirin"),
        ("uv_vis", "Caffeine UV-Vis"),
        ("fluorescence", "Quinine fluorescence"),
        ("ms", "Mass spectrum of toluene"),
    ],
)
def test_title_naming_the_method_is_not_prefixed_again(spectrum_type, title):
    from chemdraw_tool.spectrum import SPECTRUM_TYPES

    shown, _ = _title_and_labels(spectrum_type, title)
    assert not shown.startswith(SPECTRUM_TYPES[spectrum_type].title + ":"), shown


def test_isotope_in_the_title_is_superscripted():
    shown, _ = _title_and_labels("nmr_1h", "Paracetamol 1H NMR (DMSO-d6)")
    assert shown == "Paracetamol ¹H NMR (DMSO-d₆)"


def test_plain_title_still_gets_the_method_prefix():
    shown, _ = _title_and_labels("ir", "Aspirin")
    assert shown == "IR spectrum: Aspirin"


@pytest.mark.parametrize(
    "raw",
    # In einem ¹H-Spektrum heißt „2H“ zwei Protonen, nicht Deuterium.
    ["ArH (2H)", "NH, 1H", "CH₃ (3H)", "2C", "1F"],
)
def test_proton_counts_are_not_isotopes(raw):
    _, labels = _title_and_labels("nmr_1h", "", [raw])
    assert labels == [raw]


@pytest.mark.parametrize(
    ("spectrum_type", "title"),
    [
        ("fluorescence", "Chinin Fluoreszenz"),
        ("ms", "Massenspektrum Toluol"),
        ("ir", "Infrarotspektrum Aspirin"),
        ("cd", "Campher CD"),
    ],
)
def test_german_title_naming_the_method_is_not_prefixed(spectrum_type, title):
    from chemdraw_tool.spectrum import SPECTRUM_TYPES

    shown, _ = _title_and_labels(spectrum_type, title)
    assert not shown.startswith(SPECTRUM_TYPES[spectrum_type].title + ":"), shown


@pytest.mark.parametrize(
    ("spectrum_type", "title"),
    [
        ("fluorescence", "Fluorescein in 0.1 M NaOH"),
        ("ir", "Ir(ppy)3"),
        ("cd", "Cd complex"),
        ("ms", "Ms. sample"),
    ],
)
def test_substance_names_are_not_taken_for_the_method(spectrum_type, title):
    from chemdraw_tool.spectrum import SPECTRUM_TYPES

    shown, _ = _title_and_labels(spectrum_type, title)
    assert shown.startswith(SPECTRUM_TYPES[spectrum_type].title + ":"), shown


@pytest.mark.parametrize(
    "raw",
    # Zweitmeinung Gemini 22.11.: Ladung ohne Hochzeichen und Kürzel aus
    # Elementbuchstaben sind keine Summenformeln.
    ["SO42-", "PO43-", "NH4+", "UV254", "CYP2C9", "PS2", "SN2", "SN1", "E2"],
)
def test_charges_and_acronyms_stay_as_typed(raw):
    _, labels = _title_and_labels("ir", "", [raw])
    assert labels == [raw]


@pytest.mark.parametrize(
    ("spectrum_type", "title", "named"),
    [
        ("cd", "Quinine in β-CD", False),
        ("fluorescence", "Green Fluorescent Protein (GFP)", False),
        ("ir", "FTIR Aspirin", True),
        ("ms", "HRMS Paracetamol", True),
        ("ms", "LC-MS Paracetamol", True),
    ],
)
def test_method_detection_edge_cases(spectrum_type, title, named):
    from chemdraw_tool.spectrum import _title_names_method

    assert _title_names_method(spectrum_type, title) is named


@pytest.mark.parametrize(
    ("raw", "shown"),
    [("CH3-CO", "CH₃-CO"), ("H2SO4-solution", "H₂SO₄-solution")],
)
def test_hyphen_after_a_formula_is_not_a_charge(raw, shown):
    _, labels = _title_and_labels("ir", "", [raw])
    assert labels == [shown]


def test_charged_group_stays_whole():
    # Codex-Review 22.11.: die Teilformel in der Klammer wurde einzeln tiefgestellt.
    _, labels = _title_and_labels("ms", "", ["(CH3)3Si+"])
    assert labels == ["(CH3)3Si+"]
