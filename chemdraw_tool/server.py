import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from chemdraw_tool.auth import (
    verify_jwt_token,
    verify_api_key,
    optional_auth,
    get_valid_api_keys,
)
from chemdraw_tool.auth.config import validate_config, CONFIG_DIR
from chemdraw_tool.cdxml_writer import write_cdxml
from chemdraw_tool.chemdraw import find_chemdraw, open_in_chemdraw
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
    CalculationStep,
    DatabasePayload,
    DatabaseRow,
    DatabaseSource,
    FunctionalGroup,
    LipinskiData,
    MechanismPayload,
    MechanismStepPayload,
    MethodComparison,
    MethodResult,
    Molecule3DPayload,
    MoleculePayload,
    PlotPayload,
    ReactionPayload,
    SpectrumPayload,
    SpectrumPeak,
    ValidationPayload,
)
from chemdraw_tool.resolver import resolve
from chemdraw_tool.spectrum import (
    SPECTRUM_TYPES,
    render_spectrum_png,
    render_spectrum_svg,
)
from chemdraw_tool.validator import Severity, validate_input, validate_roundtrip
from chemdraw_tool.vault import is_enabled as vault_enabled
from chemdraw_tool.vault import list_entries, read_entry, search

OUTPUT_DIR = Path.home() / "ChemDraw-Output" / "einzelmolekuele"
REACTION_DIR = Path.home() / "ChemDraw-Output"
SPECTRUM_DIR = Path.home() / "ChemDraw-Output" / "spektren"
ANKI_DIR = Path.home() / "ChemDraw-Output" / "anki"
PLOT_DIR = Path.home() / "ChemDraw-Output" / "diagramme"
THREED_DIR = Path.home() / "ChemDraw-Output" / "3d"

# PNG/SVG sind die Primärformate (laufen ohne ChemDraw); CDXML ist das
# optionale Zusatzformat für Nutzer, die in ChemDraw weiterbearbeiten wollen.
VALID_FORMATS = ("png", "svg", "cdxml")
DEFAULT_FORMATS = ("png", "svg")


def _normalize_formats(formats: list[str] | None) -> list[str]:
    fmts = [f.lower().strip() for f in (formats or DEFAULT_FORMATS)]
    unknown = sorted(set(fmts) - set(VALID_FORMATS))
    if unknown:
        raise ValueError(
            f"Unbekannte Formate: {unknown} — erlaubt sind {list(VALID_FORMATS)}"
        )
    return fmts


def _write_structure_files(
    mol, slug: str, display_name: str, formats: list[str], annotate_stereo: bool = False
) -> tuple[dict[str, str], str]:
    """Schreibt die angeforderten Dateiformate für ein Einzelmolekül.

    Returns ({format: pfad}, cdxml_path) — cdxml_path ist "" wenn kein CDXML
    angefordert wurde. Die CDXML-Roundtrip-Validierung läuft nur, wenn CDXML
    tatsächlich erzeugt wird.
    """
    import logging

    artifacts: dict[str, bytes | str] = {}
    if "png" in formats:
        artifacts["png"] = render_molecule_png(
            mol, legend=display_name, annotate_stereo=annotate_stereo
        )
    if "svg" in formats:
        artifacts["svg"] = render_molecule_svg(
            mol, legend=display_name, annotate_stereo=annotate_stereo
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


mcp = FastMCP("ChemDraw Tool")

# ---------------------------------------------------------------------------
# Authentication Configuration
# ---------------------------------------------------------------------------

# Try to validate authentication configuration
# If CHEMDRAW_SECRET_KEY is not set, authentication will be disabled
_AUTH_ENABLED = False
try:
    validate_config()
    _AUTH_ENABLED = True
    logger = __import__('logging').getLogger(__name__)
    logger.info("Authentication is ENABLED")
except (ValueError, RuntimeError) as e:
    logger = __import__('logging').getLogger(__name__)
    logger.warning("Authentication is DISABLED: %s", e)

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


# ---------------------------------------------------------------------------
# Authentication Tools (only available when auth is enabled)
# ---------------------------------------------------------------------------

if _AUTH_ENABLED:
    from chemdraw_tool.auth.tokens import create_access_token, create_refresh_token
    from chemdraw_tool.auth.config import add_api_key, get_valid_api_keys, remove_api_key
    from pydantic import BaseModel
    from typing import Optional
    
    class TokenRequest(BaseModel):
        """Request model for token creation."""
        subject: str
        username: Optional[str] = None
        role: Optional[str] = None
        
    class TokenResponse(BaseModel):
        """Response model for token creation."""
        access_token: str
        refresh_token: Optional[str] = None
        token_type: str = "bearer"
        expires_in: int
        
    class APIKeyRequest(BaseModel):
        """Request model for API key management."""
        key: str
        
    class APIKeyListResponse(BaseModel):
        """Response model for API key list."""
        api_keys: list[str]
        count: int
    
    @mcp.tool()
    def create_auth_token(
        subject: str,
        username: Optional[str] = None,
        role: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> TokenResponse:
        """Create a new authentication token for API access.
        
        This tool creates JWT tokens that can be used to authenticate
        requests to the ChemDraw MCP server when running with Mistral AI Vibe.
        
        Args:
            subject: Unique identifier for the token holder (e.g., user ID or username).
            username: Optional display name for the user.
            role: Optional role for the user (e.g., 'admin', 'user').
            expires_in: Optional expiration time in minutes. Defaults to 30 minutes.
        
        Returns:
            TokenResponse: Contains the access token and optional refresh token.
        
        Example:
            create_auth_token(subject="user123", role="admin")
        """
        data = {"sub": subject}
        if username:
            data["username"] = username
        if role:
            data["role"] = role
        
        access_token = create_access_token(data, expires_delta=expires_in)
        refresh_token = create_refresh_token(data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in or 30,
        )
    
    @mcp.tool()
    def add_api_key(key: str) -> dict:
        """Add a new API key for authentication.
        
        API keys can be used as an alternative to JWT tokens for authentication.
        Once added, the key can be used in the Authorization header as:
        Authorization: Bearer <api-key>
        
        Args:
            key: The API key to add.
        
        Returns:
            dict: Confirmation message.
        """
        add_api_key(key)
        return {"status": "success", "message": "API key added", "key": key[:8] + "..."}
    
    @mcp.tool()
    def list_api_keys() -> APIKeyListResponse:
        """List all configured API keys.
        
        Returns:
            APIKeyListResponse: List of API keys (only first 8 characters shown for security).
        """
        keys = get_valid_api_keys()
        # Only show first 8 characters for security
        masked_keys = [k[:8] + "..." if len(k) > 8 else k for k in keys]
        return APIKeyListResponse(api_keys=masked_keys, count=len(keys))
    
    @mcp.tool()
    def remove_api_key(key: str) -> dict:
        """Remove an API key.
        
        Args:
            key: The API key to remove.
        
        Returns:
            dict: Confirmation message.
        """
        if remove_api_key(key):
            return {"status": "success", "message": "API key removed"}
        else:
            return {"status": "error", "message": "API key not found"}
    
    @mcp.tool()
    def get_auth_status() -> dict:
        """Get the current authentication status.
        
        Returns:
            dict: Authentication configuration status.
        """
        return {
            "auth_enabled": _AUTH_ENABLED,
            "api_keys_count": len(get_valid_api_keys()),
            "algorithm": "HS256",
            "token_expiration_minutes": 30,
        }


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
) -> MoleculePayload:
    """Generate a 2D molecular structure drawing from a name or SMILES string.

    Writes print-ready image files (PNG and/or SVG, default both) to the
    output folder and returns a structured payload with an SVG preview,
    properties and functional groups. Works fully standalone — no ChemDraw
    installation required.

    Use this tool when the user mentions structural formulas, molecular
    structures, or chemical drawings.

    IMPORTANT: Always pass English or IUPAC compound names, never localized
    names. For example use 'Aspirin' not 'Acetylsalicylsäure', 'Caffeine'
    not 'Coffein', 'Ascorbic acid' not 'Ascorbinsäure'. SMILES strings are
    always safe. Use the label parameter for the localized display name.

    Args:
        name_or_smiles: English/IUPAC compound name or SMILES string.
        label: Optional display name (can be localized, shown below structure).
        formats: Output file formats, any of "png", "svg", "cdxml"
            (default: ["png", "svg"]). Include "cdxml" ONLY when the user
            wants to edit the structure in ChemDraw or asks to open it there.
        annotate_stereo: Set True to print CIP stereo descriptors (R/S, E/Z)
            at each stereocenter — useful for stereochemistry teaching.
    """
    from chemdraw_tool.svg_renderer import (
        extract_atom_data,
        extract_functional_groups,
        render_svg,
    )

    fmts = _normalize_formats(formats)

    smiles, mol = resolve(name_or_smiles)
    mol = generate_2d(mol)

    input_issues = validate_input(mol)
    for issue in input_issues:
        if issue.severity == Severity.ERROR:
            raise ValueError(f"Input validation failed: {issue.message}")

    display_name = label or name_or_smiles
    slug = _slugify(display_name)

    files, cdxml_path = _write_structure_files(
        mol, slug, display_name, fmts, annotate_stereo=annotate_stereo
    )

    properties = _enrich_properties(smiles)
    fg_raw = extract_functional_groups(mol)
    groups = [FunctionalGroup(**g) for g in fg_raw]
    lipinski = _build_lipinski(properties)

    return MoleculePayload(
        type="molecule",
        svg=render_svg(mol, fill_container=True, annotate_stereo=annotate_stereo),
        atoms=extract_atom_data(mol),
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
def export_anki_deck(
    deck_name: str,
    cards: list[AnkiCard],
    default_tags: list[str] | None = None,
    deliver: str = "apkg",
) -> AnkiDeckPayload:
    """Export an Anki flashcard deck (.apkg) with rendered chemistry images.

    Use this whenever the user wants flashcards, Anki cards or a study deck
    for molecules, reactions (e.g. pharmacopoeia identity tests) or spectra.

    The tool renders the images reliably — YOU supply the card content from
    your knowledge, like with generate_spectrum. Each card side carries text
    plus at most ONE visual: structure (compound name or SMILES), reaction
    ({reactants, products, conditions}) or spectrum ({spectrum_type, peaks,
    title}). Proven card types: structure↔name in either direction,
    identity/detection reactions (question on the front, scheme on the
    back), functional-group recognition, spectrum band assignment,
    trivial↔IUPAC name drills.

    Re-exporting a deck under the SAME name updates existing cards in Anki
    instead of duplicating them — card fronts identify the cards, so
    corrected backs replace the old answers.

    Card options: set reversed=true on a card to also drill the opposite
    direction (one note, two cards); set cloze=true for fill-in-the-blank
    cards (front.text carries {{c1::...}} gaps, back.text becomes the
    extra note). Use "Parent::Child" deck names for Anki subdecks.

    IMPORTANT: structures take English/IUPAC names or SMILES; the card
    TEXTS can be localized freely (e.g. German). Never deliver via
    AnkiConnect unless the user explicitly asked for it.

    Args:
        deck_name: Anki deck name, also used for the filename. "::" nests
            subdecks. Re-use the exact same name to update a deck.
        cards: The flashcards. Keep fronts unambiguous; explanations belong
            on the back. tags/reversed/cloze are per-card options.
        default_tags: Tags added to every card in the deck.
        deliver: "apkg" (default — file only) or "ankiconnect" (additionally
            imports into the RUNNING Anki via the AnkiConnect add-on;
            requires the user to have it installed).
    """
    from chemdraw_tool.anki_export import write_deck

    if not cards:
        raise ValueError("Das Deck braucht mindestens eine Karte.")

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
def export_curated_deck(deck_id: str) -> AnkiDeckPayload:
    """Export one of the small, curated Anki starter decks (.apkg).

    Curated and formula-verified content (textbook classics only):
    - "analgesics-structures": structure → name drills for 8 classic
      analgesics (NSAIDs, paracetamol, morphine, celecoxib).
    - "pheur-identity-basics": classic Ph.Eur. identity tests — reagent,
      observation and reaction scheme where it helps.

    Use this when the user wants a ready-made starter deck. For custom
    content, build cards yourself and call export_anki_deck instead.

    Args:
        deck_id: "analgesics-structures" or "pheur-identity-basics".
    """
    from chemdraw_tool.anki_export import write_deck
    from chemdraw_tool.curated_decks import get_curated_deck

    deck_name, cards = get_curated_deck(deck_id)
    out_path = ANKI_DIR / f"{_slugify(deck_name)}.apkg"
    stats = write_deck(deck_name, cards, out_path)
    return AnkiDeckPayload(
        name=deck_name,
        cards=stats["cards"],
        media=stats["media"],
        fronts=[c.front.text or c.front.structure for c in cards],
        file=str(out_path),
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


@mcp.tool()
def lookup_compound(name: str) -> str:
    """Look up chemical compound properties from PubChem.

    Use this when the user asks about properties, molecular weight,
    formula, CAS number, or general information about a chemical compound.
    Returns verified data from PubChem with source citation.

    Args:
        name: Compound name (e.g. 'Aspirin', 'Sulfanilsäure', 'Histidin').
    """
    lines = [f"## {name} — PubChem-Daten\n"]
    cid = "?"

    props = pubchem_properties(name)
    if props:
        cid = props.get("CID", "?")
        lines.append("| Eigenschaft | Wert |")
        lines.append("|------------|------|")
        lines.append(f"| **CID** | {cid} |")
        if v := props.get("IUPACName"):
            lines.append(f"| **IUPAC-Name** | {v} |")
        if v := props.get("MolecularFormula"):
            lines.append(f"| **Summenformel** | {v} |")
        if v := props.get("MolecularWeight"):
            lines.append(f"| **Molmasse** | {v} g/mol |")
        if v := props.get("ExactMass"):
            lines.append(f"| **Exakte Masse** | {v} |")
        if v := props.get("XLogP"):
            lines.append(f"| **LogP** | {v} |")
        if v := props.get("TPSA"):
            lines.append(f"| **Polare Oberfläche** | {v} Å² |")
        if v := props.get("HBondDonorCount"):
            lines.append(f"| **H-Brücken-Donoren** | {v} |")
        if v := props.get("HBondAcceptorCount"):
            lines.append(f"| **H-Brücken-Akzeptoren** | {v} |")
        if v := props.get("InChIKey"):
            lines.append(f"| **InChIKey** | {v} |")
        charge = props.get("Charge")
        if charge and charge != 0:
            lines.append(f"| **Ladung** | {charge} |")
    else:
        lines.append("Eigenschaften konnten nicht abgerufen werden.")

    cas, synonyms = pubchem_synonyms(name)
    if cas:
        lines.append(f"| **CAS-Nr.** | {cas} |")
    if synonyms:
        filtered = [s for s in synonyms if s.lower() != name.lower()][:5]
        if filtered:
            lines.append(f"\n**Synonyme:** {', '.join(filtered)}")

    lines.append(
        f"\n*Quelle: [PubChem CID {cid}]"
        f"(https://pubchem.ncbi.nlm.nih.gov/compound/{cid})*"
    )
    return "\n".join(lines)


@mcp.tool()
def lookup_safety(name: str) -> str:
    """Look up GHS safety data for a chemical compound.

    Use this when the user asks about safety, hazards, H-Sätze, P-Sätze,
    GHS pictograms, or needs safety info for a lab protocol.

    Args:
        name: Compound name.
    """
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


@mcp.tool()
def lookup_physical(name: str) -> str:
    """Look up physical properties of a compound (melting point, boiling point,
    solubility, density).

    Use this when the user asks about physical properties, aggregation state,
    or needs data for substance identification.

    Args:
        name: Compound name.
    """
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


@mcp.tool()
def lookup_biochem(name: str) -> str:
    """Look up biochemical classification from ChEBI and related enzyme/protein
    info from UniProt.

    Use this when the user asks what type of compound something is, its
    biological role, or related enzymes.

    Args:
        name: Compound or enzyme name.
    """
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


@mcp.tool()
def lookup_pathway(name: str) -> str:
    """Look up metabolic pathways for a compound from KEGG.

    Use this when the user asks where a compound appears in metabolism,
    which pathways it belongs to, or its biological context.

    Args:
        name: Compound name.
    """
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
    """Look up aggregated molecule data (PubChem + GHS safety) for the DatabaseView UI.

    Use this when the user wants a structured overview of a compound's properties
    and safety information in the UI panel. Returns SVG structure plus all relevant
    database rows grouped by source.

    Args:
        name: Compound name or SMILES string (e.g. 'Aspirin', 'Paracetamol').
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
) -> ReactionPayload:
    """Generate a reaction scheme (educts → products) as image files.

    Writes the scheme as PNG and/or SVG (default both) to the output folder —
    no ChemDraw required. Conditions appear above the arrow in the UI preview.

    Use this when the user describes a chemical reaction with educts and products.

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
    """
    from chemdraw_tool.svg_renderer import render_svg

    fmts = _normalize_formats(formats)

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

    artifacts: dict[str, bytes | str] = {}
    if "png" in fmts:
        artifacts["png"] = render_reaction_png(reactant_mols, product_mols, conditions)
    if "svg" in fmts:
        artifacts["svg"] = render_reaction_svg(reactant_mols, product_mols, conditions)
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
            MolEntry(svg=render_svg(m, r_w, r_h), name=n)
            for m, n in zip(reactant_mols, reactants)
        ],
        products=[
            MolEntry(svg=render_svg(m, r_w, r_h), name=n)
            for m, n in zip(product_mols, products)
        ],
        files=files,
        cdxml_path=cdxml_path,
    )


@mcp.tool(structured_output=True, meta=_UI_META)
def batch_generate(
    molecules: list[str],
    formats: list[str] | None = None,
    annotate_stereo: bool = False,
) -> BatchPayload:
    """Generate multiple molecule structure drawings at once.

    Writes image files (PNG and/or SVG, default both) per molecule — no
    ChemDraw required. Failed names are skipped and reported in `failed`.

    Use this when the user wants several individual structures generated
    in one step (e.g. 'Draw Aspirin, Paracetamol and Ibuprofen').

    IMPORTANT: Always pass English or IUPAC compound names, never localized
    names. For example use 'Aspirin' not 'Acetylsalicylsäure', 'Caffeine'
    not 'Coffein', 'Ascorbic acid' not 'Ascorbinsäure'. SMILES strings are
    always safe.

    Args:
        molecules: List of English/IUPAC compound names or SMILES strings.
        formats: Output file formats, any of "png", "svg", "cdxml"
            (default: ["png", "svg"]). Include "cdxml" ONLY when the user
            wants to edit the structures in ChemDraw.
    """
    import logging

    from chemdraw_tool.svg_renderer import (
        extract_atom_data,
        extract_functional_groups,
        render_svg,
    )

    fmts = _normalize_formats(formats)

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

        files, cdxml_path = _write_structure_files(
        mol, slug, display_name, fmts, annotate_stereo=annotate_stereo
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
                svg=render_svg(mol, fill_container=True, annotate_stereo=annotate_stereo),
                atoms=extract_atom_data(mol),
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


@mcp.tool(structured_output=True, meta=_UI_META)
def calculate_validation(
    variante: str,
    wahrer_wert: float,
    acid_einwaagen: list[float],
    acid_volumina: list[float],
    acid_referenz_einwaagen: list[float],
    acid_referenz_volumina: list[float],
    acid_blindwert: float,
    uv_einwaagen: list[float] | None = None,
    uv_absorptionen: list[float] | None = None,
    uv_verduennungsfaktor: float = 100.0,
    uv_kolbenvolumen_ml: float = 100.0,
) -> ValidationPayload:
    """Calculate the complete Rechenweg for a validation experiment (Analyse 5).

    Compares two analytical methods (UV/HPLC vs. Acidimetry) using
    F-test and Welch t-test. Returns structured results with step-by-step
    calculations and explanations.

    Use this when the user provides measurement data for a validation
    experiment and wants the Rechenweg, statistics, and method comparison.

    Args:
        variante: "A" (HPLC/Ibuprofen) or "B" (UV/Ascorbinsäure).
        wahrer_wert: True value in % (given by the lab).
        acid_einwaagen: Weighings for analyses 1-6 in mg (Acidimetry).
        acid_volumina: Titration volumes for analyses 1-6 in mL.
        acid_referenz_einwaagen: Weighings for references 1+2 in mg.
        acid_referenz_volumina: Titration volumes for references 1+2 in mL.
        acid_blindwert: Blank titration volume in mL.
        uv_einwaagen: (Variante B) Weighings in mg for UV measurements.
        uv_absorptionen: (Variante B) Measured absorptions.
        uv_verduennungsfaktor: Total dilution factor for UV measurement (default 100).
        uv_kolbenvolumen_ml: Volumetric flask volume in mL (default 100).
    """
    from chemdraw_tool.calculator.stats import (
        descriptive_stats,
        f_test,
        one_sample_t_test,
        welch_t_test,
    )
    from chemdraw_tool.calculator.titration import (
        SUBSTANCE_FACTORS,
        calculate_gehalt_titration,
        calculate_titer,
    )

    variante = variante.upper()
    if variante == "B":
        substance = "Ascorbinsäure"
        substance_key = "ascorbinsaeure"
    elif variante == "A":
        raise ValueError(
            "Variante A (HPLC/Ibuprofen) ist noch nicht implementiert. "
            "Aktuell wird nur Variante B (UV/Ascorbinsäure) unterstützt."
        )
    else:
        raise ValueError(
            f"Unbekannte Variante '{variante}'. Aktuell nur 'B' unterstützt."
        )

    # --- Method A: UV-Photometrie (Variante B) ---
    if variante == "B":
        if not uv_einwaagen or not uv_absorptionen:
            raise ValueError(
                "UV-Daten (uv_einwaagen, uv_absorptionen) sind für "
                "Variante B erforderlich."
            )
        from chemdraw_tool.calculator.photometry import calculate_gehalt_uv

        uv_raw = calculate_gehalt_uv(
            einwaagen=uv_einwaagen,
            absorptionen=uv_absorptionen,
            substance=substance_key,
            verduennungsfaktor=uv_verduennungsfaktor,
            kolbenvolumen_ml=uv_kolbenvolumen_ml,
        )
        uv_gehalte = [r["gehalt"] for r in uv_raw]
        uv_steps = [
            CalculationStep(
                label=r["label"],
                formula=r["formula"],
                substitution=r["substitution"],
                result=r["result"],
                explanation=r["explanation"],
            )
            for r in uv_raw
        ]
        uv_stats = descriptive_stats(uv_gehalte, true_value=wahrer_wert)
        uv_t = one_sample_t_test(uv_gehalte, mu=wahrer_wert)
        method_a = MethodResult(
            name="UV-Photometrie",
            gehalt_steps=uv_steps,
            mean=uv_stats["mean"],
            std_abs=uv_stats["std_abs"],
            std_rel=uv_stats["std_rel"],
            variance=uv_stats["variance"],
            recovery=uv_stats.get("recovery", 0.0),
            rel_deviation=uv_stats.get("rel_deviation", 0.0),
            t_test_value=uv_t["t_value"],
            t_test_critical=uv_t["t_critical"],
            t_test_passed=uv_t["passed"],
            t_test_explanation=(
                f"Einstichproben-t-Test: t = |x̄ − µ| / (s / √n) = "
                f"{uv_t['t_value']:.3f}. "
                f"t_krit({uv_t['df']} FG, α=0,05) = {uv_t['t_critical']:.3f}. "
                f"{'Bestanden' if uv_t['passed'] else 'Nicht bestanden'}: "
                f"{'t < t_krit → kein signifikanter Unterschied zum wahren Wert.' if uv_t['passed'] else 't ≥ t_krit → signifikanter Unterschied zum wahren Wert.'}"
            ),
        )
    else:  # unreachable: nur Variante B erreicht diesen Block
        raise ValueError(f"Interner Fehler: unerwartete Variante '{variante}'.")

    # --- Method B: Acidimetrie ---
    faktor = SUBSTANCE_FACTORS[substance_key]
    titer = calculate_titer(
        acid_referenz_einwaagen,
        acid_referenz_volumina,
        acid_blindwert,
        faktor,
    )
    acid_raw = calculate_gehalt_titration(
        einwaagen=acid_einwaagen,
        volumina=acid_volumina,
        blindwert=acid_blindwert,
        faktor=faktor,
        titer=titer,
    )
    acid_gehalte = [r["gehalt"] for r in acid_raw]
    acid_steps = [
        CalculationStep(
            label=r["label"],
            formula=r["formula"],
            substitution=r["substitution"],
            result=r["result"],
            explanation=r["explanation"],
        )
        for r in acid_raw
    ]
    acid_stats = descriptive_stats(acid_gehalte, true_value=wahrer_wert)
    acid_t = one_sample_t_test(acid_gehalte, mu=wahrer_wert)
    method_b = MethodResult(
        name="Acidimetrie",
        gehalt_steps=acid_steps,
        mean=acid_stats["mean"],
        std_abs=acid_stats["std_abs"],
        std_rel=acid_stats["std_rel"],
        variance=acid_stats["variance"],
        recovery=acid_stats.get("recovery", 0.0),
        rel_deviation=acid_stats.get("rel_deviation", 0.0),
        t_test_value=acid_t["t_value"],
        t_test_critical=acid_t["t_critical"],
        t_test_passed=acid_t["passed"],
        t_test_explanation=(
            f"Einstichproben-t-Test: t = |x̄ − µ| / (s / √n) = "
            f"{acid_t['t_value']:.3f}. "
            f"t_krit({acid_t['df']} FG, α=0,05) = {acid_t['t_critical']:.3f}. "
            f"{'Bestanden' if acid_t['passed'] else 'Nicht bestanden'}."
        ),
    )

    # --- Method Comparison ---
    f_result = f_test(uv_gehalte, acid_gehalte)
    welch_result = welch_t_test(uv_gehalte, acid_gehalte)

    if f_result["passed"] and welch_result["passed"]:
        result_text = "Methoden sind gleichwertig (F-Test und t-Test bestanden)."
    elif not f_result["passed"]:
        result_text = (
            "Methoden sind NICHT gleichwertig — die Präzision "
            "unterscheidet sich signifikant (F-Test nicht bestanden)."
        )
    else:
        result_text = (
            "Methoden sind NICHT gleichwertig — die Mittelwerte "
            "unterscheiden sich signifikant (t-Test nicht bestanden)."
        )

    comparison = MethodComparison(
        f_test_value=f_result["f_value"],
        f_test_critical=f_result["f_critical"],
        f_test_passed=f_result["passed"],
        f_test_explanation=(
            f"F-Test: F = s₁²/s₂² = {f_result['f_value']:.3f}. "
            f"F_krit = {f_result['f_critical']:.3f}. "
            f"{'Varianzen gleichwertig.' if f_result['passed'] else 'Varianzen unterschiedlich.'}"
        ),
        t_test_value=welch_result["t_value"],
        t_test_critical=welch_result["t_critical"],
        t_test_passed=welch_result["passed"],
        t_test_explanation=(
            f"Welch-t-Test: t = {welch_result['t_value']:.3f}. "
            f"t_krit({welch_result['df']} FG) = {welch_result['t_critical']:.3f}. "
            f"{'Mittelwerte gleichwertig.' if welch_result['passed'] else 'Mittelwerte unterschiedlich.'}"
        ),
        result_text=result_text,
    )

    # --- Summary ---
    summary = (
        f"Validierung {substance} (Variante {variante}): "
        f"UV-Photometrie Gehalt = {method_a.mean:.2f} ± {method_a.std_abs:.2f} % "
        f"(WFR {method_a.recovery:.1f} %), "
        f"Acidimetrie Gehalt = {method_b.mean:.2f} ± {method_b.std_abs:.2f} % "
        f"(WFR {method_b.recovery:.1f} %). "
        f"Methodenvergleich: {result_text}"
    )

    return ValidationPayload(
        type="validation",
        variante=variante,
        substance=substance,
        wahrer_wert=wahrer_wert,
        method_a=method_a,
        method_b=method_b,
        comparison=comparison,
        summary=summary,
    )


@mcp.tool()
def save_png(png_base64: str, filename: str) -> str:
    """Persist a client-rendered PNG to ~/ChemDraw-Output/png/ and return its path.

    Fallback path for the UI: used when the app's image-clipboard write is
    blocked by the sandbox. Expects a base64 PNG (with or without a
    `data:image/png;base64,` prefix).
    """
    from chemdraw_tool.png_writer import save_png_bytes

    png_dir = Path.home() / "ChemDraw-Output" / "png"
    try:
        path = save_png_bytes(png_base64, filename, png_dir)
    except (ValueError, OSError) as exc:
        return f"Fehler: {exc}"
    return str(path)


@mcp.tool()
def open_chemdraw_file(
    file_path: str = "", name_or_smiles: str = "", cleanup: bool = True
) -> str:
    """Open a structure in ChemDraw for review or editing (macOS only).

    Provide EITHER file_path (an existing .cdxml/.cdx file, e.g. from a
    generate_* call with formats=["cdxml"]) OR name_or_smiles — then the
    structure is generated as CDXML on demand and opened directly; no prior
    generate_molecule call needed. By default runs Clean Up Structure to
    standardize bond geometry.

    Args:
        file_path: Absolute path to an existing .cdxml file.
        name_or_smiles: English/IUPAC name or SMILES to generate & open.
        cleanup: Run Clean Up Structure after opening (default: True).
    """
    if not file_path and not name_or_smiles:
        return (
            "Bitte entweder file_path (vorhandene .cdxml-Datei) oder "
            "name_or_smiles (Struktur wird dann direkt erzeugt) angeben."
        )

    if not file_path:
        smiles, mol = resolve(name_or_smiles)
        mol = generate_2d(mol)
        input_issues = validate_input(mol)
        for issue in input_issues:
            if issue.severity == Severity.ERROR:
                raise ValueError(f"Input validation failed: {issue.message}")
        slug = _slugify(name_or_smiles)
        _, file_path = _write_structure_files(mol, slug, name_or_smiles, ["cdxml"])

    if Path(file_path).suffix.lower() not in (".cdxml", ".cdx"):
        return f"Nur ChemDraw-Dateien (.cdxml/.cdx) werden geöffnet, nicht: {file_path}"

    if not Path(file_path).exists():
        return f"Datei nicht gefunden: {file_path}"

    if find_chemdraw() is None:
        return "ChemDraw ist auf diesem Mac nicht installiert."

    success = open_in_chemdraw(file_path, cleanup=cleanup)
    if success:
        msg = f"Geöffnet in ChemDraw: {file_path}"
        if cleanup:
            msg += " (Clean Up Structure ausgeführt)"
        return msg
    return f"Fehler beim Öffnen: {file_path}"


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
