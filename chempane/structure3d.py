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
_PRIMARY_TIMEOUT_S = 30
_FALLBACK_TIMEOUT_S = 10


def _ist_fulleren(mol: Chem.Mol) -> bool:
    """Geschlossener, rein aromatischer Kohlenstoffkäfig (C20/C60/C70 …) ohne Rand-H."""
    return (
        mol.GetNumAtoms() >= 20
        and len(Chem.GetMolFrags(mol)) == 1
        and all(
            a.GetAtomicNum() == 6 and a.GetIsAromatic() and a.GetDegree() == 3 and a.GetTotalNumHs() == 0
            for a in mol.GetAtoms()
        )
    )


def _embed_dg(mol3d: Chem.Mol) -> int:
    """Distanzgeometrie mit Zufallskoordinaten ohne Flachheits-/Torsionszwang (z. B. Fullerene)."""
    fb = AllChem.ETKDGv3()
    fb.randomSeed = _EMBED_SEED
    fb.useRandomCoords = True
    fb.useExpTorsionAnglePrefs = False
    fb.useBasicKnowledge = False
    fb.timeout = _FALLBACK_TIMEOUT_S
    return AllChem.EmbedMolecule(mol3d, fb)


def embed_3d(mol: Chem.Mol) -> Chem.Mol:
    """ETKDGv3-Embedding mit expliziten H, Sicherheits-Timeout und Kraftfeld-Optimierung.

    Geschlossene aromatische Kohlenstoffkäfige (Fullerene wie C60/C70) scheitern an
    ETKDGv3s Flachheitsregeln (`useBasicKnowledge`) und gehen direkt in reine
    Distanzgeometrie + UFF (MMFF94 zwingt aromatische Ringe flach). Alle anderen
    Moleküle laufen unverändert über den ETKDGv3-Primärweg ohne `maxIterations`-Deckel.
    """
    mol3d = Chem.AddHs(Chem.Mol(mol))

    if _ist_fulleren(mol):
        fallback = True
        rc = _embed_dg(mol3d)
    else:
        fallback = False
        params = AllChem.ETKDGv3()
        params.randomSeed = _EMBED_SEED  # deterministisch — gleiche Eingabe, gleiches Bild
        params.timeout = _PRIMARY_TIMEOUT_S
        rc = AllChem.EmbedMolecule(mol3d, params)
        if rc != 0:
            fallback = True
            rc = _embed_dg(mol3d)

    if rc != 0:
        raise ValueError("3D embedding failed — the structure may be too unusual for a conformer.")

    # MMFF meldet fehlende Parameter (Bor, Metalle) per Rückgabewert −1, nicht
    # per Exception — der frühere try/except erreichte UFF nie. Im Käfig-/Fallback-Weg
    # direkt UFF mit 1000 Schritten nutzen, weil MMFF94 gekrümmte aromatische Käfige
    # (C60/C70) verzerrt; im Primärweg unverändert UFF-Default.
    if fallback:
        try:
            AllChem.UFFOptimizeMolecule(mol3d, maxIters=1000)
        except (RuntimeError, ValueError):
            pass  # auch UFF kennt das Element nicht: rohe DG-Geometrie zeigen
    elif AllChem.MMFFHasAllMoleculeParams(mol3d):
        AllChem.MMFFOptimizeMolecule(mol3d)
    else:
        try:
            AllChem.UFFOptimizeMolecule(mol3d)
        except (RuntimeError, ValueError):
            pass  # auch UFF kennt das Element nicht: rohe ETKDG-Geometrie zeigen
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
