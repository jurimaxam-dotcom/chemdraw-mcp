#!/usr/bin/env python3
"""Kompatibilitäts-Einstieg — die Logik liegt in chempane.desktop_config.

Sie ist dorthin gewandert, weil das Wheel nur `chempane` enthält: PyPI-
Nutzer hätten sich sonst weder eintragen (`chemdraw-install`) noch diagnostizieren
(`chemdraw-doctor`) können. Dieser Wrapper bleibt, weil install.sh und ältere
Anleitungen den Pfad nennen.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chempane.desktop_config import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
