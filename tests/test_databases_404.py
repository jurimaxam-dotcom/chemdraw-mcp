"""Ein 404 heißt „Stoff unbekannt“ — kein Traceback im Log (E17, 10.11.2026).

Befund aus der Doku-Etappe: Ein frei gebautes Pentapeptid hat bei PubChem
keinen Eintrag; jede Abfrage (InChIKey-Properties, -Synonyme, CAS-Abschnitt)
schrieb einen vollen Traceback als WARNING nach stderr und ins server.log. Das
ist der Normalfall für unbekannte Stoffe, kein Fehler. Echte Ausfälle (5xx,
Timeout) bleiben als WARNING mit Traceback sichtbar.
"""

import logging
from unittest.mock import Mock, patch

import pytest
import requests

from chemdraw_tool import databases


def _http_error(status: int) -> Mock:
    resp = Mock()
    resp.status_code = status
    err = requests.HTTPError(f"{status} Client Error", response=resp)
    resp.raise_for_status = Mock(side_effect=err)
    return resp


# (Aufruf, HTTP-Verb) — jede PubChem-/ChEBI-/KEGG-Stelle mit raise_for_status.
CALLS = [
    (lambda: databases._get_cid("x"), "get"),
    (lambda: databases.pubchem_properties("x"), "get"),
    (lambda: databases.pubchem_properties_by_smiles("CC"), "post"),
    (lambda: databases.pubchem_properties_by_inchikey("KEY"), "get"),
    (lambda: databases.pubchem_title_by_inchikey("KEY"), "get"),
    (lambda: databases.pubchem_synonyms_by_inchikey("KEY"), "get"),
    (lambda: databases.pubchem_synonyms("x"), "get"),
    (lambda: databases.pubchem_synonyms_by_smiles("CC"), "post"),
    (lambda: databases._synonyms_and_cas({"CID": 9851104, "Synonym": []}), "get"),
    (lambda: databases.pubchem_physical_properties(1), "get"),
    (lambda: databases.chebi_lookup("x"), "get"),
    (lambda: databases.kegg_find("x"), "get"),
    (lambda: databases.kegg_compound("C00031"), "get"),
]


@pytest.mark.parametrize("call,verb", CALLS)
def test_404_is_one_quiet_line_without_traceback(call, verb, caplog):
    caplog.set_level(logging.DEBUG, logger="chemdraw_tool.databases")
    with patch(f"chemdraw_tool.databases.requests.{verb}", return_value=_http_error(404)):
        call()
    records = [r for r in caplog.records if r.name == "chemdraw_tool.databases"]
    assert records, "der 404 soll eine Zeile hinterlassen"
    assert all(r.levelno <= logging.INFO for r in records), [r.getMessage() for r in records]
    assert all(r.exc_info is None for r in records)
    assert all("404" in r.getMessage() for r in records)


@pytest.mark.parametrize("call,verb", CALLS)
def test_server_errors_and_timeouts_stay_visible(call, verb, caplog):
    for failure in (_http_error(503), requests.Timeout("read timed out")):
        caplog.clear()
        kwargs = {"return_value": failure} if isinstance(failure, Mock) else {"side_effect": failure}
        with patch(f"chemdraw_tool.databases.requests.{verb}", **kwargs):
            call()
        warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert warnings and warnings[0].exc_info is not None
