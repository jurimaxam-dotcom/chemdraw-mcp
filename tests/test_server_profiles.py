"""Beide Startprofile über frische Prozesse prüfen, unabhängig vom Testkatalog."""

import json
import os
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MVP = {
    "generate_molecule", "batch_generate", "compare_molecules",
    "generate_reaction", "lookup_molecule_data", "save_png",
    # Seit 21.10.2026: Lernweg Molekül → Anki (Panel-Knopf und Chat).
    "export_anki_deck",
    # Basis-Ausbau Welle 1 (30.10.2026): Lehrbuch-Mechanismen.
    "generate_mechanism",
    "generate_3d",
}
FULL = {p.stem for p in (ROOT / "tests/__snapshots__/tools").glob("*.json")}


@lru_cache
def _start(profile=None, vault=False):
    env = os.environ.copy()
    env.pop("CHEMDRAW_PROFILE", None)
    env.pop("CHEMDRAW_VAULT_PATH", None)
    if profile is not None:
        env["CHEMDRAW_PROFILE"] = profile
    if vault:
        env["CHEMDRAW_VAULT_PATH"] = str(ROOT / "docs")
    return subprocess.run(
        [sys.executable, "-c", """
import asyncio, json
from chemdraw_tool.server import mcp
async def inspect():
    tools = await mcp.list_tools()
    resources = await mcp.list_resources()
    blocked = False
    try:
        await mcp.call_tool('calculate_ph', {'topic': 'strong_acid', 'concentration': 0.1})
    except Exception as error:
        blocked = 'Unknown tool' in str(error)
    print(json.dumps({'tools': [t.model_dump(mode='json', by_alias=True) for t in tools],
                      'instructions': mcp.instructions, 'blocked': blocked,
                      'resources': [str(r.uri) for r in resources]}))
asyncio.run(inspect())
"""], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30,
    )


def _data(profile=None, vault=False):
    result = _start(profile, vault)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("profile", [None, "mvp"])
def test_default_and_explicit_mvp_offer_exactly_the_mvp_tools(profile):
    assert {t["name"] for t in _data(profile)["tools"]} == MVP


def test_full_profile_keeps_the_complete_snapshot_catalog():
    assert {t["name"] for t in _data("full")["tools"]} == FULL


def test_mvp_rejects_disabled_calls_instead_of_only_hiding_them():
    assert _data()["blocked"]


def test_mvp_never_registers_optional_vault_tools():
    assert {t["name"] for t in _data(vault=True)["tools"]} == MVP


def test_mvp_instructions_and_descriptions_reference_only_available_tools():
    data = _data()
    text = data["instructions"] + "\n" + "\n".join(t["description"] for t in data["tools"])
    mentioned = set(re.findall(r"\b[a-z]+(?:_[a-z0-9]+)+\b", text)) & FULL
    assert mentioned <= MVP, mentioned - MVP
    assert "bare compound name" in text
    assert "never call save_png" in data["instructions"]
    assert "export_anki_deck" in data["instructions"]
    assert len(data["instructions"].encode()) <= 2048


def test_mvp_descriptions_stay_under_the_client_cut():
    # Der Taxonomie-Test misst nur den Vollkatalog; Desktop sieht diese Texte.
    for tool in _data()["tools"]:
        size = len(tool["description"].encode())
        assert size <= 2048, f"{tool['name']}: {size} B"


def test_mvp_molecule_tool_claims_named_projections():
    # Desktop-Befund 26.10.2026: „Haworth-Projektion von …“ ging an Desktops
    # eingebautes visualize, weil keine Beschreibung Projektionen nannte.
    tool = next(t for t in _data()["tools"] if t["name"] == "generate_molecule")
    summary = tool["description"].split("Args:")[0]
    assert "Haworth" in summary and "Fischer" in summary


def test_mvp_keeps_the_panel_resource_and_metadata():
    data = _data()
    uri = "ui://chem-app/index.html"
    assert uri in data["resources"]
    panel = {t["name"] for t in data["tools"] if ((t.get("_meta") or {}).get("ui") or {}).get("resourceUri") == uri}
    assert panel == MVP - {"save_png"}


def _summary(tool):
    return next(t for t in _data()["tools"] if t["name"] == tool)["description"].split("Args:")[0]


@pytest.mark.parametrize("neighbour, target", [
    # Rückwärtszäune: der Nachbar, der den Fall sonst gewinnt, zeigt auf das neue Tool.
    ("generate_reaction", "generate_mechanism"),
    ("generate_molecule", "generate_3d"),
    ("generate_3d", "generate_molecule"),
])
def test_mvp_neighbours_fence_towards_newly_enabled_tools(neighbour, target):
    assert target in _summary(neighbour)


@pytest.mark.parametrize("tool", ["generate_mechanism", "generate_3d"])
def test_mvp_instructions_route_newly_enabled_tools(tool):
    assert tool in _data()["instructions"]


@pytest.mark.parametrize("profile", ["typo", "", "MVP"])
def test_invalid_profile_aborts_startup(profile):
    result = _start(profile)
    assert result.returncode != 0
    assert "CHEMDRAW_PROFILE" in result.stderr
