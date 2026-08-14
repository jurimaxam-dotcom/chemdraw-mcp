"""Charakterisierende Tests für databases.py.

Alle Netzwerk-Calls sind gemockt — kein Live-Treffer gegen PubChem/KEGG/ChEBI/
UniProt. Schwerpunkt: (1) die bewusste "Netzwerkfehler → leere/None-Rückgabe
statt Exception"-Garantie und (2) die reine Parse-Logik (CAS-Regex,
_walk_sections, KEGG-Textfelder), die ohne Tests am ehesten still bricht.
"""

from unittest.mock import Mock, patch

from chemdraw_tool import databases


def _resp(json_data=None, text=None):
    m = Mock()
    m.raise_for_status = Mock()
    if json_data is not None:
        m.json = Mock(return_value=json_data)
    if text is not None:
        m.text = text
    return m


# --- _get_cid ---------------------------------------------------------------


def test_get_cid_returns_first_cid():
    with patch(
        "chemdraw_tool.databases.requests.get",
        return_value=_resp({"IdentifierList": {"CID": [2244, 999]}}),
    ):
        assert databases._get_cid("aspirin") == 2244


def test_get_cid_returns_none_on_network_error():
    with patch(
        "chemdraw_tool.databases.requests.get", side_effect=Exception("network down")
    ):
        assert databases._get_cid("aspirin") is None


def test_get_cid_returns_none_on_malformed_json():
    with patch(
        "chemdraw_tool.databases.requests.get", return_value=_resp({"unexpected": {}})
    ):
        assert databases._get_cid("aspirin") is None


# --- pubchem_properties -----------------------------------------------------


def test_pubchem_properties_returns_first_property_dict():
    payload = {"PropertyTable": {"Properties": [{"MolecularFormula": "C9H8O4"}]}}
    with patch("chemdraw_tool.databases.requests.get", return_value=_resp(payload)):
        assert databases.pubchem_properties("aspirin") == {"MolecularFormula": "C9H8O4"}


def test_pubchem_properties_returns_none_when_empty():
    with patch(
        "chemdraw_tool.databases.requests.get",
        return_value=_resp({"PropertyTable": {"Properties": []}}),
    ):
        assert databases.pubchem_properties("nope") is None


def test_pubchem_properties_returns_none_on_error():
    with patch(
        "chemdraw_tool.databases.requests.get", side_effect=Exception("timeout")
    ):
        assert databases.pubchem_properties("aspirin") is None


def test_pubchem_properties_by_smiles_uses_post():
    payload = {"PropertyTable": {"Properties": [{"InChIKey": "ABC"}]}}
    with patch(
        "chemdraw_tool.databases.requests.post", return_value=_resp(payload)
    ) as mock_post:
        result = databases.pubchem_properties_by_smiles("CC(=O)O")
    assert result == {"InChIKey": "ABC"}
    mock_post.assert_called_once()


# --- pubchem_synonyms (CAS-Extraktion) --------------------------------------


def test_pubchem_synonyms_extracts_cas_number():
    payload = {
        "InformationList": {
            "Information": [{"Synonym": ["aspirin", "50-78-2", "acetylsalicylic acid"]}]
        }
    }
    with patch("chemdraw_tool.databases.requests.get", return_value=_resp(payload)):
        cas, others = databases.pubchem_synonyms("aspirin")
    assert cas == "50-78-2"
    assert "50-78-2" not in others


def test_pubchem_synonyms_cas_none_when_no_match():
    payload = {"InformationList": {"Information": [{"Synonym": ["aspirin", "ASA"]}]}}
    with patch("chemdraw_tool.databases.requests.get", return_value=_resp(payload)):
        cas, others = databases.pubchem_synonyms("aspirin")
    assert cas is None
    assert "aspirin" in others


def test_pubchem_synonyms_returns_empty_on_error():
    with patch(
        "chemdraw_tool.databases.requests.get", side_effect=Exception("boom")
    ):
        assert databases.pubchem_synonyms("aspirin") == (None, [])


# --- _walk_sections (reine Parse-Logik, kein Netz) --------------------------


def test_walk_sections_extracts_string_and_number_values():
    section = {
        "TOCHeading": "Props",
        "Information": [
            {"Name": "Signal", "Value": {"StringWithMarkup": [{"String": "Danger"}]}},
            {"Name": "pKa", "Value": {"Number": [3.5], "Unit": ""}},
        ],
    }
    results = []
    databases._walk_sections(section, results)
    assert {"name": "Signal", "value": "Danger"} in results
    assert {"name": "pKa", "value": "3.5"} in results


def test_walk_sections_recurses_into_nested_sections():
    section = {
        "Section": [
            {
                "Information": [
                    {"Name": "Deep", "Value": {"StringWithMarkup": [{"String": "x"}]}}
                ]
            }
        ]
    }
    results = []
    databases._walk_sections(section, results)
    assert {"name": "Deep", "value": "x"} in results


def test_walk_sections_number_with_unit():
    section = {
        "Information": [
            {"Name": "MP", "Value": {"Number": [135], "Unit": "°C"}},
        ]
    }
    results = []
    databases._walk_sections(section, results)
    assert {"name": "MP", "value": "135 °C"} in results


def test_walk_sections_skips_information_without_value():
    section = {"Information": [{"Name": "Empty"}]}
    results = []
    databases._walk_sections(section, results)
    assert results == []


# --- pubchem_safety / pubchem_physical_properties ---------------------------


def test_pubchem_safety_returns_empty_on_error():
    with patch(
        "chemdraw_tool.databases.requests.get", side_effect=Exception("503")
    ):
        assert databases.pubchem_safety(2244) == []


def test_pubchem_physical_properties_returns_empty_on_error():
    with patch(
        "chemdraw_tool.databases.requests.get", side_effect=Exception("503")
    ):
        assert databases.pubchem_physical_properties(2244) == []


# --- ChEBI ------------------------------------------------------------------


def test_chebi_lookup_maps_first_doc():
    payload = {
        "response": {
            "docs": [
                {
                    "short_form": "CHEBI_15377",
                    "label": "water",
                    "description": ["a thing"],
                    "obo_id": "CHEBI:15377",
                }
            ]
        }
    }
    with patch("chemdraw_tool.databases.requests.get", return_value=_resp(payload)):
        result = databases.chebi_lookup("water")
    assert result["id"] == "CHEBI_15377"
    assert result["label"] == "water"
    assert result["description"] == "a thing"


def test_chebi_lookup_returns_none_when_no_docs():
    with patch(
        "chemdraw_tool.databases.requests.get",
        return_value=_resp({"response": {"docs": []}}),
    ):
        assert databases.chebi_lookup("xyzzy") is None


def test_chebi_lookup_returns_none_on_error():
    with patch(
        "chemdraw_tool.databases.requests.get", side_effect=Exception("down")
    ):
        assert databases.chebi_lookup("water") is None


# --- KEGG (Textfeld-Parsing) ------------------------------------------------


def test_kegg_find_returns_first_id():
    text = "cpd:C00031\tD-Glucose; Grape sugar\ncpd:C00267\talpha-D-Glucose\n"
    with patch("chemdraw_tool.databases.requests.get", return_value=_resp(text=text)):
        assert databases.kegg_find("glucose") == "cpd:C00031"


def test_kegg_find_returns_none_on_error():
    with patch(
        "chemdraw_tool.databases.requests.get", side_effect=Exception("down")
    ):
        assert databases.kegg_find("glucose") is None


def test_kegg_compound_parses_names_formula_and_pathways():
    get_text = (
        "ENTRY       C00031                      Compound\n"
        "NAME        D-Glucose;\n"
        "            Grape sugar\n"
        "FORMULA     C6H12O6\n"
    )
    pathway_text = "cpd:C00031\tpath:map00010\ncpd:C00031\tpath:map00500\n"
    with patch(
        "chemdraw_tool.databases.requests.get",
        side_effect=[_resp(text=get_text), _resp(text=pathway_text)],
    ):
        result = databases.kegg_compound("cpd:C00031")
    assert "D-Glucose" in result["names"]
    assert "Grape sugar" in result["names"]
    assert result["formula"] == "C6H12O6"
    assert result["pathways"] == ["path:map00010", "path:map00500"]


def test_kegg_compound_formula_does_not_leak_into_names():
    """Regression guard: an indented line *after* FORMULA must not be swallowed
    as a NAME continuation. Without the current_field reset on FORMULA, the
    indented '180.06 g/mol' line would be appended to names."""
    get_text = "NAME        Foo;\nFORMULA     C6H12O6\n            180.06 g/mol\n"
    with patch(
        "chemdraw_tool.databases.requests.get",
        side_effect=[_resp(text=get_text), _resp(text="")],
    ):
        result = databases.kegg_compound("cpd:C00031")
    assert result["formula"] == "C6H12O6"
    assert result["names"] == ["Foo"]


# --- UniProt ----------------------------------------------------------------


def test_uniprot_search_maps_entries():
    payload = {
        "results": [
            {
                "primaryAccession": "P00533",
                "proteinDescription": {
                    "recommendedName": {
                        "fullName": {"value": "Epidermal growth factor receptor"},
                        "ecNumbers": [{"value": "2.7.10.1"}],
                    }
                },
                "genes": [{"geneName": {"value": "EGFR"}}],
                "organism": {"scientificName": "Homo sapiens"},
            }
        ]
    }
    with patch("chemdraw_tool.databases.requests.get", return_value=_resp(payload)):
        results = databases.uniprot_search("EGFR")
    assert len(results) == 1
    entry = results[0]
    assert entry["accession"] == "P00533"
    assert entry["genes"] == ["EGFR"]
    assert entry["ec"] == ["2.7.10.1"]
    assert entry["organism"] == "Homo sapiens"


def test_uniprot_search_returns_empty_on_error():
    with patch(
        "chemdraw_tool.databases.requests.get", side_effect=Exception("down")
    ):
        assert databases.uniprot_search("EGFR") == []


# --- Timeouts ---------------------------------------------------------------
# Ein einziger Sekundenwert lässt einen NICHT erreichbaren Host volle 10 s
# hängen; in Panel-Tools werden mehrere Calls verkettet → der Server wirkt
# eingefroren. (connect, read) trennt "Host antwortet gar nicht" (3 s) von
# "Host rechnet lange" (10 s).


def test_timeout_is_connect_read_tuple():
    assert databases._TIMEOUT == (3, 10)


def test_get_cid_passes_split_timeout():
    with patch(
        "chemdraw_tool.databases.requests.get",
        return_value=_resp({"IdentifierList": {"CID": [2244]}}),
    ) as mock_get:
        databases._get_cid("aspirin")
    assert mock_get.call_args.kwargs["timeout"] == (3, 10)


def test_pubchem_properties_passes_split_timeout():
    payload = {"PropertyTable": {"Properties": [{"MolecularFormula": "C9H8O4"}]}}
    with patch(
        "chemdraw_tool.databases.requests.get", return_value=_resp(payload)
    ) as mock_get:
        databases.pubchem_properties("aspirin")
    assert mock_get.call_args.kwargs["timeout"] == (3, 10)


def test_pubchem_properties_by_smiles_passes_split_timeout():
    payload = {"PropertyTable": {"Properties": [{"InChIKey": "ABC"}]}}
    with patch(
        "chemdraw_tool.databases.requests.post", return_value=_resp(payload)
    ) as mock_post:
        databases.pubchem_properties_by_smiles("CC(=O)O")
    assert mock_post.call_args.kwargs["timeout"] == (3, 10)


def test_kegg_and_uniprot_pass_split_timeout():
    with patch(
        "chemdraw_tool.databases.requests.get", return_value=_resp(text="")
    ) as mock_get:
        databases.kegg_find("glucose")
    assert mock_get.call_args.kwargs["timeout"] == (3, 10)

    with patch(
        "chemdraw_tool.databases.requests.get", return_value=_resp({"results": []})
    ) as mock_get:
        databases.uniprot_search("EGFR")
    assert mock_get.call_args.kwargs["timeout"] == (3, 10)
