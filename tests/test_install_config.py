"""Tests für die Claude-Desktop-Config-Merge-Logik des Installers.

Kern-Risiko: den Eintrag hinzufügen, ohne bestehende MCP-Server (z.B. einen
andere bereits konfigurierte lokale Server zu zerstören; idempotent bei Re-Run;
immer valides JSON. Reine Funktion, kein Datei-IO, kein Netz.
"""

import json

import pytest

from scripts.install_claude_config import (
    build_server_entry,
    install,
    merge_server_config,
)


def test_adds_entry_to_empty_config():
    result = merge_server_config({}, "chemdraw-tool", {"command": "uv", "args": ["x"]})
    assert result["mcpServers"]["chemdraw-tool"] == {"command": "uv", "args": ["x"]}


def test_preserves_other_servers():
    existing = {"mcpServers": {"concepts": {"command": "python", "args": ["s.py"]}}}
    result = merge_server_config(existing, "chemdraw-tool", {"command": "uv"})
    assert "concepts" in result["mcpServers"]
    assert result["mcpServers"]["concepts"] == {"command": "python", "args": ["s.py"]}
    assert "chemdraw-tool" in result["mcpServers"]


def test_updates_existing_entry_idempotently():
    existing = {"mcpServers": {"chemdraw-tool": {"command": "old", "args": ["alt"]}}}
    entry = {"command": "uv", "args": ["neu"]}
    once = merge_server_config(existing, "chemdraw-tool", entry)
    twice = merge_server_config(once, "chemdraw-tool", entry)
    assert once == twice
    assert once["mcpServers"]["chemdraw-tool"] == entry


def test_does_not_mutate_input():
    existing = {"mcpServers": {"concepts": {"command": "python"}}}
    snapshot = json.dumps(existing)
    merge_server_config(existing, "chemdraw-tool", {"command": "uv"})
    assert json.dumps(existing) == snapshot, "Eingabe-Dict darf nicht mutiert werden"


def test_preserves_unrelated_top_level_keys():
    existing = {
        "mcpServers": {},
        "isDxtAutoUpdatesEnabled": True,
        "preferences": {"x": 1},
    }
    result = merge_server_config(existing, "chemdraw-tool", {"command": "uv"})
    assert result["isDxtAutoUpdatesEnabled"] is True
    assert result["preferences"] == {"x": 1}


def test_handles_missing_mcpservers_key():
    result = merge_server_config({"other": 1}, "chemdraw-tool", {"command": "uv"})
    assert result["mcpServers"]["chemdraw-tool"] == {"command": "uv"}
    assert result["other"] == 1


def test_build_server_entry_uses_uv_with_directory():
    entry = build_server_entry("/Users/x/Chem-draw-addon")
    assert entry["command"] == "uv"
    assert entry["args"] == [
        "--directory",
        "/Users/x/Chem-draw-addon",
        "run",
        "chemdraw-tool-server",
    ]


def test_build_server_entry_rejects_relative_path():
    with pytest.raises(ValueError, match="absolut"):
        build_server_entry("relativer/pfad")


# --- install() IO-Schicht ---------------------------------------------------


def test_install_creates_config_when_absent(tmp_path):
    cfg = tmp_path / "Claude" / "claude_desktop_config.json"
    install("/Users/x/proj", config_path=cfg)
    data = json.loads(cfg.read_text())
    assert data["mcpServers"]["chemdraw-tool"]["command"] == "uv"
    assert not cfg.with_suffix(".json.bak").exists(), "kein Backup ohne Vorgänger"


def test_install_preserves_other_server_and_writes_backup(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text(
        json.dumps({"mcpServers": {"concepts": {"command": "python"}}}),
        encoding="utf-8",
    )
    install("/Users/x/proj", config_path=cfg)
    data = json.loads(cfg.read_text())
    assert "concepts" in data["mcpServers"]
    assert "chemdraw-tool" in data["mcpServers"]
    backup = json.loads(cfg.with_suffix(".json.bak").read_text())
    assert backup == {"mcpServers": {"concepts": {"command": "python"}}}


def test_install_is_idempotent(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    install("/Users/x/proj", config_path=cfg)
    first = cfg.read_text()
    install("/Users/x/proj", config_path=cfg)
    assert cfg.read_text() == first


def test_install_refuses_corrupt_config_without_touching_it(tmp_path):
    """Korrupte Config → klare Fehlermeldung mit Pfad; Datei bleibt unverändert,
    kein irreführendes .bak (sonst sähe es aus, als wäre installiert worden)."""
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text('{"mcpServers": {broken', encoding="utf-8")
    with pytest.raises(ValueError, match=str(cfg)):
        install("/Users/x/proj", config_path=cfg)
    assert cfg.read_text() == '{"mcpServers": {broken', "Original unangetastet"
    assert not cfg.with_suffix(".json.bak").exists()
