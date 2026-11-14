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


# --- `--echt`: Lauf gegen den echten Server -------------------------------------------

def _echt(ergebnisse=None, verweigert=None):
    return {"ergebnisse": ergebnisse or {}, "verweigert": verweigert or [], "ids": {}}


def test_echt_gruen_braucht_aufruf_und_fehlerfreies_ergebnis():
    runner = _load("run_claude")
    assert runner.bewerte_echt("generate_3d", ["generate_3d"], _echt({"generate_3d": (False, '{"type": "structure3d"}')}))[0] == "grün"


def test_echt_rot_wenn_das_tool_nicht_gerufen_wurde():
    runner = _load("run_claude")
    assert runner.bewerte_echt("generate_3d", ["generate_molecule"], _echt({"generate_molecule": (False, "{}")}))[0] == "rot"
    assert runner.bewerte_echt("generate_3d", [], _echt())[0] == "rot"


def test_echt_rot_bei_verweigertem_aufruf_und_bei_fehlendem_ergebnis():
    runner = _load("run_claude")
    assert runner.bewerte_echt("generate_3d", ["generate_3d"], _echt(verweigert=["generate_3d"]))[0] == "rot"
    assert runner.bewerte_echt("generate_3d", ["generate_3d"], _echt())[0] == "rot"


def test_echt_serverfehler_ist_rot_quellenausfall_nur_gelb():
    runner = _load("run_claude")
    kaputt = _echt({"generate_molecule": (True, "invalid_smiles: could not parse")})
    assert runner.bewerte_echt("generate_molecule", ["generate_molecule"], kaputt)[0] == "rot"
    quelle = _echt({"generate_molecule": (True, "sources_down: PubChem could not be reached")})
    assert runner.bewerte_echt("generate_molecule", ["generate_molecule"], quelle)[0] == "gelb"


# Der Stub-Lauf über Claude Code prüfte bis 14.11.2026 nur Toolnamen: `required_args`
# und `forbidden_args` aus cases.yaml wertete allein der promptfoo-Weg aus. Ein Fall
# wie „Sessel → generate_molecule mit view=chair“ war damit grün, sobald das Tool fiel.
def test_stub_lauf_rot_wenn_verlangtes_argument_fehlt():
    runner = _load("run_claude")
    fall = {"expect": "generate_molecule", "required_args": {"view": "chair"}}
    assert runner.bewerte(fall, [("generate_molecule", {"name": "cyclohexane", "view": "chair"})]) == []
    maengel = runner.bewerte(fall, [("generate_molecule", {"name": "cyclohexane"})])
    assert maengel and "view" in maengel[0]


def test_stub_lauf_rot_bei_ungefragtem_argument_und_verbotenem_tool():
    runner = _load("run_claude")
    fall = {"expect": "generate_molecule", "forbidden": ["batch_generate"], "forbidden_args": ["stereo_variants"]}
    assert runner.bewerte(fall, [("generate_molecule", {"name": "x"})]) == []
    assert runner.bewerte(fall, [("generate_molecule", {"name": "x", "stereo_variants": True})])
    assert runner.bewerte(fall, [("generate_molecule", {"name": "x"}), ("batch_generate", {})])
    assert runner.bewerte(fall, [])


def test_stub_lauf_argumente_zaehlen_nur_am_erwarteten_tool():
    runner = _load("run_claude")
    fall = {"expect": "generate_molecule", "required_args": {"view": "chair"}}
    # Sessel plus drehbares Modell ist erlaubt; das zweite Tool braucht kein `view`.
    aufrufe = [("generate_molecule", {"name": "cyclohexane", "view": "chair"}), ("generate_3d", {"name": "cyclohexane"})]
    assert runner.bewerte(fall, aufrufe) == []


# Bis 14.11.2026 lief der Stub-Lauf ohne `--allowedTools`: Claude Code verweigerte jeden
# Aufruf („you haven't granted it yet“), die Attrappe antwortete nie, und Zug 2 war die
# Reaktion des Modells auf eine Verweigerung statt auf ein Ergebnis. Die Attrappe führt
# nichts aus, also darf jedes angebotene Tool ohne Rückfrage laufen.
def test_stub_lauf_gibt_alle_angebotenen_tools_frei_und_bleibt_bei_zwei_zuegen():
    runner = _load("run_claude")
    cmd = runner.befehl("Draw aspirin", "/x/mcp.json", None, ["generate_molecule", "lookup"], max_turns=2)
    erlaubt = cmd[cmd.index("--allowedTools") + 1].split(",")
    assert erlaubt == ["mcp__chemdraw__generate_molecule", "mcp__chemdraw__lookup"]
    assert cmd[cmd.index("--max-turns") + 1] == "2"


def test_stub_lauf_mit_verweigertem_aufruf_ist_keine_messung():
    runner = _load("run_claude")
    fall = {"expect": "generate_molecule"}
    assert runner.bewerte(fall, [("generate_molecule", {})], verweigert=["generate_molecule"])
