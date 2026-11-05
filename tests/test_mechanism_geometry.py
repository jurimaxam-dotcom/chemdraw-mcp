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
import re
import statistics

import pytest

from chemdraw_tool.mechanism_renderer import geometry_of
from chemdraw_tool.server import generate_mechanism
from tests.mechanism_matrix import MATRIX

# Kein Netz: SMILES-Eingaben lösen einen PubChem-Titel-Nachschlag aus (tests/conftest.py)
pytestmark = pytest.mark.usefixtures("kein_netz", "titel_offline")

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
            if a.get("tgt_bond"):
                b1, b2 = (mitten[m] for m in a["tgt_bond"])
                mitte = ((b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2)
                if math.dist(tip, mitte) > grenze:
                    fehler.append(f"{name}: Spitze {math.dist(tip, mitte):.0f}px von der Bindungsmitte (> {grenze:.0f})")
            elif tgt in boxen:
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


# Die SN2-Vorlage dehnte die Produkt-C–O-Bindung (stabilize_sequence) — seit Etappe E laufen die
# Vorlagen durch layout_anchored, die strikte xfail-Markierung ist weg.
BL_CASES = CASES


@pytest.mark.parametrize(("cid", "rt", "subs"), BL_CASES, ids=[c[0] for c in BL_CASES])
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


@pytest.mark.parametrize(("cid", "rt", "subs"), CASES, ids=[c[0] for c in CASES])
def test_kein_geruest_kohlenstoff_traegt_ein_c(ergebnisse, cid, rt, subs):
    """Kontaktbogen 05.11.2026: im 1-Methylcyclohexyl-Kation stand an einem Ring-C ein „C“.

    RDKit beschriftet ein neutrales Gerüst-C nur, wenn seine zwei Bindungen auf einer Linie liegen
    — ein Ring mit 180° an einem Atom ist kein Sechseck mehr. Erlaubt: das Reaktionszentrum (Map 1)
    im Übergangszustand, dort steht es frei zwischen den Teilbindungen. (Ein Nitril-C beschriftet
    RDKit nicht — gemessen über die Matrix.)
    """
    payload = _payload(ergebnisse, rt, subs)
    fehler = []
    for nr, step in enumerate(payload.steps, 1):
        erlaubt = {1} if step.is_transition_state else set()
        for m in geometry_of(step.svg)["labelled_carbons"]:
            if m in erlaubt:
                continue
            fehler.append(f"{cid} Schritt {nr} ({step.label}): Kohlenstoff mit Map {m} trägt ein „C“")
    assert not fehler, "\n".join(fehler)


@pytest.mark.parametrize(("cid", "rt", "subs"), CASES, ids=[c[0] for c in CASES])
def test_alle_schritte_teilen_eine_viewbox(ergebnisse, cid, rt, subs):
    """Kontaktbogen 05.11.2026: 1-Bromoctan im Edukt riesig, im Übergangszustand winzig — jeder
    Schritt hatte seine eigene viewBox, der Betrachter zieht jede auf dieselbe Breite. Gleiche
    viewBox = gleicher Maßstab (unify_frames, aufgerufen in generate_mechanism)."""
    import re

    payload = _payload(ergebnisse, rt, subs)
    boxen = [re.findall(r"viewBox='([^']*)'", s.svg) for s in payload.steps]
    assert all(len(b) == 1 for b in boxen), f"{cid}: nicht genau eine viewBox je SVG"
    assert len({b[0] for b in boxen}) == 1, f"{cid}: {len({b[0] for b in boxen})} verschiedene viewBoxen"


_GLYPH = re.compile(r"<path class='atom-(\d+)' d='([^']*)'")
_BOND_LINE = re.compile(r"<path class='bond-\d+[^']*' d='M ([\d.-]+),([\d.-]+) L ([\d.-]+),([\d.-]+)'")
_ZAHL = re.compile(r"-?\d+(?:\.\d+)?")
# Halbe Strichstärke der Bindungen (bondLineWidth 2.5): so weit reicht die Linie über ihre Mitte
_HALBER_STRICH = 1.25


@pytest.mark.parametrize(("cid", "rt", "subs"), CASES, ids=[c[0] for c in CASES])
def test_keine_bindung_laeuft_durch_ein_beschriftungszeichen(ergebnisse, cid, rt, subs):
    """Sichtung 05.11.2026 (R1): im Azid lag das „⁻“ des endständigen N unter der Doppelbindung —
    RDKit setzt die Ladung oben rechts, auch wenn die Bindung nach rechts geht; der Leser sah
    N=N⁺=N⁻ statt ⁻N=N⁺=N⁻. Geprüft wird jedes Glyph (Atomsymbol, H, Ladung) einzeln gegen jede
    gerade Bindungslinie des RDKit-SVG; Keile (Polygone) erfasst der Ausdruck nicht.
    """
    payload = _payload(ergebnisse, rt, subs)
    fehler = []
    for nr, step in enumerate(payload.steps, 1):
        linien = [tuple(map(float, m.groups())) for m in _BOND_LINE.finditer(step.svg)]
        for m in _GLYPH.finditer(step.svg):
            werte = [float(v) for v in _ZAHL.findall(m.group(2))]
            xs, ys = werte[0::2], werte[1::2]
            box = (min(xs) - _HALBER_STRICH, min(ys) - _HALBER_STRICH, max(xs) + _HALBER_STRICH,
                   max(ys) + _HALBER_STRICH)
            for ax, ay, bx, by in linien:
                if any(_innen((ax + (bx - ax) * i / 200, ay + (by - ay) * i / 200), box) for i in range(201)):
                    fehler.append(f"{cid} Schritt {nr} ({step.label}): Bindung läuft durch ein Zeichen von atom-{m.group(1)}")
                    break
    assert not fehler, "\n".join(fehler)


SN2_FAELLE = [c for c in CASES if c[1] == "sn2"]


@pytest.mark.parametrize(("cid", "rt", "subs"), SN2_FAELLE, ids=[c[0] for c in SN2_FAELLE])
def test_sn2_uebergangszustand_traegt_delta_minus_statt_voller_ladungen(ergebnisse, cid, rt, subs):
    """Sichtung 05.11.2026 (R2): „N≡C⁻ ··· C ··· Br⁻“ hat die Gesamtladung −2 statt −1. Im
    Übergangszustand ist die Ladung auf Nucleophil und Abgangsgruppe verteilt: beide δ⁻ (Clayden
    Kap. 15), Klammern und ‡ bleiben. Kein „⁻“-Glyph (ein flacher Strich) an NU und X."""
    from chemdraw_tool.mechanism_substrate import NU, X

    payload = _payload(ergebnisse, rt, subs)
    ts = [s for s in payload.steps if s.is_transition_state]
    assert len(ts) == 1, f"{cid}: {len(ts)} Übergangszustände"
    svg = ts[0].svg
    # δ als Zeichenreferenz (das RDKit-SVG ist iso-8859-1 deklariert)
    assert svg.count("&#948;") == 2, f"{cid}: {svg.count('&#948;')}× δ im Übergangszustand"
    glyphen = geometry_of(svg)["glyphs"]
    for m in (NU, X):
        flach = [g for g in glyphen[str(m)] if g[3] - g[1] < 2.0]
        assert not flach, f"{cid}: Atom {m} trägt im Übergangszustand ein volles Ladungszeichen {flach}"


@pytest.mark.parametrize(("cid", "rt", "subs"), CASES, ids=[c[0] for c in CASES])
def test_freies_paar_startet_am_atomsymbol_nicht_am_h(ergebnisse, cid, rt, subs):
    """Sichtung 05.11.2026 (GELB): bei „HO“ (Methanol im SN1-Angriff) saß der Pfeilschwanz am H.
    Das freie Paar gehört dem O: das nächste Glyph der Beschriftung am Pfeilschwanz ist das
    Atomsymbol (das Glyph, dessen Mitte dem Atommittelpunkt am nächsten liegt)."""
    payload = _payload(ergebnisse, rt, subs)
    fehler = []
    for nr, step in enumerate(payload.steps, 1):
        geo = geometry_of(step.svg)
        for a in geo["arrows"]:
            glyphen = geo["glyphs"].get(str(a["src_map"]), [])
            if a["kind"] != "lone_pair" or len(glyphen) < 2:
                continue
            mitte = geo["centres"][str(a["src_map"])]
            symbol = min(glyphen, key=lambda g: math.dist(((g[0] + g[2]) / 2, (g[1] + g[3]) / 2), mitte))
            naechstes = min(glyphen, key=lambda g: _abstand_box(a["src"], g))
            if naechstes is not symbol and _abstand_box(a["src"], naechstes) < _abstand_box(a["src"], symbol):
                fehler.append(f"{cid} Schritt {nr} ({step.label}): Pfeil {a['src_map']}→{a['tgt_map']} startet am H")
    assert not fehler, "\n".join(fehler)
