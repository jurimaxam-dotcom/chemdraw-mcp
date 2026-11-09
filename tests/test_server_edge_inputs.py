"""Rand-Eingaben, die als Pauschalfehler, als Absturz oder als stilles Falschergebnis endeten.

Review 09.11.2026 (alle Fälle einzeln rot gesehen). Gemeinsames Muster: Der Client bekommt von
allem außer `ValueError` nur „Error executing tool …“ — eine fehlende Prüfung kostet den Nutzer
also die Erklärung, was an der Eingabe nicht stimmt.
"""

import pytest

from chemdraw_tool import server as s

DIRS = [
    "OUTPUT_DIR", "REACTION_DIR", "SPECTRUM_DIR", "TLC_DIR",
    "SCOPE_DIR", "ANKI_DIR", "PLOT_DIR", "THREED_DIR",
]


@pytest.fixture(autouse=True)
def _isoliert(tmp_path, monkeypatch):
    for name in DIRS:
        monkeypatch.setattr(s, name, tmp_path / name.lower())
    monkeypatch.setattr(s, "_enrich_properties", lambda smiles: {})


def _dateien(tmp_path):
    return sorted(p.name for p in tmp_path.rglob("*") if p.is_file())


# --- 1. Überlange Dateinamen ------------------------------------------------------------------


def test_slug_stays_below_the_filename_limit():
    slug = s._slugify("Spektrum " * 60)
    assert len(slug.encode()) <= 140


def test_short_slugs_are_unchanged():
    """Bestehende Dateinamen dürfen sich durch die Kürzung nicht ändern."""
    assert s._slugify("Acetylsalicylic acid") == "acetylsalicylic-acid"
    assert s._slugify("Suzuki scope (2026)") == "suzuki-scope-2026"


def test_long_titles_that_differ_late_do_not_collide():
    a = s._slugify("x" * 300 + " eins")
    b = s._slugify("x" * 300 + " zwei")
    assert a != b


def test_long_smiles_is_drawn_instead_of_crashing(tmp_path):
    payload = s.generate_molecule("C" * 250 + "O")
    assert payload.type == "molecule"
    assert all(len(n.encode()) < 255 for n in _dateien(tmp_path))


def test_long_title_on_a_lab_graphic(tmp_path):
    s.generate_spectrum("ir", [{"position": 1700, "intensity": 1}], title="Spektrum " * 40)
    assert _dateien(tmp_path)


# --- 2. calculate_ph: fehlender Wert ist nicht 0 ------------------------------------------------


def test_ionisation_without_pka_is_refused():
    with pytest.raises(ValueError, match="pka"):
        s.calculate_ph("ionisation", target_ph=7.4)


def test_ionisation_without_ph_is_refused():
    with pytest.raises(ValueError, match="target_ph"):
        s.calculate_ph("ionisation", pka=4.4)


def test_buffer_recipe_without_target_ph_is_refused():
    with pytest.raises(ValueError, match="target_ph"):
        s.calculate_ph("buffer_recipe", pka=4.76, total_concentration=0.1, volume_ml=100)


def test_ph_zero_is_a_value_not_a_gap():
    """pH 0 (1 M starke Säure) ist eine gültige Angabe und darf nicht als „fehlt“ gelten."""
    text = s.calculate_ph("ionisation", pka=4.4, target_ph=0)
    assert "Uncharged at pH 0" in text


# --- 3. SMILES im Dateinamen: Großschreibung und / \ tragen Bedeutung ---------------------------


@pytest.mark.parametrize(
    "a, b",
    [("c1ccccc1", "C1CCCCC1"), ("C/C=C/C", "C/C=C\\C")],
    ids=["benzol-cyclohexan", "e-z-buten"],
)
def test_3d_files_of_different_smiles_do_not_overwrite(a, b):
    first = s.generate_3d(a).files["sdf"]
    second = s.generate_3d(b).files["sdf"]
    assert first != second


def test_3d_file_of_a_name_keeps_its_readable_name(monkeypatch):
    from rdkit import Chem

    from chemdraw_tool.resolver import Resolved

    monkeypatch.setattr(
        s, "resolve", lambda name: Resolved("CCO", Chem.MolFromSmiles("CCO"))
    )
    assert s.generate_3d("ethanol").files["sdf"].endswith("/ethanol.sdf")


def test_comparisons_of_different_smiles_do_not_overwrite():
    first = s.compare_molecules(["c1ccccc1", "CCO"]).files["png"]
    second = s.compare_molecules(["C1CCCCC1", "CCO"]).files["png"]
    assert first != second


# --- 4.–8. Fehlende Eingabeprüfungen ------------------------------------------------------------


def test_compare_with_wrong_number_of_labels():
    with pytest.raises(ValueError, match="labels"):
        s.compare_molecules(["CCO", "CCC"], labels=["a"])


@pytest.mark.parametrize("reactants, products", [([], []), (["CCO"], []), ([], ["CCO"])])
def test_reaction_needs_both_sides(reactants, products):
    with pytest.raises(ValueError, match="at least one"):
        s.generate_reaction(reactants, products)


@pytest.mark.parametrize(
    "indicator",
    [{"name": "PP"}, {"name": "PP", "ph_range": [8.2]}, {"name": "PP", "ph_range": "8-10"}],
)
def test_titration_indicator_without_a_range(indicator):
    with pytest.raises(ValueError, match="ph_range"):
        s.generate_titration_curve("x", [4.76], 0.1, 20, 0.1, indicator=indicator)


@pytest.mark.parametrize("ec50", [0, -5])
def test_dose_response_needs_a_positive_ec50(ec50):
    with pytest.raises(ValueError, match="ec50"):
        s.generate_dose_response(ec50)


def test_content_with_empty_lists_names_the_real_parameters():
    with pytest.raises(ValueError, match="weights_mg"):
        s.calculate_content(
            "saponification_value", [], [],
            titrant_concentration=0.5, blank_ml=20, known_acid_value=1,
        )


# --- 9. Werte, die still umgedeutet wurden ------------------------------------------------------


def test_unknown_anki_delivery_is_refused():
    with pytest.raises(ValueError, match="deliver"):
        s.export_anki_deck("Deck", [{"front": {"text": "a"}, "back": {"text": "b"}}], deliver="email")


@pytest.mark.parametrize("f", [0, -0.2, 2])
def test_pk_curve_bioavailability_is_a_fraction(f):
    with pytest.raises(ValueError, match="bioavailability"):
        s.generate_pk_curve(500, 70, half_life_h=4, ka_per_h=1.2, bioavailability=f)


def test_pk_curve_refuses_a_zero_interval():
    with pytest.raises(ValueError, match="tau"):
        s.generate_pk_curve(500, 70, half_life_h=4, tau_h=0)
