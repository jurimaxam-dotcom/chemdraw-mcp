"""Formeln in Reaktionsbedingungen tiefstellen — und nur Formeln.

Die Bedingungen schreibt das Modell als Klartext ("H2SO4, 80 °C, 2 h"). Eine
Ziffer wird nur dann tiefgestellt, wenn sie in einem leerzeichenfreien Token
steht, das als Ganzes wie eine Summenformel gebaut ist, und direkt auf ein
Elementsymbol oder eine schließende Klammer folgt. Temperaturen, Zeiten,
Äquivalente und Prozente bleiben stehen — ein tiefgestelltes "2 h" wäre ein
sichtbarer Fehler, den niemand bestellt hat.
"""

import pytest

from chemdraw_tool.condition_text import formula_runs, subscript_formulas


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Formeln
        ("H2SO4", "H₂SO₄"),
        ("CH3OH", "CH₃OH"),
        ("Ca(OH)2", "Ca(OH)₂"),
        ("CH2Cl2", "CH₂Cl₂"),
        ("NaBH4, MeOH", "NaBH₄, MeOH"),
        ("H2SO4 (cat.), Δ", "H₂SO₄ (cat.), Δ"),
        ("H2, Pd/C", "H₂, Pd/C"),
        ("Et3N, CH2Cl2", "Et₃N, CH₂Cl₂"),
        ("Pd(PPh3)4, K2CO3", "Pd(PPh₃)₄, K₂CO₃"),
        ("Ti(OiPr)4", "Ti(OiPr)₄"),
        ("[Cu(NH3)4]2+", "[Cu(NH₃)₄]2+"),
        ("LiAlH4; then H2O", "LiAlH₄; then H₂O"),
        ("H2O/THF", "H₂O/THF"),
        ("conc. HNO3:H2SO4", "conc. HNO₃:H₂SO₄"),
        # Keine Formeln
        ("80 °C", "80 °C"),
        ("0–5 °C", "0–5 °C"),
        ("0-5 °C", "0-5 °C"),
        ("2 eq", "2 eq"),
        ("2 h", "2 h"),
        ("12h", "12h"),
        ("85 %", "85 %"),
        ("Pd/C", "Pd/C"),
        ("THF", "THF"),
        ("pH 7", "pH 7"),
        ("1 M HCl", "1 M HCl"),
        ("2H2O", "2H2O"),  # Koeffizient vorn: bewusst unangetastet
        ("SN2", "SN2"),  # Mechanismus-Kürzel, keine Formel
        ("reflux, 3 d", "reflux, 3 d"),
        ("hν", "hν"),
        ("", ""),
    ],
)
def test_subscript_formulas(text, expected):
    assert subscript_formulas(text) == expected


def test_subscript_keeps_line_breaks():
    assert subscript_formulas("H2SO4\n80 °C") == "H₂SO₄\n80 °C"


def test_formula_runs_marks_only_subscript_digits():
    assert formula_runs("H2SO4, 80 °C") == [
        ("H", False),
        ("2", True),
        ("SO", False),
        ("4", True),
        (", 80 °C", False),
    ]


def test_formula_runs_without_formula_is_one_plain_run():
    """Eine Bedingung ohne Formel bleibt EIN Lauf — so bleibt das CDXML
    eines Altaufrufs byte-identisch."""
    assert formula_runs("Δ, 2 h") == [("Δ, 2 h", False)]
    assert formula_runs("") == []
