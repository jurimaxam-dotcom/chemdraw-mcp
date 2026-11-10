"""E12: Ein eingegebenes SMILES verlässt den Rechner standardmäßig nie.

Zielgruppe sind Doktoranden mit unveröffentlichten Strukturen (Jay 10.11.2026,
„Weg 1“). Der Test fängt JEDEN HTTP-Aufruf auf `requests`-Ebene ab
(`Session.send` — darüber laufen auch `requests.get/post` und die eigene
IPv4-Session des NCI-Wegs) und sperrt Sockets als Rückfallnetz. Für jedes Tool,
das eine Struktur annimmt, wird ein Fantasie-SMILES eingegeben und geprüft, dass
weder das SMILES (wie eingegeben, kanonisch, Kekulé) noch der InChI in URL oder
Body steht. Der InChIKey darf vorkommen: er ist ein Hash, aus dem sich die
Struktur nicht zurückrechnen lässt.

Zwei Netz-Szenarien: PubChem kennt den Schlüssel nicht (alles 404 → genau dann
griff früher der SMILES-POST) und PubChem kennt ihn (Folgeaufrufe mit Titel/CID).
Die Positivkontrolle mit Opt-in beweist, dass der Detektor anschlägt.
"""

from __future__ import annotations

import json
import socket
from urllib.parse import unquote_plus

import pytest
import requests
from rdkit import Chem

from chemdraw_tool import resolver
from chemdraw_tool import server as srv

# Beim Import festgehalten, bevor die autouse-Attrappen aus conftest greifen:
# genau diese Wege (UniProt-Nachfrage, NCI-Session) soll der Abfang sehen.
_ECHTER_PROTEIN_LOOKUP = resolver._protein_lookup
_ECHTES_NCI_GET = resolver._nci_get
_ECHTER_GEN_LOOKUP = resolver._gene_lookup

# Fantasie-Strukturen: es gibt sie (Stand 10.11.2026) in keiner Datenbank.
BROMID = "N#Cc1ccc(nc1)C1(CBr)CC2(C1)OCC(F)(F)CO2"
ALKOHOL = "N#Cc1ccc(nc1)C1(CO)CC2(C1)OCC(F)(F)CO2"
AMID = "O=C(NC1CC2(C1)CC(F)(F)C2)c1cnc(Cl)c(OC(F)F)c1"
CHIRAL = "N#Cc1ccc(nc1)C(F)C1CC2(C1)OCC(F)(F)CO2"  # ein unbestimmtes Stereozentrum
STRUKTUREN = (BROMID, ALKOHOL, AMID, CHIRAL)

_ENV = "CHEMDRAW_SMILES_LOOKUP"


def _nadeln(smiles: str) -> set[str]:
    """Alles, woraus sich die Struktur zurückgewinnen lässt — nicht der InChIKey."""
    mol = Chem.MolFromSmiles(smiles)
    kekule = Chem.Mol(mol)
    Chem.Kekulize(kekule, clearAromaticFlags=True)
    inchi = Chem.MolToInchi(mol)
    return {
        smiles,
        Chem.MolToSmiles(mol),
        Chem.MolToSmiles(kekule, kekuleSmiles=True),
        inchi,
        inchi.removeprefix("InChI=1S/"),
    }


NADELN = set().union(*(_nadeln(s) for s in STRUKTUREN))
SCHLUESSEL = {Chem.MolToInchiKey(Chem.MolFromSmiles(s)) for s in STRUKTUREN}


class Abfang:
    """Zeichnet jeden HTTP-Aufruf auf und antwortet wie PubChem & Co."""

    def __init__(self, bekannt: bool):
        self.bekannt = bekannt
        self.aufrufe: list[tuple[str, str, str]] = []
        self.sockets: list[str] = []

    def antwort(self, request) -> requests.Response:
        body = request.body or ""
        if isinstance(body, bytes):
            body = body.decode("utf-8", "replace")
        self.aufrufe.append((request.method, unquote_plus(request.url), unquote_plus(body)))
        status, payload = 404, {"Fault": {"Code": "PUGREST.NotFound"}}
        url = request.url
        if self.bekannt and "/compound/inchikey/" in url:
            key = url.split("/compound/inchikey/")[1].split("/")[0]
            if key in SCHLUESSEL:
                status = 200
                if "/synonyms/" in url:
                    payload = {"InformationList": {"Information": [
                        {"CID": 999999001, "Synonym": ["Fantasy compound", "50-00-0"]}
                    ]}}
                else:
                    payload = {"PropertyTable": {"Properties": [{
                        "CID": 999999001, "Title": "Fantasy compound",
                        "MolecularFormula": "C1", "MolecularWeight": "1.0", "InChIKey": key,
                    }]}}
        r = requests.Response()
        r.status_code = status
        r.url = request.url
        r.request = request
        r.headers["Content-Type"] = "application/json"
        r._content = json.dumps(payload).encode()
        return r

    def lecks(self) -> list[str]:
        return [
            f"{m} {u} body={b[:200]!r} enthält {n!r}"
            for m, u, b in self.aufrufe
            for n in NADELN
            if n in u or n in b
        ]


@pytest.fixture(params=[False, True], ids=["pubchem-kennt-nichts", "pubchem-kennt-den-schluessel"])
def abfang(request, monkeypatch, tmp_path):
    fang = Abfang(bekannt=request.param)
    monkeypatch.setattr(requests.Session, "send", lambda self, req, **kw: fang.antwort(req))

    def kein_socket(*args, **kwargs):
        fang.sockets.append(repr(args[1:] or kwargs))
        raise OSError("Socket im Abfang-Test gesperrt")

    monkeypatch.setattr(socket.socket, "connect", kein_socket)
    monkeypatch.setattr(socket, "create_connection", kein_socket)
    # Die autouse-Attrappen aus conftest zurücknehmen: der Abfang soll sehen,
    # was der echte Code verschickt.
    monkeypatch.setattr(resolver, "_protein_lookup", _ECHTER_PROTEIN_LOOKUP)
    monkeypatch.setattr(resolver, "_nci_get", _ECHTES_NCI_GET)
    monkeypatch.setattr(resolver, "_gene_lookup", _ECHTER_GEN_LOOKUP)
    monkeypatch.setattr(srv, "_TITLE_CACHE", {})
    for const in ("OUTPUT_DIR", "REACTION_DIR", "SPECTRUM_DIR", "TLC_DIR", "SCOPE_DIR",
                  "ANKI_DIR", "PLOT_DIR", "THREED_DIR", "PROTEIN_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())
    monkeypatch.delenv(_ENV, raising=False)
    yield fang
    assert not fang.sockets, f"am requests-Abfang vorbei ins Netz: {fang.sockets[:3]}"


def _inchi(smiles: str) -> str:
    return Chem.MolToInchi(Chem.MolFromSmiles(smiles))


AUFRUFE = {
    "generate_molecule": lambda: srv.generate_molecule(BROMID),
    "generate_molecule(InChI)": lambda: srv.generate_molecule(_inchi(BROMID)),
    "generate_molecule(CXSMILES)": lambda: srv.generate_molecule(AMID + " |$;;;;;;;;;;;;;;;;;;;;;;$|"),
    "batch_generate": lambda: srv.batch_generate([BROMID, AMID]),
    "compare_molecules": lambda: srv.compare_molecules([BROMID, ALKOHOL]),
    "generate_reaction": lambda: srv.generate_reaction([BROMID, "[OH-]"], [ALKOHOL, "[Br-]"]),
    "generate_mechanism": lambda: srv.generate_mechanism("sn2", [BROMID, "[OH-]"]),
    "generate_3d": lambda: srv.generate_3d(AMID),
    "predict_spectrum(ir)": lambda: srv.predict_spectrum("ir_bands", AMID),
    "predict_spectrum(nmr)": lambda: srv.predict_spectrum("nmr_signals", AMID),
    "export_anki_deck": lambda: srv.export_anki_deck(
        deck_name="E12 probe",
        cards=[{"front": {"structure": BROMID}, "back": {"text": "fantasy"}}],
    ),
    "lookup_molecule_data": lambda: srv.lookup_molecule_data(AMID),
    **{
        f"lookup({topic})": (lambda topic=topic: srv.lookup(AMID, topic))
        for topic in ("properties", "safety", "physical", "biochem", "pathway")
    },
    "lookup(properties, InChI)": lambda: srv.lookup(_inchi(AMID), "properties"),
    "generate_molecule(stereo_variants)": lambda: srv.generate_molecule(CHIRAL, stereo_variants=True),
    "generate_molecule(view=all_h)": lambda: srv.generate_molecule(BROMID, view="all_h"),
    "generate_scope_table": lambda: srv.generate_scope_table(
        entries=[{"label": "1a", "structure": AMID}, {"label": "1b", "structure": ALKOHOL}],
        reaction={"reactants": [BROMID], "products": [ALKOHOL], "conditions": "NaOH"},
    ),
    # Schreibweisen, die RDKit als Ganzes nicht liest, die aber erkennbar eine
    # Struktur sind: nie in die Namenskaskade (E12, Advisor-Befund).
    "generate_molecule(SMILES + Etikett)": lambda: srv.generate_molecule(BROMID + " batch-7"),
    "generate_molecule((S)- + SMILES)": lambda: srv.generate_molecule("(S)-" + BROMID),
    "lookup(SMILES + Etikett)": lambda: srv.lookup(AMID + " batch-7", "biochem"),
    "generate_molecule(Etikett + SMILES)": lambda: srv.generate_molecule("batch-7 " + BROMID),
    # E8: Protein-Weg. Genkürzel + "Organismus" geht als Organismusfilter an
    # UniProt — ein SMILES an dieser Stelle darf dort nicht ankommen.
    "generate_molecule(Genkürzel + SMILES)": lambda: srv.generate_molecule("RecA " + BROMID),
    "generate_3d(Genkürzel + SMILES)": lambda: srv.generate_3d("LipA " + AMID),
    "lookup(Genkürzel + SMILES)": lambda: srv.lookup("RecA from " + AMID, "biochem"),
    "generate_3d(Protein + SMILES)": lambda: srv.generate_3d("lysozyme " + BROMID),
    # 10.11.2026: eigener Protein-Eingang — dieselbe Regel wie generate_molecule.
    "generate_protein_or_antibody": lambda: srv.generate_protein_or_antibody(AMID),
    "generate_protein_or_antibody(Genkürzel + SMILES)": lambda: srv.generate_protein_or_antibody("RecA " + BROMID),
    "generate_protein_or_antibody(Protein + SMILES)": lambda: srv.generate_protein_or_antibody("lysozyme " + BROMID),
}

# Reaktions-SMILES: ein klarer Fehler statt einer Namenssuche.
UNLESBAR = {
    "generate_molecule(Reaktions-SMILES)": lambda: srv.generate_molecule(BROMID + ">>" + ALKOHOL),
    "lookup(Reaktions-SMILES)": lambda: srv.lookup(BROMID + ">>" + ALKOHOL, "biochem"),
}


@pytest.mark.parametrize("name", list(AUFRUFE))
def test_kein_smiles_und_kein_inchi_im_netzverkehr(abfang, name):
    try:
        AUFRUFE[name]()
    except (resolver.NameResolutionError, ValueError):
        pass  # ein klarer Fehler ist erlaubt — nur hinausgehen darf nichts
    assert not abfang.lecks(), "\n".join(abfang.lecks())


def test_lookup_peptidsequenz_geht_nicht_als_name_hinaus(abfang):
    """Eine baubare Sequenz ist eine Struktur wie in resolve(): nur ihr InChIKey geht hinaus."""
    sequenz = "Trp-Phe-Ser-Gly-Ala"
    srv.lookup(sequenz, "biochem")
    assert abfang.aufrufe, "gar nicht gefragt — der Test prüft dann nichts"
    assert not any(sequenz in u or sequenz in b for _, u, b in abfang.aufrufe), abfang.aufrufe


@pytest.mark.parametrize("name", list(UNLESBAR))
def test_reaktions_smiles_geht_nicht_hinaus(abfang, name):
    try:
        text = UNLESBAR[name]()
    except resolver.NameResolutionError as exc:
        assert exc.kind == "invalid_smiles"
        assert "generate_reaction" in str(exc)
    else:
        assert "not sent" in text and "generate_reaction" in text
    assert not abfang.lecks(), "\n".join(abfang.lecks())
    assert not any(BROMID in u or BROMID in b for _, u, b in abfang.aufrufe)


@pytest.mark.parametrize("wert", ["", "0", "false", "no", "off", "${user_config.smiles_lookup}"])
def test_aus_werte_lassen_den_schutz_an(abfang, monkeypatch, wert):
    monkeypatch.setenv(_ENV, wert)
    srv.generate_molecule(BROMID)
    srv.lookup(AMID, "properties")
    assert not abfang.lecks(), "\n".join(abfang.lecks())


@pytest.mark.parametrize("wert", ["1", "true", "TRUE", "yes", "on"])
def test_opt_in_stellt_den_alten_weg_wieder_her(abfang, monkeypatch, wert):
    """Positivkontrolle: mit Opt-in geht das SMILES hinaus — der Detektor lebt."""
    monkeypatch.setenv(_ENV, wert)
    srv.lookup(AMID, "properties")
    assert any(AMID in u for _, u, _ in abfang.aufrufe), abfang.aufrufe
    if not abfang.bekannt:
        srv.generate_molecule(BROMID)
        posts = [b for m, _, b in abfang.aufrufe if m == "POST"]
        assert any(BROMID in b for b in posts), abfang.aufrufe


def test_der_inchikey_darf_hinaus(abfang):
    srv.generate_molecule(BROMID)
    key = Chem.MolToInchiKey(Chem.MolFromSmiles(BROMID))
    assert any(key in u for _, u, _ in abfang.aufrufe), abfang.aufrufe


# --- Was der Nutzer ohne Opt-in sieht -----------------------------------------


def test_lookup_ohne_treffer_sagt_was_lokal_lief_und_wie_man_einschaltet(abfang):
    if abfang.bekannt:
        pytest.skip("nur sinnvoll, wenn PubChem den Schlüssel nicht kennt")
    text = srv.lookup(AMID, "safety")
    key = Chem.MolToInchiKey(Chem.MolFromSmiles(AMID))
    assert "Read as a structure" in text
    assert key in text
    assert "C14H13ClF4N2O2" in text  # lokal gerechnet
    assert "not sent to any database" in text
    assert _ENV + "=1" in text
    assert "extension settings of Claude Desktop" in text


def test_lookup_mit_treffer_nennt_den_weg(abfang):
    if not abfang.bekannt:
        pytest.skip("nur sinnvoll, wenn PubChem den Schlüssel kennt")
    text = srv.lookup(AMID, "properties")
    assert "999999001" in text
    assert "The structure itself was not sent" in text


def test_wasser_bleibt_wasser_in_den_zeichenwerkzeugen(abfang):
    """Parse-first in resolve() unverändert: "O" ist Wasser, "CCC" Propan."""
    assert srv.generate_molecule("O").properties["formula"] == "H2O"
    assert srv.generate_molecule("CCC").properties["formula"] == "C3H8"


# Nachauftrag 1: kurze reine Buchstabenfolgen sind in `lookup` Namen (Akronyme,
# Genkürzel). Gemessen 10.11.2026: 37 von 49 Biochemie-Akronymen sind als SMILES
# lesbar, alle mit 2–4 Zeichen (NOS, PC, CBS, PNP, INS, FOS, PCOS, FCCP …); ein
# reines Buchstaben-SMILES bis 5 Zeichen ist höchstens Pentan/Diethylether/
# 1,3-Propandiol — nichts Vertrauliches.
AKRONYME = ["NO", "PC", "NOS", "CBS", "PNP", "INS", "FOS", "PCOS", "FCCP", "CCCCC"]
GENKUERZEL = ["LipA", "TrpA", "MiaB", "RecA", "GroEL", "LacZ", "Ac", "Bn", "Co", "Sn"]


@pytest.mark.parametrize("name", AKRONYME + GENKUERZEL)
def test_kurze_buchstabenfolgen_gehen_in_lookup_als_name(abfang, name):
    srv.lookup(name, "biochem")
    assert any(f"q={name}&" in u or f"query={name}" in u for _, u, _ in abfang.aufrufe), abfang.aufrufe


@pytest.mark.parametrize("name", GENKUERZEL)
def test_genkuerzel_sind_nie_eine_struktur(name):
    from rdkit import rdBase

    with rdBase.BlockLogs():
        assert resolver.parse_smiles_input(name) is None
        assert resolver.structure_notation(name) is None
    assert srv._typed_structure(name) is None


@pytest.mark.parametrize("smiles", ["CCCCCC", "OCCOCCO", "CC(C)O", "C=O"])
def test_ab_sechs_zeichen_oder_mit_smiles_zeichen_bleibt_es_struktur(abfang, smiles):
    srv.lookup(smiles, "biochem")
    assert not any(smiles in u for _, u, _ in abfang.aufrufe), abfang.aufrufe


def test_namen_gehen_weiter_als_namen_hinaus(abfang):
    srv.lookup("Aspirin", "properties")
    assert any("/compound/name/Aspirin/" in u for _, u, _ in abfang.aufrufe)


def test_datenblatt_hinweis_warum_cas_fehlt(abfang, monkeypatch):
    if abfang.bekannt:
        pytest.skip("nur sinnvoll, wenn PubChem den Schlüssel nicht kennt")
    payload = srv.generate_molecule(BROMID)
    assert "not sent" in payload.properties["lookupNote"]
    assert payload.properties["formula"] == "C14H13BrF2N2O2"
    monkeypatch.setenv(_ENV, "1")
    assert "lookupNote" not in srv.generate_molecule(BROMID).properties


def test_datenblatt_ohne_hinweis_wenn_pubchem_den_schluessel_kennt(abfang):
    if not abfang.bekannt:
        pytest.skip("nur sinnvoll, wenn PubChem den Schlüssel kennt")
    assert "lookupNote" not in srv.generate_molecule(BROMID).properties


def test_kaputter_inchi_geht_nicht_in_die_namenskaskade(abfang):
    with pytest.raises(resolver.NameResolutionError) as info:
        srv.generate_molecule("InChI=1S/C14H13ClF4N2O2/c15-garbage")
    assert info.value.kind == "invalid_smiles"
    assert abfang.aufrufe == []


# --- Sichtbarkeit: server.log und chemdraw-doctor -------------------------------


def test_server_log_vermerkt_den_zustand_beim_start(monkeypatch, caplog):
    import logging

    monkeypatch.setattr(srv, "_configure_logging", lambda log_dir: None)
    monkeypatch.setattr(srv.mcp, "run", lambda **kw: None)
    monkeypatch.delenv(_ENV, raising=False)
    with caplog.at_level(logging.INFO, logger="chemdraw_tool.server"):
        srv.main()
    assert "SMILES lookup: off" in caplog.text
    caplog.clear()
    monkeypatch.setenv(_ENV, "true")
    with caplog.at_level(logging.INFO, logger="chemdraw_tool.server"):
        srv.main()
    assert "SMILES lookup: on" in caplog.text


def test_doctor_zeigt_den_zustand(monkeypatch):
    from chemdraw_tool import doctor

    assert doctor.check_smiles_lookup in doctor.DEFAULT_CHECKS
    monkeypatch.delenv(_ENV, raising=False)
    aus = doctor.check_smiles_lookup()
    assert aus.status == doctor.OK
    assert "off" in aus.detail and "InChIKey" in aus.detail
    assert "server.log" in aus.detail  # der laufende Server kann anders eingestellt sein
    monkeypatch.setenv(_ENV, "1")
    an = doctor.check_smiles_lookup()
    assert an.status == doctor.NOTE
    assert "on" in an.detail


# --- Doku: wörtlich, was hinausgeht ---------------------------------------------

from pathlib import Path  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("datei", ["docs/tools.md", "README.md"])
def test_doku_nennt_schalter_und_datenweg(datei):
    from chemdraw_tool.privacy import SETTING_TITLE

    text = (_ROOT / datei).read_text(encoding="utf-8")
    assert "What leaves your machine" in text
    assert f"{_ENV}=1" in text
    assert SETTING_TITLE in text
    assert "InChIKey" in text
    assert "CHEMDRAW_NO_SMILES_UPLOAD" not in text
    assert "nothing leaves your machine" not in text.lower()


def test_alter_schalter_ist_ueberall_weg():
    treffer = [
        str(p.relative_to(_ROOT))
        for p in [*(_ROOT / "chemdraw_tool").rglob("*.py"), _ROOT / "docs" / "tools.md",
                  _ROOT / "README.md", _ROOT / "mcpb" / "manifest.json"]
        if "CHEMDRAW_NO_SMILES_UPLOAD" in p.read_text(encoding="utf-8")
    ]
    assert treffer == []


def test_datensatz_ohne_titel_fragt_keine_namensquelle(monkeypatch):
    """PubChem kennt den Schlüssel, nennt aber keinen Namen (gemessen: SMILES „NOS“ →
    CID 19079503 ohne Title): dann nicht „CID 19079503“ als Namen an ChEBI/KEGG schicken."""
    monkeypatch.delenv(_ENV, raising=False)
    monkeypatch.setattr(srv, "pubchem_properties_by_inchikey", lambda key: {"CID": 19079503})
    for fn in ("chebi_lookup", "uniprot_search", "uniprot_protein", "kegg_find"):
        monkeypatch.setattr(srv, fn, lambda *a, fn=fn, **k: pytest.fail(f"{fn} gefragt"))
    for topic in ("biochem", "pathway"):
        text = srv.lookup(AMID, topic)
        assert "19079503" in text and "no name" in text



# --- Nachauftrag 2: unlesbare Struktur-Schreibweisen nie als Name ----------------

ABKUERZUNGEN = {
    # Eingabe → erwartetes kanonisches SMILES nach dem lokalen Ersetzen
    "c1ccccc1C(=O)OMe": "COC(=O)c1ccccc1",
    "PhC(=O)CC1CCN(Boc)CC1": "CC(C)(C)OC(=O)N1CCC(CC(=O)c2ccccc2)CC1",
    "CC(=O)N(Me)Bn": "CC(=O)N(C)Cc1ccccc1",
    "AcN1CCC(OEt)CC1": "CCOC1CCN(C(C)=O)CC1",
    "O=C(OtBu)C(C)N(Ts)C": "CC(C(=O)OC(C)(C)C)N(C)S(=O)(=O)c1ccc(C)cc1",
    "C1CC(Ph)CC1Et": "CCC1CCC(c2ccccc2)C1",
}


@pytest.mark.parametrize("eingabe", list(ABKUERZUNGEN))
def test_gaengige_abkuerzungen_werden_lokal_aufgeloest(abfang, eingabe):
    payload = srv.generate_molecule(eingabe)
    smiles = payload.properties["smiles"]
    erwartet = Chem.MolToSmiles(Chem.MolFromSmiles(ABKUERZUNGEN[eingabe]))
    assert Chem.MolToSmiles(Chem.MolFromSmiles(smiles)) == erwartet
    assert not any(eingabe in u or eingabe in b for _, u, b in abfang.aufrufe)


UNLESBARE = [
    "CC(=O)Oc1ccccc1C(=O)O?",  # Tippfehler
    "CC(=O)OCMeC",  # Me mitten in der Kette: nicht eindeutig
    "C(=O)OMx",  # unbekannte Abkürzung
    "PhC(=O)C(Bz)C",  # Bz steht nicht auf der Liste
]


@pytest.mark.parametrize("eingabe", UNLESBARE)
def test_unlesbare_schreibweise_bricht_lokal_ab(abfang, eingabe):
    with pytest.raises(resolver.NameResolutionError) as info:
        srv.generate_molecule(eingabe)
    assert info.value.kind == "invalid_smiles"
    assert "nothing was sent" in str(info.value)
    text = srv.lookup(eingabe, "biochem")
    assert "not sent" in text
    assert abfang.aufrufe == []


def test_unlesbare_schreibweise_mit_opt_in_wie_bisher(abfang, monkeypatch):
    monkeypatch.setenv(_ENV, "1")
    with pytest.raises(resolver.NameResolutionError) as info:
        srv.generate_molecule(UNLESBARE[0])
    assert info.value.kind != "invalid_smiles"  # Namenskaskade lief: not_found
    assert any(UNLESBARE[0] in u for _, u, _ in abfang.aufrufe)


def _namen_aus_den_routing_faellen() -> list[str]:
    import re as _re

    text = (_ROOT / "evals" / "tool-routing" / "cases.yaml").read_text(encoding="utf-8")
    woerter = set()
    for prompt in _re.findall(r'prompt: "([^"]*)"', text):
        woerter.update(prompt.split())
    return sorted(woerter)


def _namen_aus_der_identitaetsliste() -> list[str]:
    daten = json.loads((_ROOT / "tests" / "identity" / "stoffe.json").read_text(encoding="utf-8"))
    return [e["eingabe"] for e in daten["stoffe"] if not e.get("fehler") == "invalid_smiles"]


SYSTEMATISCHE_NAMEN = [
    "2-(4-isobutylphenyl)propanoic acid", "N,N-dimethylformamide",
    "(2S)-2-amino-3-phenylpropanoic acid", "1,2-dichlorobenzene", "cyclo(Gly-Pro)",
    "peptide:AGS", "Ala-Gly-Ser", "hemin", "heme d1",
    "beta-D-glucopyranose", "β-D-glucopyranose", "heme b", "CID 2244", "50-78-2",
    "7732-18-5", "BSYNRYMUTXBXSQ-UHFFFAOYSA-N", "Acetylsalicylsäure", "Natriumchlorid",
    "Ac-Ala-NH2", "Boc-Gly-OH", "Boc2O", "Ac2O", "Et3N", "Et2O", "MeOH", "EtOAc", "PhD",
    "Co(II)", "Fe(III) chloride", "Cu(II)", "[18F]FDG", "[11C]raclopride", "H2O2",
    "Ca(OH)2", "B(OH)3", "Pd(PPh3)4", "PhB(OH)2", "Me3SiCl", "nBuLi", "tBuOK",
    "(S)-(−)-timolol", "(R)-carvone", "L-Dopa", "D-(+)-glucose", "vitamin B12",
    "SN2", "1H-NMR", "EC50", "t½", "Hexan/EE", "7:3", "N2", "O2", "(F", "(20",
    "Strukturformel", "Weinsäure", "Diels-Alder-Reaktion", "3D-Modell", "pKs",
    "Boc-Ala-OH", "Asp-Phe-OMe", "Met-enkephalin", "Fmoc-Gly-OH", "H-Gly-OMe",
    "Ac-Ala-Gly-NH2", "OAc", "MeCN", "PhMe", "BnOH", "TsCl", "AcOH",
]


@pytest.mark.parametrize(
    "name",
    sorted(set(SYSTEMATISCHE_NAMEN + _namen_aus_den_routing_faellen()
               + _namen_aus_der_identitaetsliste())),
)
def test_echte_namen_gelten_nie_als_unlesbare_struktur(name):
    """Die gefährliche Richtung: kein Name darf als kaputtes SMILES abgelehnt
    oder per Abkürzung umgedeutet werden. Lesbare SMILES (z. B. "O") zählen
    nicht — sie sind Strukturen nach der alten Parse-first-Regel."""
    from rdkit import rdBase

    with rdBase.BlockLogs():
        if resolver.parse_smiles_input(name) is not None:
            return
        found = resolver.structure_notation(name)
    assert found is None or found[0] in ("InChI", "molfile", "CXSMILES"), (name, found)
