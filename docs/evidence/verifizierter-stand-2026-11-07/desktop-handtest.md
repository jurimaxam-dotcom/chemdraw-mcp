# Desktop-Handtest (Strang B) — 07.11.2026, 08:28–08:50

Ausführender: Claude-Agent (Opus 5.5) per AX-Steuerung (`scripts/ax-claude.sh`), nicht Codex.
Screenshots: `/tmp/chemdraw-desktop-test/2026-11-07/verifiziert/` (Vollbild, Retina 3456×2234).
Jeder Prompt lief in einem **neuen Chat** (Sidebar → „New“), Modell Opus 5.5 Medium, Modus „Manual“.

## Schritt 0 — Neustart + Handshake

`osascript -e 'quit app "Claude"'`, `open -a Claude` (neuer Prozess PID 18854, Start 08:28),
dann `./scripts/handshake.sh` → `00-handshake.txt`:

    Gemeldet vom laufenden Server: 16 Tools, davon 12 mit Panel.
    ✅ Handshake gruen: 16 Tools, 12 mit Panel — der registrierte Befehl spricht MCP.

## Ergebnis je Schritt

| # | Prompt | erwartet | Werkzeug laut Desktop | Ergebnis | Screenshot |
|---|---|---|---|---|---|
| 1a | Zeichne Ibuprofen | Panel mit Struktur | `chemdraw-tool · generate_molecule` | **belegt.** Panel „Ibuprofen“, PubChem CID 3672, C13H18O2, 206.28 g/mol, CAS 15687-27-1 (Racemat), „1 unspecified stereocenter“ + Show variants | `01-ibuprofen.png` |
| 1b | Show variants | 2 Isomere | (Panel-Klick) | **belegt.** „2 stereoisomers“: (R)- und (S)-Ibuprofen | `02-varianten.png` |
| 1c | (R)-Ibuprofen | Keilzeichnung | (Panel-Klick) | **belegt.** (R)-Ibuprofen, CID 114864, Keil (gestrichelt) am Stereozentrum, CAS 51146-57-7 schon in der Strukturansicht | `03-r-ibuprofen.png` |
| 1d | Data | CAS 51146-57-7 | (Panel-Klick → `lookup_molecule_data`) | **belegt.** Datenblatt PubChem/GHS: CID 114864, IUPAC (2R)-…, InChIKey HEFNNWSXXWATRW-SNVBAGLBSA-N, **CAS No. 51146-57-7**. Server-Log `~/ChemDraw-Output/server.log` 08:38:36–38: PubChem-Abfragen synonyms/CAS/GHS für InChIKey HEFNNWSXXWATRW-SNVBAGLBSA-N bzw. CID 114864 | `04-data.png` (nach Scroll), `04a-data-oben.png` |
| 1e | Export PNG | Datei in `~/ChemDraw-Output` | (Panel-Klick → `save_png`) | **belegt.** Datei landet in `~/ChemDraw-Output/png/`, nicht `einzelmolekuele/` (siehe Abweichungen) | `04b-export-png.png`, `04b-export-ls.txt` |
| 1f | Add to Anki | Dialog/Datei | (Panel-Klick → `export_anki_deck`) | **belegt.** `~/ChemDraw-Output/anki/chemdraw.apkg` (77392 B, 08:40); Anki zeigt Import-Dialog „chemdraw.apkg“ | `05-anki.png`, `05-anki-ls.txt` |
| 2 | Zeige den SN2-Mechanismus von 2-Brombutan mit Cyanid Schritt für Schritt | `generate_mechanism`-Panel, Titel „(R)-2-bromobutane + cyanide“, Step 1/3 → 2/3 | Genehmigungsdialog „Claude wants to use **Generate mechanism** from chemdraw-tool“ (Argumente: reaction type sn2, substrates 2-bromobutane / cyanide, current step 0) | **nicht belegt — Rechte.** Routing und Argumente stimmen; Panel nicht erreicht, weil „Allow once“ regelgemäß nicht geklickt wurde. Titel und Step-Klicks offen | `06-sn2-rechte-dialog.png` |
| 3 | Zeig mir Koffein in 3D | `generate_3d` | `chemdraw-tool · generate_3d` | **belegt.** Panel „Koffein“, 3D conformer (ETKDG + force field), drag to rotate, SDF `~/ChemDraw-Output/3d/koffein.sdf`. Es erscheint ein Panel (Erwartung sagte „kein Panel-Knopf“ — gemeint war wohl kein Umschaltknopf) | `07-3d.png` |
| 4 | Welche IR-Banden erwarte ich für Aspirin? | `predict_spectrum`, Tabelle mit C=O ~1750 | **kein Werkzeug.** Nur Denkblock „Entscheidung über ein Werkzeug zur Spektrumdarstellung“ | **Abweichung.** Modell antwortet aus eigenem Wissen (Tabelle: O–H 2500–3300, C=O Ester 1750–1760, C=O Säure 1680–1690, C–O 1180–1220). Inhalt plausibel, aber `predict_spectrum` nicht aufgerufen | `08-ir-vorhersage.png`, `08b-ir-denkblock.png` |
| 5 | Zeichne ein schematisches IR-Spektrum von Aspirin | festhalten: `generate_spectrum` oder `visualize` | `chemdraw-tool · generate_spectrum` | **belegt: `generate_spectrum`**, nicht Desktops `visualize`. Panel „Aspirin IR (schematisch)“, PNG `~/ChemDraw-Output/spektren/aspirin-ir-schematisch.png`, Export-PNG-Knopf | `09-spektrum.png` |
| 6 | DC-Platte: Edukt Rf 0,3, Produkt Rf 0,6, Co-Spot beide | `generate_tlc`-Panel | `chemdraw-tool · generate_tlc` | **belegt.** Panel „DC Reaktionskontrolle“, Bahnen Edukt 0.30 · Reaktion 0.60 · Co-Spot 0.30/0.60 | `10-dc.png` |
| 7 | Titrationskurve 25 mL 0,1 M Essigsäure (pKs 4,76) mit 0,1 M NaOH | `generate_titration_curve`-Panel mit Äquivalenzpunkt | Genehmigungsdialog „Claude wants to use **Generate titration curve** from chemdraw-tool“ (c acid 0.1, c titrant 0.1, pKa 4.76, V acid 25 mL, Indikator Phenolphthalein 8.2–10) | **nicht belegt — Rechte.** Routing und Argumente stimmen; Kurve/Äquivalenzpunkt nicht gesehen, „Allow once“ nicht geklickt | `11-titration-rechte-dialog.png` |
| 8 | Was ist der pH von 0,1 M Essigsäure, pKs 4,76? | `calculate_ph`, pH = 2.88 | **kein Werkzeug.** Denkblock „Weighing whether a tool call is worth it“ | **Abweichung.** Zahl stimmt (pH ≈ 2,88, Näherung ½(pKs − lg c₀)), aber `calculate_ph` nicht aufgerufen | `12-ph.png`, `12b-ph-denkblock.png` |
| 9 | Schlag Ibuprofen nach | `lookup`, PubChem-Tabelle CID 3672 | **kein chemdraw-Werkzeug.** Denkblock „Ibuprofen-Informationen nachschlagen / Prüfe, ob ein passendes Projekt existiert / Wirkstoffprofil … zusammenstellen“ | **Abweichung.** Pharmakologie-Steckbrief aus Modellwissen plus ein Wirkmechanismus-Diagramm (Desktop-eigene Grafik, kein chemdraw-Panel); im sichtbaren Teil keine PubChem-Tabelle, keine CID (Antwort nicht bis zum Ende gescrollt); AX-Dump ohne chemdraw-Eintrag | `13-lookup.png`, `13b-lookup-denkblock.png` |

Zählung: **belegt** 1a–1f, 3, 5, 6 · **nicht belegt wegen Rechte-Dialog** 2, 7 · **falsches/kein Werkzeug** 4, 8, 9.

## Abweichungen

1. **Rechte-Dialoge bei `generate_mechanism` (2) und `generate_titration_curve` (7).** Beide Werkzeuge stehen in Desktop auf „genehmigungspflichtig“. Der Auftrag sagt „Permission-Dialog → Screenshot, nicht umgehen“; „Allow once“, „Always allow“ und „Decline“ wurden **nicht** geklickt, beide Dialoge stehen in ihren Chats („SN2-Mechanismus von 2-Brombutan“, „Titrationskurve Essigsäure mit NaOH“) noch offen. **Entscheidung für Owner/Jay:** Wird „Allow once“ als Handtest-Klick freigegeben, kann ein zweiter Durchlauf über genau diese zwei offenen Dialoge die Panels (Titel, Step 1/3 → 2/3, Äquivalenzpunkt) in etwa 10–15 Minuten belegen.
2. **`predict_spectrum`, `calculate_ph`, `lookup` wurden nicht aufgerufen (4, 8, 9)**, ohne Rechte-Dialog. Das Modell antwortete aus eigenem Wissen. Beleg: der AX-Dump dieser drei Chats enthält keinen `Chemdraw-tool:`-Eintrag, kein „View request/response“ und keine `MCP-UI Proxy`-Webarea (bei 3, 5, 6 schon). Ursache aus der Oberfläche nicht unterscheidbar: (a) Werkzeug in Desktop „blockiert“ und damit für das Modell unsichtbar, oder (b) Routing — das Modell hält den Aufruf für unnötig (Denkblock 8: „Weighing whether a tool call is worth it“). Der Rechtestand vom 30.10. (`docs/welle2-ph-desktop-2026-10-30.md` Z. 186) ist nachweislich überholt: `generate_3d`, `generate_spectrum`, `generate_tlc` standen dort auf „blockiert“ und liefen heute ohne Dialog; `generate_titration_curve` stand auf „blockiert“ und fragt heute nach Erlaubnis. Aktueller Stand für predict_spectrum/calculate_ph/lookup unbekannt — die Rechtetabelle wurde bewusst **nicht** geöffnet (Fehlklick-Risiko vom 30.10.).
3. **Export PNG schreibt nach `~/ChemDraw-Output/png/`**, nicht nach `~/ChemDraw-Output/einzelmolekuele/` (Auftragstext ungenau; `server.py` `save_png`: `Path.home() / "ChemDraw-Output" / "png"`). Zwei Dateien, weil zweimal gedrückt (einmal per AX-Press auf den herausgescrollten Knopf, einmal per Klick):

        -rw-r--r--   1 tom  staff  37174 Nov  7 08:39 R_-Ibuprofen-2.png
        -rw-r--r--   1 tom  staff  37174 Nov  7 08:39 R_-Ibuprofen.png

   Das Panel gibt nach dem Export **keine sichtbare Rückmeldung** (kein Pfad, kein Toast) — nur der Tooltip „Export as PNG“ (`04b-export-png.png`). `generate_molecule` selbst hatte schon `ibuprofen.png/svg` und `r-ibuprofen.png/svg` um 08:37 in `einzelmolekuele/` abgelegt.
4. **Anki:** Anki lief seit 07:25 (früherer Test). Der Import-Dialog für `chemdraw.apkg` steht offen und wurde **nicht** bestätigt (Jays Sammlung) — Jay muss ihn importieren oder schließen.
5. **Spektrum (5):** Peak-Beschriftungen um 1750/1690 cm⁻¹ überlappen im Bild („C=O Ester/Säure“ unleserlich übereinander) — kosmetisch, im Screenshot sichtbar.
6. **Erste Eingabe:** Return in der AX-Eingabe sendete nicht; ab Schritt 1 wurde über den Knopf „Send message“ gesendet. Keine Auswirkung auf Ergebnisse.
7. **Fenster:** Claude Desktop lag zu Beginn auf einem anderen Space (Ghostty im Vollbild, `screencapture -l` scheiterte). Erst nach einer Idle-Pause von Jay (≥ 45 s, 08:35) wurde Claude aktiviert, damit keine Tastenanschläge zwischen Jays Terminal und Desktop vermischt werden. Fensterbreite blieb 600 pt (schmal).
