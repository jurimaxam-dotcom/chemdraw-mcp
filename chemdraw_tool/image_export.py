"""Serverseitiges Struktur-Rendering als PNG/SVG-Dateien — der Primärpfad.

Seit der ChemDraw-Entkopplung (2026-06-09) sind PNG und SVG die primären
Artefakte der generate_*-Tools; CDXML ist ein optionales Zusatzformat.
PNG kommt aus RDKits Cairo-Backend (im PyPI-Wheel enthalten), SVG aus
MolDraw2DSVG — beides offline, ohne ChemDraw, ohne neue Dependencies.

Abgrenzung zu svg_renderer.py: dort entstehen UI-Vorschau-SVGs (ViewBox-
Cropping, fill_container, Atom-Highlights). Hier entstehen eigenständige
*Dateien* mit fester Größe und Legende (Name unter der Struktur) —
druckfertig fürs Protokoll.
"""

from __future__ import annotations

from pathlib import Path

from rdkit.Chem import rdChemReactions
from rdkit.Chem.Draw import rdMolDraw2D

from chemdraw_tool.svg_renderer import BOND_LINE_WIDTH

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# 1000x800 px ≈ 8,5 cm Bildbreite bei 300 dpi — druckfertig für Protokolle.
MOL_PNG_SIZE = (1000, 800)
MOL_SVG_SIZE = (500, 400)
# Reaktionen sind breit (Edukte + Pfeil + Produkte).
RXN_PNG_SIZE = (1600, 480)
RXN_SVG_SIZE = (900, 270)


def _draw_molecule(drawer, mol, legend: str) -> None:
    # Gleiche Strichstärke wie die UI-Vorschau (gemeinsame Konstante) — die Datei
    # darf nicht anders aussehen als das, was der Nutzer im Chat gesehen hat.
    # Bewusst NICHT übernommen: fixedBondLength (Datei soll die Canvas füllen)
    # und clearBackground=False (Datei braucht weißen Hintergrund).
    drawer.drawOptions().bondLineWidth = BOND_LINE_WIDTH
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol, legend=legend)
    drawer.FinishDrawing()


def render_molecule_png(
    mol, legend: str = "", size: tuple[int, int] = MOL_PNG_SIZE
) -> bytes:
    drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    _draw_molecule(drawer, mol, legend)
    return drawer.GetDrawingText()


def render_molecule_svg(
    mol, legend: str = "", size: tuple[int, int] = MOL_SVG_SIZE
) -> str:
    drawer = rdMolDraw2D.MolDraw2DSVG(*size)
    _draw_molecule(drawer, mol, legend)
    return drawer.GetDrawingText()


def _reaction_from_smiles(reaction_smiles: str):
    rxn = rdChemReactions.ReactionFromSmarts(reaction_smiles, useSmiles=True)
    if rxn is None:
        raise ValueError(f"Ungültiges Reaktions-SMILES: {reaction_smiles!r}")
    return rxn


def render_reaction_png(
    reaction_smiles: str, size: tuple[int, int] = RXN_PNG_SIZE
) -> bytes:
    drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    drawer.DrawReaction(_reaction_from_smiles(reaction_smiles))
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def render_reaction_svg(
    reaction_smiles: str, size: tuple[int, int] = RXN_SVG_SIZE
) -> str:
    drawer = rdMolDraw2D.MolDraw2DSVG(*size)
    drawer.DrawReaction(_reaction_from_smiles(reaction_smiles))
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def write_files(base: Path, artifacts: dict[str, bytes | str]) -> dict[str, str]:
    """Schreibt {format: inhalt} als base.<format> neben­einander.

    Überschreibt vorhandene Dateien bewusst (Regenerieren = Update, kein
    -2-Suffix — anders als der User-Export in png_writer.save_png_bytes).
    Returns {format: absoluter Pfad als str}.
    """
    base.parent.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for fmt, content in artifacts.items():
        path = base.with_suffix(f".{fmt}")
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        written[fmt] = str(path)
    return written
