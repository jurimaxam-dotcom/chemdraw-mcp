"""Die Eval-Faelle muessen zur Toolliste passen — auch ohne Modell-Lauf.

`evals/tool-routing/cases.yaml` beschreibt, welches Tool bei welchem Prompt
gewinnen soll. Der eigentliche Lauf braucht ein Modell und damit einen
API-Schluessel (siehe evals/README.md). Diese Datei prueft, was ohne Netz
pruefbar ist — und das ist genau das, was still verrottet:

* ein Fall, der auf ein Tool zeigt, das es nicht mehr gibt
* ein umbenanntes Tool, das in `forbidden` als Karteileiche stehenbleibt
* ein Fall, dessen `expect` gleichzeitig in `forbidden` steht
* ein kritisches Paar aus dem Taxonomie-Test, fuer das gar kein Fall existiert

Ohne diese Pruefung waere die Fallsammlung genau dann falsch, wenn man sie
braucht: nach einem Umbau.
"""

from pathlib import Path

import pytest
import yaml

from tests.server_catalog import mcp
from tests.test_server_taxonomy import NEEDS_DELIMITATION

CASES_FILE = Path(__file__).resolve().parents[1] / "evals" / "tool-routing" / "cases.yaml"


def _cases() -> list[dict]:
    data = yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))
    return data["cases"]


def _tool_names() -> set[str]:
    return {t.name for t in mcp._tool_manager.list_tools()}


def test_cases_file_exists_and_parses():
    assert _cases(), "cases.yaml ist leer oder fehlt"


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["id"])
def test_case_has_the_required_fields(case):
    for field in ("id", "prompt", "expect", "forbidden", "why"):
        assert field in case, f"{case.get('id', '?')}: Feld {field!r} fehlt"
    assert case["forbidden"], (
        f"{case['id']}: leere forbidden-Liste. Ein Fall ohne Negativseite geht "
        "auch dann gruen durch, wenn zusaetzlich das falsche Tool gerufen wird."
    )


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["id"])
def test_case_points_at_tools_that_exist(case):
    names = _tool_names()
    assert case["expect"] in names, (
        f"{case['id']}: erwartet {case['expect']!r}, das es nicht (mehr) gibt"
    )
    for forbidden in case["forbidden"]:
        assert forbidden in names, (
            f"{case['id']}: verbietet {forbidden!r} — Karteileiche aus einem Umbau"
        )


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["id"])
def test_case_does_not_contradict_itself(case):
    assert case["expect"] not in case["forbidden"], (
        f"{case['id']}: {case['expect']!r} steht in expect UND forbidden"
    )


def test_every_delimited_pair_has_a_case():
    """Jede Abgrenzung aus dem Taxonomie-Test braucht mindestens einen Fall.

    Sonst ist der Zaun eine Behauptung: er steht in der Beschreibung, aber
    niemand hat je geprueft, ob er haelt.
    """
    covered = {(c["expect"], f) for c in _cases() for f in c["forbidden"]}
    missing = []
    for tool, alternatives in NEEDS_DELIMITATION.items():
        for alternative in alternatives:
            # Der Zaun sagt „nicht ich, sondern X". Ein Fall deckt ihn ab, wenn
            # er X erwartet und dieses Tool verbietet — oder umgekehrt.
            if (tool, alternative) not in covered and (
                alternative,
                tool,
            ) not in covered:
                missing.append(f"{tool} <-> {alternative}")
    assert not missing, (
        "Abgrenzungen ohne Eval-Fall: " + ", ".join(sorted(missing))
    )


def test_the_bare_compound_name_is_covered():
    """Der Anlassfall darf nie aus der Sammlung fallen."""
    prompts = [c["prompt"].strip().lower() for c in _cases()]
    assert any(len(p.split()) == 1 for p in prompts), (
        "Kein Fall mit einem einzelnen Wort — genau der Prompt, der den "
        "Umbau ausgeloest hat."
    )


# --- Der Alltagsfall ohne Zeichen-Verb (Auftrag Jay, 15.08.2026) -------------
#
# Bis hier ging es darum, den richtigen aus mehreren Kandidaten zu treffen.
# Die zweite Haelfte ist, ueberhaupt zuzugreifen: „erklaer mir Ibuprofen",
# „wie laeuft die Veresterung", „ich muss die NSAR lernen" enthalten kein
# einziges Zeichen-Verb. Ohne Faelle dieser Sorte misst die Suite nur die
# Haelfte des Problems — naemlich die, die seltener weh tut.

DRAW_VERBS = (
    "zeichne", "zeig", "male", "skizzier", "abbildung", "strukturformel",
    "draw", "show", "plot", "figure", "structure of", "diagramm", "kurve",
    "gib mir", "mach mir", "erstell",
)

# Tools, deren Ausgabe ein Bild oder ein Deck ist — die also von selbst
# angeboten werden muessen, wenn die Frage es nahelegt.
PROACTIVE_TOOLS = {
    "generate_molecule",
    "generate_reaction",
    "generate_mechanism",
    "compare_molecules",
    "export_anki_deck",
}


def _implicit_cases() -> list[dict]:
    out = []
    for case in _cases():
        prompt = case["prompt"].lower()
        if case["expect"] in PROACTIVE_TOOLS and not any(
            verb in prompt for verb in DRAW_VERBS
        ):
            out.append(case)
    return out


def test_the_everyday_case_is_represented():
    """Mindestens fuenf Faelle muessen ohne Zeichen-Verb auskommen."""
    implicit = _implicit_cases()
    assert len(implicit) >= 5, (
        f"nur {len(implicit)} Faelle ohne Zeichen-Verb: "
        f"{[c['id'] for c in implicit]}. Der Alltag eines Pharmazie-Studenten "
        "besteht aus Erklaerfragen, nicht aus Zeichenauftraegen."
    )


@pytest.mark.parametrize("tool", sorted(PROACTIVE_TOOLS))
def test_every_proactive_tool_has_an_implicit_case(tool):
    """Jedes Tool, das von selbst greifen soll, braucht einen solchen Fall."""
    covered = {c["expect"] for c in _implicit_cases()}
    assert tool in covered, (
        f"{tool} wird nur von expliziten Auftraegen getroffen — ungeprueft "
        "bleibt, ob es im Gespraech ueberhaupt vorkommt."
    )


# --- Argumente, die das Modell NICHT setzen darf (Jay 26.10.2026) -----------
#
# Manche Fehlgriffe sind kein falsches Tool, sondern ein ungefragtes Argument:
# „coefficients“ gleicht eine Gleichung aus, die der Nutzer so nicht bestellt
# hat. `forbidden_args` macht daraus eine not-contains-Pruefung im Lauf.


def _tool_params(name: str) -> set[str]:
    tool = next(t for t in mcp._tool_manager.list_tools() if t.name == name)
    return set(tool.parameters.get("properties", {}))


@pytest.mark.parametrize(
    "case", [c for c in _cases() if "forbidden_args" in c], ids=lambda c: c["id"]
)
def test_forbidden_args_are_parameters_of_the_expected_tool(case):
    unknown = set(case["forbidden_args"]) - _tool_params(case["expect"])
    assert not unknown, f"{case['id']}: {sorted(unknown)} gibt es nicht als Parameter"


def test_unrequested_coefficients_are_covered():
    assert any("coefficients" in c.get("forbidden_args", []) for c in _cases()), (
        "Kein Fall prueft, dass ein schlichter Zeichenauftrag ohne Koeffizienten bleibt"
    )


def test_config_turns_forbidden_args_into_not_contains():
    import importlib.util

    path = CASES_FILE.parent / "build_config.py"
    spec = importlib.util.spec_from_file_location("build_config", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = {
        "id": "x",
        "prompt": "p",
        "expect": "generate_reaction",
        "forbidden": ["generate_molecule"],
        "forbidden_args": ["coefficients"],
        "why": "w",
    }
    asserts = module.case_asserts(case)
    assert {
        "type": "not-contains",
        "value": '"coefficients"',
        "metric": "kein-ungefragtes-Argument",
    } in asserts


# --- Argumente, die das Modell setzen MUSS (Jay 26.10.2026) -----------------
#
# Gegenstück zu `forbidden_args`: „Zeige die Haworth-Projektion von …“ ging in
# Desktop an das eingebaute visualize. Der Fall prüft, dass das Modell mit
# unseren Tools `view=haworth` setzt. Desktops eigenes visualize steht nicht in
# tools.json — die Fehlleitung selbst sieht nur der Desktop-Test.


@pytest.mark.parametrize(
    "case", [c for c in _cases() if "required_args" in c], ids=lambda c: c["id"]
)
def test_required_args_are_parameters_of_the_expected_tool(case):
    unknown = set(case["required_args"]) - _tool_params(case["expect"])
    assert not unknown, f"{case['id']}: {sorted(unknown)} gibt es nicht als Parameter"


def test_named_projections_are_covered():
    views = {c.get("required_args", {}).get("view") for c in _cases()}
    assert {"haworth", "fischer"} <= views, (
        "Kein Fall prueft, dass eine genannte Projektion `view` setzt"
    )


def test_config_turns_required_args_into_contains():
    import importlib.util

    path = CASES_FILE.parent / "build_config.py"
    spec = importlib.util.spec_from_file_location("build_config", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = {
        "id": "x",
        "prompt": "p",
        "expect": "generate_molecule",
        "forbidden": ["batch_generate"],
        "required_args": {"view": "haworth"},
        "why": "w",
    }
    assert {
        "type": "contains",
        "value": '"view":"haworth"',
        "metric": "verlangtes-Argument",
    } in module.case_asserts(case)
