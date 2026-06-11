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


class CalculationStep(BaseModel):
    label: str
    formula: str
    substitution: str
    result: str
    explanation: str = ""
    is_outlier: bool = False


class MethodResult(BaseModel):
    name: str
    gehalt_steps: list[CalculationStep]
    mean: float
    std_abs: float
    std_rel: float
    variance: float
    recovery: float
    rel_deviation: float
    t_test_value: float
    t_test_critical: float
    t_test_passed: bool
    t_test_explanation: str = ""


class MethodComparison(BaseModel):
    f_test_value: float
    f_test_critical: float
    f_test_passed: bool
    f_test_explanation: str = ""
    t_test_value: float
    t_test_critical: float
    t_test_passed: bool
    t_test_explanation: str = ""
    result_text: str


class ValidationPayload(BaseModel):
    type: str = "validation"
    variante: str
    substance: str
    wahrer_wert: float
    method_a: MethodResult
    method_b: MethodResult
    comparison: MethodComparison
    summary: str = ""


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


class AnkiDeckPayload(BaseModel):
    type: str = "anki_deck"
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
