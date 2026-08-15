"""Die Bereichskarte gehoert einmal an den Server, nicht zwanzigmal in die Tools.

Anlass (15.08.2026): Recherche zur Werkzeugwahl. Das `instructions`-Feld der
MCP-Initialisierung ist laut Spec ein „hint to the model", den Clients in den
Systemprompt uebernehmen duerfen — der einzige Ort, an dem die fuenf Bereiche
EINMAL erklaert werden koennen statt in jeder einzelnen Tool-Beschreibung.
Der Server liess das Feld bis dahin leer.

Claude Code kappt `instructions` bei 2 KB (dokumentiert) und schneidet dabei
das Ende ab — deshalb steht das Wichtigste vorn und die Laenge ist begrenzt.
"""

from chemdraw_tool.server import mcp

MAX_BYTES = 2048


def _instructions() -> str:
    return mcp.instructions or ""


def test_server_has_instructions():
    """Ohne dieses Feld muss jede Tool-Beschreibung die Landkarte mittragen."""
    assert _instructions().strip(), (
        "instructions= am FastMCP-Konstruktor ist leer — die Bereichskarte "
        "fehlt dem Modell komplett."
    )


def test_instructions_name_every_area():
    """Alle fuenf Bereiche muessen vorkommen, sonst ist die Karte unvollstaendig."""
    text = _instructions().lower()
    for area in ("draw", "lab graphic", "look up", "calculate", "anki"):
        assert area in text, f"Bereich {area!r} fehlt in den instructions"


def test_instructions_route_the_bare_compound_name():
    """Der Fall, der real danebenging: nur ein Stoffname, sonst nichts."""
    text = _instructions()
    assert "generate_molecule" in text, (
        "Die instructions muessen den Default fuer einen blanken Stoffnamen "
        "benennen — das ist der Fall, den keine Tool-Beschreibung reklamiert."
    )


def test_instructions_stay_under_the_2kb_cap():
    """Ueber 2 KB schneidet der Client ab — und zwar hinten."""
    size = len(_instructions().encode())
    assert size <= MAX_BYTES, f"instructions sind {size} B, erlaubt sind {MAX_BYTES}"


def test_instructions_are_english():
    """Nutzersichtbarer Text ist englisch (Projektkonvention)."""
    text = _instructions()
    for german in ("Zeichnen", "Nachschlagen", "Molekuel", "Struktur von"):
        assert german not in text, f"Deutscher Text in den instructions: {german!r}"
