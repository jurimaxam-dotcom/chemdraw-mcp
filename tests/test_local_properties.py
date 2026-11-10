"""Formel und Molmasse kommen aus der Struktur, wenn PubChem den Stoff nicht kennt.

Desktop-Handtest 10.11.2026: `Ala-Trp-Lys-Ser-Gly` wird seit dem lokalen
Peptid-Parser gezeichnet, PubChem führt das Peptid aber nicht — das Panel
blieb ohne Formel und Masse.
"""
import chemdraw_tool.server as srv

PENTA = "C[C@H](N)C(=O)N[C@@H](Cc1c[nH]c2ccccc12)C(=O)N[C@@H](CCCCN)C(=O)N[C@@H](CO)C(=O)NCC(=O)O"


def test_formula_and_mass_come_from_the_structure_when_pubchem_has_no_record(monkeypatch):
    monkeypatch.setattr(srv, "_pubchem_record", lambda smiles: ({}, None))
    props = srv._enrich_properties(PENTA)
    assert props["formula"] == "C25H37N7O7"
    assert props["mw"] == "547.61 g/mol"
    # Was nur PubChem weiß, wird nicht erfunden.
    assert "cas" not in props and "cid" not in props and "logP" not in props


def test_pubchem_values_win_when_there_is_a_record(monkeypatch):
    record = {"MolecularFormula": "C9H8O4", "MolecularWeight": "180.16", "CID": 2244}
    monkeypatch.setattr(srv, "_pubchem_record", lambda smiles: (record, "50-78-2"))
    props = srv._enrich_properties("CC(=O)Oc1ccccc1C(=O)O")
    assert props["formula"] == "C9H8O4" and props["mw"] == "180.16 g/mol"
    assert props["cas"] == "50-78-2"


def test_charged_structure_keeps_its_charge_in_the_formula(monkeypatch):
    monkeypatch.setattr(srv, "_pubchem_record", lambda smiles: ({}, None))
    assert srv._enrich_properties("[NH4+]")["formula"] == "H4N+"
