"""Galerie: alle Panel-Typen der gebauten UI als Screenshot + eine Übersichtsseite.

    uv run python tests/gallery_ui.py        # → /tmp/chem-gallery/*.png und sheet.png

Für den Design-Durchgang: schlechte Stellen fallen nebeneinander auf, nicht einzeln.
HOME zeigt auf einen Wegwerf-Ordner, damit nichts in ~/ChemDraw-Output landet.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Browser-Cache vor dem HOME-Wechsel festnageln, sonst sucht Playwright Chromium im Wegwerf-Ordner
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(Path.home() / "Library" / "Caches" / "ms-playwright"))
os.environ["HOME"] = tempfile.mkdtemp(prefix="gallery-home-")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402

from chemdraw_tool import server as s  # noqa: E402
from tests.test_server_anki import _cards  # noqa: E402
from tests.test_server_calibration import SIGNALS, STANDARDS  # noqa: E402
from tests.test_server_scope import ENTRIES  # noqa: E402
from tests.test_server_spectrum import IR_PEAKS  # noqa: E402
from tests.test_server_tlc import ESTER_LANES  # noqa: E402

DIST = Path(__file__).resolve().parent.parent / "chemdraw_tool" / "ui" / "dist" / "index.html"
OUT = Path("/tmp/chem-gallery")


def payloads() -> dict[str, object]:
    return {
        "molecule": lambda: s.generate_molecule("ibuprofen"),
        "compare": lambda: s.compare_molecules(["CC(C)Cc1ccc(cc1)C(C)C(=O)O", "COc1ccc2cc(ccc2c1)C(C)C(=O)O"]),
        "batch": lambda: s.batch_generate(["aspirin", "caffeine", "paracetamol"]),
        "reaction": lambda: s.generate_reaction(["ethanol", "acetic acid"], ["ethyl acetate", "water"], conditions="H2SO4, Δ"),
        "mechanism": lambda: s.generate_mechanism("sn2", ["bromoethane", "hydroxide"]),
        "mechanism_fischer": lambda: s.generate_mechanism("fischer_ester", ["acetic acid", "ethanol"]),
        "mechanism_sn1": lambda: s.generate_mechanism("sn1", ["2-bromo-2-methylpropane", "water"]),
        "pk": lambda: s.generate_pk_curve(500, 70, half_life_h=4.62, ka_per_h=1.2, bioavailability=0.8, tau_h=8, mec_mg_per_l=2, mtc_mg_per_l=6, drug="Wirkstoff X"),
        "dose_response": lambda: s.generate_dose_response(10, "nM", antagonist_concentration=20, antagonist_kb=10, drug="Agonist A"),
        "spectrum": lambda: s.generate_spectrum("ir", IR_PEAKS, title="Aspirin"),
        "tlc": lambda: s.generate_tlc(ESTER_LANES, title="Veresterung"),
        "scope": lambda: s.generate_scope_table(ENTRIES, title="Suzuki scope"),
        "titration": lambda: s.generate_titration_curve("Essigsäure", [4.76], 0.1, 20, 0.1),
        "species": lambda: s.generate_species_distribution("Phosphorsäure", [2.15, 7.2, 12.35]),
        "calibration": lambda: s.generate_calibration_curve(STANDARDS, SIGNALS, substance="Paracetamol"),
        "anki": lambda: s.export_anki_deck("Pharmazie Basics", _cards()),
        "threed": lambda: s.generate_3d("caffeine"),
    }


def main() -> None:
    import json
    import subprocess

    OUT.mkdir(exist_ok=True)
    for alt in OUT.glob("*"):
        alt.unlink()
    for name, make in payloads().items():
        try:
            data = make().model_dump()
        except Exception as e:  # noqa: BLE001 — Galerie soll weiterlaufen
            print(f"✘ {name}: {type(e).__name__}: {e}")
            continue
        (OUT / f"{name}.json").write_text(
            json.dumps({"content": [{"type": "text", "text": name}], "structuredContent": data}, default=str)
        )
    ui = DIST.parent.parent
    subprocess.run(["node", "src/host/gallery.mjs", str(OUT)], cwd=ui, check=True)
    shots = sorted(OUT.glob("*.png"))
    cols = 3
    ims = [Image.open(p) for p in shots]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), "white")
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(OUT / "sheet.png")
    print("→", OUT / "sheet.png", [p.stem for p in shots])


if __name__ == "__main__":
    main()
