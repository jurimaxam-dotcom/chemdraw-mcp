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
