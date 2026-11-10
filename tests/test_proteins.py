"""Proteine (E6, 10.11.2026): Enzyme, Antikörper, Peptidhormone, Strukturproteine.

Gemessen vor dem Bau (resolver.resolve, mit Netz): "Lysozym", "Trastuzumab",
"hemoglobin", "Trypsin" → not_found; "lysozyme" → ein 159-Atom-Peptidfragment
(PubChem CID 91976556, Titel "Lysozyme"); "alcohol dehydrogenase" → ein
Acyl-CoA (CID 78120390, Titel "Alcohol Dehydrogenase"); "insulin" → die volle
Formel mit 404 Schweratomen. Die UniProt-Antworten unter
tests/__fixtures__/uniprot/ sind echte Antworten vom 10.11.2026, gekürzt.
Kein Test geht ins Netz.
"""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from chemdraw_tool import databases

FIXTURES = Path(__file__).parent / "__fixtures__" / "uniprot"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def _resp(payload: dict) -> Mock:
    m = Mock()
    m.raise_for_status = Mock()
    m.json = Mock(return_value=payload)
    return m


@pytest.fixture
def uniprot_answers(monkeypatch):
    """requests.get in databases → Fixture je Suchbegriff; merkt sich die URLs."""
    calls: list[str] = []

    def install(mapping: dict[str, str]):
        def fake_get(url, timeout=None, **kwargs):
            calls.append(url)
            for needle, fixture in mapping.items():
                if needle in url:
                    return _resp(_fixture(fixture))
            return _resp({"results": []})

        monkeypatch.setattr(databases.requests, "get", fake_get)
        return calls

    return install


# --- databases.uniprot_protein ----------------------------------------------


@pytest.mark.parametrize(
    "name, fixture, accession, matched",
    [
        # Mensch vor Maus, "Lysozyme C" (Variante) zählt, "Lysozyme-like" nicht
        ("lysozyme", "lysozyme", "P61626", "Lysozyme C"),
        # Trypsin-1 heißt bei UniProt "Serine protease 1", der Alt-Name trifft
        ("trypsin", "trypsin", "P07477", "Trypsin I"),
        ("insulin", "insulin", "P01308", "Insulin"),
        # Familie: alphabetisch die alpha-Kette, nicht die epsilon-Kette vorn
        ("hemoglobin", "hemoglobin", "P69905", "Hemoglobin subunit alpha"),
        ("alcohol dehydrogenase", "alcohol-dehydrogenase", "P07327", "Alcohol dehydrogenase 1A"),
    ],
)
def test_uniprot_protein_picks_the_named_human_protein(
    uniprot_answers, name, fixture, accession, matched
):
    uniprot_answers({"": fixture})
    record = databases.uniprot_protein(name)
    assert record is not None
    assert record["accession"] == accession
    assert record["matched"] == matched
    assert record["organism"] == "Homo sapiens"


def test_uniprot_protein_reports_length_mass_and_precursor(uniprot_answers):
    uniprot_answers({"": "insulin"})
    record = databases.uniprot_protein("insulin")
    assert (record["length"], record["mass"]) == (110, 11981)
    # Signalpeptid + C-Peptid: das reife Insulin ist kürzer als 110 aa
    assert record["precursor"] is True
    assert record["family"] is False
    assert record["others"] == []


def test_uniprot_protein_lists_the_other_members_of_a_name(uniprot_answers):
    uniprot_answers({"": "trypsin"})
    record = databases.uniprot_protein("trypsin")
    assert [o["name"] for o in record["others"]] == ["Trypsin-2", "Trypsin-3"]


def test_uniprot_protein_marks_families(uniprot_answers):
    uniprot_answers({"": "hemoglobin"})
    record = databases.uniprot_protein("hemoglobin")
    assert record["family"] is True
    assert [o["name"] for o in record["others"]] == [
        "Hemoglobin subunit beta",
        "Hemoglobin subunit delta",
        "Hemoglobin subunit epsilon",
    ]


@pytest.mark.parametrize("name, fixture", [("glucose", "glucose"), ("glucagon", "glucagon")])
def test_uniprot_protein_ignores_proteins_that_only_contain_the_name(
    uniprot_answers, name, fixture
):
    # glucose: Transporter und Enzyme ("Sodium/glucose cotransporter 1");
    # glucagon: Rezeptor und "Pro-glucagon" — keiner HEISST so.
    uniprot_answers({"": fixture})
    assert databases.uniprot_protein(name) is None


def test_uniprot_protein_accepts_other_organisms_only_by_exact_name(monkeypatch):
    frog = {
        "results": [
            {
                "primaryAccession": "O42143",
                "organism": {"scientificName": "Xenopus laevis", "taxonId": 8355},
                "proteinDescription": {"recommendedName": {"fullName": {"value": "Glucagon-1"}}},
                "sequence": {"length": 266, "molWeight": 30951},
            },
            {
                "primaryAccession": "P00784",
                "organism": {"scientificName": "Carica papaya", "taxonId": 3649},
                "proteinDescription": {"recommendedName": {"fullName": {"value": "Papain"}}},
                "sequence": {"length": 345, "molWeight": 38922},
            },
        ]
    }
    monkeypatch.setattr(databases.requests, "get", Mock(return_value=_resp(frog)))
    assert databases.uniprot_protein("glucagon") is None
    assert databases.uniprot_protein("papain")["accession"] == "P00784"


def test_uniprot_protein_asks_once_with_the_german_variant(uniprot_answers):
    calls = uniprot_answers({"": "lysozym-de"})
    record = databases.uniprot_protein("Lysozym")
    assert record["accession"] == "P61626"
    assert len(calls) == 1
    assert "lysozyme" in requests.utils.unquote(calls[0])


@pytest.mark.parametrize(
    "name, variants",
    [
        ("Lysozym", ["Lysozym", "lysozyme"]),
        ("Katalase", ["Katalase", "catalase"]),
        ("Hämoglobin", ["Hämoglobin", "hemoglobin"]),
        ("Kollagen", ["Kollagen", "collagen"]),
        ("Glukagon", ["Glukagon", "glucagon"]),
        ("Hexokinase", ["Hexokinase"]),
        ("trypsin", ["trypsin"]),
    ],
)
def test_protein_name_variants(name, variants):
    assert databases.protein_name_variants(name) == variants


def test_uniprot_protein_returns_none_on_network_error(monkeypatch):
    def down(*args, **kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(databases.requests, "get", down)
    assert databases.uniprot_protein("lysozyme") is None


def test_uniprot_protein_uses_a_short_timeout(uniprot_answers, monkeypatch):
    seen = {}

    def fake_get(url, timeout=None):
        seen["timeout"] = timeout
        return _resp({"results": []})

    monkeypatch.setattr(databases.requests, "get", fake_get)
    databases.uniprot_protein("lysozyme")
    assert seen["timeout"] == databases.PROTEIN_TIMEOUT
    connect, read = databases.PROTEIN_TIMEOUT
    assert connect <= 2 and read <= 4


@pytest.mark.parametrize(
    "name, expected",
    [
        ("trastuzumab", True),
        ("Adalimumab", True),
        ("rituximab", True),
        ("mab", False),
        ("Schiff base", False),
        ("aspirin", False),
    ],
)
def test_is_antibody_name(name, expected):
    assert databases.is_antibody_name(name) is expected


# --- Resolver: Protein statt not_found --------------------------------------

from chemdraw_tool import resolver  # noqa: E402
from chemdraw_tool.resolver import NameResolutionError  # noqa: E402


def _record(name: str, fixture: str, monkeypatch) -> dict:
    """Echter Parse der Fixture durch databases.uniprot_protein."""
    monkeypatch.setattr(databases.requests, "get", lambda url, timeout=None: _resp(_fixture(fixture)))
    record = databases.uniprot_protein(name)
    assert record is not None
    return record


@pytest.fixture
def cascade(monkeypatch):
    """Strukturquellen ohne Netz: jede antwortet 'kennt den Namen nicht'.

    Gibt das Protokoll der Quellen-Aufrufe zurück; `hits` setzt Treffer.
    """
    resolver.resolve_name.cache_clear()
    calls: list[str] = []
    hits: dict[str, str] = {}

    def source(label):
        def lookup(name, report=None):
            calls.append(f"{label}:{name}")
            if name in hits:
                return hits[name]
            resolver._record(report, label, resolver._NOT_FOUND, "name unknown")
            return None

        return lookup

    monkeypatch.setattr(resolver, "_opsin_lookup", lambda name: None)
    monkeypatch.setattr(resolver, "_pubchem_lookup", source(resolver._PUBCHEM))
    monkeypatch.setattr(resolver, "_nci_cir_lookup", source(resolver._NCI))
    yield type("Cascade", (), {"calls": calls, "hits": hits})
    resolver.resolve_name.cache_clear()


@pytest.fixture
def no_table(monkeypatch):
    """Der UniProt-Weg aus E6 ohne die Laborstandard-Tabelle aus E8.

    Seit E8 beantwortet die Tabelle (protein_catalog.curated_choice) Namen wie
    "Lysozym", "hemoglobin", "trypsin" und "alcohol dehydrogenase" vor jeder
    Quelle — mit dem Laboreintrag (Huhn, Rind, Hefe) statt des menschlichen.
    Die Tests hier prüfen den UniProt-Weg, der für alle übrigen Namen gilt.
    """
    from chemdraw_tool import protein_catalog

    monkeypatch.setattr(protein_catalog, "curated_choice", lambda name: None)


def _protein_lookup(monkeypatch, answers: dict[str, dict | None]) -> list[str]:
    asked: list[str] = []

    def lookup(name):
        asked.append(name)
        return answers.get(name)

    monkeypatch.setattr(resolver, "_protein_lookup", lookup)
    return asked


def test_unknown_protein_name_says_protein_not_not_found(cascade, monkeypatch, no_table):
    record = _record("Lysozym", "lysozym-de", monkeypatch)
    _protein_lookup(monkeypatch, {"Lysozym": record})

    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("Lysozym")

    exc = info.value
    assert exc.kind == "protein"
    message = str(exc)
    assert "'Lysozym' is a protein" in message
    assert "Lysozyme C" in message and "P61626" in message
    assert "Homo sapiens" in message and "148 amino acids" in message
    assert "16.5 kDa" in message
    assert "precursor" in message  # Signalpeptid: reifes Lysozym ist kürzer
    assert 'lookup with topic "biochem"' in message
    assert "nothing was drawn" in message


def test_protein_family_is_named_as_family(cascade, monkeypatch, no_table):
    record = _record("hemoglobin", "hemoglobin", monkeypatch)
    _protein_lookup(monkeypatch, {"hemoglobin": record})

    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("hemoglobin")

    message = str(info.value)
    assert info.value.kind == "protein"
    assert "protein family" in message
    assert "Hemoglobin subunit alpha (UniProt P69905" in message
    assert "Hemoglobin subunit beta" in message


def test_other_entries_under_the_same_name_are_listed(cascade, monkeypatch, no_table):
    record = _record("trypsin", "trypsin", monkeypatch)
    _protein_lookup(monkeypatch, {"trypsin": record})

    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("trypsin")

    message = str(info.value)
    assert "Serine protease 1 (also called Trypsin I; UniProt P07477" in message
    assert "Trypsin-2 (P07478)" in message


def test_antibody_name_gets_an_honest_sentence_without_uniprot(cascade, monkeypatch):
    asked = _protein_lookup(monkeypatch, {})

    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("Trastuzumab")

    assert info.value.kind == "protein"
    message = str(info.value)
    assert "monoclonal antibody" in message
    assert "150 kDa" in message
    assert 'lookup with topic "biochem"' in message
    # Nichts erfunden: keine Zugangsnummer, kein Organismus
    assert "UniProt" not in message
    assert asked == []


def test_unknown_name_without_protein_stays_not_found(cascade, monkeypatch):
    asked = _protein_lookup(monkeypatch, {})

    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("Quatschium")

    assert info.value.kind == "not_found"
    assert asked == ["Quatschium"]


@pytest.mark.parametrize("status, kind", [(resolver._UNREACHABLE, "offline"), (resolver._SOURCE_ERROR, "sources_down")])
def test_no_protein_question_when_sources_did_not_answer(monkeypatch, no_table, status, kind):
    # Offline/gestört ist keine Aussage über den Namen — UniProt bliebe dann
    # das einzige "Wissen" und machte aus einem Netzproblem eine Diagnose.
    resolver.resolve_name.cache_clear()

    def broken(name, report=None):
        resolver._record(report, resolver._PUBCHEM, status, "down")
        return None

    monkeypatch.setattr(resolver, "_opsin_lookup", lambda name: None)
    monkeypatch.setattr(resolver, "_pubchem_lookup", broken)
    monkeypatch.setattr(resolver, "_nci_cir_lookup", broken)
    asked = _protein_lookup(monkeypatch, {"hemoglobin": {"accession": "P69905"}})

    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("hemoglobin")

    assert info.value.kind == kind
    assert asked == []


def test_enzyme_name_is_checked_before_the_structure_sources(cascade, monkeypatch, no_table):
    # "lysozyme" → PubChem CID 91976556, ein Peptidfragment mit Titel
    # "Lysozyme"; "alcohol dehydrogenase" → CID 78120390, ein Acyl-CoA.
    # Beide Titel passen zum Namen, nur der Stoff nicht.
    cascade.hits["alcohol dehydrogenase"] = "CCC(=O)SCCNC(=O)CC"
    record = _record("alcohol dehydrogenase", "alcohol-dehydrogenase", monkeypatch)
    _protein_lookup(monkeypatch, {"alcohol dehydrogenase": record})

    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("alcohol dehydrogenase")

    assert info.value.kind == "protein"
    assert "Alcohol dehydrogenase 1A" in str(info.value)
    assert cascade.calls == []


def test_enzyme_name_unknown_to_uniprot_takes_the_cascade_once(cascade, monkeypatch, no_table):
    asked = _protein_lookup(monkeypatch, {})

    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("Alkoholdehydrogenase")

    assert info.value.kind == "not_found"
    assert asked == ["Alkoholdehydrogenase"]  # nicht ein zweites Mal hinterher


def test_enzyme_check_when_uniprot_is_down_keeps_the_structure(cascade, monkeypatch):
    cascade.hits["urease"] = "NC(N)=O"
    _protein_lookup(monkeypatch, {})
    assert resolver.resolve("urease")[0] == "NC(N)=O"


@pytest.mark.parametrize("name", ["oxytocin", "vasopressin", "Schiff base", "Hünig's base", "caffeine"])
def test_non_enzyme_names_hit_no_uniprot_on_success(cascade, monkeypatch, name):
    cascade.hits[name] = "CCO"
    asked = _protein_lookup(monkeypatch, {name: {"accession": "X"}})
    assert resolver.resolve(name)[0] == "CCO"
    assert asked == []


def test_smiles_and_sequences_never_ask_uniprot(cascade, monkeypatch):
    asked = _protein_lookup(monkeypatch, {})
    resolver.resolve("CC(=O)Oc1ccccc1C(=O)O")
    resolver.resolve("Ala-Gly-Ser")
    resolver.resolve("peptide:AGS")
    assert asked == []


# --- generate_molecule: Größengrenze für Namen ------------------------------
# Gemessen 10.11.2026 an 1000×800-px-Bildern: Palytoxin (186 Schweratome)
# bleibt lesbar, ab Calcitonin (239) und Glucagon (246) fällt die Schrift auf
# RDKits Mindestgröße und Ketten überlagern sich; Insulin (404) ist ein
# Knäuel. Die Grenze liegt in der Lücke: über 200 Schweratome kein Bild.

from chemdraw_tool import server  # noqa: E402

BIG = json.loads((Path(__file__).parent / "__fixtures__" / "proteins" / "smiles.json").read_text())


@pytest.fixture
def drawing(tmp_path, monkeypatch):
    for attr in ("OUTPUT_DIR", "REACTION_DIR", "SPECTRUM_DIR", "TLC_DIR"):
        if hasattr(server, attr):
            monkeypatch.setattr(server, attr, tmp_path / attr.lower())
    monkeypatch.setattr(server, "_enrich_properties", lambda smiles: {})
    resolver.resolve_name.cache_clear()
    yield tmp_path
    resolver.resolve_name.cache_clear()


def _named(monkeypatch, name: str, smiles: str):
    monkeypatch.setattr(
        resolver, "resolve_name_route", lambda n: resolver.Resolution(smiles) if n == name else None
    )


def test_threshold_sits_between_the_measured_structures():
    assert server.MAX_NAMED_HEAVY_ATOMS == 200


@pytest.mark.parametrize("name", ["insulin", "glucagon", "calcitonin"])
def test_named_protein_sized_structure_is_not_drawn(drawing, monkeypatch, name):
    _named(monkeypatch, name, BIG[name])
    with pytest.raises(NameResolutionError) as info:
        server.generate_molecule(name)
    assert info.value.kind == "too_large"
    assert not any(drawing.rglob("*.png"))


def test_too_large_message_says_what_it_is_and_what_helps(drawing, monkeypatch):
    _named(monkeypatch, "insulin", BIG["insulin"])
    with pytest.raises(NameResolutionError) as info:
        server.generate_molecule("insulin")
    message = str(info.value)
    assert "C256H381N65O77S6" in message
    assert "5793.6 g/mol" in message
    assert "404 heavy atoms" in message
    assert "peptide of 51 amino-acid residues" in message
    assert "above 200 heavy atoms" in message
    assert 'lookup with topic "biochem"' in message
    assert "peptide:" in message  # Sequenzschreibweise
    assert "SMILES" in message  # der Weg, es doch zu zeichnen


@pytest.mark.parametrize("name", ["oxytocin", "palytoxin", "bivalirudin"])
def test_named_structures_below_the_limit_are_still_drawn(drawing, monkeypatch, name):
    _named(monkeypatch, name, BIG[name])
    payload = server.generate_molecule(name)
    assert payload.svg


def test_supplied_smiles_is_drawn_even_above_the_limit(drawing):
    # Der Nutzer hat die Struktur selbst geliefert — und die Panel-Knöpfe
    # (Ansichten) rufen generate_molecule mit dem SMILES erneut auf.
    payload = server.generate_molecule(BIG["glucagon"])
    assert payload.svg


def test_twenty_residue_sequence_is_still_drawn(drawing):
    # Die Grenze des Sequenz-Parsers (20 Reste) gilt; 20× Trp = 281 Schweratome.
    payload = server.generate_molecule("peptide:" + "W" * 20)
    assert payload.svg


def test_protein_name_reaches_generate_molecule_as_protein_error(drawing, monkeypatch):
    record = _record("insulin", "insulin", monkeypatch)
    monkeypatch.setattr(resolver, "resolve_name_route", lambda n: (_ for _ in ()).throw(
        resolver._protein_error(n, record)))
    with pytest.raises(NameResolutionError) as info:
        server.generate_molecule("insulin")
    assert info.value.kind == "protein"


# --- lookup(topic="biochem"): UniProt-Datenblatt für Proteinnamen ------------


@pytest.fixture
def biochem_sources(monkeypatch):
    """UniProt-Namenssuche → Fixture; ChEBI und die alte Volltextsuche → leer."""
    calls: list[str] = []

    def install(fixture: str | None, chebi: dict | None = None):
        def fake_get(url, timeout=None, **kwargs):
            calls.append(url)
            if "protein_name" in url:
                return _resp(_fixture(fixture) if fixture else {"results": []})
            if "ols4" in url:
                return _resp(chebi or {"response": {"docs": []}})
            return _resp({"results": []})

        monkeypatch.setattr(databases.requests, "get", fake_get)
        return calls

    return install


def test_biochem_sheet_for_lysozyme(biochem_sources, no_table):
    biochem_sources("lysozyme-details")
    out = server._lookup_biochem("lysozyme")
    assert out.startswith("## lysozyme — Protein (UniProt)")
    assert "- **Name:** Lysozyme C" in out
    assert "- **UniProt:** P61626" in out
    assert "- **Organism:** Homo sapiens" in out
    assert "- **Length:** 148 amino acids" in out
    assert "- **Mass:** 16.5 kDa" in out
    assert "precursor" in out
    assert "- **EC number:** 3.2.1.17" in out
    assert "- **Function:** Lysozymes have primarily a bacteriolytic function;" in out
    assert "- **PDB structures:** 133L, 134L, 1B5U" in out
    assert "https://www.uniprot.org/uniprotkb/P61626" in out
    assert "ChEBI" not in out


def test_biochem_sheet_for_trypsin_names_the_other_trypsins(biochem_sources, no_table):
    biochem_sources("trypsin-details")
    out = server._lookup_biochem("trypsin")
    assert "- **Name:** Serine protease 1 (also called Trypsin I)" in out
    assert "- **UniProt:** P07477" in out
    assert "- **Length:** 247 amino acids" in out
    assert "- **EC number:** 3.4.21.4" in out
    assert "Trypsin-2 (P07478)" in out and "Trypsin-3 (P35030)" in out


def test_biochem_sheet_for_insulin_keeps_function_short(biochem_sources, no_table):
    biochem_sources("insulin-details")
    out = server._lookup_biochem("insulin")
    assert "- **UniProt:** P01308" in out
    assert "- **Length:** 110 amino acids" in out
    assert "- **Mass:** 12.0 kDa" in out
    assert "precursor" in out
    assert "EC number" not in out  # Hormon, kein Enzym
    function = next(line for line in out.splitlines() if line.startswith("- **Function:**"))
    assert function.startswith("- **Function:** Hormone secreted by pancreatic islet beta cells")
    assert "PubMed" not in function
    assert function.count(". ") <= 2


def test_biochem_for_a_small_molecule_is_unchanged(biochem_sources):
    chebi = {"response": {"docs": [{"short_form": "CHEBI_17234", "obo_id": "CHEBI:17234",
                                    "label": "glucose", "description": ["An aldohexose."]}]}}
    biochem_sources("glucose", chebi)
    out = server._lookup_biochem("glucose")
    assert out.startswith("## glucose — Biochemical classification")
    assert "- **ID:** CHEBI:17234" in out
    assert "Protein (UniProt)" not in out


def test_biochem_for_an_antibody_explains_instead_of_listing_unrelated_proteins(biochem_sources):
    chebi = {"response": {"docs": [{"short_form": "CHEBI_231601", "obo_id": "CHEBI:231601",
                                    "label": "trastuzumab",
                                    "description": ["Trastuzumab is a HER2/neu Receptor Antagonist."]}]}}
    calls = biochem_sources(None, chebi)
    out = server._lookup_biochem("trastuzumab")
    assert "HER2/neu Receptor Antagonist" in out
    assert "monoclonal antibody" in out
    # Gemessen: die Volltextsuche lieferte "Protein phosphatase 1H" — falsch.
    assert not any("uniprotkb/search" in c and "protein_name" not in c for c in calls)


def test_antibody_sheet_names_its_fields_and_claims_no_uniprot_entry(biochem_sources):
    """E17: „Organism: therapeutic antibody against HER2“ und „(UniProt)“ im Kopf,
    obwohl es für einen therapeutischen Antikörper keinen UniProt-Eintrag gibt."""
    biochem_sources(None, {"response": {"docs": []}})
    out = server._lookup_biochem("trastuzumab")
    assert out.splitlines()[0] == "## trastuzumab — Antibody"
    assert "UniProt)" not in out.splitlines()[0]
    assert "**Organism:**" not in out
    assert "- **Type:** therapeutic monoclonal antibody" in out
    assert "- **Target:** HER2" in out
    assert "- **Drawn structure:** PDB 1N8Z" in out


def test_generic_antibody_sheet_names_the_example_not_an_organism(biochem_sources):
    biochem_sources(None, {"response": {"docs": []}})
    out = server._lookup_biochem("IgG")
    assert out.splitlines()[0] == "## IgG — Antibody"
    assert "**Organism:**" not in out
    assert "- **Example shown:** human IgG1 b12" in out


def test_batch_generate_says_protein_instead_of_a_bare_failure(drawing, monkeypatch):
    def route(name):
        raise resolver._antibody_error(name, [])

    monkeypatch.setattr(resolver, "resolve_name_route", route)
    result = server.batch_generate(["trastuzumab"])
    assert result.failed == [
        'trastuzumab (protein: no skeletal formula — generate_molecule draws its cartoon)'
    ]


def test_uniprot_protein_ignores_peptide_entries_the_parser_could_draw(monkeypatch):
    # Gemessen: "oxytocin" traf P69043 (Kaninchen, 9 aa) — lookup biochem zeigte
    # dann ein Kaninchen-Datenblatt statt ChEBI. Bis 20 Reste ist es ein Peptid
    # mit Strukturformel, kein Protein ohne.
    rabbit = {
        "results": [
            {
                "primaryAccession": "P69043",
                "organism": {"scientificName": "Oryctolagus cuniculus", "taxonId": 9986},
                "proteinDescription": {"recommendedName": {"fullName": {"value": "Oxytocin"}}},
                "sequence": {"length": 9, "molWeight": 1010},
            }
        ]
    }
    monkeypatch.setattr(databases.requests, "get", Mock(return_value=_resp(rabbit)))
    assert databases.uniprot_protein("oxytocin") is None


def test_antibody_message_promises_no_target_it_may_not_have(cascade, monkeypatch):
    # rituximab hat keinen ChEBI-Eintrag — lookup biochem zeigt dann nur den Satz.
    _protein_lookup(monkeypatch, {})
    with pytest.raises(NameResolutionError) as info:
        resolver.resolve("rituximab")
    assert "target" not in str(info.value)
