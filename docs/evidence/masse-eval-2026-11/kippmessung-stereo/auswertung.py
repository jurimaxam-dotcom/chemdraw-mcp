"""Auswertung der Kippmessung: record.json + replay.json → ergebnis.json/ergebnis.md (offline)."""

import json
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import inchi

RDLogger.DisableLog("rdApp.*")
OUT = Path(__file__).parent
REPO = Path("/Users/tom/Documents/projects/chemdraw-mcp/.claude/worktrees/agent-aad3721130258edcb")
EVID = REPO / "docs/evidence/masse-eval-2026-11"

record = json.loads((OUT / "record.json").read_text())
replay = json.loads((OUT / "replay.json").read_text())
misses = json.loads((OUT / "misses.json").read_text())
logs = json.loads((OUT / "replay_log.json").read_text())


def key_of(e):
    if e.get("status") == "gruen" and e.get("text", "").count("-") == 2 and len(e["text"]) == 27:
        return e["text"]
    return e.get("erhalten")


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
    kv, kn = (inchi.MolToInchiKey(Chem.MolFromSmiles(s)) if s and Chem.MolFromSmiles(s) else None
              for s in (sm_vor, sm_nach))
    if not kv or not kn:
        return "unklar (kein Ergebnis)"
    if kv[:14] != kn[:14]:
        return "skelett"
    if kv[:25] == kn[:25]:
        return "ladung/protonierung"
    lv, ln = _layers(sm_vor), _layers(sm_nach)
    tv, bv, mv, sv = lv
    tn, bn, mn, sn = ln
    dv = {k: v for k, v in {**{("t",) + k: v for k, v in tv.items()}, **{("b",) + k: v for k, v in bv.items()}}.items() if v != "?"}
    dn = {k: v for k, v in {**{("t",) + k: v for k, v in tn.items()}, **{("b",) + k: v for k, v in bn.items()}}.items() if v != "?"}
    if not dv and dn:
        return "flach→definiert"
    if dv and not dn:
        return "definiert→flach"
    flip = {"+": "-", "-": "+"}
    if mv and mn and mv != mn:  # /m-Inversion: Vorzeichen der t-Schicht einer Seite drehen
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


V = [v for v in replay if v != "basis"]
basis = replay["basis"]
erg = {}

# ---- Treue: record (Originalcode, live) == replay basis (nachgebaute Funktionen, Memo)?
treue = {}
for teil in ("stoffe", "holdout_pubchem", "holdout_opsin"):
    diffs = []
    for r, b in zip(record[teil], basis[teil]):
        if teil == "stoffe":
            if (r["status"], key_of(r), r.get("text")) != (b["status"], key_of(b), b.get("text")):
                diffs.append({"eingabe": r["eingabe"], "record": r, "basis": b})
        elif r["key"] != b["key"]:
            diffs.append({"name": r["name"], "record": r["key"], "basis": b["key"]})
    treue[teil] = diffs
erg["treue_record_vs_basis"] = treue
erg["memo_fehlgriffe"] = misses

# ---- Grünmenge heute vs. Lauf 11
lauf11 = {e["eingabe"]: e["status"] for e in json.loads((EVID / "identitaet-lauf.json").read_text())}
gruen_heute = {e["eingabe"] for e in basis["stoffe"] if e["status"] == "gruen"}
gruen_11 = {k for k, v in lauf11.items() if v == "gruen"}
erg["gruen_heute"] = len(gruen_heute)
erg["gruen_lauf11"] = len(gruen_11)
erg["nur_lauf11_gruen"] = sorted(gruen_11 - gruen_heute)
erg["nur_heute_gruen"] = sorted(gruen_heute - gruen_11)

# ---- (a) Masse-Liste
lauf2 = json.loads((EVID / "identitaet-lauf-2-vor-de-namen.json").read_text())
liste = json.loads((REPO / "tests/identity/stoffe-masse.json").read_text())["stoffe"]
sprache = {e["eingabe"]: e.get("sprache", "")[:2] for e in liste}
de_kand = {r["eingabe"] for r in lauf2 if r["status"] == "gruen" and sprache.get(r["eingabe"]) == "de"}

tab = {}
for v in V:
    gekippt, rot_gruen, sonst = [], [], []
    for b, n in zip(basis["stoffe"], replay[v]["stoffe"]):
        kb, kn = key_of(b), key_of(n)
        if b["status"] == n["status"] and kb == kn and b.get("text") == n.get("text"):
            continue
        zeile = {"eingabe": b["eingabe"], "erwartet": b["erwartet"], "vorher": kb, "nachher": kn,
                 "status": f'{b["status"]}→{n["status"]}', "art_neu": n.get("art"),
                 "stereo_art": stereo_art(b.get("smiles"), n.get("smiles")),
                 "deutsch_lauf2_gruen": b["eingabe"] in de_kand}
        if b["status"] == "gruen" and n["status"] != "gruen":
            gekippt.append(zeile)
        elif b["status"] != "gruen" and n["status"] == "gruen":
            rot_gruen.append(zeile)
        else:
            sonst.append(zeile)
    hold = {}
    for teil in ("holdout_pubchem", "holdout_opsin"):
        z = {"gleich": 0, "behoben": [], "gekippt": [], "beide falsch, verschieden": []}
        for b, n in zip(basis[teil], replay[v][teil]):
            if b["key"] == n["key"]:
                z["gleich"] += 1
                continue
            e = b["erwartet"]
            zeile = {"name": b["name"], "erwartet": e, "vorher": b["key"], "nachher": n["key"],
                     "stereo_art": stereo_art(b.get("smiles"), n.get("smiles"))}
            if n["key"] == e:
                z["behoben"].append(zeile)
            elif b["key"] == e:
                z["gekippt"].append(zeile)
            else:
                z["beide falsch, verschieden"].append(zeile)
        hold[teil] = z
    tab[v] = {"gruen_gekippt": gekippt, "rot_gelb_zu_gruen": rot_gruen, "sonst_geaendert": sonst,
              "holdout": hold, "de_holdout_teilmenge_geaendert": [z for z in gekippt + rot_gruen + sonst if z["deutsch_lauf2_gruen"]]}
erg["varianten"] = tab
erg["de_holdout_kandidaten"] = len(de_kand)

# Regel-Protokoll: wo hätte die Regel gegriffen / wurde sie gesperrt (Variante A+B' deckt A und B' ab)
erg["protokoll_A"] = [x for x in logs["A"] if x["regel"] == "A"]
erg["protokoll_B"] = [x for x in logs["B"] if x["regel"] == "B"]

(OUT / "ergebnis.json").write_text(json.dumps(erg, ensure_ascii=False, indent=1))

# ---- Kurzbericht
L = []
L.append(f"Grün heute (Basis-Replay): {len(gruen_heute)} · Lauf 11: {len(gruen_11)}")
L.append(f"nur Lauf 11 grün: {erg['nur_lauf11_gruen']}  · nur heute grün: {erg['nur_heute_gruen']}")
L.append(f"Treue record↔basis: " + ", ".join(f"{t}: {len(d)} Abweichungen" for t, d in treue.items()))
L.append(f"Memo-Fehlgriffe im Replay: {len(misses)}")
L.append("")
L.append("| Variante | grün gekippt | rot/gelb→grün | sonst geändert | Holdout PubChem gekippt/behoben/beide falsch | Holdout OPSIN gekippt/behoben/beide falsch |")
L.append("|---|---|---|---|---|---|")
for v, t in tab.items():
    hp, ho = t["holdout"]["holdout_pubchem"], t["holdout"]["holdout_opsin"]
    L.append(f"| {v} | {len(t['gruen_gekippt'])} | {len(t['rot_gelb_zu_gruen'])} | {len(t['sonst_geaendert'])} | "
             f"{len(hp['gekippt'])}/{len(hp['behoben'])}/{len(hp['beide falsch, verschieden'])} | "
             f"{len(ho['gekippt'])}/{len(ho['behoben'])}/{len(ho['beide falsch, verschieden'])} |")
for v, t in tab.items():
    L.append(f"\n## {v}")
    for titel, key in (("grün gekippt", "gruen_gekippt"), ("rot/gelb→grün", "rot_gelb_zu_gruen"), ("sonst geändert", "sonst_geaendert")):
        L.append(f"### {titel} ({len(t[key])})")
        for z in t[key]:
            L.append(f"- {z['eingabe']}: {z['vorher']} → {z['nachher']} (erw. {z['erwartet']}) [{z['status']}, {z['stereo_art']}]")
    for teil in ("holdout_pubchem", "holdout_opsin"):
        h = t["holdout"][teil]
        L.append(f"### {teil}: gleich {h['gleich']}")
        for k in ("gekippt", "behoben", "beide falsch, verschieden"):
            for z in h[k]:
                L.append(f"- {k}: {z['name']}: {z['vorher']} → {z['nachher']} (erw. {z['erwartet']}) [{z['stereo_art']}]")
(OUT / "ergebnis.md").write_text("\n".join(L) + "\n")
print("\n".join(L[:12]))
