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
}

NACHSCHLAGEN = {"lookup", "lookup_molecule_data"}

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
    aufzunehmen; jede Rechenart ist dort ein `topic`, kein eigenes Tool.
    """
    assert len(_registered()) <= 18


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
    "generate_molecule": "generate_scope_table",
    "generate_scope_table": "generate_molecule",
    "compare_molecules": "generate_molecule",
    "batch_generate": "generate_molecule",
    "generate_reaction": "generate_mechanism",
    "generate_mechanism": "generate_reaction",
    "lookup": "lookup_molecule_data",
    "lookup_molecule_data": "lookup",
    "calculate_solution": "calculate_content",
    "calculate_content": "calculate_solution",
    "calculate_ph": "calculate_solution",
}


@pytest.mark.parametrize("tool,alternative", sorted(NEEDS_DELIMITATION.items()))
def test_description_names_what_it_is_not_for(tool, alternative):
    """„Not this tool for: … — use X" ist die Zeile, die den Fehlgriff verhindert."""
    desc = _registered()[tool]
    assert "Not this tool for" in desc, (
        f"{tool} grenzt sich nicht ab — ohne diese Zeile wählt das Modell "
        "nach Bauchgefühl."
    )
    assert alternative in desc, f"{tool} nennt die Alternative {alternative} nicht"


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
