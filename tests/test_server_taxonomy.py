"""Der Tool-Zuschnitt des Servers ist ab jetzt eine Zusage, kein Zufall.

Anlass (15.08.2026): „Zeichne Aspirin" landete im Desktop bei
`generate_scope_table` statt bei `generate_molecule` — ein Ein-Zellen-Raster
statt der Strukturformel. Das Modell wählt Tools ausschließlich nach Namen und
Beschreibung; 22 Tools mit unscharfen Grenzen sind deshalb ein Präzisionsproblem,
kein Kosmetikproblem.

Die Antwort darauf sind Bereiche mit klaren Grenzen. Dieser Test hält sie fest,
damit ein neues Tool bewusst einem Bereich zugeordnet wird, statt still
danebenzufallen:

* Zeichnen        — Strukturen und Reaktionen
* Laborgrafik     — Messdaten und Diagramme
* Nachschlagen    — Datenbankabfragen
* Rechnen         — Zahl plus Rechenweg
* Anki            — Kartendecks

Außerhalb der Bereiche steht genau ein Tool: `save_png`, der Server-Teil des
Export-Knopfes im Panel. Es MUSS registriert bleiben (sonst kann die UI es nicht
aufrufen), darf aber nie vom Modell von sich aus benutzt werden — deshalb wird
hier auch geprüft, dass seine Beschreibung es als intern ausweist.
"""

import inspect

import pytest

from chemdraw_tool import server
from chemdraw_tool.server import mcp

# --- Die Bereiche ------------------------------------------------------

ZEICHNEN = {
    "generate_molecule",
    "compare_molecules",
    "batch_generate",
    "generate_reaction",
    "generate_mechanism",
    "generate_scope_table",
    "generate_3d",
}

LABORGRAFIK = {
    "generate_spectrum",
    "generate_tlc",
    "generate_titration_curve",
    "generate_species_distribution",
    "generate_calibration_curve",
}

# „Nachschlagen" heisst Fakten zu einem Stoff — aus einer Datenbank (lookup,
# lookup_molecule_data) oder aus seiner Struktur abgeleitet (predict_spectrum).
NACHSCHLAGEN = {"lookup", "lookup_molecule_data", "predict_spectrum"}

# Fünfter Bereich seit 15.08.2026: Rechnungen liefern Zahl UND Rechenweg —
# eine eigene Art Ausgabe, die weder Bild noch Datenblatt ist.
RECHNEN = {"calculate_solution", "calculate_content", "calculate_ph"}

ANKI = {"export_anki_deck"}

# Kein Bereich, sondern Infrastruktur des Panels.
INTERN = {"save_png"}

FAMILIES = {
    "Zeichnen": ZEICHNEN,
    "Laborgrafik": LABORGRAFIK,
    "Nachschlagen": NACHSCHLAGEN,
    "Rechnen": RECHNEN,
    "Anki": ANKI,
}

# Nur mit CHEMDRAW_VAULT_PATH registriert — sonst gar nicht vorhanden.
VAULT = {"search_vault", "read_vault_entry"}


def _registered() -> dict[str, str]:
    """{Toolname: Beschreibung} aller registrierten Tools ohne Vault."""
    return {
        t.name: (t.description or "")
        for t in mcp._tool_manager.list_tools()
        if t.name not in VAULT
    }


def test_registered_tools_are_exactly_the_families_plus_save_png():
    """Ein neues Tool muss hier eingetragen werden — genau das ist der Zweck."""
    expected = ZEICHNEN | LABORGRAFIK | NACHSCHLAGEN | RECHNEN | ANKI | INTERN
    actual = set(_registered())
    assert actual == expected, (
        f"Zusätzlich registriert: {sorted(actual - expected)} · "
        f"Fehlt: {sorted(expected - actual)} — neues Tool einem Bereich "
        "zuordnen (oder bewusst als intern eintragen)."
    )


def test_families_do_not_overlap():
    """Ein Tool gehört in genau einen Bereich, sonst ist die Grenze unklar."""
    seen: dict[str, str] = {}
    for family, tools in FAMILIES.items():
        for tool in tools:
            assert tool not in seen, f"{tool} steht in {seen[tool]} UND {family}"
            seen[tool] = family


def test_tool_count_stays_reviewable():
    """Obergrenze mit Ansage: jedes Tool ist ein Kandidat bei jeder Anfrage.

    Kein Selbstzweck — wächst die Liste wieder Richtung 22, muss das eine
    bewusste Entscheidung sein und nicht durch Anbauen passieren. Die Grenze
    wurde am 15.08.2026 von 16 auf 18 gehoben, um den Bereich „Rechnen"
    aufzunehmen, auf 19 fuer die Kalibriergerade und auf 20 fuer die
    Spektren-Vorhersage; jede Rechenart ist ein
    `topic` bzw. eine `method`, kein eigenes Tool.
    """
    assert len(_registered()) <= 20


# --- Entfernte Tools --------------------------------------------------------


@pytest.mark.parametrize(
    "gone",
    [
        "lookup_compound",
        "lookup_safety",
        "lookup_physical",
        "lookup_biochem",
        "lookup_pathway",
        "export_curated_deck",
        "calculate_validation",
        "open_chemdraw_file",
    ],
)
def test_removed_tools_are_not_registered(gone):
    """Gebündelt oder vorerst ausgebaut — in keinem Fall noch ein Kandidat."""
    assert gone not in _registered()


# --- Abgrenzung in den Beschreibungen ---------------------------------------

# Tools, deren Verwechslung real passiert ist oder naheliegt: Sie müssen sagen,
# wofür sie NICHT zuständig sind, und das Alternativtool beim Namen nennen.
NEEDS_DELIMITATION = {
    "generate_molecule": ("generate_scope_table", "lookup"),
    "generate_scope_table": ("generate_molecule",),
    "compare_molecules": ("generate_molecule",),
    "batch_generate": ("generate_molecule",),
    "generate_reaction": ("generate_mechanism",),
    "generate_mechanism": ("generate_reaction",),
    # Der Coffein-Fall (15.08.2026): Ein blanker Stoffname ist maximal nah an
    # „what is X" und enthaelt kein Zeichen-Verb. Beide Nachschlage-Tools
    # muessen deshalb auf das Zeichnen zeigen, nicht nur aufeinander.
    "lookup": ("lookup_molecule_data", "generate_molecule"),
    "lookup_molecule_data": ("lookup", "generate_molecule"),
    "calculate_solution": ("calculate_content",),
    "calculate_content": ("calculate_solution",),
    "calculate_ph": ("generate_titration_curve",),
    # Gegenrichtung: Ohne sie faengt das Zeichen-Tool die Rechenfrage ab —
    # dieselbe Konstellation wie beim Aspirin-Fehlgriff.
    "generate_titration_curve": ("calculate_ph",),
    "generate_species_distribution": ("calculate_ph",),
    # Beide machen aus einem Signal einen Gehalt — die eine ueber eine
    # gemessene Reihe, die andere ueber die Monographie-Konstante.
    "generate_calibration_curve": ("calculate_content",),
    "predict_spectrum": ("generate_spectrum",),
    "generate_spectrum": ("predict_spectrum",),
}


@pytest.mark.parametrize("tool,alternatives", sorted(NEEDS_DELIMITATION.items()))
def test_description_names_what_it_is_not_for(tool, alternatives):
    """„Not this tool for: … — use X" ist die Zeile, die den Fehlgriff verhindert."""
    desc = _registered()[tool]
    assert "Not this tool for" in desc, (
        f"{tool} grenzt sich nicht ab — ohne diese Zeile wählt das Modell "
        "nach Bauchgefühl."
    )
    for alternative in alternatives:
        assert alternative in desc, (
            f"{tool} nennt die Alternative {alternative} nicht"
        )


# --- Der unterspezifizierte Prompt ------------------------------------------
#
# Zweiter Befund vom 15.08.2026, aus der Recherche zur Werkzeugwahl: „Zeichne
# Aspirin" → generate_scope_table war ein Zaun-Problem. Ein blankes „Coffein"
# ist etwas anderes — ein unterspezifizierter Prompt. Dagegen hilft kein
# schaerferer Zaun, sondern eine erklaerte Default-Regel: irgendein Tool muss
# den Fall ausdruecklich fuer sich reklamieren, sonst gewinnt ihn das Tool,
# das „what is X" am lautesten sagt.


def test_generate_molecule_claims_the_bare_compound_name():
    """Der nackte Stoffname gehoert dem Zeichen-Tool — schriftlich."""
    desc = _registered()["generate_molecule"]
    assert "bare compound name" in desc, (
        "generate_molecule reklamiert den blanken Stoffnamen nicht. Ohne den "
        "Satz faellt 'Coffein' an lookup, weil dort 'what is X' steht."
    )


def test_lookup_does_not_magnetise_the_bare_name():
    """Der Magnet-Satz zieht jeden nackten Stoffnamen ins Nachschlagen."""
    desc = _registered()["lookup"]
    assert "what is X" not in desc, (
        "lookup beansprucht weiterhin 'what is X' — genau der Satz, der den "
        "blanken Stoffnamen abfaengt."
    )


# Superlative verschieben den Nutzungsanteil messbar (Faghih et al. 2025,
# arXiv:2505.18135: 7,48 : 1 fuer einen angehaengten Werbesatz), OHNE die
# Trefferquote zu verbessern — ein aufgeblaehtes Tool klaut Aufrufe von seinen
# Nachbarn. Deshalb duerfen Beschreibungen beschreiben, aber nicht werben.
SUPERLATIVES = (
    "One tool for every",
    "most effective",
    "best tool",
    "whenever possible",
    "always use this",
)


@pytest.mark.parametrize("phrase", SUPERLATIVES)
def test_no_tool_advertises_itself(phrase):
    """Werbung in der Beschreibung erzeugt Bias, keinen Gewinn."""
    offenders = [name for name, desc in _registered().items() if phrase in desc]
    assert not offenders, (
        f"Superlativ {phrase!r} in: {offenders} — beschreiben statt werben, "
        "sonst klaut das Tool Aufrufe von seinen Nachbarn."
    )


# --- Laenge -----------------------------------------------------------------

# Claude Code kappt Tool-Beschreibungen bei 2 KB und schneidet hinten ab. Fuer
# Claude Desktop ist das nicht dokumentiert, aber Kuerzen ist risikolos: was
# faellt, ist die Parameter-Doku am Ende — nie eine Abgrenzungszeile.
MAX_DESCRIPTION_BYTES = 2048


@pytest.mark.parametrize("tool", sorted(_registered()))
def test_description_survives_the_2kb_cap(tool):
    desc = _registered()[tool]
    size = len(desc.encode())
    assert size <= MAX_DESCRIPTION_BYTES, (
        f"{tool}: {size} B — {size - MAX_DESCRIPTION_BYTES} B ueber der Kappung. "
        "Parameter-Doku kuerzen, nie die Abgrenzung."
    )


def test_save_png_is_declared_internal():
    """Der Export-Knopf ruft es auf — das Modell nie von sich aus."""
    desc = _registered()["save_png"]
    assert "Internal" in desc
    assert "never call this directly" in desc


# --- Das gebündelte lookup --------------------------------------------------


def test_lookup_topic_is_a_closed_set():
    """Literal statt Prosa: das Schema selbst grenzt die Themen ein."""
    sig = inspect.signature(server.lookup)
    topic = sig.parameters["topic"]
    values = getattr(topic.annotation, "__args__", ())
    assert set(values) == {
        "properties",
        "safety",
        "physical",
        "biochem",
        "pathway",
    }, f"Unerwartete Themen: {values}"


def test_lookup_defaults_to_properties():
    """Ohne Themenangabe die häufigste Frage beantworten, nicht scheitern."""
    assert inspect.signature(server.lookup).parameters["topic"].default == "properties"


def test_lookup_rejects_unknown_topic():
    """Ein Tippfehler im Thema darf nicht still die Grunddaten liefern."""
    with pytest.raises(ValueError, match="topic"):
        server.lookup("Aspirin", topic="gibtsnicht")
