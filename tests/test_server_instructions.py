"""Die Bereichskarte gehoert einmal an den Server, nicht zwanzigmal in die Tools.

Anlass (15.08.2026): Recherche zur Werkzeugwahl. Das `instructions`-Feld der
MCP-Initialisierung ist laut Spec ein „hint to the model", den Clients in den
Systemprompt uebernehmen duerfen — der einzige Ort, an dem die fuenf Bereiche
EINMAL erklaert werden koennen statt in jeder einzelnen Tool-Beschreibung.
Der Server liess das Feld bis dahin leer.

Claude Code kappt `instructions` bei 2 KB (dokumentiert) und schneidet dabei
das Ende ab — deshalb steht das Wichtigste vorn und die Laenge ist begrenzt.
"""

import pytest

from tests.server_catalog import mcp

MAX_BYTES = 2048


def _instructions() -> str:
    return mcp.instructions or ""


def test_server_has_instructions():
    """Ohne dieses Feld muss jede Tool-Beschreibung die Landkarte mittragen."""
    assert _instructions().strip(), (
        "instructions= am MCPServer-Konstruktor ist leer — die Bereichskarte "
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


# --- Proaktives Auslösen (Auftrag Jay, 15.08.2026) ---------------------------
#
# Zweite Haelfte des Routing-Problems: Das Modell greift zu selten zu, nicht nur
# manchmal daneben. Ein Pharmazie-Alltag besteht aus Erklaerfragen — „erklaer
# mir Ibuprofen", „wie laeuft die Veresterung", „ich muss die NSAR lernen" —
# und keine davon enthaelt ein Zeichen-Verb. Ohne eine ausdrueckliche Regel
# antwortet das Modell mit Prosa, obwohl ein Panel mit Struktur, eine
# Reaktionsgleichung oder ein Kartendeck die bessere Antwort waere.

PROACTIVE_MARKERS = ("explain", "learn")


@pytest.mark.parametrize("marker", PROACTIVE_MARKERS)
def test_instructions_invite_the_everyday_case(marker):
    """Die Bereichskarte muss sagen, wann von selbst gezeichnet wird."""
    assert marker in _instructions().lower(), (
        f"{marker!r} fehlt — ohne die Einladung bleibt eine Erklaerfrage Prosa, "
        "obwohl ein Panel die bessere Antwort waere."
    )


def test_instructions_do_not_forbid_the_everyday_case():
    """Die Erklaerfrage ist der Anlass zu zeichnen, nicht der Ausschluss.

    Die erste Fassung der Karte trug woertlich „do not use these tools for:
    naming or explaining chemistry in prose" — eine Bremse genau dort, wo der
    Pharmazie-Alltag stattfindet. Erklaeren und Zeichnen sind kein Entweder-oder.
    """
    text = _instructions().lower()
    for brake in ("explaining chemistry in prose", "not use these tools for"):
        assert brake not in text, (
            f"Bremsklotz in den instructions: {brake!r} — haelt das Modell "
            "genau bei der haeufigsten Frage vom Zeichnen ab."
        )


def test_instructions_name_the_panel_as_the_point():
    """Das Molekuel-Panel ist interaktiv — das ist der Grund, es zu zeigen."""
    text = _instructions().lower()
    assert "panel" in text or "hover" in text, (
        "Die Karte erwaehnt das Panel nicht. Es ist der Unterschied zwischen "
        "einem Bild und etwas, in dem man Atome antippen kann."
    )


# Desktop-Abnahme 02.11.2026: Mit Tool-Suche (Desktop lädt Tools erst bei Bedarf)
# sieht das Modell vorab nur Namen und diese Hinweise. pH-Fragen beantwortete es
# dann 6/6 ohne Suche aus dem Kopf (evals: desktop-ph-*, ENABLE_TOOL_SEARCH=true).
# Die Regel muss im Standardprofil stehen und vorn, weil Claude Code hinten kappt.
def test_mvp_instructions_claim_ph_numbers_early():
    from chemdraw_tool.server import _MVP_INSTRUCTIONS as text

    assert len(text.encode()) <= MAX_BYTES
    line = next((z for z in text.splitlines() if "calculate_ph" in z and "yourself" in z), None)
    assert line, "keine eigene Zeile: pH-Zahl → calculate_ph, auch wenn man selbst rechnen könnte"
    assert text.index(line) < len(text) // 2, "pH-Regel steht in der hinteren Hälfte"


def test_mvp_instructions_drop_the_seven_tool_wording():
    from chemdraw_tool.server import _MVP_INSTRUCTIONS as text

    assert "temporarily disabled" not in text and "MVP profile" not in text


# Desktop-Handtest 10.11.2026 (Runde 5): „Draw trastuzumab“ ging an ein
# hosteigenes Zeichenwerkzeug („explaining … as a domain schematic instead“).
# Mit Tool-Suche sieht das Modell vorab nur Namen und diese Hinweise — steht
# hier nichts von Proteinen, hält es einen Antikörper für nicht zeichenbar.
@pytest.mark.parametrize("name", ["_MVP_INSTRUCTIONS", "_FULL_INSTRUCTIONS"])
def test_instructions_claim_proteins_and_antibodies_early(name):
    from chemdraw_tool import server

    text = getattr(server, name)
    assert len(text.encode()) <= MAX_BYTES
    start = next((i for i, z in enumerate(text.splitlines())
                  if "protein" in z.lower() and "antibody" in z.lower()), None)
    assert start is not None, "keine Zeile: Protein-/Antikörpername → generate_molecule"
    rule = " ".join(text.splitlines()[start:start + 2])
    assert "generate_molecule" in rule and "cartoon" in rule
    assert "trastuzumab" in rule, "ein INN als Beispiel — der Fall aus dem Handtest"
    assert text.index(text.splitlines()[start]) < len(text) // 2, "Protein-Regel steht in der hinteren Hälfte"
