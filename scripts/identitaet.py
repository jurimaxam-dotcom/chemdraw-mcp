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

Eintraege mit "fehler" (z. B. "invalid_smiles") muessen genau mit dieser
Fehlerart scheitern — loest der Server sie doch auf, ist das ROT: dann hat er
eine kaputte Eingabe still zu irgendeinem Stoff gemacht. Bei
"fehler": "ambiguous" (Familienname wie "xylene") prueft optional
"kandidaten" die InChIKeys der angebotenen Isomere in ihrer Reihenfolge.

Aufruf:  uv run python scripts/identitaet.py [--json] [--datei PFAD] [--protokoll PFAD]
         --datei     andere Fixture gleichen Schemas (Standard: tests/identity/stoffe.json),
                     z. B. tests/identity/stoffe-masse.json (Masse-Evaluation, ~1 h)
         --protokoll Ergebnisse zusätzlich als JSON in diese Datei
Exit 1 nur bei ROT.

Bei falschem Stoff sagt das Feld "art", WIE falsch — die drei Fälle
bedeuten Verschiedenes, der InChIKey trennt sie schichtweise:
    skelett  — erster Block verschieden: anderes Konstitutionsgerüst
    stereo   — Gerüst gleich, Stereoblock verschieden (Racemat vs. Enantiomer)
    ladung   — nur das letzte Zeichen verschieden (Protonierung/Salzform)
    salz     — Schlüssel verschieden, aber größtes Fragment neutralisiert gleich
               (Hydrochlorid statt freier Base o. ä.; nur mit "smiles_referenz")
Einträge mit "unsicher": true (Referenzquellen widersprechen sich) werden
bei Abweichung GELB, nie ROT.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from rdkit import Chem, RDLogger  # noqa: E402
from rdkit.Chem import inchi  # noqa: E402

from chemdraw_tool.resolver import NameResolutionError, resolve  # noqa: E402

RDLogger.DisableLog("rdApp.*")

FIXTURE = REPO / "tests" / "identity" / "stoffe.json"
# Zwischen zwei Anfragen: PubChem bittet um <5 Anfragen/Sekunde, und die
# Kaskade macht je Name mehrere.
PAUSE = 0.3
# Nach "Quelle weg" so lange warten, dann genau einmal neu versuchen.
BACKOFF = 10.0

ROT, GELB, GRUEN = "rot", "gelb", "gruen"


def pruefe(eintrag: dict) -> dict:
    """Eine Zeile der Fixture gegen die echten Quellen halten."""
    eingabe = eintrag["eingabe"]
    luecke = eintrag.get("luecke", False)
    erwartet = eintrag.get("inchikey")
    erwarteter_fehler = eintrag.get("fehler")

    try:
        _, mol = resolve(eingabe)
    except NameResolutionError as fehler:
        if erwarteter_fehler:
            if fehler.kind == erwarteter_fehler:
                erwartete_kandidaten = eintrag.get("kandidaten")
                if erwartete_kandidaten is not None:
                    angeboten = [
                        inchi.MolToInchiKey(Chem.MolFromSmiles(k.smiles))
                        for k in fehler.candidates
                    ]
                    if angeboten != erwartete_kandidaten:
                        return {
                            "status": ROT,
                            "text": f"falsche Kandidaten: {angeboten}",
                        }
                    return {
                        "status": GRUEN,
                        "text": f"mehrdeutig wie erwartet ({len(angeboten)} Kandidaten)",
                    }
                return {"status": GRUEN, "text": f"scheitert wie erwartet ({fehler.kind})"}
            return {
                "status": ROT,
                "text": f"falsche Fehlerart: {fehler.kind} statt {erwarteter_fehler}",
            }
        if fehler.kind in ("offline", "sources_down", "partial"):
            return {"status": GELB, "text": f"Quelle weg ({fehler.kind})"}
        if luecke:
            return {"status": GELB, "text": "bekannte Luecke, weiterhin unauffindbar"}
        return {"status": ROT, "text": f"nicht aufloesbar ({fehler.kind})"}
    except Exception as fehler:  # defekte Eingabe, kaputtes RDKit-Mol
        return {"status": ROT, "text": f"{type(fehler).__name__}: {fehler}"}

    schluessel = inchi.MolToInchiKey(mol)
    if erwarteter_fehler:
        return {
            "status": ROT,
            "text": f"sollte scheitern ({erwarteter_fehler}), lieferte {schluessel}",
        }
    if luecke:
        return {
            "status": GELB,
            "text": f"Luecke geschlossen → {schluessel} (Fixture nachziehen)",
        }
    if schluessel != erwartet:
        art = abweichungsart(schluessel, erwartet)
        referenz = eintrag.get("smiles_referenz")
        if art != "ladung" and referenz and gleicher_elternstoff(mol, referenz):
            art = "salz"
        if eintrag.get("unsicher"):
            return {
                "status": GELB,
                "art": art,
                "erhalten": schluessel,
                "text": f"Referenz unsicher, abweichend ({art}): {schluessel} statt {erwartet}",
            }
        return {
            "status": ROT,
            "art": art,
            "erhalten": schluessel,
            "text": f"falscher Stoff ({art}): {schluessel} statt {erwartet}",
        }
    return {"status": GRUEN, "text": schluessel}


def abweichungsart(erhalten: str, erwartet: str) -> str:
    """Welche InChIKey-Schicht abweicht: skelett, stereo oder ladung."""
    if erhalten[:14] != erwartet[:14]:
        return "skelett"
    if erhalten[:25] != erwartet[:25]:
        return "stereo"
    return "ladung"


def elternkey(mol) -> str | None:
    """InChIKey des größten Fragments, neutralisiert — Salz und freie Base gleich."""
    from rdkit.Chem.MolStandardize import rdMolStandardize

    if mol is None:
        return None
    try:
        teil = rdMolStandardize.LargestFragmentChooser().choose(mol)
        teil = rdMolStandardize.Uncharger().uncharge(teil)
        return inchi.MolToInchiKey(teil)
    except Exception:
        return None


def gleicher_elternstoff(mol, referenz_smiles: str) -> bool:
    a = elternkey(mol)
    return a is not None and a == elternkey(Chem.MolFromSmiles(referenz_smiles))


def _quelle_weg(ergebnis: dict) -> bool:
    return ergebnis["status"] == GELB and ergebnis["text"].startswith("Quelle weg")


def main() -> int:
    parser = argparse.ArgumentParser(description="Name → Molekül gegen die echten Quellen")
    parser.add_argument("--json", action="store_true", help="Ergebnis als JSON auf stdout")
    parser.add_argument("--datei", type=Path, default=FIXTURE, help="Fixture (Schema wie stoffe.json)")
    parser.add_argument("--protokoll", type=Path, help="Ergebnisse zusätzlich als JSON-Datei")
    args = parser.parse_args()
    als_json = args.json
    eintraege = json.loads(args.datei.read_text(encoding="utf-8"))["stoffe"]

    ergebnisse = []
    for nummer, eintrag in enumerate(eintraege, 1):
        start = time.perf_counter()
        ergebnis = pruefe(eintrag)
        if _quelle_weg(ergebnis):
            # Drosselung oder kurzer Ausfall: einmal mit Abstand nachfassen,
            # sonst färbt ein PubChem-Schluckauf den Rest des Laufs gelb.
            time.sleep(BACKOFF)
            ergebnis = pruefe(eintrag)
        sekunden = time.perf_counter() - start
        ergebnis = {
            **ergebnis,
            "eingabe": eintrag["eingabe"],
            "erwartet": eintrag.get("inchikey"),
            "sekunden": round(sekunden, 2),
        }
        ergebnisse.append(ergebnis)
        if not als_json:
            zeichen = {ROT: "✗", GELB: "~", GRUEN: "✓"}[ergebnis["status"]]
            print(
                f"  {zeichen} {nummer:>3} {eintrag['eingabe']:<28} {sekunden:5.1f} s  {ergebnis['text']}",
                flush=True,
            )
        time.sleep(PAUSE)

    if args.protokoll:
        args.protokoll.write_text(
            json.dumps(ergebnisse, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )

    rot = [e for e in ergebnisse if e["status"] == ROT]
    gelb = [e for e in ergebnisse if e["status"] == GELB]

    if als_json:
        print(json.dumps(ergebnisse, ensure_ascii=False, indent=1))
    else:
        print(
            f"\n{len(ergebnisse) - len(rot) - len(gelb)} grün · "
            f"{len(gelb)} gelb (Quelle/Luecke) · {len(rot)} rot (falscher Stoff/Fehler)"
        )
        if rot:
            print("\nROT — hier zeigt der Server etwas anderes an, als der Name sagt:")
            for e in rot:
                print(f"  {e['eingabe']}: {e['text']}")
    return 1 if rot else 0


if __name__ == "__main__":
    raise SystemExit(main())
