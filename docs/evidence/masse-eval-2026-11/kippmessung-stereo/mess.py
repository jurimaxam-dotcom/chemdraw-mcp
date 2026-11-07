"""Kippmessung: Stereo-sehende Gegenproben im Resolver (Varianten A, B, B').

Nur messen — kein Repo-Code wird geändert; die Schalter sind Monkeypatches.

Ablauf:
  record  — EIN Live-Lauf (Netz, PAUSE 0.3 s) mit unverändertem Resolver. Jede
            Quellenantwort (_pubchem_lookup, _nci_cir_lookup, _opsin_lookup)
            landet samt Report-Einträgen in memo.json.
  replay  — offline: dieselben Lookups aus dem Memo (Fehlgriff → live nachholen
            und als "miss" protokollieren), _pubchem_checked/_opsin_checked je
            Variante ersetzt, dieselbe pruefe()-/resolve-Schleife.

  uv run python mess.py record
  uv run python mess.py replay
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

REPO = Path("/Users/tom/Documents/projects/chemdraw-mcp/.claude/worktrees/kipp2")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import identitaet as I  # noqa: E402
from rdkit import Chem, RDLogger  # noqa: E402
from rdkit.Chem import inchi  # noqa: E402

from chemdraw_tool import resolver as R  # noqa: E402

RDLogger.DisableLog("rdApp.*")

OUT = Path(__file__).parent
MEMO_FILE = OUT / "memo.json"
EVID = REPO / "docs/evidence/masse-eval-2026-11"

ORIG = {
    "pubchem": R._pubchem_lookup,
    "nci": R._nci_cir_lookup,
    "opsin": R._opsin_lookup,
    "pubchem_checked": R._pubchem_checked,
    "opsin_checked": R._opsin_checked,
}

# ---------------------------------------------------------------- Messmengen


def stoffe():
    return json.loads((REPO / "tests/identity/stoffe-masse.json").read_text())["stoffe"]


def holdout_pubchem():
    # feste Namensliste aus dem gespeicherten Holdout-Lauf (kein neues Wikidata-Query)
    return [
        (f["name"], f["erwartet"])
        for f in json.loads((EVID / "holdout_pubchem_check.json").read_text())
    ]


def holdout_opsin():
    return [
        (f["name"], f["erwartet"])
        for f in json.loads((EVID / "holdout_opsin_check.json").read_text())
    ]


# ---------------------------------------------------------------- Memo

MEMO: dict = {"pubchem": {}, "nci": {}, "opsin": {}}
MISSES: list = []
MODE = "record"


def _report_tail(report, before):
    if report is None:
        return []
    return [[a.source, a.status, a.detail] for a in report[before:]]


def _wrap_net(kind):
    orig = ORIG[kind]

    def wrapper(name, report=None):
        if R._is_unreachable(report, R._PUBCHEM if kind == "pubchem" else R._NCI):
            return None
        if MODE == "replay" and name in MEMO[kind]:
            smiles, recs = MEMO[kind][name]
            for src, st, det in recs:
                R._record(report, src, st, det)
            return smiles
        if MODE == "replay":
            MISSES.append([kind, name])
        before = len(report) if report is not None else 0
        smiles = orig(name, report)
        MEMO[kind][name] = [smiles, _report_tail(report, before)]
        return smiles

    return wrapper


def _opsin_wrapper(name):
    if name in MEMO["opsin"]:
        return MEMO["opsin"][name]
    if MODE == "replay":
        MISSES.append(["opsin", name])
    smiles = ORIG["opsin"](name)
    MEMO["opsin"][name] = smiles
    return smiles


def install_memo():
    R._pubchem_lookup = _wrap_net("pubchem")
    R._nci_cir_lookup = _wrap_net("nci")
    R._opsin_lookup = _opsin_wrapper


# ---------------------------------------------------------------- Regeln

# Triage: "nur wenn der Name kein Stereopräfix trägt (not _STEREO_PREFIX.match(name), auch kein D-/L-)"
DL_PREFIX = re.compile(r"(?i)^(?:DL|D|L)-")

LOG: list = []  # jede Stelle, an der eine neue Regel ein anderes Ergebnis gibt


def _parent_key25(smiles):
    """Block 1+2 des InChIKeys der Komponente, die _parent_skeleton wählt."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    organic = [
        f
        for f in Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
        if any(a.GetAtomicNum() == 6 for a in f.GetAtoms())
    ]
    if not organic:
        return _water_free_key25(smiles)
    parent = max(organic, key=lambda f: f.GetNumHeavyAtoms())
    return Chem.MolToInchiKey(parent)[:25]


def _water_free_key25(smiles):
    """Block 1+2 des InChIKeys desselben Moleküls, das _skeleton verwendet (ohne Wasser)."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    frags = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
    parts = [f for f in frags if Chem.MolToSmiles(f) != "O"]
    if parts and len(parts) < len(frags):
        mol = parts[0]
        for frag in parts[1:]:
            mol = Chem.CombineMols(mol, frag)
    return Chem.MolToInchiKey(mol)[:25]


def n_defined(smiles):
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return 0
    centres = Chem.FindMolChiralCenters(
        mol, includeUnassigned=False, useLegacyImplementation=False
    )
    bonds = sum(
        b.GetStereo() not in (Chem.BondStereo.STEREONONE, Chem.BondStereo.STEREOANY)
        for b in mol.GetBonds()
    )
    return len(centres) + bonds


def _layers(smiles):
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    parts = inchi.MolToInchi(mol).split("/")[2:]
    lay = {p[0]: p[1:] for p in parts if p[:1] in "btms"}
    tetra, dbl = {}, {}
    for ci, comp in enumerate(lay.get("t", "").split(";")):
        for tok in filter(None, comp.split(",")):
            tetra[(ci, tok[:-1])] = tok[-1]
    for ci, comp in enumerate(lay.get("b", "").split(";")):
        for tok in filter(None, comp.split(",")):
            dbl[(ci, tok[:-1])] = tok[-1]
    ms = lay.get("m", "")
    return tetra, dbl, ms, lay.get("s", "")


def stereo_art(sm_vor, sm_nach):
    kv, kn = (
        inchi.MolToInchiKey(Chem.MolFromSmiles(s))
        if s and Chem.MolFromSmiles(s)
        else None
        for s in (sm_vor, sm_nach)
    )
    if not kv or not kn:
        return "unklar (kein Ergebnis)"
    if kv[:14] != kn[:14]:
        return "skelett"
    if kv[:25] == kn[:25]:
        return "ladung/protonierung"
    lv, ln = _layers(sm_vor), _layers(sm_nach)
    tv, bv, mv, sv = lv
    tn, bn, mn, sn = ln
    dv = {
        k: v
        for k, v in {
            **{("t",) + k: v for k, v in tv.items()},
            **{("b",) + k: v for k, v in bv.items()},
        }.items()
        if v != "?"
    }
    dn = {
        k: v
        for k, v in {
            **{("t",) + k: v for k, v in tn.items()},
            **{("b",) + k: v for k, v in bn.items()},
        }.items()
        if v != "?"
    }
    if not dv and dn:
        return "flach→definiert"
    if dv and not dn:
        return "definiert→flach"
    flip = {"+": "-", "-": "+"}
    if (
        mv and mn and mv != mn
    ):  # /m-Inversion: Vorzeichen der t-Schicht einer Seite drehen
        dn = {k: (flip.get(v, v) if k[0] == "t" else v) for k, v in dn.items()}
    gemeinsam = set(dv) & set(dn)
    if any(dv[k] != dn[k] for k in gemeinsam):
        return "anderes Isomer (Widerspruch)"
    if set(dn) < set(dv):
        return "weniger definiert (Teilmenge)"
    if set(dn) > set(dv):
        return "mehr definiert (Obermenge)"
    if sv != sn:
        return f"gleiche Zentren, /s{sv}→/s{sn} (absolut/relativ/racemisch)"
    return "gleiche Zentren, nur /m (Enantiomer)" if mv != mn else "unklar"


def make_pubchem_checked(rule_a: str | None):  # None | A | A>= | A⊇
    def checked(name, smiles, report):
        variant = R._spelling_variant(name)
        if variant is None:
            return smiles, name
        other = R._pubchem_lookup(variant, report)
        other_parent = R._parent_skeleton(other)
        if other_parent is None:
            return smiles, name
        same_parent = other_parent == R._parent_skeleton(smiles)
        if not same_parent and not R._same_tautomer(other, smiles):
            return other, variant
        # ---- Variante A (neu): vor der Salzregel
        if same_parent and _parent_key25(other) != _parent_key25(smiles):
            guarded = bool(R._STEREO_PREFIX.match(name) or DL_PREFIX.match(name))
            comp_ok = R._components(other) <= R._components(smiles)
            nd_d, nd_v = n_defined(smiles), n_defined(other)
            art = stereo_art(smiles, other)
            if rule_a == "A>=":  # Chef 07.11.: definiertere Form gewinnt (Zahl)
                stereo_ok = nd_v >= nd_d
            elif (
                rule_a == "A⊇"
            ):  # Zusatzspalte: Variante verliert und widerspricht nichts
                stereo_ok = art in ("flach→definiert", "mehr definiert (Obermenge)")
            else:
                stereo_ok = True
            fires = bool(rule_a) and not guarded and comp_ok and stereo_ok
            LOG.append(
                {
                    "regel": "A",
                    "name": name,
                    "variante": variant,
                    "def_direkt": nd_d,
                    "def_variante": nd_v,
                    "art": art,
                    "direkt": Chem.MolToInchiKey(Chem.MolFromSmiles(smiles)),
                    "variante_key": Chem.MolToInchiKey(Chem.MolFromSmiles(other)),
                    "gesperrt_praefix": guarded,
                    "gesperrt_salz": not comp_ok,
                    "greift": fires,
                }
            )
            if fires:
                return other, variant
        if R._components(other) == 1 < R._components(
            smiles
        ) and not R._SALT_WORD.search(name):
            return other, variant
        return smiles, name

    return checked


def make_opsin_checked(rule_b: str | None):  # None | "B" | "B'"
    def checked(name, opsin_smiles, report):
        if R._SYSTEMATIC_MARK.search(name):
            return opsin_smiles
        opsin_mol = Chem.MolFromSmiles(opsin_smiles)
        if opsin_mol is None or not any(
            a.GetAtomicNum() == 6 for a in opsin_mol.GetAtoms()
        ):
            return opsin_smiles
        pubchem = R._pubchem_lookup(name, report)
        opsin_key = R._skeleton(opsin_smiles)
        pk = R._skeleton(pubchem) if pubchem is not None else None
        if pubchem is None or pk is None:
            return opsin_smiles
        if pk == opsin_key:
            # ---- Variante B/B' (neu)
            if _water_free_key25(pubchem) != _water_free_key25(opsin_smiles):
                nd_p, nd_o = n_defined(pubchem), n_defined(opsin_smiles)
                fires = rule_b == "B" or (rule_b == "B'" and nd_p >= nd_o)
                LOG.append(
                    {
                        "regel": rule_b or "B-aus",
                        "name": name,
                        "opsin_key": Chem.MolToInchiKey(opsin_mol),
                        "pubchem_key": Chem.MolToInchiKey(Chem.MolFromSmiles(pubchem)),
                        "def_opsin": nd_o,
                        "def_pubchem": nd_p,
                        "greift": fires,
                    }
                )
                if fires:
                    return pubchem
            return opsin_smiles
        english = None if R.form_variant(name) else R.english_variant(name)
        if english and english != name:
            if R._skeleton(R._pubchem_lookup(english, report)) == opsin_key:
                return opsin_smiles
        return pubchem

    return checked


VARIANTEN = {
    "basis": (None, None),
    "A": ("A", None),
    "A>=": ("A>=", None),
    "A⊇": ("A⊇", None),
    "B": (None, "B"),
    "B'": (None, "B'"),
    "A>=+B'": ("A>=", "B'"),
    "A⊇+B'": ("A⊇", "B'"),
    "A+B'": ("A", "B'"),
}


def set_variant(name):
    rule_a, rule_b = VARIANTEN[name]
    R._pubchem_checked = make_pubchem_checked(rule_a)
    R._opsin_checked = make_opsin_checked(rule_b)
    R.resolve_name.cache_clear()


# ---------------------------------------------------------------- Läufe


def key_of(smiles):
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    return inchi.MolToInchiKey(mol) if mol is not None else None


def run_all(pause: float):
    res = {"stoffe": [], "holdout_pubchem": [], "holdout_opsin": []}
    for i, e in enumerate(stoffe(), 1):
        R.resolve_name.cache_clear()
        ergebnis = I.pruefe(e)
        if MODE == "record" and I._quelle_weg(ergebnis):
            time.sleep(I.BACKOFF)
            R.resolve_name.cache_clear()
            ergebnis = I.pruefe(e)
        smiles = None
        if MODE == "replay":
            try:
                smiles = R.resolve(e["eingabe"])[
                    0
                ]  # lru-Cache/SMILES-Weg: keine neuen Lookups
            except Exception:
                smiles = None
        res["stoffe"].append(
            {
                "eingabe": e["eingabe"],
                "erwartet": e.get("inchikey"),
                "smiles": smiles,
                **ergebnis,
            }
        )
        if MODE == "record":
            print(f"{i:>3} {ergebnis['status']:5} {e['eingabe']}", flush=True)
            time.sleep(pause)
            if i % 50 == 0:
                save_memo()
    for teil, liste in (
        ("holdout_pubchem", holdout_pubchem()),
        ("holdout_opsin", holdout_opsin()),
    ):
        for i, (name, erwartet) in enumerate(liste, 1):
            R.resolve_name.cache_clear()
            smiles = None
            try:
                smiles = R.resolve_name(name)
                k = key_of(smiles)
            except Exception as ex:
                k = None
                if MODE == "record" and getattr(ex, "kind", "") in (
                    "offline",
                    "sources_down",
                    "partial",
                ):
                    time.sleep(I.BACKOFF)
                    R.resolve_name.cache_clear()
                    try:
                        k = key_of(R.resolve_name(name))
                    except Exception:
                        k = None
            res[teil].append(
                {"name": name, "erwartet": erwartet, "key": k, "smiles": smiles}
            )
            if MODE == "record":
                print(f"{teil} {i:>3} {name} {k}", flush=True)
                time.sleep(pause)
                if i % 50 == 0:
                    save_memo()
    return res


def save_memo():
    MEMO_FILE.write_text(json.dumps(MEMO, ensure_ascii=False))


def record():
    global MODE
    MODE = "record"
    install_memo()  # Originalfunktionen _pubchem_checked/_opsin_checked bleiben aktiv
    res = run_all(I.PAUSE)
    save_memo()
    (OUT / "record.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    (OUT / "record_log.json").write_text(json.dumps(LOG, ensure_ascii=False, indent=1))


def replay():
    global MODE, LOG
    MODE = "replay"
    MEMO.update(json.loads(MEMO_FILE.read_text()))
    install_memo()
    alle = {}
    logs = {}
    for v in VARIANTEN:
        LOG = []
        set_variant(v)
        n_miss = len(MISSES)
        alle[v] = run_all(0)
        logs[v] = LOG
        print(
            f"{v}: replay fertig, neue Memo-Fehlgriffe {len(MISSES) - n_miss}",
            flush=True,
        )
    (OUT / "replay.json").write_text(json.dumps(alle, ensure_ascii=False, indent=1))
    (OUT / "replay_log.json").write_text(json.dumps(logs, ensure_ascii=False, indent=1))
    (OUT / "misses.json").write_text(json.dumps(MISSES, ensure_ascii=False, indent=1))
    save_memo()


if __name__ == "__main__":
    {"record": record, "replay": replay}[sys.argv[1]]()
