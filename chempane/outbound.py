"""Drossel für ausgehende Anfragen an fremde Dienste.

PubChem verlangt höchstens 5 Anfragen pro Sekunde je Absender
(https://pubchem.ncbi.nlm.nih.gov/docs/programmatic-access) und sperrt bei
Verstößen vorübergehend. Lokal fragt ein Nutzer von seiner eigenen Adresse; der
gehostete Server (`remote.py`) schickt dagegen die Namen aller Nutzer von einer
einzigen. Die Drossel staffelt deshalb die *Starts* der Anfragen.

Sie gilt je Prozess: eine zweite Maschine oder ein zweiter Worker verdoppelt
die Rate (siehe Hinweis in `fly.toml`).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

# 0,2 s zwischen zwei Starts = höchstens 5 pro Sekunde, 300 pro Minute.
PUBCHEM_MIN_INTERVAL = 0.2
# Länger wartet keine Anfrage auf ihren Platz; danach Absage statt Stau.
PUBCHEM_MAX_WAIT = 2.0


class OutboundBusy(Exception):
    """Kein Platz innerhalb der Wartegrenze: die Quelle lebt, wir sind zu schnell."""


class StartSpacer:
    """Vergibt Startplätze im festen Abstand; Tool-Aufrufe laufen in Threads.

    Der Platz wird unter dem Lock reserviert, gewartet wird außerhalb — so
    blockiert ein Wartender keinen, der später dran ist.
    """

    def __init__(
        self,
        min_interval: float,
        max_wait: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._min_interval = min_interval
        self._max_wait = max_wait
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._next_free = float("-inf")

    def acquire(self) -> None:
        with self._lock:
            now = self._clock()
            slot = max(now, self._next_free)
            wait = slot - now
            # Kleine Toleranz: 3 × 0,2 soll nicht an Gleitkomma-Resten scheitern.
            if wait > self._max_wait + 1e-9:
                raise OutboundBusy(
                    f"next free slot in {wait:.1f} s, limit {self._max_wait:.1f} s"
                )
            self._next_free = slot + self._min_interval
        if wait > 0:
            self._sleep(wait)


PUBCHEM = StartSpacer(PUBCHEM_MIN_INTERVAL, PUBCHEM_MAX_WAIT)


def pubchem_slot() -> None:
    """Vor jeder Anfrage an pubchem.ncbi.nlm.nih.gov aufrufen.

    Liest `PUBCHEM` bei jedem Aufruf, damit Tests den Taktgeber ersetzen können.
    """
    PUBCHEM.acquire()
