"""Kontaktbogen der Mechanismus-Matrix: je Fall eine Zeile, alle Schritte nebeneinander.

    uv run python scripts/kontaktbogen.py <ausgabeordner> [sn2|sn1|fischer_ester]

Zeichnet jeden Fall aus tests/mechanism_matrix.py über generate_mechanism (der echte Tool-Weg),
schreibt je Schritt SVG + PNG und setzt daraus kontakt-<familie>.png zusammen — das Bild für die
Sichtung durch einen Gutachter oder Jays 10-Sekunden-Blick. Hinweise (E1/E2) stehen hinter dem Titel,
reversible Mechanismen bekommen ⇌ zwischen den Schritten — beides wie im Panel. Braucht rsvg-convert und ImageMagick
(`magick`). Die Schrift muss „⁺“ und „δ“ kennen (Arial zeigte „H  regenerated“ ohne ⁺).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chemdraw_tool.server import generate_mechanism  # noqa: E402
from tests.mechanism_matrix import MATRIX  # noqa: E402

FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
STEP_PX = 420


def _font() -> str:
    for path in FONT_CANDIDATES:
        if Path(path).is_file():
            return path
    raise SystemExit("keine Schrift mit ⁺/δ gefunden: " + ", ".join(FONT_CANDIDATES))


def _run(*args: object) -> None:
    subprocess.run([str(a) for a in args], check=True)


def main(argv: list[str]) -> Path:
    if not argv or len(argv) > 2:
        raise SystemExit(__doc__)
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    family = argv[1] if len(argv) > 1 else None
    font = _font()
    rows = []
    for case_id, reaction_type, substrates, _cip in MATRIX:
        if family and reaction_type != family:
            continue
        payload = generate_mechanism(reaction_type, substrates)
        pngs = []
        for i, step in enumerate(payload.steps):
            svg, png, labelled = (out / f"{case_id}-{i}{suffix}" for suffix in (".svg", ".png", "-l.png"))
            svg.write_text(step.svg.replace("width='100%'", f"width='{STEP_PX}'"), encoding="utf-8")
            _run("rsvg-convert", "-w", STEP_PX, "-b", "white", svg, "-o", png)
            _run("magick", png, "-gravity", "North", "-splice", "0x26", "-font", font, "-pointsize", "15",
                 "-annotate", "+0+4", f"{i + 1}. {step.label}", labelled)
            pngs.append(labelled)
        if payload.reversible:
            # Gleichgewicht (Fischer): ⇌ zwischen den Schritten, wie im Panel
            eq = out / "equilibrium.png"
            _run("magick", "-size", "40x420", "xc:white", "-font", font, "-pointsize", "30", "-gravity", "center",
                 "-annotate", "+0+0", "⇌", eq)
            pngs = [p for png in pngs for p in (png, eq)][:-1]
        row = out / f"{case_id}-row.png"
        title = payload.name + "".join(f"   ▸ {note}" for note in payload.notes)
        _run("magick", *pngs, "-gravity", "center", "+append", "-gravity", "NorthWest", "-splice", "0x30",
             "-font", font, "-pointsize", "18", "-annotate", "+8+4", title, row)
        rows.append(row)
    if not rows:
        raise SystemExit(f"keine Matrixfälle für '{family}'")
    sheet = out / f"kontakt-{family or 'alle'}.png"
    _run("magick", *rows, "-background", "white", "-append", "-resize", "2400x>", sheet)
    print(sheet)
    return sheet


if __name__ == "__main__":
    main(sys.argv[1:])
