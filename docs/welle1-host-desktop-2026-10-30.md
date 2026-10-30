# Welle 1: Host- und Desktop-Abnahme, 30.10.2026

Stand nach `044e8d6` (Mechanismus und 3D im Standardprofil). Codex bearbeitete
nur Host-Tests, README und Bilder; Serveränderungen stammen von Opus.
**Desktop-Abnahme offen.** Automatische Gates ersetzen sie nicht.

## Automatische Belege

| Prüfung | Ergebnis | Lokaler Laufbeleg |
|---|---|---|
| `npm --prefix chemdraw_tool/ui run test:host` im Vollprofil | Exit 0 | `/tmp/chemdraw-wave1-host-green.log` |
| derselbe Host-Test im Standardprofil (`CHEMDRAW_PROFILE=mvp`) | Exit 0 | `/tmp/chemdraw-wave1-host-mvp.log` |
| `./test.sh` nach 3D-Freischaltung | Exit 0; 7.373 Python-Tests bestanden, 16 übersprungen; Bundle und Frontend grün | `/tmp/chemdraw-wave1-gate-final.log` |
| `./scripts/handshake.sh` | Exit 0; registrierter Desktop-Befehl meldet 9 Tools / 8 Panels | `/tmp/chemdraw-wave1-handshake.log` |

Rotproben waren kontrollierte Eingriffe **ausschließlich in den neuen Test**,
keine nachgewiesenen Produktionsfehler. Ohne den Next-Klick scheiterte der Test
mit `ROT: sn1: Weiter zeigt eine andere Zeichnung` (Exit 1,
`/tmp/chemdraw-wave1-mechanism-negative.log`). Ohne Mausbewegung beim Ziehen
scheiterte er mit `ROT: 3D: Ziehen ändert die projizierten Atomkoordinaten`
(Exit 1, `/tmp/chemdraw-wave1-3d-negative.log`). Beide Eingriffe sind entfernt.

Der Host prüft alle drei Mechanismus-Templates: sichtbarer ehrlicher Titel,
SVG-Zeichnungen, deaktiviertes Zurück im ersten Schritt und anderer SVG-Inhalt
nach Weiter. Der 3D-Fall prüft 24 Caffein-Atome, Bindungen, Bedienhinweis und
veränderte projizierte Atomkoordinaten nach echtem Pointer-Drag im iframe.

## Herkunft der README-Bilder

Die Bilder sind unveränderte Playwright-Screenshots aus dem Host-Test mit
AppBridge, sandboxed iframe und echten MCP-Serverantworten. Keine Mockdaten.

- `assets/wave1-mechanisms.png`: drei echte `generate_mechanism`-Aufrufe,
  jeweils Schritt 2. SN1: `reaction_type=sn1`, `substrates=["CC(C)Br","O"]`;
  SN2: `sn2`, `["CBr","[OH-]"]`; Fischer: `fischer_ester`, `["CC(=O)O","CO"]`.
- `assets/wave1-3d.png`: `generate_3d` mit
  `name_or_smiles="Cn1c(=O)c2c(ncn2C)n(C)c1=O"`, `label="Caffeine"`.
  Aufnahme vor dem Drag, damit das planare Ringsystem gut erkennbar bleibt.
- Der Server läuft in einem Wegwerf-HOME; Test-SDF/APKG landen dort.
- Erneut aufnehmen: Host-Test ausführen; die Dateien heißen
  `panel-host-wave1-mechanisms.png` und `panel-host-wave1-3d.png` unter Nodes
  `os.tmpdir()`. Vor dem Kopieren in `assets/` ansehen.

## Desktop-Drehbuch und Befunde

| Fall | Ergebnis | Beleg / Grenze |
|---|---|---|
| Neuer Chat: `Show the Fischer esterification mechanism step by step` | **Nicht bestanden**: fertige Antwort war Text/Mermaid, ohne Mechanismus-Panel | `/tmp/chemdraw-desktop-test/01-fischer-no-panel.png` |
| Expliziter Folgeaufruf `chemdraw-tool generate_mechanism`, `fischer_ester`, `["CC(=O)O","CO"]`, `current_step=1` | **Nicht bestanden**: Modell meldete sieben verfügbare Tools und erfolglose Suche nach `generate_mechanism` | `01-fischer-stale-catalog.txt` und `.png` im selben Ordner; Aussage des Modells, kein unabhängiger Katalognachweis |
| Erneuter natürlicher Fischer-Prompt nach Neustart | **Nicht abgenommen**: erneut Texterklärung, später widersprüchliche GUI-Beobachtungen | `01-fischer-restart-no-panel.png`; spätere AX-Zustände und Screenshots passten nicht zusammen |
| Neuer Chat: `Zeig mir den SN2-Mechanismus von 1-Brombutan mit Hydrogensulfid` | **Nicht ausgeführt / offen** | Keine verifizierte Promptübermittlung nach dem GUI-Problem |
| Neuer Chat: `Zeichne die Diels-Alder-Reaktion von Butadien mit Ethen` | **Nicht ausgeführt / offen** | Erwartet: `generate_reaction`, kein Mechanismus-Panel |
| 3D in Desktop, Ziehen | **Nicht ausgeführt / offen** | Host-Fall grün; kein Desktop-Beleg |

GUI-Grenze: Nach dem Neustart zeigte CUA einen neuen Chat im AX-Baum,
aber teils einen alten Fischer-Chat im Screenshot, teils nur ein winziges
dunkles Bild. Der native Helfer `vermarktung/out/.bin/ax-claude preflight`
meldete `screen=1 ax=1`; `window` meldete `kein Claude-Fenster`. Rebinding,
Neustart und Öffnen der App stellten keinen konsistenten Beobachtungszustand
her. Deshalb keine weiteren blinden Eingaben und keine grüne Desktop-Abnahme.
Die Ursache des Katalogunterschieds ist nicht bewiesen.

`uv run python scripts/anthropic_sync.py --check` wurde zu Beginn gestartet,
aber nach etwa zwölf Minuten ohne Ergebnis unterbrochen (Exit 130). Der
Stacktrace stand im HTTPS-Verbindungsaufbau (`urllib.request` →
`socket.connect`). Kein `--update`, kein neuer Doku-Abgleich behauptet.
Hier wurden keine Panel-Architektur und keine Abhängigkeiten geändert.

## Commits

- `187eccd`: neue Host-Fälle und Screenshot-Ausgabe.
- `5a521a2`: Host-Test auf Standardprofil umgestellt.
- `1001027`: README mit ehrlicher Galerie, 3D-Beispiel und echten Bildern;
  zum Commitzeitpunkt 9 Tools.
