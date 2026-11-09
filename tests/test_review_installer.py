"""Installer-Befunde aus dem Review 09.11.2026 (jeder Fall einmal rot gesehen)."""

import json
import os
import stat
import sys

import pytest

from chemdraw_tool import desktop_config


@pytest.mark.parametrize("content", ["[]", '"text"', "null", '{"mcpServers": null}', '{"mcpServers": []}'])
def test_config_that_is_json_but_not_the_expected_shape(tmp_path, content):
    """Gültiges JSON, falsche Form: Meldung statt AttributeError — und die Datei bleibt."""
    path = tmp_path / "claude_desktop_config.json"
    path.write_text(content, encoding="utf-8")
    if content == '{"mcpServers": null}':
        desktop_config.install_entries({"chemdraw": {"command": "/x"}}, path)
        assert json.loads(path.read_text())["mcpServers"]["chemdraw"] == {"command": "/x"}
        return
    with pytest.raises(ValueError, match="mcpServers|object"):
        desktop_config.install_entries({"chemdraw": {"command": "/x"}}, path)
    assert path.read_text(encoding="utf-8") == content


def test_first_backup_survives_a_second_install(tmp_path):
    """.bak soll den Stand VOR der ersten Installation halten, nicht den vor der letzten."""
    path = tmp_path / "claude_desktop_config.json"
    original = {"mcpServers": {"other": {"command": "/o"}}}
    path.write_text(json.dumps(original), encoding="utf-8")
    desktop_config.install_entries({"chemdraw": {"command": "/x"}}, path)
    desktop_config.install_entries({"chemdraw": {"command": "/y"}}, path)
    backup = json.loads(path.with_suffix(".json.bak").read_text(encoding="utf-8"))
    assert backup == original


def test_launcher_is_found_next_to_the_venv_interpreter(tmp_path, monkeypatch):
    """sys.executable einer venv ist ein Symlink auf das Basis-Python; das Startskript
    liegt neben dem Symlink, nicht neben dessen Ziel."""
    base = tmp_path / "base" / "bin"
    venv = tmp_path / "venv" / "bin"
    base.mkdir(parents=True)
    venv.mkdir(parents=True)
    real = base / "python"
    real.write_text("#!/bin/sh\n")
    real.chmod(real.stat().st_mode | stat.S_IEXEC)
    os.symlink(real, venv / "python")
    script = venv / "chemdraw-mcp"
    script.write_text("#!/bin/sh\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(sys, "executable", str(venv / "python"))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    entry = desktop_config.build_installed_entry()
    assert entry["command"] == str(script)
