"""Tool-Fehler sprechen Englisch — das Panel zeigt sie seit 09.11.2026 im Wortlaut.

Projektregel: Nutzertext ist Englisch. Geprüft werden
(a) alle Texte in `raise …(…)` im Paket — jede Exception kann als Tool-Fehler
    beim Nutzer landen, auch eine aus der Tiefe (pk, scope, png_writer …);
(b) alle übrigen String-Literale in `server.py` (Rückgabetexte, Hinweise in
    Payloads, Vault-Ausgaben).
Kommentare und Docstrings bleiben Deutsch; Logzeilen sieht der Nutzer nicht.

Bewusst ausgenommen:
- `aufgaben/`: der Praktikumsrechner erzeugt deutsche Aufgaben, mit Absicht.
- `de_names.py`: deutsche Namensregeln sind Daten, keine Meldungen.
- `svg_renderer._FUNCTIONAL_GROUPS`: deutsche Gruppennamen sind Schlüssel, die
  das Panel (`ui/src/utils/groupInfo.js`) ins Englische übersetzt.
- `"Fehler: "` in `save_png`: Kennung, an der `ExportPngButton.jsx` eine
  weiche Fehlerantwort erkennt und vor der Anzeige abschneidet.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "chemdraw_tool"

# Umlaute/ß oder deutsche Wörter ohne englisches Homograph (kein "die", "an", "war").
_GERMAN = re.compile(
    r"[äöüÄÖÜß]|\b(nicht|kein|keine|keinen|oder|und|der|das|mit|braucht|muss|wird|werden|"
    r"wurde|fehlt|ist|sind|für|bitte|unbekannte?r?s?|ungültige?s?|mindestens|zwischen|"
    r"darf|gebraucht|beendet|antwort|eintrag|einträge|treffer|pfad|zu|fehlgeschlagen|strukturen?)\b",
    re.IGNORECASE,
)
_ALLOWED = {"Fehler: "}
# Absichtliche Beispiele lokalisierter Namen ("never 'Acetylsalicylsäure'").
_EXAMPLES = ("Acetylsalicylsäure",)


def _python_files():
    for path in sorted(PKG.rglob("*.py")):
        rel = path.relative_to(PKG)
        if rel.parts[0] in ("aufgaben", "ui") or rel.name == "de_names.py":
            continue
        yield path


def _strings(node: ast.AST):
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            yield sub


def _docstring_ids(tree: ast.AST) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def _logging_ids(tree: ast.AST) -> set[int]:
    """Strings in Log-Aufrufen (logger.info(…), logging.getLogger(…).exception(…)):
    Log, kein Nutzertext."""
    methods = {"debug", "info", "warning", "error", "exception", "critical", "log"}
    ids = set()
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in methods
        ):
            continue
        receiver = node.func.value
        by_name = isinstance(receiver, ast.Name) and receiver.id in ("logger", "logging", "log")
        by_getter = (
            isinstance(receiver, ast.Call)
            and isinstance(receiver.func, ast.Attribute)
            and receiver.func.attr == "getLogger"
        )
        if by_name or by_getter:
            ids.update(id(s) for s in _strings(node))
    return ids


def _without_examples(text: str) -> str:
    for example in _EXAMPLES:
        text = text.replace(example, "")
    return text


def _hits(path: Path, everything: bool) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = _docstring_ids(tree) | _logging_ids(tree)
    if everything:
        candidates = list(_strings(tree))
    else:
        candidates = [
            s for node in ast.walk(tree) if isinstance(node, ast.Raise) and node.exc
            for s in _strings(node.exc)
        ]
    return [
        f"{path.relative_to(PKG)}:{s.lineno}: {s.value!r}"
        for s in candidates
        if id(s) not in skip
        and s.value not in _ALLOWED
        and _GERMAN.search(_without_examples(s.value))
    ]


def test_regex_erkennt_die_alten_meldungen():
    """Ohne diese Probe könnte der Wächter still nichts messen."""
    for text in (
        "Das Deck braucht mindestens eine Karte.",
        "compare_molecules braucht 2 bis 4 Strukturen.",
        "Die Zeit t darf nicht negativ sein.",
        "Unbekannte Formate: ",
    ):
        assert _GERMAN.search(text), text


def test_regex_laesst_englische_texte_in_ruhe():
    for text in (
        "Chemistry drawings, lab graphics and bench maths, rendered offline.",
        "labels needs one entry per structure",
        "The points sit exactly on the line, so there is no residual scatter.",
    ):
        assert not _GERMAN.search(text), text


def test_exceptions_im_paket_sprechen_englisch():
    hits = [h for path in _python_files() for h in _hits(path, everything=False)]
    assert hits == [], "Deutsche Exception-Texte:\n" + "\n".join(hits)


def test_server_texte_sprechen_englisch():
    hits = _hits(PKG / "server.py", everything=True)
    assert hits == [], "Deutsche Texte in server.py:\n" + "\n".join(hits)
