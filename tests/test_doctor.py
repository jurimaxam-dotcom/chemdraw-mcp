"""Tests für `chemdraw-doctor` — die Installations-Diagnose.

Kern-Risiko dieses Kommandos ist nicht "es findet ein Problem nicht", sondern
"es meldet ein Problem, wo keins ist": ein nicht installiertes Claude Desktop,
fehlendes Netz oder fehlendes Java sind legitime Zustände. Wer hier Fehlalarme
produziert, macht die Diagnose wertlos. Deshalb prüfen die Tests vor allem die
EINSTUFUNG (ok / note / limited / error) und den Exit-Code.

Kein Netz, kein Schreiben nach ~/ChemDraw-Output, kein echtes Claude Desktop:
alle Abhängigkeiten werden injiziert.
"""

import json
import os
import stat
from pathlib import Path

import pytest
import requests

from chemdraw_tool.doctor import (
    DEFAULT_CHECKS,
    ERROR,
    LIMITED,
    NOTE,
    OK,
    CheckResult,
    check_desktop_config,
    check_java,
    check_network,
    check_output_dir,
    check_rendering,
    check_uv,
    exit_code,
    format_report,
    main,
    run_checks,
    summarize,
)


def _executable(path: Path) -> Path:
    """Legt eine ausführbare Dummy-Datei an (kein echtes Binary nötig)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def _write_config(path: Path, data: dict | str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = data if isinstance(data, str) else json.dumps(data)
    path.write_text(text, encoding="utf-8")
    return path


# --- Pfad-Darstellung ---------------------------------------------------------


def test_paths_in_prose_are_shortened_to_tilde():
    """Kürzer heißt: passt in eine Zeile und wird nicht mitten im Pfad umbrochen."""
    from chemdraw_tool.doctor import _short

    assert _short("/Users/x/Library/Claude/config.json", home="/Users/x") == (
        "~/Library/Claude/config.json"
    )


def test_paths_outside_home_stay_absolute():
    from chemdraw_tool.doctor import _short

    assert _short("/etc/claude.json", home="/Users/x") == "/etc/claude.json"


# --- Java / OPSIN -------------------------------------------------------------


def test_java_present_is_ok():
    result = check_java(java_available=lambda: True)
    assert result.status == OK
    assert result.fix is None


def test_java_missing_is_a_limitation_not_an_error():
    """Ohne JRE läuft alles weiter — nur online statt offline."""
    result = check_java(java_available=lambda: False, platform="darwin")
    assert result.status == LIMITED
    assert "brew install openjdk" in result.fix


def test_java_fix_command_is_platform_specific():
    linux = check_java(java_available=lambda: False, platform="linux")
    assert "brew" not in linux.fix
    assert "jre" in linux.fix.lower() or "jdk" in linux.fix.lower()


def test_java_check_uses_the_resolver_probe_by_default():
    """Keine zweite Java-Suche im Projekt: der Default ist die Resolver-Logik."""
    from chemdraw_tool import resolver
    from chemdraw_tool.doctor import _default_java_probe

    assert _default_java_probe is resolver._java_runtime_available


# --- uv -----------------------------------------------------------------------


def test_uv_resolved_to_absolute_path_is_ok(tmp_path):
    uv = _executable(tmp_path / "bin" / "uv")
    result = check_uv(resolve=lambda: str(uv))
    assert result.status == OK
    assert str(uv) in result.detail


def test_uv_unresolvable_is_a_limitation_with_install_command():
    """resolve_uv_command() fällt auf das blanke "uv" zurück, wenn nichts da ist."""
    result = check_uv(resolve=lambda: "uv")
    assert result.status == LIMITED
    assert "astral.sh" in result.fix


def test_uv_check_defaults_to_the_installer_resolver():
    """Kein zweiter uv-Suchpfad: der Default kommt aus desktop_config."""
    from chemdraw_tool.desktop_config import resolve_uv_command
    from chemdraw_tool.doctor import _installer_helpers

    helpers = _installer_helpers()
    assert helpers is not None
    assert helpers.resolve_uv_command is resolve_uv_command


# --- Claude-Desktop-Config ----------------------------------------------------


def test_missing_desktop_config_is_neutral_information(tmp_path):
    """Claude Desktop nicht installiert = völlig legitim, kein Fehler."""
    result = check_desktop_config(config_path=tmp_path / "nope" / "config.json")
    assert result.status == NOTE
    assert exit_code([result]) == 0


def test_missing_desktop_config_says_other_clients_are_fine(tmp_path):
    result = check_desktop_config(config_path=tmp_path / "nope" / "config.json")
    assert "Claude Code" in result.detail


def test_broken_json_in_desktop_config_is_an_error(tmp_path):
    path = _write_config(tmp_path / "config.json", "{ not json")
    result = check_desktop_config(config_path=path)
    assert result.status == ERROR
    assert str(path) in result.detail


def test_desktop_config_without_our_entry_is_a_limitation(tmp_path):
    path = _write_config(tmp_path / "config.json", {"mcpServers": {"other": {}}})
    result = check_desktop_config(config_path=path)
    assert result.status == LIMITED
    assert "install.sh" in result.fix


def test_desktop_entry_with_missing_command_is_an_error(tmp_path):
    path = _write_config(
        tmp_path / "config.json",
        {"mcpServers": {"chemdraw-tool": {"command": "uv", "args": ["run"]}}},
    )
    result = check_desktop_config(config_path=path)
    assert result.status == ERROR
    assert "chemdraw-install" in result.fix


def test_desktop_entry_with_non_executable_command_is_an_error(tmp_path):
    binary = tmp_path / "bin" / "uv"
    binary.parent.mkdir(parents=True)
    binary.write_text("nope", encoding="utf-8")
    binary.chmod(stat.S_IRUSR)
    path = _write_config(
        tmp_path / "config.json",
        {"mcpServers": {"chemdraw-tool": {"command": str(binary)}}},
    )
    assert check_desktop_config(config_path=path).status == ERROR


def test_working_desktop_entry_is_ok(tmp_path):
    uv = _executable(tmp_path / "bin" / "uv")
    path = _write_config(
        tmp_path / "config.json",
        {"mcpServers": {"chemdraw-tool": {"command": str(uv), "args": ["run"]}}},
    )
    result = check_desktop_config(config_path=path)
    assert result.status == OK
    assert str(uv) in result.detail


# --- Netz ---------------------------------------------------------------------


class _Probe:
    """Fake für den Netz-Test: pro URL entweder ok oder eine Exception."""

    def __init__(self, failures: dict[str, Exception] | None = None):
        self.failures = failures or {}
        self.seen: list[str] = []

    def __call__(self, url: str) -> None:
        self.seen.append(url)
        for fragment, exc in self.failures.items():
            if fragment in url:
                raise exc


def test_network_uses_the_same_tolerance_as_the_resolver():
    """Strenger prüfen als der Server arbeitet ⇒ Fehlalarm. NCI braucht real >10 s."""
    from chemdraw_tool import doctor, resolver

    assert doctor._NET_TIMEOUT == resolver._TIMEOUT


def test_network_all_sources_reachable_is_ok():
    result = check_network(probe=_Probe())
    assert result.status == OK


def test_network_completely_offline_is_a_limitation_not_an_error():
    """Offline gehen SMILES (und mit Java auch IUPAC-Namen) weiter."""
    probe = _Probe(
        {
            "pubchem": requests.exceptions.ConnectionError("no route"),
            "cactus": requests.exceptions.ConnectionError("no route"),
        }
    )
    result = check_network(probe=probe)
    assert result.status == LIMITED
    assert "SMILES" in result.detail
    assert exit_code([result]) == 0


def test_network_partial_outage_names_the_dead_source():
    probe = _Probe({"cactus": requests.exceptions.ConnectionError("no route")})
    result = check_network(probe=probe)
    assert result.status == LIMITED
    assert "NCI" in result.detail
    assert "PubChem" in result.detail


def test_network_source_errors_are_distinguished_from_being_offline():
    """HTTP 500 heißt: erreichbar, aber deren Problem — anderer Rat."""
    response = requests.Response()
    response.status_code = 500
    http_error = requests.exceptions.HTTPError("boom", response=response)
    probe = _Probe({"pubchem": http_error, "cactus": http_error})
    result = check_network(probe=probe)
    assert result.status == LIMITED
    assert "500" in result.detail


def test_network_check_probes_both_resolver_sources():
    probe = _Probe()
    check_network(probe=probe)
    assert any("pubchem" in url for url in probe.seen)
    assert any("cactus" in url for url in probe.seen)


# --- Ausgabeverzeichnis -------------------------------------------------------


def test_output_dir_existing_and_writable_is_ok(tmp_path):
    target = tmp_path / "ChemDraw-Output"
    target.mkdir()
    result = check_output_dir(root=target)
    assert result.status == OK


def test_output_dir_missing_but_creatable_is_ok(tmp_path):
    result = check_output_dir(root=tmp_path / "ChemDraw-Output")
    assert result.status == OK
    assert "created" in result.detail.lower()


def test_output_dir_check_creates_nothing(tmp_path):
    target = tmp_path / "ChemDraw-Output"
    check_output_dir(root=target)
    assert not target.exists(), "Die Diagnose darf nichts anlegen"


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignoriert Schreibrechte")
def test_output_dir_not_writable_is_an_error(tmp_path):
    target = tmp_path / "ChemDraw-Output"
    target.mkdir()
    target.chmod(0o500)
    try:
        result = check_output_dir(root=target)
    finally:
        target.chmod(0o700)
    assert result.status == ERROR
    assert "chmod" in result.fix


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignoriert Schreibrechte")
def test_output_dir_uncreatable_parent_is_an_error(tmp_path):
    parent = tmp_path / "locked"
    parent.mkdir()
    parent.chmod(0o500)
    try:
        result = check_output_dir(root=parent / "ChemDraw-Output")
    finally:
        parent.chmod(0o700)
    assert result.status == ERROR


# --- RDKit-Rendering ----------------------------------------------------------


class ArgumentError(Exception):
    """Stellvertreter für Boost.Pythons ArgumentError."""


def test_rendering_producing_png_bytes_is_ok():
    result = check_rendering(render=lambda smiles: b"\x89PNG\r\n\x1a\n" + b"x" * 40)
    assert result.status == OK


def test_rendering_raising_boost_signature_error_is_an_error():
    """Stale Server-Prozess: gemischte Module → Boost-Signaturfehler."""

    def broken(smiles):
        raise ArgumentError("Python argument types did not match C++ signature")

    result = check_rendering(render=broken)
    assert result.status == ERROR
    assert "restart" in result.fix.lower()


def test_rendering_returning_garbage_is_an_error():
    result = check_rendering(render=lambda smiles: b"not a png")
    assert result.status == ERROR


# --- Einstufung, Exit-Code, Bericht -------------------------------------------


def _result(status: str, fix: str | None = "do something") -> CheckResult:
    return CheckResult(name="X", status=status, detail="detail", fix=fix)


def test_exit_code_is_zero_when_only_limitations():
    results = [_result(OK, None), _result(NOTE, None), _result(LIMITED)]
    assert exit_code(results) == 0


def test_exit_code_is_non_zero_on_a_real_error():
    assert exit_code([_result(OK, None), _result(ERROR)]) != 0


def test_summary_is_a_single_sentence_per_case():
    for results in (
        [_result(OK, None)],
        [_result(LIMITED)],
        [_result(ERROR)],
    ):
        sentence = summarize(results)
        assert sentence.count(".") == 1, sentence
        assert sentence.endswith(".")


def test_summary_distinguishes_usable_from_broken():
    assert "not" in summarize([_result(ERROR)]).lower()
    assert "usable" in summarize([_result(LIMITED)]).lower()
    assert "usable" in summarize([_result(OK, None)]).lower()


def test_report_marks_the_three_levels_distinguishably_without_colour():
    report = format_report(
        [
            CheckResult("A", OK, "fine"),
            CheckResult("B", NOTE, "neutral"),
            CheckResult("C", LIMITED, "degraded", fix="brew install openjdk"),
            CheckResult("D", ERROR, "broken", fix="uv sync"),
        ]
    )
    assert "\x1b[" not in report, "Keine ANSI-Farben — die Ausgabe kann in eine Datei laufen"
    markers = {line.strip().split()[0] for line in report.splitlines() if line.startswith("[")}
    assert len(markers) == 4, report


def test_report_shows_the_exact_fix_command_for_every_problem():
    report = format_report(
        [
            CheckResult("C", LIMITED, "degraded", fix="brew install openjdk"),
            CheckResult("D", ERROR, "broken", fix="uv sync"),
        ]
    )
    assert "brew install openjdk" in report
    assert "uv sync" in report
    assert report.count("Fix:") == 2


def test_report_ends_with_the_summary():
    report = format_report([CheckResult("A", OK, "fine")])
    assert report.rstrip().endswith(summarize([CheckResult("A", OK, "fine")]))


def test_run_checks_returns_one_result_per_check():
    results = run_checks(checks=[lambda: _result(OK, None), lambda: _result(LIMITED)])
    assert [r.status for r in results] == [OK, LIMITED]


def test_a_crashing_check_becomes_an_error_instead_of_a_traceback():
    def explodes():
        raise RuntimeError("kaputt")

    results = run_checks(checks=[explodes])
    assert results[0].status == ERROR
    assert "kaputt" in results[0].detail


def test_main_prints_report_and_returns_exit_code(capsys):
    code = main(argv=[], checks=[lambda: CheckResult("A", ERROR, "broken", fix="uv sync")])
    out = capsys.readouterr().out
    assert code != 0
    assert "uv sync" in out
    assert summarize([CheckResult("A", ERROR, "broken")]) in out


def test_default_checks_cover_every_documented_failure_mode():
    """Die sechs realen Fehlerbilder des Projekts — keins darf wegfallen."""
    assert {check.__name__ for check in DEFAULT_CHECKS} == {
        "check_rendering",
        "check_java",
        "check_uv",
        "check_desktop_config",
        "check_network",
        "check_output_dir",
    }
