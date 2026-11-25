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
