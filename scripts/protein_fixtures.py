"""Struktur-Fixtures für die Proteintests holen und kürzen (E13).

    uv run python scripts/protein_fixtures.py 1LYZ 1GFL … AF-P13518

Holt dieselbe Antwort wie der Server (RCSB ModelServer `/full`, Modell 1; bzw.
die AlphaFold-Datei) und behält nur, was protein_structure liest: die
Kategorien `_entry`, `_entity`, `_chem_comp`, `_struct_conf`,
`_struct_sheet_range` und von `_atom_site` die Rückgratatome N/CA/C/O der
Polymerreste sowie alle HETATM außer Wasser. Seitenketten, Anisotropie,
Literatur fallen weg — so bleibt eine echte, nur gekürzte Antwort von wenigen
Dutzend KB. Ziel: tests/__fixtures__/pdb/<ID>.cif.gz.
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent.parent / "tests" / "__fixtures__" / "pdb"
KEEP = {"_entry", "_entity", "_chem_comp", "_struct_conf", "_struct_sheet_range", "_atom_site"}
BACKBONE = {"N", "CA", "C", "O"}
WATER = {"HOH", "DOD", "WAT"}


def shrink(text: str) -> str:
    """Nur die gelesenen Kategorien; _atom_site auf Rückgrat + Liganden gekürzt."""
    lines = text.splitlines()
    out: list[str] = [lines[0], "#"]
    i, n = 1, len(lines)
    while i < n:
        s = lines[i].strip()
        if s == "loop_":
            j = i + 1
            headers = []
            while j < n and lines[j].lstrip().startswith("_"):
                headers.append(lines[j].strip())
                j += 1
            cat = headers[0].split(".")[0] if headers else ""
            k = j
            while k < n and not lines[k].startswith("#") and lines[k].strip() != "loop_" \
                    and not lines[k].lstrip().startswith("_"):
                k += 1
            if cat in KEEP:
                rows = lines[j:k]
                if cat == "_atom_site":
                    names = [h.split(".", 1)[1] for h in headers]
                    col = {name: names.index(name) for name in names}
                    kept = []
                    for row in rows:
                        tok = row.split()
                        if len(tok) != len(names):
                            continue
                        if tok[col["pdbx_PDB_model_num"]] not in ("1",):
                            continue
                        comp = tok[col["label_comp_id"]]
                        polymer = tok[col["label_seq_id"]] not in (".", "?")
                        if comp in WATER:
                            continue
                        if polymer and tok[col["label_atom_id"]] not in BACKBONE \
                                and tok[col["group_PDB"]] == "ATOM":
                            continue
                        kept.append(row)
                    rows = kept
                out += ["loop_", *headers, *rows, "#"]
            i = k
            continue
        if s.startswith("_") and "." in s.split()[0]:
            cat = s.split()[0].split(".")[0]
            j = i
            block = []
            while j < n and not lines[j].startswith("#"):
                block.append(lines[j])
                j += 1
            if cat in KEEP:
                out += [*block, "#"]
            i = j
            continue
        i += 1
    return "\n".join(out) + "\n"


def fetch(ident: str) -> str:
    if ident.upper().startswith("AF-"):
        acc = ident.split("-")[1]
        entry = requests.get(f"https://alphafold.ebi.ac.uk/api/prediction/{acc}", timeout=30).json()[0]
        return requests.get(entry["cifUrl"], timeout=60).text
    url = f"https://models.rcsb.org/v1/{ident.upper()}/full?model_nums=1&encoding=cif"
    return requests.get(url, timeout=60).text


def main(ids: list[str]) -> None:
    for ident in ids:
        text = shrink(fetch(ident))
        name = ident.upper() if not ident.upper().startswith("AF-") else ident
        if name.startswith("AF-") and not name.endswith("_v6"):
            name = f"{ident}-F1-model_v6"
        path = OUT / f"{name}.cif.gz"
        path.write_bytes(gzip.compress(text.encode(), mtime=0))
        print(f"{path.name}: {len(text) // 1024} KB roh, {path.stat().st_size // 1024} KB gz")


if __name__ == "__main__":
    main(sys.argv[1:])
