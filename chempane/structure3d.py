"""3D-Konformer für den Panel-Viewer — ETKDGv3 + MMFF, explizite Wasserstoffe.

Der UI-Viewer ist bewusst ein eigener leichtgewichtiger SVG-Renderer
(Ball-and-Stick mit Tiefensortierung) statt einer WebGL-Bibliothek: 3Dmol.js
hätte die Single-File-App-Resource etwa vervierfacht, und WebGL-Verfügbarkeit
im sandboxed Panel-iframe ist nicht garantiert. Hier entsteht nur das
Datenmodell: Atome (Symbol + xyz, schwerpunktzentriert) und Bindungen.
"""

from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import AllChem

_EMBED_SEED = 0xC0FFEE
_EMBED_MAX_ITERATIONS = 50
_EMBED_TIMEOUT_S = 3


def embed_3d(mol: Chem.Mol) -> Chem.Mol:
    """ETKDGv3-Embedding mit expliziten H, Zeitdeckel und Kraftfeld-Optimierung.

    Gekrümmte aromatische Käfige wie C60 scheitern an ETKDGv3s Flachheitsregeln
    (`useBasicKnowledge`) und liefen ohne Deckel minutenlang. Nach kurzem
    ETKDGv3-Versuch fällt die Funktion auf reine Distanzgeometrie mit
    Zufallskoordinaten + UFF zurück (MMFF94 zwingt aromatische Ringe flach).
    """
    mol3d = Chem.AddHs(Chem.Mol(mol))
    params = AllChem.ETKDGv3()
    params.randomSeed = _EMBED_SEED  # deterministisch — gleiche Eingabe, gleiches Bild
    params.maxIterations = _EMBED_MAX_ITERATIONS
    params.timeout = _EMBED_TIMEOUT_S

    fallback = False
    if AllChem.EmbedMolecule(mol3d, params) != 0:
        fallback = True
        fb = AllChem.ETKDGv3()
        fb.randomSeed = _EMBED_SEED
        fb.useRandomCoords = True
        fb.useExpTorsionAnglePrefs = False
        fb.useBasicKnowledge = False
        fb.maxIterations = _EMBED_MAX_ITERATIONS
        fb.timeout = _EMBED_TIMEOUT_S
        if AllChem.EmbedMolecule(mol3d, fb) != 0:
            raise ValueError("3D embedding failed — the structure may be too unusual for a conformer.")

    # MMFF meldet fehlende Parameter (Bor, Metalle) per Rückgabewert −1, nicht
    # per Exception — der frühere try/except erreichte UFF nie. Im Käfig-Fallback
    # direkt UFF nutzen, weil MMFF94 gekrümmte aromatische Käfige (C60) verzerrt.
    if not fallback and AllChem.MMFFHasAllMoleculeParams(mol3d):
        AllChem.MMFFOptimizeMolecule(mol3d)
    else:
        try:
            AllChem.UFFOptimizeMolecule(mol3d, maxIters=1000)
        except (RuntimeError, ValueError):
            pass  # auch UFF kennt das Element nicht: rohe DG-Geometrie zeigen
    return mol3d


def atoms_and_bonds(mol3d: Chem.Mol) -> tuple[list[dict], list[dict]]:
    """Schwerpunktzentrierte Atomliste + Bindungsliste für den SVG-Viewer."""
    conf = mol3d.GetConformer()
    positions = [conf.GetAtomPosition(i) for i in range(mol3d.GetNumAtoms())]
    n = len(positions)
    cx = sum(p.x for p in positions) / n
    cy = sum(p.y for p in positions) / n
    cz = sum(p.z for p in positions) / n

    atoms = [
        {
            "symbol": atom.GetSymbol(),
            "x": p.x - cx,
            "y": p.y - cy,
            "z": p.z - cz,
        }
        for atom, p in zip(mol3d.GetAtoms(), positions)
    ]
    bonds = [
        {
            "a": b.GetBeginAtomIdx(),
            "b": b.GetEndAtomIdx(),
            "order": b.GetBondTypeAsDouble(),
        }
        for b in mol3d.GetBonds()
    ]
    return atoms, bonds
