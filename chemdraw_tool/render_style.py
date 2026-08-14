"""Opt-in-Zeichenstile und Gruppen-Abkürzungen — beides ohne Default-Wirkung.

Zwei Stellschrauben, die Ausgaben ohne Nacharbeit publikationsreif machen:

1. **Gruppen-Kontraktion** — Chemiker schreiben Ph, OAc, CO₂H statt jeden
   Ring und jede Estergruppe auszuzeichnen. RDKit bringt das mit
   (`rdAbbreviations`), die Default-Liste (37 Definitionen) kennt aber
   ausgerechnet die Schutzgruppen- und Aryl-Kürzel nicht — die stehen hier
   in `_EXTRA_ABBREVIATIONS`.
2. **Stil-Presets** — benannte Bündel von `MolDrawOptions`-Werten, die der
   Nutzer beim Namen nennen kann, statt einzelne Renderparameter zu setzen.

HARTE REGEL: Ohne Stilangabe wird an den Zeichenoptionen nichts angefasst.
`apply_style(opts, "")` kehrt sofort zurück — nur so bleibt das Default-
Rendering bitgleich zum committeten Pixel-Snapshot der UI-Vorschau.
"""

from __future__ import annotations

from dataclasses import dataclass

from rdkit import Chem
from rdkit.Chem import rdAbbreviations

# ---------------------------------------------------------------------------
# Stil-Presets
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DrawStyle:
    """Überschreibungen für RDKits MolDrawOptions.

    `None` heißt: Feld nicht anfassen. Ein Preset beschreibt also nur seine
    Abweichung vom bisherigen Verhalten — es setzt keinen Vollzustand, damit
    künftige RDKit-Defaults nicht stillschweigend eingefroren werden.
    """

    bond_line_width: float | None = None
    min_font_size: int | None = None
    max_font_size: int | None = None
    padding: float | None = None
    atom_label_padding: float | None = None
    annotation_font_scale: float | None = None
    legend_font_size: int | None = None
    monochrome: bool = False
    # Der Bedingungstext über dem Reaktionspfeil kommt NICHT aus RDKit — die
    # Backends overlayen ihn selbst (Pillow bzw. <text>). Ohne diesen Faktor
    # wäre er das einzige Element, das ein Preset nicht mitskaliert.
    conditions_font_scale: float = 1.0


# Die Werte leiten sich aus dem ab, was MolDrawOptions tatsächlich hergibt
# (RDKit 2026.03: bondLineWidth 2.0, padding 0.05, minFontSize 6,
# maxFontSize 40, additionalAtomLabelPadding 0.0, annotationFontScale 0.5,
# legendFontSize 16; das Projekt zeichnet mit bondLineWidth 1.5).
# Bewusst KEINE Marken- oder Journalnamen: die Presets sind nach ihrer Wirkung
# benannt, weil sich keine Zeitschriftenvorgabe hier belegen ließe.
STYLES: dict[str, DrawStyle] = {
    # Kleine Abbildung im Zweispalten-Satz: die Zeichnung wird beim Setzen
    # verkleinert, deshalb dünnere Linien (Strich wirkt sonst fett), gedeckelte
    # Labelgröße (Labels dominieren sonst die Struktur) und knappe Ränder
    # (jeder Millimeter Weißraum kostet Spaltenbreite).
    "compact": DrawStyle(
        bond_line_width=1.2,
        max_font_size=20,
        padding=0.02,
        annotation_font_scale=0.4,
        conditions_font_scale=0.85,
    ),
    # Projektion aus der letzten Reihe: doppelte Strichstärke, Labels mit
    # Mindestgröße statt automatischer Verkleinerung, zusätzlicher Labelabstand
    # (dicke Bindungen laufen sonst in die Glyphen) und mehr Rand.
    "presentation": DrawStyle(
        bond_line_width=3.0,
        min_font_size=12,
        padding=0.08,
        atom_label_padding=0.05,
        annotation_font_scale=0.7,
        legend_font_size=24,
        # >1 muss den größeren Rand mit ausgleichen: der schrumpft die Skala,
        # in der die Textgröße gerechnet wird.
        conditions_font_scale=1.6,
    ),
    # Graustufendruck: aus Rot und Blau werden im S/W-Druck zwei kaum
    # unterscheidbare Grautöne. Nur die Palette wechselt — die Geometrie bleibt
    # der Default, damit "grayscale" keine zweite Entscheidung mittrifft.
    "grayscale": DrawStyle(monochrome=True),
}


def get_style(name: str | None) -> DrawStyle | None:
    """Liefert das Preset zu `name`; `""`/`None` heißt "Default, nichts tun".

    Wirft ValueError bei unbekanntem Namen — früh und mit der Liste der
    gültigen Werte, damit der Aufrufer nicht erst nach dem Dateischreiben
    merkt, dass der Stil nicht existiert.
    """
    key = (name or "").strip().lower()
    if not key or key == "default":
        return None
    try:
        return STYLES[key]
    except KeyError:
        raise ValueError(
            f"Unbekannter render_style: {name!r} — erlaubt sind "
            f"{sorted(STYLES)} oder '' für den Standardstil."
        ) from None


def apply_style(opts, name: str | None) -> None:
    """Setzt die Preset-Werte auf ein MolDrawOptions-Objekt.

    Aufrufer setzen VORHER ihre Basiswerte (u.a. BOND_LINE_WIDTH); dieser
    Aufruf überschreibt sie nur dort, wo das Preset etwas zu sagen hat. So
    bleibt BOND_LINE_WIDTH die gemeinsame Quelle für Export und UI-Vorschau
    (Parität), und das Preset wirkt trotzdem in beiden Pfaden gleich — es wird
    an genau dieser Stelle in beiden angewandt, statt die Konstante zu ändern.
    """
    style = get_style(name)
    if style is None:
        return
    if style.bond_line_width is not None:
        opts.bondLineWidth = style.bond_line_width
    if style.min_font_size is not None:
        opts.minFontSize = style.min_font_size
    if style.max_font_size is not None:
        opts.maxFontSize = style.max_font_size
    if style.padding is not None:
        opts.padding = style.padding
    if style.atom_label_padding is not None:
        opts.additionalAtomLabelPadding = style.atom_label_padding
    if style.annotation_font_scale is not None:
        opts.annotationFontScale = style.annotation_font_scale
    if style.legend_font_size is not None:
        opts.legendFontSize = style.legend_font_size
    if style.monochrome:
        opts.useBWAtomPalette()


# ---------------------------------------------------------------------------
# Gruppen-Kontraktion
# ---------------------------------------------------------------------------

# Format je Zeile: label SMARTS displayLabel displayLabelW (RDKit
# ParseAbbreviations). Das führende `*` ist der Anknüpfungspunkt.
# Nur Kürzel, die RDKits Default-Liste NICHT hat und die in der Praxis
# ständig gebraucht werden — Aryl-/Benzyl-Reste und die gängigen
# Schutzgruppen. Reihenfolge: vor den Defaults, damit das spezifischere
# Kürzel (Boc) vor dem enthaltenen (tBu) geprüft wird.
_EXTRA_ABBREVIATIONS = """
Boc *-C(=O)OC(C)(C)C Boc Boc
Cbz *-C(=O)OCc1ccccc1 Cbz Cbz
Ts *-S(=O)(=O)c1ccc(C)cc1 Ts Ts
Ms *-S(=O)(=O)C Ms Ms
TBS *-[Si](C)(C)C(C)(C)C TBS TBS
TMS *-[Si](C)(C)C TMS TMS
Bn *-Cc1ccccc1 Bn Bn
Ph *-c1ccccc1 Ph Ph
"""

# RDKits Obergrenze dafür, welchen Anteil eines Moleküls EINE Abkürzung
# schlucken darf. 0.4 ist RDKits eigener Default und bleibt es hier: er
# verhindert, dass ein kleines Molekül zu einem einzigen Label kollabiert
# (Boc-Piperazin würde sonst als "Boc-Piperazin-Kürzel" fast verschwinden).
# Preis: bei kleinen Molekülen greift statt Boc nur das enthaltene tBu.
ABBREVIATION_MAX_COVERAGE = 0.4

_ABBREVIATIONS = None


def _abbreviations():
    """Zusatzdefinitionen + RDKit-Defaults, einmalig geparst.

    Lazy, weil ParseAbbreviations acht SMARTS übersetzt — das gehört nicht in
    den Importpfad des MCP-Servers, wenn niemand Abkürzungen anfordert.
    """
    global _ABBREVIATIONS
    if _ABBREVIATIONS is None:
        _ABBREVIATIONS = list(
            rdAbbreviations.ParseAbbreviations(_EXTRA_ABBREVIATIONS)
        ) + list(rdAbbreviations.GetDefaultAbbreviations())
    return _ABBREVIATIONS


def condense_groups(
    mol: Chem.Mol, max_coverage: float = ABBREVIATION_MAX_COVERAGE
) -> Chem.Mol:
    """Ersetzt erkannte Gruppen durch ihr Kürzel — nur fürs ZEICHNEN.

    Das Ergebnis ist bewusst nicht sanitisiert (RDKit-Vertrag) und trägt
    Dummy-Atome mit `atomLabel`. Es taugt zum Rendern, nicht zur Analyse:
    Atomindizes, Summenformel und funktionelle Gruppen müssen weiter am
    vollen Molekül berechnet werden.
    """
    return rdAbbreviations.CondenseMolAbbreviations(
        mol, _abbreviations(), max_coverage
    )
