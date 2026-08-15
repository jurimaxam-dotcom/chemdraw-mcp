import re
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP

from chemdraw_tool.cdxml_writer import write_cdxml
from chemdraw_tool.databases import (
    _get_cid,
    chebi_lookup,
    kegg_compound,
    kegg_find,
    pubchem_physical_properties,
    pubchem_properties,
    pubchem_properties_by_smiles,
    pubchem_safety,
    pubchem_synonyms,
    pubchem_synonyms_by_smiles,
    uniprot_search,
)
from chemdraw_tool.generator import generate_2d
from chemdraw_tool.image_export import (
    render_molecule_png,
    render_molecule_svg,
    render_reaction_png,
    render_reaction_svg,
    write_files,
)
from chemdraw_tool.layout import write_reaction_cdxml
from chemdraw_tool.payloads import (
    AnkiCard,
    AnkiDeckPayload,
    BatchPayload,
    DatabasePayload,
    DatabaseRow,
    DatabaseSource,
    FunctionalGroup,
    LipinskiData,
    MechanismPayload,
    MechanismStepPayload,
    Molecule3DPayload,
    MoleculePayload,
    PlotPayload,
    ReactionPayload,
    ReactionSpec,
    ScopeEntry,
    ScopePayload,
    SpectrumPayload,
    SpectrumPeak,
    TlcLane,
    TlcPayload,
)
from chemdraw_tool.render_style import condense_groups, get_style
from chemdraw_tool.resolver import resolve
from chemdraw_tool.spectrum import (
    SPECTRUM_TYPES,
    render_spectrum_png,
    render_spectrum_svg,
)
from chemdraw_tool.tlc import render_tlc_png, render_tlc_svg
from chemdraw_tool.validator import Severity, validate_input, validate_roundtrip
from chemdraw_tool.vault import is_enabled as vault_enabled
from chemdraw_tool.vault import list_entries, read_entry, search

OUTPUT_DIR = Path.home() / "ChemDraw-Output" / "einzelmolekuele"
REACTION_DIR = Path.home() / "ChemDraw-Output"
SPECTRUM_DIR = Path.home() / "ChemDraw-Output" / "spektren"
TLC_DIR = Path.home() / "ChemDraw-Output" / "dc-platten"
SCOPE_DIR = Path.home() / "ChemDraw-Output" / "scope"
ANKI_DIR = Path.home() / "ChemDraw-Output" / "anki"
PLOT_DIR = Path.home() / "ChemDraw-Output" / "diagramme"
THREED_DIR = Path.home() / "ChemDraw-Output" / "3d"

# PNG/SVG sind die Primärformate (laufen ohne ChemDraw); CDXML ist das
# optionale Zusatzformat für Nutzer, die in ChemDraw weiterbearbeiten wollen.
VALID_FORMATS = ("png", "svg", "cdxml")
DEFAULT_FORMATS = ("png", "svg")

# Die Themen des gebündelten `lookup`. Als Literal, damit schon das
# Tool-Schema die Auswahl eingrenzt — Prosa im Docstring täte das nicht.
LookupTopic = Literal["properties", "safety", "physical", "biochem", "pathway"]

# Die Rechenarten von `calculate_solution` — dieselbe Begründung.
SolutionTopic = Literal[
    "weigh_in", "concentration", "dilution", "mixing", "molar_mass"
]

# Bestimmungsmethoden von `calculate_content`. Die Fettkennzahlen und Karl
# Fischer sind Methoden desselben Tools, weil Eingabeform (Einwaage + Ablesung
# + Blindwert) und Ausgabe (Wert + Streuung) dieselben sind — ein eigenes Tool
# pro Kennzahl wäre ein Kandidat mehr bei jeder Anfrage, ohne Mehrwert.
ContentMethod = Literal[
    "titration",
    "photometry",
    "acid_value",
    "saponification_value",
    "iodine_value",
    "water_kf",
]

# Rückgabewerte-Einheit je Methode, für Überschrift und Statistikblock.
_CONTENT_UNITS = {
    "titration": "%",
    "photometry": "%",
    "acid_value": "mg KOH/g",
    "saponification_value": "mg KOH/g",
    "iodine_value": "g I₂/100 g",
    "water_kf": "% (m/m)",
}

# Rücktitrationen: Der Blindwert ist hier die Bezugsablesung, nicht ein Abzug.
_BACK_TITRATION_METHODS = ("saponification_value", "iodine_value")

# Die Fragen von `predict_spectrum`.
SpectroTopic = Literal["ir_bands", "assign_wavenumber", "nmr_signals"]

# Die Fälle von `calculate_ph`.
PhTopic = Literal[
    "weak_acid", "weak_base", "strong_acid", "strong_base", "buffer", "buffer_recipe"
]


def _normalize_formats(formats: list[str] | None) -> list[str]:
    fmts = [f.lower().strip() for f in (formats or DEFAULT_FORMATS)]
    unknown = sorted(set(fmts) - set(VALID_FORMATS))
    if unknown:
        raise ValueError(
            f"Unbekannte Formate: {unknown} — erlaubt sind {list(VALID_FORMATS)}"
        )
    return fmts


def _write_structure_files(
    mol,
    slug: str,
    display_name: str,
    formats: list[str],
    annotate_stereo: bool = False,
    render_mol=None,
    style: str = "",
) -> tuple[dict[str, str], str]:
    """Schreibt die angeforderten Dateiformate für ein Einzelmolekül.

    Returns ({format: pfad}, cdxml_path) — cdxml_path ist "" wenn kein CDXML
    angefordert wurde. Die CDXML-Roundtrip-Validierung läuft nur, wenn CDXML
    tatsächlich erzeugt wird.

    render_mol: Molekül für die Bilddateien (z.B. die abgekürzte Variante);
    None = `mol`. CDXML entsteht IMMER aus `mol`: die Datei geht zum
    Weiterbearbeiten nach ChemDraw und soll dort die volle Struktur zeigen,
    keine Dummy-Atome mit Textlabel.
    """
    import logging

    drawn = mol if render_mol is None else render_mol

    artifacts: dict[str, bytes | str] = {}
    if "png" in formats:
        artifacts["png"] = render_molecule_png(
            drawn, legend=display_name, annotate_stereo=annotate_stereo, style=style
        )
    if "svg" in formats:
        artifacts["svg"] = render_molecule_svg(
            drawn, legend=display_name, annotate_stereo=annotate_stereo, style=style
        )
    files = write_files(OUTPUT_DIR / slug, artifacts)

    cdxml_path = ""
    if "cdxml" in formats:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filepath = OUTPUT_DIR / f"{slug}.cdxml"
        cdxml_content = write_cdxml(mol, str(filepath), name=display_name)
        rt_report = validate_roundtrip(mol, cdxml_content)
        if not rt_report.valid:
            for issue in rt_report.issues:
                logging.getLogger(__name__).warning(
                    "CDXML validation [%s]: %s", issue.check, issue.message
                )
        cdxml_path = str(filepath)
        files["cdxml"] = cdxml_path
    return files, cdxml_path


# Die Bereichskarte gehoert EINMAL hierher statt zwanzigmal in die einzelnen
# Beschreibungen: `instructions` ist laut MCP-Spec ein „hint to the model", den
# Clients in den Systemprompt uebernehmen duerfen. Wichtigstes zuerst — Claude
# Code kappt das Feld bei 2 KB und schneidet hinten ab.
_INSTRUCTIONS = """\
Chemistry drawings, lab graphics and bench maths, rendered offline.

A bare compound name with no further request ("caffeine") means: draw it —
generate_molecule. Only reach for a look-up tool when a named value is asked
for. Tools fall into five areas:

- Draw — structures and reactions: generate_molecule (one substance, the
  default), batch_generate, compare_molecules, generate_reaction,
  generate_mechanism, generate_scope_table, generate_3d.
- Lab graphic — measured data as a figure: generate_spectrum, generate_tlc,
  generate_titration_curve, generate_species_distribution,
  generate_calibration_curve.
- Look up — a named fact about a substance: lookup (text),
  lookup_molecule_data (data sheet panel), predict_spectrum (from structure).
- Calculate — a number and the working behind it: calculate_solution,
  calculate_content, calculate_ph.
- Anki — flashcard decks: export_anki_deck.

Do not use these tools for: naming or explaining chemistry in prose, choosing
a synthesis route, or literature search. Pass English or IUPAC compound names,
never localized ones ('Aspirin', not 'Acetylsalicylsäure'); SMILES are always
safe. Every drawing tool writes files itself — never call save_png, that is
the panel's own export button.
"""

mcp = FastMCP("ChemDraw Tool", instructions=_INSTRUCTIONS)
# FastMCP nimmt keine Version entgegen, der Low-Level-Server trägt sie aber in
# serverInfo — und genau das zeigt jeder Host an. Ohne diese Zeile meldet sich
# der Server mit der SDK-Version (gemessen: "1.27.1"), und der Nutzer kann nicht
# erkennen, welche chemdraw-mcp-Version bei ihm läuft.
mcp._mcp_server.version = _pkg_version("chemdraw-mcp")

# ---------------------------------------------------------------------------
# UI resource — serves the built MCP App HTML to the client iframe
# ---------------------------------------------------------------------------
_UI_DIST = Path(__file__).parent / "ui" / "dist" / "index.html"
_RESOURCE_URI = "ui://chem-app/index.html"


_UI_META = {"ui": {"resourceUri": _RESOURCE_URI}}


@mcp.resource(
    _RESOURCE_URI,
    mime_type="text/html;profile=mcp-app",
    meta={"ui": {"permissions": {"clipboardWrite": {}}}},
)
def chem_app_ui() -> str:
    """Serve the MCP App UI (single-page React app)."""
    return _UI_DIST.read_text(encoding="utf-8")


def _enrich_properties(smiles: str) -> dict[str, str]:
    """Build properties dict from PubChem using canonical SMILES.

    SMILES-based lookup is deterministic and language-independent —
    works for German names, raw SMILES input, or any other input
    as long as resolve() returned a valid canonical SMILES.
    """
    props_raw = pubchem_properties_by_smiles(smiles) or {}
    cas, _ = pubchem_synonyms_by_smiles(smiles)

    properties: dict[str, str] = {}
    if v := props_raw.get("MolecularFormula"):
        properties["formula"] = v
    if v := props_raw.get("MolecularWeight"):
        properties["mw"] = f"{v} g/mol"
    if v := props_raw.get("XLogP"):
        properties["logP"] = str(v)
    if v := props_raw.get("TPSA"):
        properties["tpsa"] = f"{v} Å²"
    if v := props_raw.get("HBondDonorCount"):
        properties["hbd"] = str(v)
    if v := props_raw.get("HBondAcceptorCount"):
        properties["hba"] = str(v)
    if v := props_raw.get("CanonicalSMILES"):
        properties["smiles"] = v
    if cas:
        properties["cas"] = cas
    return properties


def _build_lipinski(props: dict[str, str]) -> LipinskiData | None:
    """Build Lipinski Rule of 5 data from enriched properties."""
    try:
        mw = float(props["mw"].replace(" g/mol", "")) if "mw" in props else None
        logP = float(props["logP"]) if "logP" in props else None
        hbd = int(props["hbd"]) if "hbd" in props else None
        hba = int(props["hba"]) if "hba" in props else None
    except (ValueError, TypeError):
        return None

    if all(v is None for v in (mw, logP, hbd, hba)):
        return None

    violations = 0
    if mw is not None and mw > 500:
        violations += 1
    if logP is not None and logP > 5:
        violations += 1
    if hbd is not None and hbd > 5:
        violations += 1
    if hba is not None and hba > 10:
        violations += 1

    return LipinskiData(
        mw=mw,
        logP=logP,
        hbd=hbd,
        hba=hba,
        passes=violations == 0,
        violations=violations,
    )


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text or "molecule"


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_molecule(
    name_or_smiles: str,
    label: str = "",
    formats: list[str] | None = None,
    annotate_stereo: bool = False,
    abbreviate_groups: bool = False,
    render_style: str = "",
) -> MoleculePayload:
    """Draw one compound as a 2D structure — the default for a single substance.

    Writes print-ready PNG/SVG to the output folder and returns a panel with
    the drawing, properties and functional groups. No ChemDraw needed.

    Use this tool when the request names structural formulas, molecular
    structures or chemical drawings — "draw aspirin", "structure of caffeine".
    A bare compound name with no further request ("caffeine", "aspirin")
    also means this tool: show the substance, and the panel carries its data.

    Not this tool for: several products of one reaction with yields (use
    generate_scope_table); several unrelated structures at once (use
    batch_generate); differences between structures (use compare_molecules);
    an equation with an arrow (use generate_reaction); a named single value
    such as melting point, CAS number or GHS hazards (use lookup).

    IMPORTANT: Always pass English or IUPAC compound names, never localized
    names — 'Aspirin' not 'Acetylsalicylsäure', 'Caffeine' not 'Coffein'.
    SMILES are always safe; use `label` for the localized display name.

    Args:
        name_or_smiles: English/IUPAC compound name or SMILES string.
        label: Display name shown below the structure (may be localized).
        formats: Any of "png", "svg", "cdxml" (default: png + svg). Add
            "cdxml" only when the structure is to be edited in ChemDraw.
        annotate_stereo: True prints CIP descriptors (R/S, E/Z) at each
            stereocenter.
        abbreviate_groups: True draws common substituents as the short labels
            chemists write by hand (Ph, Bn, OAc, OMe, CO2H, NO2, tBu, Boc, Ts,
            TMS). The chemistry is unchanged; hover tooltips in the panel are
            switched off for abbreviated drawings.
        render_style: "" standard · "compact" thin bonds for small print ·
            "presentation" thick bonds for slides · "grayscale" b/w palette.
    """
    from chemdraw_tool.svg_renderer import (
        extract_atom_data,
        extract_functional_groups,
        render_svg,
    )

    fmts = _normalize_formats(formats)
    get_style(render_style)  # unbekannter Stil: scheitern, bevor Dateien entstehen

    smiles, mol = resolve(name_or_smiles)
    mol = generate_2d(mol)

    input_issues = validate_input(mol)
    for issue in input_issues:
        if issue.severity == Severity.ERROR:
            raise ValueError(f"Input validation failed: {issue.message}")

    display_name = label or name_or_smiles
    slug = _slugify(display_name)
    # Abgekürzt wird nur die Zeichnung. Analyse (funktionelle Gruppen,
    # Properties, Validierung) und CDXML laufen weiter am vollen Molekül.
    drawn = condense_groups(mol) if abbreviate_groups else mol

    files, cdxml_path = _write_structure_files(
        mol,
        slug,
        display_name,
        fmts,
        annotate_stereo=annotate_stereo,
        render_mol=drawn,
        style=render_style,
    )

    properties = _enrich_properties(smiles)
    fg_raw = extract_functional_groups(mol)
    groups = [FunctionalGroup(**g) for g in fg_raw]
    lipinski = _build_lipinski(properties)

    return MoleculePayload(
        type="molecule",
        svg=render_svg(
            drawn,
            fill_container=True,
            annotate_stereo=annotate_stereo,
            style=render_style,
        ),
        # Die Atomliste positioniert Tooltip und Gruppen-Highlight über dem SVG.
        # Nach dem Abkürzen zeigt das SVG andere Atome als das analysierte
        # Molekül — falsch platzierte Overlays wären schlimmer als keine.
        atoms=[] if abbreviate_groups else extract_atom_data(mol),
        name=display_name,
        properties=properties,
        functionalGroups=groups,
        lipinski=lipinski,
        files=files,
        cdxml_path=cdxml_path,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_spectrum(
    spectrum_type: str,
    peaks: list[SpectrumPeak],
    title: str = "",
    formats: list[str] | None = None,
) -> SpectrumPayload:
    """Draw a schematic spectrum from a peak list as print-ready PNG/SVG files.

    Use this tool whenever the user asks for a spectrum drawing of any kind:
    IR, NIR, Raman, UV/Vis, fluorescence, ORD, CD, 1H/13C NMR or mass
    spectrum (MS). If the user only names a compound without peak values,
    supply typical literature peak positions yourself (e.g. aspirin IR:
    C=O stretch ~1750 cm⁻¹, broad O-H ~2500-3300 cm⁻¹) — the tool then
    draws exactly the peaks it is given; it does not predict spectra.

    Not this tool for: working out WHICH bands to expect, or what a measured
    wavenumber belongs to — that is predict_spectrum, whose band list can
    then be handed to this tool for the drawing.

    Axis conventions are handled automatically (IR: inverted wavenumber
    axis with transmission dips; NMR: ppm axis right-to-left; MS: bar plot;
    ORD: Cotton-effect curve; CD: signed bands around zero).

    Args:
        spectrum_type: One of "ir", "nir", "raman", "uv_vis", "fluorescence",
            "ord", "cd", "nmr_1h", "nmr_13c", "ms".
        peaks: Peak list. position uses the type's natural unit (cm⁻¹ for
            ir/nir/raman, nm for uv_vis/fluorescence/ord/cd, ppm for NMR,
            m/z for ms). intensity is relative on any scale (negative values
            only for ord/cd). width (optional) is the half-width in x-units;
            label (optional) annotates the peak in the plot (e.g. "C=O").
        title: Display name shown in the plot title, also used for the
            filename (can be localized, e.g. "Aspirin IR").
        formats: Output file formats, any of "png", "svg" (default: both).
            CDXML is not available for spectra.
    """
    fmts = _normalize_formats(formats)
    if "cdxml" in fmts:
        raise ValueError(
            "Spektren unterstützen nur png/svg — CDXML ist ein Strukturformat"
        )

    cfg = SPECTRUM_TYPES.get(spectrum_type)
    if cfg is None:
        raise ValueError(
            f"Unbekannter Spektrentyp {spectrum_type!r} — "
            f"erlaubt sind {sorted(SPECTRUM_TYPES)}"
        )

    peak_dicts = [SpectrumPeak.model_validate(p).model_dump() for p in peaks]

    artifacts: dict[str, bytes | str] = {}
    if "png" in fmts:
        artifacts["png"] = render_spectrum_png(spectrum_type, peak_dicts, title=title)
    if "svg" in fmts:
        artifacts["svg"] = render_spectrum_svg(spectrum_type, peak_dicts, title=title)
    slug = _slugify(title or cfg.title)
    files = write_files(SPECTRUM_DIR / slug, artifacts)

    svg_preview = artifacts.get("svg") or render_spectrum_svg(
        spectrum_type, peak_dicts, title=title
    )

    return SpectrumPayload(
        spectrum_type=spectrum_type,
        name=title,
        svg=svg_preview,
        files=files,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_tlc(
    lanes: list[TlcLane],
    title: str = "",
    solvent: str = "",
    detection: str = "",
    formats: list[str] | None = None,
) -> TlcPayload:
    """Draw a TLC plate sketch from Rf values as print-ready PNG/SVG files.

    Use this whenever the user reports a thin-layer chromatography result
    ("TLC of my esterification: educt at 0.3, product at 0.65, the co-spot
    shows both") or asks for the plate sketch a lab report requires. The
    tool draws exactly the Rf values it is given — it predicts nothing.

    The plate is read from the bottom: start line at Rf 0, solvent front at
    Rf 1, so a spot at Rf 0.8 sits near the top. One lane = one application
    point with its own caption; a lane can carry several spots, so a co-spot
    lane showing educt AND product is simply two spots on one lane. Every
    spot is annotated with its Rf value so the sketch can be read off.

    Args:
        lanes: The lanes from left to right, e.g.
            [{"name": "Edukt", "spots": [{"rf": 0.30, "label": "Säure"}]},
             {"name": "Reaktion", "spots": [{"rf": 0.65, "label": "Ester"}]},
             {"name": "Co-Spot", "spots": [{"rf": 0.30}, {"rf": 0.65}]}]
            rf must lie between 0 and 1 — it is a ratio (distance travelled
            by the substance / distance travelled by the front), so values
            outside that range are rejected instead of silently clipped.
            label (optional) names the substance at that spot; intensity
            (optional, 0…1, default 1) draws a faint spot fainter.
        title: Shown in the plot title and used for the filename, e.g.
            "Veresterung Ansatz 2" (free text, can be localized).
        solvent: Mobile phase / eluent as it goes into the report, e.g.
            "Toluol/Ethylacetat 8:2" — printed as a caption on the sketch.
        detection: How the spots were visualized, e.g. "UV 254 nm", "Iod",
            "Ninhydrin" — printed next to the mobile phase.
        formats: Output file formats, any of "png", "svg" (default: both).
            CDXML is not available for plates.
    """
    fmts = _normalize_formats(formats)
    if "cdxml" in fmts:
        raise ValueError(
            "DC-Platten unterstützen nur png/svg — CDXML ist ein Strukturformat"
        )

    lane_models = [TlcLane.model_validate(lane) for lane in lanes]
    lane_dicts = [lane.model_dump() for lane in lane_models]

    # Rf-/Intensitätsprüfung passiert in tlc.build_plate — der Fehler kommt
    # damit aus einer Quelle, egal ob Datei oder Vorschau gerendert wird.
    artifacts: dict[str, bytes | str] = {}
    if "png" in fmts:
        artifacts["png"] = render_tlc_png(
            lane_dicts, title=title, solvent=solvent, detection=detection
        )
    if "svg" in fmts:
        artifacts["svg"] = render_tlc_svg(
            lane_dicts, title=title, solvent=solvent, detection=detection
        )
    slug = _slugify(title or "TLC plate")
    files = write_files(TLC_DIR / slug, artifacts)

    svg_preview = artifacts.get("svg") or render_tlc_svg(
        lane_dicts, title=title, solvent=solvent, detection=detection
    )

    return TlcPayload(
        name=title,
        solvent=solvent,
        detection=detection,
        lanes=lane_models,
        svg=svg_preview,
        files=files,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_scope_table(
    entries: list[ScopeEntry],
    title: str = "",
    reaction: ReactionSpec | None = None,
    columns: int = 0,
    formats: list[str] | None = None,
    abbreviate_groups: bool = False,
    render_style: str = "",
) -> ScopePayload:
    """Draw a substrate-scope figure: one reaction, many products in a grid.

    The standard figure of the methodology literature: the general equation
    with its conditions on top, below it a grid of product structures, each
    with its identifier ("1a") and yield ("78%"), often with extra data (ee,
    dr, time). Use it when several products of the SAME reaction are shown
    side by side — "the scope of my Suzuki couplings", "these five products
    with yields", a table of derivatives.

    Not this tool for: ONE single molecule — that is generate_molecule, even
    when a title or caption is wanted; with one entry this is the wrong
    figure. Nor for a single equation (use generate_reaction) or unrelated
    structures as separate files (use batch_generate).

    All structures share one bond length and every cell is the same size. An
    entry that cannot be resolved is skipped and reported in `failed`.

    IMPORTANT: Always pass English or IUPAC compound names, never localized
    names ('Aspirin' not 'Acetylsalicylsäure'). SMILES are always safe.

    Args:
        entries: Products in reading order, each {"structure": name or SMILES,
            "label": "1a", "yield_text": "78%", "notes": "ee 94%"}. Without
            label the entries are numbered 1a, 1b, 1c … as in a paper.
            yield_text takes free text ("quant."); a bare number gets its %.
        title: Heading above the figure (free text, may be localized).
        reaction: Optional general equation above the grid: {"reactants":
            [...], "products": [...], "conditions": "..."} — ONE
            representative example, conditions on their own line.
        columns: Grid columns (1-6); 0 derives it from the entry count.
        formats: "png" and/or "svg" (default both). No CDXML for figures.
        abbreviate_groups: True draws short substituent labels (Ph, OAc,
            tBu …) — recommended here, the cells are small.
        render_style: "" standard · "compact" for small print · "presentation"
            for slides · "grayscale" for b/w.
    """
    import logging

    from chemdraw_tool.scope import (
        ReactionHeader,
        ScopeItem,
        auto_label,
        build_grid,
        format_yield,
        render_scope_png,
        render_scope_svg,
    )

    fmts = _normalize_formats(formats)
    if "cdxml" in fmts:
        raise ValueError(
            "Scope-Figuren unterstützen nur png/svg — CDXML ist ein "
            "Strukturformat für einzelne Moleküle, keine Abbildung"
        )
    get_style(render_style)  # unbekannter Stil: scheitern, bevor Dateien entstehen

    log = logging.getLogger(__name__)
    failed: list[str] = []

    def _drawable(text: str):
        """Auflösen → 2D → (optional) Gruppen kontrahieren, wie generate_molecule."""
        _, mol = resolve(text)
        mol = generate_2d(mol)
        if any(i.severity == Severity.ERROR for i in validate_input(mol)):
            raise ValueError(f"Input validation failed for {text!r}")
        return condense_groups(mol) if abbreviate_groups else mol

    items: list = []
    echo: list[ScopeEntry] = []
    for entry in (ScopeEntry.model_validate(e) for e in entries):
        try:
            mol = _drawable(entry.structure)
        except Exception:
            # Wie batch_generate: der einzelne Ausfall wird gemeldet, nicht
            # geworfen — sonst kostet ein Tippfehler die ganze Figur.
            log.warning("Scope entry %r could not be drawn, skipping", entry.structure)
            failed.append(entry.structure)
            continue
        label = entry.label.strip() or auto_label(len(items))
        items.append(
            ScopeItem(
                mol=mol,
                label=label,
                yield_text=entry.yield_text,
                notes=entry.notes,
            )
        )
        echo.append(
            ScopeEntry(
                structure=entry.structure,
                label=label,
                yield_text=format_yield(entry.yield_text),
                notes=entry.notes,
            )
        )

    if not items:
        raise ValueError(
            "Kein einziger Eintrag ließ sich zeichnen — ohne Struktur gibt es "
            f"keine Figur. Nicht auflösbar: {failed}"
        )

    header = None
    conditions = ""
    if reaction is not None:
        spec = ReactionSpec.model_validate(reaction)
        sides: list[list] = [[], []]
        broken: list[str] = []
        for target, names in zip(sides, (spec.reactants, spec.products), strict=True):
            for name in names:
                try:
                    target.append(_drawable(name))
                except Exception:
                    broken.append(name)
        if broken or not sides[0] or not sides[1]:
            # Eine Gleichung mit fehlender Komponente wäre fachlich falsch —
            # dann lieber nur das Raster, mit Meldung.
            log.warning("Scope header incomplete (%s), drawing grid only", broken)
            failed.extend(broken)
        else:
            header = ReactionHeader(sides[0], sides[1], spec.conditions)
            conditions = spec.conditions

    figure = dict(columns=columns, title=title, header=header, style=render_style)
    artifacts: dict[str, bytes | str] = {}
    if "png" in fmts:
        artifacts["png"] = render_scope_png(items, **figure)
    if "svg" in fmts:
        artifacts["svg"] = render_scope_svg(items, **figure)
    slug = _slugify(title or "substrate-scope")
    files = write_files(SCOPE_DIR / slug, artifacts)

    svg_preview = artifacts.get("svg") or render_scope_svg(items, **figure)

    return ScopePayload(
        name=title,
        conditions=conditions,
        columns=build_grid(len(items), columns).columns,
        entries=echo,
        failed=failed,
        svg=svg_preview,
        files=files,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def export_anki_deck(
    deck_name: str = "",
    cards: list[AnkiCard] | None = None,
    default_tags: list[str] | None = None,
    deliver: str = "apkg",
    curated_deck_id: str = "",
) -> AnkiDeckPayload:
    """Export an Anki flashcard deck (.apkg) with rendered chemistry images.

    Use this whenever the user wants flashcards, Anki cards or a study deck
    for molecules, reactions (e.g. pharmacopoeia identity tests) or spectra.

    Two ways to fill the deck. Either pass `cards` you wrote yourself, or
    pass `curated_deck_id` for a ready-made, formula-verified starter deck:

    - "analgesics-structures": structure → name drills for 8 classic
      analgesics (NSAIDs, paracetamol, morphine, celecoxib).
    - "pheur-identity-basics": classic Ph.Eur. identity tests — reagent,
      observation and reaction scheme where it helps.

    The tool renders the images — YOU supply the card content from your
    knowledge, as with generate_spectrum. Each card side carries text plus at
    most ONE visual: structure (name or SMILES), reaction ({reactants,
    products, conditions}) or spectrum ({spectrum_type, peaks, title}).
    Proven types: structure↔name, identity reactions (question front, scheme
    back), functional-group recognition, band assignment, name drills.

    Re-exporting under the SAME deck name updates existing cards instead of
    duplicating them — the card front identifies the card.

    Card options: reversed=true drills both directions (one note, two cards);
    cloze=true makes fill-in-the-blank cards (front.text carries {{c1::...}},
    back.text becomes the extra note). "Parent::Child" nests subdecks.

    IMPORTANT: structures take English/IUPAC names or SMILES; card TEXTS may
    be localized freely. Never deliver via AnkiConnect unless asked.

    Args:
        deck_name: Deck name, also the filename; re-use it to update a deck.
            Ignored when curated_deck_id is set.
        cards: The flashcards. Fronts unambiguous, explanations on the back.
        default_tags: Tags added to every card.
        deliver: "apkg" (file only) or "ankiconnect" (also imports into the
            RUNNING Anki via the AnkiConnect add-on).
        curated_deck_id: "analgesics-structures" or "pheur-identity-basics".
    """
    if curated_deck_id:
        from chemdraw_tool.curated_decks import get_curated_deck

        deck_name, card_models = get_curated_deck(curated_deck_id)
    else:
        if not cards:
            raise ValueError("Das Deck braucht mindestens eine Karte.")
        if not deck_name:
            raise ValueError("Das Deck braucht einen Namen.")
        card_models = [AnkiCard.model_validate(c) for c in cards]
    out_path = ANKI_DIR / f"{_slugify(deck_name)}.apkg"

    import chemdraw_tool.anki_export as _anki

    stats = _anki.write_deck(deck_name, card_models, out_path, default_tags)
    delivery = "apkg"
    if deliver == "ankiconnect":
        delivery = _anki.push_via_ankiconnect(out_path)
    return AnkiDeckPayload(
        name=deck_name,
        cards=stats["cards"],
        media=stats["media"],
        fronts=[c.front.text or c.front.structure for c in card_models],
        file=str(out_path),
        delivery=delivery,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_titration_curve(
    substance: str,
    pka_values: list[float],
    c_acid: float,
    v_acid_ml: float,
    c_titrant: float,
    indicator: dict | None = None,
) -> PlotPayload:
    """Draw a titration curve: weak (or polyprotic) acid vs. strong base.

    Computes pH against titrant volume from the exact charge balance and
    marks equivalence points (per protolysis step), the buffer points
    (pH = pKa at half-equivalence) and optionally the indicator transition
    range as a shaded band.

    Use this when the user asks about titrations, equivalence points,
    buffer regions or indicator choice. YOU supply the substance data from
    your knowledge (like with generate_spectrum): pKa values, sensible
    concentrations (0.1 M is the classic teaching case) and the indicator's
    transition range.

    Not this tool for: a pH VALUE as a number — that is calculate_ph, which
    solves the same charge balance and shows the working. This one only
    draws. Nor for the content from a real titration series
    (calculate_content).

    Args:
        substance: Display name, e.g. "Acetic acid with NaOH" (localizable).
        pka_values: pKa per protolysis step, ascending (1-3 values).
        c_acid: Acid concentration in mol/L.
        v_acid_ml: Initial acid volume in mL.
        c_titrant: Titrant (strong base) concentration in mol/L.
        indicator: Optional {"name": "...", "ph_range": [low, high]}.
    """
    from chemdraw_tool.ph_plots import render_titration_png, render_titration_svg

    if not pka_values:
        raise ValueError("Mindestens ein pKa-Wert wird benötigt.")
    if min(c_acid, v_acid_ml, c_titrant) <= 0:
        raise ValueError("Konzentrationen und Volumen müssen positiv sein.")

    kwargs = dict(
        pka_values=pka_values,
        c_acid=c_acid,
        v_acid_ml=v_acid_ml,
        c_titrant=c_titrant,
        title=substance,
        indicator=indicator,
    )
    svg = render_titration_svg(**kwargs)
    files = write_files(
        PLOT_DIR / f"titration-{_slugify(substance)}",
        {"png": render_titration_png(**kwargs), "svg": svg},
    )
    return PlotPayload(
        name=substance,
        subtitle="Titration curve — equivalence points, buffer points, indicator",
        svg=svg,
        files=files,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_calibration_curve(
    concentrations: list[float],
    signals: list[float],
    unknown_signals: list[float] | None = None,
    substance: str = "",
    x_label: str = "Concentration",
    y_label: str = "Signal",
    through_origin: bool = False,
) -> PlotPayload:
    """Draw a calibration line and read unknown samples off it.

    Least-squares fit through the standards, with the equation, R² and the
    residuals — and, if `unknown_signals` are given, the concentration behind
    each measured signal, marked on the plot the way you would read it off
    with a ruler.

    Reading unknowns back is the point of a calibration; slope and R² alone
    answer no question anyone actually asks. A sample outside the calibrated
    range is labelled as extrapolated rather than quietly reported — the line
    was never verified there.

    Also reports the limit of detection and quantitation (DIN 32645, from the
    residual scatter), which is what a validation question asks for.

    Not this tool for: content from a monograph method with a known
    A(1%,1cm) or titration factor — that is calculate_content, which needs no
    calibration series. Use this one when YOU measured a series of standards.

    Args:
        concentrations: The standards, in whatever unit you report in.
        signals: Measured signal per standard — absorbance, peak area,
            same length and order as concentrations.
        unknown_signals: Signals of samples to read back off the line.
        substance: Display name for the title (localizable).
        x_label: Axis label for the concentration, with its unit.
        y_label: Axis label for the signal.
        through_origin: Force the line through zero. Only when the method is
            known to have no blank — otherwise it hides a systematic error.
    """
    from chemdraw_tool import calibration, calibration_plot

    if not concentrations or not signals:
        raise ValueError(
            "A calibration needs the standards and their signals — "
            "concentrations and signals must both be filled."
        )

    reg = calibration.linear_regression(concentrations, signals, through_origin)

    unknowns = [calibration.interpolate(s, reg) for s in (unknown_signals or [])]
    limits = calibration.detection_limits(reg)

    notes: list[str] = []
    for u in unknowns:
        line = (
            f"Signal {u['signal']:.6g} → **{u['concentration']:.6g}** "
            f"({u['formula']}: {u['substitution']})"
        )
        if u["extrapolated"]:
            line += "  ⚠ outside the calibrated range"
        notes.append(line)
    for u in unknowns:
        notes.extend(u["notes"])

    if reg["r_squared"] < 0.99 and not unknowns:
        notes.append(
            f"R² = {reg['r_squared']:.5f}. Below about 0.99 the linearity is "
            "usually considered insufficient for a quantitative method — check "
            "the standards before reading samples off this line."
        )
    if limits["lod"]:
        notes.append(
            f"Limit of detection ≈ {limits['lod']:.4g}, limit of quantitation "
            f"≈ {limits['loq']:.4g} ({limits['formula']})."
        )
    notes.extend(limits["notes"])

    title = f"Calibration curve: {substance}" if substance else "Calibration curve"
    kwargs = {
        "regression": reg,
        "unknowns": unknowns,
        "title": substance,
        "x_label": x_label,
        "y_label": y_label,
    }
    artifacts = {
        "png": calibration_plot.render_png(**kwargs),
        "svg": calibration_plot.render_svg(**kwargs),
    }
    files = write_files(
        PLOT_DIR / _slugify(substance or "calibration curve"), artifacts
    )

    return PlotPayload(
        name=title,
        subtitle=(
            f"{reg['equation']} · R² = {reg['r_squared']:.5f} · "
            f"n = {reg['n']} standards"
        ),
        svg=artifacts["svg"],
        files=files,
        notes=notes,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_species_distribution(
    substance: str,
    pka_values: list[float],
    labels: list[str] | None = None,
) -> PlotPayload:
    """Draw the species distribution of an acid over pH (Henderson-Hasselbalch).

    Plots the fraction α of every protonation species against pH with the
    pKa values marked — the standard diagram for absorption/distribution
    reasoning in pharmacy.

    Use this when the user asks which species dominates at a given pH, about
    degree of ionization, or absorption across membranes. YOU supply pKa
    values from your knowledge; pass species labels (formulas like "H₂PO₄⁻")
    for a readable legend.

    Not this tool for: the pH of a solution or a buffer as a number — that
    is calculate_ph. This one draws the fractions across the whole pH range;
    it answers "which species when", not "what pH do I have".

    Args:
        substance: Display name, e.g. "Phosphoric acid" (localizable).
        pka_values: pKa per protolysis step, ascending.
        labels: Optional species labels, most protonated first
            (len = len(pka_values) + 1).
    """
    from chemdraw_tool.ph_plots import render_species_png, render_species_svg

    if not pka_values:
        raise ValueError("Mindestens ein pKa-Wert wird benötigt.")

    svg = render_species_svg(pka_values, labels, substance)
    files = write_files(
        PLOT_DIR / f"species-{_slugify(substance)}",
        {"png": render_species_png(pka_values, labels, substance), "svg": svg},
    )
    return PlotPayload(
        name=substance,
        subtitle="Species distribution over pH",
        svg=svg,
        files=files,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def compare_molecules(
    structures: list[str],
    labels: list[str] | None = None,
    title: str = "",
) -> PlotPayload:
    """Compare 2-4 molecules side by side with their DIFFERENCES highlighted.

    Computes the maximum common substructure (MCS): the shared scaffold
    stays neutral, everything outside it is highlighted — ideal for
    teaching drug classes ("what distinguishes ibuprofen from naproxen?"),
    homologous series or derivatives.

    Use this when the user wants to compare structures, see differences
    between compounds, or study a drug class.

    Not this tool for: a single structure (generate_molecule), or several
    structures that are merely to be drawn rather than contrasted
    (batch_generate).

    Args:
        structures: 2-4 English/IUPAC names or SMILES strings.
        labels: Optional display names under each panel (localizable).
        title: Optional heading for the comparison (localizable).
    """
    from chemdraw_tool.image_export import (
        render_comparison_png,
        render_comparison_svg,
    )

    if not 2 <= len(structures) <= 4:
        raise ValueError("compare_molecules braucht 2 bis 4 Strukturen.")

    mols = []
    for s in structures:
        _, mol = resolve(s)
        mols.append(generate_2d(mol))

    display = title or " vs. ".join(labels or structures)
    panel_labels = labels or structures
    svg = render_comparison_svg(mols, panel_labels)
    files = write_files(
        PLOT_DIR / f"compare-{_slugify(display)}",
        {"png": render_comparison_png(mols, panel_labels), "svg": svg},
    )
    return PlotPayload(
        name=display,
        subtitle="Structure comparison — differences highlighted, shared scaffold neutral",
        svg=svg,
        files=files,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_3d(name_or_smiles: str, label: str = "") -> Molecule3DPayload:
    """Generate a 3D conformer shown as an interactive, rotatable model.

    Embeds the molecule in 3D (ETKDGv3 + force-field optimization, explicit
    hydrogens) and opens a drag-to-rotate ball-and-stick viewer in the chat
    panel. Also writes an SDF file for molecular modelling tools.

    Use this when the user asks about 3D structure, molecular geometry
    (tetrahedral, planar...), conformation or spatial arrangement.

    IMPORTANT: Pass English/IUPAC names or SMILES; use label for the
    localized display name.

    Args:
        name_or_smiles: English/IUPAC compound name or SMILES string.
        label: Optional display name (localizable).
    """
    from chemdraw_tool.structure3d import atoms_and_bonds, embed_3d

    _, mol = resolve(name_or_smiles)
    mol3d = embed_3d(mol)
    atoms, bonds = atoms_and_bonds(mol3d)

    display_name = label or name_or_smiles
    THREED_DIR.mkdir(parents=True, exist_ok=True)
    sdf_path = THREED_DIR / f"{_slugify(display_name)}.sdf"
    from rdkit import Chem as _Chem

    sdf_path.write_text(_Chem.MolToMolBlock(mol3d), encoding="utf-8")

    return Molecule3DPayload(
        name=display_name,
        atoms=atoms,
        bonds=bonds,
        files={"sdf": str(sdf_path)},
    )


def _format_calculation(title: str, result_line: str, steps, notes) -> str:
    """Rechenweg als Markdown — Schritt für Schritt zum Abschreiben.

    Bewusst als Liste statt als Tabelle: Formel, eingesetzte Zahlen und
    Ergebnis stehen so untereinander wie im Protokollheft, und lange Terme
    brechen nicht in einer Zelle um.
    """
    lines = [f"# {title}", "", f"**{result_line}**", "", "## Calculation"]
    for i, step in enumerate(steps, 1):
        lines.append(f"\n**{i}. {step['label']}**")
        lines.append(f"- Formula: `{step['formula']}`")
        lines.append(f"- Substituted: `{step['substitution']}`")
        lines.append(f"- Result: **{step['result']}**")
        if step.get("explanation"):
            lines.append(f"- {step['explanation']}")
    if notes:
        lines.append("\n## Check before you weigh")
        lines.extend(f"- {n}" for n in notes)
    return "\n".join(lines)


def _require(value, name: str, topic: str):
    """Fehlende Pflichtangabe benennen, statt stillschweigend mit 0 zu rechnen."""
    if not value:
        raise ValueError(
            f"topic='{topic}' needs {name}. Nothing was given, and calculating "
            "with zero would produce a confident wrong answer."
        )
    return value


@mcp.tool()
def calculate_solution(
    topic: SolutionTopic,
    substance: str = "",
    concentration: float = 0.0,
    volume_ml: float = 0.0,
    mass_g: float = 0.0,
    molar_mass_g: float = 0.0,
    target: float = 0.0,
    stock_concentration: float = 0.0,
    stock_volume_ml: float = 0.0,
    final_concentration: float = 0.0,
    final_volume_ml: float = 0.0,
    high: float = 0.0,
    low: float = 0.0,
    total: float = 0.0,
) -> str:
    """Do the bench maths before an experiment, with the full working shown.

    Answers the questions that come up in front of the balance and returns
    every step — formula, substituted numbers, result — because the report
    asks for the working, not just the number.

    Pick the `topic`:

    - "weigh_in": how much do I weigh out? substance, concentration (mol/L),
      volume_ml. The everyday case: "250 mL of 0.1 M NaOH" → 1.0 g.
    - "concentration": what did I actually get? substance, mass_g,
      volume_ml; `target` also gives the deviation from what you aimed for.
    - "dilution": C₁V₁ = C₂V₂. Give exactly three of stock_concentration,
      stock_volume_ml, final_concentration, final_volume_ml — the fourth
      comes back with the amount of solvent to add.
    - "mixing": mixing cross. high, low and target contents in the same unit;
      `total` scales the parts. Diluting with water is low=0.
    - "molar_mass": molar mass with element breakdown; handles hydrates.

    `substance` takes a chemical FORMULA ("NaOH", "CuSO4·5H2O"), not a
    trivial name — without a clean formula pass `molar_mass_g` directly.

    Not this tool for: content determination from titration or photometry
    (use calculate_content), pH and buffers (use calculate_ph), or a
    substance's tabulated properties (use lookup).

    Args:
        topic: Which calculation to run — see above.
        substance: Chemical formula, e.g. "NaOH" or "CuSO4·5H2O".
        concentration: Wanted concentration, mol/L ("weigh_in").
        volume_ml: Volume being prepared, mL.
        mass_g: Mass actually weighed, g ("concentration").
        molar_mass_g: Molar mass in g/mol if there is no usable formula.
        target: Target concentration ("concentration") or content ("mixing").
        stock_concentration: c₁ ("dilution").
        stock_volume_ml: V₁ ("dilution").
        final_concentration: c₂ ("dilution").
        final_volume_ml: V₂ ("dilution").
        high: Content of the stronger component ("mixing").
        low: Content of the weaker component, 0 for water ("mixing").
        total: Total amount wanted ("mixing").
    """
    from chemdraw_tool import solution as sol

    if topic == "molar_mass":
        data = sol.molar_mass(_require(substance, "a substance formula", topic))
        lines = [
            f"# Molar mass of {data['formula']}",
            "",
            f"**M = {data['mass']:.4f} g/mol**",
            "",
            "| Element | Count | Mass share | Fraction |",
            "|---|---|---|---|",
        ]
        for part in data["composition"]:
            lines.append(
                f"| {part['symbol']} | {part['count']} | "
                f"{part['mass']:.4f} g/mol | {part['fraction'] * 100:.2f} % |"
            )
        return "\n".join(lines)

    if topic == "weigh_in":
        if not substance and not molar_mass_g:
            raise ValueError(
                "topic='weigh_in' needs a substance formula (or molar_mass_g). "
                "Without a molar mass there is nothing to convert moles into grams."
            )
        r = sol.mass_for_solution(
            substance or "the substance",
            concentration=_require(concentration, "a concentration in mol/L", topic),
            volume_ml=_require(volume_ml, "a volume in mL", topic),
            molar_mass_g=molar_mass_g or None,
        )
        headline = (
            f"Weigh {r['mass_g']:.4g} g of {substance or 'the substance'} and make "
            f"up to {r['volume_ml']:.4g} mL to get {r['concentration']:.4g} mol/L."
        )
        return _format_calculation(
            f"Weighing for {r['volume_ml']:.4g} mL of {r['concentration']:.4g} mol/L "
            f"{substance or 'solution'}",
            headline,
            r["steps"],
            r["notes"],
        )

    if topic == "concentration":
        if not substance and not molar_mass_g:
            raise ValueError(
                "topic='concentration' needs a substance formula (or molar_mass_g)."
            )
        r = sol.concentration_from_mass(
            substance or "the substance",
            mass_g=_require(mass_g, "the weighed mass in g", topic),
            volume_ml=_require(volume_ml, "a volume in mL", topic),
            molar_mass_g=molar_mass_g or None,
            target=target or None,
        )
        headline = f"c = {r['concentration']:.6g} mol/L"
        if "deviation_percent" in r:
            headline += f" ({r['deviation_percent']:+.2f} % off the target)"
        return _format_calculation(
            f"Concentration of the {substance or ''} solution".strip(),
            headline,
            r["steps"],
            r["notes"],
        )

    if topic == "dilution":
        r = sol.dilution(
            c1=stock_concentration or None,
            v1_ml=stock_volume_ml or None,
            c2=final_concentration or None,
            v2_ml=final_volume_ml or None,
        )
        headline = (
            f"Take {r['v1_ml']:.4g} mL of the {r['c1']:.4g} mol/L stock and make up "
            f"to {r['v2_ml']:.4g} mL — that is {r['c2']:.4g} mol/L."
        )
        return _format_calculation("Dilution", headline, r["steps"], r["notes"])

    if topic == "mixing":
        r = sol.mixing_cross(
            high=_require(high, "the stronger content (high)", topic),
            low=low,
            target=_require(target, "the target content", topic),
            total=total or None,
        )
        if "amount_high" in r:
            headline = (
                f"Mix {r['amount_high']:.4g} of the {r['high']:.4g} component with "
                f"{r['amount_low']:.4g} of the {r['low']:.4g} component."
            )
        else:
            headline = (
                f"Ratio {r['parts_high']:.4g} : {r['parts_low']:.4g} "
                f"({r['high']:.4g} : {r['low']:.4g} component)"
            )
        return _format_calculation("Mixing cross", headline, r["steps"], r["notes"])

    raise ValueError(
        f"Unknown topic '{topic}' — pick one of: weigh_in, concentration, "
        "dilution, mixing, molar_mass."
    )


def _fat_value_rows(
    method: str,
    weights_mg: list[float],
    measurements: list[float],
    blank_ml: float,
    titrant_concentration: float,
    titer_mg_per_ml: float,
) -> list[dict]:
    """Fettkennzahl oder Wassergehalt je Messung, im Schema der Titration.

    `weights_mg` ist auch hier in mg — die Kennzahlformeln stehen in Gramm,
    die Umrechnung passiert an einer Stelle statt in jedem Aufruf.
    """
    from chemdraw_tool.calculator import fat_values as fv

    if method == "water_kf":
        if not titer_mg_per_ml:
            raise ValueError(
                "method='water_kf' needs titer_mg_per_ml — the titer of the "
                "Karl Fischer reagent in mg water per mL. It drifts, so it is "
                "redetermined before every run."
            )
    elif not titrant_concentration:
        raise ValueError(
            f"method='{method}' needs titrant_concentration in mol/L. The short "
            "formulas in the pharmacopoeia assume one particular volumetric "
            "solution; naming the real one keeps the result right."
        )

    if method in _BACK_TITRATION_METHODS and not blank_ml:
        raise ValueError(
            f"method='{method}' is a back titration and needs blank_ml — the "
            "reference reading the sample is compared against. Without it the "
            "result would be the consumption of the blank, not of the sample."
        )

    rows = []
    for i, (mass_mg, reading) in enumerate(zip(weights_mg, measurements), start=1):
        if method == "acid_value":
            r = fv.acid_value(mass_mg / 1000.0, reading, titrant_concentration)
        elif method == "saponification_value":
            r = fv.saponification_value(
                mass_mg / 1000.0, blank_ml, reading, titrant_concentration
            )
        elif method == "iodine_value":
            r = fv.iodine_value(
                mass_mg / 1000.0, blank_ml, reading, titrant_concentration
            )
        else:
            r = fv.water_content_kf(mass_mg, reading, titer_mg_per_ml, blank_ml)
        rows.append(
            {
                "label": f"Measurement {i}",
                "gehalt": r["value"],
                "formula": r["formula"],
                "substitution": r["substitution"],
                "result": r["result"],
                "explanation": r["explanation"] if i == 1 else "",
            }
        )
    return rows


@mcp.tool()
def calculate_content(
    method: ContentMethod,
    weights_mg: list[float],
    measurements: list[float],
    factor_mg_per_ml: float = 0.0,
    titer: float = 1.0,
    blank_ml: float = 0.0,
    a1_1cm: float = 0.0,
    path_length_cm: float = 1.0,
    dilution_factor: float = 1.0,
    flask_volume_ml: float = 0.0,
    reference_weights_mg: list[float] | None = None,
    reference_volumes_ml: list[float] | None = None,
    declared_content: float = 100.0,
    titrant_concentration: float = 0.0,
    titer_mg_per_ml: float = 0.0,
    known_acid_value: float = 0.0,
) -> str:
    """Work out a content determination the way a lab report wants it.

    Runs the chain in protocol order: content per measurement → Grubbs
    outlier check → mean and spread → t-test against the declared content,
    each step with formula, substituted numbers and result.

    Methods — content of a substance:

    - "titration": weights_mg, measurements (mL), factor_mg_per_ml; a
      reference titration determines the titer first.
    - "photometry": weights_mg, measurements (absorbance), a1_1cm,
      flask_volume_ml, dilution_factor.

    Fat characteristics and water, same input shape, all needing
    titrant_concentration (the short formulas hold only for the standard
    volumetric solution):

    - "acid_value": free acids, mg KOH/g.
    - "saponification_value" (mg KOH/g) and "iodine_value" (g I₂/100 g) are
      back titrations — blank_ml is the REFERENCE reading.
    - "water_kf": Karl Fischer, %; blank_ml is the drift.

    weights_mg is ALWAYS mg, also for fat values.

    Not this tool for: preparing or diluting a solution (use
    calculate_solution); drawing the titration curve (use
    generate_titration_curve); quantifying against a measured series of
    standards (use generate_calibration_curve — this one needs none).

    Args:
        method: One of the seven above.
        weights_mg: Weighed portions, mg, one per measurement.
        measurements: mL titrant or absorbance, order of weights_mg.
        factor_mg_per_ml: Titration factor from the monograph.
        titer: Titer of the volumetric solution; 1.0 if exact.
        blank_ml: Blank, mL (reference reading for back titrations).
        a1_1cm: Specific absorbance A(1%,1cm).
        path_length_cm: Cuvette path length, normally 1.
        dilution_factor: Dilution of the measured solution.
        flask_volume_ml: Volumetric flask, mL.
        reference_weights_mg, reference_volumes_ml: Reference titration.
        declared_content: Declared content, %; the t-test uses it.
        titrant_concentration: mol/L, for fat characteristics.
        titer_mg_per_ml: Karl Fischer titer, mg water/mL.
        known_acid_value: Adds the ester value to saponification.
    """
    from chemdraw_tool.calculator.photometry import calculate_gehalt_uv
    from chemdraw_tool.calculator.stats import (
        descriptive_stats,
        grubbs_test,
        one_sample_t_test,
    )
    from chemdraw_tool.calculator.titration import (
        calculate_gehalt_titration,
        calculate_titer,
    )

    if method not in _CONTENT_UNITS:
        raise ValueError(
            f"Unknown method '{method}' — use one of: "
            f"{', '.join(sorted(_CONTENT_UNITS))}."
        )
    if len(weights_mg) != len(measurements):
        raise ValueError(
            f"weights_mg ({len(weights_mg)} values) and measurements "
            f"({len(measurements)} values) must have the same length — every "
            "weighed portion belongs to exactly one reading."
        )

    sections: list[str] = []
    used_titer = titer

    if method == "titration":
        if not factor_mg_per_ml:
            raise ValueError(
                "method='titration' needs factor_mg_per_ml — the mg of substance "
                "one mL of titrant corresponds to. The monograph states it."
            )
        if reference_weights_mg and reference_volumes_ml:
            used_titer = calculate_titer(
                reference_weights_mg,
                reference_volumes_ml,
                blank_ml,
                factor_mg_per_ml,
            )
            sections.append(
                "## Titer\n\n"
                f"- Formula: `t = mean(content of reference) / declared content`\n"
                f"- From {len(reference_weights_mg)} reference titrations\n"
                f"- Result: **t = {used_titer:.4f}**\n"
                "- Every sample reading below is corrected with this titer."
            )
        rows = calculate_gehalt_titration(
            weights_mg, measurements, blank_ml, factor_mg_per_ml, used_titer
        )
    elif method == "photometry":
        if not a1_1cm:
            raise ValueError(
                "method='photometry' needs a1_1cm — the specific absorbance "
                "A(1%,1cm) from the monograph."
            )
        if not flask_volume_ml:
            raise ValueError("method='photometry' needs flask_volume_ml.")
        rows = calculate_gehalt_uv(
            weights_mg,
            measurements,
            substance="",
            verduennungsfaktor=dilution_factor,
            kolbenvolumen_ml=flask_volume_ml,
            a1pct1cm=a1_1cm,
            path_length_cm=path_length_cm,
        )
    else:
        rows = _fat_value_rows(
            method,
            weights_mg,
            measurements,
            blank_ml=blank_ml,
            titrant_concentration=titrant_concentration,
            titer_mg_per_ml=titer_mg_per_ml,
        )

    contents = [row["gehalt"] for row in rows]
    unit = _CONTENT_UNITS[method]
    # Nur die Gehaltsbestimmungen haben einen prozentualen Sollwert. Eine
    # Iodzahl gegen "100 %" zu testen waere Unsinn mit Nachkommastellen.
    has_target = method in ("titration", "photometry")

    lines = [
        f"# {method.replace('_', ' ').capitalize()}",
        "",
        "## Individual measurements",
    ]
    for i, row in enumerate(rows, 1):
        lines.append(f"\n**Measurement {i}**")
        lines.append(f"- Formula: `{row['formula']}`")
        lines.append(f"- Substituted: `{row['substitution']}`")
        lines.append(f"- Result: **{row['result']}**")
        if row.get("explanation"):
            lines.append(f"- {row['explanation']}")

    if sections:
        lines.insert(2, "\n".join(sections) + "\n")

    if method == "saponification_value" and known_acid_value:
        from chemdraw_tool.calculator.fat_values import ester_value

        ev = ester_value(sum(contents) / len(contents), known_acid_value)
        lines.append("\n## Ester value")
        lines.append(f"- Formula: `{ev['formula']}`")
        lines.append(f"- Substituted: `{ev['substitution']}`")
        lines.append(f"- Result: **{ev['result']}**")
        lines.append(f"- {ev['explanation']}")

    if len(contents) == 1:
        lines.append(
            "\n## Spread\n\nOnly one measurement — no standard deviation, no "
            "outlier test and no t-test. A single value cannot show whether it "
            "is reproducible; the pharmacopoeia asks for a series."
        )
        return "\n".join(lines)

    # Grubbs ist erst ab drei Werten definiert. Bei zweien gibt es keinen
    # "am weitesten entfernten" Wert im statistischen Sinn — das zu sagen ist
    # ehrlicher, als den Schritt stillschweigend zu überspringen.
    grubbs = grubbs_test(contents) if len(contents) >= 3 else None
    lines.append("\n## Outlier check (Grubbs)")
    if grubbs is None:
        lines.append(
            f"- Not applicable with {len(contents)} measurements — the Grubbs "
            "test needs at least three. Two values that disagree give no way to "
            "tell which one is wrong."
        )
    else:
        lines.append(f"- Formula: `{grubbs['formula']}`")
        lines.append(f"- Substituted: `{grubbs['substitution']}`")
        lines.append(
            f"- Result: **G = {grubbs['g_value']:.3f}**, "
            f"G_crit = {grubbs['g_critical']:.3f} (n = {grubbs['n']})"
        )
        lines.append(f"- {grubbs['explanation']}")

    stats = descriptive_stats(
        contents, true_value=declared_content if has_target else None
    )
    lines.append("\n## Mean and spread")
    lines.append(f"- Mean: **{stats['mean']:.2f} {unit}**")
    lines.append(f"- Standard deviation s: {stats['std_abs']:.3f} {unit}")
    lines.append(f"- RSD: {stats['std_rel']:.2f} %")
    if "recovery" in stats:
        lines.append(
            f"- Recovery against the declared {declared_content:.4g} %: "
            f"{stats['recovery']:.2f} %"
        )

    if has_target:
        t = one_sample_t_test(contents, declared_content)
        verdict = (
            "no significant difference from the declared content"
            if t["passed"]
            else "significantly different from the declared content"
        )
        lines.append(f"\n## t-test against {declared_content:.4g} %")
        lines.append("- Formula: `t = |x̄ − µ| / (s / √n)`")
        lines.append(
            f"- Result: **t = {t['t_value']:.3f}**, t_crit = {t['t_critical']:.3f} "
            f"(df = {t['df']}, α = 0.05)"
        )
        lines.append(f"- Verdict: {verdict}.")

    if grubbs is not None and grubbs["is_outlier"]:
        lines.append(
            "\n> The mean, spread and t-test above still include the flagged "
            "value. Decide whether to exclude it, then run this again with the "
            "remaining measurements — and document both runs."
        )

    return "\n".join(lines)


@mcp.tool()
def calculate_ph(
    topic: PhTopic,
    concentration: float = 0.0,
    pka: float = 0.0,
    pkb: float = 0.0,
    pka_values: list[float] | None = None,
    acid_concentration: float = 0.0,
    base_concentration: float = 0.0,
    target_ph: float = 0.0,
    total_concentration: float = 0.0,
    volume_ml: float = 0.0,
    acid_molar_mass: float = 0.0,
    base_molar_mass: float = 0.0,
) -> str:
    """Calculate pH, buffer composition and buffer recipes, with the working.

    Solves the exact charge balance — the same one that draws the titration
    curve — and puts the textbook approximation next to it. Where the two
    disagree, the approximation has lost its assumptions and the answer says
    so instead of quietly being wrong.

    Pick the `topic`:

    - "weak_acid": concentration and pka (or pka_values for a polyprotic acid).
    - "weak_base": concentration and pkb — or pka of the conjugate acid.
    - "strong_acid" / "strong_base": concentration. Includes the
      autoprotolysis of water, so 1e-8 M HCl comes out just below 7.
    - "buffer": acid_concentration, base_concentration, pka. Also reports
      ratio and buffer capacity, and warns when the pair is wrong for the pH.
    - "buffer_recipe": target_ph, pka, total_concentration, volume_ml;
      acid_molar_mass and base_molar_mass turn moles into weighable masses.

    You supply the pKa values — they are in the monograph or the table, and
    guessing them would silently change the answer.

    Not this tool for: drawing the titration curve or the species
    distribution (generate_titration_curve, generate_species_distribution —
    this one computes, those draw), or preparing a solution of a known
    concentration (calculate_solution).

    Args:
        topic: Which case to solve — see the list above.
        concentration: Concentration in mol/L of the acid or base.
        pka: pKa of the acid, or of the conjugate acid of a base.
        pkb: pKb of the base.
        pka_values: All pKa values of a polyprotic acid, in order.
        acid_concentration: [HA] in mol/L ("buffer").
        base_concentration: [A⁻] in mol/L ("buffer").
        target_ph: pH the buffer should have ("buffer_recipe").
        total_concentration: [HA] + [A⁻] in mol/L ("buffer_recipe").
        volume_ml: Volume of buffer to prepare, in mL.
        acid_molar_mass: Molar mass of the acid component, in g/mol.
        base_molar_mass: Molar mass of the base component, in g/mol.
    """
    from chemdraw_tool import ph_calc

    def block(title: str, headline: str, rows: list[str], notes: list[str]) -> str:
        lines = [f"# {title}", "", f"**{headline}**", ""]
        lines.extend(rows)
        if notes:
            lines.append("\n## Worth knowing")
            lines.extend(f"- {n}" for n in notes)
        return "\n".join(lines)

    if topic == "weak_acid":
        r = ph_calc.weak_acid_ph(
            concentration=concentration or 0,
            pka=pka or None,
            pka_values=pka_values or None,
        )
        rows = [
            f"- Exact (charge balance): **pH = {r['ph']:.2f}**",
            f"- Textbook approximation: pH = {r['ph_approx']:.2f}",
            f"  - Formula: `{r['approx_formula']}`",
            f"  - Substituted: `{r['approx_substitution']}`",
            f"- pOH = {r['poh']:.2f}",
            f"- pKa used: {', '.join(f'{p:g}' for p in r['pka_values'])}",
        ]
        return block(
            f"pH of {r['concentration']:g} mol/L weak acid",
            f"pH = {r['ph']:.2f}",
            rows,
            r["notes"],
        )

    if topic == "weak_base":
        r = ph_calc.weak_base_ph(
            concentration=concentration or 0,
            pkb=pkb or None,
            pka=pka or None,
        )
        rows = [
            f"- Exact (charge balance): **pH = {r['ph']:.2f}**",
            f"- Textbook approximation: pH = {r['ph_approx']:.2f}",
            f"  - Formula: `{r['approx_formula']}`",
            f"  - Substituted: `{r['approx_substitution']}`",
            f"- pOH = {r['poh']:.2f}",
            f"- pKb = {r['pkb']:g}, pKa of the conjugate acid = "
            f"{r['pka_conjugate']:g}",
        ]
        return block(
            f"pH of {r['concentration']:g} mol/L weak base",
            f"pH = {r['ph']:.2f}",
            rows,
            r["notes"],
        )

    if topic in ("strong_acid", "strong_base"):
        fn = ph_calc.strong_acid_ph if topic == "strong_acid" else ph_calc.strong_base_ph
        r = fn(concentration or 0)
        rows = [
            f"- pOH = {r['poh']:.2f}",
            f"- Formula: `{r['formula']}`",
            f"- Substituted: `{r['substitution']}`",
        ]
        kind = "strong acid" if topic == "strong_acid" else "strong base"
        return block(
            f"pH of {r['concentration']:g} mol/L {kind}",
            f"pH = {r['ph']:.2f}",
            rows,
            r["notes"],
        )

    if topic == "buffer":
        r = ph_calc.buffer_ph(
            acid_concentration=acid_concentration or 0,
            base_concentration=base_concentration or 0,
            pka=pka or None,
        )
        rows = [
            f"- Exact (charge balance): **pH = {r['ph']:.2f}**",
            f"- Henderson-Hasselbalch: pH = {r['ph_henderson_hasselbalch']:.2f}",
            f"  - Formula: `{r['formula']}`",
            f"  - Substituted: `{r['substitution']}`",
            f"- Ratio base : acid = {r['ratio']:.3g} : 1",
            f"- Buffer capacity β = {r['capacity']:.4f} mol/(L·pH)",
            f"- Total concentration = {r['total_concentration']:g} mol/L",
        ]
        return block("Buffer pH", f"pH = {r['ph']:.2f}", rows, r["notes"])

    if topic == "buffer_recipe":
        r = ph_calc.buffer_recipe(
            target_ph=target_ph,
            pka=pka or None,
            total_concentration=total_concentration or 0,
            volume_ml=volume_ml or 0,
            acid_molar_mass=acid_molar_mass or None,
            base_molar_mass=base_molar_mass or None,
        )
        rows = [
            f"- Ratio base : acid = {r['ratio']:.3g} : 1 "
            f"(from `ratio = 10^(pH − pKa)`)",
            f"- Acid: {r['acid_concentration']:.4g} mol/L → "
            f"**{r['acid_mol']:.4g} mol**"
            + (
                f" → **{r['acid_mass_g']:.3f} g**"
                if "acid_mass_g" in r
                else " (give acid_molar_mass for the mass)"
            ),
            f"- Base: {r['base_concentration']:.4g} mol/L → "
            f"**{r['base_mol']:.4g} mol**"
            + (
                f" → **{r['base_mass_g']:.3f} g**"
                if "base_mass_g" in r
                else " (give base_molar_mass for the mass)"
            ),
            f"- Dissolve both in water and make up to {r['volume_ml']:g} mL.",
            "- Check the pH with a meter and correct with a little acid or "
            "base — the calculated ratio assumes ideal behaviour.",
        ]
        return block(
            f"Buffer recipe for pH {r['target_ph']:g}",
            f"{r['volume_ml']:g} mL of a {r['total_concentration']:g} mol/L buffer, "
            f"pKa {r['pka']:g}",
            rows,
            r["notes"],
        )

    raise ValueError(
        f"Unknown topic '{topic}' — pick one of: weak_acid, weak_base, "
        "strong_acid, strong_base, buffer, buffer_recipe."
    )


@mcp.tool()
def predict_spectrum(
    topic: SpectroTopic,
    structure: str = "",
    wavenumber: float = 0.0,
) -> str:
    """Say what a spectrum of this structure should show — or read a band.

    Three questions, all of them exam material:

    - "ir_bands": which IR bands to expect for a structure, with range,
      intensity and band shape, ordered as you read a spectrum (high
      wavenumber first). Needs `structure`.
    - "assign_wavenumber": you measured a band — which groups absorb there?
      Ordered by how centrally the value sits in each range. Needs
      `wavenumber` in cm⁻¹.
    - "nmr_signals": how many ¹H signals the structure gives and in what
      integral ratio. Needs `structure`.

    Deterministic on purpose, and therefore honestly limited: band positions
    come from a curated table matched to the structure, signals from the
    topological equivalence of the protons. It does NOT predict chemical
    shifts in ppm — that would take a model and would be guesswork.

    The band list is ready to hand to generate_spectrum if a drawing is
    wanted; this tool only says what to expect.

    Not this tool for: drawing a spectrum from peaks you already have
    (generate_spectrum), or looking up measured data for a substance
    (lookup).

    Args:
        topic: Which question to answer — see the list above.
        structure: SMILES of the compound ("ir_bands", "nmr_signals").
            Resolve a name to SMILES first if needed.
        wavenumber: Measured band position in cm⁻¹ ("assign_wavenumber").
    """
    from chemdraw_tool import spectro

    if topic == "ir_bands":
        if not structure:
            raise ValueError("topic='ir_bands' needs a structure (SMILES).")
        bands = spectro.expected_ir_bands(structure)
        if not bands:
            return (
                f"# Expected IR bands\n\nNo characteristic bands found for "
                f"`{structure}` — the table covers the common functional "
                "groups, so an exotic structure can come back empty."
            )
        lines = [
            f"# Expected IR bands for `{structure}`",
            "",
            "| Wavenumber [cm⁻¹] | Group | Intensity | Shape |",
            "|---|---|---|---|",
        ]
        for b in bands:
            lines.append(
                f"| {b['high']}–{b['low']} | {b['group']} | "
                f"{b['intensity']} | {b['shape']} |"
            )
        hints = [b for b in bands if b["hint"]]
        if hints:
            lines.append("\n## What to look at first")
            lines.extend(f"- **{b['group']}** — {b['hint']}" for b in hints)
        lines.append(
            "\nRanges are typical values; conjugation lowers a C=O by roughly "
            "20–30 cm⁻¹, a small ring raises it."
        )
        return "\n".join(lines)

    if topic == "assign_wavenumber":
        if not wavenumber:
            raise ValueError(
                "topic='assign_wavenumber' needs a wavenumber in cm⁻¹."
            )
        hits = spectro.assign_wavenumber(wavenumber)
        if not hits:
            return (
                f"# {wavenumber:g} cm⁻¹\n\nNothing in the table absorbs there. "
                f"IR spectra run from {spectro.IR_MIN} to {spectro.IR_MAX} cm⁻¹; "
                "below about 1500 lies the fingerprint region, which is "
                "matched against a reference spectrum rather than assigned "
                "band by band."
            )
        lines = [
            f"# Bands at {wavenumber:g} cm⁻¹",
            "",
            "Most likely first — a value in the middle of a range is a better "
            "match than one at its edge.",
            "",
            "| Group | Range [cm⁻¹] | Intensity | Shape |",
            "|---|---|---|---|",
        ]
        for h in hits:
            lines.append(
                f"| **{h['group']}** | {h['high']}–{h['low']} | "
                f"{h['intensity']} | {h['shape']} |"
            )
        distinguishing = [h for h in hits if h["hint"]]
        if distinguishing:
            lines.append("\n## How to tell them apart")
            lines.extend(f"- **{h['group']}** — {h['hint']}" for h in distinguishing)
        return "\n".join(lines)

    if topic == "nmr_signals":
        if not structure:
            raise ValueError("topic='nmr_signals' needs a structure (SMILES).")
        r = spectro.proton_signals(structure)
        lines = [
            f"# ¹H signals for `{structure}`",
            "",
            f"**{r['count']} signal(s), {r['total_hydrogens']} hydrogens**",
            "",
            f"- Integral ratio: {':'.join(str(i) for i in r['integrals']) or '—'}",
            f"- {r['explanation']}",
            "",
            "## Limitation",
            f"- {r['limitation']}",
            "- No chemical shifts: predicting ppm values takes a model, and a "
            "guessed shift is worse than none.",
        ]
        return "\n".join(lines)

    raise ValueError(
        f"Unknown topic '{topic}' — pick one of: ir_bands, assign_wavenumber, "
        "nmr_signals."
    )


@mcp.tool()
def lookup(name: str, topic: LookupTopic = "properties") -> str:
    """Fetch a specific fact or value about a compound as plain text.

    Use it when the request asks for a named piece of data — pick the `topic`:

    - "properties" (default): formula, molecular weight, CAS number,
      IUPAC name, LogP, InChIKey (PubChem).
    - "safety": GHS hazards — H/P statements, pictograms, signal word.
      For lab protocols and risk assessments.
    - "physical": experimental melting point, boiling point, density,
      solubility.
    - "biochem": compound class and biological role (ChEBI), related
      enzymes and proteins (UniProt).
    - "pathway": metabolic pathways the compound appears in (KEGG).

    Not this tool for: a bare compound name with no named value asked for —
    that means show the substance, use generate_molecule. Nor for a visual
    data sheet with the structure beside the facts — use lookup_molecule_data.
    This tool draws nothing; it returns text.

    IMPORTANT: Always pass English or IUPAC compound names, never localized
    names — 'Aspirin' not 'Acetylsalicylsäure', 'Caffeine' not 'Coffein'.

    Args:
        name: English/IUPAC compound name (e.g. 'Aspirin', 'Histidine').
        topic: Which facts to fetch — see the list above.
    """
    # Kein dict.get(...) mit Fallback: ein vertipptes Thema würde sonst still
    # die Grunddaten liefern und wie eine Antwort auf die gestellte Frage
    # aussehen. Lieber hörbar scheitern.
    handlers = {
        "properties": _lookup_compound,
        "safety": _lookup_safety,
        "physical": _lookup_physical,
        "biochem": _lookup_biochem,
        "pathway": _lookup_pathway,
    }
    if topic not in handlers:
        raise ValueError(
            f"Unbekanntes topic '{topic}' — erlaubt: {', '.join(handlers)}."
        )
    return handlers[topic](name)


def _lookup_compound(name: str) -> str:
    """PubChem-Grunddaten als Markdown — Thema "properties" von `lookup`."""
    lines = [f"## {name} — PubChem-Daten\n"]
    cid = "?"

    props = pubchem_properties(name)
    have_table = bool(props)
    if props:
        cid = props.get("CID", "?")
        lines.append("| Eigenschaft | Wert |")
        lines.append("|------------|------|")
        lines.append(f"| **CID** | {cid} |")
        # Numerische Felder auf Existenz prüfen, nicht auf Wahrheit: Benzol hat
        # echt TPSA 0 und null H-Brücken — eine `if v :=`-Prüfung verschluckt
        # genau diese Messwerte und der Nutzer hält sie für unbekannt.
        for key, label, unit in (
            ("IUPACName", "IUPAC-Name", ""),
            ("MolecularFormula", "Summenformel", ""),
            ("MolecularWeight", "Molmasse", " g/mol"),
            ("ExactMass", "Exakte Masse", ""),
            ("XLogP", "LogP", ""),
            ("TPSA", "Polare Oberfläche", " Å²"),
            ("HBondDonorCount", "H-Brücken-Donoren", ""),
            ("HBondAcceptorCount", "H-Brücken-Akzeptoren", ""),
            ("InChIKey", "InChIKey", ""),
        ):
            v = props.get(key)
            if v is not None and v != "":
                lines.append(f"| **{label}** | {v}{unit} |")
        charge = props.get("Charge")
        if charge:
            lines.append(f"| **Ladung** | {charge} |")
    else:
        lines.append("Eigenschaften konnten nicht abgerufen werden.")

    cas, synonyms = pubchem_synonyms(name)
    if cas:
        # Ohne Tabellenkopf wäre eine Pipe-Zeile roher Text im Chat.
        if have_table:
            lines.append(f"| **CAS-Nr.** | {cas} |")
        else:
            lines.append(f"\n**CAS-Nr.:** {cas}")
    if synonyms:
        filtered = [s for s in synonyms if s.lower() != name.lower()][:5]
        if filtered:
            lines.append(f"\n**Synonyme:** {', '.join(filtered)}")

    lines.append(
        f"\n*Quelle: [PubChem CID {cid}]"
        f"(https://pubchem.ncbi.nlm.nih.gov/compound/{cid})*"
    )
    return "\n".join(lines)


def _lookup_safety(name: str) -> str:
    """GHS-Gefahrstoffdaten als Markdown — Thema "safety" von `lookup`."""
    cid = _get_cid(name)
    if cid is None:
        return f"Verbindung '{name}' nicht in PubChem gefunden."

    safety = pubchem_safety(cid)
    if not safety:
        return f"Keine GHS-Sicherheitsdaten für '{name}' in PubChem."

    lines = [f"## {name} — Sicherheitsdaten (GHS)\n"]
    lines.append("| Kategorie | Information |")
    lines.append("|-----------|------------|")

    for entry in safety:
        n = entry.get("name", "")
        v = entry.get("value", "")
        if v:
            lines.append(f"| **{n}** | {v} |")

    lines.append(
        f"\n*Quelle: [PubChem CID {cid}]"
        f"(https://pubchem.ncbi.nlm.nih.gov/compound/{cid}#section=Safety-and-Hazards)*"
    )
    return "\n".join(lines)


def _lookup_physical(name: str) -> str:
    """Schmelz-/Siedepunkt, Dichte, Löslichkeit — Thema "physical" von `lookup`."""
    cid = _get_cid(name)
    if cid is None:
        return f"Verbindung '{name}' nicht in PubChem gefunden."

    props = pubchem_physical_properties(cid)
    if not props:
        return f"Keine experimentellen Daten für '{name}' in PubChem."

    lines = [f"## {name} — Physikalische Eigenschaften\n"]
    lines.append("| Eigenschaft | Wert |")
    lines.append("|------------|------|")

    seen = set()
    for entry in props:
        n = entry.get("name", "")
        v = entry.get("value", "")
        if v and n not in seen:
            seen.add(n)
            lines.append(f"| **{n}** | {v} |")

    lines.append(
        f"\n*Quelle: [PubChem CID {cid}]"
        f"(https://pubchem.ncbi.nlm.nih.gov/compound/{cid}#section=Experimental-Properties)*"
    )
    return "\n".join(lines)


def _lookup_biochem(name: str) -> str:
    """ChEBI-Klassifikation + UniProt-Enzyme — Thema "biochem" von `lookup`."""
    lines = [f"## {name} — Biochemische Einordnung\n"]

    chebi = chebi_lookup(name)
    if chebi:
        lines.append("### ChEBI (Chemical Entities of Biological Interest)\n")
        lines.append(f"- **ID:** {chebi['obo_id']}")
        lines.append(f"- **Name:** {chebi['label']}")
        if chebi["description"]:
            lines.append(f"- **Beschreibung:** {chebi['description']}")
        lines.append(
            f"- *Quelle: [ChEBI {chebi['obo_id']}]"
            f"(https://www.ebi.ac.uk/chebi/searchId.do?chebiId={chebi['id']})*"
        )
    else:
        lines.append("Kein ChEBI-Eintrag gefunden.\n")

    proteins = uniprot_search(name)
    if proteins:
        lines.append("\n### UniProt (Proteine/Enzyme, Mensch)\n")
        for p in proteins[:3]:
            acc = p["accession"]
            lines.append(f"- **{p['name']}** ({acc})")
            if p["genes"]:
                lines.append(f"  - Gene: {', '.join(p['genes'])}")
            if p["ec"]:
                lines.append(f"  - EC: {', '.join(p['ec'])}")
            lines.append(
                f"  - *[UniProt {acc}](https://www.uniprot.org/uniprotkb/{acc})*"
            )

    return "\n".join(lines)


def _lookup_pathway(name: str) -> str:
    """KEGG-Stoffwechselwege — Thema "pathway" von `lookup`."""
    kegg_id = kegg_find(name)
    if kegg_id is None:
        return f"'{name}' nicht in KEGG gefunden."

    data = kegg_compound(kegg_id)
    lines = [f"## {name} — KEGG Stoffwechseldaten\n"]
    lines.append(f"- **KEGG-ID:** {data['id']}")
    if data["names"]:
        lines.append(f"- **Namen:** {', '.join(data['names'][:5])}")
    if data["formula"]:
        lines.append(f"- **Formel:** {data['formula']}")

    if data["pathways"]:
        lines.append(f"\n### Stoffwechselwege ({len(data['pathways'])})\n")
        for pw in data["pathways"][:10]:
            pw_id = pw.replace("path:", "")
            lines.append(f"- [{pw_id}](https://www.kegg.jp/pathway/{pw_id})")
        if len(data["pathways"]) > 10:
            lines.append(f"- ... und {len(data['pathways']) - 10} weitere")
    else:
        lines.append("\nKeine Stoffwechselwege verknüpft.")

    lines.append(
        f"\n*Quelle: [KEGG {data['id']}](https://www.kegg.jp/entry/{data['id']})*"
    )
    return "\n".join(lines)


@mcp.tool(structured_output=True, meta=_UI_META)
def lookup_molecule_data(name: str) -> DatabasePayload:
    """Show a compound's data sheet as a panel: structure plus grouped facts.

    Aggregates PubChem properties and GHS safety into one panel with the
    drawn structure beside them, grouped by source. Use it when the request
    asks for a data sheet, an overview or "all the data" on a substance.

    Not this tool for: a bare compound name with no data asked for — that
    means show the substance, use generate_molecule. Nor for a single fact in
    text form, or the topics this does not cover (physical constants,
    biochem, pathways) — that is lookup.

    IMPORTANT: Always pass English or IUPAC compound names, never localized
    names ('Aspirin' not 'Acetylsalicylsäure'). SMILES are always safe.

    Args:
        name: English/IUPAC compound name or SMILES (e.g. 'Aspirin').
    """
    from chemdraw_tool.svg_renderer import render_svg

    # Resolve & render SVG (thumbnail size for DatabaseView sidebar)
    _, mol = resolve(name)
    mol = generate_2d(mol)
    svg = render_svg(mol, width=150, height=120, fill_container=True)

    sources: list[DatabaseSource] = []

    # --- PubChem properties source ---
    props = pubchem_properties(name) or {}
    cid_raw = props.get("CID")
    try:
        cid_int = int(cid_raw) if cid_raw else None
    except (ValueError, TypeError):
        cid_int = None
    cid_str = str(cid_int) if cid_int else ""

    pubchem_rows: list[DatabaseRow] = []
    if cid_str:
        pubchem_rows.append(DatabaseRow(key="CID", val=cid_str))
    if (v := props.get("IUPACName")) is not None:
        pubchem_rows.append(DatabaseRow(key="IUPAC-Name", val=v))
    if (v := props.get("MolecularFormula")) is not None:
        pubchem_rows.append(DatabaseRow(key="Summenformel", val=v))
    if (v := props.get("MolecularWeight")) is not None:
        pubchem_rows.append(DatabaseRow(key="Molmasse", val=f"{v} g/mol"))
    if (v := props.get("XLogP")) is not None:
        pubchem_rows.append(DatabaseRow(key="LogP", val=str(v)))
    if (v := props.get("TPSA")) is not None:
        pubchem_rows.append(DatabaseRow(key="TPSA", val=f"{v} Å²"))
    if (v := props.get("HBondDonorCount")) is not None:
        pubchem_rows.append(DatabaseRow(key="H-Brücken-Donoren", val=str(v)))
    if (v := props.get("HBondAcceptorCount")) is not None:
        pubchem_rows.append(DatabaseRow(key="H-Brücken-Akzeptoren", val=str(v)))
    if (v := props.get("InChIKey")) is not None:
        pubchem_rows.append(DatabaseRow(key="InChIKey", val=v))
    cas_nr, _ = pubchem_synonyms(name)
    if cas_nr:
        pubchem_rows.append(DatabaseRow(key="CAS-Nr.", val=cas_nr))

    sources.append(
        DatabaseSource(
            type="PubChem",
            source=f"PubChem CID {cid_str}" if cid_str else "PubChem",
            url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid_str}"
            if cid_str
            else "https://pubchem.ncbi.nlm.nih.gov",
            rows=pubchem_rows,
        )
    )

    # --- GHS safety source (reuses CID from properties, no extra network call) ---
    if cid_int:
        safety = pubchem_safety(cid_int)
        if safety:
            safety_rows = [
                DatabaseRow(key=e["name"], val=e["value"])
                for e in safety
                if e.get("value")
            ]
            sources.append(
                DatabaseSource(
                    type="GHS",
                    source=f"PubChem CID {cid_int} — Safety",
                    url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid_int}#section=Safety-and-Hazards",
                    rows=safety_rows,
                )
            )

    return DatabasePayload(
        type="database",
        molecule_svg=svg,
        sources=sources,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_reaction(
    reactants: list[str],
    products: list[str],
    conditions: str = "",
    name: str = "",
    formats: list[str] | None = None,
    abbreviate_groups: bool = False,
    render_style: str = "",
) -> ReactionPayload:
    """Generate a reaction scheme (educts → products) as image files.

    Writes the scheme as PNG and/or SVG (default both) to the output folder —
    no ChemDraw required. Conditions appear above the arrow in the UI preview.

    Use this when the user describes a chemical reaction with educts and products.

    Not this tool for: the step-by-step course with electron-flow arrows —
    that is generate_mechanism. Also not for many products of one reaction
    with yields (generate_scope_table).

    IMPORTANT: Always pass English or IUPAC compound names, never localized
    names. For example use 'Aspirin' not 'Acetylsalicylsäure', 'Caffeine'
    not 'Coffein'. SMILES strings are always safe.

    Args:
        reactants: List of English/IUPAC reactant names or SMILES strings.
        products: List of English/IUPAC product names or SMILES strings.
        conditions: Reaction conditions shown above the arrow (e.g. 'HCl, 0-5 °C').
        name: Display name for the reaction step (can be localized).
        formats: Output file formats, any of "png", "svg", "cdxml"
            (default: ["png", "svg"]). Include "cdxml" ONLY when the user
            wants to edit the scheme in ChemDraw or asks to open it there.
        abbreviate_groups: Set True to draw common substituents as short labels
            (Ph, Bn, OAc, OMe, CO2H, tBu, Boc, Ts …) instead of full skeletons.
            Keeps a multi-step scheme narrow enough to stay readable. The
            CDXML export still contains the full structures.
        render_style: Named look for the scheme. Empty = standard style.
            "compact" = thin bonds and tight margins for a small printed
            figure, "presentation" = thick bonds and large labels for slides,
            "grayscale" = black-and-white atom palette for grayscale printing.
    """
    from chemdraw_tool.svg_renderer import render_svg

    fmts = _normalize_formats(formats)
    get_style(render_style)  # unbekannter Stil: scheitern, bevor Dateien entstehen

    reactant_mols = []
    for r in reactants:
        _, mol = resolve(r)
        mol = generate_2d(mol)
        input_issues = validate_input(mol)
        for issue in input_issues:
            if issue.severity == Severity.ERROR:
                raise ValueError(f"Reactant '{r}' validation failed: {issue.message}")
        reactant_mols.append(mol)

    product_mols = []
    for p in products:
        _, mol = resolve(p)
        mol = generate_2d(mol)
        input_issues = validate_input(mol)
        for issue in input_issues:
            if issue.severity == Severity.ERROR:
                raise ValueError(f"Product '{p}' validation failed: {issue.message}")
        product_mols.append(mol)

    slug = _slugify(name or "reaktion")
    out_dir = REACTION_DIR / slug

    # Abkürzen betrifft nur die Zeichnung — das CDXML unten wird aus den
    # vollen Molekülen geschrieben.
    if abbreviate_groups:
        drawn_reactants = [condense_groups(m) for m in reactant_mols]
        drawn_products = [condense_groups(m) for m in product_mols]
    else:
        drawn_reactants, drawn_products = reactant_mols, product_mols

    artifacts: dict[str, bytes | str] = {}
    if "png" in fmts:
        artifacts["png"] = render_reaction_png(
            drawn_reactants, drawn_products, conditions, style=render_style
        )
    if "svg" in fmts:
        artifacts["svg"] = render_reaction_svg(
            drawn_reactants, drawn_products, conditions, style=render_style
        )
    files = write_files(out_dir / slug, artifacts)

    cdxml_path = ""
    if "cdxml" in fmts:
        out_dir.mkdir(parents=True, exist_ok=True)
        filepath = out_dir / f"{slug}.cdxml"
        write_reaction_cdxml(
            reactant_mols,
            product_mols,
            str(filepath),
            conditions=conditions,
            name=name,
            reactant_names=reactants,
            product_names=products,
        )
        cdxml_path = str(filepath)
        files["cdxml"] = cdxml_path

    r_w, r_h = 250, 200
    from chemdraw_tool.payloads import MolEntry

    return ReactionPayload(
        type="reaction",
        name=name,
        conditions=conditions,
        reactants=[
            MolEntry(svg=render_svg(m, r_w, r_h, style=render_style), name=n)
            for m, n in zip(drawn_reactants, reactants)
        ],
        products=[
            MolEntry(svg=render_svg(m, r_w, r_h, style=render_style), name=n)
            for m, n in zip(drawn_products, products)
        ],
        files=files,
        cdxml_path=cdxml_path,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def batch_generate(
    molecules: list[str],
    formats: list[str] | None = None,
    annotate_stereo: bool = False,
    abbreviate_groups: bool = False,
    render_style: str = "",
) -> BatchPayload:
    """Generate multiple molecule structure drawings at once.

    Writes image files (PNG and/or SVG, default both) per molecule — no
    ChemDraw required. Failed names are skipped and reported in `failed`.

    Use this when the user wants several individual structures generated
    in one step (e.g. 'Draw Aspirin, Paracetamol and Ibuprofen').

    Not this tool for: ONE molecule — that is generate_molecule. Also not
    for products of one reaction with yields (generate_scope_table) or for
    contrasting structures (compare_molecules).

    IMPORTANT: Always pass English or IUPAC compound names, never localized
    names. For example use 'Aspirin' not 'Acetylsalicylsäure', 'Caffeine'
    not 'Coffein', 'Ascorbic acid' not 'Ascorbinsäure'. SMILES strings are
    always safe.

    Args:
        molecules: List of English/IUPAC compound names or SMILES strings.
        formats: Output file formats, any of "png", "svg", "cdxml"
            (default: ["png", "svg"]). Include "cdxml" ONLY when the user
            wants to edit the structures in ChemDraw.
        abbreviate_groups: Set True to draw common substituents as short labels
            (Ph, Bn, OAc, OMe, CO2H, tBu, Boc, Ts …) instead of full skeletons.
            Applies to every molecule in the batch, so a series of structures
            stays visually consistent.
        render_style: Named look applied to every molecule in the batch. Empty
            = standard style. "compact" for small printed figures,
            "presentation" for slides, "grayscale" for grayscale printing.
    """
    import logging

    from chemdraw_tool.svg_renderer import (
        extract_atom_data,
        extract_functional_groups,
        render_svg,
    )

    fmts = _normalize_formats(formats)
    get_style(render_style)  # unbekannter Stil: scheitern, bevor Dateien entstehen

    mol_payloads = []
    cdxml_paths = []
    failed = []

    for name_or_smiles in molecules:
        try:
            smiles, mol = resolve(name_or_smiles)
        except Exception:
            logging.getLogger(__name__).warning(
                "Could not resolve %r, skipping", name_or_smiles
            )
            failed.append(name_or_smiles)
            continue

        mol = generate_2d(mol)

        input_issues = validate_input(mol)
        if any(i.severity == Severity.ERROR for i in input_issues):
            logging.getLogger(__name__).warning(
                "Input validation failed for %r, skipping", name_or_smiles
            )
            failed.append(name_or_smiles)
            continue

        display_name = name_or_smiles
        slug = _slugify(display_name)
        drawn = condense_groups(mol) if abbreviate_groups else mol

        files, cdxml_path = _write_structure_files(
            mol,
            slug,
            display_name,
            fmts,
            annotate_stereo=annotate_stereo,
            render_mol=drawn,
            style=render_style,
        )
        if cdxml_path:
            cdxml_paths.append(cdxml_path)

        properties = _enrich_properties(smiles)
        fg_raw = extract_functional_groups(mol)
        groups = [FunctionalGroup(**g) for g in fg_raw]
        lipinski = _build_lipinski(properties)

        mol_payloads.append(
            MoleculePayload(
                type="molecule",
                svg=render_svg(
                    drawn,
                    fill_container=True,
                    annotate_stereo=annotate_stereo,
                    style=render_style,
                ),
                atoms=[] if abbreviate_groups else extract_atom_data(mol),
                name=display_name,
                properties=properties,
                functionalGroups=groups,
                lipinski=lipinski,
                files=files,
                cdxml_path=cdxml_path,
            )
        )

    return BatchPayload(
        type="batch",
        molecules=mol_payloads,
        cdxml_paths=cdxml_paths,
        failed=failed,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def generate_mechanism(
    reaction_type: str,
    substrates: list[str],
    current_step: int = 0,
) -> MechanismPayload:
    """Generate a step-by-step reaction mechanism visualization.

    Use this when the user asks about a reaction mechanism, electron-flow
    arrows, or wants to see how a reaction proceeds step by step.

    Not this tool for: the net equation educt → product without
    intermediates — that is generate_reaction. Only the mechanism types
    listed in reaction_type exist; for anything else use generate_reaction.

    Args:
        reaction_type: Mechanism type (e.g. "sn2", "sn1", "fischer_ester").
        substrates: List of substrate SMILES or names.
        current_step: 0 = overview (all steps), 1-N = specific step.
    """
    from chemdraw_tool.mechanism import validate_substrates
    from chemdraw_tool.mechanism_coords import stabilize_sequence
    from chemdraw_tool.mechanism_renderer import render_step_svg
    from chemdraw_tool.templates import get_template, list_templates

    template = get_template(reaction_type)
    if template is None:
        available = ", ".join(list_templates())
        raise ValueError(
            f"Reaktionstyp '{reaction_type}' nicht gefunden. "
            f"Verfügbare Typen: {available}"
        )

    resolved = []
    for s in substrates:
        try:
            smi, _mol = resolve(s)
            resolved.append(smi)
        except Exception:
            resolved.append(s)

    if not validate_substrates(template, resolved):
        raise ValueError(
            f"Substrate passen nicht zum Reaktionstyp '{reaction_type}'. "
            f"Erwartet: Substrat-Pattern '{template.substrate_pattern}'"
            + (
                f", Nucleophil-Pattern '{template.nucleophile_pattern}'"
                if template.nucleophile_pattern
                else ""
            )
        )

    steps_smiles = [step.molecules for step in template.steps]
    stabilized = stabilize_sequence(steps_smiles)

    if not stabilized:
        raise ValueError(
            f"Reaktionstyp '{reaction_type}' hat keine Schritte definiert."
        )

    step_payloads = []
    for step, mols in zip(template.steps, stabilized):
        svg = render_step_svg(step, mols)
        step_payloads.append(
            MechanismStepPayload(
                svg=svg,
                label=step.label,
                is_transition_state=step.is_transition_state,
            )
        )

    substrate_names = " + ".join(resolved[:2])
    display_name = f"{template.name}: {substrate_names}"

    clamped_step = max(0, min(current_step, len(step_payloads)))

    return MechanismPayload(
        type="mechanism",
        name=display_name,
        reaction_type=reaction_type,
        steps=step_payloads,
        current_step=clamped_step,
    )


@mcp.tool()
def save_png(png_base64: str, filename: str) -> str:
    """Internal helper for the panel UI — never call this directly.

    The panel's export button calls it when the image clipboard is blocked
    by the sandbox; saving a picture is the user's click, not yours. The
    generate_* tools already write their PNG and SVG files themselves.

    Expects a base64 PNG (with or without a `data:image/png;base64,`
    prefix) and returns the path it was written to.
    """
    from chemdraw_tool.png_writer import save_png_bytes

    png_dir = Path.home() / "ChemDraw-Output" / "png"
    try:
        path = save_png_bytes(png_base64, filename, png_dir)
    except (ValueError, OSError) as exc:
        return f"Fehler: {exc}"
    return str(path)


if vault_enabled():

    @mcp.tool()
    def search_vault(query: str) -> str:
        """Search the configured local knowledge vault.

        Optional, opt-in feature. Enabled via CHEMDRAW_VAULT_PATH env var.
        For most users, materials live in Claude Projects instead.

        Args:
            query: Search term.
        """
        results = search(query)
        if not results:
            entries = list_entries()
            lines = [f"Keine Treffer für '{query}'.\n"]
            lines.append("**Verfügbare Einträge:**\n")
            for cat, names in sorted(entries.items()):
                lines.append(f"### {cat}")
                for name in names:
                    lines.append(f"- {name}")
                lines.append("")
            return "\n".join(lines)

        lines = [f"## Suchergebnisse für '{query}'\n"]
        for r in results:
            lines.append(f"### {r['name']} ({r['category']})")
            lines.append(f"*Pfad: {r['path']}*")
            if r["snippet"]:
                lines.append(f"\n> {r['snippet']}\n")
            lines.append(
                f'→ `read_vault_entry("{r["name"]}")` für vollständigen Inhalt\n'
            )
        return "\n".join(lines)

    @mcp.tool()
    def read_vault_entry(name: str) -> str:
        """Read a specific entry from the configured local vault.

        Args:
            name: Entry name.
        """
        entry_name, content = read_entry(name)
        if content is None:
            entries = list_entries()
            lines = [f"Eintrag '{name}' nicht gefunden.\n"]
            lines.append("**Verfügbare Einträge:**\n")
            for cat, names in sorted(entries.items()):
                lines.append(f"### {cat}")
                for name in names:
                    lines.append(f"- {name}")
                lines.append("")
            return "\n".join(lines)

        return f"# {entry_name}\n\n{content}"


def main():
    import logging

    log_path = Path.home() / "ChemDraw-Output" / "server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(str(log_path))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logging.getLogger().addHandler(fh)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger(__name__).info("MCP server starting")
    mcp.run(transport="stdio")
