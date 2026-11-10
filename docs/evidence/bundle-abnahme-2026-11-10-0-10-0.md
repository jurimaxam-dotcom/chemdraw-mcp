# Bundle-Abnahme 0.10.0 in Claude Desktop — 10.11.2026

**Das veröffentlichte `chemdraw-mcp-0.10.0.mcpb` zeichnet Lysozym im Panel, der Cartoon dreht sich. Das Panel erschien erst nach einem Neustart von Claude Desktop.**

Gemessen von Codex (Tisch-Faden `20261110-184651-bundle-abnahme-0-10`), vom Owner geprüft: Hash selbst
nachgerechnet und mit dem Release-Asset verglichen, drei Screenshots und die Prozessliste selbst angesehen.

| Schritt | Befund | Beleg |
|---|---|---|
| Download vom Release v0.10.0 | SHA-256 `7ce1893a…f08b2d56`, gleich dem Digest des Release-Assets | `shasum`, `gh release view` |
| Installation | Upgrade der vorhandenen, deaktivierten Extension 0.8.0 → 0.10.0 (Update → Install); kein leeres Profil | `B-install-dialog.png`, `B-version-after.txt` |
| Erstes Aktivieren | „Unable to connect to extension server“, während die Umgebung von PyPI geladen wurde; nach etwa zwei Minuten startete der Launcher neu und der Server lief | Codex-Bericht, nicht selbst gesehen |
| „Draw lysozyme“ (wörtlich) | ging an den parallel aktiven Repo-Konnektor `chemdraw`: kein Bundle-Nachweis | `B-first-repo-response.png` |
| Gezielter Prompt, vor Neustart | Tool `generate_protein_or_antibody` der Extension antwortet, **kein Panel** | `B-bundle-result-no-panel.png` |
| Gezielter Prompt, nach Neustart 18:59 | Konnektor „ChemDraw MCP (unofficial)“, Panel sichtbar (1LYZ, 129 Reste) | `B-before-drag.png` |
| Mauszug (CGEvent) | Cartoon dreht: Faltblatt wandert von rechts nach links | `B-before-drag.png` → `B-after-drag.png` |
| Herkunft des Servers | `…/chemdraw-mcp-bundle/env-0.10.0/bin/chemdraw-mcp`, Parent `run.sh` im Extension-Ordner | `B-final-runtime.txt` |
| Endzustand | Extension wieder Disabled, 0.10.0 bleibt installiert; Repo-Konnektoren unverändert | `B-restored-disabled.png` |

Gezielter Prompt wörtlich: „Use the ChemDraw MCP (unofficial) desktop extension, not chemdraw or
chemdraw-pharma, to draw lysozyme.“ Modell Opus 5.5 Medium.

## Offen

- **Panel fehlt bis zum Neustart.** Ursache nicht ermittelt; deckt sich mit dem Befund vom 21.10.
  (nach `.mcpb`-Installation fehlt das Panel bis zum Desktop-Neustart). Ob ein Erstinstallierer ohne
  Vorversion dasselbe sieht, ist nicht gemessen.
- **Erster Start läuft in ein Zeitlimit**, solange die Umgebung lädt; der zweite Anlauf kam von selbst.
- Nicht gemessen: Installation in einem leeren Desktop-Profil, wörtliches „Draw lysozyme“ mit dem
  Bundle als einzigem Konnektor.

Screenshots unter `/tmp/chemdraw-desktop-test/bundle-0-10-0/`, außerhalb des Repos (private Chat-Titel).
