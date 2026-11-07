# Panel-Kritik: Panel-UI und 3D (Auftrag D, 07.11.2026)

Anlass: Jay, 07.11.2026 11:02: „3D cleaner und eindrucksvoller; Panel mit allen Tools besser sortiert und cleaner.“
Reiner Lesebericht. Kein Code geändert. Grundlage: Quellcode auf `c56d84c`, Screenshots unter
`docs/evidence/verifizierter-stand-2026-11-07/screenshots/` (01, 02, 04, 07, 09, 10, 12, 17, 18, 20, 21, 23 angesehen).

Legende: **Sicherheit** hoch = im Code und im Screenshot belegt, mittel = im Code belegt, nicht im Bild gesehen,
niedrig = Schluss aus dem Code, nicht gemessen. **Schwere** 1 = Kosmetik, 2 = stört, 3 = kostet Verständnis oder
Vertrauen, 4 = falsches oder verlorenes Ergebnis.

Pfade kurz: `ui/` = `chemdraw_tool/ui/src/`.

---

## 1. Ist-Aufnahme je View

### 1.1 Reihenfolge der Bausteine (wie gerendert)

| View | Kopf | Hauptfläche | Chips/Umschalter | Kennwerte | Aktionen | Dateipfad |
|---|---|---|---|---|---|---|
| MoleculeView 2D (`ui/MoleculeView.jsx:249-303`) | Titel, PubChem-Zeile, Found as (`:251-256`) | StructureCanvas 320 px, Kernwerte rechts (`:265-276`) | unter den Kernwerten: All H, Fischer, Haworth, 3D (`:277-284`); darunter Stereo-Zeile mit Show variants (`:289-290`); darunter Gruppen-Chips und GroupNote (`:292-296`) | Formel, Molmasse, CAS (`:271-275`) | oben rechts: Structure/Data, Export PNG, Add to Anki (`:257-261`) | fehlt, obwohl `files.png/svg` im Payload stehen (`chemdraw_tool/payloads.py:91`) |
| MoleculeView 3D-Modus (`:266-269`, `:287`) | wie 2D | Kuhle als Quadrat, volle Breite (`ui/styles.css:212-214`) | All H, 3D unter den Kernwerten | Kernwerte als Reihe unter der Kuhle, bricht bei 520 px in 2 Zeilen (Screenshot 23) | Export PNG verschwindet (`:259`), Anki rutscht nach links | als Fließtext im Hinweis: „Drag to rotate · explicit hydrogens · SDF: …“ (`:287`) |
| Molecule3DView, Chat-Einstieg `generate_3d` (`ui/Molecule3DView.jsx:11-48`) | SectionHeader, Untertitel „3D conformer … · drag to rotate“ (`:23-26`) | Ball3DCanvas in fester Höhe 500 px (`:15`) | keine | keine | keine (kein Export, kein Anki, kein Weg zu 2D) | „SDF: …“ als eigene Monospace-Zeile 10 px (`:30-45`) |
| DatabaseView (`ui/DatabaseView.jsx:23-86`) | SectionHeader, Untertitel = **Formel** (`:28`) | startet auf Daten: Reiter und Tabelle (`:75-83`) | Structure/Data | in der Tabelle | Structure/Data, Export PNG (`:32-39`); **kein** Add to Anki | fehlt |
| DatabaseView, Strukturseite (`:43-73`) | wie oben | StructureCanvas und Seitenleiste `aside` (`:61-71`) | Stereo-Hinweis und Gruppen in der Seitenleiste, ohne GroupNote | keine | wie oben | fehlt |
| AmbiguousView (`ui/AmbiguousView.jsx:63-97`) | Rückweg-Leiste über dem Titel (`:65`), Titel, Untertitel | Kandidaten-Raster (`:74-90`) | keine | keine | Klick auf Karte | entfällt |
| ReactionView (`ui/ReactionView.jsx:322-342`) | nur Titel, falls `name` (`:324`), keine Kopfzeile mit Linie | skalierte Reaktionszeile auf `--bg-alt` (`:325-338`) | Bilanz-Badges und Apply coefficients (`:339-340`) | Bilanz als Badge | **keine**: kein Export, kein Anki | fehlt, obwohl `files` im Payload (`payloads.py:146`) |
| MechanismView (`ui/MechanismView.jsx:231-323`) | SectionHeader mit `reaction_type` roh als Untertitel („sn2“, Screenshot 17) (`:242-245`) | Karte fester Höhe 540 px mit innerem Scroll (`:234`, `:297-311`) | eigener Segment-Umschalter Overview/Step by step (`:264-295`); im Schrittmodus Back/Next und Punkte (`:146-181`, `:207-211`) | keine | **keine** | fehlt |
| SpectrumView (`ui/SpectrumView.jsx:31-92`) | SectionHeader (`:42-45`) | weiße Grafikplatte, 480 px hoch (`:34`, `:46-61`) | keine | keine | Export PNG klein unten rechts (`:89`) | „PNG: …“ unten links (`:74-88`) |
| TlcView (`ui/TlcView.jsx:34-121`) | SectionHeader | weiße Platte 520 px (`:37`) | keine | Bahnen-Zeile mit Rf (`:69-92`) | Export PNG klein unten rechts (`:118`) | „PNG: …“ unten links |
| PlotView: Titration, Speziesverteilung, Vergleich (`ui/PlotView.jsx:15-87`) | SectionHeader | weiße Platte 480 px (`:18`) | keine | Notizen als Liste (`:44-58`) | Export PNG klein unten rechts (`:84`) | „PNG: …“ unten links |
| ScopeView, nur Profil full (`ui/ScopeView.jsx:28-107`) | SectionHeader | weiße Platte 560 px (`:31`) | keine | Einträge-Zeile (`:58-85`), Fehlliste rot (`:86-92`) | **kein Export-Knopf** | „PNG: …“ ohne Knopf (`:93-105`) |
| AnkiDeckView (`ui/AnkiDeckView.jsx:21-68`) | SectionHeader, Untertitel mit Zählern und Zustellweg (`:23-32`) | Liste der Vorderseiten (`:33-45`) | keine | Kartenzahl im Untertitel | keine (kein „In Anki öffnen“, kein „Im Finder zeigen“) | Pfad in eigener Box mit Rahmen, ohne Präfix (`:51-66`) |
| Batch (`ui/App.jsx:24-33`) | je Molekül eigener vollständiger Kopf | n MoleculeViews untereinander, Abstand 16 px | je Panel eigene Chips | je Panel | je Panel eigene drei Knöpfe | je Panel fehlt; **`failed` wird nicht angezeigt** |

### 1.2 Uneinheitlich, doppelt, fehlend

| # | Befund | Stelle | Sicherheit | Schwere |
|---|---|---|---|---|
| U1 | Aktionen stehen an drei Orten: oben rechts (Molekül, Datenblatt), unten rechts klein (Spektrum, DC, Plot), gar nicht (Reaktion, Mechanismus, Scope, 3D-Einstieg, Anki). | MoleculeView:257, SpectrumView:65-90, ReactionView:322-342 | hoch | 3 |
| U2 | Dateipfad viermal anders: „PNG: …“ Monospace 10 px (Diagramme), „SDF: …“ (3D-Einstieg), im Fließtext eines Hinweises (3D-Modus), Box mit Rahmen ohne Präfix (Anki). Molekül 2D, Reaktion, Mechanismus zeigen keinen Pfad. Langer Pfad bricht mitten im Wort um („…schematisch.pn / g“, Screenshots 09, 10). | SpectrumView:74-88, Molecule3DView:30-45, MoleculeView:287, AnkiDeckView:51-66 | hoch | 2 |
| U3 | Der Untertitel bedeutet in jeder View etwas anderes: PubChem-Datensatz (Molekül), Formel (Datenblatt), Methode (3D), Typ und Herkunft (Spektrum), Bedingungen (DC, Scope), roher Enum-Wert „sn2“ (Mechanismus). | MoleculeView:254, DatabaseView:28, Molecule3DView:25, MechanismView:244 | hoch | 2 |
| U4 | Innenabstand doppelt: `body` hat 16 px (`ui/styles.css:129-131`), Diagramm- und 3D-Views legen 12/16 px drauf, Anki 16 px, Mechanismus 8/12 px, Molekül, Datenblatt und Reaktion 0. Kanten springen zwischen Panels (Screenshot 01 gegen 09). | SpectrumView:39, TlcView:42, PlotView:23, ScopeView:36, Molecule3DView:20, MechanismView:239, AnkiDeckView:22 | hoch | 2 |
| U5 | Feste Höhen 480/500/520/540/560 px statt Inhaltshöhe; bei breitem Panel bleibt die Grafik schmal mit weißen Rändern (Screenshot 20: Titration nutzt etwa 60 % der Breite). | SpectrumView:34, Molecule3DView:15, TlcView:37, MechanismView:234, ScopeView:31, PlotView:18 | hoch | 2 |
| U6 | Zwei Segment-Umschalter: `.seg` (ViewToggle) und ein Nachbau im Mechanismus mit Inline-Stilen, ohne `role="tab"`, ohne `aria-selected`, ohne `type="button"`. | ui/components/ViewToggle.jsx:21-44, MechanismView:264-295 | hoch | 2 |
| U7 | Drei Chip-Stile in einem Panel: `.chip-toggle` (Ansichten, etwa 28 px hoch, ohne `min-height`), `.stereo-note-button` (gestrichelt), `.functional-group` (36 px, Punkt und Zahl). Screenshot 01 zeigt drei Chip-Reihen untereinander. | ui/styles.css:300-305, 237 | hoch | 2 |
| U8 | Knopfhöhen: `.seg` 40, Export/Anki 40 oder 32, CopyButton 36/32, `.candidate-back` 36, Mechanismus Back/Next etwa 24, Schritt-Punkte 6 bis 10 px. | ui/styles.css:204, 289, 300; MechanismView:20-33, 146-180 | hoch | 2 |
| U9 | Radius-Tokens gemischt: `--radius-sm` 4, `--radius-md` 8, `--radius` 10, wörtlich 12 px, Fallback auf Host-Variable `--border-radius-sm`. | ui/styles.css:12, 190, 209; ExportPngButton.jsx:102 | hoch | 1 |
| U10 | Fehlerfarbe hart kodiert und uneinheitlich: `#e74c3c` (Knöpfe), `#c0392b` (Scope), kein Token, keine Dunkelvariante. | ExportPngButton.jsx:79, AddToAnkiButton.jsx:81, ScopeView:89 | hoch | 1 |
| U11 | Leere Zustände je View mit eigenem Inline-Div und eigenem Text, ohne Rahmen oder Kopf. | SpectrumView:23-29, TlcView:26-32, PlotView:7-13, ScopeView:15-21, MechanismView:223-229, Ball3DCanvas.jsx:67-73 | hoch | 1 |
| U12 | Datenblatt hat kein Add to Anki, das Molekülpanel schon; dieselbe Substanz, zwei Knopfsätze. | DatabaseView:32-39 | hoch | 2 |
| U13 | Datenblatt zeigt Gruppen in einer Seitenleiste ohne GroupNote, Molekülpanel unter der Zeichnung mit GroupNote. | DatabaseView:61-71, MoleculeView:292-296 | hoch | 1 |
| D1 | Titel doppelt: Panel-Kopf und matplotlib-Titel in der Grafik („TLC: DC Reaktionskontrolle“, „Titration curve: Essigsäure mit NaOH“). | Screenshots 09, 10, 20; Renderer in `chemdraw_tool/tlc.py`, `ph_plots.py` | hoch | 1 |
| D2 | Dunkles Theme ist doppelt ausgeschrieben (Media-Query und `data-theme`), je 50 Zeilen. | ui/styles.css:18-67 und 69-116 | hoch | 1 |
| D3 | 3D-Bedienhinweis steht doppelt und verschieden: „drag to rotate“ im Untertitel (Einstieg) und „Drag to rotate · explicit hydrogens“ als Fußnote (Knopf). | Molecule3DView:25, MoleculeView:287 | hoch | 1 |
| F1 | **Batch verschweigt Fehlschläge**: `BatchPayload.failed` wird nicht gerendert; fehlt ein Name, sieht die Liste vollständig aus. | ui/App.jsx:24-33, payloads.py:161 | mittel | 4 |
| F2 | **Scope im Dunkelmodus**: die RDKit-Umfärbung gilt für `svg:not(.plot-svg svg)`; `.scope-svg` liegt auf festem Weiß (`ScopeView:44`), Kohlenstoff wird also hell auf Weiß. Commit `40723f9` hat dasselbe für den Vergleich (PlotView) schon gelöst. | ui/styles.css:48-66, 98-116 | mittel (nicht im Bild, Scope nur im Profil full) | 3 |
| F3 | Scope hat keinen Export-Knopf; der Test deckt nur DC und Plot ab. | ScopeView:93-105, `ui/__tests__/panelExport.test.mjs:17-27` | hoch | 2 |
| F4 | Reaktion: kein Export, kein Pfad, kein Rückweg nach „Apply coefficients“ (die ursprüngliche Gleichung ist weg). | ReactionView:287-342 | hoch | 3 |
| F5 | Mechanismus: kein Export, kein Pfad; Überblick-Kacheln sind `div` mit `onClick`, per Tastatur nicht erreichbar; Hover-Farbe `rgba(255,255,255,0.05)` ist im hellen Theme unsichtbar. | MechanismView:81-97 | hoch | 2 |
| F6 | Mechanismus: Fallback-Titel deutsch „Mechanismus“, Nutzertext soll englisch sein (CLAUDE.md, Conventions). | MechanismView:243 | hoch | 1 |
| F7 | Mechanismus Schritt 1: der Back-Knopf ist deaktiviert in `var(--border)`-Farbe und damit fast unsichtbar (Screenshot 18 zeigt nur Next); die Zeile wirkt rechtslastig. | MechanismView:153 | hoch | 1 |
| F8 | Mechanismus: Überblick scrollt innen in einer 540-px-Karte; der dritte Schritt liegt unter der Kante (Screenshot 17), im Chat entsteht Scroll im Scroll. | MechanismView:234, 309 | hoch | 2 |
| F9 | Ladezustand der Ansicht-Chips unsichtbar: `aria-busy` wird gesetzt, `.chip-toggle` hat dafür keinen Stil. 3D (ETKDG) und Show variants dauern spürbar, der Klick sieht tot aus. | MoleculeView:280, 282; StereoNote.jsx:59; ui/styles.css:300-302 | mittel | 3 |
| F10 | 3D-Modus: Export PNG verschwindet, die Knopfzeile springt (Layout-Shift im Kopf). | MoleculeView:259, Screenshot 23 | hoch | 2 |
| F11 | 3D-Modus: der Rückweg (3D-Chip) liegt unter den Kernwerten, bei 520 px rund 250 px unter der Unterkante der Kuhle (Screenshot 23). | MoleculeView:277-284, ui/styles.css:212-214 | hoch | 2 |
| F12 | Anki-Panel: kein Weg, die Datei erneut zu öffnen oder im Finder zu zeigen; bei „AnkiConnect unreachable“ bleibt nur der Pfad. | AnkiDeckView:21-68 | mittel | 2 |
| F13 | Molekül-Payload trägt `lipinski` und `subtitle`, das Panel zeigt beides nicht. Bewusst oder vergessen, offen. | payloads.py:77, 87; MoleculeView | niedrig | 1 |
| F14 | `displayPath` kürzt nur `/Users/<name>/`; Pfade unter `/var/folders/…` (Host-Test, Screenshot 21) laufen voll aus. Betrifft echte Nutzer kaum. | ui/utils/displayPath.js | hoch | 1 |
| F15 | Grafikplatten bleiben im Dunkelmodus weiß (`#ffffff`). Für matplotlib-Bilder richtig (Druckfarben), wirkt aber wie ein Fremdkörper; ein Rand in `--bg-alt` statt harter Kante würde den Übergang weicher machen. | SpectrumView:49, TlcView:54, PlotView:30, ScopeView:44 | hoch | 1 |
| F16 | Gradient-IDs (`bowl`, `contact-shadow`, `atom-C`) sind dokumentweit; im Batch stehen mehrere 3D-Viewer im selben Dokument. Heute gleiche Inhalte, also unsichtbar; sobald die Kuhle themen- oder molekülabhängig wird, greift jedes SVG auf die erste Definition. `useId` als Präfix. | Ball3DCanvas.jsx:144, 150, 158 | niedrig | 1 |

---

## 2. Nielsens zehn Heuristiken je View

Skala: 4 = voll erfüllt, 0 = verletzt. H1 Sichtbarkeit des Systemstatus · H2 Sprache der Nutzer · H3 Kontrolle und
Freiheit · H4 Konsistenz · H5 Fehlervermeidung · H6 Erkennen statt Erinnern · H7 Flexibilität und Effizienz ·
H8 Ästhetik und Minimalismus · H9 Fehler erkennen und beheben · H10 Hilfe.

| View | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 | H9 | H10 | Summe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Molekül 2D | 2 | 4 | 3 | 3 | 3 | 3 | 3 | 2 | 4 | 3 | 30 |
| Molekül 3D-Modus | 2 | 3 | 3 | 2 | 3 | 2 | 2 | 2 | 4 | 3 | 26 |
| 3D-Einstieg (Molecule3DView) | 3 | 3 | 1 | 2 | 3 | 2 | 1 | 3 | 3 | 3 | 24 |
| Datenblatt | 3 | 4 | 4 | 2 | 3 | 3 | 2 | 3 | 3 | 3 | 30 |
| Auswahl (Mehrdeutig, Varianten) | 3 | 4 | 4 | 3 | 4 | 4 | 3 | 4 | 4 | 3 | 36 |
| Reaktion | 3 | 4 | 1 | 2 | 3 | 3 | 1 | 3 | 3 | 3 | 26 |
| Mechanismus | 3 | 2 | 3 | 1 | 3 | 3 | 1 | 2 | 3 | 2 | 23 |
| Spektrum | 3 | 3 | 3 | 3 | 3 | 3 | 2 | 2 | 3 | 3 | 28 |
| DC | 3 | 3 | 3 | 3 | 3 | 4 | 2 | 2 | 3 | 3 | 29 |
| Plot (Titration, Spezies, Vergleich) | 3 | 3 | 3 | 3 | 3 | 3 | 2 | 2 | 3 | 3 | 28 |
| Scope | 3 | 3 | 3 | 2 | 3 | 3 | 1 | 2 | 3 | 3 | 26 |
| Anki | 3 | 3 | 2 | 1 | 3 | 3 | 2 | 3 | 2 | 3 | 25 |
| Batch | 1 | 4 | 3 | 3 | 2 | 3 | 2 | 1 | 1 | 3 | 23 |

Begründung (ein Satz je Heuristik, die von 4 abweicht):

- **Molekül 2D.** H1: Chips laden ohne sichtbaren Zustand (F9). H3: Rückweg zur Skelettformel nur über erneuten Klick auf den gedrückten Chip, es gibt keinen Chip „2D“. H4: drei Chip-Stile (U7). H5: Show variants und 3D ohne Hinweis auf die Dauer. H6: Stereo-Punkt und Elementfarben ohne Legende. H7: keine Tastenkürzel, sonst gut. H8: sechs Blöcke untereinander, drei davon Chip-Reihen (Screenshot 01). H10: Gruppen-Hinweis vorbildlich, Ansichts-Chips erklären sich nur per `title`.
- **Molekül 3D-Modus.** H1: Laden von `generate_3d` unsichtbar (F9). H2: „ETKDG + force field“ nur im Tooltip, „explicit hydrogens“ ohne Bezug. H4: Export verschwindet (F10), Hinweis anders als im Einstieg (D3). H6: keine Elementlegende. H7: keine Tastatur-Drehung, kein Zurücksetzen der Drehlage. H8: drei Formen ineinander (Rahmen, helles Quadrat, Kreis), siehe Abschnitt 3.
- **3D-Einstieg.** H3: Sackgasse ohne Weg zu 2D, Daten oder Anki. H4: andere Höhe, Innenabstand und Pfadzeile als das 3D im Molekülpanel. H6: keine Legende. H7: kein Export, kein Anki.
- **Datenblatt.** H4: Untertitel = Formel statt PubChem-Datensatz, Gruppen in der Seitenleiste (U3, U13). H5 und H9: „No data available“ ohne Grund. H7: kein Anki (U12). H8: ein Copy-Knopf je Zeile ergibt eine Spalte gleicher Icons (Screenshot 04).
- **Auswahl.** H1: „Drawing …“ steht unter dem Raster und kann außerhalb des Sichtbereichs liegen. H4: Rückweg-Leiste über dem Titel, sonst steht der Kopf oben. H7: kein Vergleich der Kandidaten mit Formel. H10: Kandidaten-SMILES nur im `title`.
- **Reaktion.** H3: Apply coefficients ohne Rückweg (F4). H4: kein Kopf mit Trennlinie, keine Aktionen. H7: kein Export, kein Pfad.
- **Mechanismus.** H2: Untertitel „sn2“ roh, Fallback deutsch (F6). H4: eigener Umschalter, eigene Knöpfe (U6, U8). H7: keine Pfeiltasten, Kacheln nicht fokussierbar (F5), kein Export. H8: Scroll im Scroll (F8). H10: Punkte ohne Beschriftung.
- **Spektrum, DC, Plot.** H2: Titel übernimmt die Modellsprache („schematisch“, Screenshot 09), Panel-Text ist englisch. H7: Werte (Peaks, Rf, pKs) nicht kopierbar. H8: Titel doppelt (D1), feste Höhe lässt Breite liegen (U5). H9: leere Zustände ohne Grund (U11).
- **Scope.** H4: einzige Grafik-View ohne Export (F3). H7: kein Export. H8: Dunkelmodus-Risiko (F2).
- **Anki.** H3 und H7: kein erneutes Öffnen (F12). H4: eigener Innenabstand, eigene Pfadbox, keine Aktionen. H9: bei nicht erreichbarem AnkiConnect nur ein Satz im Untertitel.
- **Batch.** H1 und H9: Fehlschläge unsichtbar (F1). H5: kein Zähler „3 of 4 drawn“. H8: n vollständige Panels mit je drei Knöpfen und Gruppen; bei vier Molekülen weit über 2000 px Höhe.

### Kognitive Last (Dinge, die man zugleich im Kopf halten muss)

| View | Gleichzeitige Blöcke | Bewertung |
|---|---|---|
| Molekül 2D | Kopf mit 3 Steuerungen · Zeichnung · 3 Kernwerte · Ansicht-Chips · Stereo-Zeile · Gruppen-Chips · Gruppen-Hinweis = 7 | über der Grenze von etwa 4 |
| Molekül 3D | Kopf · Kuhle · Kernwerte in 2 Zeilen · Chips · Hinweis mit Pfad · Stereo · Gruppen = 7; Gruppen und Stereo wirken auf die 3D-Fläche nicht | über der Grenze, zwei Blöcke funktionslos |
| Datenblatt | Kopf · Reiter · Tabelle = 3 | gut |
| Auswahl | Rückweg · Titel · Raster = 3 | gut |
| Reaktion | Titel · Zeile · Bilanz = 3 | gut |
| Mechanismus | Kopf · Hinweise · Umschalter · Navigation · Schritt · Punkte = 6 | hoch |
| Diagramme | Kopf · Grafik · Kennzeile · Fuß = 4 | an der Grenze, gut |
| Anki | Kopf · Liste · Pfad = 3 | gut |

Folgerung: Last entsteht fast nur im Molekülpanel. Der Hebel ist Gruppieren (eine Ansicht-Achse, ein Info-Block),
nicht Weglassen. Im 3D-Modus können Stereo-Zeile und Gruppen ausgeblendet werden, weil sie dort nichts markieren.

---

## 3. 3D konkret: cleaner und eindrucksvoller

Ist-Zustand (Screenshot 23, dunkles Theme): drei Formen ineinander. Außen der Rahmen von `.structure-canvas`
(`ui/styles.css:209`, 12 px Radius, 6 px Innenabstand `:295`), darin ein hellgraues Quadrat
(`ui/components/Ball3DCanvas.jsx:130`, `#f4f5f8`, unabhängig vom Theme), darin der Kreis der Kuhle (`:144-149`,
`:166-173`). Im dunklen Panel ist das Quadrat die hellste Fläche des ganzen Chats und zieht den Blick von der
Molekülform weg. Die Ecken außerhalb des Kreises sind toter Raum.

| # | Vorschlag | Stelle | Aufwand | Wirkung |
|---|---|---|---|---|
| 3.1 | **Quadrat weg, Hintergrund transparent.** `background` am `svg` streichen, Rahmen und Innenabstand von `.structure-3d` entfernen; die Kuhle ist dann die einzige Form. | Ball3DCanvas.jsx:130-132; ui/styles.css:295-296 | S | hoch: eine Form statt drei |
| 3.2 | **Kuhle je Theme.** Die vier Stopps des Gradienten als CSS-Variablen (`--bowl-0` bis `--bowl-3`) in `:root` und beiden Dunkel-Blöcken; hell wie heute, dunkel etwa von `#2c3430` (Lichtfleck) bis `#151a18` (Rand) mit Randschimmer `rgba(255,255,255,0.06)`. `stopColor` per `style={{ stopColor: "var(--bowl-0)" }}`. Kontaktschatten im Dunkeln dunkler und kleiner. | Ball3DCanvas.jsx:144-154, 171; ui/styles.css:3-16, 18-28, 69-78 | S | hoch: 3D fügt sich ins Panel; braucht 3.3 |
| 3.3 | **Elementfarben je Theme.** Kohlenstoff im Dunkeln heller (etwa `#9aa19d`), Wasserstoff im Hellen etwas dunkler (`#c4c8cc` statt `#d8d8d8`, heute auf hellem Kuhlengrund kaum sichtbar, Screenshot 23). Optional ein 0,75-px-Rand in der Atomfarbe × 0,5 als Kontur. | Ball3DCanvas.jsx:9-20, 155-163 | S | mittel |
| 3.4 | **Bindungen zweifarbig und mit Tiefe.** Jede Bindung als zwei Hälften in der Farbe ihres Atoms (CPK-Konvention) statt einheitlich `#5a5a5a`; Strichbreite und Helligkeit mit derselben Tiefe skalieren wie die Atome (heute schrumpfen nur Atome, `:207-209`, Bindungen bleiben gleich dick). | Ball3DCanvas.jsx:181-195 | S | hoch: Heteroatome lesen sich sofort, Tiefe wird glaubhaft |
| 3.5 | **Doppel- und aromatische Bindungen.** Heute: Ordnung ab 2 nur dicker, 1,5 (aromatisch) wie Einfach (`:183`; Screenshot 07 Koffein). Vorschlag: Doppelbindung als zwei parallele dünne Linien (Versatz senkrecht zur projizierten Bindung, 2,5 px), Dreifach als drei, aromatisch als eine volle und eine gestrichelte Linie. Die Ordnung liefert der Server schon (`chemdraw_tool/structure3d.py:52`). | Ball3DCanvas.jsx:181-195 | M | hoch für Chemiker: Carbonyl, Aromat, Nitril ohne Legende erkennbar |
| 3.6 | **Atomgrößen.** Heute zwei Klassen (H 0,34, sonst 0,58, `:22`). Kovalenzradien je Element (C 0,76, N 0,71, O 0,66, S 1,05, Cl 1,02, Br 1,20, I 1,39) machen Halogene und Schwefel sofort sichtbar. Faktor 0,55 behalten; `atomReach` rechnet schon mit dem Maximum. | Ball3DCanvas.jsx:22-23, 57-60 | S | mittel |
| 3.7 | **Tiefenwirkung.** (a) Leichte Perspektive: `s = d / (d - z)` mit `d` etwa 4 × `maxExtent` auf x, y und Radius. (b) Hinteres Drittel in Richtung Kuhlenfarbe mischen statt `opacity` (Opacity lässt hintere Bindungen durch Atome scheinen). (c) Glanzpunkt der Atome oben links lassen, das passt zum Licht der Kuhle. | Ball3DCanvas.jsx:82-90, 201-210 | S bis M | mittel bis hoch |
| 3.8 | **Kontaktschatten mitführen.** Heute fest bei 74 % Höhe (`:174-180`); bei Ibuprofen liegt das OH unter dem Schatten (Screenshot 23). Schatten unter den tiefsten projizierten Punkt legen, Breite aus der projizierten x-Ausdehnung. | Ball3DCanvas.jsx:174-180 | S | mittel: das Molekül liegt sichtbar in der Kuhle |
| 3.9 | **Einblend-Drehung.** Beim ersten Erscheinen eine sanfte Drehung um y (etwa 40° in 1,2 s, ease-out), dann Stillstand; Abbruch bei `pointerdown`; bei `prefers-reduced-motion: reduce` ganz aus. `requestAnimationFrame` in einem `useEffect`, Ziel ist der heutige Startwinkel `{x: -0.4, y: 0.6}`. Keine Dauerrotation. | Ball3DCanvas.jsx:44-45, 103-118 | S | hoch: zeigt ohne Text, dass es drehbar ist, und trägt im GIF |
| 3.10 | **Drag-Verhalten.** (a) `onPointerCancel` und `onLostPointerCapture` fehlen; bricht der Host das Ziehen ab, bleibt `drag.current` gesetzt und die nächste Mausbewegung dreht ohne gedrückte Taste. (b) `cursor: grabbing` während des Ziehens. (c) Doppelklick setzt die Drehlage zurück. (d) Tastatur: `tabIndex=0`, Pfeiltasten drehen 10°. (e) Optional kurzes Nachgleiten (300 ms), aus bei reduced motion. | Ball3DCanvas.jsx:103-139 | S, Nachgleiten M | mittel; (a) ist ein echter Fehler, Sicherheit niedrig (nicht reproduziert) |
| 3.11 | **Legende der Elemente.** Unter der Kuhle eine Zeile mit Punkten nur für die vorkommenden Elemente („● C ● H ● N ● O“); die Liste `elements` existiert schon (`:62-65`). | Ball3DCanvas.jsx:62-65, MoleculeView:287 | S | mittel: erspart CPK-Wissen (H6) |
| 3.12 | **Atom-Hover.** Tooltip mit Element und Nummer am nächsten projizierten Atom, wie `AtomTooltip` in 2D. | Ball3DCanvas.jsx, components/AtomTooltip.jsx | M | niedrig bis mittel |
| 3.13 | **Rückweg und Pfad ordnen.** Die Ansicht-Chips direkt unter die Kuhle (vor die Kernwerte), Hinweis und SDF-Pfad in die gemeinsame Fußzeile (Abschnitt 4). Stereo-Zeile und Gruppen im 3D-Modus ausblenden. | MoleculeView:271-296 | S | hoch für „cleaner“ |
| 3.14 | **3D als PNG exportieren statt Knopf verstecken.** Das SVG der Kuhle ist in sich geschlossen (Gradienten in `defs`); `ExportPngButton` kann das `outerHTML` des aktuellen SVG bekommen und exportiert die aktuelle Drehlage. Beseitigt F10. | MoleculeView:259, Ball3DCanvas.jsx:120 | S bis M | mittel |
| 3.15 | **Einstieg und Knopf angleichen.** `Molecule3DView` nutzt dieselbe quadratische Fläche wie der 3D-Modus (statt fester 500 px) und dieselbe Fußzeile; dazu ein Knopf „2D structure“, der `generate_molecule` per Bridge lädt. | Molecule3DView.jsx:11-48 | M | mittel: beseitigt die Sackgasse (H3) |
| 3.16 | **Vollbild.** Nur über den Host: ext-apps kennt Anzeigemodi (`requestDisplayMode`); ob Claude Desktop „fullscreen“ für dieses Panel anbietet, ist ungeprüft. Erst `scripts/anthropic_sync.py --check` und `getHostContext()` auslesen; `element.requestFullscreen()` scheitert im iframe ohne `allow="fullscreen"`. Ein Vergrößern im Panel lohnt nicht, die Kuhle hat schon die volle Breite. | Ball3DCanvas.jsx; main.jsx:23 | M, Sicherheit niedrig | mittel, wenn der Host es kann |

**Lieber lassen:**

| Idee | Warum nicht |
|---|---|
| WebGL, 3Dmol.js, three.js | Bewusste Entscheidung (`Ball3DCanvas.jsx:3-5`): Single-File-Bundle, WebGL im sandboxed iframe nicht garantiert. SVG reicht bis etwa 100 Atome. |
| Dauerrotation | Lenkt beim Lesen der Chat-Antwort ab, kostet Akku, kollidiert mit reduced motion; eine Einblend-Drehung reicht. |
| Zoom per Mausrad | Das Rad gehört im iframe dem Chat-Scroll; ein abgefangenes Rad hält den Nutzer im Panel fest. Die Kuhle skaliert schon auf die volle Breite. |
| Echte Schatten, Ambient Occlusion, Reflexe | Im SVG nur mit Filtern, teuer und auf großen Molekülen ruckelig; Mehrwert gering gegenüber 3.4 und 3.7. |
| Kalottenmodell-Umschalter, Abstandsmessung | Weitere Steuerung erhöht die Last im ohnehin vollen Molekülpanel; erst auf Nutzerwunsch. |
| Leuchteffekte (Glow, Neon) auf dunkler Kuhle | Wirkt als Effekt, nicht als Chemie; typisches KI-Slop-Muster. |

---

## 4. Einheitliche Panel-Grammatik

Sechs Zonen, immer in dieser Reihenfolge; leere Zonen entfallen ohne Abstand:

1. **Kopf**: Titel, eine Zeile Herkunft (immer dieselbe Bedeutung: woher die Daten kommen), rechts die Primär-Umschalter.
2. **Hauptfläche**: genau eine Zeichnung oder Liste, Breite 100 %, Höhe aus dem Seitenverhältnis, kein innerer Scroll.
3. **Chips**: alle Ansicht-Umschalter dieser Fläche in **einer** Reihe direkt unter ihr.
4. **Kennwerte**: Zahlen mit Kopier-Knopf (Formel, Masse, CAS, Rf, pKs, Kartenzahl).
5. **Info**: Hinweise und Erklärungen (Stereo, Gruppen, Mechanismus-Notizen, Bilanz).
6. **Fußzeile**: links Dateipfad mit Präfix, rechts Aktionen (Export PNG, Add to Anki, Open). Gleiche Höhe in jeder View.

Primär-Umschalter oben (Structure/Data) wechseln den Inhalt des ganzen Panels; Aktionen unten wirken auf das
Ergebnis. Diese Trennung beantwortet „wo ist der Knopf“ für alle Views gleich.

### Struktur (Molekül 2D und 3D, Datenblatt-Strukturseite, je Batch-Eintrag)

```
+--------------------------------------------------------------+
| Ibuprofen                                [Structure | Data ] |
| PubChem: Ibuprofen, (+-)- (CID 3672)                         |
|--------------------------------------------------------------|
|                                                              |
|               (2D-Zeichnung  oder  3D-Kuhle)                 |
|                                                              |
| [ 2D | All H | Fischer | Haworth | 3D ]        ● C ● H ● O   |
|                                                              |
| Formula C13H18O2 [⧉]   Molar mass 206.28   CAS 15687-27-1 [⧉]|
|                                                              |
| ● 1 unspecified stereocenter   [Show variants]               |
| Functional groups (● Carboxylic acid 1) (● Aromatic ring 1)  |
| Hover a group to see where it sits in the structure.         |
|--------------------------------------------------------------|
| PNG ~/ChemDraw-Output/einzelmolekuele/ibuprofen.png          |
|                                [Export PNG]  [Add to Anki]   |
+--------------------------------------------------------------+
```

Im 3D-Modus: Legende rechts in der Chip-Reihe, Stereo und Gruppen ausgeblendet, Fußzeile „SDF …“ statt „PNG …“,
Export PNG exportiert die aktuelle Drehlage. Kernwerte bei 520 px in einer Reihe (Schrift 17 px wie im
Schmal-Layout, `ui/styles.css:269`).

### Daten (Datenblatt, Datenseite des Molekülpanels)

```
+--------------------------------------------------------------+
| Ibuprofen                                [Structure | Data ] |
| PubChem: Ibuprofen, (+-)- (CID 3672)                         |
|--------------------------------------------------------------|
| [PubChem] [GHS]                                              |
| CID              114864                                 [⧉]  |
| IUPAC name       (2R)-2-[4-(2-methylpropyl)…]           [⧉]  |
| …                                                            |
|--------------------------------------------------------------|
| Source  PubChem CID 114864 ->                                |
|                                [Export PNG]  [Add to Anki]   |
+--------------------------------------------------------------+
```

Copy-Knöpfe erst bei Hover oder Fokus der Zeile voll deckend (ruhigere Spalte, Screenshot 04).

### Reaktion und Mechanismus

```
+--------------------------------------------------------------+
| SN2: 2-bromobutane + cyanide             [Overview | Steps ] |
| Nucleophilic substitution · your substrates                  |
|--------------------------------------------------------------|
|                                                              |
|          (Reaktionszeile  oder  Mechanismus-Schritt)         |
|                                                              |
| [<-]  Step 1 of 3 · Reactants: backside attack  [->]   ● ○ ○ |
|                                                              |
| not balanced: right side lacks H2O   [Apply]  [Undo]         |
| | Note: E2 competes at higher temperature                    |
|--------------------------------------------------------------|
| PNG ~/ChemDraw-Output/reaktionen/sn2.png         [Export PNG]|
+--------------------------------------------------------------+
```

Overview zeigt alle Schritte untereinander in voller Höhe (kein innerer Scroll).

### Diagramm (Spektrum, DC, Titration, Spezies, Vergleich, Scope)

```
+--------------------------------------------------------------+
| Aspirin, IR                                                  |
| Schematic, drawn from the given peak list                    |
|--------------------------------------------------------------|
| +----------------------------------------------------------+ |
| |              (Grafik, ohne zweiten Titel)                | |
| +----------------------------------------------------------+ |
|                                                              |
| Edukt 0.30 · Reaktion 0.60 · Co-Spot 0.30, 0.60              |
| · back-calculated samples …                                  |
|--------------------------------------------------------------|
| PNG ~/ChemDraw-Output/spektren/aspirin-ir.png    [Export PNG]|
+--------------------------------------------------------------+
```

### Anki

```
+--------------------------------------------------------------+
| ChemDraw                                                     |
| 3 cards · 3 images · imported into Anki via AnkiConnect      |
|--------------------------------------------------------------|
| 1. Ibuprofen                                                 |
| 2. …                                                         |
| … and 4 more cards                                           |
|--------------------------------------------------------------|
| APKG ~/ChemDraw-Output/anki/chemdraw.apkg     [Open in Anki] |
+--------------------------------------------------------------+
```

### Auswahl (Mehrdeutig, Stereo-Varianten, Batch-Fehlschläge)

```
+--------------------------------------------------------------+
| [<- Back to the structure]                                   |
| Ibuprofen                                                    |
| 2 stereoisomers. Pick one to draw it with wedges.            |
|--------------------------------------------------------------|
| +-------------+ +-------------+                              |
| |(R)-Ibuprofen| |(S)-Ibuprofen|                              |
| |    Bild     | |    Bild     |                              |
| +-------------+ +-------------+                              |
| Drawing (S)-Ibuprofen …   (Status direkt unter dem Raster)   |
+--------------------------------------------------------------+
```

Batch: oben eine Zeile „3 of 4 drawn · not resolved: xyz“, darunter die Panels kompakt (Kopf, Fläche,
Kernwerte, Fußzeile; Gruppen eingeklappt).

### Abweichungstabelle (heute gegen Grammatik)

| View | Kopf | Hauptfläche | Chips | Kennwerte | Info | Fußzeile Pfad | Fußzeile Aktionen |
|---|---|---|---|---|---|---|---|
| Molekül 2D | ok | ok | unter den Kernwerten statt unter der Fläche | rechts statt darunter (ab 620 px) | ok | fehlt | oben statt unten |
| Molekül 3D | ok | drei Formen | weit unter der Fläche | ok | Stereo und Gruppen funktionslos | im Hinweistext | Export fehlt, oben |
| 3D-Einstieg | Untertitel = Bedienhinweis | feste Höhe | fehlt (kein 2D) | fehlt | fehlt | eigene Zeile | fehlt |
| Datenblatt | Untertitel = Formel | ok | Gruppen in Seitenleiste | in Tabelle ok | ok | Quelle als Link ok | oben, Anki fehlt |
| Auswahl | Rückweg über Titel ok | ok | entfällt | entfällt | Status unter Raster ok | entfällt | entfällt |
| Reaktion | ohne Herkunft, ohne Linie | ok | Apply ohne Undo | Bilanz ok | ok | fehlt | fehlt |
| Mechanismus | Untertitel roh | feste Höhe, innerer Scroll | eigener Umschalter | entfällt | Notizen über dem Umschalter | fehlt | fehlt |
| Spektrum, DC, Plot | ok | feste Höhe, Titel doppelt | entfällt | ok | ok | ok | klein, ok |
| Scope | ok | feste Höhe, Dunkelmodus | entfällt | ok | Fehlliste rot ok | ok | Export fehlt |
| Anki | eigener Innenabstand | ok | entfällt | im Untertitel ok | entfällt | Box ohne Präfix | fehlt |
| Batch | je Panel | je Panel | je Panel | je Panel | Fehlschläge fehlen | fehlt | je Panel dreifach |

Umsetzung als zwei kleine Bausteine: `PanelFooter({ files, actions })` (Pfad mit Präfix links, Knöpfe rechts;
ersetzt die Inline-Kopien in SpectrumView, TlcView, PlotView, ScopeView, Molecule3DView, AnkiDeckView) und eine
gemeinsame Hülle `.panel` ohne zusätzlichen Innenabstand (beseitigt U4). Die Diagramm-Views verlieren ihre feste
Höhe zugunsten von `aspect-ratio` aus der SVG-viewBox (U5); `ui/utils/svgSize.js` liest die Maße schon.

---

## 5. Die fünf Änderungen mit dem größten Effekt pro Aufwand

| Rang | Änderung | Stellen | Was genau | Aufwand | Absichernder Test |
|---|---|---|---|---|---|
| 1 | **3D-Kuhle als eine Form, je Theme** | `ui/components/Ball3DCanvas.jsx:130-132, 144-154, 171-180`; `ui/styles.css:295-296` und die Theme-Blöcke `:3-16, 18-28, 69-78` | Quadrat-Hintergrund und inneren Rahmen streichen, Gradient-Stopps und Kontaktschatten als `--bowl-*`-Variablen je Theme, C- und H-Farbe je Theme (3.1 bis 3.3), Schatten unter den tiefsten Punkt (3.8). | S | `ui/__tests__/ball3dCanvas.test.mjs`: das SVG hat keinen festen `background`, jeder `stop` im Bowl-Gradienten verweist auf `var(--bowl-…)`. `ui/host/host.e2e.mjs` Schritt 3d2: `page.emulateMedia({ colorScheme: "dark" })`, Pixel in der Ecke von `[data-view-3d]` gleich Panel-Hintergrund, Screenshot zum Ansehen. |
| 2 | **Bindungen, die Chemie zeigen** | `Ball3DCanvas.jsx:22, 181-195` | Zweifarbige Bindungshälften mit Tiefenskalierung (3.4), Doppel- und Dreifachbindung als Parallel-Linien, aromatisch voll plus gestrichelt (3.5), Kovalenzradien je Element (3.6). Mit Rang 1 der größte sichtbare Sprung für „eindrucksvoller“. | S plus M | `ball3dCanvas.test.mjs`: Formaldehyd (`C=O`) ergibt für C=O zwei Linien; Benzol ergibt sechs Linien mit `stroke-dasharray`; eine C-O-Bindung trägt zwei Farben. Host-E2E: Koffein-Screenshot `panel-host-wave1-3d.png` ansehen. |
| 3 | **Eine Ansicht-Achse direkt unter der Fläche, mit Ladezustand und Einblend-Drehung** | `ui/MoleculeView.jsx:271-296`; `ui/styles.css:293, 300-302`; `Ball3DCanvas.jsx:44, 103-118` | Chips als ein Segment „2D · All H · Fischer · Haworth · 3D“ direkt unter Zeichnung oder Kuhle, vor den Kernwerten; `.chip-toggle[aria-busy="true"]` bekommt den vorhandenen `.seg-spinner` (F9); Stereo und Gruppen im 3D-Modus aus; Einblend-Drehung mit Abbruch beim Anfassen und ohne bei reduced motion (3.9); `onPointerCancel` ergänzen (3.10a). | S | `ui/__tests__/moleculeView.test.mjs`: nach 3D-Klick mit offenem Deferred trägt der 3D-Chip `aria-busy="true"` und enthält `.seg-spinner`; im 3D-Modus kein `[data-testid="stereo-note"]`. Host-E2E 3d2: Oberkante des 3D-Chips höchstens 24 px unter der Unterkante von `[data-view-3d]`. |
| 4 | **Gemeinsame Fußzeile mit Pfad und Aktionen** | neu `ui/components/PanelFooter.jsx`; ersetzt `SpectrumView.jsx:65-90`, `TlcView.jsx:94-119`, `PlotView.jsx:60-85`, `ScopeView.jsx:93-105`, `Molecule3DView.jsx:30-45`, `AnkiDeckView.jsx:51-66`; neu in `MoleculeView.jsx` (statt `:259`, `:287`) und `ReactionView.jsx:339` | Ein Baustein, ein Ort: Pfad mit Präfix links, Export PNG rechts. Schließt F3 (Scope ohne Export), F4 zur Hälfte (Reaktion ohne Export und Pfad), F10 (3D-Export der Drehlage, 3.14), U1, U2, U4. | M | `ui/__tests__/panelExport.test.mjs`: `CASES` um ScopeView, ReactionView, SpectrumView, Molecule3DView erweitern; neuer Fall „jede View mit `files.png` zeigt `[data-testid="panel-footer"]` mit gekürztem Pfad“. Host-E2E: Export-Knopf im 3D-Modus vorhanden; die heutige Prüfung „Export PNG pausiert im 3D-Modus“ (`host.e2e.mjs:432`) wird bewusst umgedreht. |
| 5 | **Zwei stille Verluste schließen** | `ui/App.jsx:24-33`; `ui/styles.css:48-66, 98-116` | Batch: Kopfzeile „N of M drawn“ und Liste `failed` (F1). Scope: `.scope-svg` aus der Dunkel-Umfärbung ausnehmen wie `.plot-svg` (F2). | S | Neuer `ui/__tests__/batchView.test.mjs`: Payload mit `failed: ["xyz"]` rendert „xyz“ in einem `role="status"`. Für F2 ein Text-Test in `ui/__tests__/uiText.test.mjs`, der jeden `svg:not(...)`-Selektor in `styles.css` auf `.scope-svg` prüft; alternativ Host-E2E mit `CHEMDRAW_PROFILE=full` und dunklem Schema. |

Danach, in dieser Reihenfolge: Mechanismus auf die Grammatik (`.seg`, fokussierbare Kacheln, Pfeiltasten,
lesbarer Untertitel, englischer Fallback, kein innerer Scroll; `MechanismView.jsx:20-33, 81-97, 146-180, 234,
243-244, 264-295`; Test in `ui/__tests__/mechanismView.test.mjs`: `role="tablist"`, Punkte mit
`aria-label="Step n"`, ArrowRight schaltet weiter) · Undo für Apply coefficients (`ReactionView.jsx:290-314`) ·
Elementlegende (3.11) · Anki im Datenblatt (U12) · doppelte Diagrammtitel im Renderer abschalten (D1, Python-Seite;
Golden-Dateien betroffen, also bewusst segnen).
