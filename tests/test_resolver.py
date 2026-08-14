from unittest.mock import Mock, patch

import pytest
import requests
from rdkit import Chem

from chemdraw_tool import resolver
from chemdraw_tool.resolver import (
    NameResolutionError,
    _opsin_lookup,
    is_smiles,
    resolve,
    resolve_name,
    validate_smiles,
)


@pytest.fixture(autouse=True)
def _clear_resolution_cache():
    """resolve_name() cacht Erfolge prozessweit — zwischen Tests leeren,
    sonst sieht ein Test den gemockten Treffer des vorherigen."""
    resolve_name.cache_clear()
    yield
    resolve_name.cache_clear()


def test_is_smiles_recognizes_smiles_with_parens():
    assert is_smiles("CC(=O)Oc1ccccc1C(=O)O") is True


def test_is_smiles_recognizes_simple_ring():
    assert is_smiles("c1ccccc1") is True


def test_is_smiles_recognizes_complex():
    assert is_smiles("CN1C=NC2=C1C(=O)N(C(=O)N2C)C") is True


def test_is_smiles_rejects_plain_name():
    assert is_smiles("Aspirin") is False


def test_is_smiles_rejects_german_name():
    assert is_smiles("Sulfanilsäure") is False


def test_is_smiles_rejects_single_word():
    assert is_smiles("Histidin") is False


def test_validate_smiles_benzene():
    mol = validate_smiles("c1ccccc1")
    assert mol is not None


def test_validate_smiles_aspirin():
    mol = validate_smiles("CC(=O)Oc1ccccc1C(=O)O")
    assert mol is not None


def test_validate_smiles_invalid():
    mol = validate_smiles("definitely_not_a_molecule_XYZ")
    assert mol is None


@patch("chemdraw_tool.resolver.requests.get")
def test_resolve_name_returns_smiles(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 2244, "SMILES": "CC(=O)OC1=CC=CC=C1C(=O)O"}]
        }
    }
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp
    smiles = resolve_name("Aspirin")
    assert smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"


@patch("chemdraw_tool.resolver.requests.get")
def test_resolve_name_calls_pubchem(mock_get):
    # "Aspirin", nicht "Water": OPSIN kennt water und löst es offline,
    # bevor der PubChem-Pfad (den dieser Test prüft) erreicht wird.
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "PropertyTable": {"Properties": [{"CID": 2244, "SMILES": "O"}]}
    }
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp
    resolve_name("Aspirin")
    url = mock_get.call_args[0][0]
    assert "Aspirin" in url
    assert "pubchem" in url


def test_resolve_smiles_input():
    smiles, mol = resolve("c1ccccc1")
    assert smiles == "c1ccccc1"
    assert mol is not None


@patch("chemdraw_tool.resolver.requests.get")
def test_resolve_name_input(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 2244, "SMILES": "CC(=O)OC1=CC=CC=C1C(=O)O"}]
        }
    }
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp
    smiles, mol = resolve("Aspirin")
    assert smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
    assert mol is not None


def test_resolve_invalid_smiles_raises():
    with pytest.raises(ValueError, match="Could not resolve"):
        resolve("C(C)(C)(C)(C)(C)")


def test_is_smiles_rejects_stereo_prefix_names():
    assert is_smiles("(R)-Limonene") is False
    assert is_smiles("(S)-Ibuprofen") is False
    assert is_smiles("(E)-Stilbene") is False
    assert is_smiles("(Z)-Butene") is False
    assert is_smiles("(+)-Camphor") is False
    assert is_smiles("(-)-Menthol") is False
    assert is_smiles("(±)-Naproxen") is False


def test_is_smiles_still_accepts_valid_smiles_with_parens():
    assert is_smiles("C(=O)O") is True
    assert is_smiles("C(C)C") is True
    assert is_smiles("[C@@H](O)(F)Cl") is True


@patch("chemdraw_tool.resolver.requests.get")
def test_resolve_falls_back_to_name_on_invalid_smiles_parse(mock_get):
    """If is_smiles says True but RDKit can't parse it, try name resolution."""
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 22311, "SMILES": "CC1=CCC(CC1)C(=C)C"}]
        }
    }
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp
    smiles, mol = resolve("(R)-Limonene")
    assert mol is not None
    assert "C" in smiles


# --- Kurze valide SMILES ohne Sonderzeichen (Regression: Screenshot 2026-06-10) ---
# "O" ging als NAME an PubChem → molekularer Sauerstoff O=O statt Wasser;
# "CO" → Cobalt [Co] statt Methanol. Der Tool-Docstring verspricht
# "SMILES strings are always safe" → resolve() muss parse-first arbeiten.


@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_water_smiles_offline(mock_pubchem):
    """'O' ist valides SMILES (Wasser) und darf NIE ins Netz gehen."""
    smiles, mol = resolve("O")
    mock_pubchem.assert_not_called()
    assert smiles == "O"
    assert mol.GetNumAtoms() == 1
    assert mol.GetAtomWithIdx(0).GetSymbol() == "O"


@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_methanol_smiles_offline(mock_pubchem):
    """'CO' ist valides SMILES (Methanol), nicht der Name von Cobalt."""
    smiles, mol = resolve("CO")
    mock_pubchem.assert_not_called()
    assert smiles == "CO"
    symbols = sorted(a.GetSymbol() for a in mol.GetAtoms())
    assert symbols == ["C", "O"]


@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_name_path_still_works_for_real_names(mock_pubchem):
    """'Aspirin' parsed nicht als SMILES → Namens-Pfad bleibt intakt."""
    mock_pubchem.return_value = "CC(=O)Oc1ccccc1C(=O)O"
    smiles, mol = resolve("Aspirin")
    mock_pubchem.assert_called_once()
    assert mol.GetNumAtoms() == 13


# --- OPSIN: systematische IUPAC-Namen offline (py2opsin; braucht eine JRE) ---
# PubChem/NCI sind index-basiert und scheitern an systematischen Namen, die in
# keiner DB stehen. OPSIN parst Nomenklatur regelbasiert und offline — er steht
# deshalb VOR den Netz-Lookups in der Kaskade.


def test_opsin_lookup_parses_systematic_name():
    smiles = _opsin_lookup("propan-2-ol")
    assert smiles is not None
    assert Chem.CanonSmiles(smiles) == Chem.CanonSmiles("CC(C)O")


def test_opsin_lookup_trivial_name_returns_none():
    """Markennamen kennt OPSIN nicht → None, Kaskade geht weiter."""
    assert _opsin_lookup("Tylenol") is None


@patch("chemdraw_tool.resolver._java_runtime_available", return_value=False)
def test_opsin_lookup_without_java_returns_none(mock_java):
    """Ohne JRE degradiert OPSIN still — kein Crash, Netz-Kaskade übernimmt."""
    assert _opsin_lookup("propan-2-ol") is None


@patch("chemdraw_tool.resolver._nci_cir_lookup")
@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_systematic_iupac_name_offline(mock_pubchem, mock_nci):
    """Systematische Namen dürfen NIE ins Netz gehen — OPSIN löst offline."""
    smiles, mol = resolve("2-methylbutan-2-ol")
    mock_pubchem.assert_not_called()
    mock_nci.assert_not_called()
    symbols = sorted(a.GetSymbol() for a in mol.GetAtoms())
    assert symbols == ["C", "C", "C", "C", "C", "O"]


@patch("chemdraw_tool.resolver._nci_cir_lookup")
@patch("chemdraw_tool.resolver._pubchem_lookup")
def test_resolve_systematic_stereo_name_offline(mock_pubchem, mock_nci):
    """(2S)-Stereodeskriptor übersteht OPSIN→RDKit: L-Tryptophan per InChIKey."""
    smiles, mol = resolve("(2S)-2-amino-3-(1H-indol-3-yl)propanoic acid")
    mock_pubchem.assert_not_called()
    assert Chem.MolToInchiKey(mol) == "QIVBCDIJIAJPQS-VIFPVBQESA-N"


# --- Fehler-Diagnose: nicht gefunden vs. Netzproblem vs. Mischform ----------
# Vorher warf JEDER Kaskaden-Ausfall dieselbe Meldung ("Use an English/IUPAC
# name…") — bei Netzausfall schickt das den Nutzer auf eine aussichtslose
# Fehlersuche am Namen. Die Ursache muss durch die Kaskade nach oben.


def _http_resp(status: int):
    """Antwort mit HTTP-Fehlerstatus (raise_for_status wirft wie im Ernstfall)."""
    resp = Mock()
    resp.status_code = status
    err = requests.exceptions.HTTPError(f"HTTP {status}")
    err.response = Mock(status_code=status)
    resp.raise_for_status = Mock(side_effect=err)
    return resp


def _ok_pubchem_resp(smiles: str = "CC(=O)Oc1ccccc1C(=O)O"):
    resp = Mock()
    resp.status_code = 200
    resp.raise_for_status = Mock()
    resp.json = Mock(
        return_value={"PropertyTable": {"Properties": [{"SMILES": smiles}]}}
    )
    return resp


def test_resolution_error_is_valueerror_for_callers():
    """server.py fängt ValueError — die neue Fehlerklasse muss darunter fallen."""
    assert issubclass(NameResolutionError, ValueError)


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_all_sources_answer_unknown_name_says_not_found(mock_get, _opsin):
    mock_get.return_value = _http_resp(404)
    with pytest.raises(NameResolutionError) as exc:
        resolve_name("Blahzorbium")
    assert exc.value.kind == "not_found"
    msg = str(exc.value)
    assert msg.startswith("Could not resolve 'Blahzorbium'")
    assert "IUPAC" in msg
    assert "SMILES" in msg


@patch("chemdraw_tool.resolver._java_runtime_available", return_value=True)
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_connection_error_reports_network_not_bad_name(mock_get, _opsin, _java):
    mock_get.side_effect = requests.exceptions.ConnectionError("no route to host")
    with pytest.raises(NameResolutionError) as exc:
        resolve_name("Aspirin")
    assert exc.value.kind == "offline"
    msg = str(exc.value)
    assert "network" in msg.lower()
    # Der irreführende Rat von früher darf hier NICHT stehen:
    assert "Use an English/IUPAC name" not in msg
    # Stattdessen: was offline noch geht.
    assert "SMILES" in msg
    assert "OPSIN" in msg


@patch("chemdraw_tool.resolver._java_runtime_available", return_value=False)
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_offline_without_java_points_to_smiles_and_jre(mock_get, _opsin, _java):
    mock_get.side_effect = requests.exceptions.ConnectionError("down")
    with pytest.raises(NameResolutionError) as exc:
        resolve_name("Aspirin")
    msg = str(exc.value)
    assert exc.value.kind == "offline"
    assert "SMILES" in msg
    assert "Java" in msg


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_timeout_counts_as_network_problem(mock_get, _opsin):
    mock_get.side_effect = requests.exceptions.ReadTimeout("too slow")
    with pytest.raises(NameResolutionError) as exc:
        resolve_name("Aspirin")
    assert exc.value.kind == "offline"
    assert "timed out" in str(exc.value)


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_http_503_is_reported_as_source_outage(mock_get, _opsin):
    mock_get.return_value = _http_resp(503)
    with pytest.raises(NameResolutionError) as exc:
        resolve_name("Aspirin")
    assert exc.value.kind == "sources_down"
    msg = str(exc.value)
    assert "503" in msg
    assert "Use an English/IUPAC name" not in msg


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_mixed_outcome_is_reported_as_partial(mock_get, _opsin):
    """PubChem antwortet (kennt den Namen nicht), NCI ist nicht erreichbar."""
    mock_get.side_effect = [
        _http_resp(404),
        requests.exceptions.ConnectionError("down"),
    ]
    with pytest.raises(NameResolutionError) as exc:
        resolve_name("Aspirin")
    assert exc.value.kind == "partial"
    msg = str(exc.value)
    assert "PubChem" in msg and "NCI CIR" in msg
    assert "retry" in msg.lower()


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_error_message_names_the_sources_and_their_outcome(mock_get, _opsin):
    mock_get.return_value = _http_resp(404)
    with pytest.raises(NameResolutionError) as exc:
        resolve_name("Blahzorbium")
    msg = str(exc.value)
    assert "PubChem" in msg
    assert "NCI CIR" in msg


# --- Latenz: getrennte connect/read-Timeouts + kein Retry auf toten Host ----


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_lookups_use_split_connect_read_timeout(mock_get, _opsin):
    mock_get.return_value = _ok_pubchem_resp()
    resolve_name("Aspirin")
    assert mock_get.call_args.kwargs["timeout"] == (3, 10)


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_unreachable_host_is_not_dialed_twice(mock_get, _opsin):
    """Umlaut-Name = 4 Calls (2× PubChem, 2× NCI). Ist ein Host tot, darf er
    nicht ein zweites Mal ins Connect-Timeout laufen."""
    mock_get.side_effect = requests.exceptions.ConnectionError("down")
    with pytest.raises(NameResolutionError):
        resolve_name("Sulfanilsäure")
    assert mock_get.call_count == 2


# --- Cache: Erfolge ja, Fehlschläge nie ------------------------------------


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_successful_resolution_is_cached(mock_get, _opsin):
    mock_get.return_value = _ok_pubchem_resp()
    first = resolve_name("Aspirin")
    second = resolve_name("Aspirin")
    assert first == second
    assert mock_get.call_count == 1


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_failed_resolution_is_not_cached(mock_get, _opsin):
    """Wer offline war und wieder online geht, darf nicht auf dem Fehler sitzen
    bleiben — Fehlschläge gehören NICHT in den Cache."""
    mock_get.side_effect = [
        requests.exceptions.ConnectionError("down"),
        requests.exceptions.ConnectionError("down"),
        _ok_pubchem_resp(),
    ]
    with pytest.raises(NameResolutionError):
        resolve_name("Aspirin")
    assert resolve_name("Aspirin") == "CC(=O)Oc1ccccc1C(=O)O"


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_cache_is_clearable(mock_get, _opsin):
    mock_get.return_value = _ok_pubchem_resp()
    resolve_name("Aspirin")
    resolver.resolve_name.cache_clear()
    resolve_name("Aspirin")
    assert mock_get.call_count == 2
