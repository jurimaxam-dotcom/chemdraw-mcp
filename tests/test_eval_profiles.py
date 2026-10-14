"""Routing-Evals muessen genau das angebotene Profil messen."""

import importlib.util
from pathlib import Path

import pytest
import yaml

ROUTING = Path(__file__).resolve().parents[1] / "evals" / "tool-routing"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROUTING / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CASES = [
    {"id": "drawing", "expect": "generate_molecule"},
    {"id": "specialist", "expect": "calculate_content"},
]


def test_claude_runner_filters_cases_by_offered_tools():
    runner = _load("run_claude")
    assert runner.select_cases(CASES, {"generate_molecule"}, set()) == CASES[:1]
    assert runner.select_cases(CASES, {"generate_molecule", "calculate_content"}, set()) == CASES


@pytest.mark.parametrize("selection", [{"typo"}, {"specialist"}, {"drawing", "typo"}])
def test_explicit_unknown_or_disabled_cases_fail(selection):
    runner = _load("run_claude")
    with pytest.raises(ValueError):
        runner.select_cases(CASES, {"generate_molecule"}, selection)


def test_empty_profile_cannot_report_green():
    runner = _load("run_claude")
    with pytest.raises(ValueError):
        runner.select_cases(CASES, set(), set())


def test_promptfoo_build_filters_by_exported_tool_names(tmp_path, monkeypatch):
    builder = _load("build_config")
    monkeypatch.setattr(builder, "HERE", tmp_path)
    cases = [dict(c, prompt="Draw aspirin", forbidden=["lookup"], why="Routing") for c in CASES]
    (tmp_path / "cases.yaml").write_text(yaml.safe_dump({"cases": cases}))
    (tmp_path / "tools.json").write_text('[{"name": "generate_molecule"}]')
    assert builder.main() == 0
    config = yaml.safe_load((tmp_path / "promptfooconfig.yaml").read_text())
    assert len(config["tests"]) == 1
    assert config["tests"][0]["description"].startswith("drawing:")


def test_promptfoo_rejects_empty_matching_suite(tmp_path, monkeypatch):
    builder = _load("build_config")
    monkeypatch.setattr(builder, "HERE", tmp_path)
    (tmp_path / "cases.yaml").write_text(yaml.safe_dump({"cases": [dict(c, prompt="Draw aspirin", forbidden=["lookup"], why="Routing") for c in CASES]}))
    (tmp_path / "tools.json").write_text('[{"name": "save_png"}]')
    with pytest.raises(SystemExit):
        builder.main()
    assert not (tmp_path / "promptfooconfig.yaml").exists()
