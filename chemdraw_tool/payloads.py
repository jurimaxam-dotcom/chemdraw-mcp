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
    color: str = "#999999"


class LipinskiData(BaseModel):
    mw: float | None = None
    logP: float | None = None
    hbd: int | None = None
    hba: int | None = None
    passes: bool = False
    violations: int = 0


class MoleculePayload(BaseModel):
    type: str = "molecule"
    svg: str = ""
    atoms: list[AtomData] = []
    name: str = ""
    subtitle: str = ""
    properties: dict[str, str] = {}
    functionalGroups: list[FunctionalGroup] = []
    lipinski: LipinskiData | None = None
    # Geschriebene Dateien: {"png": pfad, "svg": pfad, "cdxml": pfad}.
    # PNG/SVG sind die Primärformate; cdxml nur auf Anforderung (dann ist
    # zusätzlich cdxml_path gesetzt — Kompatibilität für UI + open_chemdraw_file).
    files: dict[str, str] = {}
    cdxml_path: str = ""


class MolEntry(BaseModel):
    svg: str = ""
    name: str = ""


class ReactionPayload(BaseModel):
    type: str = "reaction"
    name: str = ""
    conditions: str = ""
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


class DatabaseSource(BaseModel):
    type: str  # "PubChem" | "GHS"
    source: str
    url: str
    rows: list[DatabaseRow] = []


class DatabasePayload(BaseModel):
    type: str = "database"
    molecule_svg: str = ""
    sources: list[DatabaseSource] = []


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


class Molecule3DPayload(BaseModel):
    """3D conformer for the interactive panel viewer (ball-and-stick)."""

    type: str = "molecule3d"
    name: str
    atoms: list[dict] = []
    bonds: list[dict] = []
    files: dict[str, str] = {}
