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
        "Metamizol (unbekannte Form)",  # beliebige Klammerzusätze bleiben gesperrt
        "Citral A+C",
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


def test_all_salt_word_anion_spellings_have_a_translation():
    """Die endliche Anion-Sprache des Salzschutzes muss übersetzbar sein.

    Nur der Anion-Abschnitt vor natrium; Kationen und Salz/Hydrat sind keine
    Anion-Suffixe. Der Parser bleibt testintern, neue Regex-Operatoren fallen rot.
    """
    from itertools import product
    from re import _parser

    from chemdraw_tool.de_names import _ANIONS
    from chemdraw_tool.resolver import _SALT_WORD

    def expand(tokens):
        words = [""]
        for op, value in tokens:
            if op is _parser.LITERAL:
                choices = [chr(value)]
            elif op is _parser.IN:
                assert all(kind is _parser.LITERAL for kind, _ in value)
                choices = [chr(char) for _, char in value]
            elif op is _parser.SUBPATTERN:
                choices = expand(value[-1])
            elif op is _parser.BRANCH:
                choices = [word for branch in value[1] for word in expand(branch)]
            elif op is _parser.MAX_REPEAT:
                low, high, child = value
                assert (low, high) == (0, 1)
                choices = [""] + expand(child)
            else:
                pytest.fail(f"Ungeprüfter Regex-Operator: {op}")
            words = [left + right for left, right in product(words, choices)]
        return words

    anions = set(expand(_parser.parse(_SALT_WORD.pattern.split("|natrium")[0], 0)))
    # Hydrogentartrat wird vom Salzschutz über das angehängte tartrat erkannt.
    anions.add("hydrogentartrat")
    assert all(_SALT_WORD.search(word) for word in anions)
    assert not (missing := anions - _ANIONS.keys()), sorted(missing)


@pytest.mark.parametrize(
    ("german", "english"),
    [("Metoprololhydrogentartrat", "Metoprolol hydrogen tartrate"),
     ("Sorafenibtosylat", "Sorafenib tosylate"),
     ("Amiloridhydroiodid", "Amiloride hydroiodide")],
)
def test_long_and_new_counterions_are_not_split_at_short_suffixes(german, english):
    assert english_variant(german) == english


@pytest.mark.parametrize(("name", "expected"), [
    ("Cefixim Anhydrat", "Cefixime"),
    ("Metamizol (freie Säure)", "Metamizol"),
    ("Citral A+B", "Citral"),
])
def test_only_measured_form_suffixes_are_removed(name, expected):
    assert english_variant(name) == expected


@pytest.mark.parametrize("name", ["Cefixim Trihydrat", "Cefixim Natriumsalz", "Metamizol (Natrium)"])
def test_other_form_suffixes_are_not_discarded(name):
    variant = english_variant(name)
    assert variant is None or variant != "Cefixime"
    if "(" in name:
        assert variant is None


def test_edta_composite_stems_get_both_linking_vowels():
    assert english_variant("Ethylendiamintetraessigsäure") == "ethylenediaminetetraacetic acid"
    assert english_variant("ethylenediaminetetraacetic acid") is None


def test_meglumine_antimoniate_is_an_exact_name_not_a_generic_glucamine_rule():
    assert english_variant("N-Methylglucaminantimonat") == "meglumine antimoniate"
    assert english_variant("n-methylglucaminantimonat") == "meglumine antimoniate"
    assert english_variant("N-Methylglucaminchlorid") != "meglumine antimoniate"


def test_dinitrate_is_not_split_into_stem_di_and_nitrate():
    assert english_variant("Isosorbiddinitrat") == "Isosorbide dinitrate"


def test_benzathine_is_separated_without_adding_e_to_penicillin():
    assert english_variant("Benzylpenicillin-Benzathin") == "Benzylpenicillin benzathine"
    assert english_variant("Benzylpenicillinbenzathin") == "Benzylpenicillin benzathine"
