"""Salzform-Messung (06.11.2026): auf dem PubChem-direkt-Weg mit Variante die Komponenten von Direkttreffer und Variante.

    uv run python docs/evidence/masse-eval-2026-11/salzform_mess.py docs/evidence/masse-eval-2026-11/salzform_mess.json   # Netz, ~25 min

Läuft im Repo-Wurzelordner; setzt fort, was in der Ausgabedatei schon steht.
"""
import json
import sys
import time
from pathlib import Path

from rdkit import Chem, RDLogger

from chemdraw_tool import resolver

RDLogger.DisableLog("rdApp.*")
REPO = Path.cwd()
OUT = Path(sys.argv[1])
cache = json.loads(OUT.read_text()) if OUT.exists() else {}
names = [(s["eingabe"], s["inchikey"], "lauf") for s in json.loads((REPO/"tests/identity/stoffe-masse.json").read_text())["stoffe"] if isinstance(s.get("eingabe"), str)]
names += [(x["name"], x["erwartet"], "holdout") for x in json.loads((REPO/"docs/evidence/masse-eval-2026-11/holdout_pubchem_check.json").read_text())]
def ik(s):
    m = Chem.MolFromSmiles(s) if s else None
    return Chem.MolToInchiKey(m) if m is not None else None
def nfrag(s):
    m = Chem.MolFromSmiles(s) if s else None
    return len(Chem.GetMolFrags(m)) if m is not None else None
for name, erw, quelle in names:
    if name in cache:
        continue
    var = resolver._spelling_variant(name)
    if var is None:
        continue
    if quelle == "lauf" and resolver._opsin_lookup(name):
        continue
    d = resolver._pubchem_lookup(name, [])
    if not d:
        continue
    v = resolver._pubchem_lookup(var, [])
    time.sleep(0.3)
    cache[name] = dict(quelle=quelle, variante=var, erwartet=erw, direkt=d, var=v,
        ik_d=ik(d), ik_v=ik(v), n_d=nfrag(d), n_v=nfrag(v),
        stamm_gleich=resolver._parent_skeleton(d) == resolver._parent_skeleton(v) if v else None)
    OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
print(len(cache))
