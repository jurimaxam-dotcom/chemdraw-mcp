# Welle 2: pH-Kurven — Host, README und Desktop, 30.10.2026

## Prüfstand

Produktivstand `6093b88`, Planstand beim Desktop-Neustart `0aaa048`.
Claude Desktop per CUA Cmd-Q beendet; `pgrep -x Claude` lieferte keinen PID.
Erst danach per CUA neu gestartet. Serverlog:
`tools/list` am `2026-10-30T22:16:29.079Z`, beantwortet `.081Z`.
Während der Fälle kein weiterer eigener Neustart; Opus hat ebenfalls
zugesagt, Desktop bis zum Bericht unangetastet zu lassen.

## Kontrollchat: Modell nennt 7, Desktop verbindet 15

Nach dem ersten bereits abgeschickten pH-Prompt traf der Kontrollauftrag ein.
Der Kontrollchat wurde deshalb vor den übrigen drei pH-Fällen eingeschoben:

> Liste alle Tools von chemdraw-tool mit Namen

Chat `bd13de2a-3124-4cce-a52e-429c528a212a`, Opus 5.5 Mittel, frischer Chat:

1. batch_generate
2. compare_molecules
3. export_anki_deck
4. generate_molecule
5. generate_reaction
6. lookup_molecule_data
7. save_png

Das Modell sagt ausdrücklich „7 Tools“ und nennt das Präfix
`mcp__remote-devices__chemdraw-tool__`. Kein neuer Welle-1-/Welle-2-Name in
seiner Liste. AX/Screenshot:
`/tmp/chemdraw-desktop-test/welle2-ph-tools-control.{png,ax.txt}`.

Unabhängiger lokaler Beleg:

```text
rg -n 'Connected to chemdraw-tool \(15 tools\)' ~/Library/Logs/Claude/main.log
25233:2026-10-30 23:16:28 [info] [LocalMcpServerManager] Connected to chemdraw-tool (15 tools)
```

Das ist ein starker Hinweis auf eine veraltete Auswahl auf dem Weg vom
lokalen Desktop zum Modell. Eine Modell-Selbstauskunft beweist dessen
Toolkontext nicht endgültig; kein sicherer Schluss auf die genaue Cache- oder
Synchronisationsursache. Routingfehlschläge sind hier deshalb keine isolierte
Messung der neuen Beschreibungsqualität.

## Desktop-Fälle, unveränderte Prompts

1. **Phosphorsäure-Titration/Indikator**
   `Welcher Indikator passt für die Titration von Phosphorsäure mit NaOH? Zeig mir die Kurve.`
   Chat `e6b86074-927d-4a67-86d3-cbbb6443426c`: AX zeigt
   `visualize: Titration phosphorsaeure naoh indikatoren`. Kein
   `generate_titration_curve`-Panel; Abnahme rot.
   Belege: `/tmp/chemdraw-desktop-test/welle2-ph-phosphoric-titration.{png,ax.txt}`.

## Backend und Host

```text
uv run pytest tests/test_ph_plots.py tests/test_server_plots.py -q
26 passed in 1.78s

npm --prefix chemdraw_tool/ui run test:host
Exit 0
```

Logs: `/tmp/chemdraw-desktop-test/welle2-ph-{pytest,host}.log`.
Vier neue Fälle gegen echten Server und sandboxed AppBridge:

- Phosphorsäure-Titration: drei EP-Beschriftungen, echte Datenkurve,
  Phenolphthalein-Label und gefülltes Indikatorband.
- Essigsäure, 0.1 M/25 mL gegen 0.1 M NaOH: EP-Markierung liegt bei
  25 mL, Pufferbeschriftung pH = pKa = 4.76, echte Datenkurve.
- Ibuprofen: zwei echte Datenkurven, Labels HA/A−.
- Phosphorsäure-Spezies: vier echte Datenkurven mit vier Labels.

Alle vier: PNG unter `diagramme/`, Exportknopf, genau ein `save_png` über
Bridge, echte PNG-Magic-Bytes. Ein Wegwerf-HOME schützt den Benutzerordner.
Der Gesamt-Hostlauf einschließlich aller alten Fälle endete mit Exit 0.
Screenshots: `/tmp/chemdraw-desktop-test/welle2-ph-host-*.png`.

## Zusätzlicher Rendererbefund: Pufferpunkte bei Phosphorsäure

Visuell liegt der dritte rote Punkt über der schwarzen berechneten Kurve.
Unabhängig numerisch mit derselben reinen Ladungsbilanz nachgerechnet:

```python
from chemdraw_tool.ph_core import exact_ph
for k, pka in enumerate([2.15, 7.2, 12.35]):
    v = 25 * (k + .5)
    total = 25 + v
    print(v, exact_ph([2.15, 7.2, 12.35],
                      c_acid=.1 * 25 / total, c_na=.1 * v / total), pka)
```

| Halbäquivalenz-Volumen mL | Tatsächlicher Kurven-pH | Gezeichneter roter Punkt |
|---|---|---|
| 12.5 | 2.285969 | 2.15 |
| 37.5 | 7.199998 | 7.20 |
| 62.5 | 11.861965 | 12.35 |

Der Renderer setzt die roten y-Koordinaten direkt auf pKa; sie stimmen in
diesem Fall nicht alle mit der exakten Kurve überein. Kein Fix in dieser
Testetappe. Belegbild:
`/tmp/chemdraw-desktop-test/welle2-ph-phosphoric-renderer-marker.png`.
Der grüne Hosttest prüft Existenz von Kurve/Markierungen, nicht diese
wissenschaftliche Übereinstimmung. Auch 26 grüne Backendtests decken diesen
Fall bisher nicht ab.

## README-Bilder

Direkt mit dem vorhandenen Renderer erzeugt, visuell geprüft:

- `assets/wave2-titration-acetic.png`: Essigsäure 0.1 M, 25 mL, NaOH 0.1 M,
  pKa 4.76, EP 25 mL, Phenolphthaleinband 8.2–10.
- `assets/wave2-species-phosphoric.png`: pKa 2.15/7.20/12.35,
  H₃PO₄/H₂PO₄⁻/HPO₄²⁻/PO₄³⁻; vier Kurven und drei Kreuzungen.

Das Titrationsbeispiel im README nennt jetzt Essigsäure; die separate
Speziesverteilung nennt Phosphorsäure. Der neue Phosphorsäure-Titrationsrender
mit den abweichenden Pufferpunkten wurde als Befund unter `/tmp/` gesichert
und nicht als neues README-Bild übernommen. Bestehende Bilder bleiben erhalten.

## Weitere Desktop-Fälle

2. **Essigsäure-Titration**
   `Show me the titration curve of 0.1 M acetic acid with 0.1 M NaOH and mark the equivalence point.`
   Chat `f95440f2-7cd0-4cc6-a9c0-6f77f088e366`: wählt **Mathviz: Plot function**.
   Desktop zeigt eine Berechtigungsanfrage für Mathviz mit symbolischem
   EP `25*ca/cb`, Pufferpunkt `12.5*ca/cb`, pKa-Regler 4.76 und beiden
   Konzentrationen 0.1. Kein `generate_titration_curve`-Panel. Die
   Mathviz-Freigabe wurde nicht erteilt, da der angeforderte ChemDraw-Weg
   bereits verfehlt war. Keine Aussage über eine fertig gerenderte Kurve.
   Belege: `/tmp/chemdraw-desktop-test/welle2-ph-acetic-titration.{png,ax.txt}`.

Eigener Host-/README-Commit: `5eb9c43`.

3. **Ibuprofen-Speziesverteilung**
   `Liegt Ibuprofen (pKs 4,4) im Magen bei pH 1,5 eher geladen oder ungeladen vor? Mit Diagramm bitte.`
   Chat `f7d4336b-1a39-45fe-a3e9-556778e2671b`: wählt **Mathviz: Plot function**.
   Die Berechtigungsanfrage zeigt zwei Henderson-Hasselbalch-Ausdrücke,
   pKs-Regler 4.4, pH-Regler 1.5, Labels geladen/ungeladen und
   `Schnittpunkt: true`. Kein `generate_species_distribution`-Panel.
   Mathviz-Freigabe nicht erteilt; Toolwahl rot, Diagramm im Desktop nicht
   fertig gerendert. Belege:
   `/tmp/chemdraw-desktop-test/welle2-ph-ibuprofen-species.{png,ax.txt}`.

4. **Phosphorsäure-Speziesverteilung**
   `Zeichne die Speziesverteilung von Phosphorsäure über den ganzen pH-Bereich`
   Chat `8a46ed74-082a-442f-8f19-8c991c9f3e44`: wählt **Mathviz: Plot function**.
   Berechtigungsanfrage enthält vier Speziesfunktionen, vier Formel-Labels,
   pKs-Regler 2.15/7.20/12.35 und pH-Bereich 0–14. Kein
   `generate_species_distribution`-Panel. Mathviz nicht freigegeben;
   Toolwahl rot, fertige Grafik im Desktop nicht abgenommen.
   Belege: `/tmp/chemdraw-desktop-test/welle2-ph-phosphoric-species.{png,ax.txt}`.

## Abnahme und Übergabe

**0/4 erwartete ChemDraw-Aufrufe**: ein Visualize-Widget, drei
Mathviz-Berechtigungsanfragen. Kein ChemDraw-Panel im Desktop, daher kein
Desktop-Panel-Export prüfbar. Der Export wurde im echten AppBridge-Host für
alle vier Fälle grün belegt. Keine zusätzliche Mathviz-Berechtigung erteilt;
es wurde keine laufende ChemDraw-Toolausführung verhindert.

Der Kontrollchat nennt sieben alte Tools, während das lokale Desktop-Log 15
verbundene Tools bestätigt. Das schränkt die Aussagekraft der vier
Routingfälle ein: erst die Weitergabe/Entdeckung der neuen Tools klären,
dann die neuen Beschreibungen erneut bewerten. Konkrete Ursache bleibt offen.

Zusätzlich offen: falsche rote Phosphorsäure-Pufferpunkte im Renderer,
oben quantitativ belegt; das ist unabhängig vom Desktop-Routing.

Der obligatorische Doku-Abgleich wurde erneut als
`PYTHONUNBUFFERED=1 uv run python scripts/anthropic_sync.py --check`
gestartet und nach rund viereinhalb Minuten ohne Ausgabe beendet. Log:
`/tmp/chemdraw-desktop-test/welle2-ph-sync.log` (leer). Kein kompletter
Abgleich, kein `--update`. Diese Etappe ändert keine Panelarchitektur.

Alle vier Host-Screenshots sowie beide neuen README-Bilder visuell geprüft.
Kein fremdes WIP übernommen. Desktop darf nach Bericht wieder neu gestartet
werden; drei nicht bestätigte Mathviz-Anfragen bleiben in den Testchats.
