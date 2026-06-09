"""Generate test payloads for the UI test harness."""

import json
from pathlib import Path

from chemdraw_tool.generator import generate_2d
from chemdraw_tool.resolver import resolve
from chemdraw_tool.svg_renderer import extract_atom_data, render_svg

OUT = Path(__file__).parent / "test-payloads.json"


def _mol(name_or_smiles: str, name: str = ""):
    _, mol = resolve(name_or_smiles)
    mol = generate_2d(mol)
    return mol, name or name_or_smiles


def main():
    payloads = {}

    # --- Molecule ---
    mol, _ = _mol("Aspirin")
    payloads["molecule"] = {
        "type": "molecule",
        "svg": render_svg(mol),
        "atoms": extract_atom_data(mol),
        "name": "Aspirin",
        "subtitle": "Acetylsalicylsäure",
        "properties": {
            "formula": "C₉H₈O₄",
            "mw": "180.16 g/mol",
            "logP": "1.24",
            "tpsa": "63.6 Å²",
            "hbd": "1",
            "hba": "4",
            "cas": "50-78-2",
            "smiles": "CC(=O)Oc1ccccc1C(=O)O",
        },
    }

    # --- Reaction ---
    r1, _ = _mol("Salicylic acid", "Salicylsäure")
    r2, _ = _mol("CC(=O)OC(C)=O", "Essigsäureanhydrid")
    p1, _ = _mol("Aspirin", "Aspirin")
    p2, _ = _mol("CC(O)=O", "Essigsäure")
    rw, rh = 250, 200
    payloads["reaction"] = {
        "type": "reaction",
        "name": "Veresterung nach Fischer",
        "conditions": "H₂SO₄, Δ",
        "reactants": [
            {"svg": render_svg(r1, rw, rh), "name": "Salicylsäure"},
            {"svg": render_svg(r2, rw, rh), "name": "Essigsäureanhydrid"},
        ],
        "products": [
            {"svg": render_svg(p1, rw, rh), "name": "Aspirin"},
            {"svg": render_svg(p2, rw, rh), "name": "Essigsäure"},
        ],
    }

    # --- Database ---
    db_mol, _ = _mol("Aspirin")
    payloads["database"] = {
        "type": "database",
        "molecule_svg": render_svg(db_mol, 150, 120),
        "sources": [
            {
                "type": "PubChem",
                "source": "PubChem CID 2244",
                "url": "https://pubchem.ncbi.nlm.nih.gov/compound/2244",
                "rows": [
                    {"key": "CID", "val": "2244"},
                    {"key": "IUPAC-Name", "val": "2-Acetoxybenzoic acid"},
                    {"key": "Summenformel", "val": "C₉H₈O₄"},
                    {"key": "Molmasse", "val": "180.16 g/mol"},
                    {"key": "LogP", "val": "1.24"},
                    {"key": "TPSA", "val": "63.6 Å²"},
                    {"key": "H-Brücken-Donoren", "val": "1"},
                    {"key": "H-Brücken-Akzeptoren", "val": "4"},
                    {"key": "CAS-Nr.", "val": "50-78-2"},
                    {"key": "InChIKey", "val": "BSYNRYMUTXBXSQ"},
                ],
            },
            {
                "type": "GHS",
                "source": "PubChem CID 2244 — Safety",
                "url": "https://pubchem.ncbi.nlm.nih.gov/compound/2244#section=Safety-and-Hazards",
                "rows": [
                    {"key": "Signalwort", "val": "Warnung"},
                    {"key": "GHS-Piktogramm", "val": "GHS07 (Ausrufezeichen)"},
                    {
                        "key": "H-Sätze",
                        "val": "H302 — Gesundheitsschädlich bei Verschlucken",
                    },
                    {"key": "P-Sätze", "val": "P264, P270, P301+P312, P330, P501"},
                ],
            },
        ],
    }

    # --- Batch ---
    names = ["Aspirin", "Paracetamol", "Ibuprofen"]
    batch_mols = []
    for n in names:
        m, _ = _mol(n)
        batch_mols.append(
            {
                "type": "molecule",
                "svg": render_svg(m),
                "atoms": extract_atom_data(m),
                "name": n,
                "properties": {},
            }
        )
    payloads["batch"] = {"type": "batch", "molecules": batch_mols}

    OUT.write_text(json.dumps(payloads, indent=2), encoding="utf-8")
    print(f"Payloads geschrieben: {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
