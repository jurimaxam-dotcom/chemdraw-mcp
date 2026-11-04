#!/usr/bin/env python3
"""Erzeugt alle Datei-Bilder des README aus den Tools selbst — keine Handarbeit.

Aufruf (Projektordner, auf dem Mac, kein Netz nötig):
    uv run python scripts/readme_bilder.py              # schreibt assets/*.png
    uv run python scripts/readme_bilder.py --pruefen    # rendert zweimal, vergleicht Hashes
    UPDATE_README_BILDER=1 uv run pytest tests/test_readme.py   # Hash-Manifest neu segnen

Regeln, damit gleiche Eingabe gleichen Hash ergibt:
- feste Beispiele, jede Struktur als SMILES (kein Namensauflöser, kein Netz);
  das Datenblatt bekommt PubChem-Antworten aus Fixtures wie in
  tests/test_server_lookup_ui.py, der Scope dieselbe Suzuki-Reihe wie im README.
  Eine Socket-Sperre macht jeden versteckten Netzaufruf zu einem lauten Fehler.
- jede PNG verliert ihre Text-/Zeitchunks (tEXt, iTXt, zTXt, tIME) — das nimmt
  auch die matplotlib-Version aus dem Hash.
- SVG → PNG (Mechanismus-Schritte, Datenblatt-Struktur) über rsvg-convert
  (librsvg, kein Browser; `brew install librsvg`).

Die Ausgabe der Tools landet in einem Wegwerf-Ordner (alle *_DIR des Servers
umgebogen), nie in ~/ChemDraw-Output.

Bildklassen und Rendergrößen:
- Tool-Grafiken (Struktur, Spektrum, DC, pH-, PK-, Hill-Kurve, Scope): genau
  die PNG, die das Tool schreibt — Größe bestimmt das Tool.
- Galerie (Mechanismen, 3D): 1500 × 560 bzw. 560 × 560 px.
- Karten (Look up, Calculate, Anki): 1500 × 860 px.

wave1-3d.png entsteht ohne Browser: die Atomkoordinaten aus generate_3d
(fester ETKDG-Seed) als Kugel-Stab-Projektion in matplotlib. Das Panel selbst
ist eine WebGL-Ansicht, die nur ein Browser zeigen kann.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import textwrap
import zipfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

import chemdraw_tool.server as s  # noqa: E402

ASSETS = ROOT / "assets"
DPI = 100
CARD = (1500, 860)
GALLERY = (1500, 560)
INK = "#1C1C1E"
MUTED = "#6B6B6B"
PAPER = "#FAFAF7"
LINE = "#D8D8D2"
ACCENT = "#1F7A6D"

CAFFEINE = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"

# Reihenfolge = Reihenfolge im README.
BILDER = [
    "caffeine.png",
    "wave1-mechanisms.png",
    "wave1-3d.png",
    "aspirin-ir.png",
    "tlc-wave2.png",
    "wave2-titration-acetic.png",
    "wave2-species-phosphoric.png",
    "lookup-datasheet.png",
    "calculate-ph.png",
    "anki-card.png",
    "scope-suzuki.png",
    "pk-curve.png",
    "dose-response.png",
]


# --- Werkzeuge: PNG säubern, kein Netz, Wegwerf-Ausgabe -----------------------

_DROP = {b"tEXt", b"iTXt", b"zTXt", b"tIME"}


def clean_png(data: bytes) -> bytes:
    """Entfernt Text- und Zeitchunks; IDAT bleibt Byte für Byte, wie es war."""
    sig, out, pos = data[:8], [data[:8]], 8
    assert sig == b"\x89PNG\r\n\x1a\n", "keine PNG"
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind = data[pos + 4 : pos + 8]
        end = pos + 12 + length
        if kind not in _DROP:
            out.append(data[pos:end])
        pos = end
    return b"".join(out)


@contextmanager
def offline():
    """Jeder Verbindungsversuch wird ein Fehler — sonst driften Hashes mit PubChem."""

    def refuse(*_a, **_k):
        raise RuntimeError("readme_bilder.py: Netzaufruf — Beispiel braucht SMILES/Fixture")

    # generate_molecule ergänzt CAS & Co. aus PubChem und fängt Fehler still ab —
    # ohne Netz ist das „kein Datensatz“; die Zeichnung hängt nicht daran.
    with (
        patch.object(socket.socket, "connect", refuse),
        patch.object(socket, "create_connection", refuse),
        patch.object(s, "pubchem_properties_by_inchikey", return_value=None),
        patch.object(s, "pubchem_synonyms_by_inchikey", return_value=(None, [])),
        patch.object(s, "pubchem_properties_by_smiles", return_value=None),
        patch.object(s, "pubchem_synonyms_by_smiles", return_value=(None, [])),
    ):
        yield


@contextmanager
def tool_output():
    with tempfile.TemporaryDirectory(prefix="readme-bilder-") as tmp:
        names = [n for n in dir(s) if n.endswith("_DIR")]
        old = {n: getattr(s, n) for n in names}
        for n in names:
            setattr(s, n, Path(tmp) / n.lower())
        try:
            yield Path(tmp)
        finally:
            for n, v in old.items():
                setattr(s, n, v)


def tool_png(payload) -> bytes:
    return clean_png(Path(payload.files["png"]).read_bytes())


def svg_to_png(svg: str, width: int) -> bytes:
    exe = shutil.which("rsvg-convert")
    if exe is None:
        raise SystemExit("rsvg-convert fehlt — brew install librsvg")
    svg = re.sub(r"\bwidth='100%'", f"width='{width}'", svg, count=1)
    return subprocess.run(
        [exe, "-w", str(width), "-b", PAPER],
        input=svg.encode("utf-8"),
        capture_output=True,
        check=True,
    ).stdout


def png_array(data: bytes):
    """RGBA auf Kartenpapier legen — transparente Ränder sonst mit Interpolations-Säumen."""
    import numpy as np
    from PIL import Image

    img = Image.open(io.BytesIO(data)).convert("RGBA")
    paper = Image.new("RGBA", img.size, PAPER)
    return np.asarray(Image.alpha_composite(paper, img).convert("RGB"))


def figure(size: tuple[int, int]):
    fig = plt.figure(figsize=(size[0] / DPI, size[1] / DPI), dpi=DPI, facecolor="white")
    return fig


def save(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor=fig.get_facecolor(), metadata={"Software": None})
    plt.close(fig)
    return clean_png(buf.getvalue())


def panel(fig, rect, title: str = ""):
    """Karte mit abgerundetem Rahmen; liefert eine Achse ohne Ticks (0..1)."""
    ax = fig.add_axes(rect)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(
        FancyBboxPatch(
            (0.005, 0.005), 0.99, 0.99, boxstyle="round,pad=0,rounding_size=0.02",
            transform=ax.transAxes, facecolor=PAPER, edgecolor=LINE, linewidth=1.2,
        )
    )
    if title:
        ax.text(0.04, 0.94, title, fontsize=15, fontweight="bold", color=INK, va="top")
    return ax


def image_in(fig, rect, data: bytes):
    ax = fig.add_axes(rect)
    ax.imshow(png_array(data), interpolation="antialiased")
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


# --- Tool-Grafiken --------------------------------------------------------------


def caffeine() -> bytes:
    return tool_png(s.generate_molecule(CAFFEINE))


def aspirin_ir() -> bytes:
    peaks = [
        {"position": 3000, "intensity": 0.45, "width": 260, "label": "O–H (broad)"},
        {"position": 1750, "intensity": 1.0, "width": 18, "label": "C=O (ester + acid)"},
        {"position": 1690, "intensity": 0.95, "width": 18},
        {"position": 1605, "intensity": 0.4, "width": 14, "label": "Aromatic C=C"},
        {"position": 1190, "intensity": 0.65, "width": 18, "label": "C–O"},
    ]
    return tool_png(s.generate_spectrum("ir", peaks, title="Aspirin (schematic)"))


def tlc() -> bytes:
    lanes = [
        {"name": "Starting material", "spots": [{"rf": 0.30, "label": "Acid"}]},
        {"name": "Product", "spots": [{"rf": 0.65, "label": "Ester"}]},
        {"name": "Co-spot", "spots": [{"rf": 0.30}, {"rf": 0.65}]},
    ]
    return tool_png(
        s.generate_tlc(lanes, title="Esterification TLC", solvent="Hexane/ethyl acetate 7:3",
                       detection="UV 254 nm")
    )


TITRATION = dict(substance="Acetic acid with NaOH", pka_values=[4.76], c_acid=0.1,
                 v_acid_ml=25, c_titrant=0.1,
                 indicator={"name": "Phenolphthalein", "ph_range": [8.2, 10.0]})


def titration() -> bytes:
    return tool_png(s.generate_titration_curve(**TITRATION))


def species() -> bytes:
    return tool_png(s.generate_species_distribution("Phosphoric acid", [2.15, 7.20, 12.35]))


def scope() -> bytes:
    entries = [
        {"structure": "Cc1ccc(-c2ccccc2)cc1", "label": "3a", "yield_text": "92"},
        {"structure": "COc1ccc(-c2ccccc2)cc1", "label": "3b", "yield_text": "88", "notes": "12 h"},
        {"structure": "O=C(O)c1ccc(-c2ccccc2)cc1", "label": "3c", "yield_text": "64",
         "notes": "ee 94%, dr 10:1"},
        {"structure": "c1ccc(-c2cccnc2)cc1", "label": "3d", "yield_text": "71"},
    ]
    reaction = {"reactants": ["Brc1ccccc1", "OB(O)c1ccccc1"], "products": ["c1ccc(-c2ccccc2)cc1"],
                "conditions": "Pd(PPh3)4 (2 mol%), K2CO3 (2 eq), toluene/H2O 4:1, 80 °C, 12 h"}
    return tool_png(s.generate_scope_table(entries, title="Suzuki coupling of aryl bromides",
                                           reaction=reaction, columns=4))


def pk() -> bytes:
    return tool_png(s.generate_pk_curve(dose_mg=500, vd_l=70, ke_per_h=0.15, ka_per_h=1.2,
                                        bioavailability=0.8, tau_h=8, mec_mg_per_l=2,
                                        mtc_mg_per_l=6, drug="Drug X"))


def dose_response() -> bytes:
    return tool_png(s.generate_dose_response(ec50=10, unit="nM", antagonist_concentration=20,
                                             antagonist_kb=10, drug="Agonist A"))


# --- Galerie: Mechanismen und 3D -------------------------------------------------

MECHANISMS = [
    ("sn1", [r"CC(C)Br", "O"]),
    ("sn2", ["CBr", "[OH-]"]),
    ("fischer_ester", ["CC(=O)O", "CO"]),
]


def mechanisms() -> bytes:
    fig = figure(GALLERY)
    w = 1 / 3
    for i, (kind, substrates) in enumerate(MECHANISMS):
        p = s.generate_mechanism(kind, substrates, current_step=2)
        step = p.steps[1]
        title = p.name.split(" — ")[0]
        ax = panel(fig, [i * w + 0.008, 0.02, w - 0.016, 0.96])
        ax.text(0.5, 0.93, title, ha="center", va="top", fontsize=14, fontweight="bold", color=INK)
        ax.text(0.5, 0.855, f"Step 2 / {len(p.steps)}", ha="center", va="top", fontsize=11,
                color=MUTED)
        label = f"[{step.label}]‡" if step.is_transition_state else step.label
        ax.text(0.5, 0.79, label, ha="center", va="top", fontsize=12,
                color=ACCENT if step.is_transition_state else INK)
        image_in(fig, [i * w + 0.03, 0.06, w - 0.06, 0.62], svg_to_png(step.svg, 900))
    return save(fig)


_CPK = {"C": "#3A3A3A", "H": "#F2F2F2", "N": "#3050F8", "O": "#E8302A", "S": "#E0C030"}
_RADIUS = {"H": 0.22}


def threed() -> bytes:
    import numpy as np

    p = s.generate_3d(CAFFEINE, label="Caffeine")
    xyz = np.array([[a["x"], a["y"], a["z"]] for a in p.atoms], dtype=float)
    xyz -= xyz.mean(axis=0)
    # Hauptachsen: größte Ausdehnung waagrecht, kleinste in die Tiefe — dann leicht kippen.
    _, _, vt = np.linalg.svd(xyz)
    xyz = xyz @ vt.T
    tilt = np.radians(25)
    rot = np.array([[1, 0, 0], [0, np.cos(tilt), -np.sin(tilt)], [0, np.sin(tilt), np.cos(tilt)]])
    xyz = xyz @ rot.T
    fig = figure((560, 560))
    panel(fig, [0.01, 0.01, 0.98, 0.98], "Caffeine — 3D conformer")
    view = fig.add_axes([0.06, 0.04, 0.88, 0.82])
    view.set_aspect("equal")
    view.axis("off")
    span = np.abs(xyz[:, :2]).max() + 0.8
    view.set_xlim(-span, span)
    view.set_ylim(-span, span)
    elements = [a["symbol"] for a in p.atoms]
    items = []
    for b in p.bonds:
        i, j = b["a"], b["b"]
        items.append((min(xyz[i, 2], xyz[j, 2]) - 0.01, "bond", (i, j)))
    for i in range(len(xyz)):
        items.append((xyz[i, 2], "atom", i))
    for _, kind, ref in sorted(items, key=lambda t: (t[0], t[1], str(t[2]))):
        if kind == "bond":
            i, j = ref
            view.plot(xyz[[i, j], 0], xyz[[i, j], 1], color="#8A8A8A", lw=4.5,
                      solid_capstyle="round", zorder=1)
        else:
            el = elements[ref]
            r = _RADIUS.get(el, 0.34)
            view.add_patch(plt.Circle(xyz[ref, :2], r, facecolor=_CPK.get(el, "#B0B0B0"),
                                      edgecolor="#2A2A2A", lw=0.8, zorder=2))
            view.add_patch(plt.Circle(xyz[ref, :2] + r * np.array([-0.3, 0.3]), r * 0.28,
                                      facecolor="white", alpha=0.35, lw=0, zorder=2))
    return save(fig)


# --- Karten: Look up, Calculate, Anki ---------------------------------------------

_FIXTURES = ROOT / "tests" / "__fixtures__"
# PubChem-Antwort für Koffein (CID 2519), so wie die Lookup-Tests sie mocken.
_CAFFEINE_PROPS = {
    "CID": 2519,
    "IUPACName": "1,3,7-trimethylpurine-2,6-dione",
    "MolecularFormula": "C8H10N4O2",
    "MolecularWeight": 194.19,
    "XLogP": -0.1,
    "TPSA": 58.4,
    "HBondDonorCount": 0,
    "HBondAcceptorCount": 3,
    "InChIKey": "RYYVLZVUVIJVGH-UHFFFAOYSA-N",
}


def _datasheet():
    from rdkit import Chem
    from rdkit.Chem import AllChem

    from chemdraw_tool import databases

    mol = Chem.MolFromSmiles(CAFFEINE)
    AllChem.Compute2DCoords(mol)
    ghs = json.loads((_FIXTURES / "pubchem_ghs_2519_caffeine.json").read_text(encoding="utf-8"))
    with (
        patch.object(s, "resolve", return_value=(CAFFEINE, mol)),
        patch.object(s, "pubchem_properties_by_inchikey", return_value=_CAFFEINE_PROPS),
        patch.object(s, "pubchem_synonyms_by_inchikey", return_value=("58-08-2", ["Caffeine"])),
        patch.object(s, "pubchem_ghs", return_value={"status": "ok", **databases.parse_ghs(ghs)}),
        patch.object(s, "pubchem_properties_by_smiles", return_value=None),
        patch.object(s, "pubchem_synonyms_by_smiles", return_value=(None, [])),
    ):
        return s.lookup_molecule_data("caffeine")


def lookup_card() -> bytes:
    p = _datasheet()
    fig = figure(CARD)
    panel(fig, [0.01, 0.015, 0.98, 0.97], "Caffeine — data sheet (lookup_molecule_data)")
    image_in(fig, [0.03, 0.08, 0.36, 0.74], svg_to_png(p.molecule_svg, 700))
    ax = fig.add_axes([0.42, 0.05, 0.55, 0.82])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    pub = next(src for src in p.sources if src.type == "PubChem")
    ghs = next((src for src in p.sources if src.type == "GHS"), None)
    y = 0.97
    ax.text(0, y, f"PubChem · {pub.source}", fontsize=12, color=MUTED, va="top")
    y -= 0.07
    for row in pub.rows[:9]:
        ax.text(0, y, row.key, fontsize=13, color=MUTED, va="top")
        ax.text(0.34, y, _wrap(row.val, 42), fontsize=13, color=INK, va="top")
        y -= 0.065 * (1 + row.val.count(" ") // 99 + (len(row.val) > 42))
    if ghs and ghs.groups:
        y -= 0.03
        ax.plot([0, 1], [y + 0.02, y + 0.02], color=LINE, lw=1)
        g = ghs.groups[0]
        ax.text(0, y, "GHS", fontsize=12, color=MUTED, va="top")
        y -= 0.065
        signal = g.signal
        if signal:
            ax.text(0, y, "Signal word", fontsize=13, color=MUTED, va="top")
            ax.text(0.34, y, signal, fontsize=13, color="#B3261E", fontweight="bold", va="top")
            y -= 0.065
        for h in g.hazards[:3]:
            ax.text(0, y, h.code, fontsize=13, color=MUTED, va="top")
            ax.text(0.34, y, _wrap(h.text, 42), fontsize=13, color=INK, va="top")
            y -= 0.065 * (1 + (len(h.text) > 42))
    return save(fig)


def _wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width)) or text


def _markdown(ax, text: str, x: float, y: float, width: int = 52) -> None:
    """Die Textantwort des Tools, leicht gesetzt: #, **fett**, - Liste, `Formel`."""
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            y -= 0.025
            continue
        indent = (len(line) - len(line.lstrip())) // 2
        line = line.strip()
        size, weight, color, step = 14, "normal", INK, 0.054
        if line.startswith("## "):
            line, size, weight, color = line[3:], 14, "bold", MUTED
        elif line.startswith("# "):
            line, size, weight, step = line[2:], 16, "bold", 0.075
        elif line.startswith("**") and line.endswith("**"):
            line, size, weight, color, step = line.strip("*"), 26, "bold", ACCENT, 0.1
        if line.startswith("- "):
            line = "•  " + line[2:]
        line = line.replace("**", "").replace("`", "")
        wrapped = textwrap.wrap(line, width - 3 * indent, subsequent_indent="    ")
        for part in wrapped:
            ax.text(x + 0.04 * indent, y, part, fontsize=size, fontweight=weight, color=color,
                    va="top")
            y -= step


def calculate_card() -> bytes:
    cases = [
        ("What is the pH of 0.1 M acetic acid, pKa 4.76?",
         s.calculate_ph(topic="weak_acid", concentration=0.1, pka=4.76)),
        ("And of 10⁻⁸ M HCl?", s.calculate_ph(topic="strong_acid", concentration=1e-8)),
    ]
    fig = figure(CARD)
    for i, (prompt, answer) in enumerate(cases):
        ax = panel(fig, [0.01 + i * 0.495, 0.015, 0.485, 0.97])
        ax.text(0.05, 0.95, f"“{prompt}”", fontsize=13, style="italic", color=MUTED, va="top")
        ax.text(0.05, 0.895, "calculate_ph", fontsize=12, family="monospace", color=MUTED,
                va="top")
        _markdown(ax, answer, 0.05, 0.82)
    return save(fig)


def anki_card() -> bytes:
    p = s.export_anki_deck(
        deck_name="NSAIDs",
        cards=[{"front": {"text": "Name this structure", "structure": ASPIRIN},
                "back": {"text": "Aspirin (acetylsalicylic acid)"}}],
    )
    with zipfile.ZipFile(p.file) as z, tempfile.TemporaryDirectory() as tmp:
        media = json.loads(z.read("media"))
        z.extract("collection.anki2", tmp)
        con = sqlite3.connect(Path(tmp) / "collection.anki2")
        (fields,) = con.execute("select flds from notes").fetchone()
        con.close()
        front_html, back_html = fields.split("\x1f")
        image_name = re.search(r'src="([^"]+)"', front_html).group(1)
        key = next(k for k, v in media.items() if v == image_name)
        image = z.read(key)
    front_text = re.sub(r"<[^>]+>", "", front_html.split("<img")[0]).strip()
    back_text = re.sub(r"<[^>]+>", "", back_html).strip()
    fig = figure(CARD)
    for i, side in enumerate(["Front", "Back"]):
        ax = panel(fig, [0.01 + i * 0.495, 0.015, 0.485, 0.97])
        ax.text(0.05, 0.95, f"{side} · deck “{p.name}”", fontsize=12, color=MUTED, va="top")
        ax.text(0.5, 0.86, front_text, fontsize=16, color=INK, ha="center", va="top")
        left = 0.01 + i * 0.495
        if side == "Front":
            image_in(fig, [left + 0.06, 0.08, 0.365, 0.66], image)
        else:
            image_in(fig, [left + 0.12, 0.42, 0.245, 0.36], image)
            ax.plot([0.08, 0.92], [0.38, 0.38], color=LINE, lw=1.5)
            ax.text(0.5, 0.3, back_text, fontsize=18, fontweight="bold", color=INK,
                    ha="center", va="top")
    return save(fig)


RENDER = {
    "caffeine.png": caffeine,
    "wave1-mechanisms.png": mechanisms,
    "wave1-3d.png": threed,
    "aspirin-ir.png": aspirin_ir,
    "tlc-wave2.png": tlc,
    "wave2-titration-acetic.png": titration,
    "wave2-species-phosphoric.png": species,
    "lookup-datasheet.png": lookup_card,
    "calculate-ph.png": calculate_card,
    "anki-card.png": anki_card,
    "scope-suzuki.png": scope,
    "pk-curve.png": pk,
    "dose-response.png": dose_response,
}
assert list(RENDER) == BILDER


def render_all(target: Path) -> dict[str, str]:
    """Rendert jedes Bild nach target, liefert {name: sha256}."""
    target.mkdir(parents=True, exist_ok=True)
    hashes = {}
    with offline(), tool_output():
        for name, fn in RENDER.items():
            data = fn()
            (target / name).write_bytes(data)
            hashes[name] = hashlib.sha256(data).hexdigest()
    return hashes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ziel", type=Path, default=ASSETS)
    ap.add_argument("--pruefen", action="store_true",
                    help="zweimal in Wegwerf-Ordner rendern und Hashes vergleichen")
    args = ap.parse_args()
    if args.pruefen:
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first, second = render_all(Path(a)), render_all(Path(b))
        diff = [n for n in BILDER if first[n] != second[n]]
        for n in BILDER:
            print(f"{'gleich ' if n not in diff else 'ANDERS '} {first[n][:16]}  {n}")
        print("deterministisch" if not diff else f"NICHT deterministisch: {diff}")
        return 1 if diff else 0
    for name, digest in render_all(args.ziel).items():
        print(f"{digest[:16]}  {args.ziel / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
