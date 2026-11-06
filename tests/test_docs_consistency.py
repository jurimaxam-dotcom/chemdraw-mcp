"""Doku-Gate: was README, docs/ und CHANGELOG behaupten, gegen den echten Code.

tests/test_readme.py prüft Toolliste, Toolzahlen und Bilder. Hier steht der Rest
dessen, was sich mechanisch prüfen lässt (Jay 06.11.2026: „bei jedem Release
dauerhaft auf Aktualität prüfen“):

(a) jeder Toolname in der Nutzerdoku ist registriert (kein umbenanntes,
    gestrichenes Tool, das im Text weiterlebt),
(b) jeder Parameter unter „Options on the drawing tools“ existiert an den
    genannten Tools; die `topic`-Werte von `lookup` und die Render-Stile
    stimmen mit Schema bzw. render_style.STYLES,
(c) „N with a panel“ stimmt je Profil,
(d) Umgebungsvariablen, Konsolenbefehle und Repo-Pfade gibt es wirklich,
(e) „N inputs“ der Identitätsliste stimmt mit tests/identity/stoffe.json.

Was sich nicht mechanisch prüfen lässt (stimmt die Beschreibung einer Funktion
noch?), steht als Release-Checkliste in docs/registry-publish.md.
Nutzerdoku = die Seiten, die README verlinkt, plus CHANGELOG [Unreleased];
Abnahmeprotokolle unter docs/ sind datierte Belege und bleiben, wie sie sind.
"""

import asyncio
import json
import re
import tomllib
from functools import lru_cache
from pathlib import Path

from chemdraw_tool.render_style import STYLES
from chemdraw_tool.server import create_server

ROOT = Path(__file__).resolve().parents[1]
USER_DOCS = ["README.md", "docs/tools.md", "docs/installation.md", "docs/development.md"]
VAULT_TOOLS = {"search_vault", "read_vault_entry"}
PANEL_URI = "ui://chem-app/index.html"


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _unreleased() -> str:
    text = _read("CHANGELOG.md")
    begin = text.index("## [Unreleased]")
    return text[begin : text.index("\n## [", begin + 1)]


def _docs() -> dict[str, str]:
    return {**{n: _read(n) for n in USER_DOCS}, "CHANGELOG.md [Unreleased]": _unreleased()}


@lru_cache
def _tools(profile: str) -> dict:
    return {t.name: t for t in asyncio.run(create_server(profile).list_tools())}


def _params(tool: str) -> set[str]:
    return set(_tools("full")[tool].input_schema.get("properties", {}))


def _section(text: str, start: str) -> str:
    begin = text.index(start)
    nxt = text.find("\n## ", begin + len(start))
    return text[begin : nxt if nxt != -1 else None]


# --- (a) Toolnamen ------------------------------------------------------------


def test_jeder_toolname_in_der_doku_ist_registriert():
    bekannt = set(_tools("full")) | VAULT_TOOLS
    praefixe = {n.split("_")[0] for n in bekannt}
    tot = []
    for name, text in _docs().items():
        for wort in re.findall(r"`([a-z]+_[a-z0-9_]+)`", text):
            if wort.split("_")[0] in praefixe and wort not in bekannt and not _ist_parameter(wort):
                tot.append(f"{name}: `{wort}`")
    assert not tot, f"Doku nennt Tools, die es nicht (mehr) gibt: {tot}"


def _ist_parameter(wort: str) -> bool:
    return any(wort in t.input_schema.get("properties", {}) for t in _tools("full").values())


# --- (b) Parameter und Werte ----------------------------------------------------


def _optionen() -> list[tuple[str, set[str]]]:
    """(Parameter, genannte Tools) je Aufzählungspunkt unter „Options on the drawing tools“."""
    teil = _section(_read("docs/tools.md"), "## Options on the drawing tools")
    punkte = re.split(r"\n- ", teil)[1:]
    assert punkte, "Abschnitt „Options on the drawing tools“ ohne Aufzählung — Regex kaputt?"
    ergebnis = []
    for punkt in punkte:
        param = re.match(r"\*\*`(\w+)", punkt).group(1)
        tools = set(re.findall(r"`(\w+)`", punkt)) & set(_tools("full"))
        ergebnis.append((param, tools or {"generate_molecule"}))
    return ergebnis


def test_jede_option_gibt_es_an_den_genannten_tools():
    fehlt = [f"`{p}` an `{t}`" for p, tools in _optionen() for t in sorted(tools) if p not in _params(t)]
    assert not fehlt, f"docs/tools.md beschreibt Parameter, die das Tool nicht hat: {fehlt}"


def test_render_stile_der_doku_gibt_es():
    teil = _section(_read("docs/tools.md"), "## Options on the drawing tools")
    punkt = next(p for p in re.split(r"\n- ", teil) if p.startswith("**`render_style`"))
    genannt = set(re.findall(r'`"(\w+)"`', punkt))
    assert genannt == set(STYLES), f"Doku {sorted(genannt)} ≠ render_style.STYLES {sorted(STYLES)}"


def test_lookup_topics_der_doku_stimmen_mit_dem_schema():
    teil = _section(_read("docs/tools.md"), "## Look up")
    punkt = next(p for p in re.split(r"\n- ", teil) if p.startswith("**`lookup`**"))
    genannt = set(re.findall(r"`(\w+)`", punkt)) - {"lookup", "topic"}
    schema = set(_tools("full")["lookup"].input_schema["properties"]["topic"]["enum"])
    assert genannt == schema, f"Doku {sorted(genannt)} ≠ Schema {sorted(schema)}"


# --- (c) Panelzahlen ------------------------------------------------------------


def _panel(profile: str) -> int:
    return sum(((t.meta or {}).get("ui") or {}).get("resourceUri") == PANEL_URI for t in _tools(profile).values())


def test_panelzahlen_je_profil_stimmen():
    profile = _section(_read("docs/tools.md"), "## Profiles")
    for name, zeile in (("mvp", "| `mvp` (default) |"), ("full", "| `full` |")):
        erwartet = f"{zeile} {len(_tools(name))}, {_panel(name)} with a panel |"
        assert erwartet in profile, f"Profiltabelle falsch, erwartet: {erwartet}"


# --- (d) Umgebung, Befehle, Pfade ------------------------------------------------


def test_umgebungsvariablen_der_doku_gibt_es_im_code():
    code = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "chemdraw_tool").rglob("*.py"))
    code += _read("mcpb/server/run.sh")
    genannt = {v for text in _docs().values() for v in re.findall(r"\bCHEMDRAW_[A-Z_]+\b", text)}
    assert genannt, "keine CHEMDRAW_-Variable in der Doku — Regex kaputt?"
    fehlt = sorted(v for v in genannt if v not in code)
    assert not fehlt, f"Doku nennt Umgebungsvariablen, die der Code nicht liest: {fehlt}"


def test_konsolenbefehle_der_doku_gibt_es():
    scripts = set(tomllib.loads(_read("pyproject.toml"))["project"]["scripts"])
    genannt = {b for text in _docs().values() for b in re.findall(r"`(chemdraw-[a-z-]+)`", text)}
    fehlt = sorted(genannt - scripts)
    assert not fehlt, f"Doku nennt Befehle, die pyproject nicht installiert: {fehlt}"


def test_repo_pfade_der_doku_gibt_es():
    fehlt = []
    for name, text in _docs().items():
        for pfad in re.findall(r"`((?:[\w.-]+/)+[\w.-]+\.\w+)`", text):
            if not (ROOT / pfad).exists():
                fehlt.append(f"{name}: {pfad}")
    assert not fehlt, f"Doku zeigt auf Dateien, die es nicht gibt: {fehlt}"


# --- (e) Identitätsliste ---------------------------------------------------------


def test_identitaetszahl_stimmt():
    stoffe = json.loads(_read("tests/identity/stoffe.json"))["stoffe"]
    mit_key = sum("inchikey" in s for s in stoffe)
    zahl = re.search(r"identity test checks (\d+) inputs", _read("docs/tools.md"))
    assert zahl, "Satz zur Identitätsliste fehlt in docs/tools.md — umformuliert? Test anpassen."
    assert int(zahl.group(1)) == mit_key, f"docs/tools.md nennt {zahl.group(1)}, stoffe.json hat {mit_key}"
