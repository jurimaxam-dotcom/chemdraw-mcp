"""Deutsche Trivialnamen → englische Schreibweise (Masse-Eval 11/2026, Befund 1).

75 deutsche Eingaben fand keine Quelle, obwohl PubChem den Stoff unter dem
englischen INN führt (Amilorid ↔ amiloride). Die Regeln unten sind genau die,
die in der Messung gegen PubChem getroffen haben (scratchpad-Messung 05.11.:
68 von 80 not_found-Eingaben danach mit richtigem InChIKey-Gerüst).
"""

import pytest

from chemdraw_tool.de_names import english_variant, salt_variant


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
        # Salznamen (06.11.2026): zusammengesetzte Gegenionen vor ihrem Kurzwort —
        # sonst bleibt "hydro" am Stamm ("Bendamustinhydro chloride", not_found)
        ("Bendamustinhydrochlorid", "Bendamustine hydrochloride"),
        ("Bendamustin Hydrochlorid", "Bendamustine hydrochloride"),
        ("Bendamustin-Hydrochlorid", "Bendamustine hydrochloride"),
        ("Histamindihydrochlorid", "Histamine dihydrochloride"),
        ("Dextromethorphanhydrobromid", "Dextromethorphane hydrobromide"),
        ("Metoprololtartrat", "Metoprolol tartrate"),
        ("Enalaprilmaleat", "Enalapril maleate"),
        ("Bisoprololfumarat", "Bisoprolol fumarate"),
        ("Doxazosinmesilat", "Doxazosine mesilate"),
        ("Sumatriptansuccinat", "Sumatriptane succinate"),
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


# Salznamen-Messung (06.11.2026, docs/evidence/masse-eval-2026-11/salznamen_mess.json):
# PubChem kennt manche Salze nur mit dem INN ohne Endungs-e ("Cefalotin sodium",
# "Anamorelin hydrochloride"). salt_variant übersetzt nur das Gegenion und lässt
# den Stamm stehen; None, wenn kein Gegenion am Ende steht oder die Variante
# dieselbe ist wie english_variant (dann kein zweiter Netzaufruf).
@pytest.mark.parametrize(
    ("german", "english"),
    [
        ("Cefalotin-Natrium", "Cefalotin sodium"),
        ("Benazolin-Kalium", "Benazolin potassium"),
        ("Anamorelinhydrochlorid", "Anamorelin hydrochloride"),
        ("Camostatmesilat", "Camostat mesilate"),
        ("Dibekacinsulfat", "Dibekacin sulfate"),
        ("Metformin Hydrochlorid", "Metformin hydrochloride"),
    ],
)
def test_salt_variant_keeps_the_stem(german, english):
    assert salt_variant(german) == english


@pytest.mark.parametrize("name", ["Metoprololtartrat", "Dexamethason", "Buspiron", "Natrium", "caffeine", ""])
def test_no_salt_variant_without_counterion_or_when_english_variant_is_the_same(name):
    assert salt_variant(name) is None


@pytest.mark.parametrize(
    ("german", "english"),
    [("Cefalotin-Natrium", "Cefalotine sodium"), ("Metamizolnatrium", "Metamizol sodium"),
     ("Natriumchlorid", "sodium chloride"), ("Kaliumcitrat", "potassium citrate")],
)
def test_sodium_and_potassium_also_stand_behind_the_stem(german, english):
    """-Natrium/-Kalium hinten ist das Gegenion wie -chlorid; vorn bleibt es Kation."""
    assert english_variant(german) == english
