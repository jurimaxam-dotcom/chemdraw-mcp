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


def embed_3d(mol: Chem.Mol) -> Chem.Mol:
    """ETKDGv3-Embedding mit expliziten H und Kraftfeld-Optimierung."""
    mol3d = Chem.AddHs(Chem.Mol(mol))
    params = AllChem.ETKDGv3()
    params.randomSeed = 0xC0FFEE  # deterministisch — gleiche Eingabe, gleiches Bild
    if AllChem.EmbedMolecule(mol3d, params) != 0:
        raise ValueError("3D-Embedding fehlgeschlagen — Struktur zu exotisch?")
    try:
        AllChem.MMFFOptimizeMolecule(mol3d)
    except Exception:
        AllChem.UFFOptimizeMolecule(mol3d)
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
