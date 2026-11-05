"""Pfeil-Geometrie der Mechanismus-Bilder (Etappe E, 05.11.2026).

Befund: Pfeile begannen und endeten an Atom-Mittelpunkten plus festem Versatz — jede
Beschriftung breiter als der Versatz („HO“, „C⁺“, „Br⁻“, „H⁺“) schluckte das Ende. Dieser Test
prüft jede Substrat-Kombination der Matrix und die drei Vorlagen über den echten Tool-Weg
(`generate_mechanism`). Die Geometrie liest er aus dem Datensatz, den der Renderer ins SVG
legt (`geometry_of`), statt Pfadkoordinaten zurückzurechnen.

Regeln (docs/mechanismus-substrate-design.md, „Pfeil-Geometrie“):
- kein Punkt des Pfeilkörpers (ohne die ersten/letzten 3 px) in einer Beschriftung;
- Spitze: höchstens 0,35 Bindungslängen vor der Beschriftung des Ziels, nie darin;
  unbeschriftetes Ziel → höchstens 0,35 Bindungslängen vom Atom;
- Start: freies Elektronenpaar höchstens 0,35 Bindungslängen neben der Beschriftung der Quelle
  (nie darin), Bindungspfeil höchstens 0,35 Bindungslängen von der Bindungsmitte;
- alle Schritte eines Mechanismus mit derselben Bindungslänge in Pixeln (± 5 %);
- Übergangszustände in eckigen Klammern mit ‡.
"""

from __future__ import annotations

import math
import statistics

import pytest

from chemdraw_tool.mechanism_renderer import geometry_of
from chemdraw_tool.server import generate_mechanism
from tests.mechanism_matrix import MATRIX

CASES = [(cid, rt, subs) for cid, rt, subs, _cip in MATRIX] + [
    (f"vorlage-{rt}", rt, []) for rt in ("sn1", "sn2", "fischer_ester")
]

# Anteil der Bindungslänge, den ein Pfeilende von seinem Anker entfernt sein darf
TOLERANZ = 0.35
# So viele Pixel an beiden Enden des Pfeilkörpers bleiben außer Betracht (Ansatz, Spitze)
ENDEN_PX = 3.0


def _bezier(p0, c, p1, n: int = 40):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1]))
    return pts


def _innen(p, box) -> bool:
    x0, y0, x1, y1 = box
    return x0 < p[0] < x1 and y0 < p[1] < y1


def _abstand_box(p, box) -> float:
    """Abstand eines Punktes zum Rand der Box (0 im Innern)."""
    x0, y0, x1, y1 = box
    dx = max(x0 - p[0], 0.0, p[0] - x1)
    dy = max(y0 - p[1], 0.0, p[1] - y1)
    return math.hypot(dx, dy)


@pytest.fixture(scope="module")
def ergebnisse():
    return {}


def _payload(cache, rt, subs):
    key = (rt, tuple(subs))
    if key not in cache:
        cache[key] = generate_mechanism(rt, list(subs))
    return cache[key]


@pytest.mark.parametrize(("cid", "rt", "subs"), CASES, ids=[c[0] for c in CASES])
def test_pfeile_treffen_keine_beschriftung(ergebnisse, cid, rt, subs):
    payload = _payload(ergebnisse, rt, subs)
    if subs:
        assert payload.substrates_drawn, f"{cid}: Vorlage statt Substrat ({payload.fallback_reason})"
    fehler: list[str] = []
    for nr, step in enumerate(payload.steps, 1):
        geo = geometry_of(step.svg)
        bl = geo["bond_px"]
        assert bl and bl > 10, f"{cid} Schritt {nr}: keine messbare Bindungslänge ({bl})"
        grenze = TOLERANZ * bl
        boxen = {int(k): v for k, v in geo["boxes"].items()}
        mitten = {int(k): v for k, v in geo["centres"].items()}
        hindernisse = geo["obstacles"]
        assert len(geo["arrows"]) == geo["arrows_defined"], (
            f"{cid} Schritt {nr}: {geo['arrows_defined']} Pfeile definiert, {len(geo['arrows'])} gezeichnet"
        )
        for a in geo["arrows"]:
            name = f"{cid} Schritt {nr} ({step.label}) Pfeil {a['src_map']}→{a['tgt_map']}"
            src, ctrl, tip = a["src"], a["ctrl"], a["tip"]
            # Körper
            for p in _bezier(src, ctrl, tip):
                if math.dist(p, src) <= ENDEN_PX or math.dist(p, tip) <= ENDEN_PX:
                    continue
                for box in hindernisse:
                    if _innen(p, box):
                        fehler.append(f"{name}: Körper läuft durch Beschriftung {box} bei {p[0]:.0f},{p[1]:.0f}")
                        break
                else:
                    continue
                break
            # Spitze
            tgt = a["tgt_map"]
            if tgt in boxen:
                box = boxen[tgt]
                if _innen(tip, box):
                    fehler.append(f"{name}: Spitze in der Beschriftung des Ziels")
                elif _abstand_box(tip, box) > grenze:
                    fehler.append(f"{name}: Spitze {_abstand_box(tip, box):.0f}px vor der Beschriftung (> {grenze:.0f})")
            elif math.dist(tip, mitten[tgt]) > grenze:
                fehler.append(f"{name}: Spitze {math.dist(tip, mitten[tgt]):.0f}px vom Atom (> {grenze:.0f})")
            # Start
            quelle = a["src_map"]
            if a["kind"] == "lone_pair":
                if quelle in boxen:
                    box = boxen[quelle]
                    if _innen(src, box):
                        fehler.append(f"{name}: Start auf der Beschriftung der Quelle")
                    elif _abstand_box(src, box) > grenze:
                        fehler.append(f"{name}: Start {_abstand_box(src, box):.0f}px neben der Quelle (> {grenze:.0f})")
                elif math.dist(src, mitten[quelle]) > grenze:
                    fehler.append(f"{name}: Start {math.dist(src, mitten[quelle]):.0f}px vom Atom (> {grenze:.0f})")
            elif a["kind"] == "bond":
                b1, b2 = (mitten[m] for m in a["bond"])
                mitte = ((b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2)
                if math.dist(src, mitte) > grenze:
                    fehler.append(f"{name}: Start {math.dist(src, mitte):.0f}px von der Bindungsmitte (> {grenze:.0f})")
        if step.is_transition_state:
            if not (geo["ts_bracket"] and "class='ts-bracket'" in step.svg and "&#8225;" in step.svg):
                fehler.append(f"{cid} Schritt {nr}: Übergangszustand ohne Klammern und ‡")
    assert not fehler, "\n".join(fehler)


# Befund 05.11.2026, nicht im Renderer zu beheben: in der SN2-Vorlage behält das OH im Produkt
# seinen Platz aus dem Übergangszustand (mechanism_coords.stabilize_sequence) — die C–O-Bindung
# ist 3,4 Bindungslängen lang. Strikt: wird das Layout repariert, ist dieser Fall rot und die
# Markierung muss weg.
_GEDEHNT = {"vorlage-sn2": "SN2-Vorlage: Produkt-C–O-Bindung gedehnt (stabilize_sequence)"}
BL_CASES = [
    pytest.param(*c, id=c[0], marks=pytest.mark.xfail(strict=True, reason=_GEDEHNT[c[0]])) if c[0] in _GEDEHNT
    else pytest.param(*c, id=c[0])
    for c in CASES
]


@pytest.mark.parametrize(("cid", "rt", "subs"), BL_CASES)
def test_alle_schritte_haben_dieselbe_bindungslaenge(ergebnisse, cid, rt, subs):
    payload = _payload(ergebnisse, rt, subs)
    laengen = [geometry_of(s.svg)["bond_px"] for s in payload.steps]
    mitte = statistics.median(laengen)
    for nr, bl in enumerate(laengen, 1):
        assert bl == pytest.approx(mitte, rel=0.05), f"{cid} Schritt {nr}: {bl:.1f}px statt {mitte:.1f}px"


def test_stereodeskriptor_steht_im_sn2_produkt():
    """(R)-2-Brombutan + CN⁻ → (S)-2-Methylbutannitril: das (S) gehört ins Bild, nicht nur in den Text."""
    payload = generate_mechanism("sn2", ["C[C@@H](Br)CC", "[C-]#N"])
    assert "CIP_Code" in payload.steps[0].svg, "Edukt ohne (R)"
    assert "CIP_Code" in payload.steps[-1].svg, "Produkt ohne (S)"


def test_achirales_molekuel_bekommt_keinen_deskriptor():
    payload = generate_mechanism("fischer_ester", ["CC(=O)O", "CCO"])
    assert all("CIP_Code" not in s.svg for s in payload.steps)
