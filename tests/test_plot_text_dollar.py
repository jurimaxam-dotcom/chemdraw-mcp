"""Ein `$` in Nutzertext darf kein Diagramm abstürzen lassen.

matplotlib liest Text zwischen zwei `$` als Mathtext. `A $#$ B` ist kein gültiger
Mathtext → ValueError mitten im Rendern (Review 09.11.2026). Gültiger Mathtext
(`CH$_3$`) bleibt, was er war — nur was nicht parst, wird wörtlich gesetzt.
"""

import pytest

from chemdraw_tool import (
    calibration,
    calibration_plot,
    ph_plots,
    pk_plots,
    spectrum,
    tlc,
)
from chemdraw_tool.ph_plots import safe_text

BAD = "A $#$ B"


def test_valid_mathtext_and_plain_text_are_untouched():
    assert safe_text("Aspirin") == "Aspirin"
    assert safe_text("CH$_3$") == "CH$_3$"
    assert safe_text("costs 5 $") == "costs 5 $"


def test_unparsable_mathtext_is_set_literally():
    assert safe_text(BAD) == r"A \$#\$ B"


FAELLE = {
    "spectrum-title": lambda: spectrum.render_spectrum_png(
        "ir", [{"position": 1700, "label": "C=O"}], title=BAD
    ),
    "spectrum-label": lambda: spectrum.render_spectrum_png(
        "ir", [{"position": 1700, "label": BAD}]
    ),
    "tlc-title": lambda: tlc.render_tlc_png(
        [{"name": "A", "spots": [{"rf": 0.5}]}], title=BAD
    ),
    "tlc-lane": lambda: tlc.render_tlc_png([{"name": BAD, "spots": [{"rf": 0.5}]}]),
    "tlc-spot": lambda: tlc.render_tlc_png(
        [{"name": "A", "spots": [{"rf": 0.5, "label": BAD}]}]
    ),
    "tlc-solvent": lambda: tlc.render_tlc_png(
        [{"name": "A", "spots": [{"rf": 0.5}]}], solvent=BAD, detection=BAD
    ),
    "titration-title": lambda: ph_plots.render_titration_png(
        pka_values=[4.76], c_acid=0.1, v_acid_ml=20, c_titrant=0.1, title=BAD
    ),
    "titration-indicator": lambda: ph_plots.render_titration_png(
        pka_values=[4.76], c_acid=0.1, v_acid_ml=20, c_titrant=0.1,
        indicator={"name": BAD, "ph_range": [8.2, 10]},
    ),
    "species-title": lambda: ph_plots.render_species_png([4.76], None, BAD),
    "species-labels": lambda: ph_plots.render_species_png([4.76], [BAD, "A-"], ""),
    "pk-drug": lambda: pk_plots.render_pk_png(dose=500, vd=40, ke=0.15, drug=BAD),
    "dose-response": lambda: pk_plots.render_dose_response_png(ec50=10, unit=BAD, drug=BAD),
    "calibration": lambda: calibration_plot.render_png(
        regression=calibration.linear_regression([1, 2, 3, 4], [0.1, 0.2, 0.31, 0.4]),
        title=BAD, x_label=BAD, y_label=BAD,
    ),
}


@pytest.mark.parametrize("name", FAELLE)
def test_dollar_text_renders(name):
    assert FAELLE[name]().startswith(b"\x89PNG")
