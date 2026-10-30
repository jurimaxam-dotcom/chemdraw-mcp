"""Charakterisierende Tests für die fünf Text-`lookup_*`-Tools in server.py.

Diese Tools parsen fremde, versionierte JSON-/Textstrukturen (PubChem PUG +
PUG-View, ChEBI/OLS4, KEGG, UniProt) und formatieren sie zu Markdown. Getestet
wird die GESAMTE Kette: eingefrorene, realistische API-Antwort → databases.py →
Markdown-Ausgabe des Tools. Ändert sich das Parsing oder die Formatierung,
wird der Test rot, statt dass ein Nutzer eine leere Antwort bekommt.

Kein Netz: `requests.get`/`.post` sind global gesperrt (Fixture `_no_network`),
jeder Test erlaubt genau die URLs, die er erwartet — unerwartete URLs landen in
`router.unmatched` und werden geprüft (die databases-Funktionen schlucken
Exceptions, ein blosses `raise` bliebe unsichtbar).
"""

import json
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from chemdraw_tool.server import lookup


# Seit dem Bündeln (15.08.2026) gibt es nach außen nur noch `lookup(name, topic)`.
# Die Tests rufen weiter pro Thema auf — über diese Weichen, damit jeder Test
# zusätzlich den Dispatch mitprüft, statt an den privaten Helfern vorbeizulaufen.
def lookup_compound(name):
    return lookup(name, topic="properties")


def lookup_safety(name):
    return lookup(name, topic="safety")


def lookup_physical(name):
    return lookup(name, topic="physical")


def lookup_biochem(name):
    return lookup(name, topic="biochem")


def lookup_pathway(name):
    return lookup(name, topic="pathway")

# --- HTTP-Attrappe ----------------------------------------------------------


class _Resp:
    """Minimaler requests.Response-Ersatz."""

    def __init__(self, *, json_data=None, text=None, status=200):
        self._json = json_data
        self.text = text if text is not None else ""
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")

    def json(self):
        if self._json is None:
            raise ValueError("Antwort enthält kein JSON")
        return self._json


class _Router:
    """Bildet URL-Fragmente auf eingefrorene Antworten ab."""

    def __init__(self, routes: dict):
        self.routes = routes
        self.calls: list[str] = []
        self.unmatched: list[str] = []

    def __call__(self, url, *args, **kwargs):
        self.calls.append(url)
        for fragment, resp in self.routes.items():
            if fragment in url:
                if isinstance(resp, Exception):
                    raise resp
                return resp
        self.unmatched.append(url)
        return _Resp(status=404)


@contextmanager
def http(routes: dict):
    router = _Router(routes)
    with (
        patch("chemdraw_tool.databases.requests.get", router),
        patch("chemdraw_tool.databases.requests.post", router),
    ):
        yield router
    assert not router.unmatched, f"Unerwartete HTTP-Aufrufe: {router.unmatched}"


@pytest.fixture(autouse=True)
def _no_network():
    """Sperrt echte Netz-Aufrufe für den Fall, dass ein Test das Patchen vergisst."""

    def _blocked(url, *args, **kwargs):
        raise AssertionError(f"Ungemockter Netz-Aufruf: {url}")

    with (
        patch("chemdraw_tool.databases.requests.get", _blocked),
        patch("chemdraw_tool.databases.requests.post", _blocked),
    ):
        yield


# --- Eingefrorene API-Antworten ---------------------------------------------

# PubChem PUG: /compound/name/aspirin/property/.../JSON
PUBCHEM_PROPS_ASPIRIN = {
    "PropertyTable": {
        "Properties": [
            {
                "CID": 2244,
                "MolecularFormula": "C9H8O4",
                "MolecularWeight": "180.16",
                "IUPACName": "2-acetyloxybenzoic acid",
                "ExactMass": "180.04225873",
                "Charge": 0,
                "XLogP": 1.2,
                "TPSA": 63.6,
                "HBondDonorCount": 1,
                "HBondAcceptorCount": 4,
                "ConnectivitySMILES": "CC(=O)OC1=CC=CC=C1C(=O)O",
                "SMILES": "CC(=O)OC1=CC=CC=C1C(=O)O",
                "InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
            }
        ]
    }
}

# PubChem PUG: /compound/name/aspirin/synonyms/JSON
PUBCHEM_SYNONYMS_ASPIRIN = {
    "InformationList": {
        "Information": [
            {
                "CID": 2244,
                "Synonym": [
                    "aspirin",
                    "ACETYLSALICYLIC ACID",
                    "50-78-2",
                    "2-Acetoxybenzoic acid",
                    "Acetylsalicylsäure",
                    "Acetysal",
                    "Easprin",
                    "Ecotrin",
                ],
            }
        ]
    }
}

# PubChem PUG-View: ?heading=GHS+Classification
PUBCHEM_GHS_ASPIRIN = {
    "Record": {
        "RecordType": "CID",
        "RecordNumber": 2244,
        "RecordTitle": "Aspirin",
        "Section": [
            {
                "TOCHeading": "Safety and Hazards",
                "Section": [
                    {
                        "TOCHeading": "Hazards Identification",
                        "Section": [
                            {
                                "TOCHeading": "GHS Classification",
                                "Information": [
                                    {
                                        "Name": "Pictogram(s)",
                                        "Value": {
                                            "StringWithMarkup": [
                                                {"String": "Irritant; Health Hazard"}
                                            ]
                                        },
                                    },
                                    {
                                        "Name": "Signal",
                                        "Value": {
                                            "StringWithMarkup": [{"String": "Warning"}]
                                        },
                                    },
                                    {
                                        "Name": "GHS Hazard Statements",
                                        "Value": {
                                            "StringWithMarkup": [
                                                {"String": "H302: Harmful if swallowed"}
                                            ]
                                        },
                                    },
                                    {
                                        # kommt in echten Antworten vor: Eintrag
                                        # ohne "Value" — darf nicht durchrutschen
                                        "Name": "ECHA C&L Notifications Summary",
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }
}

# PubChem PUG-View: ?heading=Experimental+Properties
PUBCHEM_PHYSICAL_ASPIRIN = {
    "Record": {
        "RecordType": "CID",
        "RecordNumber": 2244,
        "Section": [
            {
                "TOCHeading": "Chemical and Physical Properties",
                "Section": [
                    {
                        "TOCHeading": "Experimental Properties",
                        "Section": [
                            {
                                "TOCHeading": "Melting Point",
                                "Information": [
                                    {
                                        "Name": "Melting Point",
                                        "Value": {
                                            "StringWithMarkup": [{"String": "135 °C"}]
                                        },
                                    },
                                    {
                                        # zweite Quelle, gleicher Name —
                                        # die Ausgabe dedupliziert nach Name
                                        "Name": "Melting Point",
                                        "Value": {
                                            "StringWithMarkup": [
                                                {"String": "275 °F (NTP, 1992)"}
                                            ]
                                        },
                                    },
                                ],
                            },
                            {
                                "TOCHeading": "Density",
                                "Information": [
                                    {
                                        "Name": "Density",
                                        "Value": {"Number": [1.4], "Unit": "g/cu cm"},
                                    }
                                ],
                            },
                            {
                                "TOCHeading": "Solubility",
                                "Information": [
                                    {
                                        "Name": "Solubility",
                                        "Value": {
                                            "StringWithMarkup": [
                                                {"String": "In water, 4.6 mg/mL"}
                                            ]
                                        },
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }
        ],
    }
}

# OLS4/ChEBI: /api/search?q=...&ontology=chebi
CHEBI_GLUCOSE = {
    "response": {
        "numFound": 3,
        "docs": [
            {
                "id": "chebi:class:http://purl.obolibrary.org/obo/CHEBI_17234",
                "short_form": "CHEBI_17234",
                "obo_id": "CHEBI:17234",
                "label": "glucose",
                "description": ["An aldohexose used as a source of energy."],
                "ontology_name": "chebi",
            },
            {"short_form": "CHEBI_4167", "obo_id": "CHEBI:4167", "label": "D-glucose"},
        ],
    }
}

# UniProt: /uniprotkb/search?query=...&format=json
UNIPROT_HEXOKINASE = {
    "results": [
        {
            "primaryAccession": "P19367",
            "proteinDescription": {
                "recommendedName": {
                    "fullName": {"value": "Hexokinase-1"},
                    "ecNumbers": [{"value": "2.7.1.1"}],
                }
            },
            "genes": [{"geneName": {"value": "HK1"}}],
            "organism": {"scientificName": "Homo sapiens"},
        },
        {
            "primaryAccession": "P52789",
            "proteinDescription": {
                "recommendedName": {
                    "fullName": {"value": "Hexokinase-2"},
                    "ecNumbers": [{"value": "2.7.1.1"}],
                }
            },
            "genes": [{"geneName": {"value": "HK2"}}],
            "organism": {"scientificName": "Homo sapiens"},
        },
        {
            "primaryAccession": "P52790",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Hexokinase-3"}}
            },
            "genes": [{"geneName": {"value": "HK3"}}],
            "organism": {"scientificName": "Homo sapiens"},
        },
        {
            "primaryAccession": "P35557",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Hexokinase-4"}}
            },
            "genes": [{"geneName": {"value": "GCK"}}],
            "organism": {"scientificName": "Homo sapiens"},
        },
    ]
}

# KEGG REST (Plaintext)
KEGG_FIND_GLUCOSE = (
    # Wie die echte KEGG-Antwort: C00031 führt „Glucose" wörtlich
    "cpd:C00031\tD-Glucose; Grape sugar; Dextrose; Glucose; D-Glucopyranose\n"
    "cpd:C00267\talpha-D-Glucose; alpha-D-Glucopyranose\n"
)
KEGG_GET_C00031 = (
    "ENTRY       C00031                      Compound\n"
    "NAME        D-Glucose;\n"
    "            Grape sugar;\n"
    "            Dextrose;\n"
    "            D-Glucopyranose\n"
    "FORMULA     C6H12O6\n"
    "EXACT_MASS  180.0634\n"
    "MOL_WEIGHT  180.1559\n"
    "REACTION    R00010 R00027 R00028\n"
    "///\n"
)
KEGG_PATHWAYS_C00031 = "".join(
    f"cpd:C00031\tpath:map{n:05d}\n" for n in (10, 20, 30, 40, 51, 52, 500, 520, 562)
) + "".join(f"cpd:C00031\tpath:hsa{n:05d}\n" for n in (10, 500, 520))


# --- lookup_compound --------------------------------------------------------


def test_lookup_compound_formats_full_pubchem_table():
    with http(
        {
            "/property/": _Resp(json_data=PUBCHEM_PROPS_ASPIRIN),
            "/synonyms/": _Resp(json_data=PUBCHEM_SYNONYMS_ASPIRIN),
        }
    ):
        out = lookup_compound("Aspirin")

    assert out.startswith("## Aspirin — PubChem data")
    assert "| **CID** | 2244 |" in out
    assert "| **IUPAC name** | 2-acetyloxybenzoic acid |" in out
    assert "| **Molecular formula** | C9H8O4 |" in out
    assert "| **Molecular weight** | 180.16 g/mol |" in out
    assert "| **Exact mass** | 180.04225873 |" in out
    assert "| **XLogP** | 1.2 |" in out
    assert "| **Polar surface area** | 63.6 Å² |" in out
    assert "| **H-bond donors** | 1 |" in out
    assert "| **H-bond acceptors** | 4 |" in out
    assert "| **InChIKey** | BSYNRYMUTXBXSQ-UHFFFAOYSA-N |" in out
    assert "| **CAS No.** | 50-78-2 |" in out
    # Ladung 0 ist der Normalfall und wird bewusst nicht gezeigt
    assert "Ladung" not in out
    assert "https://pubchem.ncbi.nlm.nih.gov/compound/2244" in out


def test_lookup_compound_synonyms_exclude_query_name_and_cap_at_five():
    with http(
        {
            "/property/": _Resp(json_data=PUBCHEM_PROPS_ASPIRIN),
            "/synonyms/": _Resp(json_data=PUBCHEM_SYNONYMS_ASPIRIN),
        }
    ):
        out = lookup_compound("Aspirin")

    syn_line = next(line for line in out.splitlines() if line.startswith("**Synonyms:"))
    names = syn_line.removeprefix("**Synonyms:** ").split(", ")
    assert len(names) == 5
    assert "aspirin" not in [n.lower() for n in names]  # Suchname raus
    assert "50-78-2" not in names  # CAS steht in der Tabelle
    assert names[0] == "ACETYLSALICYLIC ACID"


def test_lookup_compound_omits_rows_for_missing_fields():
    """Fehlt ein Feld in der PubChem-Antwort, fehlt die Zeile — kein 'None'."""
    sparse = {
        "PropertyTable": {"Properties": [{"CID": 962, "MolecularFormula": "H2O"}]}
    }
    with http(
        {
            "/property/": _Resp(json_data=sparse),
            "/synonyms/": _Resp(json_data={"InformationList": {"Information": [{}]}}),
        }
    ):
        out = lookup_compound("Wasser")

    assert "| **Molecular formula** | H2O |" in out
    assert "None" not in out
    for absent in ("IUPAC name", "Molecular weight", "XLogP", "InChIKey", "CAS No.", "Synonyms"):
        assert absent not in out


def test_lookup_compound_shows_charge_for_ions():
    charged = {"PropertyTable": {"Properties": [{"CID": 1038, "Charge": -2}]}}
    with http(
        {
            "/property/": _Resp(json_data=charged),
            "/synonyms/": _Resp(json_data={"InformationList": {"Information": [{}]}}),
        }
    ):
        out = lookup_compound("Sulfat")

    assert "| **Charge** | -2 |" in out


def test_lookup_compound_degrades_gracefully_on_api_error():
    """PubChem down (500) → Hinweistext statt Exception, und kein Link ins Leere
    (früher „/compound/?" — Messung 30.10.2026)."""
    with http(
        {
            "/property/": _Resp(status=500),
            "/synonyms/": _Resp(status=500),
        }
    ):
        out = lookup_compound("Aspirin")

    assert "Properties could not be retrieved from PubChem." in out
    assert "https://pubchem.ncbi.nlm.nih.gov/compound/?" not in out


def test_lookup_compound_handles_unknown_substance():
    """PubChem antwortet mit leerer Property-Liste (Substanz unbekannt)."""
    with http(
        {
            "/property/": _Resp(json_data={"PropertyTable": {"Properties": []}}),
            "/synonyms/": _Resp(json_data={"Fault": {"Code": "PUGREST.NotFound"}}),
        }
    ):
        out = lookup_compound("Xyzzyol")

    assert "Properties could not be retrieved from PubChem." in out
    assert "Synonyms" not in out


def test_lookup_compound_shows_zero_values():
    """Null ist ein Messwert, keine Leerstelle.

    Benzol hat echt TPSA 0, null H-bond donors und null -Akzeptoren. Eine
    Wahrheitsprüfung (`if v := ...`) verschluckt genau diese Zeilen und der
    Nutzer hält die Angabe für unbekannt statt für null.
    """
    benzene = {
        "PropertyTable": {
            "Properties": [
                {
                    "CID": 241,
                    "MolecularFormula": "C6H6",
                    "TPSA": 0,
                    "HBondDonorCount": 0,
                    "HBondAcceptorCount": 0,
                }
            ]
        }
    }
    with http(
        {
            "/property/": _Resp(json_data=benzene),
            "/synonyms/": _Resp(json_data={"InformationList": {"Information": [{}]}}),
        }
    ):
        out = lookup_compound("Benzol")

    assert "| **Polar surface area** | 0 Å² |" in out
    assert "| **H-bond donors** | 0 |" in out
    assert "| **H-bond acceptors** | 0 |" in out


def test_lookup_compound_shows_logp_of_zero():
    """LogP 0 bedeutet 'verteilt sich gleich' — eine Aussage, kein fehlender Wert."""
    with http(
        {
            "/property/": _Resp(
                json_data={"PropertyTable": {"Properties": [{"CID": 1, "XLogP": 0}]}}
            ),
            "/synonyms/": _Resp(json_data={"InformationList": {"Information": [{}]}}),
        }
    ):
        out = lookup_compound("Testolin")

    assert "| **XLogP** | 0 |" in out


def test_lookup_compound_keeps_markdown_valid_on_partial_outage():
    """Properties tot, Synonyms leben: die CAS-Zeile darf keine kopflose
    Tabellenzeile hinter den Fehlertext hängen — das rendert als roher Text."""
    with http(
        {
            "/property/": _Resp(status=500),
            "/synonyms/": _Resp(json_data=PUBCHEM_SYNONYMS_ASPIRIN),
        }
    ):
        out = lookup_compound("Aspirin")

    assert "Properties could not be retrieved from PubChem." in out
    assert "50-78-2" in out, "die CAS-Nummer ist bekannt und soll nicht verschwinden"
    assert "| **CAS No.** | 50-78-2 |" not in out, (
        "Tabellenzeile ohne Tabellenkopf — muss als normale Zeile ausgegeben werden"
    )


# --- lookup_safety ----------------------------------------------------------
#
# Seit Etappe 5 (26.10.2026) nach Quelle getrennt, gegen echte, eingefrorene
# PUG-View-Antworten (Koffein, Natriumchlorid als Negativ-Fixture).

_FIXTURES = Path(__file__).parent / "__fixtures__"


def _ghs_json(name):
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _safety(name, cid, ghs_resp):
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [cid]}}),
            "heading=GHS": ghs_resp,
        }
    ):
        return lookup_safety(name)


def test_lookup_safety_caffeine_lead_source_first():
    out = _safety("Caffeine", 2519, _Resp(json_data=_ghs_json("pubchem_ghs_2519_caffeine.json")))

    assert out.startswith("## Caffeine — GHS classification (PubChem CID 2519)")
    lead = out.index("**Lead source:** EU harmonised")
    assert lead < out.index("ECHA") < out.index("NITE-CMC")
    lead_block = out[lead : out.index("**Other sources")]
    assert "Signal word: Warning" in lead_block
    assert "H302: Harmful if swallowed" in lead_block
    assert "%" not in lead_block, "die EU-Verordnung nennt keinen Anteil"
    assert "Pictograms: Irritant" in lead_block
    assert "P-codes: P264, P270, P301+P317, P330, P501" in lead_block
    assert "Danger" not in lead_block
    others = out[out.index("**Other sources") :]
    assert "H302 98.9%" in others and "not classified 0.6%" in others
    assert "Danger · H301, H332, H360" in others
    assert "#section=Safety-and-Hazards" in out


def test_lookup_safety_nacl_never_leads_with_the_mislinked_entry():
    out = _safety(
        "Sodium chloride", 5234,
        _Resp(json_data=_ghs_json("pubchem_ghs_5234_sodium_chloride.json")),
    )

    lead = out.index("**Lead source:** ECHA")
    lead_block = out[lead : out.index("**Other sources")]
    assert "Not classified: 89.2% of all reports (1840 of 2063)" in lead_block
    assert lead_block.index("Not classified") < lead_block.index("H319")
    assert "H318" not in lead_block and "Danger" not in lead_block
    assert out.index("record name differs: product-by-process") < out.index("H318")


def test_lookup_safety_without_references_still_reads():
    """Synthetische Antwort ohne Reference-Liste: kein Absturz, keine Leitquelle."""
    out = _safety("Aspirin", 2244, _Resp(json_data=PUBCHEM_GHS_ASPIRIN))
    assert "Warning" in out and "H302" in out
    assert "**Lead source:**" not in out
    assert "record name missing" in out


def test_lookup_safety_reports_unknown_compound():
    with http({"/cids/JSON": _Resp(json_data={"Fault": {"Code": "PUGREST.NotFound"}})}):
        out = lookup_safety("Xyzzyol")

    assert out == "Compound 'Xyzzyol' not found in PubChem."


@pytest.mark.parametrize(
    "resp",
    [
        _Resp(status=404),
        _Resp(json_data={"Record": {"Section": [{"TOCHeading": "Safety and Hazards"}]}}),
    ],
)
def test_lookup_safety_reports_missing_ghs_data(resp):
    """CID existiert, PubChem hat keine GHS-Daten — das ist nicht „not classified“."""
    out = _safety("Water", 962, resp)
    assert "no GHS classification" in out
    assert "not the same as" in out


def test_lookup_safety_failure_is_not_reported_as_no_data():
    out = _safety("Aspirin", 2244, _Resp(status=503))
    assert "could not be retrieved" in out
    assert "no GHS classification" not in out


# --- lookup_physical --------------------------------------------------------


def test_lookup_physical_formats_experimental_properties():
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [2244]}}),
            "heading=Experimental": _Resp(json_data=PUBCHEM_PHYSICAL_ASPIRIN),
        }
    ):
        out = lookup_physical("Aspirin")

    assert out.startswith("## Aspirin — Physical properties")
    assert "| **Melting Point** | 135 °C |" in out
    assert "| **Density** | 1.4 g/cu cm |" in out
    assert "| **Solubility** | In water, 4.6 mg/mL |" in out
    assert "#section=Experimental-Properties" in out


def test_lookup_physical_deduplicates_repeated_property_names():
    """PubChem liefert dieselbe Größe aus mehreren Quellen — nur die erste zählt."""
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [2244]}}),
            "heading=Experimental": _Resp(json_data=PUBCHEM_PHYSICAL_ASPIRIN),
        }
    ):
        out = lookup_physical("Aspirin")

    assert out.count("| **Melting Point** |") == 1
    assert "275 °F" not in out


def test_lookup_physical_reports_unknown_compound():
    with http({"/cids/JSON": _Resp(status=404)}):
        out = lookup_physical("Xyzzyol")

    assert out == "Compound 'Xyzzyol' not found in PubChem."


def test_lookup_physical_reports_missing_experimental_data():
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [123]}}),
            "heading=Experimental": _Resp(json_data={"Record": {"Section": []}}),
        }
    ):
        out = lookup_physical("Neustoff")

    assert out == "No experimental data for 'Neustoff' in PubChem."


# --- lookup_biochem ---------------------------------------------------------


def test_lookup_biochem_formats_chebi_and_uniprot():
    with http(
        {
            "ols4/api/search": _Resp(json_data=CHEBI_GLUCOSE),
            "uniprotkb/search": _Resp(json_data=UNIPROT_HEXOKINASE),
        }
    ):
        out = lookup_biochem("Glucose")

    assert "### ChEBI" in out
    assert "- **ID:** CHEBI:17234" in out
    assert "- **Name:** glucose" in out
    assert "- **Description:** An aldohexose used as a source of energy." in out
    assert "chebiId=CHEBI_17234" in out

    assert "### UniProt (proteins/enzymes, human)" in out
    assert "- **Hexokinase-1** (P19367)" in out
    assert "  - Gene: HK1" in out
    assert "  - EC: 2.7.1.1" in out
    assert "https://www.uniprot.org/uniprotkb/P19367" in out
    # nur die ersten drei Treffer werden gezeigt
    assert "Hexokinase-3" in out
    assert "Hexokinase-4" not in out
    assert "P35557" not in out


def test_lookup_biochem_without_chebi_hit_still_lists_proteins():
    with http(
        {
            "ols4/api/search": _Resp(json_data={"response": {"docs": []}}),
            "uniprotkb/search": _Resp(json_data=UNIPROT_HEXOKINASE),
        }
    ):
        out = lookup_biochem("Hexokinase")

    assert "No ChEBI entry found." in out
    assert "### ChEBI" not in out
    assert "- **Hexokinase-1** (P19367)" in out


def test_lookup_biochem_handles_chebi_entry_without_description():
    no_desc = {
        "response": {
            "docs": [
                {
                    "short_form": "CHEBI_4167",
                    "obo_id": "CHEBI:4167",
                    "label": "D-glucose",
                }
            ]
        }
    }
    with http(
        {
            "ols4/api/search": _Resp(json_data=no_desc),
            "uniprotkb/search": _Resp(json_data={"results": []}),
        }
    ):
        out = lookup_biochem("D-Glucose")

    assert "- **Name:** D-glucose" in out
    assert "Beschreibung" not in out
    assert "### UniProt" not in out


def test_lookup_biochem_degrades_when_both_apis_fail():
    with http(
        {
            "ols4/api/search": _Resp(status=500),
            "uniprotkb/search": requests.ConnectionError("no route to host"),
        }
    ):
        out = lookup_biochem("Glucose")

    assert out.startswith("## Glucose — Biochemical classification")
    assert "No ChEBI entry found." in out
    assert "UniProt" not in out


# --- lookup_pathway ---------------------------------------------------------


def test_lookup_pathway_formats_kegg_entry_and_pathways():
    with http(
        {
            "/find/compound/": _Resp(text=KEGG_FIND_GLUCOSE),
            "/get/": _Resp(text=KEGG_GET_C00031),
            "/link/pathway/": _Resp(text=KEGG_PATHWAYS_C00031),
        }
    ):
        out = lookup_pathway("Glucose")

    assert out.startswith("## Glucose — KEGG metabolic data")
    assert "- **KEGG ID:** cpd:C00031" in out
    assert "- **Names:** D-Glucose, Grape sugar, Dextrose, D-Glucopyranose" in out
    assert "- **Formula:** C6H12O6" in out
    assert "### Metabolic pathways (12)" in out
    assert "- [map00010](https://www.kegg.jp/pathway/map00010)" in out
    # maximal 10 Links, Rest als Zähler
    assert out.count("https://www.kegg.jp/pathway/") == 10
    assert "- ... and 2 more" in out
    assert "https://www.kegg.jp/entry/cpd:C00031" in out


def test_lookup_pathway_reports_unknown_compound():
    with http({"/find/compound/": _Resp(text="\n")}):
        out = lookup_pathway("Xyzzyol")

    assert out == "'Xyzzyol' not found in KEGG."


def test_lookup_pathway_reports_compound_without_pathways():
    with http(
        {
            "/find/compound/": _Resp(text="cpd:C99999\tTestol\n"),
            "/get/": _Resp(text="ENTRY       C99999\nNAME        Testol\n"),
            "/link/pathway/": _Resp(text="\n"),
        }
    ):
        out = lookup_pathway("Testol")

    assert "No metabolic pathways linked." in out
    assert "### Metabolic pathways" not in out
    assert "Formula" not in out  # Feld fehlt in der KEGG-Antwort


def test_lookup_pathway_degrades_on_kegg_error():
    with http({"/find/compound/": _Resp(status=502)}):
        out = lookup_pathway("Glucose")

    assert out == "'Glucose' not found in KEGG."


def test_lookup_pathway_survives_broken_entry_fetch():
    """find liefert eine ID, /get fällt aus → Tool bleibt antwortfähig."""
    with http(
        {
            "/find/compound/": _Resp(text=KEGG_FIND_GLUCOSE),
            "/get/": _Resp(status=500),
            "/link/pathway/": _Resp(text=KEGG_PATHWAYS_C00031),
        }
    ):
        out = lookup_pathway("Glucose")

    assert "- **KEGG ID:** cpd:C00031" in out
    assert "### Metabolic pathways (12)" in out
    assert "Names" not in out


# --- Befunde aus dem echten Aufruf 30.10.2026 (Basis-Ausbau Welle 1) ----------


def test_lookup_pathway_takes_the_exact_name_not_the_first_fuzzy_hit():
    """KEGG sortiert „glucose" mit UDP-glucose (C00029) vorn; das war die Antwort —
    ein anderer Stoff mit eigener Formel und eigenen Wegen."""
    find = (
        "cpd:C00029\tUDP-glucose; UDPglucose; UDP-D-glucose\n"
        "cpd:C00031\tD-Glucose; Grape sugar; Dextrose; Glucose; D-Glucopyranose\n"
    )
    with http(
        {
            "/find/compound/": _Resp(text=find),
            "/get/": _Resp(text=KEGG_GET_C00031),
            "/link/pathway/": _Resp(text=KEGG_PATHWAYS_C00031),
        }
    ):
        out = lookup_pathway("glucose")
    assert "- **KEGG ID:** cpd:C00031" in out


def test_lookup_pathway_without_exact_name_says_so_instead_of_guessing():
    with http({"/find/compound/": _Resp(text="cpd:C00029\tUDP-glucose; UDPglucose\n")}):
        out = lookup_pathway("glucose")
    assert out == "'glucose' not found in KEGG."


def test_lookup_physical_skips_rows_without_a_property_name():
    """PubChem liefert Werte ohne Überschrift; daraus wurde die Zeile „| **** | … |"."""
    data = {"Record": {"Section": [{"TOCHeading": "Experimental Properties", "Section": [
        {"TOCHeading": "", "Information": [{"Value": {"StringWithMarkup": [{"String": "white crystals"}]}}]},
        {"TOCHeading": "Melting Point", "Information": [{"Value": {"StringWithMarkup": [{"String": "235 °C"}]}}]},
    ]}]}}
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [2519]}}),
            "heading=Experimental": _Resp(json_data=data),
        }
    ):
        out = lookup_physical("caffeine")
    assert "| **** |" not in out
    assert "| **Melting Point** | 235 °C |" in out


def test_lookup_compound_without_cid_has_no_broken_source_link():
    """Properties tot → früher „PubChem CID ?" mit Link auf /compound/?."""
    with http(
        {
            "/property/": _Resp(status=503),
            "/synonyms/": _Resp(json_data={"InformationList": {"Information": [
                {"Synonym": ["caffeine", "58-08-2"]}]}}),
        }
    ):
        out = lookup_compound("caffeine")
    assert "CID ?" not in out and "/compound/?" not in out
