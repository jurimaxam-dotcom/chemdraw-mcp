"""Ob eine eingegebene Struktur an Datenbanken gehen darf (E12, Jay 10.11.2026: „Weg 1“).

Standard: nein. Ein SMILES (oder InChI), das der Nutzer eintippt, geht an keine
Quelle; gefragt wird nur mit dem InChIKey, den RDKit lokal rechnet — einem Hash,
aus dem sich die Struktur nicht zurückrechnen lässt. Zielgruppe sind Doktoranden
mit unveröffentlichten Strukturen.

Opt-in: CHEMDRAW_SMILES_LOOKUP=1 (oder true/yes/on). Im .mcpb-Bundle setzt das
Häkchen in den Extension-Einstellungen von Claude Desktop die Variable über
`mcp_config.env`; boolesche `user_config`-Werte kommen dort als Text "true" oder
"false" an (@anthropic-ai/mcpb 2.1.2, dist/shared/config.js). Alles außerhalb der
Liste gilt als aus — auch ein nicht ersetzter Platzhalter "${user_config.…}".

Eigenes Modul ohne RDKit-Import, damit `chemdraw-doctor` es billig laden kann.
Gelesen bei jedem Aufruf, nicht beim Import: Tests und ein Neustart mit anderer
Umgebung sehen sofort den neuen Stand.
"""

from __future__ import annotations

import os

ENV_VAR = "CHEMDRAW_SMILES_LOOKUP"
_ON = frozenset({"1", "true", "yes", "on"})

# Name des Häkchens in mcpb/manifest.json (user_config) — eine Quelle für Doku-Texte.
SETTING_TITLE = "Look up typed structures by SMILES"

HOW_TO_ENABLE = (
    f"turn on '{SETTING_TITLE}' in the extension settings of Claude Desktop, "
    f"or set {ENV_VAR}=1 and restart the server"
)


def smiles_lookup_enabled() -> bool:
    """Darf ein eingegebenes SMILES an PubChem & Co. gehen? Standard: nein."""
    return os.environ.get(ENV_VAR, "").strip().lower() in _ON


def status_line() -> str:
    """Ein Satz für server.log und chemdraw-doctor."""
    if smiles_lookup_enabled():
        return (
            f"SMILES lookup: on ({ENV_VAR}) — a structure you type is sent to PubChem when "
            "PubChem does not know its InChIKey, and the lookup tool sends it to its "
            "databases as typed."
        )
    return (
        "SMILES lookup: off — a structure you type (SMILES, InChI) is not sent to any "
        "database by this server; only its InChIKey is."
    )
