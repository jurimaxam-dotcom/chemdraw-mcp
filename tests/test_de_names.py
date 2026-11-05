"""Deutsche Trivialnamen → englische Schreibweise (Masse-Eval 11/2026, Befund 1).

75 deutsche Eingaben fand keine Quelle, obwohl PubChem den Stoff unter dem
englischen INN führt (Amilorid ↔ amiloride). Die Regeln unten sind genau die,
die in der Messung gegen PubChem getroffen haben (scratchpad-Messung 05.11.:
68 von 80 not_found-Eingaben danach mit richtigem InChIKey-Gerüst).
"""

import pytest

from chemdraw_tool.de_names import english_variant


@pytest.mark.parametrize(
    ("german", "english"),
    [
        # Endungen der INN-Eindeutschung
        ("Dexamethason", "Dexamethasone"),
        ("Amilorid", "Amiloride"),
        ("Lamivudin", "Lamivudine"),
        ("Artesunat", "Artesunate"),
        ("Isofluran", "Isoflurane"),
        ("Ceftazidim", "Ceftazidime"),
        ("gliclazid", "gliclazide"),
        # -säure → -ic acid, inkl. deutscher Stämme
        ("Maleinsäure", "Maleinic acid"),
        ("Zoledronsäure", "Zoledronic acid"),
        ("Amidotrizoesäure", "Amidotrizoic acid"),
        ("4-Aminosalicylsäure", "4-Aminosalicylic acid"),
        ("meso-Dimercaptobernsteinsäure", "meso-Dimercaptosuccinic acid"),
        ("γ-Aminobuttersäure", "gamma-Aminobutyric acid"),
        # Kation vorn, Anion hinten — zusammengeschrieben oder mit Bindestrich
        ("Natriumlactat", "sodium lactate"),
        ("Calciumgluconat", "calcium gluconate"),
        ("Silbersulfadiazin", "silver sulfadiazine"),
        ("Alcuroniumchlorid", "Alcuronium chloride"),
        ("Medroxyprogesteronacetat", "Medroxyprogesterone acetate"),
        ("Beclometasondipropionat", "Beclometasone dipropionate"),
        ("Atracurium-Besilat", "Atracurium besilate"),
        ("Vecuronium-Bromid", "Vecuronium bromide"),
        ("Fludarabin-Phosphat", "Fludarabine phosphate"),
        # Halogen-Präfix ohne Bindevokal
        ("5-Fluorcytosin", "5-Fluorocytosine"),
        # Racemat-Präfix: PubChem führt das Racemat unter dem nackten Namen
        ("(RS)-Ketamin", "Ketamine"),
        ("(RS)-methadone", "methadone"),
        ("(±)-Cyclophosphamid", "Cyclophosphamide"),
    ],
)
def test_english_variant(german, english):
    assert english_variant(german) == english


@pytest.mark.parametrize(
    "name",
    [
        "caffeine",
        "ethanol",
        "Metamizol (freie Säure)",  # Klammerzusatz: keine sichere Umschreibung
        "Citral A+B",
        "",
    ],
)
def test_no_variant_when_nothing_to_rewrite(name):
    """None heißt: kein zweiter Netzversuch. Englische Namen bleiben unberührt."""
    assert english_variant(name) is None


def test_english_names_do_not_grow_twice():
    """Englische -ine/-ide/-one/-ic-acid-Namen bleiben, wie sie sind. (Ein
    englischer Name auf -in wie 'aspirin' bekäme ein -e; harmlos, weil die
    Variante erst gefragt wird, wenn alle Quellen den Originalnamen verwarfen.)"""
    assert english_variant("caffeine") is None
    assert english_variant("amiloride") is None
    assert english_variant("dexamethasone") is None
    assert english_variant("maleic acid") is None
