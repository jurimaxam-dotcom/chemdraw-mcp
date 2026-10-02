"""pH-Mathematik ohne Zeichen-Stack: α-Fraktionen und exakte Ladungsbilanz.

Aus ph_plots herausgelöst (02.10.2026), damit der Rechenkern (ph_calc) ohne
matplotlib importierbar ist — Voraussetzung, um ihn per Pyodide im Browser
laufen zu lassen. ph_plots zeichnet weiter mit genau diesen Funktionen, Bild
und Zahl kommen also aus einer Quelle.
"""

from __future__ import annotations

from collections.abc import Sequence


def alpha_fractions(pka_values: Sequence[float], ph: float) -> list[float]:
    """Anteile der Protonierungsspezies H(n)A … A(n-) bei gegebenem pH.

    Index 0 = vollprotonierte Form. Summe ist 1.
    """
    h = 10.0 ** (-ph)
    kas = [10.0 ** (-pka) for pka in pka_values]
    n = len(kas)
    terms = []
    for k in range(n + 1):
        ka_product = 1.0
        for j in range(k):
            ka_product *= kas[j]
        terms.append(h ** (n - k) * ka_product)
    denominator = sum(terms)
    return [t / denominator for t in terms]


def exact_ph(pka_values: Sequence[float], c_acid: float, c_na: float) -> float:
    """pH aus der Ladungsbilanz [Na+] + [H+] = [OH-] + Σ k·α_k·C_A,
    gelöst per Bisektion (f ist in pH streng monoton).

    `ph_calc` und `ph_plots` nutzen dieselbe Bilanz: Die gezeichnete Kurve
    und die gerechnete Zahl müssen aus einer Quelle kommen, sonst widersprechen
    sich Bild und Text im selben Protokoll.
    """

    def f(ph: float) -> float:
        h = 10.0 ** (-ph)
        oh = 10.0 ** (ph - 14.0)
        alphas = alpha_fractions(pka_values, ph)
        bound = sum(k * a for k, a in enumerate(alphas)) * c_acid
        return c_na + h - oh - bound

    lo, hi = 0.0, 14.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if f(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0
