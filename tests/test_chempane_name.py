"""Umbenennung chemdraw-mcp → chempane, Etappe 1: der Name nach außen.

Neu wird geschrieben, alt wird weiter gelesen (Plan § Entscheidungen, 22.11.2026):
- Umgebungsvariablen: CHEMPANE_* gilt, CHEMDRAW_* wird gelesen, die neue gewinnt.
- Ausgabeordner: ~/chempane-output; nur wenn der fehlt und ~/ChemDraw-Output da ist,
  bleibt der alte in Gebrauch. Nichts wird verschoben.
- Cache: …/chempane, der alte wird nicht übernommen.
- serverInfo.version kommt aus dem Paket chempane, nicht aus der Hülle chemdraw-mcp
  (Etappe 0, Befund 3: die Hülle meldete sonst ihre eigene Version).
"""

import re
import tomllib
from pathlib import Path

import pytest

from chempane import settings

ROOT = Path(__file__).resolve().parent.parent


# --- Umgebungsvariablen ------------------------------------------------------------------


def test_new_env_var_is_read(monkeypatch):
    monkeypatch.delenv("CHEMDRAW_PROFILE", raising=False)
    monkeypatch.setenv("CHEMPANE_PROFILE", "pharma")
    assert settings.env("PROFILE") == "pharma"


def test_old_env_var_is_still_read(monkeypatch):
    monkeypatch.delenv("CHEMPANE_PROFILE", raising=False)
    monkeypatch.setenv("CHEMDRAW_PROFILE", "full")
    assert settings.env("PROFILE") == "full"


def test_new_env_var_wins_over_the_old_one(monkeypatch):
    monkeypatch.setenv("CHEMPANE_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CHEMDRAW_LOG_LEVEL", "WARNING")
    assert settings.env("LOG_LEVEL") == "DEBUG"


def test_env_default_when_neither_is_set(monkeypatch):
    monkeypatch.delenv("CHEMPANE_PROFILE", raising=False)
    monkeypatch.delenv("CHEMDRAW_PROFILE", raising=False)
    assert settings.env("PROFILE", "mvp") == "mvp"


def test_legacy_vars_in_use_names_only_old_ones_without_a_new_twin():
    environ = {"CHEMDRAW_PROFILE": "mvp", "CHEMDRAW_LOG_LEVEL": "DEBUG", "CHEMPANE_LOG_LEVEL": "INFO"}
    assert settings.legacy_vars_in_use(environ) == ["CHEMDRAW_PROFILE"]


def test_old_smiles_lookup_var_still_switches_the_lookup_on(monkeypatch):
    from chempane import privacy

    monkeypatch.delenv("CHEMPANE_SMILES_LOOKUP", raising=False)
    monkeypatch.setenv("CHEMDRAW_SMILES_LOOKUP", "1")
    assert privacy.smiles_lookup_enabled()


def test_profile_from_a_config_entry_reads_both_names():
    assert settings.profile_from_env({"CHEMPANE_PROFILE": "pharma"}) == "pharma"
    assert settings.profile_from_env({"CHEMDRAW_PROFILE": "pharma"}) == "pharma"
    assert settings.profile_from_env({"CHEMPANE_PROFILE": "mvp", "CHEMDRAW_PROFILE": "full"}) == "mvp"
    assert settings.profile_from_env({}) == "mvp"
    assert settings.profile_from_env(None) == "mvp"


def test_server_profile_follows_the_new_env_var(monkeypatch):
    import asyncio

    from chempane.server import create_server

    monkeypatch.delenv("CHEMDRAW_PROFILE", raising=False)
    monkeypatch.setenv("CHEMPANE_PROFILE", "pharma")
    tools = asyncio.run(create_server().list_tools())
    assert len(tools) == 9


def test_no_module_reads_a_chemdraw_env_var_directly():
    """Eine Lesestelle für alle Produktvariablen — sonst gilt die neue nur halb."""
    offenders = []
    for path in (ROOT / "chempane").rglob("*.py"):
        if path.name == "settings.py":
            continue
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"(environ(\.get)?|getenv)\s*[\[(]\s*[\"'](CHEMDRAW|CHEMPANE)_", text):
            offenders.append(f"{path.relative_to(ROOT)}: {match.group(0)}")
    assert offenders == []


# --- Ausgabeordner -----------------------------------------------------------------------


def test_output_root_is_new_on_a_fresh_machine(tmp_path):
    assert settings.output_root(tmp_path) == tmp_path / "chempane-output"


def test_output_root_keeps_the_old_folder_when_only_it_exists(tmp_path):
    (tmp_path / "ChemDraw-Output").mkdir()
    assert settings.output_root(tmp_path) == tmp_path / "ChemDraw-Output"


def test_output_root_prefers_the_new_folder_when_both_exist(tmp_path):
    (tmp_path / "ChemDraw-Output").mkdir()
    (tmp_path / "chempane-output").mkdir()
    assert settings.output_root(tmp_path) == tmp_path / "chempane-output"


def test_server_output_dirs_hang_below_the_output_root():
    from chempane import server

    for name in ("OUTPUT_DIR", "SPECTRUM_DIR", "TLC_DIR", "SCOPE_DIR", "ANKI_DIR", "PLOT_DIR", "THREED_DIR", "PROTEIN_DIR"):
        assert getattr(server, name).parent == server.REACTION_DIR, name
    assert server.REACTION_DIR == settings.output_root()


def test_doctor_checks_the_same_output_root():
    from chempane import doctor

    assert doctor.OUTPUT_ROOT == settings.output_root()


def test_doctor_notes_the_old_output_folder_in_use(tmp_path):
    from chempane import doctor

    old = tmp_path / "ChemDraw-Output"
    old.mkdir()
    result = doctor.check_output_dir(root=old)
    assert "chempane-output" in result.detail


def test_doctor_names_legacy_env_vars(monkeypatch):
    from chempane import doctor

    monkeypatch.delenv("CHEMPANE_LOG_LEVEL", raising=False)
    monkeypatch.setenv("CHEMDRAW_LOG_LEVEL", "DEBUG")
    result = doctor.check_legacy_env()
    assert "CHEMDRAW_LOG_LEVEL" in result.detail
    assert "CHEMPANE_LOG_LEVEL" in result.detail


def test_doctor_is_quiet_without_legacy_env_vars(monkeypatch):
    from chempane import doctor

    for var in settings.PRODUCT_VARS:
        monkeypatch.delenv(f"CHEMDRAW_{var}", raising=False)
    assert doctor.check_legacy_env().status == doctor.OK


# --- Cache und Version -------------------------------------------------------------------


def test_panel_part_cache_lives_under_chempane():
    from chempane import result_budget

    assert result_budget._DEFAULT_STORE_DIR.parts[-2:] == ("chempane", "panel-parts")


def test_server_reports_the_chempane_version(monkeypatch):
    from chempane import server

    asked = []

    def fake_version(name):
        asked.append(name)
        return "9.9.9"

    monkeypatch.setattr(server, "_pkg_version", fake_version)
    instance = server.create_server("mvp")
    assert asked == ["chempane"]
    assert instance._lowlevel_server.version == "9.9.9"


def test_doctor_header_names_chempane(monkeypatch):
    from chempane import doctor

    assert doctor._environment_header().startswith("chempane doctor — ")


# --- Paket und Befehle -------------------------------------------------------------------


@pytest.fixture(scope="module")
def project():
    return tomllib.load((ROOT / "pyproject.toml").open("rb"))["project"]


def test_distribution_is_named_chempane(project):
    assert project["name"] == "chempane"


def test_new_commands_exist(project):
    scripts = project["scripts"]
    assert scripts["chempane"] == "chempane.server:main"
    assert scripts["chempane-install"] == "chempane.desktop_config:main"
    assert scripts["chempane-doctor"] == "chempane.doctor:main"


def test_old_commands_stay_as_aliases_until_1_0(project):
    scripts = project["scripts"]
    assert scripts["chemdraw-mcp"] == "chempane.server:main"
    assert scripts["chemdraw-tool-server"] == "chempane.server:main"
    assert scripts["chemdraw-install"] == "chempane.desktop_config:main"
    assert scripts["chemdraw-doctor"] == "chempane.doctor:main"


def test_server_info_name_is_chempane():
    """Der Name, den der Host in serverInfo sieht, trägt kein „ChemDraw“ mehr."""
    from chempane.server import create_server

    assert create_server("mvp").name == "chempane"
