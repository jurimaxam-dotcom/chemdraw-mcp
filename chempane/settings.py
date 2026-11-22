"""Namen nach außen nach der Umbenennung chemdraw-mcp → chempane (22.11.2026).

Regel: neu schreiben, alt weiter lesen, nichts verschieben.

- Umgebungsvariablen: ``CHEMPANE_<NAME>`` gilt, ``CHEMDRAW_<NAME>`` wird weiter gelesen;
  sind beide gesetzt, gewinnt die neue. ``chempane-doctor`` nennt veraltete Namen.
- Ausgabeordner: ``~/chempane-output``. Fehlt er und gibt es ``~/ChemDraw-Output``,
  bleibt der alte in Gebrauch — Nutzerdateien werden nie automatisch verschoben.
- Cache: Verzeichnisname ``chempane``; der alte Cache wird nicht übernommen.

Ohne RDKit-Import, damit ``chempane-doctor`` es billig laden kann. Alles wird bei
jedem Aufruf gelesen, nicht beim Import.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

PACKAGE = "chempane"
PREFIX = "CHEMPANE_"
LEGACY_PREFIX = "CHEMDRAW_"

# Variablen, die das Produkt liest (Entwickler-Schalter wie Lease oder Eval-Ausgabe
# gehören nicht dazu und behalten ihren Namen).
PRODUCT_VARS = ("PROFILE", "SMILES_LOOKUP", "VAULT_PATH", "LOG_LEVEL")

OUTPUT_DIR_NAME = "chempane-output"
LEGACY_OUTPUT_DIR_NAME = "ChemDraw-Output"
CACHE_DIR_NAME = "chempane"
DEFAULT_PROFILE = "mvp"


def env(name: str, default: str = "", environ: Mapping[str, str] | None = None) -> str:
    """``CHEMPANE_<name>``, sonst ``CHEMDRAW_<name>``, sonst ``default``."""
    source = os.environ if environ is None else environ
    for key in (PREFIX + name, LEGACY_PREFIX + name):
        if key in source:
            return source[key]
    return default


def legacy_vars_in_use(environ: Mapping[str, str] | None = None) -> list[str]:
    """Alte Variablennamen, die gesetzt sind und keine neue Schwester haben."""
    source = os.environ if environ is None else environ
    return [
        LEGACY_PREFIX + name
        for name in PRODUCT_VARS
        if LEGACY_PREFIX + name in source and PREFIX + name not in source
    ]


def profile_from_env(entry_env: Mapping[str, str] | None) -> str:
    """Profil aus dem ``env``-Block eines Desktop-Config-Eintrags (beide Namen)."""
    return env("PROFILE", DEFAULT_PROFILE, environ=entry_env or {})


def output_root(home: Path | None = None) -> Path:
    """Wurzel aller Ausgaben; der alte Ordner nur, wenn allein er existiert."""
    base = Path.home() if home is None else Path(home)
    new = base / OUTPUT_DIR_NAME
    old = base / LEGACY_OUTPUT_DIR_NAME
    if not new.exists() and old.is_dir():
        return old
    return new
