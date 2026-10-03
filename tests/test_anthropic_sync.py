"""scripts/anthropic_sync.py: Anthropic-Doku und Paketversionen im Blick behalten.

Alles ohne Netz: der Abruf wird als Funktion hineingereicht.
"""

import importlib.util
import json
from pathlib import Path

SKRIPT = Path(__file__).parent.parent / "scripts" / "anthropic_sync.py"
spec = importlib.util.spec_from_file_location("anthropic_sync", SKRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

INDEX = """# Claude Docs

> Index

- [Design guidelines](https://claude.com/docs/connectors/building/mcp-apps/design-guidelines.md): Design MCP Apps that feel native.
- [Get started](https://claude.com/docs/connectors/getting-started.md): Connect Claude to an app.
- [Open links](https://claude.com/docs/connectors/building/mcp-apps/external-links.md): Declare allowed link destinations.
Eine Zeile ohne Link.
"""


def test_index_wird_in_eintraege_zerlegt():
    eintraege = sync.parse_index(INDEX)
    assert [e["url"] for e in eintraege] == [
        "https://claude.com/docs/connectors/building/mcp-apps/design-guidelines.md",
        "https://claude.com/docs/connectors/getting-started.md",
        "https://claude.com/docs/connectors/building/mcp-apps/external-links.md",
    ]
    assert eintraege[0]["titel"] == "Design guidelines"
    assert eintraege[0]["beschreibung"].startswith("Design MCP Apps")


def test_auswahl_nach_pfadmuster():
    eintraege = sync.parse_index(INDEX)
    gewaehlt = sync.waehle(eintraege, ["/connectors/building/mcp-apps/"])
    assert len(gewaehlt) == 2 and all("mcp-apps" in e["url"] for e in gewaehlt)


def test_normalisierung_ignoriert_leerraum_aber_nicht_inhalt():
    a = "Titel\n\n\n\nText   mit  Leerraum  \n"
    b = "Titel\n\nText mit Leerraum\n"
    assert sync.fingerabdruck(a) == sync.fingerabdruck(b)
    assert sync.fingerabdruck(a) != sync.fingerabdruck(b + "Neuer Satz")


def test_vergleich_findet_neu_geaendert_und_weg():
    alt = {
        "u1": {"hash": "aaa", "titel": "Eins"},
        "u2": {"hash": "bbb", "titel": "Zwei"},
        "u3": {"hash": "ccc", "titel": "Drei"},
    }
    neu = {
        "u1": {"hash": "aaa", "titel": "Eins"},
        "u2": {"hash": "XXX", "titel": "Zwei"},
        "u4": {"hash": "ddd", "titel": "Vier"},
    }
    r = sync.vergleiche(alt, neu)
    assert r["neu"] == ["u4"]
    assert r["geaendert"] == ["u2"]
    assert r["weg"] == ["u3"]


def test_versionsvergleich_nennt_hauptversionen():
    zeilen = sync.versionsbericht(
        {"ext-apps": "^1.7.4", "mcp": ">=1.27,<2", "mcpb": "2.1.2"},
        {"ext-apps": "2.0.3", "mcp": "2.3.0", "mcpb": "2.1.2"},
    )
    status = {z["name"]: z["status"] for z in zeilen}
    assert status["ext-apps"] == "NEUE HAUPTVERSION"
    assert status["mcp"] == "NEUE HAUPTVERSION"
    assert status["mcpb"] == "aktuell"


def test_versionsvergleich_kleine_aenderung():
    z = sync.versionsbericht({"x": "1.7.4"}, {"x": "1.9.0"})[0]
    assert z["status"] == "neuere Nebenversion"


def test_pins_werden_aus_den_projektdateien_gelesen():
    pins = sync.lese_pins(Path(__file__).parent.parent)
    assert pins["ext-apps"].lstrip("^~") .startswith("1.")
    assert pins["mcpb"].count(".") == 2
    assert "mcp" in pins


def test_pruefung_mit_fake_abruf_und_stand(tmp_path):
    seiten = {
        "https://x/index.txt": "- [A](https://x/a.md): Seite A\n- [B](https://x/b.md): Seite B\n",
        "https://x/a.md": "Inhalt A",
        "https://x/b.md": "Inhalt B",
    }
    quellen = {"indizes": [{"name": "x", "url": "https://x/index.txt", "einschliessen": ["/"]}]}
    stand_datei = tmp_path / "stand.json"
    cache = tmp_path / "cache"

    erster = sync.pruefe(quellen, stand_datei, cache, abruf=seiten.__getitem__, aktualisieren=True)
    assert sorted(erster["neu"]) == ["https://x/a.md", "https://x/b.md"]
    assert json.loads(stand_datei.read_text())["seiten"]

    seiten["https://x/b.md"] = "Inhalt B, jetzt anders"
    zweiter = sync.pruefe(quellen, stand_datei, cache, abruf=seiten.__getitem__, aktualisieren=False)
    assert zweiter["geaendert"] == ["https://x/b.md"]
    assert zweiter["neu"] == [] and zweiter["weg"] == []
    # ohne --update bleibt der gespeicherte Stand unverändert (erst nach dem Lesen wird er übernommen)
    gespeichert = json.loads(stand_datei.read_text())["seiten"]["https://x/b.md"]["hash"]
    assert gespeichert == sync.fingerabdruck("Inhalt B")
    # mit --update wird er übernommen
    sync.pruefe(quellen, stand_datei, cache, abruf=seiten.__getitem__, aktualisieren=True)
    uebernommen = json.loads(stand_datei.read_text())["seiten"]["https://x/b.md"]["hash"]
    assert uebernommen == sync.fingerabdruck("Inhalt B, jetzt anders")


def test_veralteter_stand_wird_gemeldet(tmp_path):
    stand = tmp_path / "stand.json"
    stand.write_text(json.dumps({"geprueft": "2026-09-01", "seiten": {}}))
    assert "veraltet" in sync.alterswarnung(stand, heute="2026-10-03", tage=7)
    assert sync.alterswarnung(stand, heute="2026-09-03", tage=7) == ""
    assert "noch nie" in sync.alterswarnung(tmp_path / "fehlt.json", heute="2026-10-03", tage=7)
