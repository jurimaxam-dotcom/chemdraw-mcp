"""Tests für die Claude-Desktop-Config-Merge-Logik des Installers.

Kern-Risiko: den Eintrag hinzufügen, ohne bestehende MCP-Server (z.B. einen
andere bereits konfigurierte lokale Server zu zerstören; idempotent bei Re-Run;
immer valides JSON. Reine Funktion, kein Datei-IO, kein Netz.
"""

import json
import shutil
from pathlib import Path

import pytest

from scripts.install_claude_config import (
    build_server_entry,
    install,
    merge_server_config,
    resolve_uv_command,
    verify_entry,
)


def _fake_uv(directory: Path) -> Path:
    """Legt ein ausführbares Dummy-uv an (kein echtes Binary nötig)."""
    directory.mkdir(parents=True, exist_ok=True)
    uv = directory / "uv"
    uv.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    uv.chmod(0o755)
    return uv


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


def test_build_server_entry_uses_uv_with_directory(tmp_path):
    entry = build_server_entry(
        "/Users/x/Chem-draw-addon", uv_command=str(_fake_uv(tmp_path / "bin"))
    )
    assert entry["args"] == [
        "--directory",
        "/Users/x/Chem-draw-addon",
        "run",
        "chemdraw-tool-server",
    ]


def test_build_server_entry_rejects_relative_path():
    with pytest.raises(ValueError, match="absolut"):
        build_server_entry("relativer/pfad")


# --- uv-Auflösung -----------------------------------------------------------
# Claude Desktop startet MCP-Server nicht in einer Login-Shell, sondern mit dem
# minimalen GUI-/launchd-PATH. Ein blankes "uv" als command ist dort nicht
# auflösbar → "Server startet nicht", ohne verwertbare Fehlermeldung.


def test_build_server_entry_writes_absolute_existing_command(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    entry = build_server_entry("/Users/x/proj", uv_command=str(uv))
    command = Path(entry["command"])
    assert command.is_absolute(), (
        f"command muss absolut sein, war: {entry['command']!r}"
    )
    assert command.exists(), "command muss auf ein existierendes Binary zeigen"
    assert entry["command"] == str(uv)


def test_build_server_entry_resolves_real_uv_when_available():
    """Ohne Vorgabe muss der echte uv-Pfad aus dem PATH landen — nicht "uv"."""
    real_uv = shutil.which("uv")
    if real_uv is None:
        pytest.skip("uv nicht im PATH dieser Maschine")
    assert build_server_entry("/Users/x/proj")["command"] == real_uv


def test_resolve_uv_command_uses_which(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    assert resolve_uv_command(which=lambda _: str(uv)) == str(uv)


def test_resolve_uv_command_prefers_explicit_path(tmp_path):
    """install.sh kennt den tatsächlich benutzten uv-Pfad (ggf. frisch nach
    ~/.local/bin installiert) und reicht ihn durch — der gewinnt."""
    explicit = _fake_uv(tmp_path / "explicit")
    other = _fake_uv(tmp_path / "path")
    assert resolve_uv_command(str(explicit), which=lambda _: str(other)) == str(
        explicit
    )


def test_resolve_uv_command_probes_known_install_locations(tmp_path):
    """uv liegt da, steht aber nicht im PATH (keg-only/GUI-PATH-Fall)."""
    uv = _fake_uv(tmp_path / "opt")
    assert resolve_uv_command(which=lambda _: None, candidates=(uv,)) == str(uv)


def test_resolve_uv_command_skips_non_executable_candidates(tmp_path):
    dead = tmp_path / "dead" / "uv"
    dead.parent.mkdir(parents=True)
    dead.write_text("kein Binary\n", encoding="utf-8")
    dead.chmod(0o644)
    good = _fake_uv(tmp_path / "good")
    assert resolve_uv_command(
        str(dead), which=lambda _: None, candidates=(dead, good)
    ) == str(good)


def test_resolve_uv_command_falls_back_to_bare_uv_without_crashing():
    assert resolve_uv_command(which=lambda _: None, candidates=()) == "uv"


# --- Verifikation nach dem Schreiben ----------------------------------------


def test_verify_entry_names_the_resolved_start_command(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    line = verify_entry(build_server_entry("/Users/x/proj", uv_command=str(uv)))
    assert line.startswith("✓")
    assert str(uv) in line


def test_verify_entry_warns_when_command_is_not_resolvable():
    line = verify_entry({"command": "uv", "args": []})
    assert line.startswith("⚠")
    assert "PATH" in line


# --- install() IO-Schicht ---------------------------------------------------


def test_install_creates_config_when_absent(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    cfg = tmp_path / "Claude" / "claude_desktop_config.json"
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    data = json.loads(cfg.read_text())
    assert data["mcpServers"]["chemdraw-tool"]["command"] == str(uv)
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
