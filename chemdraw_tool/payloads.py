"""Pydantic payload models for MCP structured output."""

from __future__ import annotations

from pydantic import BaseModel


class AtomData(BaseModel):
    idx: int
    el: str
    x: float
    y: float
    hCount: int = 0
    charge: int = 0


class FunctionalGroup(BaseModel):
    name: str
    atomIndices: list[int] = []
    # Zahl der Gruppen, nicht der markierten Atome — das Panel zeigt sie
    # neben dem Namen, und dort liest sie jeder als "wie viele davon".
    count: int = 1
    color: str = "#999999"


class StereoWarning(BaseModel):
    """Ein Stereoelement, dessen Konfiguration die Eingabe offen lässt."""

    kind: str  # "atom" | "double_bond"
    # Indizes in `atoms` desselben Payloads. Leer, wenn die Zeichnung die
    # Atome nicht mehr zeigt (abgekürzte Gruppen) — der Hinweis bleibt dann.
    atoms: list[int] = []
    label: str = ""


class LipinskiData(BaseModel):
    mw: float | None = None
    logP: float | None = None
    hbd: int | None = None
    hba: int | None = None
    passes: bool = False
    violations: int = 0


class IsomerCandidate(BaseModel):
    """One structure a family name ("xylene", "Glucose") can mean."""

    label: str
    name: str = ""
    smiles: str
    svg: str = ""


class MoleculePayload(BaseModel):
    type: str = "molecule"
    svg: str = ""
    atoms: list[AtomData] = []
    name: str = ""
    subtitle: str = ""
    properties: dict[str, str] = {}
    functionalGroups: list[FunctionalGroup] = []
    # Unbestimmte Stereozentren/Doppelbindungen; stereoNote ist derselbe
    # Befund als Satz fürs Modell, falls kein Panel angezeigt wird.
    stereoWarnings: list[StereoWarning] = []
    stereoNote: str = ""
    lipinski: LipinskiData | None = None
    # Geschriebene Dateien: {"png": pfad, "svg": pfad, "cdxml": pfad}.
    # PNG/SVG sind die Primärformate; cdxml nur auf Anforderung (dann ist
    # zusätzlich cdxml_path gesetzt — Kompatibilität für UI + open_chemdraw_file).
    files: dict[str, str] = {}
    cdxml_path: str = ""
    # Nur bei type="ambiguous" gefüllt (AmbiguousPayload): der Name meint
    # mehrere Isomere, gezeichnet wurde keins. Die Felder stehen hier und nicht
    # nur in der Unterklasse, damit das outputSchema von generate_molecule sie
    # ehrlich zeigt — die Annotation bleibt MoleculePayload (eine Union würde
    # das SDK in {"result": …} wickeln).
    message: str = ""
    candidates: list[IsomerCandidate] = []


class AmbiguousPayload(MoleculePayload):
    """Auswahl statt Zeichnung: ein Familienname, mehrere Kandidaten.

    Unterklasse, damit generate_molecule weiter `-> MoleculePayload` annotiert
    bleibt; das SDK serialisiert die Instanz samt eigenem `type`.
    """

    type: str = "ambiguous"


class MolEntry(BaseModel):
    svg: str = ""
    name: str = ""


class ReactionPayload(BaseModel):
    type: str = "reaction"
    name: str = ""
    conditions: str = ""
    conditions_below: str = ""
    arrow: str = "forward"
    reactants: list[MolEntry] = []
    products: list[MolEntry] = []
    files: dict[str, str] = {}
    cdxml_path: str = ""


class BatchPayload(BaseModel):
    type: str = "batch"
    molecules: list[MoleculePayload] = []
    cdxml_paths: list[str] = []
    failed: list[str] = []


class SpectrumPeak(BaseModel):
    position: float
    intensity: float = 1.0
    width: float | None = None
    label: str = ""


class SpectrumPayload(BaseModel):
    type: str = "spectrum"
    spectrum_type: str
    name: str = ""
    svg: str = ""
    files: dict[str, str] = {}


class TlcSpot(BaseModel):
    """One spot on a TLC lane. rf is the ratio substance/front (0…1)."""

    rf: float
    label: str = ""
    # 1.0 = strong spot, ~0.3 = faint — only affects how solid it is drawn.
    intensity: float = 1.0


class TlcLane(BaseModel):
    """One application point on the plate, e.g. "Edukt" or "Co-Spot"."""

    name: str
    spots: list[TlcSpot] = []


class TlcPayload(BaseModel):
    type: str = "tlc"
    name: str = ""
    solvent: str = ""
    detection: str = ""
    lanes: list[TlcLane] = []
    svg: str = ""
    files: dict[str, str] = {}


class ScopeEntry(BaseModel):
    """One product in a substrate-scope figure (the grid's cells)."""

    structure: str
    # Identifier printed under the structure, e.g. "1a". Left empty the tool
    # numbers the entries itself (1a, 1b, 1c …), as papers do.
    label: str = ""
    # Yield as printed: "78%", "78" (a % is added) or free text ("quant.").
    yield_text: str = ""
    # Anything extra the figure carries: "ee 94%", "dr 10:1", "12 h, 60 °C".
    notes: str = ""


class ScopePayload(BaseModel):
    type: str = "scope"
    name: str = ""
    conditions: str = ""
    columns: int = 0
    entries: list[ScopeEntry] = []
    # Entries (or header components) that could not be resolved — the figure
    # is drawn from the rest, like batch_generate does.
    failed: list[str] = []
    svg: str = ""
    files: dict[str, str] = {}


class DatabaseRow(BaseModel):
    key: str
    val: str


class GhsHazard(BaseModel):
    code: str  # "H302", "H300+H310"
    text: str = ""
    # Nur ECHA-Aggregate nennen einen Anteil; None heisst "nicht angegeben",
    # nie 0 %.
    percent: float | None = None


class GhsNotClassified(BaseModel):
    """Eine Quelle meldet ausdruecklich "erfuellt die GHS-Kriterien nicht"."""

    percent: float | None = None
    reports: int | None = None
    total: int | None = None


class GhsGroup(BaseModel):
    """Die Einstufung EINER Quelle (PubChem ReferenceNumber)."""

    id: str  # stabil: "ghs-<ReferenceNumber>"
    source: str  # lesbarer Quellenname
    record_name: str = ""
    url: str = ""
    lead: bool = False
    note: str = ""  # z. B. "record name differs: …"
    signal: str = ""
    hazards: list[GhsHazard] = []
    pictograms: list[str] = []
    p_codes: list[str] = []
    not_classified: GhsNotClassified | None = None
    reports_total: int | None = None


class DatabaseSource(BaseModel):
    type: str  # "PubChem" | "GHS" — zugleich der Reiter im Panel, je Typ einer
    source: str
    url: str
    rows: list[DatabaseRow] = []
    # GHS: eine Gruppe je Quelle, Leitquelle zuerst. Leer + `note`, wenn PubChem
    # nichts hat oder der Abruf scheiterte (status "empty" / "error").
    groups: list[GhsGroup] = []
    status: str = ""
    note: str = ""


class DatabasePayload(BaseModel):
    type: str = "database"
    molecule_svg: str = ""
    sources: list[DatabaseSource] = []
    # Dieselben Strukturdaten wie im MoleculePayload — damit das Panel zwischen
    # Datenblatt und Struktur umschalten kann, ohne dafuer nachzuladen. RDKit
    # rechnet beides lokal in Millisekunden; teuer ist nur das Netz, und das
    # steckt in `sources`, die ohnehin schon geholt wurden.
    atoms: list[AtomData] = []
    functionalGroups: list[FunctionalGroup] = []
    stereoWarnings: list[StereoWarning] = []
    stereoNote: str = ""
    name: str = ""
    smiles: str = ""


class MechanismStepPayload(BaseModel):
    svg: str
    label: str
    is_transition_state: bool = False


class MechanismPayload(BaseModel):
    type: str = "mechanism"
    name: str
    reaction_type: str
    steps: list[MechanismStepPayload]
    current_step: int = 0


class ReactionSpec(BaseModel):
    """Reaction visual on an Anki card side (names or SMILES)."""

    reactants: list[str]
    products: list[str]
    conditions: str = ""


class SpectrumSpec(BaseModel):
    """Spectrum visual on an Anki card side."""

    spectrum_type: str
    peaks: list[SpectrumPeak]
    title: str = ""


class CardSide(BaseModel):
    """One side of an Anki card: text plus at most one rendered visual."""

    text: str = ""
    structure: str = ""  # compound name or SMILES
    reaction: ReactionSpec | None = None
    spectrum: SpectrumSpec | None = None


class AnkiCard(BaseModel):
    front: CardSide
    back: CardSide
    tags: list[str] = []
    # Basic-and-Reversed: EINE Notiz erzeugt BEIDE Richtungen (Front→Back
    # und Back→Front). Schließt cloze aus.
    reversed: bool = False
    # Cloze/Lückentext: front.text trägt die {{c1::...}}-Lücken, back.text
    # wird Ankis "Back Extra"-Feld. Schließt reversed aus.
    cloze: bool = False


class AnkiDeckPayload(BaseModel):
    type: str = "anki_deck"
    delivery: str = "apkg"
    name: str
    cards: int
    media: int
    fronts: list[str] = []
    file: str = ""


class PlotPayload(BaseModel):
    """Generic rendered diagram (titration curve, species distribution, …)."""

    type: str = "plot"
    name: str
    subtitle: str = ""
    svg: str = ""
    files: dict[str, str] = {}
    # Zahlen und Warnungen, die zum Diagramm gehören und nicht in den Untertitel
    # passen — etwa die zurückgerechneten Proben einer Kalibriergeraden. Leer
    # bei allen älteren Plots, deshalb rückwärtskompatibel.
    notes: list[str] = []


class Molecule3DPayload(BaseModel):
    """3D conformer for the interactive panel viewer (ball-and-stick)."""

    type: str = "molecule3d"
    name: str
    atoms: list[dict] = []
    bonds: list[dict] = []
    files: dict[str, str] = {}
