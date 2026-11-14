#!/usr/bin/env python3
"""Baut aus den exportierten Anhängen eines Laufs die Checkpoint-Tabelle.

Aufruf: bericht.py <laufordner> <A|B> <sekunden>. Benennt die Anhänge nach ihrem Anzeigenamen um
(panel-*.png, baum-*.txt, Video) und schreibt bericht.md + bericht.json. Exit 1 bei rotem Checkpoint.
"""
import json
import shutil
import sys
from pathlib import Path

lauf, stufe, sekunden = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
anh = lauf / "anhaenge"
manifest = anh / "manifest.json"
ergebnisse, dateien = [], []
if manifest.exists():
    for test in json.loads(manifest.read_text()):
        for a in test.get("attachments", []):
            quelle = anh / a["exportedFileName"]
            name = a.get("suggestedHumanReadableName") or a["exportedFileName"]
            if not quelle.exists():
                continue
            if name.startswith("ergebnis-"):
                ergebnisse.append(json.loads(quelle.read_text()))
                continue
            # Xcode hängt an den Namen eine laufende Kennung; den eigenen Namen wiederherstellen.
            for prefix in ("panel-", "baum-"):
                if name.startswith(prefix):
                    stamm, ext = name.rsplit(".", 1)
                    stamm = stamm.split("_0_")[0]
                    name = f"{stamm}.{ext}"
            # Xcodes eigene Mitschnitte (Debug description, UI Snapshot, Synthesized Event) bleiben im xcresult.
            if not name.startswith(("panel-", "baum-", "Screen Recording")):
                continue
            ziel = lauf / ("bilder" if name.endswith(".png") else "video" if name.endswith((".mp4", ".mov")) else "baeume")
            ziel.mkdir(exist_ok=True)
            shutil.copy2(quelle, ziel / name)
            dateien.append(str((ziel / name).relative_to(lauf)))

zeichen = {"gruen": "✔", "rot": "✘", "befund": "◆"}
rot = befund = gruen = 0
z = [f"# Desktop-Probe Stufe {stufe} — {lauf.name}", "", f"Laufzeit gesamt: {sekunden} s · Tools: {len(ergebnisse)}", ""]
for e in sorted(ergebnisse, key=lambda e: e["tool"]):
    z.append(f"## {e['tool']} ({e['dauer_s']} s)")
    for c in e["checkpoints"]:
        rot += c["status"] == "rot"
        befund += c["status"] == "befund"
        gruen += c["status"] == "gruen"
        info = f" — {c['info']}" if c["info"] else ""
        z.append(f"- {zeichen[c['status']]} {c['name']} ({c['s']} s){info}")
    z.append("")
z.insert(3, f"Checkpoints: {gruen} grün · {rot} rot · {befund} Befund (◆ = kein Fehler des Tests, aber meldenswert)")
if not ergebnisse:
    z.append("Keine Ergebnisse exportiert — siehe xcodebuild.log.")
(lauf / "bericht.md").write_text("\n".join(z) + "\n")
(lauf / "bericht.json").write_text(json.dumps({"stufe": stufe, "sekunden": sekunden, "ergebnisse": ergebnisse, "dateien": dateien}, ensure_ascii=False, indent=1))
print("\n".join(z))
sys.exit(1 if rot or not ergebnisse else 0)
