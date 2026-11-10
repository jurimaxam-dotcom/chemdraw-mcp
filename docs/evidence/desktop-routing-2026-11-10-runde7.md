# Desktop-Routing Runde 7 — 10.11.2026

## Ergebnis

- generate_protein **7/8**, chemdraw insgesamt **7/8** bei den Protein-/Antikörperprompts.
- Viermal „Draw trastuzumab“: **4/4** generate_protein.
- Gegenproben: **2/2** generate_molecule, jeweils Panel sichtbar.
- Ein Fehlgriff: „Draw an antibody“ → Desktop Visualize. Kein Protein-Panel über generate_molecule.

## Schritt 0 (ungezählt)

Beide Konnektoren listen Generate protein: chemdraw 13 interaktive + 4 sonstige Tools, chemdraw-pharma 17 + 7. CUA-AX zeigte jeweils Always allow=0, Needs approval=1, Blocked=0. Screenshots: `00-chemdraw.png`, `00-pharma.png`; beim Pharma-Screenshot ist nach Scrollen der Konnektorname oberhalb des sichtbaren Ausschnitts, die CUA-AX-Ansicht zeigte URL `claude.ai/new#customize/connectors/yours/id/chemdraw-pharma`.

Positivkontrolle „With chemdraw, draw lysozyme“: chemdraw · generate_protein, Lysozyme C (PDB 1LYZ) als Cartoon sichtbar. `00-control-permission.png`, `00-control-result.png`, AX-Dateien und Prozessliste mit Präfix `00-control`.

## Zehn gezählte Versuche

Zeit = `date` unmittelbar nach Prüfung des Eingabefelds und vor dem Sendeklick, CET am 10.11.2026. Jeder Versuch in einem neuen Chat. Prozesssatz **S** in jeder Zeile identisch; je Versuch vollständiger `ps`-Nachweis in `NN-process.txt`.

**S:** Python-Server PIDs 70555 und 70561, Start jeweils 16:07:44; 70664, Start 16:07:47; 70674, Start 16:07:48. `ps -axo pid,lstart,command` zeigt vier Serverprozesse. Die GUI benennt den verwendeten Konnektor; die Zuordnung eines einzelnen Aufrufs zu genau einer dieser PIDs wurde nicht gemessen.

| Nr. | Uhrzeit CET | Prompt (wörtlich) | Konnektor | Tool | ChemDraw-Panel | Prozesse | Screenshot |
|---|---|---|---|---|---|---|---|
| 1 | 16:11:26 | Draw trastuzumab | chemdraw-pharma | generate_protein | ja | S | `01-result.png` |
| 2 | 16:12:59 | Draw trastuzumab | chemdraw-pharma | generate_protein | ja | S | `02-result.png` |
| 3 | 16:14:20 | Draw trastuzumab | chemdraw | generate_protein | ja | S | `03-result.png` |
| 4 | 16:15:38 | Draw trastuzumab | chemdraw | generate_protein | ja | S | `04-result.png` |
| 5 | 16:16:42 | Draw an antibody | Desktop Visualize | Visualize Widget | nein (Visualize sichtbar) | S | `05-result.png` |
| 6 | 16:18:01 | Show me trastuzumab | chemdraw-pharma | generate_protein | ja | S | `06-result.png` |
| 7 | 16:19:16 | Zeichne Trastuzumab | chemdraw-pharma | generate_protein | ja | S | `07-result.png` |
| 8 | 16:20:27 | Draw lysozyme | chemdraw | generate_protein | ja | S | `08-result.png` |
| 9 | 16:21:13 | Draw caffeine | chemdraw | generate_molecule | ja | S | `09-result.png` |
| 10 | 16:22:26 | Draw aspirin | chemdraw | generate_molecule | ja | S | `10-result.png` |

## Ablauf und Grenzen

- Alle zehn Eingabetexte vor dem Absenden gelesen; `NN-input.ax` enthält den tatsächlichen Feldwert. Kein gezählter Versuch verworfen.
- Vor der Positivkontrolle verdoppelte `scripts/ax-claude.sh type` die Zeichen (`00-control-input.ax`). Nicht abgesendet, durch exaktes Paste ersetzt (`00-control-input-corrected.ax`).
- Der AX-Helfer traf bei `click New` einmal Dispatch; es wurde dort kein Prompt gesendet. CUA öffnete danach nachweislich `claude.ai/new`. `press Allow once` fokussierte teilweise nur den Knopf. Deshalb Fallback auf CUA für verlässliche GUI-Klicks und Paste, AX-Helfer weiter für Dumps; Screenshots per screencapture.
- Bei Genehmigungsdialogen ausschließlich **Allow once** betätigt; keine Konnektor-Einstellung und kein Always allow verändert. Nicht jeder spätere Aufruf zeigte erneut einen Dialog.
- Desktop nicht neu gestartet, Prozesssatz S über alle zehn Messpunkte unverändert. Kein Code geändert, kein Gate gefahren; Arbeitsbaum am Ende sauber.
- Modell in Desktop: Opus 5.5 Medium, Manual. Zwei aktive ChemDraw-Konnektoren. Screenshots der Ergebnisse als Kontaktbogen `results-overview.jpg` selbst angesehen: sieben Protein-Cartoons, ein Visualize-Schema, zwei Molekülpanels.
- Keine Deutung über die beobachteten Zahlen hinaus.
