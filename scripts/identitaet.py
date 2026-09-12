#!/usr/bin/env python3
"""Identitaets-Pruefung: Name → Molekuel, gegen die echten Quellen.

Der Rest des Projekts prueft, was mit einem Molekuel passiert, nachdem es
aufgeloest ist: Rendering (Golden-SVG), Tooltexte (Snapshots), Struktur-Sanity
(Validator). Der eine Schritt davor ist ungeprueft — und er ist der einzige,
der alles darunter *konsistent* falsch machen kann: greift `resolve()` daneben,
stimmen Zeichnung, Formel, Masse und CAS untereinander perfekt ueberein, nur
eben fuer den falschen Stoff. `tests/test_resolver.py` laeuft komplett ueber
Mocks und kann das prinzipiell nicht sehen.

Darum diese Liste: Eingabe → erwarteter InChIKey, live gegen OPSIN/PubChem/NCI.

Warum NICHT im Auto-Gate (./test.sh), sondern neben scripts/handshake.sh:
das hier braucht Netz. Ein Ausfall bei PubChem wuerde den Loop sonst rot
faerben, ohne dass eine Zeile Code kaputt ist — und ein Gate, das aus fremden
Gruenden rot wird, wird ignoriert. Deshalb trennt der Lauf hart:

    ROT   — aufgeloest, aber der falsche Stoff (oder gar nicht auffindbar,
            obwohl er es sein muesste). Das ist ein Befund.
    GELB  — Quelle weg (offline/sources_down/partial) oder eine bekannte
            Luecke, die sich bewegt hat. Kein Fehler, aber sichtbar.

Aufruf:  uv run python scripts/identitaet.py [--json]
Exit 1 nur bei ROT.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from rdkit import RDLogger  # noqa: E402
from rdkit.Chem import inchi  # noqa: E402

from chemdraw_tool.resolver import NameResolutionError, resolve  # noqa: E402

RDLogger.DisableLog("rdApp.*")

FIXTURE = REPO / "tests" / "identity" / "stoffe.json"
# Zwischen zwei Anfragen: PubChem bittet um <5 Anfragen/Sekunde, und die
# Kaskade macht je Name mehrere.
PAUSE = 0.3

ROT, GELB, GRUEN = "rot", "gelb", "gruen"


def pruefe(eintrag: dict) -> dict:
    """Eine Zeile der Fixture gegen die echten Quellen halten."""
    eingabe = eintrag["eingabe"]
    luecke = eintrag.get("luecke", False)
    erwartet = eintrag.get("inchikey")

    try:
        _, mol = resolve(eingabe)
    except NameResolutionError as fehler:
        if fehler.kind in ("offline", "sources_down", "partial"):
            return {"status": GELB, "text": f"Quelle weg ({fehler.kind})"}
        if luecke:
            return {"status": GELB, "text": "bekannte Luecke, weiterhin unauffindbar"}
        return {"status": ROT, "text": f"nicht aufloesbar ({fehler.kind})"}
    except Exception as fehler:  # defekte Eingabe, kaputtes RDKit-Mol
        return {"status": ROT, "text": f"{type(fehler).__name__}: {fehler}"}

    schluessel = inchi.MolToInchiKey(mol)
    if luecke:
        return {
            "status": GELB,
            "text": f"Luecke geschlossen → {schluessel} (Fixture nachziehen)",
        }
    if schluessel != erwartet:
        return {
            "status": ROT,
            "text": f"falscher Stoff: {schluessel} statt {erwartet}",
        }
    return {"status": GRUEN, "text": schluessel}


def main() -> int:
    als_json = "--json" in sys.argv
    eintraege = json.loads(FIXTURE.read_text(encoding="utf-8"))["stoffe"]

    ergebnisse = []
    for eintrag in eintraege:
        ergebnis = {**pruefe(eintrag), "eingabe": eintrag["eingabe"]}
        ergebnisse.append(ergebnis)
        if not als_json:
            zeichen = {ROT: "✗", GELB: "~", GRUEN: "✓"}[ergebnis["status"]]
            print(f"  {zeichen} {eintrag['eingabe']:<28} {ergebnis['text']}")
        time.sleep(PAUSE)

    rot = [e for e in ergebnisse if e["status"] == ROT]
    gelb = [e for e in ergebnisse if e["status"] == GELB]

    if als_json:
        print(json.dumps(ergebnisse, ensure_ascii=False, indent=1))
    else:
        print(
            f"\n{len(ergebnisse) - len(rot) - len(gelb)} grün · "
            f"{len(gelb)} gelb (Quelle/Luecke) · {len(rot)} rot (falscher Stoff)"
        )
        if rot:
            print("\nROT — hier zeigt der Server etwas anderes an, als der Name sagt:")
            for e in rot:
                print(f"  {e['eingabe']}: {e['text']}")
    return 1 if rot else 0


if __name__ == "__main__":
    raise SystemExit(main())
