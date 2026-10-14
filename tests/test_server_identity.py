"""Woher die Zahlen stammen, muss am Panel stehen.

Das Panel zeigt CAS, XLogP und TPSA woertlich aus PubChem. Falsch wird das
nicht durch einen falschen Zahlenwert, sondern durch einen falsch aufgeloesten
Namen: dann ist alles darunter konsistent falsch. Der Datensatz, den PubChem
zurueckgibt, ist die einzige Stelle, an der das sichtbar werden kann — und er
kostet keine zusaetzliche Anfrage.
"""

import pytest

from chemdraw_tool import databases, server

_SMILES = "COC(=O)C(C1CCCCN1)C2=CC=CC=C2"


def test_smiles_property_query_asks_for_the_record_title():
    assert "Title" in databases._PUBCHEM_SMILES_PROPS_URL


def _fake_pubchem(monkeypatch, props, cas="113-45-1"):
    """Beide Wege stillegen — sonst greift der Test ans echte Netz."""
    monkeypatch.setattr(server, "pubchem_properties_by_inchikey", lambda key: props)
    monkeypatch.setattr(server, "pubchem_synonyms_by_inchikey", lambda key: (cas, []))
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


# --- Der Datensatz muss der Stammdatensatz sein ---------------------------
# Gemessen am 12.09.2026: Auf das Metformin-SMILES antwortet PubChem mit
# CID 152743144 ("[14C]metformin") — obwohl CID 4091 dieselbe Struktur, denselben
# InChIKey und dasselbe SMILES fuehrt. Ergebnis im Panel: keine CAS, dafuer ein
# radioaktiver Name. Ueber den InChIKey steht der Stammdatensatz an erster Stelle.


def test_lookup_goes_by_inchikey_first(monkeypatch):
    gefragt = {}

    def per_key(key):
        gefragt["key"] = key
        return {"CID": 4091, "Title": "Metformin"}

    def per_smiles(smiles):  # darf gar nicht erst drankommen
        gefragt["smiles"] = smiles
        return {"CID": 152743144, "Title": "[14C]metformin"}

    monkeypatch.setattr(server, "pubchem_properties_by_inchikey", per_key)
    monkeypatch.setattr(server, "pubchem_properties_by_smiles", per_smiles)
    monkeypatch.setattr(server, "pubchem_synonyms_by_inchikey", lambda k: ("657-24-9", []))
    monkeypatch.setattr(server, "pubchem_synonyms_by_smiles", lambda s: (None, []))

    props = server._enrich_properties("CN(C)C(=N)N=C(N)N")

    assert gefragt["key"] == "XZWYZXLIPXDOLR-UHFFFAOYSA-N"
    assert "smiles" not in gefragt, "SMILES-Weg trotz InChIKey-Treffer"
    assert props["pubchemTitle"] == "Metformin"
    assert props["cas"] == "657-24-9"


def test_lookup_falls_back_to_smiles_when_the_key_is_unknown(monkeypatch):
    """Kennt PubChem den InChIKey nicht, ist der SMILES-Weg besser als nichts."""
    monkeypatch.setattr(server, "pubchem_properties_by_inchikey", lambda k: None)
    monkeypatch.setattr(
        server, "pubchem_properties_by_smiles", lambda s: {"Title": "Irgendwas", "CID": 7}
    )
    monkeypatch.setattr(server, "pubchem_synonyms_by_inchikey", lambda k: (None, []))
    monkeypatch.setattr(server, "pubchem_synonyms_by_smiles", lambda s: ("1-2-3", []))

    props = server._enrich_properties("CCO")

    assert props["pubchemTitle"] == "Irgendwas"
    assert props["cas"] == "1-2-3"


def test_unparsable_input_skips_the_key_route(monkeypatch):
    """Ohne Molekuel kein InChIKey — dann direkt ueber SMILES, ohne Absturz."""
    monkeypatch.setattr(
        server,
        "pubchem_properties_by_inchikey",
        lambda k: pytest.fail("InChIKey-Weg ohne Molekuel"),
    )
    monkeypatch.setattr(server, "pubchem_properties_by_smiles", lambda s: {"Title": "X"})
    monkeypatch.setattr(server, "pubchem_synonyms_by_smiles", lambda s: (None, []))

    assert server._enrich_properties("kein_smiles")["pubchemTitle"] == "X"


def test_inchikey_endpoints_exist():
    assert "/inchikey/" in databases._PUBCHEM_INCHIKEY_PROPS_URL
    assert "/inchikey/" in databases._PUBCHEM_INCHIKEY_SYNONYMS_URL


# --- Der Daten-Knopf im Panel (gemessen 01.10.2026) -------------------------
# PubChem liefert kein "CanonicalSMILES" mehr (heute "SMILES" /
# "ConnectivitySMILES"). Damit fehlte properties.smiles, MoleculeView fragte das
# Datenblatt mit dem Anzeigenamen ("Methylphenidat") an — resolve() scheiterte.
# Und selbst mit SMILES ging lookup_molecule_data per NAME zu PubChem, wo ein
# SMILES mit 404 beantwortet wird.


def test_payload_smiles_survives_a_pubchem_answer_without_canonical_smiles(monkeypatch):
    _fake_pubchem(monkeypatch, {"CID": 4158, "Title": "Methylphenidate"})
    props = server._enrich_properties(_SMILES)
    assert props["smiles"] == _SMILES


def test_data_sheet_goes_by_structure_not_by_name(monkeypatch):
    _fake_pubchem(
        monkeypatch,
        {"CID": 4158, "Title": "Methylphenidate", "InChIKey": "DUGOZIWVEXMGBE-UHFFFAOYSA-N"},
    )

    def per_name(name):
        raise AssertionError(f"Namensweg mit {name!r} — das Panel schickt ein SMILES")

    monkeypatch.setattr(server, "pubchem_properties", per_name)
    monkeypatch.setattr(server, "pubchem_synonyms", per_name)
    monkeypatch.setattr(server, "pubchem_safety", lambda cid: [])

    sheet = server.lookup_molecule_data(_SMILES)

    rows = {r.key: r.val for r in sheet.sources[0].rows}
    assert rows["CID"] == "4158"
    assert rows["CAS-Nr."] == "113-45-1"


# --- PubChem-Feldnamen (live geprueft 14.10.2026) ----------------------------
# Wer heute "CanonicalSMILES,IsomericSMILES" anfragt, bekommt die Schluessel
# "ConnectivitySMILES" und "SMILES" zurueck. Die alten Namen in der URL sind
# Altlast; die Lesestelle auf "CanonicalSMILES" lief immer ins Leere.


@pytest.mark.parametrize(
    "url",
    [
        databases._PUBCHEM_PROPS_URL,
        databases._PUBCHEM_SMILES_PROPS_URL,
        databases._PUBCHEM_INCHIKEY_PROPS_URL,
    ],
)
def test_property_urls_ask_for_current_pubchem_field_names(url):
    assert "CanonicalSMILES" not in url
    assert "IsomericSMILES" not in url
    assert ",SMILES," in url


def test_payload_smiles_is_the_drawn_structure_not_pubchems(monkeypatch):
    """Das Datenblatt fragt mit properties.smiles an — es muss die gezeichnete
    Struktur sein. Ein abweichender PubChem-Datensatz (SMILES-Rueckfallweg,
    z. B. ein Isotopolog) darf sie nicht ersetzen."""
    _fake_pubchem(
        monkeypatch,
        {"CID": 1, "Title": "Anderes", "SMILES": "C", "ConnectivitySMILES": "C"},
    )
    assert server._enrich_properties(_SMILES)["smiles"] == _SMILES


def test_zero_valued_properties_are_kept(monkeypatch):
    """XLogP 0, TPSA 0, 0 Donoren/Akzeptoren sind Messwerte, keine Luecken."""
    _fake_pubchem(
        monkeypatch,
        {
            "CID": 297,
            "MolecularWeight": "16.04",
            "XLogP": 0,
            "TPSA": 0,
            "HBondDonorCount": 0,
            "HBondAcceptorCount": 0,
        },
    )
    props = server._enrich_properties("C")
    assert props["logP"] == "0"
    assert props["tpsa"] == "0 Å²"
    assert props["hbd"] == "0"
    assert props["hba"] == "0"
