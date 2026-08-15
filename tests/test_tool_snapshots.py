"""Tool-Snapshots: die Beschreibungen sind der Vertrag, nicht Beiwerk.

Das Modell waehlt ein Tool ausschliesslich nach Name, Beschreibung und Schema.
Eine beilaeufig umformulierte Zeile aendert damit das Verhalten des Servers,
ohne dass ein einziger Verhaltenstest rot wird — genau so ist „Zeichne Aspirin"
bei `generate_scope_table` gelandet (siehe test_server_taxonomy.py).

Vorbild ist das `toolsnaps`-Verfahren des github-mcp-server: fuer jedes Tool
liegt eine eingefrorene JSON-Datei im Repo. Jede Aenderung an Name,
Beschreibung, Eingabe- oder Ausgabeschema wird dadurch zu einem sichtbaren Diff
im Review — nicht zu einer stillen Verhaltensaenderung.

Bewusst neu segnen (und den Diff dabei ansehen!):

    UPDATE_TOOLSNAPS=1 uv run pytest tests/test_tool_snapshots.py

Das schreibt die Snapshots neu UND loescht verwaiste Dateien entfernter Tools.
Ein fehlender Snapshot wird NICHT still angelegt — sonst waere ein neues Tool
genau der Fall, den dieser Test verhindern soll: unbemerkt hinzugekommen.

Aufgenommen werden nur die vier Felder, die die Toolauswahl steuern: name,
description, inputSchema, outputSchema. `_meta` bleibt draussen — dass die
Panel-Tools ihr UI-Meta tragen, prueft test_server_ui.py, und der echte
stdio-Handshake (scripts/handshake.sh) zaehlt es beim laufenden Server nach.
"""

import asyncio
import json
import os
from pathlib import Path

import pytest

from chemdraw_tool.server import mcp

SNAPSHOT_DIR = Path(__file__).parent / "__snapshots__" / "tools"

UPDATE_HINT = (
    "Bewusst neu segnen mit:  UPDATE_TOOLSNAPS=1 uv run pytest "
    "tests/test_tool_snapshots.py   (Diff vorher ansehen!)"
)

# Nur mit CHEMDRAW_VAULT_PATH registriert. Ohne diese Ausnahme haengen die
# Snapshots an der Umgebung: wer die Variable gesetzt hat, bekaeme zwei
# „fehlende" Snapshots gemeldet — falsch-rot aus reiner Konfiguration.
VAULT = {"search_vault", "read_vault_entry"}


def _registered_tools() -> dict[str, dict]:
    """{Toolname: Snapshot-Dict} aller registrierten Tools ohne Vault.

    `mcp.list_tools()` ist async, das Projekt hat aber kein pytest-asyncio —
    `asyncio.run` haelt die Abhaengigkeitsliste kurz und reicht hier voellig.
    Es ist bewusst der Weg ueber die MCP-Ebene: genau diese Struktur bekommt
    der Client zu sehen.
    """
    tools = asyncio.run(mcp.list_tools())
    return {
        tool.name: {
            "name": tool.name,
            "description": tool.description or "",
            "inputSchema": tool.inputSchema,
            "outputSchema": tool.outputSchema,
        }
        for tool in tools
        if tool.name not in VAULT
    }


def _serialize(snapshot: dict) -> str:
    """Deterministische Serialisierung — sonst diffen Snapshots ohne Anlass."""
    return json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _snapshot_path(name: str) -> Path:
    return SNAPSHOT_DIR / f"{name}.json"


def _stored_names() -> set[str]:
    if not SNAPSHOT_DIR.is_dir():
        return set()
    return {p.stem for p in SNAPSHOT_DIR.glob("*.json")}


def _rewrite_snapshots() -> None:
    """Schreibt alle Snapshots neu und raeumt verwaiste Dateien weg."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    current = _registered_tools()
    for name, snapshot in current.items():
        _snapshot_path(name).write_text(_serialize(snapshot), encoding="utf-8")
    # Entfernte Tools muessen auch abgesegnet weggeraeumt werden koennen,
    # sonst bleibt der Test dauerhaft rot.
    for orphan in _stored_names() - set(current):
        _snapshot_path(orphan).unlink()


@pytest.fixture(scope="module", autouse=True)
def _maybe_rewrite_snapshots():
    """UPDATE_TOOLSNAPS=1 segnet den aktuellen Stand ab — sonst passiert nichts."""
    if os.environ.get("UPDATE_TOOLSNAPS") == "1":
        _rewrite_snapshots()


@pytest.mark.parametrize("name", sorted(_registered_tools()))
def test_tool_matches_its_snapshot(name):
    """Name, Beschreibung und Schemata muessen Zeichen fuer Zeichen passen."""
    path = _snapshot_path(name)
    assert path.is_file(), (
        f"Kein Snapshot fuer Tool '{name}' ({path}). Ein neues Tool wird NICHT "
        f"still angelegt — es soll im Review auffallen.\n{UPDATE_HINT}"
    )
    expected = path.read_text(encoding="utf-8")
    actual = _serialize(_registered_tools()[name])
    assert actual == expected, (
        f"Tool '{name}' weicht von seinem Snapshot ab — Beschreibung oder Schema "
        f"hat sich geaendert. Das aendert die Toolauswahl des Modells.\n"
        f"{UPDATE_HINT}"
    )


def test_no_orphaned_snapshots():
    """Ein entferntes Tool laesst seinen Snapshot zurueck — auch das ist rot."""
    orphans = sorted(_stored_names() - set(_registered_tools()))
    assert not orphans, (
        f"Snapshots ohne registriertes Tool: {orphans} — Tool entfernt oder "
        f"umbenannt?\n{UPDATE_HINT}"
    )


def test_tool_count_is_pinned_by_the_snapshot_set():
    """Die Anzahl der Tools steht fest — als Zahl der Dateien im Verzeichnis.

    Redundant zu den beiden Tests darueber, und trotzdem hier: die Zahl der
    Tools ist die Groesse, die bei jeder Anfrage die Trefferquote bestimmt
    (Obergrenze siehe test_server_taxonomy.py). Sie soll beim Lesen der
    Fehlermeldung sofort dastehen.
    """
    registered = _registered_tools()
    stored = _stored_names()
    assert len(registered) == len(stored), (
        f"{len(registered)} registrierte Tools, aber {len(stored)} Snapshots.\n"
        f"{UPDATE_HINT}"
    )
