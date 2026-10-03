#!/usr/bin/env python3
"""Anthropic-Doku und Paketversionen im Blick behalten.

Warum: Was Claude Desktop für MCP-Apps, Extensions und Panels anbietet, ändert sich laufend
(Hauptversion von ext-apps, neue MCP-Spezifikation, neue Seiten im Leitfaden). Dieses Skript
holt die Seiten, die für dieses Projekt zählen, und sagt, was NEU, GEÄNDERT oder WEG ist —
und welche Pakete eine neue Version haben.

Quellen: die maschinenlesbaren Indizes `llms.txt` von claude.com/docs und modelcontextprotocol.io
(Liste in docs/anthropic/quellen.json). Es werden nur Seiten aus diesen Indizes geholt, deren Pfad
zu einem Muster passt.

Urheberrecht: Die Texte bleiben LOKAL (`.cache/anthropic/`, nicht im Git). Ins Repository kommen nur
Fingerabdrücke, Titel und Links (`docs/anthropic/stand.json`) und die eigene Auswertung
(`docs/anthropic/abgleich.md`).

    uv run python scripts/anthropic_sync.py --check         # holen und vergleichen, nichts speichern
    uv run python scripts/anthropic_sync.py --diff URL      # Textunterschied einer Seite
    uv run python scripts/anthropic_sync.py --update        # Stand übernehmen (nach dem Lesen!)
    uv run python scripts/anthropic_sync.py --alter         # nur Altersmeldung, ohne Netz (für den Sitzungsstart)
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUELLEN = ROOT / "docs" / "anthropic" / "quellen.json"
STAND = ROOT / "docs" / "anthropic" / "stand.json"
CACHE = ROOT / ".cache" / "anthropic"
TAGE_BIS_VERALTET = 7
USER_AGENT = "chemdraw-mcp-doc-watch (+https://github.com/jurimaxam-dotcom/chemdraw-mcp)"

_LINK = re.compile(r"^- \[(?P<titel>[^\]]+)\]\((?P<url>https?://[^)\s]+)\)(?::\s*(?P<beschreibung>.*))?$")


# --- reine Funktionen (getestet ohne Netz) -------------------------------------------------------


def parse_index(text: str) -> list[dict]:
    eintraege = []
    for zeile in text.splitlines():
        m = _LINK.match(zeile.strip())
        if m:
            eintraege.append(
                {"titel": m["titel"], "url": m["url"], "beschreibung": (m["beschreibung"] or "").strip()}
            )
    return eintraege


def waehle(eintraege: list[dict], muster: list[str]) -> list[dict]:
    regeln = [re.compile(m) for m in muster]
    return [e for e in eintraege if any(r.search(e["url"]) for r in regeln)]


def normalisiere(text: str) -> str:
    zeilen = [re.sub(r"[ \t]+", " ", z).strip() for z in text.replace("\r\n", "\n").split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(zeilen)).strip() + "\n"


def fingerabdruck(text: str) -> str:
    return hashlib.sha256(normalisiere(text).encode("utf-8")).hexdigest()[:16]


def slug(url: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", re.sub(r"^https?://", "", url)).strip("_")[:150] + ".md"


def vergleiche(alt: dict, neu: dict) -> dict:
    return {
        "neu": sorted(set(neu) - set(alt)),
        "weg": sorted(set(alt) - set(neu)),
        "geaendert": sorted(u for u in set(alt) & set(neu) if alt[u]["hash"] != neu[u]["hash"]),
    }


def _hauptversion(v: str) -> int | None:
    m = re.search(r"(\d+)\.(\d+)", v)
    return int(m.group(1)) if m else None


def _zahlen(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def versionsbericht(unsere: dict, neueste: dict) -> list[dict]:
    zeilen = []
    for name, pin in unsere.items():
        letzte = neueste.get(name, "?")
        if letzte == "?":
            status = "unbekannt"
        else:
            ours = re.sub(r"<\d+.*$", "", pin)  # „>=1.27,<2“ → untere Grenze
            ours = re.search(r"\d+(?:\.\d+)+", ours)
            ours = ours.group(0) if ours else pin
            if _hauptversion(letzte) != _hauptversion(ours) and _hauptversion(letzte) and _hauptversion(ours):
                status = "NEUE HAUPTVERSION" if _hauptversion(letzte) > _hauptversion(ours) else "aktuell"
            elif _zahlen(letzte) > _zahlen(ours):
                status = "neuere Nebenversion"
            else:
                status = "aktuell"
        zeilen.append({"name": name, "unsere": pin, "neueste": letzte, "status": status})
    return zeilen


def lese_pins(root: Path) -> dict:
    pins = {}
    paket = json.loads((root / "chemdraw_tool" / "ui" / "package.json").read_text())
    pins["ext-apps"] = paket["dependencies"]["@modelcontextprotocol/ext-apps"]
    m = re.search(r"@anthropic-ai/mcpb@(\d+\.\d+\.\d+)", (root / "scripts" / "build-mcpb.sh").read_text())
    pins["mcpb"] = m.group(1) if m else "?"
    m = re.search(r'"mcp([^"]*)"', (root / "pyproject.toml").read_text().split("dependencies", 1)[1])
    pins["mcp"] = (m.group(1) or "?") if m else "?"
    return pins


def alterswarnung(stand: Path, heute: str | None = None, tage: int = TAGE_BIS_VERALTET) -> str:
    if not stand.exists():
        return "Anthropic-Doku: noch nie geprüft — `uv run python scripts/anthropic_sync.py --check`"
    geprueft = json.loads(stand.read_text()).get("geprueft", "")
    try:
        alter = (dt.date.fromisoformat(heute or dt.date.today().isoformat()) - dt.date.fromisoformat(geprueft)).days
    except ValueError:
        return "Anthropic-Doku: Stand unlesbar — neu prüfen"
    if alter > tage:
        return f"Anthropic-Doku: Stand veraltet ({alter} Tage, geprüft {geprueft}) — vor Architekturarbeit `scripts/anthropic_sync.py --check`"
    return ""


# --- Netz und Dateien ----------------------------------------------------------------------------


def hole(url: str) -> str:
    anfrage = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(anfrage, timeout=30) as antwort:  # noqa: S310 — feste, bekannte https-Adressen
        return antwort.read().decode("utf-8", "replace")


def sammle(quellen: dict, abruf=hole) -> dict[str, dict]:
    """url → {titel, beschreibung, hash, text} für alle gewählten Seiten."""
    seiten = {}
    for index in quellen["indizes"]:
        for e in waehle(parse_index(abruf(index["url"])), index["einschliessen"]):
            try:
                text = abruf(e["url"])
            except Exception as fehler:  # noqa: BLE001 — eine tote Seite darf den Rest nicht stoppen
                print(f"  ! {e['url']}: {fehler}", file=sys.stderr)
                continue
            seiten[e["url"]] = {**e, "quelle": index["name"], "hash": fingerabdruck(text), "text": text}
    return seiten


def pruefe(quellen: dict, stand_datei: Path, cache: Path, abruf=hole, aktualisieren: bool = False) -> dict:
    alt = json.loads(stand_datei.read_text())["seiten"] if stand_datei.exists() else {}
    neu = sammle(quellen, abruf)
    ergebnis = vergleiche(alt, neu)
    ergebnis["texte"] = {u: neu[u]["text"] for u in ergebnis["geaendert"] + ergebnis["neu"]}
    ergebnis["vorher"] = {}
    for u in ergebnis["geaendert"]:
        datei = cache / slug(u)
        ergebnis["vorher"][u] = datei.read_text() if datei.exists() else ""
    if aktualisieren:
        cache.mkdir(parents=True, exist_ok=True)
        for u, s in neu.items():
            (cache / slug(u)).write_text(s["text"])
        stand_datei.parent.mkdir(parents=True, exist_ok=True)
        stand_datei.write_text(
            json.dumps(
                {
                    "geprueft": dt.date.today().isoformat(),
                    "hinweis": "Fingerabdrücke und Titel — die Texte liegen lokal in .cache/anthropic/ und gehören Anthropic.",
                    "seiten": {
                        u: {k: s[k] for k in ("titel", "beschreibung", "quelle", "hash")} for u, s in sorted(neu.items())
                    },
                },
                indent=1,
                ensure_ascii=False,
            )
            + "\n"
        )
    return ergebnis


def neueste_versionen() -> dict:
    def json_von(url):
        return json.loads(hole(url))

    return {
        "ext-apps": json_von("https://registry.npmjs.org/@modelcontextprotocol/ext-apps/latest")["version"],
        "mcpb": json_von("https://registry.npmjs.org/@anthropic-ai/mcpb/latest")["version"],
        "mcp": json_von("https://pypi.org/pypi/mcp/json")["info"]["version"],
    }


def letzte_releases(n: int = 4) -> list[str]:
    try:
        daten = json.loads(hole(f"https://api.github.com/repos/modelcontextprotocol/ext-apps/releases?per_page={n}"))
    except Exception as fehler:  # noqa: BLE001
        return [f"(Releases nicht lesbar: {fehler})"]
    return [f"{r['tag_name']}  {r['published_at'][:10]}  {(r.get('name') or '')[:70]}" for r in daten]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="holen und vergleichen, nichts speichern")
    ap.add_argument("--update", action="store_true", help="Stand und lokalen Cache übernehmen")
    ap.add_argument("--diff", metavar="URL", help="Textunterschied einer Seite gegen den lokalen Cache")
    ap.add_argument("--alter", action="store_true", help="nur Altersmeldung (ohne Netz)")
    a = ap.parse_args()

    if a.alter:
        meldung = alterswarnung(STAND)
        if meldung:
            print(meldung)
        return 0
    quellen = json.loads(QUELLEN.read_text())
    if a.diff:
        neu = hole(a.diff)
        datei = CACHE / slug(a.diff)
        alt = datei.read_text() if datei.exists() else ""
        sys.stdout.writelines(difflib.unified_diff(alt.splitlines(True), neu.splitlines(True), "lokal", "jetzt", n=2))
        return 0

    r = pruefe(quellen, STAND, CACHE, aktualisieren=a.update)
    print(f"Anthropic-Doku — {len(r['neu'])} neu · {len(r['geaendert'])} geändert · {len(r['weg'])} weg")
    for u in r["neu"]:
        print(f"  NEU        {u}")
    for u in r["geaendert"]:
        print(f"  GEÄNDERT   {u}")
    for u in r["weg"]:
        print(f"  WEG        {u}")
    print("\nPakete (unser Stand → neueste Version):")
    for z in versionsbericht(lese_pins(ROOT), neueste_versionen()):
        marke = "!!" if z["status"] == "NEUE HAUPTVERSION" else "  "
        print(f"  {marke} {z['name']:9} {z['unsere']:14} → {z['neueste']:8} {z['status']}")
    print("\nLetzte ext-apps-Releases:")
    for zeile in letzte_releases():
        print("   ", zeile)
    if a.update:
        print(f"\nStand übernommen: {STAND.relative_to(ROOT)} (Texte lokal in .cache/anthropic/)")
    elif r["neu"] or r["geaendert"] or r["weg"]:
        print("\nNächster Schritt: Seiten lesen (`--diff URL`), `docs/anthropic/abgleich.md` anpassen, dann `--update`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
