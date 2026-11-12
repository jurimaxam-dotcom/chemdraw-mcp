"""Panel-Ergebnisse unter Claude Desktops Größengrenze halten (M2, 12.11.2026).

Desktop legt ein Tool-Ergebnis über rund 150.000 Zeichen als Datei ab, das Panel
bekommt dann nur einen Verweis und lädt nie (Anthropic, troubleshooting: „App
doesn't render when tool results are large“). Das SDK schickt die Nutzlast
zweimal — als `structuredContent` und als JSON im Textblock —, und der Textblock
muss bleiben: eine Desktop-Fassung reichte `structuredContent` nicht ans Panel
weiter (`ui/src/utils/toolData.js`). Also bekommt jede Kopie ein Budget.

Unter dem Budget ändert sich nur die Einrückung des Textblocks. Darüber werden
die größten Zeichenketten (SVGs) und notfalls Listen durch leere Platzhalter
ersetzt, hier zwischengespeichert und vom Panel über das interne Tool
`load_panel_part` stückweise nachgeladen — so, wie es Anthropic empfiehlt
(„Fetch details on demand“). Beide Kopien bleiben gleich; das Modell liest
statt eines riesigen SVGs den Vermerk `_deferred`.
"""

from __future__ import annotations

import json
import secrets
from collections import OrderedDict
from copy import deepcopy
from typing import Any

from mcp.types import CallToolResult, TextContent
from pydantic import BaseModel

# Zeichen je Kopie (kompaktes JSON). Zwei Kopien plus Hülle bleiben so unter
# 120.000 — mit Abstand zu Desktops ~150.000 und zu den 100.000 Zeichen Text.
BUDGET = 55_000
# Rohzeichen je Nachlade-Stück; JSON-Escapes (\n, \") machen daraus etwas mehr.
PART_SIZE = 50_000
# Kleineres lohnt das Zurückhalten nicht. Listen dürfen kleiner sein (die
# Atomliste eines Stapelmoleküls hat ~1.400 Zeichen), weil alle Teile eines
# Ergebnisses ohnehin in einem Block nachgeladen werden.
_MIN_STRING = 2_000
_MIN_LIST = 500
# Ergebnisse, deren Teile noch abrufbar sind. Ein Panel lädt sofort nach; ältere
# Einträge fallen heraus, nach einem Server-Neustart sind alle weg (das Panel
# zeigt dann einen Hinweis statt einer leeren Fläche).
_STORE_MAX = 32
_STORE: OrderedDict[str, str] = OrderedDict()

DEFERRED_KEY = "_deferred"


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _wire(value: Any) -> int:
    """Länge der größeren Kopie auf der Leitung: der Textblock als JSON-String.

    Gemessen mit `json.dumps` (ASCII-maskiert), also mit `\\"` je Anführungszeichen,
    `\\n` je Zeilenumbruch und `\\uXXXX` je Nicht-ASCII-Zeichen — so lang wird er
    höchstens, egal wie der Host serialisiert. structuredContent ist kürzer.
    """
    return len(json.dumps(_compact(value)))


def _walk(node: Any, path: tuple = ()):
    """Alle Zeichenketten und Listen mit ihrem Pfad (Schlüssel bzw. Index)."""
    if isinstance(node, dict):
        for key, child in node.items():
            yield from _walk(child, (*path, key))
    elif isinstance(node, list):
        if path:
            yield path, node
        for index, child in enumerate(node):
            yield from _walk(child, (*path, index))
    elif isinstance(node, str) and path:
        yield path, node


def _set(root: Any, path: tuple, value: Any) -> None:
    for step in path[:-1]:
        root = root[step]
    root[path[-1]] = value


def _remember(parts: list[str]) -> str:
    """Alle Teile als ein JSON-Array: das Panel holt einen Block statt je Teil einen."""
    token = secrets.token_hex(8)
    _STORE[token] = _compact(parts)
    while len(_STORE) > _STORE_MAX:
        _STORE.popitem(last=False)
    return token


def shape(payload: dict) -> dict:
    """Die Nutzlast, die beide Kopien tragen: unverändert oder mit Platzhaltern.

    Zuerst Zeichenketten (Platzhalter ""), erst wenn das nicht reicht Listen
    (Platzhalter []), jeweils die größten zuerst. Beide Platzhalter bestehen die
    Prüfung gegen das outputSchema. Das Panel setzt in umgekehrter Reihenfolge
    zurück, damit eine nachgeladene Liste die in ihr nachgeladenen Texte aufnimmt.
    """
    if _wire(payload) <= BUDGET:
        return payload
    shaped = deepcopy(payload)
    candidates = [(p, v) for p, v in _walk(shaped) if p != ("type",)]
    strings = sorted(((p, v) for p, v in candidates if isinstance(v, str)), key=lambda c: -len(c[1]))
    # Listen von innen nach außen: erst `molecules[3].atoms`, ganz zuletzt
    # `molecules` selbst — so bleiben Namen und Formeln für Claude lesbar.
    lists = sorted(
        ((p, v) for p, v in candidates if isinstance(v, list)),
        key=lambda c: (-len(c[0]), -len(_compact(c[1]))),
    )
    paths: list[list] = []
    parts: list[str] = []

    def measured() -> int:
        # Vermerk mit Platzhalter-Token einrechnen: 16 Hex-Zeichen wie das echte.
        return _wire({**shaped, DEFERRED_KEY: {"token": "0" * 16, "paths": paths}})

    for path, value in [*strings, *lists]:
        if any(tuple(done) == path[: len(done)] for done in paths):
            continue  # liegt in einer schon zurückgehaltenen Liste
        text = value if isinstance(value, str) else _compact(_get(shaped, path))
        if len(text) < (_MIN_STRING if isinstance(value, str) else _MIN_LIST):
            continue
        _set(shaped, path, "" if isinstance(value, str) else [])
        paths.append(list(path))
        parts.append(text)
        if measured() <= BUDGET:
            break
    if not paths:
        return payload
    shaped[DEFERRED_KEY] = {"token": _remember(parts), "paths": paths}
    return shaped


def _get(root: Any, path: tuple) -> Any:
    for step in path:
        root = root[step]
    return root


def tool_result(result: Any) -> Any:
    """Ein Panel-Tool-Ergebnis als CallToolResult mit beiden Kopien im Budget.

    Das SDK reicht ein fertiges CallToolResult unverändert durch und prüft nur
    `structured_content` gegen das Ausgabemodell (mcp 2.3,
    `func_metadata.py: convert_result`). Alles, was kein Modell ist (Fehlertext,
    fertiges Ergebnis), bleibt beim SDK.
    """
    if not isinstance(result, BaseModel):
        return result
    payload = shape(result.model_dump(mode="json", by_alias=True))
    return CallToolResult(
        content=[TextContent(type="text", text=_compact(payload))],
        structured_content=payload,
    )


def load_part(token: str, offset: int = 0) -> dict:
    """Ein Stück des zurückgehaltenen Blocks (JSON-Array der Teile, in der
    Reihenfolge von `_deferred.paths`) und der Versatz des nächsten Stücks."""
    block = _STORE.get(token)
    if block is None:
        raise ValueError(
            "This panel content is no longer held by the server (it keeps the last "
            f"{_STORE_MAX} results, and a restart clears them). Run the tool again."
        )
    if not 0 <= offset <= len(block):
        raise ValueError(f"offset must be between 0 and {len(block)}.")
    end = min(offset + PART_SIZE, len(block))
    return {"text": block[offset:end], "next": end if end < len(block) else None}
