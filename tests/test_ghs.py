"""GHS nach Quelle getrennt (Etappe 5, 26.10.2026).

Vorher: `_walk_sections` machte aus der GHS-Antwort eine flache Liste — bei
Koffein 18 Zeilen mit vier Signalwörtern ohne Herkunft, jeweils nur der erste
H-Satz einer Quelle. Hier wird gegen zwei eingefrorene, echte PUG-View-Antworten
geprüft (heute geholt, `heading=GHS+Classification`):

- Koffein (CID 2519): vier Quellen — EU-harmonisiert, ECHA-Aggregat, NITE-CMC
  (Japan, Danger/H301/H360), HCIS (Australien).
- Natriumchlorid (CID 5234): die Negativ-Fixture. PubChem hängt einen
  EU-Eintrag an, dessen Stoffname „product-by-process definition
  polyazodyestuff …“ lautet — falsch verknüpft. Würde er Leitquelle, zeigte das
  Panel für Kochsalz Danger/H318.

Kein Netz: `requests.get` wird gepatcht, wo überhaupt geholt wird.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from chemdraw_tool import databases

FIXTURES = Path(__file__).parent / "__fixtures__"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def caffeine() -> dict:
    return _load("pubchem_ghs_2519_caffeine.json")


@pytest.fixture
def nacl() -> dict:
    return _load("pubchem_ghs_5234_sodium_chloride.json")


def _by_ref(sources: list[dict]) -> dict:
    return {s["ref"]: s for s in sources}


# --- Parser: Gruppierung je ReferenceNumber ---------------------------------


def test_caffeine_groups_into_four_sources_in_record_order(caffeine):
    parsed = databases.parse_ghs(caffeine)
    assert parsed["record_title"] == "Caffeine"
    assert [s["ref"] for s in parsed["sources"]] == [272, 51, 262, 65]


def test_reference_metadata_survives(caffeine):
    src = _by_ref(databases.parse_ghs(caffeine)["sources"])
    assert "1272/2008" in src[272]["source_name"]
    assert src[272]["record_name"] == "caffeine"
    assert src[51]["record_name"] == "Caffeine (EC: 200-362-1)"
    assert src[51]["source_name"] == "European Chemicals Agency (ECHA)"
    assert src[272]["url"] == "https://eur-lex.europa.eu/eli/reg/2008/1272/oj"


def test_every_hazard_statement_is_kept_not_only_the_first(caffeine):
    """NITE-CMC meldet drei H-Sätze in EINEM Information-Eintrag."""
    nite = _by_ref(databases.parse_ghs(caffeine)["sources"])[262]
    assert [h["code"] for h in nite["hazards"]] == ["H301", "H332", "H360"]
    assert nite["signal"] == "Danger"
    assert nite["hazards"][0]["text"] == "Toxic if swallowed"


def test_percent_is_read_where_given_and_never_invented(caffeine):
    src = _by_ref(databases.parse_ghs(caffeine)["sources"])
    assert src[51]["hazards"] == [
        {"code": "H302", "percent": 98.9, "text": "Harmful if swallowed"}
    ]
    # EU-Verordnung nennt keinen Anteil — dann gibt es auch keinen.
    assert src[272]["hazards"][0]["percent"] is None


def test_pictograms_come_from_markup_not_from_the_blank_string(caffeine):
    src = _by_ref(databases.parse_ghs(caffeine)["sources"])
    assert src[272]["pictograms"] == ["Irritant"]
    assert src[262]["pictograms"] == ["Acute Toxic", "Irritant", "Health Hazard"]


def test_p_codes_are_a_clean_list(caffeine):
    eu = _by_ref(databases.parse_ghs(caffeine)["sources"])[272]
    assert eu["p_codes"] == ["P264", "P270", "P301+P317", "P330", "P501"]


def test_not_classified_share_is_its_own_finding(caffeine, nacl):
    echa_caf = _by_ref(databases.parse_ghs(caffeine)["sources"])[51]
    assert echa_caf["not_classified"] == {"percent": 0.6, "reports": 13, "total": 2217}
    assert echa_caf["reports_total"] == 2217

    echa_nacl = _by_ref(databases.parse_ghs(nacl)["sources"])[52]
    assert echa_nacl["not_classified"] == {"percent": 89.2, "reports": 1840, "total": 2063}
    assert echa_nacl["hazards"] == [
        {"code": "H319", "percent": 10.8, "text": "Causes serious eye irritation"}
    ]


def test_sources_without_note_have_no_not_classified_claim(caffeine):
    eu = _by_ref(databases.parse_ghs(caffeine)["sources"])[272]
    assert eu["not_classified"] is None


def test_hazards_sorted_by_percent_descending():
    data = {
        "Record": {
            "RecordTitle": "X",
            "Section": [{"Information": [
                {"ReferenceNumber": 1, "Name": "GHS Hazard Statements", "Value": {
                    "StringWithMarkup": [
                        {"String": "H315 (12.5%): Causes skin irritation [Warning Skin]"},
                        {"String": "H300+H310 (80%): Fatal if swallowed or in contact with skin"},
                        {"String": "H360Df (40.1%): May damage the unborn child"},
                    ]}},
            ]}],
            "Reference": [{"ReferenceNumber": 1, "SourceName": "European Chemicals Agency (ECHA)", "Name": "X (EC: 1)"}],
        }
    }
    src = databases.parse_ghs(data)["sources"][0]
    assert [h["code"] for h in src["hazards"]] == ["H300+H310", "H360Df", "H315"]
    assert [h["percent"] for h in src["hazards"]] == [80.0, 40.1, 12.5]


def test_plain_not_classified_statement_without_percent():
    """Manche Quellen schreiben nur „Not Classified“ — ohne Anteil, also kein 0 %."""
    data = {"Record": {"RecordTitle": "Y", "Section": [{"Information": [
        {"ReferenceNumber": 3, "Name": "GHS Hazard Statements",
         "Value": {"StringWithMarkup": [{"String": "Not Classified"}]}},
    ]}], "Reference": [{"ReferenceNumber": 3, "SourceName": "S", "Name": "Y"}]}}
    src = databases.parse_ghs(data)["sources"][0]
    assert src["hazards"] == []
    assert src["not_classified"] == {"percent": None, "reports": None, "total": None}


def test_missing_reference_list_does_not_crash():
    data = {"Record": {"Section": [{"Information": [
        {"Name": "Signal", "Value": {"StringWithMarkup": [{"String": "Warning"}]}},
    ]}]}}
    sources = databases.parse_ghs(data)["sources"]
    assert len(sources) == 1
    assert sources[0]["signal"] == "Warning"
    assert sources[0]["record_name"] == ""


# --- Leitquelle -------------------------------------------------------------


def test_caffeine_lead_is_eu_harmonised_and_all_names_match(caffeine):
    parsed = databases.parse_ghs(caffeine)
    ordered = databases.order_ghs_sources(parsed["sources"], [parsed["record_title"]])
    assert [s["ref"] for s in ordered] == [272, 51, 262, 65]
    assert [s["lead"] for s in ordered] == [True, False, False, False]
    # „caffeine - FY2008 (…)“ von NITE ist derselbe Stoff, kein Fehlbezug.
    assert all(s["name_matches"] for s in ordered)
    assert all(s["note"] == "" for s in ordered)


def test_nacl_mislinked_eu_entry_never_leads(nacl):
    parsed = databases.parse_ghs(nacl)
    ordered = databases.order_ghs_sources(parsed["sources"], [parsed["record_title"]])
    assert [s["ref"] for s in ordered] == [52, 97], "ECHA vorn, Fehlbezug ans Ende"
    assert ordered[0]["lead"] is True
    assert ordered[1]["lead"] is False
    assert ordered[1]["name_matches"] is False
    assert ordered[1]["note"].startswith("record name differs: product-by-process")


def test_falls_back_to_echa_then_first_match():
    srcs = [
        {"ref": 1, "source_name": "NITE-CMC", "record_name": "foo"},
        {"ref": 2, "source_name": "European Chemicals Agency (ECHA)", "record_name": "Foo (EC: 1)"},
    ]
    assert databases.order_ghs_sources(srcs, ["Foo"])[0]["ref"] == 2
    only_nite = databases.order_ghs_sources(srcs[:1], ["foo"])
    assert only_nite[0]["lead"] is True


def test_no_lead_when_no_name_matches():
    srcs = [
        {"ref": 1, "source_name": "Regulation (EC) No 1272/2008", "record_name": "bar"},
        {"ref": 2, "source_name": "X", "record_name": ""},
    ]
    ordered = databases.order_ghs_sources(srcs, ["foo"])
    assert not any(s["lead"] for s in ordered)
    assert ordered[0]["note"] == "record name differs: bar"
    assert ordered[1]["note"] == "record name missing"


# --- Abruf: drei verschiedene Ausgänge --------------------------------------


class _Resp:
    def __init__(self, *, json_data=None, status=200):
        self._json = json_data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error", response=self)

    def json(self):
        return self._json


def test_fetch_ok(caffeine):
    with patch("chemdraw_tool.databases.requests.get", return_value=_Resp(json_data=caffeine)):
        res = databases.pubchem_ghs(2519)
    assert res["status"] == "ok"
    assert len(res["sources"]) == 4


def test_fetch_404_means_no_ghs_data_not_failure():
    with patch("chemdraw_tool.databases.requests.get", return_value=_Resp(status=404)):
        res = databases.pubchem_ghs(962)
    assert res == {"status": "empty", "record_title": "", "sources": []}


def test_fetch_empty_section_means_no_ghs_data():
    empty = {"Record": {"RecordTitle": "Water", "Section": [{"TOCHeading": "Safety and Hazards"}]}}
    with patch("chemdraw_tool.databases.requests.get", return_value=_Resp(json_data=empty)):
        res = databases.pubchem_ghs(962)
    assert res["status"] == "empty"


@pytest.mark.parametrize("effect", [Exception("boom"), requests.ConnectionError("down")])
def test_fetch_error_is_reported_not_swallowed(effect):
    with patch("chemdraw_tool.databases.requests.get", side_effect=effect):
        res = databases.pubchem_ghs(2519)
    assert res["status"] == "error"


def test_fetch_503_is_error():
    with patch("chemdraw_tool.databases.requests.get", return_value=_Resp(status=503)):
        assert databases.pubchem_ghs(2519)["status"] == "error"
