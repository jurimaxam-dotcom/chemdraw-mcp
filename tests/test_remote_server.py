"""Tests für den separat startbaren Remote-MCP-Konnektor (Streamable HTTP).

Prüft den ersten Pilot-Anwendungsfall: Name/SMILES → interaktive 2D-Struktur
mit funktionellen Gruppen, komplett ohne lokale Datei-Exporte, Anki, Pfade
oder geteilten Nutzerzustand.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from starlette.testclient import TestClient

from chempane.remote import (
    MAX_INPUT_LENGTH,
    RemoteConfig,
    create_remote_app,
    create_remote_server,
)

ASPIRIN_SMILES = "CC(=O)Oc1ccccc1C(=O)O"


def test_remote_server_exposes_only_readonly_generate_molecule_and_panel_resource():
    srv = create_remote_server()

    async def _inspect():
        tools = await srv.list_tools()
        resources = await srv.list_resources()
        prompts = await srv.list_prompts()
        return tools, resources, prompts

    tools, resources, prompts = asyncio.run(_inspect())
    assert [t.name for t in tools] == ["generate_molecule"]
    tool = tools[0]
    assert tool.annotations is not None
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.destructive_hint is False
    # Das Portal liest den Namen fürs Listing aus annotations.title, nicht aus dem Tool-Titel.
    assert tool.annotations.title == "Draw a structure"
    # Directory-Zusage: die Beschreibung enthält keine Anweisungen an das Modell, nur Parameter-Doku.
    assert "IMPORTANT" not in tool.description
    assert "on the server" in tool.description and "locally" not in tool.description
    assert (tool.meta or {}).get("ui", {}).get("resourceUri") == "ui://chem-app/index.html"
    assert "formats" not in (tool.input_schema.get("properties") or {})
    assert [str(r.uri) for r in resources] == ["ui://chem-app/index.html"]
    assert prompts == []


def test_remote_server_rejects_local_and_anki_tools():
    srv = create_remote_server()
    for forbidden in ("save_png", "load_panel_part", "export_anki_deck", "lookup_molecule_data", "generate_3d"):
        with pytest.raises(ToolError, match="Unknown tool"):
            asyncio.run(srv.call_tool(forbidden, {}))


def test_remote_generate_molecule_draws_2d_with_groups_and_writes_no_files(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    srv = create_remote_server()
    result = asyncio.run(
        srv.call_tool("generate_molecule", {"name_or_smiles": ASPIRIN_SMILES, "label": "Aspirin"})
    )
    assert not result.is_error
    payload = result.structured_content
    assert payload["type"] == "molecule"
    assert payload["remote"] is True
    assert payload["name"] == "Aspirin"
    assert "<svg" in payload["svg"]
    group_names = {g["name"] for g in payload["functionalGroups"]}
    assert "Carbonsäure" in group_names
    assert "Ester" in group_names
    assert payload["files"] == {}
    assert payload["cdxml_path"] == ""
    raw = json.dumps(payload) + " ".join(getattr(c, "text", "") for c in result.content)
    for forbidden in ("/Users/", "chempane-output", "ChemDraw-Output", ".png", ".svg", ".cdxml"):
        assert forbidden not in raw, f"unerwarteter Dateipfad/Export im Remote-Ergebnis: {forbidden}"
    assert list(tmp_path.iterdir()) == []


def test_remote_generate_molecule_supports_all_h_view():
    srv = create_remote_server()
    result = asyncio.run(
        srv.call_tool("generate_molecule", {"name_or_smiles": "CCO", "label": "Ethanol", "view": "all_h"})
    )
    assert not result.is_error
    payload = result.structured_content
    assert payload["remote"] is True
    assert payload["initialView"] == "all_h"
    assert "<svg" in payload["viewSvg"]
    assert len(payload["viewAtoms"]) > 0
    assert payload["files"] == {}


def test_remote_input_and_size_limits():
    srv = create_remote_server()
    with pytest.raises(ToolError):
        asyncio.run(srv.call_tool("generate_molecule", {"name_or_smiles": "   "}))
    with pytest.raises(ToolError, match="too long"):
        asyncio.run(srv.call_tool("generate_molecule", {"name_or_smiles": "C" * (MAX_INPUT_LENGTH + 1)}))
    with pytest.raises(ToolError, match="heavy atoms"):
        asyncio.run(srv.call_tool("generate_molecule", {"name_or_smiles": "C" * 205}))


def test_remote_http_healthz_streamable_draw_and_rate_limit():
    cfg = RemoteConfig(rate_limit_requests=3, rate_limit_window_seconds=60.0)
    app = create_remote_app(cfg)
    with TestClient(app) as client:
        health = client.get("/healthz")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "pytest-remote", "version": "0.1"},
            },
        }
        r1 = client.post("/mcp", json=init_req, headers=headers)
        assert r1.status_code == 200, r1.text

        call_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "generate_molecule",
                "arguments": {"name_or_smiles": ASPIRIN_SMILES, "label": "Aspirin"},
            },
        }
        r2 = client.post("/mcp", json=call_req, headers=headers)
        assert r2.status_code == 200, r2.text
        assert "Carbons" in r2.text or "<svg" in r2.text

        r3 = client.post("/mcp", json=call_req, headers=headers)
        assert r3.status_code == 200

        # 4. Request im 60s-Fenster muss mit 429 geblockt werden
        r4 = client.post("/mcp", json=call_req, headers=headers)
        assert r4.status_code == 429


def _init_req() -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "pytest-remote", "version": "0.1"},
        },
    }


def test_remote_rate_limit_gemeinsamer_ausgang_bekommt_eigenes_limit():
    # Claude leitet Tool-Aufrufe über das eigene Backend: alle Nutzer kommen aus 160.79.104.0/21.
    # Das Limit je IP wäre dort ein gemeinsamer Deckel für alle, also gilt für diesen Bereich ein eigenes.
    cfg = RemoteConfig(
        rate_limit_requests=2,
        shared_rate_limit_requests=5,
        rate_limit_window_seconds=60.0,
        trust_proxy=True,
    )
    assert cfg.shared_ranges == ("160.79.104.0/21",)
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    with TestClient(create_remote_app(cfg)) as client:
        claude = {**headers, "X-Forwarded-For": "160.79.104.17"}
        for _ in range(5):
            assert client.post("/mcp", json=_init_req(), headers=claude).status_code == 200
        # Auch der gemeinsame Bereich ist gedeckelt, und eine zweite Adresse daraus teilt den Zähler.
        andere = {**headers, "X-Forwarded-For": "160.79.111.200"}
        assert client.post("/mcp", json=_init_req(), headers=andere).status_code == 429

        fremd = {**headers, "X-Forwarded-For": "203.0.113.9"}
        for _ in range(2):
            assert client.post("/mcp", json=_init_req(), headers=fremd).status_code == 200
        assert client.post("/mcp", json=_init_req(), headers=fremd).status_code == 429


def test_remote_config_liest_gemeinsamen_bereich_aus_der_umgebung(monkeypatch):
    monkeypatch.setenv("CHEMPANE_REMOTE_SHARED_RANGES", "198.51.100.0/24, 2001:db8::/32")
    monkeypatch.setenv("CHEMPANE_REMOTE_SHARED_RATE_LIMIT", "900")
    cfg = RemoteConfig.from_env()
    assert cfg.shared_ranges == ("198.51.100.0/24", "2001:db8::/32")
    assert cfg.shared_rate_limit_requests == 900


def test_remote_getippte_struktur_loest_keine_netzanfrage_aus(monkeypatch):
    # Zusage der Remote-Datenschutzerklärung: ein SMILES wird im Container gezeichnet und geht nirgendwohin.
    import requests

    anfragen: list[str] = []

    def _sperre(self, method, url, *args, **kwargs):
        anfragen.append(url)
        raise requests.ConnectionError("Netz im Test gesperrt")

    monkeypatch.setattr(requests.sessions.Session, "request", _sperre)
    srv = create_remote_server()
    asyncio.run(srv.call_tool("generate_molecule", {"name_or_smiles": ASPIRIN_SMILES, "label": "Aspirin"}))
    assert anfragen == []

    # Gegenprobe: die Sperre greift wirklich, ein Name ohne OPSIN-Treffer muss sie auslösen.
    with pytest.raises(ToolError):
        asyncio.run(srv.call_tool("generate_molecule", {"name_or_smiles": "Koffein"}))
    assert anfragen, "Die Sperre hat keine Anfrage gesehen: der Test prüft nichts."


def test_remote_datenschutzseite_nur_mit_betreiberangabe():
    # Betreibername und Kontakt stehen nicht im Repo, sondern kommen aus der Umgebung des Hosts.
    with TestClient(create_remote_app(RemoteConfig())) as client:
        assert client.get("/privacy").status_code == 404
    cfg = RemoteConfig(operator="Erika Mustermann", contact="kontakt-platzhalter")
    with TestClient(create_remote_app(cfg)) as client:
        seite = client.get("/privacy")
        assert seite.status_code == 200
        assert seite.headers["content-type"].startswith("text/html")
        for text in ("Erika Mustermann", "kontakt-platzhalter", "PubChem", "Fly.io", "sent to no other service"):
            assert text in seite.text, text


def test_remote_datenschutzseite_nennt_dsgvo_pflichtangaben():
    # Art. 13 DSGVO verlangt Rechtsgrundlage, Betroffenenrechte und Beschwerderecht.
    cfg = RemoteConfig(operator="Erika Mustermann", contact="kontakt-platzhalter")
    with TestClient(create_remote_app(cfg)) as client:
        seite = client.get("/privacy")
        assert seite.status_code == 200
        body = seite.text
        # 1. Rechtsgrundlage (Art. 13 Abs. 1 lit. c DSGVO)
        assert "Legal basis" in body
        assert "Art. 6(1)(b) GDPR" in body
        assert "Art. 6(1)(f) GDPR" in body
        # 2. Betroffenenrechte (Art. 13 Abs. 2 lit. b DSGVO)
        lower = body.lower()
        for recht in ("access", "rectify", "erase", "restrict", "portable", "object"):
            assert recht in lower, f"Betroffenenrecht fehlt: {recht}"
        for artikel in ("Art. 15", "Art. 16", "Art. 17", "Art. 18", "Art. 20", "Art. 21"):
            assert artikel in body, f"Artikel-Verweis fehlt: {artikel}"
        # 3. Beschwerderecht bei einer Aufsichtsbehörde (Art. 13 Abs. 2 lit. d, Art. 77 DSGVO)
        assert "complaint" in lower
        assert "supervisory authority" in lower
        assert "Art. 77 GDPR" in body
        # 4. Direkte Verbindung (Claude Code) vs. claude.ai-Connector und Drittlandhinweis (USA)
        assert "Claude Code" in body
        assert "United States" in body


def test_remote_rate_limit_ignoriert_gefaelschten_ersten_xff_eintrag():
    # Ein Client kann X-Forwarded-For vorschalten (z. B. eine Anthropic-IP), der Proxy hängt die
    # echte Client-IP hinten an oder setzt Fly-Client-IP. Beides darf das Per-IP-Limit nicht umgehen.
    cfg = RemoteConfig(
        rate_limit_requests=2,
        shared_rate_limit_requests=10,
        rate_limit_window_seconds=60.0,
        trust_proxy=True,
    )
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    with TestClient(create_remote_app(cfg)) as client:
        # 1) Gefälschter erster XFF-Eintrag (Anthropic-Bereich) vor echter Client-IP 203.0.113.42
        spoof_xff = {**headers, "X-Forwarded-For": "160.79.104.17, 203.0.113.42"}
        assert client.post("/mcp", json=_init_req(), headers=spoof_xff).status_code == 200
        assert client.post("/mcp", json=_init_req(), headers=spoof_xff).status_code == 200
        assert client.post("/mcp", json=_init_req(), headers=spoof_xff).status_code == 429

        # 2) Fly-Client-IP hat Vorrang vor einem gefälschten X-Forwarded-For
        spoof_with_fly = {
            **headers,
            "X-Forwarded-For": "160.79.104.99",
            "Fly-Client-IP": "198.51.100.7",
        }
        assert client.post("/mcp", json=_init_req(), headers=spoof_with_fly).status_code == 200
        assert client.post("/mcp", json=_init_req(), headers=spoof_with_fly).status_code == 200
        assert client.post("/mcp", json=_init_req(), headers=spoof_with_fly).status_code == 429


def test_remote_config_liest_betreiber_aus_der_umgebung(monkeypatch):
    monkeypatch.setenv("CHEMPANE_REMOTE_OPERATOR", "Erika Mustermann")
    monkeypatch.setenv("CHEMPANE_REMOTE_CONTACT", "kontakt-platzhalter")
    cfg = RemoteConfig.from_env()
    assert (cfg.operator, cfg.contact) == ("Erika Mustermann", "kontakt-platzhalter")


def test_remote_tagesbudget_deckelt_die_kosten():
    # Fly.io kennt kein Ausgabenlimit: das Tagesbudget ist die Obergrenze für ausgehende Daten.
    cfg = RemoteConfig(rate_limit_requests=100, daily_limit_requests=3)
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    with TestClient(create_remote_app(cfg)) as client:
        for _ in range(3):
            assert client.post("/mcp", json=_init_req(), headers=headers).status_code == 200
        voll = client.post("/mcp", json=_init_req(), headers=headers)
        assert voll.status_code == 429
        assert voll.json()["error"] == "daily_limit_reached"
        # Health-Prüfung und Datenschutzseite zählen nicht mit und bleiben erreichbar.
        assert client.get("/healthz").status_code == 200


def test_remote_tagesbudget_aus_der_umgebung(monkeypatch):
    assert RemoteConfig().daily_limit_requests == 50_000
    monkeypatch.setenv("CHEMPANE_REMOTE_DAILY_LIMIT", "1234")
    assert RemoteConfig.from_env().daily_limit_requests == 1234


def test_remote_dockerfile_stellt_java_fuer_opsin_mit_speicherdeckel_bereit():
    # Ohne JRE im Image geht jeder systematische IUPAC-Name an PubChem statt offline über OPSIN.
    # Der Container läuft mit 512 MB RAM (fly.toml) → Heap hart deckeln.
    from pathlib import Path

    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")
    assert "default-jre-headless" in dockerfile
    assert "JAVA_TOOL_OPTIONS=" in dockerfile
    assert "-Xmx" in dockerfile


def test_remote_log_enthaelt_keine_eingaben(caplog, monkeypatch):
    # Die Datenschutzseite sagt: das Log zeichnet keine Stoffnamen oder Strukturen auf. Die MCP-Bibliothek
    # protokolliert aber den Fehlertext eines Tools, und der zitiert die Eingabe; der Resolver nennt Namen.
    import logging

    from chempane import remote
    from chempane.resolver import NameResolutionError

    def kein_treffer(name):
        logging.getLogger("chempane.resolver").info("Retrying with transliterated name: %r", name)
        raise NameResolutionError(
            f"Could not resolve '{name}' to a structure.", name=name, kind="not_found", attempts=[]
        )

    monkeypatch.setattr(remote, "resolve", kein_treffer)
    entfernen = remote.install_log_privacy()
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    try:
        with caplog.at_level(logging.DEBUG), TestClient(create_remote_app(RemoteConfig())) as client:
            for eingabe in ("geheimstoff-4711", "C1CC(geheim"):
                req = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "generate_molecule", "arguments": {"name_or_smiles": eingabe}},
                }
                antwort = client.post("/mcp", json=req, headers=headers)
                assert antwort.status_code == 200
                # Der Nutzer bekommt den Hinweis weiterhin im Wortlaut.
                assert eingabe in antwort.text
    finally:
        entfernen()
    assert "geheim" not in caplog.text
    # Dass ein Tool gescheitert ist, bleibt sichtbar.
    assert "generate_molecule" in caplog.text


def test_remote_log_filter_laesst_unerwartete_fehler_ohne_eingabe_durch(caplog):
    import logging

    from chempane import remote

    entfernen = remote.install_log_privacy()
    try:
        with caplog.at_level(logging.DEBUG):
            try:
                raise RuntimeError("kaputt bei geheimstoff-4711")
            except RuntimeError:
                logging.getLogger("mcp.server.mcpserver.server").exception(
                    "Tool %r raised an unexpected exception", "generate_molecule"
                )
    finally:
        entfernen()
    assert "geheim" not in caplog.text
    assert "RuntimeError" in caplog.text


def test_remote_rate_limit_liest_die_echte_adresse_hinter_cloudflare():
    # mcp.chempane.com läuft über Cloudflare: Fly sieht als Gegenstelle eine Cloudflare-Adresse, die echte
    # steht in CF-Connecting-IP. Ohne das greift weder das Limit je Nutzer noch Anthropics eigener Bereich.
    cfg = RemoteConfig(
        rate_limit_requests=2,
        shared_rate_limit_requests=4,
        rate_limit_window_seconds=60.0,
        trust_proxy=True,
    )
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    with TestClient(create_remote_app(cfg)) as client:
        # Zwei Nutzer über dieselbe Cloudflare-Adresse haben je ein eigenes Limit.
        for nutzer in ("203.0.113.5", "203.0.113.6"):
            ueber_cf = {**headers, "Fly-Client-IP": "173.245.48.10", "CF-Connecting-IP": nutzer}
            assert client.post("/mcp", json=_init_req(), headers=ueber_cf).status_code == 200
            assert client.post("/mcp", json=_init_req(), headers=ueber_cf).status_code == 200
            assert client.post("/mcp", json=_init_req(), headers=ueber_cf).status_code == 429
        # Claude über Cloudflare (IPv6-Gegenstelle) zählt im gemeinsamen Bereich mit dem höheren Limit.
        claude = {**headers, "Fly-Client-IP": "2606:4700::1234", "CF-Connecting-IP": "160.79.104.17"}
        for _ in range(4):
            assert client.post("/mcp", json=_init_req(), headers=claude).status_code == 200
        assert client.post("/mcp", json=_init_req(), headers=claude).status_code == 429


def test_remote_rate_limit_glaubt_cf_kopf_nur_von_cloudflare():
    # chempane.fly.dev ist direkt erreichbar: wer dort CF-Connecting-IP selbst setzt, darf sich damit
    # weder ein frisches Limit noch Anthropics Bereich erschleichen.
    cfg = RemoteConfig(
        rate_limit_requests=2,
        shared_rate_limit_requests=10,
        rate_limit_window_seconds=60.0,
        trust_proxy=True,
    )
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    with TestClient(create_remote_app(cfg)) as client:
        for vorgetaeuscht in ("160.79.104.17", "203.0.113.77", "160.79.104.18"):
            direkt = {**headers, "Fly-Client-IP": "198.51.100.7", "CF-Connecting-IP": vorgetaeuscht}
            status = client.post("/mcp", json=_init_req(), headers=direkt).status_code
            assert status == (429 if vorgetaeuscht == "160.79.104.18" else 200)


def test_remote_wartet_auf_einen_freien_platz_statt_sofort_abzuweisen(monkeypatch):
    # Gemessen am 26.11.2026: 40 gleichzeitige Pings ergaben 30-mal 503. Kurze Spitzen sollen warten.
    import time
    from concurrent.futures import ThreadPoolExecutor

    from chempane import remote

    echt = remote.resolve

    def langsam(name):
        time.sleep(0.3)
        return echt(name)

    monkeypatch.setattr(remote, "resolve", langsam)
    cfg = RemoteConfig(max_concurrent=1, queue_wait_seconds=10.0)
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "generate_molecule", "arguments": {"name_or_smiles": ASPIRIN_SMILES}},
    }
    with TestClient(create_remote_app(cfg)) as client, ThreadPoolExecutor(4) as pool:
        codes = list(pool.map(lambda _: client.post("/mcp", json=req, headers=headers).status_code, range(4)))
    assert codes == [200, 200, 200, 200]


def test_remote_weist_ab_wenn_die_wartezeit_ablaeuft(monkeypatch):
    import time
    from concurrent.futures import ThreadPoolExecutor

    from chempane import remote

    echt = remote.resolve

    def langsam(name):
        time.sleep(0.6)
        return echt(name)

    monkeypatch.setattr(remote, "resolve", langsam)
    cfg = RemoteConfig(max_concurrent=1, queue_wait_seconds=0.05)
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "generate_molecule", "arguments": {"name_or_smiles": ASPIRIN_SMILES}},
    }
    with TestClient(create_remote_app(cfg)) as client, ThreadPoolExecutor(3) as pool:
        antworten = list(pool.map(lambda _: client.post("/mcp", json=req, headers=headers), range(3)))
    codes = sorted(a.status_code for a in antworten)
    assert codes[0] == 200 and codes[-1] == 503
    assert all(a.headers.get("Retry-After") for a in antworten if a.status_code == 503)


def test_remote_log_nennt_nur_registrierte_toolnamen(caplog):
    # Bei einem unbekannten Tool reicht die Bibliothek den Namen aus der Anfrage ins Log durch —
    # dort kann ebenso gut ein Stoffname stehen.
    import logging

    from chempane import remote

    entfernen = remote.install_log_privacy()
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    try:
        with caplog.at_level(logging.DEBUG), TestClient(create_remote_app(RemoteConfig())) as client:
            req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "geheimstoff-4711", "arguments": {}},
            }
            client.post("/mcp", json=req, headers=headers)
            logging.getLogger("mcp.server.mcpserver.server").info(
                "Tool %r failed: %r", "geheimstoff-4711", "Unknown tool"
            )
    finally:
        entfernen()
    assert "geheim" not in caplog.text


def test_remote_wartezeit_null_bedient_freie_plaetze():
    cfg = RemoteConfig(queue_wait_seconds=0.0)
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    with TestClient(create_remote_app(cfg)) as client:
        assert client.post("/mcp", json=_init_req(), headers=headers).status_code == 200


def test_remote_volle_warteschlange_weist_sofort_ab(monkeypatch):
    import time
    from concurrent.futures import ThreadPoolExecutor

    from chempane import remote

    echt = remote.resolve

    def langsam(name):
        time.sleep(0.5)
        return echt(name)

    monkeypatch.setattr(remote, "resolve", langsam)
    # Ein Platz, ein Wartender: von vier gleichzeitigen Anfragen kommen zwei durch, zwei gehen sofort.
    cfg = RemoteConfig(max_concurrent=1, queue_wait_seconds=10.0, max_queued=1)
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "generate_molecule", "arguments": {"name_or_smiles": ASPIRIN_SMILES}},
    }
    with TestClient(create_remote_app(cfg)) as client, ThreadPoolExecutor(4) as pool:
        codes = sorted(pool.map(lambda _: client.post("/mcp", json=req, headers=headers).status_code, range(4)))
    assert codes == [200, 200, 503, 503]
