"""Sekundärstruktur aus dem Rückgrat — DSSP-artig nach Kabsch & Sander (1983).

Gebraucht, wenn eine Datei für die gezeigten Ketten keine HELIX/SHEET-Angaben
trägt (manche NMR- und Kryo-EM-Einträge). Drei Zustände wie im Rest des
Pakets: H (α-Helix), E (Strang in einer Leiter), C (alles andere).

Verfahren (Kabsch & Sander, Biopolymers 22:2577, 1983):
  - Amid-H fehlt in Röntgenstrukturen: H = N + Einheitsvektor(C₋₁ → O₋₁) · 1 Å.
  - Elektrostatische Energie zwischen C=O (Akzeptor i) und N–H (Donor j):
    E = 0,084 · 332 · (1/r(ON) + 1/r(CH) − 1/r(OH) − 1/r(CN)) kcal/mol;
    Wasserstoffbrücke bei E < −0,5.
  - 4-Turn bei i: Brücke i → i+4. Zwei aufeinanderfolgende 4-Turns (i−1, i)
    machen i … i+3 zur Helix (minimale Helix, 4 Reste).
  - Brücke zwischen i und j (|i − j| ≥ 3): parallel bei [Hb(i−1→j) ∧ Hb(j→i+1)]
    oder [Hb(j−1→i) ∧ Hb(i→j+1)], antiparallel bei [Hb(i→j) ∧ Hb(j→i)] oder
    [Hb(i−1→j+1) ∧ Hb(j−1→i+1)]. E = Rest in einer Leiter aus mindestens zwei
    aufeinanderfolgenden Brücken gleicher Art; eine Einzelbrücke (DSSP: B)
    bleibt C.
Vereinfachungen gegenüber DSSP: keine β-Ausbuchtungen (bulges), keine 3₁₀-/
π-Helices (beide zeigt der Cartoon als Schleife), keine Konkurrenz um die
beste Brücke je Rest (DSSP nimmt die zwei energieärmsten; hier zählt jede
unter der Schwelle). Übereinstimmung mit den hinterlegten Angaben:
tests/test_protein_ss.py.
"""

from __future__ import annotations

import numpy as np

HBOND_CUTOFF = -0.5  # kcal/mol
_Q = 0.084 * 332.0
_CA_PAIR = 9.0  # Å; DSSP prüft nur Paare mit Cα-Abstand darunter


def _arr(points) -> np.ndarray:
    return np.array([p if p is not None else (np.nan, np.nan, np.nan) for p in points], dtype=float)


def assign(n: np.ndarray, ca: np.ndarray, c: np.ndarray, o: np.ndarray,
           linked: np.ndarray, proline: np.ndarray) -> str:
    """H/E/C je Rest. `linked[i]`: Rest i hängt kovalent an Rest i−1.

    Fehlende Atome sind NaN; solche Reste nehmen an keiner Brücke teil.
    """
    count = len(ca)
    ss = ["C"] * count
    if count < 3:
        return "".join(ss)
    # Amid-H aus der Peptidebene des Vorgängers
    h = np.full_like(n, np.nan)
    co = c[:-1] - o[:-1]
    norm = np.linalg.norm(co, axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        h[1:] = n[1:] + co / norm
    donor_ok = linked & ~proline & ~np.isnan(h).any(axis=1) & ~np.isnan(n).any(axis=1)
    acceptor_ok = ~np.isnan(c).any(axis=1) & ~np.isnan(o).any(axis=1)

    # Kandidatenpaare über den Cα-Abstand (blockweise, auch für 3000 Reste)
    pairs_a, pairs_d = [], []
    valid_ca = ~np.isnan(ca).any(axis=1)
    idx = np.arange(count)
    for start in range(0, count, 512):
        block = slice(start, min(count, start + 512))
        d = np.linalg.norm(ca[block, None, :] - ca[None, :, :], axis=2)
        a_idx, d_idx = np.nonzero(d < _CA_PAIR)
        a_idx = a_idx + start
        keep = a_idx != d_idx
        pairs_a.append(a_idx[keep])
        pairs_d.append(idx[d_idx[keep]])
    a = np.concatenate(pairs_a)
    d = np.concatenate(pairs_d)
    near = {(i, j) for i, j in zip(a.tolist(), d.tolist()) if j - i >= 3}
    keep = acceptor_ok[a] & donor_ok[d] & valid_ca[a] & valid_ca[d] & (d != a + 1) & (d != a - 1)
    a, d = a[keep], d[keep]
    r_on = np.linalg.norm(o[a] - n[d], axis=1)
    r_ch = np.linalg.norm(c[a] - h[d], axis=1)
    r_oh = np.linalg.norm(o[a] - h[d], axis=1)
    r_cn = np.linalg.norm(c[a] - n[d], axis=1)
    energy = _Q * (1 / r_on + 1 / r_ch - 1 / r_oh - 1 / r_cn)
    hb = set(zip(a[energy < HBOND_CUTOFF].tolist(), d[energy < HBOND_CUTOFF].tolist()))

    # Durchgehende Kette zwischen i und k (kein Bruch dazwischen)
    breaks = np.cumsum(~linked)

    def joined(i: int, k: int) -> bool:
        return 0 <= i < count and 0 <= k < count and breaks[i] == breaks[k]

    # α-Helix: zwei aufeinanderfolgende 4-Turns
    turn4 = np.zeros(count, dtype=bool)
    for i in range(count - 4):
        if joined(i, i + 4) and (i, i + 4) in hb:
            turn4[i] = True
    for i in range(1, count - 4):
        if turn4[i - 1] and turn4[i]:
            for k in range(i, i + 4):
                ss[k] = "H"

    # β-Brücken
    def hbond(i: int, k: int) -> bool:
        return (i, k) in hb

    bridges: dict[tuple[int, int], str] = {}
    for i, j in near:
        if not (joined(i - 1, i + 1) and joined(j - 1, j + 1)):
            continue
        if (hbond(i - 1, j) and hbond(j, i + 1)) or (hbond(j - 1, i) and hbond(i, j + 1)):
            bridges[(i, j)] = "p"
        elif (hbond(i, j) and hbond(j, i)) or (hbond(i - 1, j + 1) and hbond(j - 1, i + 1)):
            bridges[(i, j)] = "a"
    ladder = set()
    for (i, j), kind in bridges.items():
        step = 1 if kind == "p" else -1
        if bridges.get((i + 1, j + step)) == kind or bridges.get((i - 1, j - step)) == kind:
            ladder.update((i, j))
    for i in ladder:
        if ss[i] != "H":
            ss[i] = "E"
    return "".join(ss)


def assign_segments(segments) -> list[str] | None:
    """Zuweisung für Segmente (protein_structure.Segment) über alle Ketten.

    None, wenn das Rückgrat unvollständig ist (CA-only-Einträge) — dann bleibt
    alles Schleife, wie bisher.
    """
    n = _arr([p for s in segments for p in (s.n or [None] * len(s.coords))])
    c = _arr([p for s in segments for p in (s.c or [None] * len(s.coords))])
    o = _arr([p for s in segments for p in (s.o or [None] * len(s.coords))])
    ca = _arr([p for s in segments for p in s.coords])
    complete = ~(np.isnan(n).any(axis=1) | np.isnan(c).any(axis=1) | np.isnan(o).any(axis=1))
    if complete.mean() < 0.8:
        return None
    linked = np.array([k > 0 for s in segments for k in range(len(s.coords))], dtype=bool)
    proline = np.array([ch == "P" for s in segments
                        for ch in (s.seq or "X" * len(s.coords))], dtype=bool)
    flat = assign(n, ca, c, o, linked, proline)
    out, pos = [], 0
    for s in segments:
        out.append(flat[pos:pos + len(s.coords)])
        pos += len(s.coords)
    return out


MIN_FILLED_HELIX = 6  # Reste; kürzere berechnete Helices ergänzen hinterlegte Angaben nicht


def fill_missing_helices(deposited: str, computed: str) -> str:
    """Hinterlegte Zuordnung + berechnete Helices, die dort ganz fehlen.

    Alte Einträge (1LYZ 1975, 2PTN 1981) führen nicht jede Helix als HELIX-
    Datensatz; im Cartoon stand sie dann als graue Spirale. Übernommen wird
    nur ein berechneter H-Lauf ab MIN_FILLED_HELIX Resten, über dessen ganze
    Länge die Angaben C sagen — nichts Hinterlegtes wird überschrieben.
    """
    import re

    out = list(deposited)
    for m in re.finditer(r"H{%d,}" % MIN_FILLED_HELIX, computed):
        if set(deposited[m.start():m.end()]) == {"C"}:
            out[m.start():m.end()] = "H" * (m.end() - m.start())
    return "".join(out)
