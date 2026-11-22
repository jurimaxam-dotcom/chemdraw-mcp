"""Tests für die Claude-Desktop-Config-Merge-Logik des Installers.

Kern-Risiko: den Eintrag hinzufügen, ohne bestehende MCP-Server (z.B. einen
andere bereits konfigurierte lokale Server zu zerstören; idempotent bei Re-Run;
immer valides JSON. Reine Funktion, kein Datei-IO, kein Netz.
"""

import json
import shutil
from pathlib import Path

import pytest

from chempane.desktop_config import (
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
        "chempane",
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
    assert data["mcpServers"]["chempane"]["command"] == str(uv)
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
    assert "chempane" in data["mcpServers"]
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


# --- Zwei Konnektoren (Welle 3, Entscheidung 06.11.2026) ------------------
# Claude Desktop bekommt zwei Einträge aus demselben Paket: `chemdraw` mit dem
# Standardprofil (18 Tools) und `chemdraw-pharma` mit dem Profil `pharma`
# (seit 16.11.2026: nur die 7 Zusatz-Tools plus die 2 Panel-Helfer, vorher das
# Vollprofil — beide an hieß 18 Tools doppelt). Das Profil steht fest im
# Eintrag (env); beide Konnektoren zusammen ergeben den vollen Satz.


def test_exactly_two_connectors_with_fixed_profiles():
    from chempane.desktop_config import CONNECTORS

    assert CONNECTORS == {"chempane": "mvp", "chempane-pharma": "pharma"}


def test_connector_profiles_are_profiles_the_server_knows():
    from chempane.desktop_config import CONNECTORS, PROFILES
    from chempane.server import PROFILES as SERVER_PROFILES

    assert set(CONNECTORS.values()) <= PROFILES == SERVER_PROFILES


def test_install_rewrites_a_pharma_connector_on_the_full_profile(tmp_path):
    """Installationen vom 07.–16.11.2026 tragen `chemdraw-pharma` mit `full`:
    beide Konnektoren an zeigte dem Modell 18 Tools doppelt. Ein erneuter
    Installer-Lauf schreibt den Eintrag auf `pharma` um."""
    uv = _fake_uv(tmp_path / "bin")
    cfg = tmp_path / "claude_desktop_config.json"
    alt = {"command": str(uv), "args": ["run"], "env": {"CHEMDRAW_PROFILE": "full"}}
    cfg.write_text(json.dumps({"mcpServers": {"chemdraw-pharma": alt}}), encoding="utf-8")
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    servers = json.loads(cfg.read_text())["mcpServers"]
    assert servers["chempane-pharma"]["env"] == {"CHEMPANE_PROFILE": "pharma"}
    assert servers["chempane"]["env"] == {"CHEMPANE_PROFILE": "mvp"}
    assert "chemdraw-pharma" not in servers


def test_build_server_entry_pins_the_profile_in_env(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    entry = build_server_entry("/Users/x/proj", uv_command=str(uv), profile="full")
    assert entry["env"] == {"CHEMPANE_PROFILE": "full"}
    assert entry["args"] == [
        "--directory",
        "/Users/x/proj",
        "run",
        "chempane",
    ]


def test_build_server_entry_defaults_to_the_mvp_profile(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    assert build_server_entry("/Users/x/proj", uv_command=str(uv))["env"] == {
        "CHEMPANE_PROFILE": "mvp"
    }


def test_build_server_entry_rejects_unknown_profile(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    with pytest.raises(ValueError, match="mvp"):
        build_server_entry("/Users/x/proj", uv_command=str(uv), profile="typo")


def test_build_installed_entry_pins_the_profile(tmp_path):
    from chempane.desktop_config import build_installed_entry

    launcher = _fake_uv(tmp_path / "bin")
    entry = build_installed_entry(launcher=str(launcher), profile="full")
    assert entry["command"] == str(launcher)
    assert entry["env"] == {"CHEMPANE_PROFILE": "full"}


def test_install_writes_both_connectors(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    cfg = tmp_path / "claude_desktop_config.json"
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    servers = json.loads(cfg.read_text())["mcpServers"]
    assert set(servers) == {"chempane", "chempane-pharma"}
    assert servers["chempane"]["env"] == {"CHEMPANE_PROFILE": "mvp"}
    assert servers["chempane-pharma"]["env"] == {"CHEMPANE_PROFILE": "pharma"}
    for entry in servers.values():
        assert entry["command"] == str(uv)
        assert entry["args"] == [
            "--directory",
            "/Users/x/proj",
            "run",
            "chempane",
        ]


def test_install_migrates_the_old_chemdraw_tool_entry(tmp_path):
    """Vor Welle 3 hieß der einzige Eintrag `chemdraw-tool`. Der Installer ersetzt
    ihn kontrolliert — sonst stünden drei ChemDraw-Konnektoren im Menü."""
    uv = _fake_uv(tmp_path / "bin")
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "chemdraw-tool": {
                        "command": "uv",
                        "args": ["run", "chemdraw-tool-server"],
                    },
                    "concepts": {"command": "python", "args": ["s.py"]},
                },
                "preferences": {"x": 1},
            }
        ),
        encoding="utf-8",
    )
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    data = json.loads(cfg.read_text())
    assert set(data["mcpServers"]) == {"chempane", "chempane-pharma", "concepts"}
    assert data["mcpServers"]["concepts"] == {"command": "python", "args": ["s.py"]}
    assert data["preferences"] == {"x": 1}
    backup = json.loads(cfg.with_suffix(".json.bak").read_text())
    assert "chemdraw-tool" in backup["mcpServers"], "Backup hält den alten Eintrag"


def test_install_twice_migration_stays_stable(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text(
        json.dumps({"mcpServers": {"chemdraw-tool": {"command": "uv"}}}),
        encoding="utf-8",
    )
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    first = cfg.read_text()
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    assert cfg.read_text() == first


# --- Umbenennung chemdraw → chempane (22.11.2026) --------------------------
# Die Konnektoren hießen bis 0.11.3 `chemdraw` und `chemdraw-pharma`. Der Installer
# ersetzt sie durch `chempane`/`chempane-pharma` — sonst stünden vier Einträge mit
# denselben Tools im Menü. Was der Nutzer selbst in den alten Eintrag geschrieben
# hat (zusätzliche env-Werte), wandert mit; das Profil schreibt der Installer neu.


def _old_config(cfg: Path, uv: Path) -> None:
    cfg.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "chemdraw": {
                        "command": str(uv),
                        "args": ["--directory", "/Users/x/proj", "run", "chemdraw-tool-server"],
                        "env": {"CHEMDRAW_PROFILE": "mvp", "CHEMDRAW_SMILES_LOOKUP": "1"},
                    },
                    "chemdraw-pharma": {
                        "command": str(uv),
                        "args": ["--directory", "/Users/x/proj", "run", "chemdraw-tool-server"],
                        "env": {"CHEMDRAW_PROFILE": "pharma", "CHEMDRAW_VAULT_PATH": "/notes"},
                    },
                    "concepts": {"command": "python", "args": ["s.py"]},
                },
                "preferences": {"x": 1},
            }
        ),
        encoding="utf-8",
    )


def test_install_replaces_the_chemdraw_connectors_with_chempane(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    cfg = tmp_path / "claude_desktop_config.json"
    _old_config(cfg, uv)
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    data = json.loads(cfg.read_text())
    assert set(data["mcpServers"]) == {"chempane", "chempane-pharma", "concepts"}
    assert data["mcpServers"]["concepts"] == {"command": "python", "args": ["s.py"]}
    assert data["preferences"] == {"x": 1}
    backup = json.loads(cfg.with_suffix(".json.bak").read_text())
    assert {"chemdraw", "chemdraw-pharma"} <= set(backup["mcpServers"]), "Backup hält die alten Einträge"


def test_migration_keeps_the_users_own_env_values(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    cfg = tmp_path / "claude_desktop_config.json"
    _old_config(cfg, uv)
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    servers = json.loads(cfg.read_text())["mcpServers"]
    assert servers["chempane"]["env"] == {"CHEMPANE_PROFILE": "mvp", "CHEMDRAW_SMILES_LOOKUP": "1"}
    assert servers["chempane-pharma"]["env"] == {"CHEMPANE_PROFILE": "pharma", "CHEMDRAW_VAULT_PATH": "/notes"}


def test_migration_is_idempotent(tmp_path):
    uv = _fake_uv(tmp_path / "bin")
    cfg = tmp_path / "claude_desktop_config.json"
    _old_config(cfg, uv)
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    first = cfg.read_text()
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    assert cfg.read_text() == first


def test_legacy_names_cover_both_old_connectors():
    from chempane.desktop_config import LEGACY_SERVER_NAMES

    assert {"chemdraw-tool", "chemdraw", "chemdraw-pharma"} <= set(LEGACY_SERVER_NAMES)


def test_installed_entry_prefers_the_chempane_launcher(tmp_path, monkeypatch):
    """Im venv liegen nach der Umbenennung beide Startskripte; eingetragen wird das neue."""
    from chempane import desktop_config

    venv_bin = tmp_path / "venv" / "bin"
    for name in ("chemdraw-mcp", "chempane", "chemdraw-tool-server"):
        _fake_uv(venv_bin).rename(venv_bin / name)
    monkeypatch.setattr(desktop_config.sys, "executable", str(venv_bin / "python"))
    entry = desktop_config.build_installed_entry(profile="mvp")
    assert entry["command"] == str(venv_bin / "chempane")


def test_migration_backs_up_the_old_entries_even_when_a_bak_exists(tmp_path):
    """Wer schon einmal installiert hat, hat eine .bak von damals — sie wird bewusst nicht
    überschrieben. Die Umbenennung löscht aber Einträge; die müssen trotzdem gesichert sein."""
    uv = _fake_uv(tmp_path / "bin")
    cfg = tmp_path / "claude_desktop_config.json"
    _old_config(cfg, uv)
    alt_bak = cfg.with_suffix(".json.bak")
    alt_bak.write_text('{"mcpServers": {}}', encoding="utf-8")
    install("/Users/x/proj", config_path=cfg, uv_command=str(uv))
    assert alt_bak.read_text(encoding="utf-8") == '{"mcpServers": {}}', "erste .bak bleibt"
    sicherung = cfg.with_suffix(".json.vor-chempane.bak")
    assert sicherung.exists(), "Stand vor der Umbenennung fehlt"
    assert {"chemdraw", "chemdraw-pharma"} <= set(json.loads(sicherung.read_text())["mcpServers"])
