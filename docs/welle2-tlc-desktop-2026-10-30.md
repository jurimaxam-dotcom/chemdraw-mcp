# Welle 2: DC-Panel und Spektren-Retest, 30.10.2026

## Prüfstand und Grenze

Desktop frisch nach `d6098a9` gebunden; Spektren-Auswahltext/Exportknopf
`6ba60ca`, DC-Freischaltung `90cfd7b`, DC-/Plot-Exportknopf `d6098a9`.
Während der sieben Fälle kein eigener Desktop-Neustart; Opus hat ebenfalls
zugesagt, den Prozess bis zum Bericht unangetastet zu lassen.

Serverlog: Client `tools/list` am `2026-10-30T22:10:14.585Z`, Antwort `.592Z`.
Das belegt eine beantwortete Liste, nicht allein deren Inhalt. Frische Chats,
Opus 5.5 Mittel, unveränderte Prompts. Keine grünen Desktop-Behauptungen aus
Host- oder Python-Tests ableiten.

## Spektren: vier Retests

Alle vier wählen weiterhin `visualize`, kein `generate_spectrum`:

| Prompt | Im AX-Baum sichtbarer Toolname | Chat-ID |
|---|---|---|
| Zeichne das IR-Spektrum von Aspirin | visualize: Aspirin ir spektrum schematisch | f2f86d72-e931-4827-a1fa-2f9a760b7a1e |
| Plot a mass spectrum: molecular ion at m/z 180, base peak at 120, another at 138 | visualize: Mass spectrum mz180 120 138 | 66d2ebe1-480a-48a5-bbcf-0feae7302722 |
| Zeichne ein 1H-NMR von Ethylacetat | visualize: Ethylacetat 1h nmr | deafe94a-e833-4de7-ac3b-69e71069eb09 |
| Aspirin IR-Spektrum schematisch | visualize: Aspirin ir spektrum schematisch | 3588534e-96eb-487a-a48e-d2bb64aaf254 |

Belege: `/tmp/chemdraw-desktop-test/welle2-generate_spectrum-retest-{ir,ms,nmr,schematic}.{png,ax.txt}`.
Der neue Auswahltext hat diese vier beobachteten Modellentscheidungen nicht
geändert. Daraus folgt noch keine gesicherte Ursache (Beschreibung,
Toolsichtbarkeit, Desktop-Host oder Modellpriorität).

## DC-Host und Backend

```text
uv run pytest tests/test_tlc.py tests/test_server_tlc.py -q
43 passed in 1.73s

npm --prefix chemdraw_tool/ui run test:host
Exit 0
```

Host-Log: `/tmp/chemdraw-desktop-test/welle2-tlc-host.log`.
Drei neue echte Server-/AppBridge-Fälle im MVP-Profil:

- Veresterung: drei Bahnen, Fleckenverteilung 1/1/2; Co-Spot bei 0.30/0.65.
- Drei Bahnen bei 0.20/0.45/0.80; Laufmittel `Hexane/ethyl acetate 7:3`
  auch in der SVG, nicht nur im Paneltext.
- Zwei Bahnen bei 2.1/6 = 0.35 und 4.2/6 = 0.70; `Ethyl acetate` in der SVG.
  Der Host bekommt die Quotienten als Zahlen; die Interpretation der
  natürlichsprachlichen Laufstrecken muss der Desktop-Test separat belegen.

Bei allen drei Fällen: echte SVG-Flecken (kubische Ellipsenpfade), beschriftete
Bahnen und Rf-Werte, PNG-Datei unter `dc-platten/`, Klick auf Exportknopf,
genau ein `save_png` über die Bridge und PNG-Magic-Bytes der Exportdatei.
Das Wegwerf-HOME schützt den echten Benutzerordner. Der erste selbst erstellte
Test war wegen einer falschen Annahme über die Zahl dekorativer SVG-Patches
rot; die tatsächlich erzeugten Pfade wurden geprüft und die Zählung auf
Ellipsen korrigiert. Das war kein Produktfehler und ist kein Rotbeleg für
den bereits vorhandenen Exportknopf.

Host-Screenshots, visuell geprüft:
`/tmp/chemdraw-desktop-test/welle2-generate_tlc-host-{3-4,3-3,2-2}.png`.
Das Bild mit drei Bahnen/vier Flecken zeigt den Co-Spot korrekt; Export ist
sichtbar als `Saved`. Der komplette bestehende Hostlauf einschließlich der
Spektrenfälle endete mit Exit 0.

## README-Bild

`assets/tlc-wave2.png` ist direkt durch `render_tlc_png` erzeugt und visuell
geprüft: drei Bahnen Starting material (0.30), Product (0.65), Co-spot (beide),
Laufmittel Hexane/ethyl acetate 7:3, Detection UV 254 nm. Rf-Werte stehen
rechts neben den Flecken, Laufmittel unter der Platte. Es sind vorgegebene
Beispielwerte, keine vorhergesagten oder gemessenen Daten.
README/Bild und Host-Fälle: `2c9a71a`.

## DC-Desktop

Erster Fall, Prompt unverändert:

> DC meiner Veresterung: Edukt bei Rf 0,3, Produkt bei 0,65, der Co-Spot zeigt beide. Mach mir die Skizze fürs Protokoll.

Chat `9d7797a3-6da3-49ed-8d79-607fde685fda` erstellt eine eigene
`dc_veresterung.svg` plus PNG über Befehlsausführung/Dateierstellung. Im
Datei-Viewer stehen Edukt, Co-Spot und Reaktionsmischung; Co-Spot enthält beide
Flecken. Kein `generate_tlc`-Panel. Daher Tool-/Panel-Abnahme rot, unabhängig
von der fachlich passenden eigenen Skizze. Belege:
`/tmp/chemdraw-desktop-test/welle2-generate_tlc-cospot.{png,ax.txt}`.

Zweiter Fall, Prompt unverändert:

> Zeichne eine DC-Platte mit drei Bahnen, Laufmittel Hexan/EE 7:3, Flecken bei 0,2, 0,45 und 0,8

Chat `69122136-0622-4294-9963-89303ad15c6f`: `visualize: Dc platte hexan ee drei bahnen`.
Kein `generate_tlc`-Panel, Tool-/Panel-Abnahme rot. Belege:
`/tmp/chemdraw-desktop-test/welle2-generate_tlc-solvent.{png,ax.txt}`.

Dritter Fall, Prompt unverändert:

> My TLC in ethyl acetate: spot A ran 2.1 cm, front 6.0 cm; spot B 4.2 cm. Draw the plate.

Chat `98933fc5-d3a9-4de9-bc54-d8ffe36365b7`:
`visualize: Tlc plate ethyl acetate`. Rf(A) = 0.35 und Rf(B) = 0.70 werden
korrekt berechnet und in der Visualize-Grafik beschriftet. Kein
`generate_tlc`-Panel: Tool-/Panel-Abnahme rot, obwohl die Quotienten stimmen.
Belege: `/tmp/chemdraw-desktop-test/welle2-generate_tlc-distances.{png,ax.txt}`.

**Export im Desktop:** Bei keinem der drei DC-Prompts entstand das
ChemDraw-Panel. Deshalb ist der ChemDraw-PNG-Knopf dort nicht prüfbar.
Ein Downloadknopf an einer selbst erzeugten SVG-Datei zählt nicht als
Nachweis für den Panel-Export. Der Export ist nur im echten Host grün belegt.

**Toolsichtbarkeit, reine Beobachtung nach allen sieben Fällen:** Im Menü
„Dateien, Konnektoren und mehr hinzufügen → Konnektoren“ steht
`C chemdraw-tool, Value: 1` (eingeschaltet). Es wurde kein Schalter verändert.
AX-Beleg: `/tmp/chemdraw-desktop-test/welle2-chemdraw-connector.ax.txt`.
Das spricht gegen einen vollständig ausgeschalteten Konnektor; es beweist
nicht, welche Beschreibungen der Modellkontext tatsächlich enthielt.

Ergebnis: **0/7 erwartete ChemDraw-Toolaufrufe**, sechs Visualize-Widgets und
eine eigene SVG/PNG-Dateierstellung über Befehle. Screenshots und AX-Texte
sind keine Host-Simulation, sondern vom tatsächlichen Desktop. Weitere
Ursachendiagnose und gezielter Retest nach Fix bleiben offen.

## Doku-Abgleich und Rest

`PYTHONUNBUFFERED=1 uv run python scripts/anthropic_sync.py --check` erneut
versucht; nach fünf Minuten ohne Ausgabe beendet. Log:
`/tmp/chemdraw-desktop-test/welle2-anthropic-sync.log` (leer).
Kein erfolgreich abgeschlossener Abgleich, kein `--update`. Keine
Panelarchitektur geändert; nur Tests, README und Prüfbericht ergänzt.

Keine fremden Python-/Profil-/Routing-Änderungen in eigene Commits aufgenommen.
