# Welle 1: Host- und Desktop-Abnahme, 30.10.2026

Stand nach `044e8d6` (Mechanismus und 3D im Standardprofil). Codex bearbeitete
nur Host-Tests, README und Bilder; Serveränderungen stammen von Opus.
**Desktop-Abnahme nicht bestanden:** In der Nachprüfung ab 22:43 erfüllt nur
Diels–Alder einen von acht Fällen. Details und Screenshots stehen unten.
Automatische Gates ersetzen die Desktop-Prüfung nicht.

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


## Nachprüfung mit deaktivierter Extension (ab 22:43)

Folgeauftrag: `20261030-224243-folge-zu-faden-20261030`.
Die installierte Extension `local.mcpb.jurimaxam-dotcom.chemdraw-mcp` ist laut
Manifest Version 0.5.1. Ihre Detailseite war beim Öffnen bereits auf
**Deaktiviert**; sie wurde nicht deinstalliert und nicht erneut eingeschaltet.
Beleg: `/tmp/chemdraw-desktop-test/extension-disabled.png`.

Die Fensterdifferenz ließ sich in diesem Lauf durch explizites Aktivieren lösen:
`osascript -e 'tell application "Claude" to activate'`. Danach passten Screenshot
und AX-Baum wieder zusammen. Ein AX-Raise allein hatte vorher nicht gereicht.
Ein vollständiger Neustart wurde über Quit, Prüfung auf Prozessende und erneutes
`open -a Claude` durchgeführt. Neuer Prozess: PID 67054, Start 22:43:43;
Desktop-`tools/list` abgeschlossen 21:43:49 UTC. Der unabhängige Handshake
meldete anschließend **10 Tools / 8 Panels**, Exit 0
(`/tmp/chemdraw-wave1-followup-handshake.log`).

Jeder folgende Prompt wurde in einem neuen Chat unverändert übermittelt.

| Fall | Ergebnis | Screenshot und AX-Protokoll unter `/tmp/chemdraw-desktop-test/` |
|---|---|---|
| (a) `Show the Fischer esterification mechanism step by step` | **Nicht bestanden:** fertige Text-/Mermaid-Antwort, kein Mechanismus-Panel; Weiter/Zurück deshalb nicht prüfbar | `a-fischer-final.png`, `a-fischer-final.txt` |
| (b) `Zeig mir den SN2-Mechanismus von 1-Brombutan mit Hydrogensulfid` | **Nicht bestanden:** Tool-Suche, dann `generate_reaction` mit CCCCBr + [SH-] → CCCCS + [Br-]. Modell sagt, das Mechanismus-Werkzeug sei nicht geladen. Kein Lehrbuch-Panel CH3Br + OH- | `b-sn2-final.png`, `b-sn2-final.txt` |
| (c) `Zeichne die Diels-Alder-Reaktion von Butadien mit Ethen` | **Bestanden:** `generate_reaction`, Panel Butadien + Ethen → Cyclohexen, ausgeglichene Bilanz; kein Mechanismus-Panel | `c-diels-alder-final.png`, `c-diels-alder-final.txt` |

Die doppelte Installation ist damit ein plausibler früherer Einfluss, erklärt
aber noch nicht die erneuten Abweichungen nach bestätigter Deaktivierung und
Neustart. Der Modelltext über nicht geladene Werkzeuge bleibt eine Beobachtung;
ein Fehler der Desktop-Indexierung ist damit noch nicht bewiesen.


(d) `Show ibuprofen in 3D`: **Nicht bestanden**. Statt eines
`generate_3d`-Panels lud Claude Tools und führte einen Befehl zur Berechnung
von 3D-Koordinaten aus; außerdem wurde eine 3D-Bibliothek vom CDN geprüft.
Nach zwei Minuten war der Befehl noch aktiv und kein ChemDraw-Panel vorhanden.
Der abweichende Testlauf wurde gestoppt; Ziehen deshalb nicht prüfbar.
Belege: `d-ibuprofen-no-panel.png` und `.txt` im Screenshot-Ordner.
Das ist kein Nachweis, dass die eigene Ersatzdarstellung fertig werden würde.

Vor (e)–(h) wurde Desktop erneut vollständig beendet (`pgrep -x Claude`: Exit 1)
und gestartet. Neuer PID 73654, Start 22:49:01; `tools/list` abgeschlossen
21:49:07 UTC. Der Screenshot `restart-before-e.png` stimmt mit dem neuen
Chat im AX-Baum überein.


(e) `Warum ist Wasser gewinkelt?`: **Nicht bestanden**. Abgeschlossene
VSEPR-Erklärung mit Mermaid und Winkeltabelle, aber ohne Toolaufruf und ohne
3D-Panel. Kein Datenblatt, jedoch das erwartete `generate_3d` fehlt ebenfalls.
Belege: `e-water-final.png` und `.txt` im Screenshot-Ordner.


(f) `Was ist die CAS-Nummer von Paracetamol?`: **Nicht bestanden als Routing-Test**.
Die abgeschlossene Antwort nennt korrekt **103-90-2**, kommt aber ausdrücklich
über vorhandenes Wissen, ohne `lookup` oder anderen Toolaufruf. Der Begleittext
ist deutsch; eine englische `lookup`-Antwort wurde nicht erzeugt und ist daher
hier nicht prüfbar. Belege: `f-cas-final.png` und `.txt`.


(g) `In welchen Stoffwechselwegen kommt Glucose vor?`: **Nicht bestanden**.
Abgeschlossene Text-/Mermaid-Antwort mit Glykolyse, Gluconeogenese,
Glykogenstoffwechsel, Pentosephosphatweg und Nebenwegen, aber ohne `lookup`
und ohne KEGG-ID. Die geforderte Zuordnung C00031 ist daher nicht geprüft;
C00029 wurde ebenfalls nicht genannt. Belege: `g-glucose-final.png` und `.txt`.

(h) `Coffein`: **Nicht bestanden**. Abgeschlossene pharmakologische
Übersicht samt Mermaid und Abbauformel. Weder `generate_molecule` noch
`lookup` wurden verwendet; keine Strukturzeichnung. Das Modell nennt die
pharmakologische Übersicht ausdrücklich seine Annahme.
Belege: `h-coffein-final.png` und `.txt`.

### Ergebnis der Nachprüfung

| Fall | Bestanden | Entscheidender Befund |
|---|---|---|
| a Fischer | nein | Text/Mermaid statt Mechanismus-Panel |
| b SN2 | nein | `generate_reaction` statt ehrlichem Lehrbuch-Mechanismus |
| c Diels–Alder | ja | Reaktionspanel mit richtigem Produkt, kein Mechanismus-Panel |
| d Ibuprofen 3D | nein | Eigene Koordinatenberechnung; nach zwei Minuten gestoppt, kein ChemDraw-3D-Panel |
| e Wasser-Geometrie | nein | Text/Mermaid statt `generate_3d` |
| f Paracetamol-CAS | nein | CAS korrekt, aber ohne `lookup`; keine englische Toolantwort |
| g Glucose pathways | nein | Text statt `lookup pathway`, keine KEGG-ID |
| h Coffein | nein | Pharmakologieübersicht statt `generate_molecule` |

README auf zehn Standard-Tools aktualisiert: `7616b96`.
Erneute Prüfungen: `./test.sh` Exit 0 (**7.393 bestanden, 16 übersprungen**,
Bundle und Frontend grün), `/tmp/chemdraw-wave1-final-ten-gate.log`;
`npm --prefix chemdraw_tool/ui run test:host` Exit 0,
`/tmp/chemdraw-wave1-final-ten-host.log`. Die Läufe starteten bei HEAD
`7616b96`; währenddessen begann fremde Welle-2-Arbeit im Arbeitsbaum.
Sie sind Laufbelege, keine Abnahme dieser uncommitteten Welle-2-Änderungen.

Offen bleibt die Desktop-Auswahl/Entdeckung der Tools. Dieser Lauf änderte
keine Serverlogik, keine Toolbeschreibungen und keine fremde Welle-2-Arbeit.
Die deaktivierte Extension bleibt installiert. Die tatsächlichen
Reaktionsaufrufe wurden im Desktop jeweils einmal erlaubt, ohne eine
Dauerfreigabe zu setzen.
