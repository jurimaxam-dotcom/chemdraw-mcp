"""„found as": generate_molecule und lookup_molecule_data nennen den Umweg.

Folgepunkt aus dem Masse-Eval (06.11.2026): Löst der Resolver einen Namen über
eine andere Schreibweise auf (deutsche Regel, Transliteration, Variante,
Salzform), steht diese Schreibweise im Payload — für Panel und Modell. Der
Resolver ist gepatcht, kein Netz.
"""

from unittest.mock import patch

import pytest
from rdkit import Chem

from chemdraw_tool import server as srv
from chemdraw_tool.payloads import DatabasePayload, MoleculePayload
from chemdraw_tool.resolver import Resolved

DEXA = "CC1CC2C3CCC4=CC(=O)C=CC4(C3(C(CC2(C1(C(=O)CO)O)C)O)F)C"


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    for const in ("OUTPUT_DIR", "REACTION_DIR", "PLOT_DIR", "ANKI_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())
    monkeypatch.setattr(srv, "_enrich_properties", lambda smiles: {})
    monkeypatch.setattr(srv, "_pubchem_record", lambda smiles: ({}, None))


def _route(found_as):
    return lambda text: Resolved(DEXA, Chem.MolFromSmiles(DEXA), found_as)


def test_generate_molecule_says_what_the_name_was_found_as(monkeypatch):
    monkeypatch.setattr(srv, "resolve", _route("Dexamethasone"))
    payload = srv.generate_molecule("Dexamethason")
    assert payload.foundAs == "Dexamethasone"


def test_literal_hit_leaves_found_as_empty(monkeypatch):
    monkeypatch.setattr(srv, "resolve", _route(""))
    assert srv.generate_molecule("Dexamethasone").foundAs == ""


@patch("chemdraw_tool.server.pubchem_ghs",
       return_value={"status": "empty", "record_title": "", "sources": []})
def test_lookup_molecule_data_says_it_too(_ghs, monkeypatch):
    monkeypatch.setattr(srv, "resolve", _route("Dexamethasone"))
    payload = srv.lookup_molecule_data("Dexamethason")
    assert isinstance(payload, DatabasePayload)
    assert payload.foundAs == "Dexamethasone"


def test_both_panel_payloads_have_the_field():
    assert MoleculePayload.model_fields["foundAs"].default == ""
    assert DatabasePayload.model_fields["foundAs"].default == ""


def test_batch_generate_carries_found_as_per_molecule(monkeypatch):
    """batch_generate liefert dieselben MoleculePayloads — das Feld steht im
    Schema, also muss es auch dort gefüllt sein."""
    routes = {"Dexamethason": "Dexamethasone", "Dexamethasone": ""}
    monkeypatch.setattr(
        srv, "resolve", lambda text: Resolved(DEXA, Chem.MolFromSmiles(DEXA), routes[text])
    )
    result = srv.batch_generate(["Dexamethason", "Dexamethasone"])
    assert [m.foundAs for m in result.molecules] == ["Dexamethasone", ""]


def test_plain_tuple_from_a_stand_in_means_no_hint(monkeypatch):
    """Bestehende Attrappen liefern (smiles, mol) — das bleibt gültig."""
    monkeypatch.setattr(srv, "resolve", lambda text: (DEXA, Chem.MolFromSmiles(DEXA)))
    assert srv.generate_molecule("Dexamethason").foundAs == ""
