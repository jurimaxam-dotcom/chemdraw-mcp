"""Parität zwischen Payload-Diskriminatoren (Python) und Panel-Views (JSX).

Zweite Hälfte der Lehre aus dem generate_spectrum-Bug (2026-06-11): ein Tool
kann korrekt registriert sein, das Meta tragen und trotzdem nur
„Unbekannter Typ" anzeigen — nämlich dann, wenn der `type`-Diskriminator des
Payloads in `App.jsx` keinen `case` hat. Beide Richtungen sind eine Lücke:

* Payload ohne View  → Panel zeigt „Unbekannter Typ: …"
* View ohne Payload  → toter Code, meist ein Tippfehler beim Umbenennen

Der Test liest die Wahrheit an beiden Enden aus dem Quellcode: die
`type`-Defaults aus `chemdraw_tool/payloads.py` (per Introspektion, nicht per
Textsuche) und die `case`-Literale aus `chemdraw_tool/ui/src/App.jsx`.
"""

import re
from pathlib import Path
from typing import get_type_hints

from pydantic import BaseModel

from chemdraw_tool import payloads

APP_JSX = Path(__file__).parent.parent / "chemdraw_tool" / "ui" / "src" / "App.jsx"

# case "molecule":  /  case 'molecule' :  — Anführungszeichen und Abstände frei,
# aber das Literal muss am Zeilenanfang stehen (so schreibt es Prettier).
_CASE_RE = re.compile(r"""^\s*case\s+["']([^"']+)["']\s*:""", re.MULTILINE)


def _view_case_types() -> set[str]:
    """Alle `case`-Literale des switch in App.jsx."""
    return set(_CASE_RE.findall(APP_JSX.read_text(encoding="utf-8")))


def _payload_types() -> dict[str, str]:
    """{Modellname: type-Default} für alle Payload-Modelle mit Diskriminator."""
    found = {}
    for name, obj in vars(payloads).items():
        if not (isinstance(obj, type) and issubclass(obj, BaseModel)):
            continue
        if obj.__module__ != payloads.__name__:
            continue
        field = obj.model_fields.get("type")
        default = getattr(field, "default", None)
        if isinstance(default, str) and default:
            found[name] = default
    return found


def test_app_jsx_is_parsed_at_all():
    """Schutz vor einem Test, der still nichts prüft: findet die Regex keine
    cases mehr (Umbau auf eine Map, Prettier-Neuformatierung), muss das
    auffallen, statt die Paritätsprüfung leerlaufen zu lassen."""
    assert APP_JSX.exists(), f"App.jsx nicht gefunden: {APP_JSX}"
    cases = _view_case_types()
    assert len(cases) >= 5, f"Nur {len(cases)} case-Literale gefunden — Parsing kaputt?"
    assert {"molecule", "spectrum"} <= cases


def test_payload_models_are_found_at_all():
    """Gegenstück: die Introspektion muss die Payload-Modelle wirklich sehen."""
    types = _payload_types()
    assert len(types) >= 5, f"Nur {len(types)} Payload-Typen gefunden — Parsing kaputt?"
    assert types.get("MoleculePayload") == "molecule"
    assert types.get("SpectrumPayload") == "spectrum"
    # Felder ohne Default (DatabaseSource.type) sind keine Diskriminatoren
    assert "DatabaseSource" not in types


def test_every_payload_type_has_a_view_case():
    """Payload ohne `case` in App.jsx → Panel zeigt 'Unbekannter Typ'."""
    cases = _view_case_types()
    orphans = {model: t for model, t in _payload_types().items() if t not in cases}
    assert not orphans, (
        f"Payload-Typen ohne View in App.jsx: {orphans} — das Panel zeigt dafür "
        "'Unbekannter Typ'. Entweder case ergänzen oder Payload entfernen."
    )


def test_every_view_case_has_a_payload_type():
    """`case` ohne Payload → toter Zweig, meist ein Tippfehler beim Umbenennen."""
    payload_types = set(_payload_types().values())
    dangling = _view_case_types() - payload_types
    assert not dangling, (
        f"App.jsx behandelt Typen, die kein Payload liefert: {sorted(dangling)} — "
        "Tippfehler oder verwaister View."
    )


def test_every_panel_tool_returns_a_renderable_type():
    """Die Kette bis ans Ende: jedes Tool mit UI-Meta liefert einen Payload,
    dessen `type` in App.jsx einen case hat."""
    from chemdraw_tool.server import _RESOURCE_URI, mcp

    cases = _view_case_types()
    broken = {}
    for tool in mcp._tool_manager.list_tools():
        if tool.meta != {"ui": {"resourceUri": _RESOURCE_URI}}:
            continue
        ret = get_type_hints(tool.fn).get("return")
        assert isinstance(ret, type) and issubclass(ret, BaseModel), (
            f"{tool.name} trägt UI-Meta, gibt aber kein Payload-Modell zurück "
            f"(Rückgabe: {ret!r}) — das Panel bekommt nichts Strukturiertes."
        )
        payload_type = getattr(ret.model_fields.get("type"), "default", None)
        if payload_type not in cases:
            broken[tool.name] = payload_type
    assert not broken, (
        f"Panel-Tools ohne passenden View-case: {broken} — Payload kommt an, "
        "Panel zeigt 'Unbekannter Typ'."
    )
