"""Rückgrat eines Proteins (N, Cα, C, O je Rest) aus PDB oder AlphaFold — Daten, kein Bild.

Datenweg ohne API-Schlüssel (gemessen 10.11.2026):
  UniProt-Zugangsnummer → PDBe best_structures (nach Abdeckung/Auflösung
  sortiert, nennt pdb_id + chain_id) → RCSB ModelServer `/full` (Modell 1,
  mmCIF; 1LYZ 101 KB, 2HHB 383 KB, 1HZH 885 KB, je 1,0–1,6 s). Ohne PDB-Eintrag
  (PDBe antwortet 404) das AlphaFold-Modell (API → cifUrl; pLDDT steht im
  B-Faktor). Das alte PDB-Textformat ist kein verlässlicher Weg — neue Einträge
  gibt es nur als mmCIF.

  E13 (Cartoon): Das Band braucht je Rest die Peptidebene, also neben Cα das
  Carbonyl-O; die eigene Sekundärstruktur-Zuweisung (protein_ss) zusätzlich N
  und C. Gemessen 10.11.2026: Der ModelServer nimmt per GET nur einen
  Atomnamen; ein POST mit vier Namen (N/CA/C/O) liefert halb so viele Bytes,
  ist aber nicht schneller (1,0–3,8 s gegen 1,0–1,6 s), und `/full` bringt die
  Liganden (Häm, Zn²⁺, Inhibitor) im selben Abruf mit. Gelesen werden davon nur
  Rückgratatome und HETATM.

Der Leser kennt genau vier Kategorien (`_atom_site`, `_struct_conf`,
`_struct_sheet_range`, `_chem_comp` für Ligandennamen) und braucht keine
Abhängigkeit. Fallen, alle gemessen:
  - Calcium-Ionen heißen ebenfalls CA (2PRK: HETATM, type_symbol CA) → Cα nur
    mit type_symbol C, und nur in Polymerresten (label_seq_id gesetzt).
  - Selenomethionin (MSE) steht als HETATM in der Kette — es ist ein Rest,
    kein Ligand.
  - Spaltenreihenfolge unterscheidet sich (AlphaFold vs. ModelServer) → per
    Kopfzeile lesen.
  - AlphaFold legt Stränge als `STRN` in `_struct_conf` ab (DSSP-Typen), die PDB
    in `_struct_sheet_range`.
  - Ketten wählt man per auth_asym_id (so nennen sie PDBe und RCSB), Reste und
    Sekundärstruktur-Bereiche schlüsselt man per label_asym_id + label_seq_id —
    das umgeht die Kabat-Einfügecodes der Fab-Fragmente.
  - Kettenbrüche (fehlende Schleifen, Chromophor) erkennt der Cα–Cα-Abstand
    > 4,2 Å, nicht die Restnummer.
  - Nur Modell 1, nur die erste Altloc.
"""

from __future__ import annotations

import logging
import math
import re
import threading
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)

MAX_RESIDUES = 3000  # darüber wird die Spur unlesbar und das Payload zu groß
BREAK_DISTANCE = 4.2  # Å; benachbarte Cα liegen 3,8 Å auseinander (cis-Pro 2,9)
# Alte Verfeinerungen haben schiefere Geometrie: 1LYZ (1975) 4,53 Å, 2PRK 4,48 Å
# zwischen Resten mit fortlaufender label_seq_id (gemessen 10.11.2026). Bei
# fortlaufender Nummer gilt deshalb erst diese Grenze — echte Lücken springen in
# label_seq_id (1N8Z: 5,3–15 Å, 1HZH: 11 Å).
CONSECUTIVE_BREAK_DISTANCE = 5.0

_MODELSERVER_URL = (
    "https://models.rcsb.org/v1/{pdb}/full?model_nums=1&encoding=cif"
)
_PDBE_BEST_URL = "https://www.ebi.ac.uk/pdbe/api/mappings/best_structures/{acc}"
_ALPHAFOLD_API_URL = "https://alphafold.ebi.ac.uk/api/prediction/{acc}"
_TIMEOUT = (3, 15)


class StructureUnavailable(Exception):
    """Keine Struktur zu bekommen (Netz, Quelle gestört, Eintrag fehlt)."""


class NoStructure(StructureUnavailable):
    """Weder PDB-Struktur noch AlphaFold-Modell — kein Netzproblem, es gibt keins."""


class TooLarge(ValueError):
    """Mehr Cα als MAX_RESIDUES."""


# --- mmCIF ------------------------------------------------------------------

_TOKEN = re.compile(r"'(?:[^']|'(?=\S))*'|\"(?:[^\"]|\"(?=\S))*\"|\S+")
_WANTED = ("_atom_site", "_struct_conf", "_struct_sheet_range", "_chem_comp")


def _tokens(line: str) -> list[str]:
    out = []
    for tok in _TOKEN.findall(line):
        if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "'\"":
            tok = tok[1:-1]
        out.append(tok)
    return out


def parse_mmcif(text: str) -> dict[str, list[dict[str, str]]]:
    """Die drei Kategorien als Zeilenlisten {Kategorie: [{Feld: Wert}]}.

    Versteht Schleifen (`loop_`) und Einzeleinträge (`_cat.feld wert`, so
    schreibt mmCIF eine Kategorie mit genau einer Zeile — ein Eintrag mit nur
    einer Helix). Textblöcke zwischen Semikolon-Zeilen werden übersprungen bzw.
    als ein Wert gelesen.
    """
    result: dict[str, list[dict[str, str]]] = {}
    lines = text.splitlines()
    i, n = 0, len(lines)
    single: dict[str, dict[str, str]] = {}

    def text_block(j: int) -> tuple[str, int]:
        buf = [lines[j][1:]]
        j += 1
        while j < n and not lines[j].startswith(";"):
            buf.append(lines[j])
            j += 1
        return "\n".join(buf).strip(), j + 1

    while i < n:
        line = lines[i]
        stripped = line.strip()
        if stripped == "loop_":
            i += 1
            headers = []
            while i < n and lines[i].lstrip().startswith("_"):
                headers.append(lines[i].strip().split()[0])
                i += 1
            category = headers[0].split(".")[0] if headers else ""
            fields = [h.split(".", 1)[1] for h in headers]
            values: list[str] = []
            while i < n:
                row = lines[i]
                s = row.strip()
                if s.startswith(";"):
                    value, i = text_block(i)
                    values.append(value)
                    continue
                if not s or s.startswith("#"):
                    i += 1
                    if not s:
                        continue
                    break
                if s == "loop_" or s.startswith("_") or s.startswith("data_"):
                    break
                values.extend(_tokens(row))
                i += 1
            if category in _WANTED and fields:
                k = len(fields)
                rows = [dict(zip(fields, values[j : j + k])) for j in range(0, len(values) - k + 1, k)]
                result.setdefault(category, []).extend(rows)
            continue
        if stripped.startswith("_") and "." in stripped.split()[0]:
            key = stripped.split()[0]
            category, fld = key.split(".", 1)
            rest = stripped[len(key) :].strip()
            if rest:
                toks = _tokens(rest)
                value = toks[0] if toks else ""
                i += 1
            elif i + 1 < n and lines[i + 1].startswith(";"):
                value, i = text_block(i + 1)
            else:
                toks = _tokens(lines[i + 1]) if i + 1 < n else []
                value = toks[0] if toks else ""
                i += 2
            if category in _WANTED:
                single.setdefault(category, {})[fld] = value
            continue
        i += 1
    for category, row in single.items():
        result.setdefault(category, []).append(row)
    return result


# --- Rückgrat ---------------------------------------------------------------

XYZ = tuple[float, float, float]


@dataclass
class Segment:
    """Ein lückenloses Stück einer Kette: Rückgrat je Rest + Sekundärstruktur.

    `coords` sind die Cα; `n`, `c`, `o` die übrigen Rückgratatome desselben
    Rests (None, wo die Datei keins hat — CA-only-Einträge, Chromophor). Die
    Carbonyl-O-Atome geben dem Cartoon-Band seine Orientierung (Peptidebene),
    N/C/O braucht die eigene Sekundärstruktur-Zuweisung (protein_ss).
    """

    chain: str  # auth_asym_id
    coords: list[XYZ]
    ss: str  # je Rest H (Helix), E (Strang), C (Schleife)
    plddt: list[float] = field(default_factory=list)  # nur AlphaFold
    first: str = ""  # auth_seq_id des ersten Rests (für die N-/C-Marken)
    last: str = ""
    n: list[XYZ | None] = field(default_factory=list)
    c: list[XYZ | None] = field(default_factory=list)
    o: list[XYZ | None] = field(default_factory=list)
    seq: str = ""  # Einbuchstabencode je Rest (X = unbekannt); Prolin hat kein H


@dataclass
class Ligand:
    """Eine HETATM-Gruppe (Cofaktor, Metallion, Inhibitor) — schwere Atome."""

    code: str  # Komponenten-ID, z. B. HEM
    name: str  # Anzeigename, z. B. "heme b"
    chain: str  # auth_asym_id
    resnum: str  # auth_seq_id
    elements: list[str]
    coords: list[XYZ]

    @property
    def is_ion(self) -> bool:
        return len(self.coords) == 1


@dataclass
class Backbone:
    segments: list[Segment]
    source: str  # "pdb" | "alphafold"
    identifier: str  # PDB-ID oder AlphaFold-Modell-ID
    chains: list[str]
    ligands: list[Ligand] = field(default_factory=list)
    # "deposited": HELIX/SHEET bzw. _struct_conf der Datei; "computed": eigene
    # DSSP-artige Zuweisung (protein_ss), weil die Datei für die gezeigten
    # Ketten keine Angaben hat
    ss_source: str = "deposited"

    @property
    def residue_count(self) -> int:
        return sum(len(s.coords) for s in self.segments)


def _helix_type(conf_type: str, helix_class: str = "") -> str | None:
    t = conf_type.upper()
    # HELX_P: PDB, alle Helixklassen — nur Klasse 1 (rechtsgängig α) zählt; die
    # 3₁₀-Helices (Klasse 5) sind in Antikörpern zahlreich (1HZH: 120 von 1331
    # Resten) und machten das β-Sandwich zur Helix-Mischung. HELX_RH_AL_P: α-Helix
    # in AlphaFold/DSSP; 3₁₀- und PP-Helices bleiben Schleife.
    if t == "HELX_P" and helix_class in ("", "1", "?", "."):
        return "H"
    if t.startswith("HELX_RH_AL"):
        return "H"
    if t.startswith("STRN"):
        return "E"
    return None


def _ss_map(tables: dict) -> dict[tuple[str, int], str]:
    ss: dict[tuple[str, int], str] = {}

    def mark(row: dict, code: str):
        try:
            asym = row["beg_label_asym_id"]
            beg, end = int(row["beg_label_seq_id"]), int(row["end_label_seq_id"])
        except (KeyError, ValueError):
            return
        for seq in range(beg, end + 1):
            ss.setdefault((asym, seq), code)

    for row in tables.get("_struct_conf", []):
        code = _helix_type(row.get("conf_type_id", ""), row.get("pdbx_PDB_helix_class", ""))
        if code:
            mark(row, code)
    for row in tables.get("_struct_sheet_range", []):
        mark(row, "E")
    return ss


_THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E",
    "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F",
    "PRO": "P", "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V", "MSE": "M",
    "SEC": "U", "PYL": "O",
}
_BACKBONE = ("N", "CA", "C", "O")

# Liganden: was im Kristall nur Lösungsmittel, Puffer oder Kryoschutz ist, und
# Zucker der Glykosylierung (1HZH: 221 Atome NAG/MAN/…) bleiben weg; ebenso
# freie Aminosäuren und Halogenid-/Alkaliionen (meist aus dem Puffer).
_WATER = {"HOH", "DOD", "WAT", "H2O"}
_SKIP_LIGANDS = _WATER | set(_THREE_TO_ONE) | {
    # Puffer, Fällungs- und Kryoschutzmittel, Salze
    "SO4", "PO4", "PI", "GOL", "EDO", "PEG", "PGE", "PG4", "1PE", "P6G", "2PE", "MPD", "DMS",
    "ACT", "ACY", "ACE", "FMT", "TRS", "EPE", "MES", "CIT", "FLC", "BME", "IMD", "NO3", "NH4",
    "IPA", "EOH", "MOH", "BU3", "PEO", "SCN", "AZI", "TAR", "MLI", "CAC", "BCT", "IOD", "BR",
    "CL", "NA", "K", "LI", "CS", "RB", "F", "UNX", "UNL",
    # Glykane
    "NAG", "NDG", "MAN", "BMA", "GAL", "GLA", "FUC", "FUL", "SIA", "GLC", "BGC", "XYP",
}
# Kurznamen für häufige Cofaktoren; sonst _chem_comp.name
_LIGAND_NAMES = {
    "HEM": "heme b", "HEC": "heme c", "HEA": "heme a", "HEB": "heme b", "HAS": "heme a",
    "SRM": "siroheme", "CLA": "chlorophyll a", "B12": "cobalamin", "COB": "cobalamin",
    "ZN": "Zn²⁺", "FE": "Fe³⁺", "FE2": "Fe²⁺", "CU": "Cu²⁺", "CU1": "Cu⁺", "MG": "Mg²⁺",
    "CA": "Ca²⁺", "MN": "Mn²⁺", "CO": "Co²⁺", "NI": "Ni²⁺", "CD": "Cd²⁺", "HG": "Hg²⁺",
    "NAD": "NAD⁺", "NAI": "NADH", "NAP": "NADP⁺", "NDP": "NADPH", "FAD": "FAD",
    "FMN": "FMN", "ATP": "ATP", "ADP": "ADP", "AMP": "AMP", "ANP": "AMP-PNP", "GTP": "GTP",
    "GDP": "GDP", "SAM": "S-adenosylmethionine", "SAH": "S-adenosylhomocysteine",
    "PLP": "pyridoxal phosphate", "TPP": "thiamine diphosphate", "COA": "coenzyme A",
    "BTN": "biotin", "BTI": "biotin", "LPR": "lisinopril", "ROC": "saquinavir",
    "SF4": "[4Fe-4S] cluster", "FES": "[2Fe-2S] cluster", "RET": "retinal",
    "0G6": "PPACK", "CRO": "chromophore", "GYS": "chromophore",
}
LIGAND_CONTACT = 7.0  # Å zum nächsten Rückgratatom einer gezeigten Kette
MAX_LIGANDS = 16
MAX_LIGAND_ATOMS = 800


def _ligand_name(code: str, comp_names: dict[str, str]) -> str:
    if code in _LIGAND_NAMES:
        return _LIGAND_NAMES[code]
    name = (comp_names.get(code) or code).strip()
    if name.isupper():
        name = name.lower()
    return name if len(name) <= 40 else code


def _xyz(row: dict) -> XYZ:
    return (float(row["Cartn_x"]), float(row["Cartn_y"]), float(row["Cartn_z"]))


def backbone_from_mmcif(
    text: str,
    chains: list[str] | None = None,
    *,
    source: str = "pdb",
    identifier: str = "",
) -> Backbone:
    """Rückgrat (N, Cα, C, O) der gewünschten Ketten (auth_asym_id) + Liganden.

    `chains=None` nimmt alle Polymerketten. Wirft TooLarge über MAX_RESIDUES.
    Polymerreste sind Zeilen mit Sequenznummer — auch HETATM (Selenomethionin
    MSE ist in Kristallstrukturen häufig und darf die Kette nicht brechen).
    """
    tables = parse_mmcif(text)
    ss = _ss_map(tables)
    wanted = set(chains) if chains else None
    model = None
    seen: set[tuple[str, str, str]] = set()
    residues: dict[tuple[str, str], dict] = {}  # (asym, seq) → Rest
    per_asym: dict[str, list[dict]] = {}
    order: list[str] = []
    het_groups: dict[tuple[str, str, str], dict] = {}
    for row in tables.get("_atom_site", []):
        num = row.get("pdbx_PDB_model_num", "1")
        if model is None:
            model = num
        if num != model:
            continue
        element = row.get("type_symbol", "C").upper()
        if element in ("H", "D"):
            continue
        atom = row.get("label_atom_id", "")
        comp = row.get("label_comp_id", "")
        if comp in _WATER:
            continue
        auth = row.get("auth_asym_id") or row.get("label_asym_id", "")
        asym = row.get("label_asym_id", auth)
        seq = row.get("label_seq_id", ".")
        polymer = seq not in (".", "?", "")
        if row.get("group_PDB") == "HETATM":
            # Ligand, oder modifizierter Polymerrest ohne Cα (GFP-Chromophor
            # CRO) — Reste mit Cα (MSE) fallen unten wieder heraus
            key = (asym, row.get("auth_seq_id", ""), comp)
            g = het_groups.setdefault(key, {"chain": auth, "code": comp,
                                            "resnum": row.get("auth_seq_id", ""),
                                            "poly": (asym, seq) if polymer else None,
                                            "atoms": {}})
            g["atoms"].setdefault(atom, (element, _xyz(row)))  # erste Altloc
        if not polymer or row.get("group_PDB") not in ("ATOM", "HETATM"):
            continue
        if wanted is not None and auth not in wanted:
            continue
        if atom not in _BACKBONE or (atom == "CA" and element != "C"):
            continue  # Calcium heißt auch CA
        key = (asym, seq, atom)
        if key in seen:
            continue  # zweite Altloc desselben Atoms
        seen.add(key)
        res = residues.get((asym, seq))
        if res is None:
            res = {"asym": asym, "auth": auth, "seq": seq, "comp": comp, "atoms": {},
                   "resnum": row.get("auth_seq_id", "") + (
                       row.get("pdbx_PDB_ins_code", "")
                       if row.get("pdbx_PDB_ins_code", "?") not in ("?", ".") else ""),
                   "b": row.get("B_iso_or_equiv", "0")}
            residues[(asym, seq)] = res
            if asym not in per_asym:
                per_asym[asym] = []
                order.append(asym)
            per_asym[asym].append(res)
        res["atoms"][atom] = _xyz(row)
        if atom == "CA":
            res["b"] = row.get("B_iso_or_equiv", "0")

    total = sum(1 for v in per_asym.values() for r in v if "CA" in r["atoms"])
    if total > MAX_RESIDUES:
        raise TooLarge(
            f"The structure has {total} residues in the selected chains; the backbone "
            f"view is limited to {MAX_RESIDUES}."
        )
    segments: list[Segment] = []
    has_deposited = False
    for asym in order:
        current: Segment | None = None
        prev = None
        prev_seq = -10
        for res in per_asym[asym]:
            xyz = res["atoms"].get("CA")
            if xyz is None:
                continue  # Rest ohne Cα (Chromophor, Rumpfmodell) — kein Spurpunkt
            try:
                seq = int(res["seq"])
            except ValueError:
                seq = 0
            code = ss.get((asym, seq))
            has_deposited = has_deposited or code is not None
            gap = math.dist(prev, xyz) if prev is not None else 0.0
            limit = CONSECUTIVE_BREAK_DISTANCE if seq == prev_seq + 1 else BREAK_DISTANCE
            if current is None or gap > limit:
                current = Segment(chain=res["auth"], coords=[], ss="", first=res["resnum"])
                segments.append(current)
            current.coords.append(xyz)
            current.n.append(res["atoms"].get("N"))
            current.c.append(res["atoms"].get("C"))
            current.o.append(res["atoms"].get("O"))
            current.seq += _THREE_TO_ONE.get(res["comp"], "X")
            current.ss += code or "C"
            current.last = res["resnum"]
            if source == "alphafold":
                try:
                    current.plddt.append(float(res["b"]))
                except ValueError:
                    current.plddt.append(0.0)
            prev, prev_seq = xyz, seq
    ss_source = "deposited"
    if segments:
        from chemdraw_tool.protein_ss import assign_segments, fill_missing_helices

        computed = assign_segments(segments)
        if computed is not None and not has_deposited:
            # Keine HELIX/SHEET-Angaben für die gezeigten Ketten: selbst zuweisen
            for seg, code in zip(segments, computed):
                seg.ss = code
            ss_source = "computed"
        elif computed is not None:
            # Alte Einträge (1LYZ, 2PTN) lassen Helices aus — nur dort ergänzen,
            # wo die Angaben über die ganze berechnete Helix Schleife sagen
            filled = [fill_missing_helices(seg.ss, code) for seg, code in zip(segments, computed)]
            if any(f != seg.ss for f, seg in zip(filled, segments)):
                for seg, code in zip(segments, filled):
                    seg.ss = code
                ss_source = "deposited+computed"
    chain_ids = []
    for s in segments:
        if s.chain not in chain_ids:
            chain_ids.append(s.chain)
    comp_names = {r.get("id", ""): r.get("name", "") for r in tables.get("_chem_comp", [])}
    with_ca = {k for k, r in residues.items() if "CA" in r["atoms"]}
    het_groups = {k: g for k, g in het_groups.items() if g["poly"] not in with_ca}
    ligands = _select_ligands(het_groups, segments, wanted, comp_names)
    return Backbone(segments=segments, source=source, identifier=identifier, chains=chain_ids,
                    ligands=ligands, ss_source=ss_source)


def _select_ligands(groups: dict, segments: list[Segment], wanted: set[str] | None,
                    comp_names: dict[str, str]) -> list[Ligand]:
    """Cofaktoren, Metallionen und gebundene Wirkstoffe an den gezeigten Ketten."""
    if not segments or not groups:
        return []
    import numpy as np

    bb = np.array([p for s in segments for p in s.coords]
                  + [p for s in segments for p in s.o if p is not None], dtype=float)
    out: list[Ligand] = []
    atoms_total = 0
    for g in groups.values():
        code = g["code"]
        if code in _SKIP_LIGANDS or not g["atoms"]:
            continue
        coords = [xyz for _, xyz in g["atoms"].values()]
        pts = np.array(coords, dtype=float)
        near = float(np.min(np.linalg.norm(bb[None, :, :] - pts[:, None, :], axis=2)))
        if near > LIGAND_CONTACT and (wanted is None or g["chain"] not in wanted):
            continue
        if near > 2 * LIGAND_CONTACT:
            continue  # Kette stimmt, liegt aber bei einer anderen Kopie
        if len(out) >= MAX_LIGANDS or atoms_total + len(coords) > MAX_LIGAND_ATOMS:
            logger.info("ligand %s left out (limit)", code)
            continue
        atoms_total += len(coords)
        out.append(Ligand(code=code, name=_ligand_name(code, comp_names), chain=g["chain"],
                          resnum=g["resnum"],
                          elements=[e.capitalize() for e, _ in g["atoms"].values()],
                          coords=coords))
    return out


# --- Abrufe -----------------------------------------------------------------

_CACHE: dict[tuple, Backbone] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_MAX = 32


def _cached(key: tuple, build):
    with _CACHE_LOCK:
        if key in _CACHE:
            return _CACHE[key]
    value = build()
    with _CACHE_LOCK:
        while len(_CACHE) >= _CACHE_MAX:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[key] = value
    return value


def _get(url: str) -> requests.Response:
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise StructureUnavailable(f"network error for {url}: {exc}") from exc
    return resp


def pdb_backbone(pdb_id: str, chains: list[str] | None = None) -> Backbone:
    """Rückgrat und Liganden eines PDB-Eintrags vom RCSB ModelServer."""
    pdb = pdb_id.upper()

    def build():
        resp = _get(_MODELSERVER_URL.format(pdb=pdb))
        if resp.status_code != 200:
            raise StructureUnavailable(f"ModelServer answered {resp.status_code} for {pdb}")
        backbone = backbone_from_mmcif(resp.text, chains, source="pdb", identifier=pdb)
        if not backbone.segments:
            raise StructureUnavailable(f"no Cα atoms for chains {chains} in {pdb}")
        return backbone

    return _cached(("pdb", pdb, tuple(chains or ())), build)


def best_pdb_chain(accession: str) -> tuple[str, str] | None:
    """(PDB-ID, Kette) der besten Struktur laut PDBe — None, wenn es keine gibt.

    PDBe antwortet ohne Eintrag mit 404 und {"message": …}: das heißt „keine
    PDB-Struktur" (→ AlphaFold), nicht „Quelle gestört".
    """
    resp = _get(_PDBE_BEST_URL.format(acc=accession))
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise StructureUnavailable(f"PDBe answered {resp.status_code} for {accession}")
    try:
        entries = resp.json().get(accession, [])
    except ValueError as exc:
        raise StructureUnavailable(f"PDBe sent no JSON for {accession}") from exc
    if not entries:
        return None
    best = entries[0]
    return best["pdb_id"].upper(), best["chain_id"]


def alphafold_backbone(accession: str) -> Backbone:
    """Cα-Spur des AlphaFold-Modells (pLDDT je Rest im B-Faktor)."""

    def build():
        resp = _get(_ALPHAFOLD_API_URL.format(acc=accession))
        if resp.status_code == 404:
            raise NoStructure(f"no AlphaFold model for {accession}")
        if resp.status_code != 200:
            raise StructureUnavailable(f"AlphaFold API answered {resp.status_code}")
        try:
            entry = resp.json()[0]
            url = entry["cifUrl"]
        except (ValueError, LookupError, TypeError) as exc:
            raise StructureUnavailable(f"AlphaFold API sent no model URL for {accession}") from exc
        cif = _get(url)
        if cif.status_code != 200:
            raise StructureUnavailable(f"AlphaFold file answered {cif.status_code}")
        model_id = url.rsplit("/", 1)[-1].removesuffix(".cif")
        return backbone_from_mmcif(cif.text, None, source="alphafold", identifier=model_id)

    return _cached(("af", accession), build)


def structure_for_accession(accession: str) -> tuple[Backbone, str]:
    """Beste PDB-Kette, sonst AlphaFold. Zweiter Wert: Ketten-ID bzw. "".

    Hängt PDBe (gemessen: 15-s-Timeout), wird AlphaFold gefragt
    statt aufzugeben — ein Modell ist besser als keine Zeichnung.
    """
    try:
        best = best_pdb_chain(accession)
    except StructureUnavailable as exc:
        logger.warning("PDBe best structure failed for %s: %s — trying AlphaFold", accession, exc)
        best = None
    if best:
        pdb, chain = best
        return pdb_backbone(pdb, [chain]), chain
    return alphafold_backbone(accession), ""
