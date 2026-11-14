#!/usr/bin/env python3
"""Tool-Wahl-Lauf über Claude Code (`claude -p`) — ohne API-Schlüssel.

Gleiche Fälle wie promptfoo (`cases.yaml`), aber das Modell ist das, was Jay in
Claude Code/Desktop benutzt, und es sieht den Server so, wie er sich beim Verbinden
meldet (die Tools des gewählten Profils + `instructions`). Der Server ist eine Attrappe
(`stub_server.py`): es wird nichts ausgeführt, nur gemessen, WELCHES Tool gerufen wird.
Die eingebauten Claude-Code-Tools sind abgeschaltet (`--tools ""`), sonst wählt das
Modell statt eines Tools Bash.

    uv run python evals/tool-routing/run_claude.py              # alle Fälle
    uv run python evals/tool-routing/run_claude.py bare-name-de # einzelne Fälle
    MODEL=sonnet uv run python evals/tool-routing/run_claude.py # anderes Modell

`--echt` fährt stattdessen den ECHTEN Server: je Panel-Tool ein Prompt aus
`evals/panel-beispiele.json`. Grün heißt dort: das Tool wurde gerufen, der Server hat
ohne Fehler geantwortet, und kein Aufruf wurde verweigert. Das ist der Teil des
Desktop-Handtests, der ohne Bildschirm geht (Prompt → Aufruf → Ergebnis). Er sagt NICHT
voraus, ob Desktop das Tool ruft: die `desktop-*`-Fälle (in Desktop rot) waren im Stub-Lauf grün.

    uv run python evals/tool-routing/run_claude.py --echt                 # alle Panel-Tools
    uv run python evals/tool-routing/run_claude.py --echt generate_3d

Exit 0 = alle Fälle grün, 1 = mindestens ein Fall rot, 3 = nur gelb (Quelle nicht erreichbar).
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HIER = Path(__file__).parent
REPO = HIER.parent.parent
PREFIX = "mcp__chemdraw__"


def gerufene_tools(prompt: str, config: str, modell: str | None, cwd: str) -> tuple[list[str], str]:
    namen, text, _ = _lauf(prompt, config, modell, cwd, [])
    return namen, text


def _lauf(prompt: str, config: str, modell: str | None, cwd: str, erlaubt: list[str]) -> tuple[list[str], str, dict]:
    """Ein `claude -p`-Lauf. `erlaubt` (nur --echt): Tools, die ohne Rückfrage laufen dürfen."""
    cmd = [
        "claude", "-p", prompt,
        "--mcp-config", config, "--strict-mcp-config", "--tools", os.environ.get("BUILTIN_TOOLS", ""),
        # Ohne Isolation leaken Jays Hooks und CLAUDE.md (CWD-Wächter, Antwortstil) in die Wahl
        "--setting-sources", "project", "--disable-slash-commands",
        "--output-format", "stream-json", "--verbose",
        "--max-turns", "3" if erlaubt else "2", "--no-session-persistence",
    ]
    if erlaubt:
        cmd += ["--allowedTools", ",".join(PREFIX + name for name in erlaubt)]
    if modell:
        cmd += ["--model", modell]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=cwd).stdout
    namen: list[str] = []
    text = ""
    echt: dict = {"ergebnisse": {}, "verweigert": [], "ids": {}, "aufrufe": []}
    for zeile in out.splitlines():
        try:
            e = json.loads(zeile)
        except ValueError:
            continue
        if e.get("type") == "assistant":
            for b in e["message"]["content"]:
                if b.get("type") == "tool_use":
                    namen.append(b["name"].removeprefix(PREFIX))
                    echt["ids"][b.get("id")] = namen[-1]
                    echt["aufrufe"].append((namen[-1], b.get("input") or {}))
                elif b.get("type") == "text" and not text:
                    text = b["text"]
        elif e.get("type") == "user" and isinstance(e["message"].get("content"), list):
            for b in e["message"]["content"]:
                if b.get("type") == "tool_result":
                    inhalt = b.get("content")
                    if isinstance(inhalt, list):
                        inhalt = " ".join(str(t.get("text", "")) for t in inhalt if isinstance(t, dict))
                    name = echt["ids"].get(b.get("tool_use_id"), "?")
                    echt["ergebnisse"][name] = (bool(b.get("is_error")), str(inhalt or ""))
        elif e.get("type") == "result":
            echt["verweigert"] = [d.get("tool_name", "?").removeprefix(PREFIX) for d in e.get("permission_denials") or []]
    if text.startswith("Failed to authenticate"):
        # Kein Messwert: ein abgelaufener Login darf nicht als „Modell wählt kein Tool" erscheinen
        raise SystemExit(f"ABBRUCH (kein Ergebnis, kein roter Fall): {text}\nAnmelden: `claude` im Terminal starten und /login ausführen.")
    return namen, text, echt


# Fehlerarten des Servers, die eine Quelle meinen und keinen Fehler im Code (wie identitaet.py: gelb)
_GELB = ("offline", "sources_down", "could not be reached", "timed out", "temporarily")


def bewerte_echt(tool: str, namen: list[str], echt: dict) -> tuple[str, str]:
    """('grün'|'gelb'|'rot', Grund) für einen Lauf gegen den echten Server."""
    if echt["verweigert"]:
        return "rot", f"Aufruf verweigert: {echt['verweigert']}"
    if tool not in namen:
        return "rot", f"nicht gerufen (gerufen: {namen or '—'})"
    if tool not in echt["ergebnisse"]:
        return "rot", "gerufen, aber kein tool_result im Lauf"
    fehler, inhalt = echt["ergebnisse"][tool]
    if fehler or '"error"' in inhalt[:400]:
        kurz = " ".join(inhalt.split())[:200]
        return ("gelb" if any(w in inhalt.lower() for w in _GELB) else "rot"), f"Server meldet Fehler: {kurz}"
    return "grün", ""


def _neu_seit(pfad: Path, beginn: float) -> list[str]:
    """Dateien, die seit `beginn` geändert wurden — mtime, damit auch Überschreiben auffällt."""
    if not pfad.exists():
        return []
    return sorted(str(f.relative_to(pfad)) for f in pfad.rglob("*") if f.is_file() and f.stat().st_mtime >= beginn)


def main_echt(auswahl: list[str]) -> int:
    from chemdraw_tool.server import mcp

    beispiele = json.loads((REPO / "evals" / "panel-beispiele.json").read_text(encoding="utf-8"))
    offen = {n: b for n, b in beispiele.items() if "auslassen" not in b}
    fremd = set(auswahl) - offen.keys()
    if fremd:
        print(f"ABBRUCH: kein Beispiel für {', '.join(sorted(fremd))}", file=sys.stderr)
        return 2
    fälle = [(n, b) for n, b in offen.items() if not auswahl or n in auswahl]
    # Alles erlauben, was angeboten und nicht ausgelassen ist: ein falsch gewähltes Tool soll
    # als falsche Wahl erscheinen, nicht als Rechtefrage. export_anki_deck bleibt verweigert.
    erlaubt = sorted({t.name for t in asyncio.run(mcp.list_tools())} - (beispiele.keys() - offen.keys()))
    arbeit = tempfile.mkdtemp(prefix="tool-echt-")
    echtes_output = Path.home() / "ChemDraw-Output"
    beginn = time.time()
    try:
        heim = Path(arbeit) / "home"
        heim.mkdir()
        config_pfad = Path(arbeit) / "mcp.json"
        # venv-Binärdatei direkt (uv bräuchte das echte HOME); HOME des Servers = Wegwerf-Ordner
        config_pfad.write_text(json.dumps({"mcpServers": {"chemdraw": {
            "command": str(REPO / ".venv" / "bin" / "chemdraw-tool-server"),
            "env": {"CHEMDRAW_PROFILE": os.environ.get("CHEMDRAW_PROFILE", "mvp"), "HOME": str(heim)},
        }}}))
        modell = os.environ.get("MODEL")

        def lauf(fall: tuple[str, dict]) -> tuple[str, list[str], str, dict]:
            return (fall[0], *_lauf(fall[1]["prompt"], str(config_pfad), modell, arbeit, erlaubt))

        zahl = {"grün": 0, "gelb": 0, "rot": 0}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for tool, namen, text, echt in pool.map(lauf, fälle):
                urteil, grund = bewerte_echt(tool, namen, echt)
                zahl[urteil] += 1
                print(f"{ {'grün': '✔', 'gelb': '●', 'rot': '✘'}[urteil]} {tool:<32} gerufen: {namen or '—'}")
                if grund:
                    print(f"    {grund}")
                if not namen:
                    print(f"    Modell schrieb stattdessen: {' '.join(text.split())[:200]}")
    finally:
        shutil.rmtree(arbeit, ignore_errors=True)
    # Nur Hinweis, kein Rot: ein parallel benutztes Claude Desktop schreibt in denselben Ordner (gesehen 12.11.2026)
    neu = _neu_seit(echtes_output, beginn)
    if neu:
        print(f"⚠ ~/ChemDraw-Output: {len(neu)} Datei(en) seit Laufbeginn geändert ({', '.join(neu[:3])}). "
              "Von diesem Lauf dürfen sie nicht stammen (Wegwerf-HOME) — prüfen, ob Desktop parallel lief.")
    print(f"\n{zahl['grün']}/{len(fälle)} grün · {zahl['gelb']} gelb (Quelle) · {zahl['rot']} rot")
    return 1 if zahl["rot"] else 3 if zahl["gelb"] else 0


def select_cases(cases: list[dict], offered: set[str], selection: set[str]) -> list[dict]:
    """Explizite Auswahl validieren, sonst nur angebotene Werkzeuge messen."""
    by_id = {case["id"]: case for case in cases}
    unknown = selection - by_id.keys()
    if unknown:
        raise ValueError("Unbekannte Fall-IDs: " + ", ".join(sorted(unknown)))
    disabled = {name for name in selection if by_id[name]["expect"] not in offered}
    if disabled:
        raise ValueError("Im gewählten Profil deaktivierte Fälle: " + ", ".join(sorted(disabled)))
    selected = [
        case for case in cases
        if case["expect"] in offered and (not selection or case["id"] in selection)
    ]
    if not selected:
        raise ValueError("Keine passenden Eval-Fälle für die angebotenen Tools.")
    return selected


def main() -> int:
    if "--echt" in sys.argv[1:]:
        return main_echt([a for a in sys.argv[1:] if a != "--echt"])
    from chemdraw_tool.server import mcp

    fälle = yaml.safe_load((HIER / "cases.yaml").read_text())["cases"]
    offered = {tool.name for tool in asyncio.run(mcp.list_tools())}
    try:
        fälle = select_cases(fälle, offered, set(sys.argv[1:]))
    except ValueError as error:
        print(f"ABBRUCH: {error}", file=sys.stderr)
        return 2
    config = json.dumps({"mcpServers": {"chemdraw": {
        "command": "uv",
        "args": ["run", "--directory", str(REPO), "python", str(HIER / "stub_server.py")],
        "env": {"CHEMDRAW_PROFILE": os.environ.get("CHEMDRAW_PROFILE", "mvp")},
    }}})
    # Eigener Ordner (0700) statt des geteilten Temp-Ordners: `--setting-sources project`
    # liest .claude/settings.json aus dem CWD — in /tmp könnte ein Mitnutzer dort
    # Hooks hinterlegen (Sicherheitsscan F2).
    arbeit = tempfile.mkdtemp(prefix="tool-routing-")
    try:
        config_pfad = Path(arbeit) / "mcp.json"
        config_pfad.write_text(config)
        return _messen(fälle, str(config_pfad), arbeit)
    finally:
        shutil.rmtree(arbeit, ignore_errors=True)


def bewerte(fall: dict, aufrufe: list[tuple[str, dict]]) -> list[str]:
    """Mängel eines Stub-Laufs; leer = grün. Argumente zählen nur am erwarteten Tool."""
    namen = [name for name, _ in aufrufe]
    maengel = []
    if fall["expect"] not in namen:
        maengel.append(f"erwartet {fall['expect']}")
    falsch = [t for t in fall.get("forbidden", []) if t in namen]
    if falsch:
        maengel.append(f"verboten {falsch}")
    eigene = [eingabe for name, eingabe in aufrufe if name == fall["expect"]]
    for arg, wert in fall.get("required_args", {}).items():
        if eigene and not any(e.get(arg) == wert for e in eigene):
            maengel.append(f"Argument {arg}={wert!r} fehlt (gesetzt: {[e.get(arg) for e in eigene]})")
    for arg in fall.get("forbidden_args", []):
        if any(arg in e for e in eigene):
            maengel.append(f"ungefragtes Argument {arg}")
    return maengel


def _messen(fälle: list[dict], config: str, cwd: str) -> int:
    modell = os.environ.get("MODEL")

    def lauf(fall: dict) -> tuple[dict, list[tuple[str, dict]], str]:
        _, text, echt = _lauf(fall["prompt"].strip(), config, modell, cwd, [])
        return fall, echt["aufrufe"], text

    rot = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for fall, aufrufe, text in pool.map(lauf, fälle):
            tools = [name for name, _ in aufrufe]
            maengel = bewerte(fall, aufrufe)
            ok = not maengel
            rot += not ok
            print(f"{'✔' if ok else '✘'} {fall['id']:<28} gerufen: {tools or '—'}")
            if not ok:
                if not tools:
                    print(f"    Modell schrieb stattdessen: {' '.join(text.split())[:200]}")
                print(f"    {'; '.join(maengel)}\n    warum: {' '.join(fall['why'].split())}")
    print(f"\n{len(fälle) - rot}/{len(fälle)} grün")
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main())
