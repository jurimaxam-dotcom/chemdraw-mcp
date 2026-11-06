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
    # Seit Etappe 1 (26.10.2026): fünfbindiger Kohlenstoff geht nicht mehr als
    # Name ins Netz, sondern scheitert lokal als invalid_smiles.
    with pytest.raises(NameResolutionError, match="Could not read") as exc:
        resolve("C(C)(C)(C)(C)(C)")
    assert exc.value.kind == "invalid_smiles"


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


# --- Masse-Eval-Befund 2: OPSIN zerlegt Trivialnamen ---------------------------
# OPSIN liest "tropic-amide" als Tropasäureamid, "methyl-dopa" als N-Methyl-DOPA.
# Messung 06.11. (233 OPSIN-Treffer): kein Trennmerkmal im Namen, aber ohne
# Lokanten fragt der Resolver PubChem gegen; nur ein anderes Gerüst zählt.

_OPSIN_TROPICAMIDE = "C(C(CO)C1=CC=CC=C1)(=O)N"  # was OPSIN baut
_PUBCHEM_TROPICAMIDE = "CCN(CC1=CC=NC=C1)C(=O)C(CO)C2=CC=CC=C2"


@patch("chemdraw_tool.resolver._pubchem_lookup", return_value=_PUBCHEM_TROPICAMIDE)
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=_OPSIN_TROPICAMIDE)
def test_trivial_name_opsin_misparse_loses_to_pubchem(_opsin, _pubchem):
    assert resolve_name("tropicamide") == _PUBCHEM_TROPICAMIDE


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=_OPSIN_TROPICAMIDE)
def test_trivial_name_offline_keeps_opsin_answer(_opsin):
    """Ohne Netz bleibt OPSINs Antwort — "ethanol" muss offline gehen."""

    def offline(name, report=None):
        resolver._record(report, resolver._PUBCHEM, *resolver._classify_error(
            requests.exceptions.ConnectionError("down")))
        return None

    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=offline):
        assert resolve_name("tropicamide") == _OPSIN_TROPICAMIDE


@patch("chemdraw_tool.resolver._pubchem_lookup", return_value="N[C@@H](CC)C(=O)O")
@patch("chemdraw_tool.resolver._opsin_lookup", return_value="NC(CC)C(=O)O")
def test_trivial_name_same_skeleton_keeps_opsin(_opsin, _pubchem):
    """Nur das Gerüst entscheidet — ein Stereo-Unterschied ist keine Uneinigkeit."""
    assert resolve_name("butyrine") == "NC(CC)C(=O)O"


def test_german_name_wrong_pubchem_synonym_keeps_opsin():
    """PubChem führt 'Glycin' beim Fotoentwickler; 'Glycine' bestätigt OPSIN."""
    answers = {"Glycin": "OC(=O)CNc1ccc(O)cc1", "Glycine": "C(C(=O)O)N"}
    with patch("chemdraw_tool.resolver._opsin_lookup", return_value="NCC(=O)O"), \
         patch("chemdraw_tool.resolver._pubchem_lookup",
               side_effect=lambda n, report=None: answers.get(n)):
        assert resolve_name("Glycin") == "NCC(=O)O"


@patch("chemdraw_tool.resolver._pubchem_lookup")
@patch("chemdraw_tool.resolver._opsin_lookup", return_value="CC(C)O")
def test_name_with_locants_never_cross_checked(_opsin, mock_pubchem):
    for name in ("propan-2-ol", "(R)-butan-2-ol", "N,N-dimethylformamide"):
        resolve_name.cache_clear()
        resolve_name(name)
    mock_pubchem.assert_not_called()


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


# --- Kaputtes SMILES nie in die Namenskaskade (Etappe 1, 26.10.2026) ---------
# Gemessen: "c1cccc1" wurde über NCI still zu Cyclopentan, "C1CCC" bekam
# „retry once the connection is stable“, "CN(C)(C)C" „Use the English name“.
# Beweis, dass keine Namensquelle gefragt wird: resolve_name ist der einzige
# Eingang in die Kaskade und wirft hier sofort.


@pytest.fixture
def _no_cascade(monkeypatch):
    def forbidden(name):
        raise AssertionError(f"Namenskaskade betreten für {name!r}")

    monkeypatch.setattr(resolver, "resolve_name", forbidden)


@pytest.mark.parametrize(
    "smiles, fragments",
    [
        ("c1cccc1", ["kekulize", "c1ccccc1", "C1CCCC1"]),
        ("CN(C)(C)C", ["valence", "atom 2 (N)", "C[N+](C)(C)C"]),
        ("C1CCC", ["ring bond 1", "never closed", "C1CCC1"]),
        ("C(C)(C)(C)(C)(C)", ["valence", "atom 1 (C)"]),
        ("CC(C", ["parenthesis"]),
        ("CC)C", ["parenthesis"]),
    ],
)
def test_broken_smiles_is_invalid_smiles_not_a_name(_no_cascade, smiles, fragments):
    with pytest.raises(NameResolutionError) as exc:
        resolve(smiles)
    assert exc.value.kind == "invalid_smiles"
    message = str(exc.value)
    assert smiles in message
    for fragment in fragments:
        assert fragment in message, message


def test_invalid_smiles_error_is_still_a_valueerror(_no_cascade):
    with pytest.raises(ValueError):
        resolve("c1cccc1")


# Gegenprobe: Element­symbole, Summenformeln und Namen sehen teils aus wie
# SMILES-Zeichen ("Co" = c + aromatisches o, "CO2" = offener Ring 2), sind aber
# Namen — sie müssen weiter in die Kaskade.
@pytest.mark.parametrize(
    "name",
    ["Co", "Cs", "Sn", "Pb", "NaCl", "Fe", "CO2", "SO2", "NO2", "N2O", "N2",
     "O3", "Cl2", "CS2", "PCl5", "SF6", "BF3", "H2O", "2-Propanol", "Coffein",
     "Aspirin", "(R)-Limonene", "[2.2]paracyclophane"],
)
def test_names_and_formulas_still_go_to_the_cascade(monkeypatch, name):
    seen = []

    def fake(n):
        seen.append(n)
        return "C"

    monkeypatch.setattr(resolver, "resolve_name", fake)
    smiles, _ = resolve(name)
    assert seen == [name]
    assert smiles == "C"


def test_fixture_inputs_are_never_classified_invalid_smiles(monkeypatch):
    """Alle Eingaben aus tests/identity/stoffe.json, die auflösbar sein sollen,
    erreichen die Kaskade oder parsen als SMILES — keine wird invalid_smiles."""
    import json
    from pathlib import Path

    fixture = Path(__file__).parent / "identity" / "stoffe.json"
    entries = json.loads(fixture.read_text(encoding="utf-8"))["stoffe"]
    monkeypatch.setattr(resolver, "resolve_name", lambda n: "C")
    for entry in entries:
        if "fehler" in entry:
            continue
        resolve(entry["eingabe"])  # wirft nicht


def test_two_open_rings_get_no_append_suggestion(_no_cascade):
    with pytest.raises(NameResolutionError) as exc:
        resolve("C1CC2")
    assert "ring bond 2" in str(exc.value)
    assert "Suggestion" not in str(exc.value)


# --- NCI CIR meldet "unbekannt" als HTTP 500 (Masse-Evaluation 04.11.2026) ---
# Belegt per curl: cactus.nci.nih.gov antwortet auf jeden unbekannten Namen mit
# Status 500 und dem Body "<h1>Page not found (404)</h1>". Vorher zählte das als
# Quellenfehler → kind "partial" ("retry once the connection is stable") für jeden
# deutschen Trivialnamen, den PubChem nicht kennt. Im Lauf über 711 Eingaben
# waren so 14 % gelb statt "not_found".


def _nci_resp(status: int, text: str):
    resp = Mock()
    resp.status_code = status
    resp.text = text
    resp.raise_for_status = Mock()
    return resp


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_nci_page_not_found_500_is_not_found(mock_get, _opsin):
    """PubChem 404 + NCI 500 'Page not found' → jede Quelle hat geantwortet: not_found."""
    mock_get.side_effect = [
        _http_resp(404),
        _nci_resp(500, "<h1>Page not found (404)</h1>\n"),
        _http_resp(404),  # englische Variante "Nifedipine", ebenfalls unbekannt
    ]
    with pytest.raises(NameResolutionError) as exc:
        resolve_name("Nifedipin")
    assert mock_get.call_count == 3
    assert exc.value.kind == "not_found"
    msg = str(exc.value)
    assert "retry" not in msg.lower()
    assert "English" in msg


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver.requests.get")
def test_nci_real_500_stays_source_error(mock_get, _opsin):
    """Ein 500 ohne 'Page not found' bleibt ein Quellenfehler → partial."""
    mock_get.side_effect = [
        _http_resp(404),
        _nci_resp(500, "<h1>Internal Server Error</h1>"),
    ]
    with pytest.raises(NameResolutionError) as exc:
        resolve_name("Nifedipin")
    assert exc.value.kind == "partial"


# --- Deutsche Trivialnamen: englische Variante als letzter Versuch -----------
# Masse-Eval 11/2026: 75 deutsche Eingaben ohne PubChem-Synonym (Amilorid,
# Dexamethason, Maleinsäure). Die Variante steht GANZ HINTEN, damit kein heute
# aufgelöster Name einen anderen Weg nimmt — sie greift nur, wo sonst
# not_found stünde.


def _only_for(hit_name: str, smiles: str = "CC(=O)O"):
    """PubChem-Attrappe: trifft nur für genau diesen Namen."""
    calls: list[str] = []

    def lookup(name, report=None):
        calls.append(name)
        if name == hit_name:
            return smiles
        resolver._record(report, resolver._PUBCHEM, resolver._NOT_FOUND, "name unknown")
        return None

    return lookup, calls


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_german_name_falls_back_to_english_variant_last(mock_nci, mock_opsin):
    lookup, calls = _only_for("Dexamethasone")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name("Dexamethason") == "CC(=O)O"
    assert calls == ["Dexamethason", "Dexamethasone"]
    # NCI wurde mit dem Original gefragt, bevor die Variante drankam
    assert [c.args[0] for c in mock_nci.call_args_list] == ["Dexamethason"]


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_umlaut_name_variant_is_built_from_the_original(mock_nci, mock_opsin):
    """'Maleinsaeure' hat kein -säure mehr — die Regel braucht das Original."""
    lookup, calls = _only_for("Maleinic acid")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name("Maleinsäure") == "CC(=O)O"
    assert calls == ["Maleinsäure", "Maleinsaeure", "Maleinic acid"]


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_direct_hit_never_asks_for_the_variant(mock_nci, mock_opsin):
    lookup, calls = _only_for("Dexamethason")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        resolve_name("Dexamethason")
    assert calls == ["Dexamethason"]


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_variant_miss_keeps_not_found(mock_nci, mock_opsin):
    lookup, calls = _only_for("nothing")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        with pytest.raises(NameResolutionError) as exc:
            resolve_name("Dexamethason")
    assert exc.value.kind == "not_found"
    assert calls == ["Dexamethason", "Dexamethasone"]
