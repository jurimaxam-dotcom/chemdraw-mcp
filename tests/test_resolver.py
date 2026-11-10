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
    assert mock_pubchem.call_args_list[0].args[0] == "Aspirin"
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


# Nachbesserung (Codex-Abnahme 06.11.): PubChem führt "sodium phosphate" als
# Hydrogenphosphat-Anion (Ladung −2) und Silikate in anderer Stöchiometrie.
# Gemessen an 22 Fällen: jede Salz-Kippe ist kohlenstofffrei, jeder Gewinn
# organisch. Werte = echte Antworten von OPSIN/PubChem (06.11.2026).
_SALZE = {
    # Name: (OPSIN, PubChem, erwartet)
    "sodium phosphate": (
        "[O-]P(=O)([O-])[O-].[Na+].[Na+].[Na+]",
        "[O-]P(=O)([O-])[O-].[Na+]",
        "OPSIN",
    ),
    "calcium silicate": (
        "[Si]([O-])([O-])([O-])[O-].[Ca+2].[Ca+2]",
        "O[Si](O)(O)[O-].O[Si](O)(O)[O-].[Ca+2]",
        "OPSIN",
    ),
    "sodium silicate": (
        "[Si]([O-])([O-])([O-])[O-].[Na+].[Na+].[Na+].[Na+]",
        "[O-][Si](=O)[O-].[Na+].[Na+]",
        "OPSIN",
    ),
    "magnesium oxide": ("[O-2].[Mg+2]", "O=[Mg]", "OPSIN"),
    # organisch, gleiches Muster wie Lauf 4 — hier muss PubChem gewinnen
    "sodium calcium edetate": (
        "C(N(CC(=O)[O-])CC(=O)O)CN(CC(=O)[O-])CC(=O)[O-].[Ca+2].[Na+]",
        "C(CN(CC(=O)[O-])CC(=O)[O-])N(CC(=O)[O-])CC(=O)[O-].[Na+].[Na+].[Ca+2]",
        "PubChem",
    ),
}


@pytest.mark.parametrize("name", sorted(_SALZE))
def test_salt_cross_check_keeps_opsin_for_inorganic_names(name):
    opsin, pubchem, wer = _SALZE[name]
    with patch("chemdraw_tool.resolver._opsin_lookup", return_value=opsin), \
         patch("chemdraw_tool.resolver._pubchem_lookup", return_value=pubchem):
        assert resolve_name(name) == (opsin if wer == "OPSIN" else pubchem)


def test_sodium_phosphate_stays_neutral_trisodium_salt():
    """Abnahme 1: Na3PO4, Ladung 0, Gerüst RYFMWSXOAZQYPI."""
    opsin, pubchem, _ = _SALZE["sodium phosphate"]
    with patch("chemdraw_tool.resolver._opsin_lookup", return_value=opsin), \
         patch("chemdraw_tool.resolver._pubchem_lookup", return_value=pubchem):
        mol = Chem.MolFromSmiles(resolve_name("sodium phosphate"))
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    assert CalcMolFormula(mol) == "Na3O4P"
    assert Chem.GetFormalCharge(mol) == 0
    assert Chem.MolToInchiKey(mol).startswith("RYFMWSXOAZQYPI")


@patch("chemdraw_tool.resolver._pubchem_lookup", return_value="N[C@@H](Cc1cc(I)c(O)c(I)c1)C(=O)[O-]")
@patch("chemdraw_tool.resolver._opsin_lookup", return_value="IN([C@@H](CC1=CC=C(C=C1)O)C(=O)O)I")
def test_charged_pubchem_answer_with_right_skeleton_still_wins(_opsin, _pubchem):
    """Holdout 06.11.: PubChem führt Diiodtyrosin als Anion; OPSIN baut N,N-Diiod.
    Eine Ladungsregel würde hier den falschen Stoff wählen — darum gibt es keine."""
    smiles = resolve_name("diiodo-L-tyrosine")
    assert Chem.MolToInchiKey(Chem.MolFromSmiles(smiles)).startswith("NYPYHUZRZVSYKL")


# Formkonflikt (Codex-Abnahme #4, 06.11.): PubChem führt "potassium citrate"
# als Monohydrat (CID 2735208), OPSIN baut das wasserfreie Salz aus dem Namen.
# Kristallwasser ist keine Gerüstkorrektur. Gemessen über 301 OPSIN-Treffer:
# nur Wasser abziehen ändert genau diesen Fall; die größte organische
# Komponente zu vergleichen kippte zwei Gewinne, deren Gegenionen PubChem
# richtig hat (Edetat Na2Ca, Goldthiomalat Au/Na). Werte = echte Antworten.
_FORMEN = {
    # Name: (OPSIN, PubChem, erwartet)
    "potassium citrate": (
        "C(CC(O)(C(=O)[O-])CC(=O)[O-])(=O)[O-].[K+].[K+].[K+]",
        "C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O.O.[K+].[K+].[K+]",
        "OPSIN",
    ),
    "potassium citrate monohydrate": (
        "C(CC(O)(C(=O)[O-])CC(=O)[O-])(=O)[O-].[K+].[K+].[K+].O",
        "C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O.O.[K+].[K+].[K+]",
        "OPSIN",
    ),
    "gold monosodium thiomalate": (
        "C(C(S)CC(=O)[O-])(=O)[O-].[Na+].[Au+3].C(C(S)CC(=O)[O-])(=O)[O-]",
        "C(C(C(=O)[O-])S)C(=O)[O-].[Na+].[Au+]",
        "PubChem",
    ),
}


@pytest.mark.parametrize("name", sorted(_FORMEN))
def test_water_alone_is_a_form_conflict_not_a_correction(name):
    opsin, pubchem, wer = _FORMEN[name]
    with patch("chemdraw_tool.resolver._opsin_lookup", return_value=opsin), \
         patch("chemdraw_tool.resolver._pubchem_lookup", return_value=pubchem):
        assert resolve_name(name) == (opsin if wer == "OPSIN" else pubchem)


def test_potassium_citrate_stays_anhydrous():
    opsin, pubchem, _ = _FORMEN["potassium citrate"]
    with patch("chemdraw_tool.resolver._opsin_lookup", return_value=opsin), \
         patch("chemdraw_tool.resolver._pubchem_lookup", return_value=pubchem):
        mol = Chem.MolFromSmiles(resolve_name("potassium citrate"))
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    assert CalcMolFormula(mol) == "C6H5K3O7"
    assert Chem.MolToInchiKey(mol).startswith("QEEAPRPFLLJWCF")


# Erweiterte Gegenprobe aus Codex-Abnahme #4: organische Salze, bei denen OPSIN
# und PubChem dieselbe Zusammensetzung liefern (nur andere Schreibweise) — kein
# Umschalten. Echte Antwortpaare (OPSIN, PubChem), gemessen 06.11.2026.
_SALZE_ORGANISCH = {
    'sodium citrate': (
        'C(CC(O)(C(=O)[O-])CC(=O)[O-])(=O)[O-].[Na+].[Na+].[Na+]',
        'C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O.[Na+].[Na+].[Na+]',
    ),
    'calcium gluconate': (
        'O=C([C@H](O)[C@@H](O)[C@H](O)[C@H](O)CO)[O-].[Ca+2].O=C([C@H](O)[C@@H](O)[C@H](O)[C@H](O)CO)[O-]',
        'C([C@H]([C@H]([C@@H]([C@H](C(=O)[O-])O)O)O)O)O.C([C@H]([C@H]([C@@H]([C@H](C(=O)[O-])O)O)O)O)O.[Ca+2]',
    ),
    'sodium acetate': (
        'C(C)(=O)[O-].[Na+]',
        'CC(=O)[O-].[Na+]',
    ),
    'magnesium stearate': (
        'C(CCCCCCCCCCCCCCCCC)(=O)[O-].[Mg+2].C(CCCCCCCCCCCCCCCCC)(=O)[O-]',
        'CCCCCCCCCCCCCCCCCC(=O)[O-].CCCCCCCCCCCCCCCCCC(=O)[O-].[Mg+2]',
    ),
    'calcium citrate': (
        'C(CC(O)(C(=O)[O-])CC(=O)[O-])(=O)[O-].[Ca+2].C(CC(O)(C(=O)[O-])CC(=O)[O-])(=O)[O-].[Ca+2].[Ca+2]',
        'C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O.C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O.[Ca+2].[Ca+2].[Ca+2]',
    ),
    'magnesium citrate': (
        'C(CC(O)(C(=O)[O-])CC(=O)[O-])(=O)[O-].[Mg+2].C(CC(O)(C(=O)[O-])CC(=O)[O-])(=O)[O-].[Mg+2].[Mg+2]',
        'C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O.C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O.[Mg+2].[Mg+2].[Mg+2]',
    ),
    'sodium tartrate': (
        'C(=O)([O-])C(O)C(O)C(=O)[O-].[Na+].[Na+]',
        '[C@@H]([C@H](C(=O)[O-])O)(C(=O)[O-])O.[Na+].[Na+]',
    ),
    'aluminium acetate': (
        'C(C)(=O)[O-].[Al+3].C(C)(=O)[O-].C(C)(=O)[O-]',
        'CC(=O)[O-].CC(=O)[O-].CC(=O)[O-].[Al+3]',
    ),
    'silver acetate': (
        'C(C)(=O)[O-].[Ag+]',
        'CC(=O)[O-].[Ag+]',
    ),
    'lithium citrate': (
        'C(CC(O)(C(=O)[O-])CC(=O)[O-])(=O)[O-].[Li+].[Li+].[Li+]',
        '[Li+].[Li+].[Li+].C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O',
    ),
    'calcium lactate': (
        'C(C(O)C)(=O)[O-].[Ca+2].C(C(O)C)(=O)[O-]',
        'CC(C(=O)[O-])O.CC(C(=O)[O-])O.[Ca+2]',
    ),
    'sodium oxalate': (
        'C(C(=O)[O-])(=O)[O-].[Na+].[Na+]',
        'C(=O)(C(=O)[O-])[O-].[Na+].[Na+]',
    ),
    'calcium acetate': (
        'C(C)(=O)[O-].[Ca+2].C(C)(=O)[O-]',
        'CC(=O)[O-].CC(=O)[O-].[Ca+2]',
    ),
    'sodium bicarbonate': (
        'C([O-])(O)=O.[Na+]',
        'C(=O)(O)[O-].[Na+]',
    ),
    'sodium citrate dihydrate': (
        'O.O.C(CC(O)(C(=O)[O-])CC(=O)[O-])(=O)[O-].[Na+].[Na+].[Na+]',
        'C(C(=O)[O-])C(CC(=O)[O-])(C(=O)[O-])O.O.O.[Na+].[Na+].[Na+]',
    ),
}


@pytest.mark.parametrize("name", sorted(_SALZE_ORGANISCH))
def test_organic_salt_same_composition_keeps_opsin(name):
    opsin, pubchem = _SALZE_ORGANISCH[name]
    with patch("chemdraw_tool.resolver._opsin_lookup", return_value=opsin), \
         patch("chemdraw_tool.resolver._pubchem_lookup", return_value=pubchem):
        assert resolve_name(name) == opsin


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
    nach_erstem = mock_get.call_count  # Treffer + Variantenprobe (Befund 3)
    second = resolve_name("Aspirin")
    assert first == second
    assert nach_erstem >= 1
    assert mock_get.call_count == nach_erstem


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
    je_lauf = mock_get.call_count
    resolver.resolve_name.cache_clear()
    resolve_name("Aspirin")
    assert mock_get.call_count == 2 * je_lauf


# --- Kaputtes SMILES nie in die Namenskaskade (Etappe 1, 26.10.2026) ---------
# Gemessen: "c1cccc1" wurde über NCI still zu Cyclopentan, "C1CCC" bekam
# „retry once the connection is stable“, "CN(C)(C)C" „Use the English name“.
# Beweis, dass keine Namensquelle gefragt wird: resolve_name_route ist der
# einzige Eingang in die Kaskade und wirft hier sofort.


@pytest.fixture
def _no_cascade(monkeypatch):
    def forbidden(name):
        raise AssertionError(f"Namenskaskade betreten für {name!r}")

    monkeypatch.setattr(resolver, "resolve_name_route", forbidden)


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
        return resolver.Resolution("C")

    monkeypatch.setattr(resolver, "resolve_name_route", fake)
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
    monkeypatch.setattr(resolver, "resolve_name_route", lambda n: resolver.Resolution("C"))
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
# Dexamethason, Maleinsäure). Als Auflösungsweg steht die Variante GANZ HINTEN —
# sie greift nur, wo sonst not_found stünde. Seit Befund 3 prüft sie zusätzlich
# einen Direkttreffer gegen (siehe „PubChem-Synonymfehler“ unten).


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
def test_direct_hit_keeps_its_answer_when_the_variant_is_unknown(mock_nci, mock_opsin):
    """Seit Befund 3 fragt ein Direkttreffer die Variante einmal gegen (siehe
    unten); kennt PubChem die Variante nicht, bleibt der Direkttreffer."""
    lookup, calls = _only_for("Dexamethason")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name("Dexamethason") == "CC(=O)O"
    assert calls == ["Dexamethason", "Dexamethasone"]


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_variant_miss_keeps_not_found(mock_nci, mock_opsin):
    lookup, calls = _only_for("nothing")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        with pytest.raises(NameResolutionError) as exc:
            resolve_name("Dexamethason")
    assert exc.value.kind == "not_found"
    assert calls == ["Dexamethason", "Dexamethasone"]


# --- PubChem-Synonymfehler (Masse-Eval-Befund 3, 06.11.2026) ----------------
# "(−)-Ephedrin" trifft als Synonym genau einen Record: CID 104213,
# 1-Bromo-3-methyl-5-nitrobenzene (35 Synonyme, nur "(-)-ephedrin" passt).
# "Risperidon" trifft CID 44402564, ein Dihydro-Analogon mit 5 Synonymen.
# Eine Schreibweise ändert kein Stammmolekül. Verglichen wird die größte
# organische Komponente: Gegenionen/Protonierung sind Depositor-Form, kein
# anderer Stoff (Centrophenoxin: Variante = HCl-Salz; mit Gegenionen im
# Vergleich kippte der Holdout 1 von 553 Fällen auf das Salz). Werte = echte
# PubChem-Antworten vom 06.11.2026.
_SYNONYMFEHLER = {
    # Eingabe: (Variante, PubChem für Eingabe, PubChem für Variante)
    "(−)-Ephedrin": (
        "Ephedrine",
        "CC1=CC(=CC(=C1)Br)[N+](=O)[O-]",
        "C[C@@H]([C@@H](C1=CC=CC=C1)O)NC",
    ),
    "Risperidon": (
        "Risperidone",
        "CC1=C(C(=O)N2CCCCC2=N1)CCN3CCC(CC3)C4C5=C(C=C(C=C5)F)ON4",
        "CC1=C(C(=O)N2CCCCC2=N1)CCN3CCC(CC3)C4=NOC5=C4C=CC(=C5)F",
    ),
}


def _pubchem_table(table: dict):
    calls: list[str] = []

    def lookup(name, report=None):
        calls.append(name)
        if name in table:
            return table[name]
        resolver._record(report, resolver._PUBCHEM, resolver._NOT_FOUND, "name unknown")
        return None

    return lookup, calls


@pytest.mark.parametrize("name", sorted(_SYNONYMFEHLER))
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_variant_overrules_a_stray_pubchem_synonym(_opsin, name):
    variante, direkt, richtig = _SYNONYMFEHLER[name]
    lookup, calls = _pubchem_table({name: direkt, variante: richtig})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name(name) == richtig
    assert calls == [name, variante]


def test_stereo_prefix_is_dropped_for_the_variant():
    """(−)/(+)/(S)/(RS)-Klammerpräfixe ändern kein Gerüst — die Variante fragt ohne."""
    assert resolver._spelling_variant("(−)-Ephedrin") == "Ephedrine"
    assert resolver._spelling_variant("(S)-(−)-timolol") == "timolol"
    assert resolver._spelling_variant("(+)-Pseudoephedrin") == "Pseudoephedrine"
    assert resolver._spelling_variant("risperidone") is None


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_agreeing_variant_keeps_the_direct_answer(_opsin):
    """Gleiches Gerüst, andere Form (Stereo, Schreibweise) → Direkttreffer bleibt."""
    lookup, calls = _pubchem_table({"Procain": "CCN(CC)CCOC(=O)C1=CC=C(C=C1)N",
                                    "Procaine": "NC1=CC=C(C=C1)C(=O)OCCN(CC)CC"})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name("Procain") == "CCN(CC)CCOC(=O)C1=CC=C(C=C1)N"
    assert calls == ["Procain", "Procaine"]


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_name_without_variant_costs_no_second_call(_opsin):
    lookup, calls = _pubchem_table({"risperidone": "C"})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name("risperidone") == "C"
    assert calls == ["risperidone"]


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_unreachable_variant_keeps_the_direct_answer(_opsin):
    """Netz weg zwischen den beiden Fragen → kein Fehler, Direkttreffer bleibt."""
    def lookup(name, report=None):
        if name == "Risperidon":
            return _SYNONYMFEHLER["Risperidon"][1]
        resolver._record(report, resolver._PUBCHEM, resolver._UNREACHABLE, "timeout")
        return None
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name("Risperidon") == _SYNONYMFEHLER["Risperidon"][1]


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_salt_form_of_the_variant_is_no_correction(_opsin):
    """Centrophenoxin: direkt freie Base (richtig), Variante HCl-Salz → Formkonflikt."""
    base = "CN(C)CCOC(=O)COC1=CC=C(C=C1)Cl"
    lookup, calls = _pubchem_table({"Centrophenoxin": base,
                                    "Centrophenoxine": base + ".Cl"})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name("Centrophenoxin") == base
    assert calls == ["Centrophenoxin", "Centrophenoxine"]


# Salzform-Befund (06.11.2026): Ein INN ohne Salzwort meint den freien Stoff.
# PubChem führt "Bendamustin" als Hydrochlorid (CID 77082), "Phenelzin" als
# Sulfat (CID 61100); die englische Variante trifft jeweils die freie Base
# (CID 65628, 3675) — dieselbe, die Wikidata als Referenz führt. Gleiches
# Stammmolekül, verschieden viele Komponenten → die Form ohne Gegenion.
# Werte = echte PubChem-Antworten vom 06.11.2026.
_SALZFORM = {
    # Eingabe: (Variante, PubChem für Eingabe, PubChem für Variante)
    "Bendamustin": (
        "Bendamustine",
        "CN1C2=C(C=C(C=C2)N(CCCl)CCCl)N=C1CCCC(=O)O.Cl",
        "CN1C2=C(C=C(C=C2)N(CCCl)CCCl)N=C1CCCC(=O)O",
    ),
    "Phenelzin": (
        "Phenelzine",
        "C1=CC=C(C=C1)CCNN.OS(=O)(=O)O",
        "C1=CC=C(C=C1)CCNN",
    ),
}


@pytest.mark.parametrize("name", sorted(_SALZFORM))
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_name_without_salt_word_gets_the_free_form(_opsin, name):
    """INN ohne Salzwort, PubChem direkt = Salz, Variante = freie Base → freie Base."""
    variante, direkt, frei = _SALZFORM[name]
    lookup, calls = _pubchem_table({name: direkt, variante: frei})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name(name) == frei
    assert calls == [name, variante]


# Schnitt 3 = Variante A>= (Chef-Entscheid 07.11.2026, Kippmessung
# docs/evidence/masse-eval-2026-11/kippmessung-stereo/): Gleiches Stammmolekül,
# aber Block 1+2 des InChIKeys weicht ab — einer der beiden PubChem-Records
# trägt die Stereochemie unvollständig oder falsch. Die Variante gewinnt nur,
# wenn sie mindestens so viele definierte Stereoelemente hat (≥ gezählt).
# Werte = aufgezeichnete PubChem-Antworten (memo.json, 07.11.2026).
_STEREO_FORM = {
    # Eingabe: (Variante, PubChem für Eingabe, PubChem für Variante)
    "Naloxon": (  # 3 → 4 Elemente: C14 fehlt im deutschen Record
        "Naloxone",
        "C=CCN1CC[C@]23[C@@H]4C(=O)CC[C@]2(C1CC5=C3C(=C(C=C5)O)O4)O",
        "C=CCN1CC[C@]23[C@@H]4C(=O)CC[C@]2([C@H]1CC5=C3C(=C(C=C5)O)O4)O",
    ),
    "Vareniclin": (  # flach → definiert; die Zentren sind ohnehin erzwungen
        "Varenicline",
        "C1C2CNCC1C3=CC4=NC=CN=C4C=C23",
        "C1[C@@H]2CNC[C@H]1C3=CC4=NC=CN=C4C=C23",
    ),
}

_LINCOMYCIN = (  # 9 → 0 Elemente: die Variante ist der flache Record
    "Lincomycine",
    "CCC[C@@H]1C[C@H](N(C1)C)C(=O)N[C@@H]([C@@H]2[C@@H]([C@@H]([C@H]([C@H](O2)SC)O)O)O)[C@@H](C)O",
    "CCCC1CC(N(C1)C)C(=O)NC(C2C(C(C(C(O2)SC)O)O)O)C(C)O",
)


@pytest.mark.parametrize("name", sorted(_STEREO_FORM))
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_spelling_variant_with_more_defined_stereo_wins(_opsin, name):
    """Gleiches Gerüst, Variante mit ≥ definierten Stereoelementen → Variante."""
    variante, direkt, definiert = _STEREO_FORM[name]
    lookup, calls = _pubchem_table({name: direkt, variante: definiert})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name(name) == definiert
    assert calls == [name, variante]


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_spelling_variant_never_drops_defined_stereo(_opsin):
    """Lincomycin: direkt 9 Elemente, Variante flach → der definierte Direkttreffer bleibt."""
    variante, definiert, flach = _LINCOMYCIN
    lookup, _ = _pubchem_table({"Lincomycin": definiert, variante: flach})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name("Lincomycin") == definiert


@pytest.mark.parametrize("name", ["L-Naloxon", "D-Naloxon", "DL-Naloxon", "l-Naloxon"])
def test_stereo_form_rule_skips_d_l_prefixed_names(name):
    """Ein D-/L-Präfix legt die Form im Namen fest — dort tauscht die Regel nicht."""
    _, direkt, definiert = _STEREO_FORM["Naloxon"]
    with patch("chemdraw_tool.resolver._spelling_variant", return_value="Naloxone"), \
         patch("chemdraw_tool.resolver._pubchem_lookup", return_value=definiert):
        assert resolver._pubchem_checked(name, direkt, []) == (direkt, name)


@pytest.mark.parametrize("name", ["Buspiron", "Spironolacton", "Tandospiron", "Bendamustin",
                                  "Phenelzin", "Salbutamol", "Ameisensäure"])
def test_salt_word_needs_a_whole_word_for_iron_zinc_salt(name):
    """"-iron" (Buspiron, Spironolacton) ist kein Eisen — sonst blockiert der
    Schutz die Salzregel für jeden solchen INN."""
    assert not resolver._SALT_WORD.search(name)


@pytest.mark.parametrize("name", [
    "Bendamustinhydrochlorid", "bendamustine hydrochloride", "Phenelzinsulfat",
    "Natriumcitrat", "sodium citrate", "Kaliumcitrat", "Docusat-Natrium",
    "Eisengluconat", "iron sucrose", "zinc oxide",
])
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_name_with_salt_word_keeps_the_salt(_opsin, name):
    """Nennt der Name das Gegenion, ist das Salz gemeint — auch wenn die
    Variante (zufällig) die freie Form trifft."""
    salz = "CN1C2=C(C=C(C=C2)N(CCCl)CCCl)N=C1CCCC(=O)O.Cl"
    frei = "CN1C2=C(C=C(C=C2)N(CCCl)CCCl)N=C1CCCC(=O)O"
    variante = resolver._spelling_variant(name)
    table = {name: salz}
    if variante:
        table[variante] = frei
    lookup, _ = _pubchem_table(table)
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolve_name(name) == salz


# --- Deutsche Salznamen (06.11.2026) ------------------------------------------
# "Bendamustinhydrochlorid" fand keine Quelle (PubChem 404, NCI 500), weil die
# englische Variante "Bendamustinhydro chloride" lautete. Mit dem ganzen
# Gegenion trifft "Bendamustine hydrochloride" das Salz (CID 77082) — echte
# PubChem-Antwort vom 06.11.2026. Der Umweg erscheint als found_as.
_BENDAMUSTIN_HCL = "CN1C2=C(C=C(C=C2)N(CCCl)CCCl)N=C1CCCC(=O)O.Cl"


@pytest.mark.parametrize("name", ["Bendamustinhydrochlorid", "Bendamustin Hydrochlorid",
                                  "Bendamustin-Hydrochlorid"])
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_german_salt_name_resolves_to_the_salt(_nci, _opsin, name):
    lookup, calls = _only_for("Bendamustine hydrochloride", _BENDAMUSTIN_HCL)
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolver.resolve_name_route(name) == (_BENDAMUSTIN_HCL, "Bendamustine hydrochloride")
    assert calls == [name, "Bendamustine hydrochloride"]


# "Cefalotin-Natrium": PubChem kennt "Cefalotin sodium", nicht "Cefalotine
# sodium" (echte Antworten 06.11.2026). Nach der englischen Variante fragt die
# Kaskade deshalb einmal die Salzvariante (Stamm unverändert, Gegenion englisch).
_CEFALOTIN_NA = "CC(=O)OCC1=C(N2[C@@H]([C@@H](C2=O)NC(=O)CC3=CC=CS3)SC1)C(=O)[O-].[Na+]"


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_salt_variant_comes_after_the_english_variant(_nci, _opsin):
    lookup, calls = _only_for("Cefalotin sodium", _CEFALOTIN_NA)
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolver.resolve_name_route("Cefalotin-Natrium") == (_CEFALOTIN_NA, "Cefalotin sodium")
    assert calls == ["Cefalotin-Natrium", "Cefalotine sodium", "Cefalotin sodium"]


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_name_without_counterion_asks_no_salt_variant(_nci, _opsin):
    lookup, calls = _only_for("nothing")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        with pytest.raises(NameResolutionError):
            resolve_name("Dexamethason")
    assert calls == ["Dexamethason", "Dexamethasone"]


# --- „found as": der Umweg wird sichtbar (Folgepunkt Masse-Eval, 06.11.2026) --
# Löst resolve_name einen Namen nicht wörtlich, sondern über eine andere
# Schreibweise auf, nennt das Ergebnis diese Schreibweise — so lässt sich ein
# falscher Treffer erkennen. Wörtliche Treffer bleiben ohne Hinweis.


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_found_as_names_the_english_variant(_nci, _opsin):
    lookup, _ = _only_for("Dexamethasone")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        route = resolver.resolve_name_route("Dexamethason")
    assert route == ("CC(=O)O", "Dexamethasone")


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_found_as_names_the_transliteration(_nci, _opsin):
    lookup, _ = _only_for("Maleinsaeure")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolver.resolve_name_route("Maleinsäure").found_as == "Maleinsaeure"


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_found_as_names_the_transliteration_via_nci(_opsin):
    lookup, _ = _only_for("nothing")

    def nci(name, report=None):
        return "CC(=O)O" if name == "Maleinsaeure" else None

    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup), \
         patch("chemdraw_tool.resolver._nci_cir_lookup", side_effect=nci):
        assert resolver.resolve_name_route("Maleinsäure").found_as == "Maleinsaeure"


@pytest.mark.parametrize("name", sorted(_SALZFORM))
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_found_as_names_the_variant_of_the_salt_rule(_opsin, name):
    variante, direkt, frei = _SALZFORM[name]
    lookup, _ = _pubchem_table({name: direkt, variante: frei})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolver.resolve_name_route(name) == (frei, variante)


@pytest.mark.parametrize("name", sorted(_SYNONYMFEHLER))
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_found_as_names_the_variant_that_overruled_a_synonym(_opsin, name):
    variante, direkt, richtig = _SYNONYMFEHLER[name]
    lookup, _ = _pubchem_table({name: direkt, variante: richtig})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolver.resolve_name_route(name).found_as == variante


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
def test_literal_hit_has_no_found_as(_opsin):
    """Direkttreffer, Variante bestätigt nur → kein Hinweis (Procain bleibt Procain)."""
    lookup, _ = _pubchem_table({"Procain": "CCN(CC)CCOC(=O)C1=CC=C(C=C1)N",
                                "Procaine": "NC1=CC=C(C=C1)C(=O)OCCN(CC)CC"})
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolver.resolve_name_route("Procain").found_as == ""
        assert resolver.resolve_name_route("risperidone").found_as == ""


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_found_as_ignores_a_pure_case_difference(_nci, _opsin):
    lookup, _ = _only_for("Dexamethasone")
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolver._found_as("dexamethasone", "Dexamethasone") == ""


def test_resolve_carries_found_as_and_stays_a_pair(monkeypatch):
    monkeypatch.setattr(resolver, "resolve_name_route",
                        lambda n: resolver.Resolution("CCO", "Ethanol"))
    result = resolver.resolve("Äthanol")
    smiles, mol = result  # alle übrigen Aufrufer entpacken weiter zwei Werte
    assert (smiles, result.found_as) == ("CCO", "Ethanol") and mol is not None
    assert resolver.resolve("CCO").found_as == ""


# --- rifabutin + (S)-(−)-timolol (Lauf 9, 06.11.2026) ----------------------
# Echte PubChem-Antworten 06.11.2026: "rifabutin" und "rifabutine" liefern zwei
# Tautomere desselben Stoffs (Imidazolin-NH an anderer Stelle, gleiche
# InChI-Formel + /c-Schicht, gleicher RDKit-Kanontautomer). Die Standard-InChI
# führt diese Tautomerie nicht zusammen — erster Key-Block AZFB… vs. ZWBT….
# Die Gegenprobe darf das nicht als zweiten Stoff lesen: sonst kippt sie auf
# die Variante und meldet „found as rifabutine".
_RIFABUTIN_PC = (
    "C[C@H]1/C=C/C=C(\\C(=O)NC2=C(C3=C(C4=C(C(=C3O)C)O[C@@](C4=O)(O/C=C/[C@@H]([C@H]"
    "([C@H]([C@@H]([C@@H]([C@@H]([C@H]1O)C)O)C)OC(=O)C)C)OC)C)C5=NC6(CCN(CC6)CC(C)C)"
    "N=C25)O)/C"
)
_RIFABUTIN_PC_E = (
    "C[C@H]1/C=C/C=C(\\C(=O)N=C2C(=C3C(=C4C2=NC5(N4)CCN(CC5)CC(C)C)C6=C(C(=C3O)C)"
    "O[C@@](C6=O)(O/C=C/[C@@H]([C@H]([C@H]([C@@H]([C@@H]([C@@H]([C@H]1O)C)O)C)"
    "OC(=O)C)C)OC)C)O)/C"
)


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_tautomer_of_the_variant_is_not_another_compound(_nci, _opsin):
    answers = {"rifabutin": _RIFABUTIN_PC, "rifabutine": _RIFABUTIN_PC_E}
    with patch("chemdraw_tool.resolver._pubchem_lookup",
               side_effect=lambda n, report=None: answers.get(n)):
        assert resolver.resolve_name_route("rifabutin") == (_RIFABUTIN_PC, "")


def test_parent_skeleton_still_separates_constitutional_isomers():
    """Gegenprobe zur Lockerung: Propanol-1 und -2 haben dieselbe Formel."""
    assert resolver._parent_skeleton("CCCO") != resolver._parent_skeleton("CC(C)O")


# "(S)-(−)-timolol": OPSIN None, PubChem 404, NCI 500 (echte Antworten
# 06.11.2026) — die Kette aus Deskriptor und Drehsinn kennt keine Quelle,
# "(S)-timolol" trifft. Der Drehsinn ist neben R/S redundant; R/S bleibt, denn
# ohne ihn liefert PubChem für "(R)-X" das andere Enantiomer oder das Racemat.
_S_TIMOLOL = "CC(C)(C)NC[C@@H](COC1=NSN=C1N2CCOCC2)O"


@pytest.mark.parametrize("name", ["(S)-(−)-timolol", "(S)-(-)-timolol"])
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_rotation_sign_beside_a_descriptor_is_dropped_last(_nci, _opsin, name):
    lookup, calls = _only_for("(S)-timolol", _S_TIMOLOL)
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        assert resolver.resolve_name_route(name) == (_S_TIMOLOL, "(S)-timolol")
    assert calls[-1] == "(S)-timolol"


@pytest.mark.parametrize("name", ["(−)-timolol", "(+)-Ephedrin"])
@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_rotation_sign_alone_is_never_dropped(_nci, _opsin, name):
    """Ohne R/S trägt der Drehsinn die einzige Stereoangabe."""
    lookup, calls = _only_for("timolol", _S_TIMOLOL)
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        with pytest.raises(NameResolutionError):
            resolve_name(name)
    assert "timolol" not in calls


@patch("chemdraw_tool.resolver._opsin_lookup", return_value=None)
@patch("chemdraw_tool.resolver._nci_cir_lookup", return_value=None)
def test_r_descriptor_never_lands_on_the_s_record(_nci, _opsin):
    """'(R)-(+)-x' fragt '(R)-x', nie das nackte 'x' (dort läge das S-Enantiomer)."""
    lookup, calls = _only_for("timolol", _S_TIMOLOL)
    with patch("chemdraw_tool.resolver._pubchem_lookup", side_effect=lookup):
        with pytest.raises(NameResolutionError):
            resolve_name("(R)-(+)-timolol")
    assert calls[-1] == "(R)-timolol"
    assert "timolol" not in calls


# Form-Zusätze: nur die gemessene Whitelist, und erst nach erfolglosem Original.
@pytest.mark.parametrize("name,base", [
    ("Citral A+B", "Citral"),
    ("Cefixim Anhydrat", "Cefixim"),
    ("Metamizol (freie Säure)", "Metamizol"),
])
def test_form_suffix_retries_the_complete_cascade_and_marks_found_as(monkeypatch, name, base):
    calls = []
    def opsin(query):
        calls.append(query)
        return "CCO" if query == base else None
    monkeypatch.setattr(resolver, "_opsin_lookup", opsin)
    monkeypatch.setattr(resolver, "_pubchem_lookup", lambda *args: None)
    monkeypatch.setattr(resolver, "_nci_cir_lookup", lambda *args: None)
    assert resolver.resolve_name_route(name) == ("CCO", base)
    assert calls == [name, base]


def test_form_suffix_never_replaces_an_original_hit(monkeypatch):
    opsin = Mock(return_value="CCO")
    monkeypatch.setattr(resolver, "_opsin_lookup", opsin)
    pubchem = Mock(side_effect=lambda query, report: "CCN" if query == "Citral" else None)
    monkeypatch.setattr(resolver, "_pubchem_lookup", pubchem)
    assert resolver.resolve_name_route("Citral A+B") == ("CCO", "")
    opsin.assert_called_once_with("Citral A+B")
    # Die vorhandene OPSIN-Gegenprobe darf den Originalnamen fragen, aber keine Kurzform.
    pubchem.assert_called_once_with("Citral A+B", [])


@pytest.mark.parametrize("name", ["Citral (Gemisch)", "Citral A+C", "Citral Trihydrat"])
def test_unknown_form_suffix_does_not_retry_the_base(monkeypatch, name):
    opsin = Mock(side_effect=lambda query: "CCO" if query == "Citral" else None)
    monkeypatch.setattr(resolver, "_opsin_lookup", opsin)
    monkeypatch.setattr(resolver, "_pubchem_lookup", lambda *args: None)
    monkeypatch.setattr(resolver, "_nci_cir_lookup", lambda *args: None)
    with pytest.raises(NameResolutionError):
        resolver.resolve_name_route(name)
    opsin.assert_called_once_with(name)


def test_form_suffix_keeps_descriptor_and_rotation_in_the_base_name(monkeypatch):
    original = "(R)-(+)-timolol Anhydrat"
    base = "(R)-(+)-timolol"
    calls = []
    def opsin(query):
        calls.append(query)
        return "CC[C@H](O)C" if query == base else None
    monkeypatch.setattr(resolver, "_opsin_lookup", opsin)
    monkeypatch.setattr(resolver, "_pubchem_lookup", lambda *args: None)
    monkeypatch.setattr(resolver, "_nci_cir_lookup", lambda *args: None)
    assert resolver.resolve_name_route(original) == ("CC[C@H](O)C", base)
    assert calls == [original, base]


def test_form_suffix_is_not_shortened_to_vet_conflicting_original_hits(monkeypatch):
    # Die bestehende Gegenprobe zwischen OPSIN und PubChem bleibt beim Original.
    monkeypatch.setattr(resolver, "_opsin_lookup", lambda name: "CCO")
    lookup = Mock(side_effect=lambda name, report: "CCN" if name == "Citral A+B" else "CCO")
    monkeypatch.setattr(resolver, "_pubchem_lookup", lookup)
    assert resolver.resolve_name_route("Citral A+B") == ("CCN", "")
    lookup.assert_called_once_with("Citral A+B", [])


# Zweiatomige Elemente (Befund 09.11.2026, auch in 0.9.0): OPSIN liest
# "oxygen" als Atom [O] und wird für kohlenstofffreie Treffer nicht gegen
# PubChem geprüft; "Stickstoff" ist bei PubChem [NH] (CID 5460607), "Iod"
# kennt PubChem nicht und NCI liefert Iodid. Die Attrappen geben genau diese
# gemessenen Fehlantworten zurück.
_MEASURED_OPSIN = {
    "nitrogen": "[N]", "oxygen": "[O]", "fluorine": "[F]", "chlorine": "[Cl]",
    "bromine": "[Br]", "iodine": "[I]",
    "sodium": "[Na]", "Natrium": "[Na]", "iron": "[Fe]", "ozone": "O=[O+][O-]",
}
_MEASURED_PUBCHEM = {
    "hydrogen": "[HH]", "nitrogen": "N#N", "oxygen": "O=O", "fluorine": "FF",
    "chlorine": "ClCl", "bromine": "BrBr", "iodine": "II",
    "Wasserstoff": "[HH]", "Stickstoff": "[NH]", "Sauerstoff": "O=O",
    "Fluor": "FF", "Chlor": "ClCl", "Brom": "BrBr", "Jod": "II",
    "sodium": "[Na]", "Natrium": "[Na]", "iron": "[Fe]",
    "ozone": "[O-][O+]=O", "oxygen atom": "O",
}
_MEASURED_NCI = {"Iod": "[I-]"}


@pytest.fixture
def _measured_sources(monkeypatch):
    monkeypatch.setattr(resolver, "_opsin_lookup", lambda name: _MEASURED_OPSIN.get(name))
    monkeypatch.setattr(resolver, "_pubchem_lookup",
                        lambda name, report=None: _MEASURED_PUBCHEM.get(name))
    monkeypatch.setattr(resolver, "_nci_cir_lookup",
                        lambda name, report=None: _MEASURED_NCI.get(name))


def _canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


@pytest.mark.parametrize(("name", "expected"), [
    ("hydrogen", "[H][H]"), ("nitrogen", "N#N"), ("oxygen", "O=O"),
    ("fluorine", "FF"), ("chlorine", "ClCl"), ("bromine", "BrBr"), ("iodine", "II"),
    ("Wasserstoff", "[H][H]"), ("Stickstoff", "N#N"), ("Sauerstoff", "O=O"),
    ("Fluor", "FF"), ("Chlor", "ClCl"), ("Brom", "BrBr"), ("Iod", "II"), ("Jod", "II"),
    ("Oxygen", "O=O"), (" chlorine ", "ClCl"),
])
def test_diatomic_element_names_resolve_to_the_molecule(_measured_sources, name, expected):
    assert _canonical(resolve(name)[0]) == _canonical(expected)


@pytest.mark.parametrize("name", ["hydrogen", "Wasserstoff"])
def test_hydrogen_is_drawn_as_two_atoms_with_a_bond(_measured_sources, name):
    """„[HH]“ ist EIN Atom mit einem impliziten H — die Zeichnung zeigte „HH“
    statt H–H (Desktop-Handtest 10.11.2026). Zwei Atome, eine Bindung."""
    mol = resolve(name)[1]
    assert (mol.GetNumAtoms(), mol.GetNumBonds()) == (2, 1)


@pytest.mark.parametrize(("name", "expected"), [
    ("sodium", "[Na]"), ("Natrium", "[Na]"), ("iron", "[Fe]"),
    ("ozone", "O=[O+][O-]"),
])
def test_other_element_names_keep_their_source_answer(_measured_sources, name, expected):
    assert resolve(name)[0] == expected


# Einzelatome (Messung 10.11.2026, OPSIN mit Java aktiv): OPSIN kennt
# "oxygen atom"/"atomic oxygen" nicht (None). PubChem führt "oxygen atom" als
# Synonym von Wasser (CID 962 → O), "hydrogen atom" als [1HH] und "atomic
# hydrogen" als [HH] — dreimal ein Molekül statt des Atoms. Die übrigen
# Kombinationen liefert PubChem schon heute als Atom ([O], [N], [Cl], [F], [Br],
# [I]); die Regel macht das ohne Netz und für alle sieben Elemente gleich.
@pytest.mark.parametrize(("name", "expected"), [
    ("oxygen atom", "[O]"), ("atomic oxygen", "[O]"),
    ("hydrogen atom", "[H]"), ("atomic hydrogen", "[H]"),
    ("nitrogen atom", "[N]"), ("atomic nitrogen", "[N]"),
    ("chlorine atom", "[Cl]"), ("atomic chlorine", "[Cl]"),
    ("fluorine atom", "[F]"), ("bromine atom", "[Br]"), ("iodine atom", "[I]"),
    ("Oxygen Atom", "[O]"), ("  atomic  oxygen ", "[O]"),
])
def test_atom_names_resolve_to_the_single_atom_without_any_lookup(monkeypatch, name, expected):
    def forbidden(*args, **kwargs):
        raise AssertionError("Atomname darf keine Quelle befragen")
    for source in ("_opsin_lookup", "_pubchem_lookup", "_nci_cir_lookup"):
        monkeypatch.setattr(resolver, source, forbidden)
    assert resolve(name)[0] == expected


@pytest.mark.parametrize("name", ["oxygen atoms", "sodium atom", "atomic mass", "oxygen atom transfer"])
def test_atom_rule_stays_narrow(_measured_sources, name):
    """Nur Element der Tabelle + "atom" bzw. "atomic" + Element, sonst die Kaskade."""
    assert resolver._ATOMIC_ELEMENTS.get(resolver._atom_phrase_key(name)) is None


@pytest.mark.parametrize("smiles", ["O", "[O]", "O=O", "[Cl]"])
def test_element_smiles_stay_smiles_without_any_lookup(monkeypatch, smiles):
    def forbidden(*args, **kwargs):
        raise AssertionError("SMILES darf keine Quelle befragen")
    for source in ("_opsin_lookup", "_pubchem_lookup", "_nci_cir_lookup"):
        monkeypatch.setattr(resolver, source, forbidden)
    assert resolve(smiles)[0] == smiles
