"""Referenzfehler dürfen weder durch Neubau noch durch Metadaten-Caches zurückkehren."""

import argparse
import io
import json
import sys
import urllib.error

import pytest
from rdkit import Chem
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

from scripts import masse_eval


@pytest.mark.parametrize("name,key,qid,chembl,formula", [
    ("fumaric acid", "VZCYOOQTPOCHFL-OWOJBTEDSA-N", "Q139857", "CHEMBL503160", "C4H4O4"),
    ("tenofovir disoproxil", "JFVZFKDSXNQEJW-CQSZACIVSA-N", "Q27132753", "CHEMBL1538", "C19H30N5O10P"),
])
def test_reference_is_the_named_compound(name, key, qid, chembl, formula):
    rows = json.loads(masse_eval.LISTE.read_text())["stoffe"]
    row = next(x for x in rows if x["eingabe"] == name)
    assert row["inchikey"] == key
    assert f"wikidata:{qid}" in row["quelle"]
    assert f"chembl:{chembl}" in row["quelle"]
    mol = Chem.MolFromSmiles(row["smiles_referenz"])
    assert Chem.MolToInchiKey(mol) == key
    assert CalcMolFormula(mol) == row["formel"] == formula


def test_rebuilding_list_keeps_verified_references_despite_bad_source_labels(tmp_path, monkeypatch):
    # Dieselbe Fehlerklasse: ein korrektes Molekülobjekt trägt den falschen Namen.
    wrong = {"keys": {"VNWKTOKETHGBQD-UHFFFAOYSA-N"}, "smiles": {"C"},
             "chembl": set(), "inn": None, "de": None, "gruppe": "Säure/Base",
             "en": "fumaric acid", "suchwort": "fumaric acid"}
    parent = {"keys": {"SGOIRFVFHAKUTI-ZCFIWIBFSA-N"},
              "smiles": {"C[C@H](CN1C=NC2=C1N=CN=C2N)OCP(=O)(O)O"},
              "chembl": {"CHEMBL483"}, "inn": "tenofovir", "de": None,
              "en": "tenofovir disoproxil", "suchwort": None}
    monkeypatch.setattr(masse_eval, "_lehrbuch", lambda: {"Q125026916": wrong})
    monkeypatch.setattr(masse_eval, "_eml", lambda: {"Q155954": parent})
    monkeypatch.setattr(masse_eval, "_chembl_nach_keys", lambda keys: {})
    monkeypatch.setattr(masse_eval, "_chembl_nach_ids", lambda ids: {})
    monkeypatch.setattr(masse_eval, "REPO", tmp_path)
    monkeypatch.setattr(masse_eval, "LISTE", tmp_path / "liste.json")
    curated = tmp_path / "kuratiert.json"
    curated.write_text('{"stoffe": []}')
    monkeypatch.setattr(masse_eval, "KURATIERT", curated)
    assert masse_eval.baue_liste(argparse.Namespace()) == 0
    result = {x["eingabe"]: x for x in json.loads(masse_eval.LISTE.read_text())["stoffe"]}
    assert result["fumaric acid"]["inchikey"] == "VZCYOOQTPOCHFL-OWOJBTEDSA-N"
    assert result["tenofovir disoproxil"]["inchikey"] == "JFVZFKDSXNQEJW-CQSZACIVSA-N"
    assert result["tenofovir"]["inchikey"] == "SGOIRFVFHAKUTI-ZCFIWIBFSA-N"
    assert "notiz" not in result["fumaric acid"]


def test_rebuilding_list_keeps_stereo_reference_corrections(tmp_path, monkeypatch):
    # Wikidata/ChEMBL haben diese Namen mit unvollständiger Stereo verknüpft.
    # Der Builder muss die unabhängig belegten Hauptrecords wieder einsetzen.
    fixture_path = masse_eval.REPO / "tests" / "identity" / "stoffe-masse.json"
    fixture_keys = {
        row["eingabe"]: row["inchikey"]
        for row in json.loads(fixture_path.read_text())["stoffe"]
    }
    records = [
        ("Q422273", "clindamycin", None,
         "KDLRVYVGXIQJDK-NOWPCOIGSA-N",
         "CCC[C@@H]1C[C@H](N(C1)C)C(=O)NC([C@@H]2[C@@H]([C@@H]([C@H]([C@H](O2)SC)O)O)O)C(C)Cl"),
        ("Q105381234", "cocaine", None,
         "ZPUCINDJVBIVPJ-PFSRBDOWSA-N",
         "COC(=O)[C@@H]1C2CCC(C[C@@H]1OC(=O)c1ccccc1)N2C"),
        ("Q179894", "pantothenic acid", "Pantothensäure",
         "GHOKWGTUZJEAQD-UHFFFAOYSA-N",
         "CC(C)(CO)C(C(=O)NCCC(=O)O)O"),
        ("Q27109935", "trehalose", None,
         "HDTRYLNUVZCQOY-MFAKQEFJSA-N",
         "C([C@@H]1[C@H]([C@@H]([C@H](C(O1)OC2[C@@H]([C@H]([C@@H]([C@H](O2)CO)O)O)O)O)O)O)O"),
    ]
    lehr = {}
    for qid, en, de, key, smiles in records:
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None and Chem.MolToInchiKey(mol) == key
        lehr[qid] = {
            "keys": {key}, "smiles": {smiles}, "chembl": set(), "inn": None,
            "de": de, "en": en, "gruppe": "test", "suchwort": en,
        }
    monkeypatch.setattr(masse_eval, "_lehrbuch", lambda: lehr)
    monkeypatch.setattr(masse_eval, "_eml", lambda: {})
    monkeypatch.setattr(masse_eval, "LEHRBUCH", {"test": [row[1] for row in records]})
    monkeypatch.setattr(masse_eval, "_chembl_nach_keys", lambda keys: {})
    monkeypatch.setattr(masse_eval, "_chembl_nach_ids", lambda ids: {})
    monkeypatch.setattr(masse_eval, "REPO", tmp_path)
    monkeypatch.setattr(masse_eval, "LISTE", tmp_path / "liste.json")
    curated = tmp_path / "kuratiert.json"
    curated.write_text('{"stoffe": []}')
    monkeypatch.setattr(masse_eval, "KURATIERT", curated)

    assert masse_eval.baue_liste(argparse.Namespace()) == 0
    result = {x["eingabe"]: x for x in json.loads(masse_eval.LISTE.read_text())["stoffe"]}
    for name in ("clindamycin", "cocaine", "pantothenic acid", "Pantothensäure", "trehalose"):
        assert result[name]["inchikey"] == fixture_keys[name]


@pytest.fixture
def name_cache(tmp_path, monkeypatch):
    cache = tmp_path / "chembl-namen.json"
    monkeypatch.setattr(masse_eval, "CHEMBL_NAMEN_CACHE", cache, raising=False)
    monkeypatch.setattr(masse_eval.time, "sleep", lambda _: None)
    return cache


def _response():
    return io.StringIO(json.dumps({"molecules": [
        {"pref_name": "FUMARIC ACID", "molecule_structures": {"standard_inchi_key": "FOUND"}},
    ]}))


def test_chembl_names_cache_successes_and_confirmed_misses(name_cache, monkeypatch):
    calls = []

    def fetch(request, **kwargs):
        calls.append(request.full_url)
        return _response()

    monkeypatch.setattr(masse_eval.urllib.request, "urlopen", fetch)
    assert masse_eval._chembl_namen(["FOUND", "MISSING"]) == {"FOUND": "fumaric acid"}
    assert masse_eval._chembl_namen(["MISSING", "FOUND", "FOUND"]) == {"FOUND": "fumaric acid"}
    assert len(calls) == 1
    assert name_cache.exists()
    # Auch ein anderer Aufruf darf nur seine angefragten Treffer zurückgeben.
    assert masse_eval._chembl_namen(["MISSING"]) == {}
    assert len(calls) == 1


def test_chembl_names_do_not_cache_outages(name_cache, monkeypatch):
    calls = []

    def fetch(request, **kwargs):
        calls.append(request.full_url)
        if len(calls) == 1:
            raise urllib.error.URLError("offline")
        return _response()

    monkeypatch.setattr(masse_eval.urllib.request, "urlopen", fetch)
    assert masse_eval._chembl_namen(["FOUND"]) == {}
    assert masse_eval._chembl_namen(["FOUND"]) == {"FOUND": "fumaric acid"}
    assert len(calls) == 2


def test_chembl_name_cache_expires_and_can_be_refreshed(name_cache, monkeypatch):
    clock = [1_000_000.0]
    calls = []
    monkeypatch.setattr(masse_eval.time, "time", lambda: clock[0])

    def fetch(request, **kwargs):
        calls.append(request.full_url)
        return _response()

    monkeypatch.setattr(masse_eval.urllib.request, "urlopen", fetch)
    masse_eval._chembl_namen(["FOUND"])
    clock[0] += 8 * 86400
    masse_eval._chembl_namen(["FOUND"])
    assert len(calls) == 2
    masse_eval._chembl_namen(["FOUND"], refresh=True)
    assert len(calls) == 3


def test_corrupt_cache_does_not_break_names(name_cache, monkeypatch):
    name_cache.write_text("not json")
    monkeypatch.setattr(masse_eval.urllib.request, "urlopen", lambda *a, **kw: _response())
    assert masse_eval._chembl_namen(["FOUND"]) == {"FOUND": "fumaric acid"}


def test_report_cli_can_explicitly_refresh_cached_names(monkeypatch):
    args_seen = []
    monkeypatch.setattr(sys, "argv", ["masse_eval.py", "identitaet", "--refresh-names"])
    monkeypatch.setattr(masse_eval, "identitaet_bericht", lambda args: args_seen.append(args) or 0)
    assert masse_eval.main() == 0
    assert args_seen[0].refresh_names is True


@pytest.fixture
def report_with_tautomers(tmp_path, monkeypatch):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    entries = [
        {"eingabe": "correct", "inchikey": "A", "quelle": "wikidata:Q1 + chembl:1"},
        {"eingabe": "tautomer", "inchikey": "B", "quelle": "wikidata:Q2 + chembl:2"},
        {"eingabe": "tautomer alias", "inchikey": "B", "quelle": "wikidata:Q2 + chembl:2"},
        {"eingabe": "uncertain", "inchikey": "C", "quelle": "wikidata:Q3 + chembl:3"},
        # Gleicher Key wie Q1, aber ein weiterer Wikidata-Stoff (cocaine/Kokain).
        {"eingabe": "wrong", "inchikey": "A", "quelle": "wikidata:Q4 + chembl:4"},
        {"eingabe": "ez", "inchikey": "D", "quelle": "wikidata:Q5 + chembl:5"},
        {"eingabe": "ez alias", "inchikey": "D", "quelle": "wikidata:Q5 + chembl:5"},
    ]
    results = [
        {"eingabe": "correct", "status": "gruen", "text": "A"},
        {"eingabe": "tautomer", "status": "gelb", "art": "tautomer", "text": "Tautomer"},
        {"eingabe": "tautomer alias", "status": "gelb", "art": "tautomer", "text": "Tautomer"},
        {"eingabe": "uncertain", "status": "gelb", "text": "Referenz unsicher"},
        {"eingabe": "wrong", "status": "rot", "art": "stereo", "text": "wrong", "erwartet": "A"},
        {"eingabe": "ez", "status": "gelb", "art": "ez_fehlt", "text": "E/Z fehlt"},
        {"eingabe": "ez alias", "status": "gelb", "art": "ez_fehlt", "text": "E/Z fehlt"},
    ]
    for result in results:
        result["sekunden"] = 0.1
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({"stoffe": entries}))
    protocol = tmp_path / "protocol.json"
    protocol.write_text(json.dumps(results))
    monkeypatch.setattr(masse_eval, "REPO", tmp_path)
    monkeypatch.setattr(masse_eval, "LISTE", fixture)
    monkeypatch.setattr(masse_eval, "PROTOKOLL", protocol)
    monkeypatch.setattr(masse_eval, "_nachklassifizieren", lambda *args: None)
    monkeypatch.setattr(masse_eval, "EVIDENZ", evidence)
    monkeypatch.setattr(masse_eval, "_chembl_namen", lambda *args, **kwargs: {})
    assert masse_eval.identitaet_bericht(argparse.Namespace()) == 0
    return (evidence / "identitaet.md").read_text()


def test_identity_report_separates_tautomers_from_green_and_other_yellow(report_with_tautomers):
    assert "1 grün · 1 gelb (Quelle/Referenz) · 2 gelb (Tautomer) · 2 gelb (E/Z fehlt) · 1 rot" in report_with_tautomers
    assert "| Tautomer | 2 |" in report_with_tautomers
    assert "| Quelle/Referenz | 1 |" in report_with_tautomers


def test_identity_report_distinguishes_source_compounds_from_distinct_keys(report_with_tautomers):
    assert "7 Eingaben (5 Wikidata-Stoffe, 4 unterschiedliche InChIKeys)" in report_with_tautomers


def test_report_does_not_count_missing_ez_as_green_or_source_yellow(report_with_tautomers):
    assert "| E/Z fehlt | 2 |" in report_with_tautomers
    assert "1 grün · 1 gelb (Quelle/Referenz)" in report_with_tautomers


@pytest.mark.parametrize("confirmed_correction", [False, True])
def test_rebuilding_list_keeps_vinblastine_uncertain_after_corrections(
    tmp_path, monkeypatch, confirmed_correction,
):
    fixture = json.loads(masse_eval.LISTE.read_text())["stoffe"]
    reference = next(row for row in fixture if row["eingabe"] == "vinblastine")
    key = reference["inchikey"]
    source = {
        "keys": {key}, "smiles": {reference["smiles_referenz"]},
        "chembl": {"CHEMBL22969"}, "inn": None, "de": "Vinblastin",
        "en": "vinblastine", "suchwort": "vinblastine", "gruppe": "test",
    }
    monkeypatch.setattr(masse_eval, "_lehrbuch", lambda: {"Q282629": source})
    monkeypatch.setattr(masse_eval, "_eml", lambda: {})
    monkeypatch.setattr(masse_eval, "LEHRBUCH", {"test": ["vinblastine"]})
    monkeypatch.setattr(masse_eval, "_chembl_nach_keys", lambda keys: {key: "CHEMBL22969"})
    monkeypatch.setattr(masse_eval, "_chembl_nach_ids", lambda ids: {})
    if confirmed_correction:
        # Selbst der Zweig, der unsicher/notiz entfernt, darf den Entscheid nicht verlieren.
        monkeypatch.setitem(masse_eval.REFERENZ_KORREKTUREN, "vinblastine", {
            field: reference[field]
            for field in ("inchikey", "formel", "quelle", "smiles_referenz")
        })
    monkeypatch.setattr(masse_eval, "REPO", tmp_path)
    monkeypatch.setattr(masse_eval, "LISTE", tmp_path / "liste.json")
    curated = tmp_path / "kuratiert.json"
    curated.write_text('{"stoffe": []}')
    monkeypatch.setattr(masse_eval, "KURATIERT", curated)
    assert masse_eval.baue_liste(argparse.Namespace()) == 0
    rows = json.loads(masse_eval.LISTE.read_text())["stoffe"]
    assert {row["eingabe"] for row in rows} == {"vinblastine", "Vinblastin"}
    for row in rows:
        assert row["inchikey"] == key
        assert row.get("unsicher") is True
        assert row.get("notiz") == reference["notiz"]
