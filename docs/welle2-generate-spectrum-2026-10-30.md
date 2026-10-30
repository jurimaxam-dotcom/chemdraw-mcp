# Welle 2: generate_spectrum — Host und Desktop, 30.10.2026

## Abnahmegrenze

Ausgangsstand `c6c847c`: Der Renderer ist mit 41 Python-Tests grün; die
Desktop-Toolwahl ist bei allen drei unveränderten Prompts rot. Ein gezeichnetes
Visualize-Widget ist kein ChemDraw-Spektrenpanel. Kein grüner Desktop-Abschluss.

## Desktop, ursprüngliche Prompts

Drei frische Chats, Claude Desktop, Opus 5.5 Mittel. Desktop war laut Auftrag
nach `c6c847c` neu gestartet. Zusätzlich im tatsächlichen Serverlog gesehen:
`2026-10-30T21:59:03.042Z` Client `tools/list`, Antwort um `.047Z`.
Das beweist eine abgeschlossene Liste, nicht für sich den Inhalt dieser Liste.

| Prompt, unverändert | Beobachtet im AX-Baum | Ergebnis |
|---|---|---|
| Zeichne das IR-Spektrum von Aspirin | `visualize: Aspirin ir spektrum schematisch` | rot: kein `generate_spectrum`, kein ChemDraw-Panel |
| Plot a mass spectrum: molecular ion at m/z 180, base peak at 120, another at 138 | `visualize: Mass spectrum mz180 aspirin` | rot: kein `generate_spectrum`, kein ChemDraw-Panel |
| Zeichne ein 1H-NMR von Ethylacetat | `visualize: H nmr ethylacetat` | rot: kein `generate_spectrum`, kein ChemDraw-Panel |

Screenshots und vollständige AX-Texte:
`/tmp/chemdraw-desktop-test/welle2-generate_spectrum-{ir,ms,nmr}.{png,ax.txt}`.
Chat-IDs: IR `b5987ca4-541e-40ae-9789-b730e0aac3fe`,
MS `6852c8e8-a6cb-469a-bdbe-a6e265619fb7`,
NMR `e1653106-5793-4333-bcf9-83c8e8031b7e`.

Die NMR-Visualisierung zeigt drei Signalgruppen und eine fallende ppm-Achse;
das erfüllt die Tool- und Panel-Abnahme trotzdem nicht. Die Visualize-Grafik
wurde nicht als Referenzbild oder Nachweis des ChemDraw-Renderers übernommen.

## Exportbefund vor Fix

`SpectrumView.jsx` enthielt bei Beginn nur SVG, Titel und PNG-Pfad, keinen
Exportknopf. Neuer echter Host-Fall einmal rot:

```text
npm --prefix chemdraw_tool/ui run test:host
✔ generate_spectrum liefert eine erfolgreiche echte Serverantwort
✔ ir: echte SVG mit Achseneinheit und allen Peakbeschriftungen
✔ ir: sichtbarer PNG-Pfad verweist auf echte PNG-Datei in spektren/
Error: ROT: ir: PNG-Exportknopf sichtbar
```

Log: `/tmp/chemdraw-desktop-test/welle2-host-red.log`.
Opus hat den fehlenden Knopf und die Toolwahl übernommen (Tisch-Faden
`20261030-225903-welle-2-generate-spectrum`, Nachrichten 4 und 6).

Der tatsächliche Exportvertrag unterscheidet zwei Wege:

- `generate_spectrum` schreibt PNG/SVG nach `~/ChemDraw-Output/spektren/`.
- Der bestehende `ExportPngButton` kopiert primär ein Bild. Bei gesperrter
  Zwischenablage ruft er `save_png` und schreibt nach `~/ChemDraw-Output/png/`.

Der ursprüngliche Wunsch „Exportknopf schreibt nach spektren/“ trifft deshalb
auf den bestehenden allgemeinen Exportknopf nicht zu. Der Host-Test prüft beide
Dateipfade getrennt und echte PNG-Magic-Bytes, den Knopf und den Bridge-Aufruf.

## Renderer und README

```text
uv run pytest tests/test_spectrum.py tests/test_server_spectrum.py -q
41 passed in 2.20s
```

README-Bild: `assets/aspirin-ir.png`, direkt durch `render_spectrum_png`
gerendert, anschließend visuell geprüft. Zwei getrennte C=O-Minima, keine
abgeschnittene 0-%-Strecke; fallende Wellenzahlachse. Schematisches Beispiel,
keine Messdaten. Peakliste:

| Position cm⁻¹ | relative Intensität | Breite, falls vorgegeben | Beschriftung |
|---|---|---|---|
| 1750 | 1 | Standard | C=O (ester + acid) |
| 1690 | 0.95 | Standard | — |
| 3000 | 0.45 | 300 | O–H (broad) |
| 1600 | 0.35 | Standard | Aromatic C=C |
| 1200 | 0.65 | Standard | C–O |

Beide Carbonylbanden haben eine gemeinsame Beschriftung, da die getrennten
langen Labels bei diesem engen Abstand am unteren Rand ineinander laufen.
README und Bild: `862b781`, gepusht.

## Host nach Exportknopf im Arbeitsstand

Der zweite Lauf hat alle drei neuen Spektrenfälle bestanden:
IR- und NMR-Achse fallen von links nach rechts; MS hat drei Balken mit
120 als Basispeak, 138 bei 60 % und 180 bei 20 %. Bei allen drei Typen:
PNG-Exportknopf sichtbar, genau ein `save_png` über die Bridge, echte PNG-Datei
in `png/`; ursprüngliche Tool-Datei zusätzlich in `spektren/` vorhanden.
Der gesamte bestehende Hostlauf endete mit Exit 0. Log:
`/tmp/chemdraw-desktop-test/welle2-host-green.log`.

Screenshots (zusätzlich zum Desktop, kein Ersatz dafür):
`/tmp/chemdraw-desktop-test/welle2-generate_spectrum-host-{ir,ms,nmr_1h}.png`.
Visuell geprüft: zwei getrennte IR-Minima, drei MS-Balken, drei NMR-Signale,
Exportknopf sichtbar. **Restfehler:** die langen Carbonyl-Labels laufen am
unteren Rand ineinander; bei NMR überlappen `Acetyl singlet` und `CH3 triplet`.
Der numerisch grüne Renderer-Test und der Host-Test prüfen keine
Beschriftungskollisionen. Das README-Bild benutzt deshalb eine gemeinsame
C=O-Beschriftung; das löst die allgemeine Kollision im Renderer nicht.

## Noch offen

- Beschreibungs-Fix gegen `visualize`, Desktop-Neustart und erneute Toolwahl.
- Live-Desktop-Export erst nach tatsächlichem ChemDraw-Panel prüfbar.

## Weitere Verifikation und Übergabe

`./scripts/handshake.sh`: Exit 0, registrierter absoluter Startbefehl über
`/opt/homebrew/bin/uv`; gemeldet **13 Tools / 10 Panels**. Zwischenzeitlich ist
`generate_tlc` mit `90cfd7b` dazugekommen; die ursprünglichen 12/9 sind deshalb
kein aktueller Sollwert mehr. Handshake-Log:
`/tmp/chemdraw-desktop-test/welle2-handshake.log`.

`uv run python scripts/anthropic_sync.py --check` gestartet, nach sechs Minuten
ohne Ausgabe beendet. Kein abgeschlossener Dokumentationsabgleich und kein
`--update`; diese Etappe ergänzt vorhandene Tests und ein Rendererbeispiel,
ändert keine Panelarchitektur. Den Sync vor weiterer Architekturarbeit erneut
ausführen.

Eigene Commits: README/Bild `862b781`, Hostfälle/Prüfbericht `600edd3`.
Hostgrün umfasst den noch uncommitteten Exportknopf-Arbeitsstand des anderen
Arbeiters (SpectrumView.jsx plus dist), daher erst mit dessen Fix-Commit als
reproduzierbare Gesamtversion abnehmen. Kein fremdes WIP in eigene Commits
aufgenommen. Die Desktop-Toolwahl nach diesem Fix ist noch ungetestet.

Tisch-Faden `20261030-225903-welle-2-generate-spectrum` ist nach Nachricht 6
am Hop-Limit. Kein neuer Faden zur Umgehung dieses Limits.
