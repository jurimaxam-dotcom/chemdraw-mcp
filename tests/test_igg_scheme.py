"""Tests für das IgG1-Schema (chemdraw_tool/igg_scheme.py)."""

from __future__ import annotations

import pytest

from chemdraw_tool.igg_scheme import (
    build_igg_figure,
    render_igg_png,
    render_igg_svg,
)

DEFAULT_TITLE = "IgG antibody — schematic (IgG1)"


@pytest.fixture(scope="module")
def svg() -> str:
    return render_igg_svg()


@pytest.mark.parametrize(
    "label",
    ["VH", "CH1", "CH2", "CH3", "VL", "CL", "hinge", "Fab", "Fc",
     "antigen-binding", "N297", "heavy chain", "light chain"],
)
def test_svg_enthaelt_beschriftung(svg, label):
    assert label.lower() in svg.lower()


def test_svg_nennt_interketten_disulfide(svg):
    for cys in ("226", "229", "214", "220"):
        assert cys in svg


def test_png_signatur():
    data = render_igg_png(dpi=60)
    assert data.startswith(b"\x89PNG\r\n\x1a\n")


def test_svg_deterministisch():
    assert render_igg_svg("A", "B") == render_igg_svg("A", "B")


def test_eigener_titel_und_untertitel():
    out = render_igg_svg("Trastuzumab", "humanized IgG1κ")
    assert "Trastuzumab" in out
    assert "humanized IgG1κ" in out
    assert DEFAULT_TITLE not in out


def test_standardtitel_bei_leerem_titel(svg):
    assert DEFAULT_TITLE in svg


def test_dollarzeichen_im_titel_stuerzt_nicht_ab():
    out = render_igg_svg("Price $#$ test")
    assert "test" in out


def test_figur_etwa_sieben_zoll():
    fig = build_igg_figure()
    w, h = fig.get_size_inches()
    assert 6.0 <= w <= 8.0 and 6.0 <= h <= 8.0


def test_kein_text_ueberlappt_oder_ragt_heraus():
    """Alle Textboxen liegen in der Figur und schneiden einander nicht."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    fig = build_igg_figure("Trastuzumab", "humanized IgG1κ")
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    fig_box = fig.bbox
    from matplotlib.text import Text

    boxes = []
    seen: set[int] = set()
    for text in fig.findobj(Text):
        if id(text) in seen:
            continue
        seen.add(id(text))
        if not text.get_visible() or not str(text.get_text()).strip():
            continue
        box = text.get_window_extent(renderer)
        assert box.x0 >= fig_box.x0 - 1 and box.x1 <= fig_box.x1 + 1, text.get_text()
        assert box.y0 >= fig_box.y0 - 1 and box.y1 <= fig_box.y1 + 1, text.get_text()
        boxes.append((text.get_text(), box))
    for i, (ta, a) in enumerate(boxes):
        for tb, b in boxes[i + 1:]:
            assert not a.overlaps(b), f"{ta!r} überlappt {tb!r}"
