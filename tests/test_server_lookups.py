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

from contextlib import contextmanager
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
                "CanonicalSMILES": "CC(=O)OC1=CC=CC=C1C(=O)O",
                "IsomericSMILES": "CC(=O)OC1=CC=CC=C1C(=O)O",
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
    "cpd:C00031\tD-Glucose; Grape sugar; Dextrose\n"
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

    assert out.startswith("## Aspirin — PubChem-Daten")
    assert "| **CID** | 2244 |" in out
    assert "| **IUPAC-Name** | 2-acetyloxybenzoic acid |" in out
    assert "| **Summenformel** | C9H8O4 |" in out
    assert "| **Molmasse** | 180.16 g/mol |" in out
    assert "| **Exakte Masse** | 180.04225873 |" in out
    assert "| **LogP** | 1.2 |" in out
    assert "| **Polare Oberfläche** | 63.6 Å² |" in out
    assert "| **H-Brücken-Donoren** | 1 |" in out
    assert "| **H-Brücken-Akzeptoren** | 4 |" in out
    assert "| **InChIKey** | BSYNRYMUTXBXSQ-UHFFFAOYSA-N |" in out
    assert "| **CAS-Nr.** | 50-78-2 |" in out
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

    syn_line = next(line for line in out.splitlines() if line.startswith("**Synonyme:"))
    names = syn_line.removeprefix("**Synonyme:** ").split(", ")
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

    assert "| **Summenformel** | H2O |" in out
    assert "None" not in out
    for absent in ("IUPAC-Name", "Molmasse", "LogP", "InChIKey", "CAS-Nr.", "Synonyme"):
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

    assert "| **Ladung** | -2 |" in out


def test_lookup_compound_degrades_gracefully_on_api_error():
    """PubChem down (500) → Hinweistext statt Exception, CID bleibt '?'."""
    with http(
        {
            "/property/": _Resp(status=500),
            "/synonyms/": _Resp(status=500),
        }
    ):
        out = lookup_compound("Aspirin")

    assert "Eigenschaften konnten nicht abgerufen werden." in out
    assert "https://pubchem.ncbi.nlm.nih.gov/compound/?" in out


def test_lookup_compound_handles_unknown_substance():
    """PubChem antwortet mit leerer Property-Liste (Substanz unbekannt)."""
    with http(
        {
            "/property/": _Resp(json_data={"PropertyTable": {"Properties": []}}),
            "/synonyms/": _Resp(json_data={"Fault": {"Code": "PUGREST.NotFound"}}),
        }
    ):
        out = lookup_compound("Xyzzyol")

    assert "Eigenschaften konnten nicht abgerufen werden." in out
    assert "Synonyme" not in out


def test_lookup_compound_shows_zero_values():
    """Null ist ein Messwert, keine Leerstelle.

    Benzol hat echt TPSA 0, null H-Brücken-Donoren und null -Akzeptoren. Eine
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

    assert "| **Polare Oberfläche** | 0 Å² |" in out
    assert "| **H-Brücken-Donoren** | 0 |" in out
    assert "| **H-Brücken-Akzeptoren** | 0 |" in out


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

    assert "| **LogP** | 0 |" in out


def test_lookup_compound_keeps_markdown_valid_on_partial_outage():
    """Properties tot, Synonyme leben: die CAS-Zeile darf keine kopflose
    Tabellenzeile hinter den Fehlertext hängen — das rendert als roher Text."""
    with http(
        {
            "/property/": _Resp(status=500),
            "/synonyms/": _Resp(json_data=PUBCHEM_SYNONYMS_ASPIRIN),
        }
    ):
        out = lookup_compound("Aspirin")

    assert "Eigenschaften konnten nicht abgerufen werden." in out
    assert "50-78-2" in out, "die CAS-Nummer ist bekannt und soll nicht verschwinden"
    assert "| **CAS-Nr.** | 50-78-2 |" not in out, (
        "Tabellenzeile ohne Tabellenkopf — muss als normale Zeile ausgegeben werden"
    )


# --- lookup_safety ----------------------------------------------------------


def test_lookup_safety_formats_ghs_table():
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [2244]}}),
            "heading=GHS": _Resp(json_data=PUBCHEM_GHS_ASPIRIN),
        }
    ):
        out = lookup_safety("Aspirin")

    assert out.startswith("## Aspirin — Sicherheitsdaten (GHS)")
    assert "| **Pictogram(s)** | Irritant; Health Hazard |" in out
    assert "| **Signal** | Warning |" in out
    assert "| **GHS Hazard Statements** | H302: Harmful if swallowed |" in out
    # Information ohne "Value" darf keine leere Zeile erzeugen
    assert "ECHA C&L Notifications Summary" not in out
    assert "#section=Safety-and-Hazards" in out
    assert "compound/2244" in out


def test_lookup_safety_reports_unknown_compound():
    with http({"/cids/JSON": _Resp(json_data={"Fault": {"Code": "PUGREST.NotFound"}})}):
        out = lookup_safety("Xyzzyol")

    assert out == "Verbindung 'Xyzzyol' nicht in PubChem gefunden."


def test_lookup_safety_reports_missing_ghs_section():
    """CID existiert, aber PubChem hat keine GHS-Daten (leere Section)."""
    empty = {"Record": {"Section": [{"TOCHeading": "Safety and Hazards"}]}}
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [962]}}),
            "heading=GHS": _Resp(json_data=empty),
        }
    ):
        out = lookup_safety("Wasser")

    assert out == "Keine GHS-Sicherheitsdaten für 'Wasser' in PubChem."


def test_lookup_safety_degrades_on_pug_view_error():
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [2244]}}),
            "heading=GHS": _Resp(status=503),
        }
    ):
        out = lookup_safety("Aspirin")

    assert out == "Keine GHS-Sicherheitsdaten für 'Aspirin' in PubChem."


# --- lookup_physical --------------------------------------------------------


def test_lookup_physical_formats_experimental_properties():
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [2244]}}),
            "heading=Experimental": _Resp(json_data=PUBCHEM_PHYSICAL_ASPIRIN),
        }
    ):
        out = lookup_physical("Aspirin")

    assert out.startswith("## Aspirin — Physikalische Eigenschaften")
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

    assert out == "Verbindung 'Xyzzyol' nicht in PubChem gefunden."


def test_lookup_physical_reports_missing_experimental_data():
    with http(
        {
            "/cids/JSON": _Resp(json_data={"IdentifierList": {"CID": [123]}}),
            "heading=Experimental": _Resp(json_data={"Record": {"Section": []}}),
        }
    ):
        out = lookup_physical("Neustoff")

    assert out == "Keine experimentellen Daten für 'Neustoff' in PubChem."


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
    assert "- **Beschreibung:** An aldohexose used as a source of energy." in out
    assert "chebiId=CHEBI_17234" in out

    assert "### UniProt (Proteine/Enzyme, Mensch)" in out
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

    assert "Kein ChEBI-Eintrag gefunden." in out
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

    assert out.startswith("## Glucose — Biochemische Einordnung")
    assert "Kein ChEBI-Eintrag gefunden." in out
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

    assert out.startswith("## Glucose — KEGG Stoffwechseldaten")
    assert "- **KEGG-ID:** cpd:C00031" in out
    assert "- **Namen:** D-Glucose, Grape sugar, Dextrose, D-Glucopyranose" in out
    assert "- **Formel:** C6H12O6" in out
    assert "### Stoffwechselwege (12)" in out
    assert "- [map00010](https://www.kegg.jp/pathway/map00010)" in out
    # maximal 10 Links, Rest als Zähler
    assert out.count("https://www.kegg.jp/pathway/") == 10
    assert "- ... und 2 weitere" in out
    assert "https://www.kegg.jp/entry/cpd:C00031" in out


def test_lookup_pathway_reports_unknown_compound():
    with http({"/find/compound/": _Resp(text="\n")}):
        out = lookup_pathway("Xyzzyol")

    assert out == "'Xyzzyol' nicht in KEGG gefunden."


def test_lookup_pathway_reports_compound_without_pathways():
    with http(
        {
            "/find/compound/": _Resp(text="cpd:C99999\tTestol\n"),
            "/get/": _Resp(text="ENTRY       C99999\nNAME        Testol\n"),
            "/link/pathway/": _Resp(text="\n"),
        }
    ):
        out = lookup_pathway("Testol")

    assert "Keine Stoffwechselwege verknüpft." in out
    assert "### Stoffwechselwege" not in out
    assert "Formel" not in out  # Feld fehlt in der KEGG-Antwort


def test_lookup_pathway_degrades_on_kegg_error():
    with http({"/find/compound/": _Resp(status=502)}):
        out = lookup_pathway("Glucose")

    assert out == "'Glucose' nicht in KEGG gefunden."


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

    assert "- **KEGG-ID:** cpd:C00031" in out
    assert "### Stoffwechselwege (12)" in out
    assert "Namen" not in out
