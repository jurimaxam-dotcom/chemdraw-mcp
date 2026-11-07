"""Abnahme Schnitt 3: Replay mit dem echten Resolver-Code statt Monkeypatch.

Lädt chemdraw_tool und scripts/identitaet aus dem Haupt-Repo (mit A>= im Code),
bevor mess.py den Worktree 112021f auf sys.path setzt — Python nimmt dann die
schon geladenen Module. Fixtures und Holdout-Listen kommen weiter aus dem
Worktree (Stand der Messung), die Quellenantworten aus memo.json.

Drei Läufe aus demselben Memo:
  basis   — Monkeypatch ohne Regel (Vergleichsgrundlage wie in auswertung.py)
  A>=     — Monkeypatch A>= (die Messung)
  echt    — keine Ersetzung: _pubchem_checked/_opsin_checked aus dem Repo
Gate: echt == A>= Eintrag für Eintrag, 0 Memo-Fehlgriffe, Zählung wie gemessen.

  uv run python replay_echt.py   (Worktree: siehe README)
"""

import json
import sys
from pathlib import Path

MAIN = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(MAIN))
sys.path.insert(0, str(MAIN / "scripts"))
import identitaet  # noqa: E402,F401  (Haupt-Repo zuerst laden)

from chemdraw_tool import resolver as R  # noqa: E402

assert Path(R.__file__).resolve().is_relative_to(MAIN / "chemdraw_tool"), R.__file__
sys.path.insert(0, str(Path(__file__).parent))
import mess  # noqa: E402

assert mess.R is R

ECHT = {"pubchem_checked": R._pubchem_checked, "opsin_checked": R._opsin_checked}


def _vergleich(a, b):
    """Einträge, in denen zwei Läufe verschieden ausgehen."""
    diff = []
    for teil in ("stoffe", "holdout_pubchem", "holdout_opsin"):
        for x, y in zip(a[teil], b[teil], strict=True):
            if teil == "stoffe":
                gx = (x["status"], x.get("erhalten"), x.get("text"), x.get("smiles"))
                gy = (y["status"], y.get("erhalten"), y.get("text"), y.get("smiles"))
            else:
                gx, gy = (x["key"], x["smiles"]), (y["key"], y["smiles"])
            if gx != gy:
                diff.append({"teil": teil, "eintrag": x.get("eingabe") or x.get("name")})
    return diff


def _zaehlung(basis, neu):
    """Wie auswertung.py: grün gekippt / rot→grün (Masse), Holdout gekippt/behoben."""
    z = {"gekippt": [], "rot_zu_gruen": []}
    for b, n in zip(basis["stoffe"], neu["stoffe"], strict=True):
        if b["status"] == "gruen" and n["status"] != "gruen":
            z["gekippt"].append(b["eingabe"])
        elif b["status"] != "gruen" and n["status"] == "gruen":
            z["rot_zu_gruen"].append(b["eingabe"])
    for teil in ("holdout_pubchem", "holdout_opsin"):
        h = {"gekippt": [], "behoben": [], "beide_falsch": []}
        for b, n in zip(basis[teil], neu[teil], strict=True):
            if b["key"] == n["key"]:
                continue
            if n["key"] == b["erwartet"]:
                h["behoben"].append(b["name"])
            elif b["key"] == b["erwartet"]:
                h["gekippt"].append(b["name"])
            else:
                h["beide_falsch"].append(b["name"])
        z[teil] = h
    return z


def main():
    mess.MODE = "replay"
    mess.MEMO.update(json.loads(mess.MEMO_FILE.read_text()))
    mess.install_memo()
    laeufe = {}
    for v in ("basis", "A>="):
        mess.set_variant(v)
        laeufe[v] = mess.run_all(0)
    R._pubchem_checked = ECHT["pubchem_checked"]
    R._opsin_checked = ECHT["opsin_checked"]
    R.resolve_name.cache_clear()
    laeufe["echt"] = mess.run_all(0)
    ergebnis = {
        "memo_fehlgriffe": mess.MISSES,
        "echt_vs_monkeypatch_A>=": _vergleich(laeufe["echt"], laeufe["A>="]),
        "zaehlung_echt": _zaehlung(laeufe["basis"], laeufe["echt"]),
        "gruen_basis": sum(e["status"] == "gruen" for e in laeufe["basis"]["stoffe"]),
        "gruen_echt": sum(e["status"] == "gruen" for e in laeufe["echt"]["stoffe"]),
        "mengen": {t: len(laeufe["echt"][t]) for t in laeufe["echt"]},
    }
    out = Path(__file__).parent / "replay_echt.json"
    out.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1))
    z = ergebnis["zaehlung_echt"]
    print(
        f"Mengen {ergebnis['mengen']} · Memo-Fehlgriffe {len(mess.MISSES)} · "
        f"echt≠A>= {len(ergebnis['echt_vs_monkeypatch_A>='])}\n"
        f"Masse: gekippt {len(z['gekippt'])}, rot→grün {len(z['rot_zu_gruen'])} {z['rot_zu_gruen']}\n"
        f"Holdout PubChem: gekippt {z['holdout_pubchem']['gekippt']}, "
        f"behoben {len(z['holdout_pubchem']['behoben'])}, beide falsch {z['holdout_pubchem']['beide_falsch']}\n"
        f"Holdout OPSIN: {z['holdout_opsin']}\n"
        f"grün basis {ergebnis['gruen_basis']} → echt {ergebnis['gruen_echt']}"
    )


if __name__ == "__main__":
    main()
