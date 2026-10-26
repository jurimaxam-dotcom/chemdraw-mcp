"""Stoffbilanz einer gezeichneten Gleichung (Etappe 6).

Zwei getrennte Schritte: (1) Erhaltung prüfen, wie die Gleichung dasteht
(alle Koeffizienten 1); (2) nur bei eindeutigem, positivem Nullraum
Koeffizienten vorschlagen. Die Zeichnung selbst ändert sich nie.
"""

from rdkit import Chem

from chemdraw_tool.reaction_balance import (
    check_balance,
    element_counts,
    suggest_coefficients,
)


def _mols(*smiles):
    return [Chem.MolFromSmiles(s) for s in smiles]


def _check(left, right, arrow="forward"):
    return check_balance(_mols(*left), _mols(*right), arrow=arrow)


# --- Elementzählung -------------------------------------------------------


def test_counts_implicit_hydrogens():
    assert element_counts(Chem.MolFromSmiles("CCO")) == ({"C": 2, "H": 6, "O": 1}, 0)


def test_explicit_h_atoms_are_not_double_counted():
    h2 = Chem.MolFromSmiles("[H][H]")
    assert h2.GetNumAtoms() == 2
    assert element_counts(h2) == ({"H": 2}, 0)
    with_hs = Chem.AddHs(Chem.MolFromSmiles("CCO"))
    assert element_counts(with_hs) == ({"C": 2, "H": 6, "O": 1}, 0)


def test_isotopes_count_as_their_element():
    assert element_counts(Chem.MolFromSmiles("[14CH4]")) == ({"C": 1, "H": 4}, 0)
    assert element_counts(Chem.MolFromSmiles("[2H]O[2H]")) == ({"H": 2, "O": 1}, 0)


def test_charge_is_its_own_line():
    assert element_counts(Chem.MolFromSmiles("[NH4+]")) == ({"N": 1, "H": 4}, 1)


# --- Die sieben Fälle aus dem Auftrag --------------------------------------


def test_fischer_esterification_is_balanced():
    b = _check(["CCO", "CC(=O)O"], ["CCOC(C)=O", "O"])
    assert b.balanced is True
    assert b.difference == {}
    assert b.chargeDifference == 0
    assert b.suggestedCoefficients is None
    assert b.summary == ""
    assert "both sides" in b.note


def test_fischer_without_water_lacks_water_on_the_right():
    b = _check(["CCO", "CC(=O)O"], ["CCOC(C)=O"])
    assert b.balanced is False
    # + = rechts mehr: links stehen 2 H und 1 O zu viel.
    assert b.difference == {"H": -2, "O": -1}
    assert b.summary == "right side lacks H₂O"
    assert "right side lacks H2O" in b.note
    # Kein Koeffizientensatz gleicht diese drei Stoffe aus.
    assert b.suggestedCoefficients is None
    assert "no coefficients" in b.note


def test_hydrogen_oxygen_water_gets_suggestion():
    b = _check(["[H][H]", "O=O"], ["O"])
    assert b.balanced is False
    assert b.difference == {"O": -1}
    assert b.summary == "left: +1 O"
    assert b.suggestedCoefficients == [2, 1, 2]
    assert b.suggestedEquation == "2 H₂ + O₂ → 2 H₂O"
    assert "not balanced as drawn" in b.note.lower()
    assert "2 H2 + O2 → 2 H2O" in b.note


def test_methane_combustion_suggestion():
    b = _check(["C", "O=O"], ["O=C=O", "O"])
    assert b.balanced is False
    assert b.difference == {"H": -2, "O": 1}
    assert b.summary == "left: +2 H; right: +1 O"
    assert b.suggestedCoefficients == [1, 2, 1, 2]
    assert b.suggestedEquation == "CH₄ + 2 O₂ → CO₂ + 2 H₂O"


def test_ammonium_hydroxide_charge_balanced():
    b = _check(["[NH4+]", "[OH-]"], ["N", "O"])
    assert b.balanced is True
    assert b.chargeDifference == 0
    assert b.formulas == ["H4N+", "HO-", "H3N", "H2O"]


def test_multidimensional_nullspace_gives_no_suggestion():
    b = _check(["[H][H]", "O=O"], ["O", "OO"])
    assert b.balanced is False
    assert b.suggestedCoefficients is None
    assert "more than one" in b.note


def test_negative_coefficient_gives_no_suggestion():
    # H2O + H2 → H2O2 ginge nur mit H2 auf der anderen Seite.
    b = _check(["O", "[H][H]"], ["OO"])
    assert b.balanced is False
    assert b.suggestedCoefficients is None
    assert "other side" in b.note


# --- Randfälle -------------------------------------------------------------


def test_zero_coefficient_gives_no_suggestion():
    b = _check(["[H][H]", "O=O", "N#N"], ["O"])
    assert b.suggestedCoefficients is None
    assert "does not take part" in b.note


def test_charge_difference_reported():
    b = _check(["[NH4+]"], ["N"])
    assert b.balanced is False
    assert b.difference == {"H": -1}
    assert b.chargeDifference == -1
    assert b.summary == "right side lacks H⁺"


def test_retro_keeps_left_right_and_neutral_text():
    b = _check(["CCOC(C)=O", "O"], ["CCO", "CC(=O)O"], arrow="retro")
    assert b.balanced is True
    assert "both sides" in b.note
    s = _check(["O"], ["[H][H]", "O=O"], arrow="retro")
    assert s.suggestedEquation == "2 H₂O ⇒ 2 H₂ + O₂"
    for word in ("reactant", "product", "educt"):
        assert word not in s.note.lower()


def test_equilibrium_arrow_in_suggestion():
    b = _check(["[H][H]", "O=O"], ["O"], arrow="equilibrium")
    assert b.suggestedEquation == "2 H₂ + O₂ ⇌ 2 H₂O"


def test_placeholder_atoms_are_not_checked():
    assert _check(["*CO"], ["*C=O"]) is None


def test_empty_side_is_not_checked():
    assert check_balance(_mols("CCO"), []) is None


def test_suggest_coefficients_plain():
    left = [element_counts(m) for m in _mols("[H][H]", "O=O")]
    right = [element_counts(m) for m in _mols("O")]
    coeffs, reason = suggest_coefficients(left, right)
    assert coeffs == [2, 1, 2]
    assert reason == ""


def test_lacking_molecule_uses_conventional_formula():
    # Hill hieße "ClH"/"H3N" — für den Badge die übliche Schreibweise.
    b = _check(["CC(=O)Cl", "CO"], ["CC(=O)OC"])
    assert b.summary == "right side lacks HCl"
    assert "right side lacks HCl" in b.note
    n = _check(["CC(=O)Cl", "N"], ["CC(N)=O"])
    assert n.summary == "right side lacks HCl"
    ammonia = _check(["CC(N)=O", "O"], ["CC(=O)O"])
    assert ammonia.summary == "right side lacks NH₃"
