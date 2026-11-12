"""M2: Kein Panel-Tool-Ergebnis sprengt Claude Desktops Größengrenzen.

Anthropic, troubleshooting „App doesn't render when tool results are large“:
ab rund 150.000 Zeichen legt Desktop (mit aktiver Code-Sandbox) das Ergebnis
als Datei ab, das Panel bekommt nur einen Verweis und lädt nie. Gemessen am
12.11.2026: Vancomycin über generate_molecule 207.938, ein Stapel mit 20
Arzneistoffen 406.528, zwei große Moleküle im Vergleich 761.115 — weil das SDK
die Nutzlast zweimal schickt (structuredContent und eingerücktes JSON im Text)
und SMILES-Eingaben keine Atomgrenze haben.

Gemessen wird, was über die Leitung geht: das ganze CallToolResult als JSON.
Grenzen mit Abstand: 120.000 Zeichen gesamt (Desktop ~150.000), 80.000 je
Textblock (Claude liest höchstens 100.000 Zeichen Text). Kein Netz: SMILES
statt Namen, Datenbanken antworten „offline“, Proteine aus den Fixtures.
"""

import asyncio
import json
import re

import pytest
import requests
from mcp.server.mcpserver.exceptions import ToolError

from chemdraw_tool import protein_structure as ps
from chemdraw_tool import resolver
from chemdraw_tool import server as srv
from tests.test_protein_tools import ROUTES

GESAMT_MAX = 120_000
TEXT_MAX = 80_000

VANCOMYCIN = (
    "C[C@H]1[C@H]([C@@](C[C@@H](O1)O[C@@H]2[C@H]([C@@H]([C@H](O[C@H]2OC3=C4C=C5C=C3OC6=C(C=C(C=C6)"
    "[C@H]([C@H](C(=O)N[C@H](C(=O)N[C@H]5C(=O)N[C@@H]7C8=CC(=C(C=C8)O)C9=C(C=C(C=C9O)O)[C@H]"
    "(NC(=O)[C@H]([C@@H](C1=CC(=C(O4)C=C1)Cl)O)NC7=O)C(=O)O)CC(=O)N)NC(=O)[C@@H](CC(C)C)NC)O)Cl)"
    "CO)O)O)(C)N)O"
)
PACLITAXEL = (
    "CC1=C2[C@@]([C@]([C@H]([C@@H]3[C@]4([C@H](OC4)C[C@@H]([C@]3(C(=O)[C@@H]2OC(=O)C)C)O)OC(=O)C)"
    "OC(=O)C5=CC=CC=C5)(C[C@@H]1OC(=O)[C@@H]([C@H](C6=CC=CC=C6)NC(=O)C7=CC=CC=C7)O)O)(C)C"
)
# Arzneistoffgroß, damit der Stapel die Grenze über die Menge reißt, nicht über ein Riesenmolekül.
ARZNEISTOFFE = [
    "CC(=O)Oc1ccccc1C(=O)O", "Cn1c(=O)c2c(ncn2C)n(C)c1=O", "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "COc1ccc2cc(ccc2c1)C(C)C(=O)O", "CC(=O)Nc1ccc(O)cc1", "CN1CCC[C@H]1c1cccnc1",
    "CN1C2CCC1C(C(=O)OC)C(OC(=O)c1ccccc1)C2", "CC(C)NCC(O)COc1cccc2ccccc12",
    "CN1CCC23C4C1CC5=C2C(=C(C=C5)OC)OC3C(C=C4)O", "CN(C)CCCN1c2ccccc2CCc2ccccc21",
    "OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl", "CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21",
    "NC(=O)N1c2ccccc2C=Cc2ccccc21", "CC12CCC3C(CCC4=CC(=O)CCC34C)C1CCC2O",
    "CC(C)(C)NCC(O)c1ccc(O)c(CO)c1", "COc1ccc(cc1)C(=O)c1ccccc1", "Clc1ccc(cc1)C(c1ccccc1)N1CCN(CC1)CCOCC(=O)O",
    "CC1(C)SC2C(NC(=O)Cc3ccccc3)C(=O)N2C1C(=O)O", "CN1CCN(CC1)C1=Nc2ccccc2Nc2ccc(C)cc21",
    "OCC(O)C1OC(=O)C(O)=C1O",
]

FAELLE = {
    # je Panel-Tool des full-Profils ein Alltagsfall (evals/panel-beispiele.json, Namen → SMILES)
    "generate_molecule": ("generate_molecule", {"name_or_smiles": "Cn1c(=O)c2c(ncn2C)n(C)c1=O"}),
    "compare_molecules": ("compare_molecules", {"structures": [ARZNEISTOFFE[2], ARZNEISTOFFE[3]]}),
    "batch_generate": ("batch_generate", {"molecules": ["c1ccccc1", "Cc1ccccc1", "Oc1ccccc1"]}),
    "generate_reaction": ("generate_reaction", {
        "reactants": ["CC(=O)O", "CCO"], "products": ["CC(=O)OCC", "O"], "conditions": "H2SO4"}),
    "generate_mechanism": ("generate_mechanism", {
        "reaction_type": "sn2", "substrates": ["C[C@@H](Br)CC", "[C-]#N"]}),
    "generate_3d": ("generate_3d", {"name_or_smiles": "Cn1c(=O)c2c(ncn2C)n(C)c1=O"}),
    "generate_protein_or_antibody": ("generate_protein_or_antibody", {"name": "trastuzumab"}),
    "lookup_molecule_data": ("lookup_molecule_data", {"name": "CC(=O)Nc1ccc(O)cc1"}),
    "generate_spectrum": ("generate_spectrum", {
        "spectrum_type": "ir", "peaks": [{"position": 1750, "intensity": 1, "label": "Ester C=O"}]}),
    "generate_tlc": ("generate_tlc", {"lanes": [{"name": "A", "spots": [{"rf": 0.3}]}]}),
    "generate_titration_curve": ("generate_titration_curve", {
        "substance": "Acetic acid", "pka_values": [4.76], "c_acid": 0.1, "v_acid_ml": 25, "c_titrant": 0.1}),
    "generate_species_distribution": ("generate_species_distribution", {
        "substance": "Ibuprofen", "pka_values": [4.4]}),
    "generate_scope_table": ("generate_scope_table", {
        "entries": [{"label": "1a", "structure": ARZNEISTOFFE[0]}, {"label": "1b", "structure": ARZNEISTOFFE[4]}]}),
    "generate_calibration_curve": ("generate_calibration_curve", {
        "concentrations": [1, 2, 4, 8], "signals": [0.11, 0.21, 0.42, 0.8]}),
    "generate_pk_curve": ("generate_pk_curve", {"dose_mg": 500, "vd_l": 40, "half_life_h": 6}),
    "generate_dose_response": ("generate_dose_response", {"ec50": 1.5}),
    # Grenzfälle: groß, viele, lang
    "Vancomycin": ("generate_molecule", {"name_or_smiles": VANCOMYCIN}),
    "Paclitaxel": ("generate_molecule", {"name_or_smiles": PACLITAXEL}),
    "Vancomycin 3D": ("generate_3d", {"name_or_smiles": VANCOMYCIN}),
    "Vancomycin Datenblatt": ("lookup_molecule_data", {"name": VANCOMYCIN}),
    "Stapel mit 20 Arzneistoffen": ("batch_generate", {"molecules": ARZNEISTOFFE}),
    "Vergleich 4 × Vancomycin": ("compare_molecules", {"structures": [VANCOMYCIN] * 4}),
    "Reaktion mit Vancomycin": ("generate_reaction", {
        "reactants": [VANCOMYCIN, "CC(=O)Cl"], "products": [PACLITAXEL, VANCOMYCIN]}),
    "Scope mit 12 Einträgen": ("generate_scope_table", {
        "entries": [{"label": f"{i}", "structure": s} for i, s in enumerate(ARZNEISTOFFE[:12])]}),
    "Mechanismus Fischer-Ester": ("generate_mechanism", {
        "reaction_type": "fischer_ester", "substrates": ["OC(=O)c1ccc(cc1)-c1ccc(cc1)OC(=O)c1ccccc1", "OCCCCCCCCCC"]}),
    "Antikörper (IgG 1HZH)": ("generate_protein_or_antibody", {"name": "antibody"}),
    # Knopfwege des Panels (MoleculeView, AddToAnkiButton): rufen dieselben Tools mit
    # anderen Argumenten — die Platzhalter müssen jedes Payload-Schema bestehen.
    "Vancomycin All H": ("generate_molecule", {"name_or_smiles": VANCOMYCIN, "view": "all_h"}),
    # Stereovarianten: drei offene Zentren (das Höchstmaß, 8 Isomere) im großen Gerüst
    "Vancomycin Stereovarianten": ("generate_molecule", {
        "name_or_smiles": re.sub(r"\[C@@?H\]", "[CH]", VANCOMYCIN, count=3), "stereo_variants": True}),
    "Anki-Deck mit 12 Strukturen": ("export_anki_deck", {
        "deck_name": "M2 probe", "deliver": "apkg",
        "cards": [{"front": {"structure": s}, "back": {"text": "x"}} for s in [VANCOMYCIN, PACLITAXEL, *ARZNEISTOFFE[:10]]]}),
}


@pytest.fixture(scope="module")
def server():
    return srv.create_server("full")


@pytest.fixture
def offline(monkeypatch, tmp_path, kein_netz):
    """Datenbanken antworten wie ohne Netz, Proteine aus Fixtures, Dateien nach tmp_path."""

    def kein_requests(self, req, **kw):
        raise requests.ConnectionError("offline (test_result_size)")

    def fake_get(url, timeout=None, **kw):
        for needle, answer in ROUTES.items():
            if needle in url:
                return answer()
        raise requests.ConnectionError(f"offline: {url}")

    monkeypatch.setattr(requests.Session, "send", kein_requests)
    monkeypatch.setattr(ps.requests, "get", fake_get)
    monkeypatch.setattr(srv, "_TITLE_CACHE", {})
    for const in ("OUTPUT_DIR", "REACTION_DIR", "SPECTRUM_DIR", "TLC_DIR", "SCOPE_DIR",
                  "ANKI_DIR", "PLOT_DIR", "THREED_DIR", "PROTEIN_DIR"):
        monkeypatch.setattr(srv, const, tmp_path / const.lower())
    ps._CACHE.clear()
    resolver.resolve_name.cache_clear()
    yield
    ps._CACHE.clear()
    resolver.resolve_name.cache_clear()


def _messen(server, tool: str, args: dict):
    result = asyncio.run(server.call_tool(tool, args))
    assert not result.is_error, result.content[0].text[:300]
    # ASCII-maskiert wie json.dumps' Vorgabe: die längste Serialisierung, die ein Host wählen kann.
    leitung = json.dumps(result.model_dump(mode="json", by_alias=True, exclude_none=True))
    texte = [len(b.text) for b in result.content if b.type == "text"]
    return result, len(leitung), max(texte, default=0)


def test_jedes_panel_tool_hat_einen_alltagsfall(server):
    panel = {
        t.name for t in asyncio.run(server.list_tools())
        if ((t.meta or {}).get("ui") or {}).get("resourceUri")
    }
    # export_anki_deck läuft nur mit deliver="apkg" (Datei in tmp_path, kein Anki)
    assert panel == {k for k in FAELLE if k in panel} | {"export_anki_deck"}


@pytest.mark.parametrize("fall", list(FAELLE))
def test_ergebnis_bleibt_unter_desktops_grenzen(server, offline, fall):
    tool, args = FAELLE[fall]
    _, gesamt, text = _messen(server, tool, args)
    assert gesamt <= GESAMT_MAX, f"{fall}: {gesamt:,} Zeichen auf der Leitung (Deckel {GESAMT_MAX:,})"
    assert text <= TEXT_MAX, f"{fall}: Textblock {text:,} Zeichen (Deckel {TEXT_MAX:,})"


def _nachladen(server, payload: dict) -> tuple[dict, int]:
    """Wie das Panel (ui/src/utils/toolData.js): Teile holen, rückwärts einsetzen."""
    vermerk = payload.pop("_deferred")
    block, offset, groesstes, abrufe = "", 0, 0, 0
    while offset is not None:
        antwort = asyncio.run(server.call_tool(
            "load_panel_part", {"token": vermerk["token"], "offset": offset}))
        assert not antwort.is_error, antwort.content[0].text
        leitung = json.dumps(antwort.model_dump(mode="json", by_alias=True, exclude_none=True))
        groesstes, abrufe = max(groesstes, len(leitung)), abrufe + 1
        stueck = json.loads(antwort.content[0].text)
        block, offset = block + stueck["text"], stueck["next"]
    teile = json.loads(block)
    assert len(teile) == len(vermerk["paths"])
    for pfad, text in reversed(list(zip(vermerk["paths"], teile))):
        ziel = payload
        for schritt in pfad[:-1]:
            ziel = ziel[schritt]
        ziel[pfad[-1]] = text if isinstance(ziel[pfad[-1]], str) else json.loads(text)
    return payload, groesstes, abrufe


GROSS = ["Vancomycin", "Stapel mit 20 Arzneistoffen", "Vergleich 4 × Vancomycin", "Scope mit 12 Einträgen",
         "Vancomycin All H", "Vancomycin Stereovarianten"]


@pytest.mark.parametrize("fall", GROSS)
def test_zurueckgehaltene_teile_ergeben_das_ganze_ergebnis(server, offline, fall):
    tool, args = FAELLE[fall]
    result, _, _ = _messen(server, tool, args)
    assert result.structured_content.get("_deferred"), f"{fall}: nichts zurückgehalten — Fall zu klein?"
    # Beide Kopien gleich: das Panel liest den Textblock, wenn der Host structuredContent weglässt.
    assert json.loads(result.content[0].text) == result.structured_content
    ganz, groesstes, abrufe = _nachladen(server, dict(result.structured_content))
    erwartet = getattr(srv, tool)(**args).model_dump(mode="json", by_alias=True)
    erwartet.pop("files", None), ganz.pop("files", None)  # Pfade tragen keinen Zufall, aber sicher ist sicher
    assert ganz == erwartet
    assert groesstes <= TEXT_MAX, f"{fall}: ein Nachlade-Stück hat {groesstes:,} Zeichen"
    # ein Block für alle Teile: Abrufe nach Größe, nicht nach Zahl der Bilder
    # (gemessen 12.11.: Vancomycin 2, Stapel 5, Vergleich 4 × Vancomycin 17)
    assert abrufe <= 20, f"{fall}: {abrufe} Abrufe"


def test_unter_dem_budget_bleibt_structured_content_wie_vom_sdk(server, offline):
    tool, args = FAELLE["generate_molecule"]
    result, _, _ = _messen(server, tool, args)
    assert "_deferred" not in result.structured_content
    assert result.structured_content == srv.generate_molecule(**args).model_dump(mode="json", by_alias=True)
    assert "\n" not in result.content[0].text  # kompakt statt eingerückt


def test_unbekanntes_token_meldet_was_hilft(server, offline):
    with pytest.raises(ToolError, match="Run the tool again"):
        asyncio.run(server.call_tool("load_panel_part", {"token": "weg"}))


def test_teile_ueberstehen_einen_server_neustart(server, offline, monkeypatch):
    """Desktop zeigt alte Ergebnisse beim Wiederöffnen eines Chats erneut an —
    dann muss das Panel auch nach einem Neustart des Servers nachladen können."""
    from chemdraw_tool import result_budget

    tool, args = FAELLE["Vancomycin"]
    result, _, _ = _messen(server, tool, args)
    monkeypatch.setattr(result_budget, "_STORE", type(result_budget._STORE)())  # neuer Prozess
    ganz, _, _ = _nachladen(srv.create_server("full"), dict(result.structured_content))
    assert ganz["svg"].startswith("<?xml")


def test_token_ist_ein_inhaltsschluessel(server, offline):
    """Gleiches Ergebnis, gleiches Token: der Speicher wächst nicht je Aufruf."""
    tool, args = FAELLE["Vancomycin"]
    a, _, _ = _messen(server, tool, args)
    b, _, _ = _messen(server, tool, args)
    assert a.structured_content["_deferred"]["token"] == b.structured_content["_deferred"]["token"]
