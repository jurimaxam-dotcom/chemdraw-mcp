"""Woher die Zahlen stammen, muss am Panel stehen.

Das Panel zeigt CAS, XLogP und TPSA woertlich aus PubChem. Falsch wird das
nicht durch einen falschen Zahlenwert, sondern durch einen falsch aufgeloesten
Namen: dann ist alles darunter konsistent falsch. Der Datensatz, den PubChem
zurueckgibt, ist die einzige Stelle, an der das sichtbar werden kann — und er
kostet keine zusaetzliche Anfrage.
"""

from chemdraw_tool import databases, server

_SMILES = "COC(=O)C(C1CCCCN1)C2=CC=CC=C2"


def test_smiles_property_query_asks_for_the_record_title():
    assert "Title" in databases._PUBCHEM_SMILES_PROPS_URL


def _fake_pubchem(monkeypatch, props, cas="113-45-1"):
    monkeypatch.setattr(server, "pubchem_properties_by_smiles", lambda smiles: props)
    monkeypatch.setattr(server, "pubchem_synonyms_by_smiles", lambda smiles: (cas, []))


def test_enrich_properties_names_the_pubchem_record(monkeypatch):
    _fake_pubchem(
        monkeypatch,
        {
            "CID": 4158,
            "Title": "Methylphenidate",
            "MolecularFormula": "C14H19NO2",
            "MolecularWeight": "233.31",
            "XLogP": 0.2,
        },
    )
    props = server._enrich_properties(_SMILES)
    assert props["pubchemTitle"] == "Methylphenidate"
    assert props["cid"] == "4158"


def test_enrich_properties_stays_silent_without_a_record(monkeypatch):
    _fake_pubchem(monkeypatch, None, cas=None)
    props = server._enrich_properties("CCO")
    assert "pubchemTitle" not in props
    assert "cid" not in props
