"""Kalibriergerade als Bild: die Probenbeschriftung muss lesbar neben der Geraden stehen.

Befund 22.11.2026 (Chinin-Fluoreszenz): Die Zahl stand rechts oberhalb der Probe —
bei steigender Geraden genau dort, wo die Gerade weiterläuft. Geprüft wird
geometrisch im gerenderten Bild: Der Textrahmen darf weder die Regressionsgerade
noch einen Standard-Punkt schneiden.
"""

import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg

from chempane import calibration_plot
from chempane.calibration import interpolate, linear_regression

CHININ_X = [0.05, 0.10, 0.20, 0.30, 0.40]
CHININ_Y = [27.1, 53.0, 101.4, 152.2, 200.6]


def _rendered(x, y, signals):
    regression = linear_regression(x, y)
    unknowns = [interpolate(s, regression) for s in signals]
    fig = calibration_plot.build_figure(regression=regression, unknowns=unknowns)
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    return fig, canvas.get_renderer()


def _labels(fig):
    ax = fig.axes[0]
    return [t for t in ax.texts if t.get_text()]


def _regression_line(fig):
    # Die einzige durchgezogene Linie mit zorder 1 ist die Gerade.
    ax = fig.axes[0]
    (line,) = [ln for ln in ax.lines if ln.get_linestyle() == "-" and ln.get_zorder() == 1]
    return line


@pytest.mark.parametrize(
    ("x", "y", "signals"),
    [
        (CHININ_X, CHININ_Y, [92.1]),  # der gemeldete Fall
        (CHININ_X, CHININ_Y, [40.0, 180.0]),  # links unten und rechts oben
        ([1, 2, 3, 4, 5], [11.0, 9.0, 7.0, 5.0, 3.0], [8.0]),  # fallende Gerade
    ],
)
def test_sample_label_does_not_touch_the_line(x, y, signals):
    fig, renderer = _rendered(x, y, signals)
    line = _regression_line(fig)
    path = line.get_path().transformed(line.get_transform())
    labels = _labels(fig)
    assert len(labels) == len(signals)
    for label in labels:
        box = label.get_window_extent(renderer)
        assert not path.intersects_bbox(box, filled=False), label.get_text()


def test_sample_label_does_not_cover_a_standard():
    fig, renderer = _rendered(CHININ_X, CHININ_Y, [92.1, 100.0])
    ax = fig.axes[0]
    standards = ax.transData.transform(list(zip(CHININ_X, CHININ_Y)))
    for label in _labels(fig):
        box = label.get_window_extent(renderer).expanded(1.0, 1.0)
        for px, py in standards:
            assert not box.contains(px, py), label.get_text()


def test_sample_label_stays_inside_the_axes():
    fig, renderer = _rendered(CHININ_X, CHININ_Y, [27.5, 199.0])
    axes_box = fig.axes[0].get_window_extent(renderer)
    for label in _labels(fig):
        box = label.get_window_extent(renderer)
        assert axes_box.x0 <= box.x0 and box.x1 <= axes_box.x1, label.get_text()
        assert axes_box.y0 <= box.y0 and box.y1 <= axes_box.y1, label.get_text()


def test_sample_label_avoids_a_standard_next_to_its_corner():
    # Codex-Review 22.11.: Probe 1,88 → Zahl „3.1“ lag genau auf dem Standard (3, 2).
    x, y = [1, 2, 3, 4, 5], [0, 1, 2, 3, 3]
    fig, renderer = _rendered(x, y, [1.88])
    ax = fig.axes[0]
    standards = ax.transData.transform(list(zip(x, y)))
    line = _regression_line(fig)
    path = line.get_path().transformed(line.get_transform())
    for label in _labels(fig):
        box = label.get_window_extent(renderer)
        assert not path.intersects_bbox(box, filled=False), label.get_text()
        for px, py in standards:
            assert not box.expanded(1.0, 1.0).padded(4).contains(px, py), (label.get_text(), px, py)
