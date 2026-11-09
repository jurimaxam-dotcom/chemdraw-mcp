"""Fund (f), Durchsicht 09.11.2026: Installer sprach den Nutzer auf Deutsch an.

Projektregel: Nutzertext ist Englisch. Geprüft wird alles, was `chemdraw-install`
bzw. `install.sh` (samt dem eingebundenen `uv-holen.sh`) auf den Bildschirm
bringt — Erfolgszeilen, Warnungen, Fehlermeldungen, `--help`. Kommentare und
Docstrings bleiben Deutsch; sie sieht der Nutzer nicht.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from chemdraw_tool import desktop_config

ROOT = Path(__file__).resolve().parent.parent

# Merkmale deutschen Texts: Umlaute/ß oder typische Wörter aus den alten Meldungen.
_GERMAN = re.compile(
    r"[äöüÄÖÜß]|\b(nicht|bitte|registriert|neu starten|fertig|wählen|zeichne|startet|muss|"
    r"kein|keine|oder|und|der|das|mit|evtl|gefunden|fehlgeschlagen|prüfen|datei|wurde|"
    r"fehler|lade|geprüft|projekt|bereit|sauber|installieren|abbruch|erwartet|erhalten|"
    r"hinterlegt|vorhanden|entpacken|stimmt)\b",
    re.IGNORECASE,
)


def _german(text: str) -> list[str]:
    return [line for line in text.splitlines() if _GERMAN.search(line)]


def _fake_uv(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    uv = directory / "uv"
    uv.write_text("#!/bin/sh\n")
    uv.chmod(0o755)
    return uv


def test_chemdraw_install_spricht_englisch(tmp_path, monkeypatch, capsys):
    cfg = tmp_path / "Claude" / "claude_desktop_config.json"
    monkeypatch.setattr(desktop_config, "claude_config_path", lambda: cfg)
    uv = _fake_uv(tmp_path / "bin")
    monkeypatch.setattr(
        sys, "argv", ["chemdraw-install", "--project-dir", str(tmp_path), "--uv-command", str(uv)]
    )
    assert desktop_config.main() == 0
    out = capsys.readouterr()
    assert out.out.strip(), "Installer gibt nichts aus"
    assert _german(out.out + out.err) == []


def test_help_spricht_englisch(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["chemdraw-install", "--help"])
    with pytest.raises(SystemExit):
        desktop_config.main()
    assert _german(capsys.readouterr().out) == []


def test_warnung_bei_nicht_aufloesbarem_uv_spricht_englisch():
    line = desktop_config.verify_entry({"command": "uv", "args": []})
    assert _german(line) == []


def test_fehlermeldungen_sprechen_englisch(tmp_path, monkeypatch):
    messages = []
    with pytest.raises(ValueError) as exc:
        desktop_config.build_server_entry("relativ/pfad")
    messages.append(str(exc.value))
    with pytest.raises(ValueError) as exc:
        desktop_config.build_server_entry("/abs", profile="falsch")
    messages.append(str(exc.value))
    broken = tmp_path / "claude_desktop_config.json"
    broken.write_text("{kaputt")
    with pytest.raises(ValueError) as exc:
        desktop_config.install_entries({"chemdraw": {}}, broken)
    messages.append(str(exc.value))
    monkeypatch.setattr(sys, "executable", str(tmp_path / "nirgends" / "python"))
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(RuntimeError) as exc:
        desktop_config.build_installed_entry()
    messages.append(str(exc.value))
    assert _german("\n".join(messages)) == []


def _shell_output_lines(path: Path, pattern: str) -> str:
    """Die Zeilen eines Shellskripts, die etwas ausgeben (ohne Kommentare)."""
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if re.search(pattern, stripped):
            # Shell-Variablen ($erwartet, ${ist:-…}) sind Code, kein Nutzertext.
            lines.append(re.sub(r"\$\{?\w+", "$VAR", stripped))
    return "\n".join(lines)


def test_install_sh_spricht_englisch():
    text = _shell_output_lines(ROOT / "install.sh", r"^echo\b")
    assert text, "keine echo-Zeilen gefunden — Test misst nichts"
    assert _german(text) == []


def test_uv_holen_spricht_englisch():
    text = _shell_output_lines(ROOT / "mcpb" / "server" / "uv-holen.sh", r"^_uv_log\s+\"")
    assert text, "keine _uv_log-Zeilen gefunden — Test misst nichts"
    assert _german(text) == []


def test_konfiguration_bleibt_unveraendert(tmp_path, monkeypatch, capsys):
    """Nur der Text ändert sich: die geschriebenen Einträge bleiben dieselben."""
    cfg = tmp_path / "claude_desktop_config.json"
    monkeypatch.setattr(desktop_config, "claude_config_path", lambda: cfg)
    uv = _fake_uv(tmp_path / "bin")
    monkeypatch.setattr(
        sys, "argv", ["chemdraw-install", "--project-dir", str(tmp_path), "--uv-command", str(uv)]
    )
    desktop_config.main()
    servers = json.loads(cfg.read_text())["mcpServers"]
    assert set(servers) == {"chemdraw", "chemdraw-pharma"}
