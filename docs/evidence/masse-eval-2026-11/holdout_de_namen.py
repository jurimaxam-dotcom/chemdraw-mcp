"""Holdout für chemdraw_tool/de_names.py: Präzision an Namen, die nicht zum Einstellen dienten.

Die Umschreibregeln wurden an den 80 `not_found`-Eingaben aus Lauf 2 eingestellt.
Hier laufen sie über die deutschen Eingaben, die schon in Lauf 2 direkt grün
waren — die Variante wird gebaut, an PubChem geschickt und ihr InChIKey mit der
Wikidata-Erwartung verglichen. Ein "anderer Stoff" hier wäre ein Fehlgriff, den
die Kaskade in der Praxis bei einem fremden Namen machen würde.

    uv run python docs/evidence/masse-eval-2026-11/holdout_de_namen.py   # Netz, ~2 min
"""

import json
import time
from pathlib import Path

from rdkit import Chem
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

from chemdraw_tool import resolver
from chemdraw_tool.de_names import english_variant

HIER = Path(__file__).parent
REPO = HIER.parents[2]

lauf2 = json.loads((HIER / "identitaet-lauf-2-vor-de-namen.json").read_text())
liste = json.loads((REPO / "tests/identity/stoffe-masse.json").read_text())["stoffe"]
sprache = {e["eingabe"]: e["sprache"][:2] for e in liste}
kandidaten = [r for r in lauf2 if r["status"] == "gruen" and sprache.get(r["eingabe"]) == "de"]

zahl = {"ohne Variante": 0, "gleich": 0, "Stereo/Form": 0, "anderer Stoff": 0, "nicht gefunden": 0}
for r in kandidaten:
    variante = english_variant(r["eingabe"])
    if not variante:
        zahl["ohne Variante"] += 1
        continue
    smiles = resolver._pubchem_lookup(variante, [])
    time.sleep(0.3)
    if not smiles:
        zahl["nicht gefunden"] += 1
        continue
    mol = Chem.MolFromSmiles(smiles)
    key = Chem.MolToInchiKey(mol)
    if key == r["erwartet"]:
        zahl["gleich"] += 1
    elif key[:14] == r["erwartet"][:14]:
        zahl["Stereo/Form"] += 1
        print(f"~  {r['eingabe']} → {variante}")
    else:
        zahl["anderer Stoff"] += 1
        print(f"XX {r['eingabe']} → {variante}: {CalcMolFormula(mol)} {smiles[:70]}")

print(f"deutsche Eingaben, in Lauf 2 grün: {len(kandidaten)} · {zahl}")
