# Panel-Überarbeitung: verbindliche Spezifikation (17.11.2026)

Anlass: Jay, 16.11.2026: „UI bitte überarbeiten, einmal komplett nach deinem Ermessen, überlege wie es am cleansten
ist für den User.“ und „3D ist zu klein, das muss wieder größer werden.“ Grundlage: Code auf `f578934`, Bilder des
Referenz-Hosts (`scripts/desktop-probe/out/etappe1…5/nachher/`, lokal, nicht versioniert, @1x) und des echten Desktop-Chats
(`/tmp/chemdraw-desktop-test/release-2026-11-16/`, lokal, @2x: 1856 px Bild = 928 CSS-px). Pfade kurz: `ui/` =
`chemdraw_tool/ui/src/`. Alle Maße in CSS-px. Diese Datei entscheidet; wer abweicht, ändert erst sie.

**Korrektur des Owners (16.11.2026, 23:30):** Die erste Fassung deckelte 3D auf 600×600 – kleiner als der Stand nach Jays „3D ist zu klein“ (`60ee87b`: 968×720 im Molekül-Panel, 936×640 bei `generate_3d`). 3D nimmt die volle Inhaltsbreite und bis zu 720 px Höhe. Außerdem: Die Dateiliste hinter „Files“ steht immer im DOM (`hidden`, solange zugeklappt), damit `.panel-footer-path` mit `title` für `test:host` erreichbar bleibt.

---

## §1 Befund: die zwölf stärksten Unruhe-Quellen

| # | Befund | Beleg |
|---|---|---|
| B1 | **3D zu klein.** Die Kuhle teilt die Zeile mit der Kernwert-Spalte: ~300 px Durchmesser in einem 1000-px-Panel. Im 3D-Einstieg bei 320 px Breite liegt unter der Kuhle ein leerer Streifen (~150 px). | `etappe5/…/e5-molekuel-3d-chat1000-light.png`, Desktop `02-molecule3d-after.png`, `e5-3d-320x700-light.png` |
| B2 | **Dateipfade dominieren den Fuß:** 2–4 Mono-Zeilen, bis 90 Zeichen, im Referenz-Host volle `/var/folders/…`-Pfade. Beim Protein vier Zeilen (`SCHEME PNG`, `SCHEME SVG`). | `06-reaction.png`, `03-protein-after.png`, `e5-protein-schema-chat1000-light.png` |
| B3 | **Alles hat einen Rahmen:** Reiter, Achse, jeder Knopf, jeder Chip, die Bühne, der Expand-Knopf. Im Molekül-Panel 16 umrandete Formen. | `04-molecule-structure.png` |
| B4 | **Vier Bühnen-Arten:** umrandet (Molekül 2D), gefüllt `--bg-alt` (Reaktion, Mechanismus), umrandeter Plotrahmen (Titration, DC), nackt (3D, Protein). | `04-molecule-structure.png`, `06-reaction.png`, `08-titration.png`, `03-protein-after.png` |
| B5 | **Continue-Zeile zu laut:** vier umrandete Knöpfe mit Pfeil, bei 928 px zwei Zeilen, so hoch wie die Hauptreiter. | `04-molecule-structure.png`, `07-data-pubchem.png` |
| B6 | **Expand doppelt:** Desktop zeigt über jedem Panel ein eigenes Vergrößern-Symbol, wir daneben einen umrandeten Text-Knopf. | `05-batch.png`, `08-tlc.png` |
| B7 | **Protein: Bedienung vor Bild.** Vier Segmentgruppen plus „Reset“ als Segment; bei 320 px drei Zeilen Steuerung vor dem Bild, dazu Hinweis, Legende, zwei Fußnoten, vier Pfadzeilen. | `03-protein-after.png`, `e5-protein-320x700-dark.png` |
| B8 | **Titel doppelt in Grafiken:** matplotlib-Titel wiederholt den Panel-Titel („TLC: DC-Platte“, „Titration curve: …“); die DC-Platte steht schmal in einem breiten leeren Rahmen. | `08-tlc.png`, `08-titration.png` |
| B9 | **Study im Vollbild kaputt:** die Bühne fällt auf einen 8-px-Streifen zusammen, die Kernwerte schweben mittig. | `12-expand-molecule.png`, `12-expand-study-repeat.png` |
| B10 | **Untertitel ohne feste Bedeutung:** „3 steps“, „PDB 1N8Z, chains A/B · cartoon · 434 residues · from the complex …“, „Titration curve — …“, Formel. | `06-mechanism-overview.png`, `03-protein-after.png`, `08-titration.png` |
| B11 | **Scope im Dunkeln:** reinweiße Fläche über volle Breite, die hellste Stelle im ganzen Chat. | `etappe3/…/e3-scope-chat1000-dark.png` |
| B12 | **Schrift ohne Leiter:** 10/11/12/13/15/17/19 px plus Mono 11 px; Rf-Werte in Mono, Etiketten in drei Grautönen. Mechanismus: Back/Next 24 px hoch in einer gefüllten Karte, Export allein im Fuß. | `08-tlc.png`, `06-mechanism-step.png` |

---

## §2 Grundsätze und Rahmen

1. **Die Zeichnung ist der Held:** volle Inhaltsbreite und kein Rahmen um die Bühne. Nichts steht neben ihr, Kernwerte stehen darunter.
2. **Eine Linie trennt genau eine Sache:** die Haarlinie über dem Fuß. Keine Linie unter dem Kopf; der Abstand von 16 px trennt genug.
3. **Rahmen nur an Dingen, die man anklickt und die nicht in einer Gruppe stehen:** Batch-Karten, Kandidaten, Chips. Knöpfe sind ruhig (keine Kante, Fläche erst bei Hover), Segmente haben eine Spur statt einer Kante.
4. **Ein Akzent** (das vorhandene Teal) nur für Fokus, Links, den einen Primärknopf und Ausnahmen wie den Übergangszustand. Unter 3 % der Fläche.
5. **Sekundäres ist erreichbar, nicht sichtbar:** Pfade hinter „Files“, Erklärungen im `title`, Fußnoten einzeilig.
6. **Systemschrift des Hosts** (`--font-sans` aus Desktop). Begründung: Das Panel soll wie ein Teil des Chats lesen; Webfonts verbietet die CSP ohnehin.

### Drei Layout-Lagen (entschieden nach Mechanik, nicht nach Namen)

| Lage | Erkennung | Breite | Höhe |
|---|---|---|---|
| **Chat** | kein `[data-host-height]` | 860–1000 px | inhaltsgroß; Ziel ≤ 700 px, 3D und Protein-Struktur ausgenommen |
| **Fill schmal** | `[data-host-height]` und `max-width: 619px` | 320–619 px (Seitenpanel) | `--host-height`: die Bühne nimmt den Rest, nie unter 240 px |
| **Fill breit** | `[data-host-height]` und ≥ 620 px | bis 1600 px | wie schmal, Bühne nie unter 320 px |

Eine breitenbegrenzte Bühne (Kuhle, DC-Platte) steht in Fill mittig. Der Rest fällt **unter** den Fuß, nie zwischen Bühne und Kernwerte: Der Rahmen ist eine Spalte, der Fuß rutscht nicht nach unten.

```
CHAT 1000                                         FILL SCHMAL 320           FILL BREIT (Expand)
┌───────────────────────────────────────────────┐ ┌──────────────────────┐ ┌──────────────────────────────┐
│ Title 19/26                 [Tab|Tab|Tab] [⤢] │ │ Title 17/24      [⤢] │ │ Title         [Tab|Tab|Tab] │
│ subtitle 12, one line                         │ │ subtitle (2 lines)   │ │ subtitle                    │
│                                               │ │ [Tab|Tab|Tab]        │ │                             │
│ [2D|All H|3D]                 hint · [Reset]  │ │ [2D|All H|3D] [Reset]│ │ stage-bar                   │
│                                               │ │                      │ │                             │
│                STAGE (full width)             │ │   STAGE (fills)      │ │   STAGE (fills)             │
│                                               │ │                      │ │                             │
│ Formula C8H10N4O2   Molar mass 194.19   CAS … │ │ Formula   Molar mass │ │ facts                       │
│ (●Amide 3) (●Aromatic ring 2)  note           │ │ CAS                  │ │ groups / legend             │
│ Continue in chat  Explain…  Predict…  Quiz…   │ │ chips, wrap          │ │ continue                    │
│───────────────────────────────────────────────│ │ Continue in chat     │ │─────────────────────────────│
│ Files (2) ▾                [Export PNG] [Anki]│ │ Explain… Quiz…       │ │ Files ▾   [Export] [Anki]   │
└───────────────────────────────────────────────┘ │──────────────────────│ └──────────────────────────────┘
                                                  │ Files ▾  [PNG][Anki] │
                                                  └──────────────────────┘
```

Reihenfolge der Zonen, fest: `panel-head` → `stage-bar` (optional) → `stage` → `panel-facts` → `panel-extras`
(Gruppen, Legende, Bilanz, Hinweis) → `continue-row` → `panel-foot`. Eine leere Zone entfällt mitsamt ihrem Abstand.

---

## §3 Tokens

Neu in `ui/styles/tokens.css`. **Nur diese Datei enthält Farbwerte für die Oberfläche.** B- und C-CSS verwenden nur
Tokens. Ausgenommen sind die SVG-Umfärberegeln (Atom-, matplotlib- und RDKit-Farben), weil sie Daten färben.
Flächen und Linien leiten sich aus den Host-Variablen ab (`--bg`, `--fg`, `--border` holen Desktops `--color-*`).
Die Hex-Werte sind nur Rückfall für den Referenz-Host. Dunkel steht in beiden Selektoren
(`@media (prefers-color-scheme: dark) :root:not([data-theme="light"])` und `:root[data-theme="dark"]`).

```css
:root {
  /* Abstand: 4er-Raster */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-6: 24px; --space-8: 32px;
  /* Radien: drei Stufen, ineinander (innen = außen − Polster) */
  --radius-s: 4px;   /* Kopier-Knopf, Formel-Marke, Segment-Knopf in der Spur */
  --radius-m: 8px;   /* Knopf, Segment-Spur, Karte, Papierbühne */
  --radius-pill: 999px; /* nur Gruppen-Chip (Filter-Bedeutung) */
  /* Schriftleiter: 1,25er-Schritte */
  --text-meta: 12px;  --lh-meta: 16px;   /* Etiketten, Untertitel, Hinweis, Fuß */
  --text-body: 13px;  --lh-body: 20px;   /* Fließtext, Knöpfe, Tabellen */
  --text-value: 15px; --lh-value: 20px;  /* Kernwerte */
  --text-title: 19px; --lh-title: 26px;  /* Panel-Titel; schmal 17/24 */
  --weight-regular: 400; --weight-strong: 600;
  /* Linien */
  --line-w: 1px;
  --line: var(--border);
  --line-strong: color-mix(in srgb, var(--fg) 32%, var(--bg));
  /* Flächen */
  --surface-0: var(--bg);
  --surface-1: color-mix(in srgb, var(--fg) 5%, var(--bg));   /* Segment-Spur, Hover */
  --surface-2: color-mix(in srgb, var(--fg) 9%, var(--bg));   /* gedrückt */
  --text: var(--fg);
  --text-2: var(--fg-muted);
  --accent: #23796d;
  --on-accent: var(--bg);
  --danger: #b42318;
  --success: var(--copy-success);
  --paper: #fbfbf9;            /* Papierbühne, Anki-Kartengrund; in beiden Themen hell */
  --focus: var(--accent);
  /* Bühnen */
  --stage-h: 320px;            /* 2D-Zeichnung im Chat */
  --stage-3d-max: 720px;       /* größte Höhe der 3D-Bühne im Chat; die Breite ist immer die volle Inhaltsbreite */
  --plot-max-h: 400px;
}
/* dunkel, beide Selektoren: */
  --accent: #82c6b7; --danger: #f97066; --line-strong: color-mix(in srgb, var(--fg) 36%, var(--bg));
```

Die übrigen dunklen Werte ergeben sich aus `--bg`/`--fg`. **Kontrastziele**, geprüft gegen die Rückfallpaletten
und gegen Desktops dunkle Fläche (#2f2f2d laut Bild): `--text-2` auf `--surface-0` ≥ 4,5:1; `--accent` als Linktext
≥ 4,5:1; `--line-strong` (Fokus- und Chip-Kanten) ≥ 3:1. Heute erfüllt mit #596961/#fafbf9 ≈ 5,6:1 und #aab9af/#202724 ≈ 7:1.

**Bleiben** (Namen unverändert, andere Dateien hängen daran): `--bg --bg-alt --fg --fg-muted --border --font
--font-mono --copy-success --copy-success-bg --bowl-* --atom3d-* --atom-* --plot-paper --plot-max-h --group-color
--stereo-color --mech-min-h --host-height --canvas-min --safe-*`. `--card-paper` wird Alias von `--paper`.
**Entfallen**: `--radius`, `--radius-sm`, `--radius-md`, `--shadow`, `--shadow-card`, `--border-radius-sm`-Rückfall,
jede wörtliche Farbe in JSX-Inline-Styles (`#e74c3c`, `#c0392b`, `var(--danger, …)`). Schriftgrößen 10/11/17 entfallen
außer `--text-title` schmal. Mono nur noch in der aufgeklappten Dateiliste.

**Global** (in `frame.css`): `:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }` für alle
Bedienelemente; Hover = `background: var(--surface-1)`, kein `filter: brightness`; Übergänge nur `background-color
120ms`, unter `prefers-reduced-motion` keine. Keine Schatten, keine Verläufe außer in der Kuhle.

---

## §4 Gemeinsame Bausteine (Vertrag für B und C)

Alles in `ui/components/Panel.jsx` (neu, A), Styles in `ui/styles/frame.css` (A). B und C bauen nur aus diesen
Bausteinen und erfinden keine eigenen Kopf-, Knopf- oder Fußformen. Bestehende Klassen, auf die Tests zielen,
bleiben als Haken erhalten (`.panel-title`, `.panel-subtitle`, `.structure-canvas`, `.structure-drawing`,
`.plot-svg`, `.batch-card`, `.candidate`, `.functional-group`, `.export-png`, `.add-to-anki`, `.key-facts`,
`.source-row`, `.group-section`, `.group-note`, `.panel-footer`, `.seg-spinner`, `.molecule-panel`, alle `data-*` und `data-testid`).

| Baustein | API | DOM und Maße | ersetzt |
|---|---|---|---|
| **Panel** | `<Panel kind="molecule" fill>` | `article.panel[data-panel=kind]`, Spalte mit `gap: var(--space-4)`, kein eigener Innenabstand (nur `body` 16 px, schmal 12 px) | Inline-Paddings in Protein, 3D, Plot, Anki, Mechanismus |
| **PanelHead** | `title, subtitle, foundAs, tabs, expand` | `header.panel-head`: Grid `1fr auto`; links `h2.panel-title` 19/26/600 und `p.panel-subtitle` 12/16 `--text-2`, eine Zeile mit Ellipse, voller Text im `title` (schmal zwei Zeilen); rechts Hauptreiter und Expand. Unter 480 px rutschen die Reiter in eine eigene Zeile unter den Titel, Expand bleibt rechts neben dem Titel | `SectionHeader`, `.panel-header` (bleibt als Alias) |
| **Tabs (Haupt)** | wie heute | `.seg`: Spur `--surface-1`, **keine Kante**, Radius m, Polster 2. Knopf 28 hoch (Spur 32), Radius s, 13/600 `--text-2`. Gewählt: `--surface-0`, `--text`, 1 px `--line` als `box-shadow` (springt nicht) | `Tabs.jsx` (nur Optik) |
| **Tabs (Unter)** und **Achse** | `size="sm"` bzw. `role=group` mit `aria-pressed` | gleiche Form, Knopf 24 (Spur 28), 12/600. Die Molekül-Achse bleibt `aria-pressed` (Probe: `checkBox` „2D“/„3D“), Protein-Achsen bleiben Tabs | `.seg-sm`, `.view-axis` |
| **ExpandButton** | wie heute | 32×32, ruhig, nur Symbol (eigenes SVG, zwei Diagonalpfeile, 1,5 px Strich), `aria-label="Expand"`, `title="Open in the side panel"` | Text-Knopf mit Rahmen |
| **StageBar** | `left, right` | `div.stage-bar`: Flex, `min-height 28`, `justify-content: space-between`, `gap 8`, darunter 8 px. Links Achse oder Unterreiter, rechts Hinweis (12, `--text-2`, ab < 480 px ausgeblendet, dann nur `title`) und ruhige Knöpfe (Reset view, Back/Next) | `RotateRow`, Protein-Steuerleiste, Mechanismus-Navigation |
| **Stage** | `variant="plain" \| "paper" \| "3d"` | `div.stage`. **plain** (Standard): keine Kante, keine Fläche, Breite 100 %, Höhe `--stage-h` (Chat) bzw. Rest (Fill). **paper**: `--paper`, Radius m, Polster 12, nur Scope. **3d**: volle Inhaltsbreite, Höhe `min(Breite, var(--stage-3d-max))` (Chat 1000: 968×720, nie kleiner als der Stand `60ee87b`); in Fill nimmt sie den Rest, schmal nie unter `--canvas-min`, breit nie unter 200 px | `.structure-canvas`-Rahmen, `.plot-svg`-Rahmen, `--bg-alt`-Flächen |
| **Facts** | `items=[{label, value, copy}]` | `dl.panel-facts.key-facts`: Flex-Zeile mit Umbruch, `gap 8px 32px`; `dt` 12/16 `--text-2`, `dd` 15/20 `--weight-regular`, `tabular-nums`; Kopierknopf ruhig hinter dem Wert. Schmal zwei Spalten | `Fact` in MoleculeView, Rf-Zeile, Anki-Zähler |
| **Chip** | `pressed, color, count` | `button.chip` (und `.functional-group`): 32 hoch, Pille, 1 px `--line`, Punkt 8 px in `--group-color`, Zahl `--text-2`. Gedrückt: Kante `--group-color`, Fläche `color-mix(--group-color 12%, --bg)`, 600. **Einzige Pille im Panel.** Stereo-Knopf und Ansichts-Chips werden ruhige Knöpfe | `.functional-group`, `.chip-toggle`, `.stereo-note-button`, `.balance-badge` |
| **Button** | `variant="quiet" \| "primary"`, `icon` | `button.btn`: 32 hoch, Polster 0 12, Radius m, 13/600. **quiet**: keine Kante, `--text-2`, Hover `--surface-1`, Text `--text`. **primary**: `--accent`/`--on-accent`, nur „Reveal all“. Ein Symbol 14 px links, aus einem eigenen Strich-Satz (1,5 px). `disabled`: `--text-2` bei 50 % Deckkraft, bleibt sichtbar | Export, Anki, Reset, Clear, Back/Next, Apply, Undo, Study-Knöpfe |
| **ContinueRow** | wie heute | eine Zeile: Etikett „Continue in chat“ 12/600 `--text-2`, dann Knöpfe als **quiet** mit 1 px `--line`-Kante (die einzige Knopfkante, weil sie eine Nachricht schreiben), 28 hoch, 13/400, **ohne Pfeil**. Umbruch erlaubt, schmal steht das Etikett über den Knöpfen | Pfeil-Knöpfe 36–40 px |
| **PanelFoot** | `files, children, hideFiles` | `footer.panel-foot.panel-footer`: Haarlinie oben, `padding-top 8`, eine Zeile 32 hoch. Links **Files-Schalter** (`button[aria-expanded]`, Text „Files“ + Zahl in `--text-2`, Chevron als SVG); offen: darunter eine Liste mit Etikett (12/600), Pfad (Mono 12, Ellipse links gekürzt, voll im `title`) und Kopierknopf je Zeile, dazu „Copy folder“. Rechts die Aktionen in fester Reihenfolge: Export PNG, Add to Anki. Rückmeldung („Saved: …“) ersetzt für 4 s den Files-Schalter, `role=status` | `PanelFooter` (Logik bleibt, `FooterStatus` bleibt) |
| **Hint** | `children, tone="quiet" \| "warn"` | `p.hint` 12/16 `--text-2`, höchstens zwei Zeilen; `warn` mit 6 px Punkt in `--danger`. Für Stereo-Satz, Projektionssatz, „3D cartoon unavailable …“, Zitat, Bilanz-Befund | `.panel-note`, `.panel-note-quiet`, Inline-Divs |
| **PanelState** | `kind="loading" \| "empty" \| "error", title, message` | nimmt die Bühnenhöhe ein (kein Sprung), Fläche `--surface-1`, Radius m, Text mittig 13; `error`: Titel 600 in `--text`, Satz `--text-2`, kein Rot in der Fläche. Laden: der vorhandene `.seg-spinner` 12 px, sonst keine Animation | `ToolPlaceholder`-Kästen (gestrichelt), `ToolError`, leere Zustände in Spectrum/Tlc/Plot/Scope/Mechanism/Ball3DCanvas |
| **CopyButton** | wie heute | 24×24 (`is-xs` 20), Radius s, ruhig; Zustand „copied“ = Häkchen-SVG in `--success`, keine Fläche | `.copy-button` |

---

## §5 Je Panel-Art

Skizzen: links Chat 1000, rechts Fill schmal 320. Angegeben ist nur, was vom Rahmen in §2 abweicht. Zielhöhen
gelten für den Chat bei 1000 und 860 px, jeweils im schlechtesten Fall (Continue-Zeile umgebrochen).

### 5.1 Molekül (Structure / Data / Study) — A
```
Koffein                       [Structure|Data|Study][⤢] │ Koffein                 [⤢]
PubChem: Caffeine (CID 2519)                            │ PubChem: Caffeine (CID…
[2D|All H|3D]                                           │ [Structure|Data|Study]
            ( Zeichnung 100 % × 320 )                   │ [2D|All H|3D]
Formula C8H10N4O2  Molar mass 194.19 g/mol  CAS 58-08-2 │ (Zeichnung, Rest)
(●Amide 3) (●Aromatic ring 2)  Click a group to pin it  │ Formula      Molar mass
● 1 unspecified stereocenter  [Show variants]           │ CAS
```
- **Entfällt:** die rechte Kernwert-Spalte samt Trennlinie, der Bühnenrahmen, die Linie unter dem Kopf und das Etikett „Functional groups“ (die Chips erklären sich; das Etikett lebt als `aria-label` der Sektion weiter).
- **3D-Modus:** Bühne `variant="3d"`, volle Breite × 720 bei 1000 px (bei 860 px volle Breite × 720). Rechts in der StageBar „Drag to rotate“ und „Reset view“. Die Kernwerte bleiben als Zeile darunter; Gruppen und Stereo bleiben aus.
- **Data:** Unterreiter PubChem/GHS in der StageBar; Tabelle `.source-row` 36 hoch, Etikettspalte 10,5 em, Linie nur zwischen Zeilen. Der Quellen-Link steht als Hint unter der Tabelle. GHS-Aufklapper mit SVG-Chevron statt ▸▾.
- **Study:** gleiche Geometrie wie Structure. Verdecktes = `--surface-1` mit 1 px gestrichelter `--line-strong`-Kante; das ist die einzige gestrichelte Form, sie bedeutet „verdeckt“. Im Fuß keine Files und kein Export, nur Add to Anki. **B9 beheben:** In Fill bekommt die Study-Bühne dieselbe Flex-Kette wie Structure (`[data-view="study"] .stage { flex: 1 0 var(--canvas-min) }`).
- **Ziel:** 2D ≤ 660 / ≤ 700 px; Data ≤ 700 px (10 Zeilen); 3D ≈ 1000 px (ausgenommen).

### 5.2 Datenblatt (lookup_molecule_data) — A
Wie 5.1 mit Startreiter Data. Der Untertitel wird der PubChem-Datensatz wie im Molekül-Panel (nicht die Formel).
Add to Anki im Fuß wie beim Molekül. Ziel ≤ 700 px.

### 5.3 Batch (Raster und Detail) — A
```
3 structures                                  [⤢] │ 6 structures        [⤢]
Open a structure for its data sheet and export.   │ ┌────────┐┌────────┐
┌──────────┐ ┌──────────┐ ┌──────────┐            │ │ (bild) ││ (bild) │
│  (bild)  │ │  (bild)  │ │  (bild)  │            │ │benzene ││toluene │
│ benzene  │ │ toluene  │ │ phenol   │            │ │C6H6 78…││C7H8 92…│
│ C6H6 78… │ │ C7H8 92… │ │ C6H6O 94…│            │ └────────┘└────────┘
└──────────┘ └──────────┘ └──────────┘            │
Not drawn (1): xyz                                │
```
- Karten: 1 px `--line`, Radius m, Polster 12, Bild 120 hoch, Name 13/600, Fakten 12 `--text-2`. Hover: Kante `--line-strong`. Spalten `minmax(180px, 1fr)`, schmal `minmax(128px, 1fr)`.
- Fuß: „Files“ zeigt den Ordner. Fehlschläge als Hint `warn`.
- Detail: Rückweg als quiet Button mit Chevron links, „Back to all structures“, darunter das volle Molekül-Panel (5.1) ohne eigenen Expand. Position „2 / 6“ rechts in derselben Zeile.
- Ziel: 6 Strukturen ≤ 700 px.

### 5.4 Auswahl (AmbiguousView) — A
Kandidaten-Karten wie Batch-Karten (dieselbe Klasse `.candidate` behält ihre Maße und übernimmt Kante und Radius
der Batch-Karte). Rückweg wie im Batch-Detail. Status „Drawing …“ direkt unter dem Raster als Hint.

### 5.5 Vergleich (compare_molecules) — B
```
Ibuprofen vs. Naproxen                        [⤢] │ Ibuprofen vs. Naproxen
Structure comparison · differences highlighted    │ (Bild, volle Breite)
  ( beide Strukturen, Bühne plain, ≤ 400 hoch )   │
```
Bühne plain (heute Plotrahmen). Bildunterschriften bleiben im SVG. Ziel ≤ 560 px.

### 5.6 Reaktion — B
Kopf mit Expand. Bühne plain (die gefüllte `--bg-alt`-Fläche entfällt). Darunter als Facts-Zeile: Bilanz als Text mit
SVG-Häkchen („balanced“, `--success`) oder als Hint `warn` mit „Apply coefficients“ und „Undo“ als quiet Buttons.
Ziel ≤ 440 px.

### 5.7 Mechanismus — B
```
Nucleophilic Substitution (SN2) — 2-bromobutane…  [Overview|Step by step][⤢]
SN2 · 3 steps
 Übersicht: Kacheln ohne Kartenfläche, Pfeile 30 px, Übergangszustand in --accent
 Step:  [‹ Back]        Step 1 / 3 · Reactants: backside attack  ● ○ ○        [Next ›]
        ( Schritt, Bühne plain )
```
- **Entfällt:** die gefüllte Karte um die Bühne. Back/Next werden quiet Buttons (32 hoch, Chevron-SVG statt „←“) in der StageBar. Zähler und Punkte in der Mitte; die Punkte behalten `aria-label="Step n"` und die Zahl bleibt im Format „Step n / N“ (Tests).
- `utils/mechanismLayout.js`: `TILE_PAD`, `CAPTION_H`, `ARROW_*` bleiben; nur die verfügbare Breite ändert sich (kein Kartenpolster mehr).
- Ziel: Übersicht ≤ 700 px, Schritt ≤ 620 px.

### 5.8 Spektrum, Titration, Speziesverteilung, Pharma-Kurven (PlotView) — B
```
Aspirin IR                                    [⤢] │ Aspirin IR          [⤢]
IR · schematic, drawn from the given peak list    │ IR · schematic…
   ( Plot, Bühne plain, Breite 100 %, ≤ 400 )     │ (Plot, Rest)
Ester-C=O 1750 cm⁻¹ · Säure-C=O 1690 cm⁻¹ (Notes) │
```
Bühne plain, kein Rahmen und kein Polster. Die Fläche färbt weiter über `--plot-paper`. Notizen als Facts-Zeile,
sonst als Hint. Der matplotlib-Titel bleibt im Export (Exportdateien unverändert). In der Anzeige blendet CSS ihn aus:
`.plot-svg[data-svg-source="matplotlib"] [data-plot-title]`, sofern der Renderer die Marke setzt. Fehlt die Marke,
bleibt der Titel stehen; eine Python-Änderung gehört nicht in diese Runde. Ziel ≤ 620 px.

### 5.9 DC-Platte — B
Die Platte bleibt hell (Kieselgel), der Plotgrund färbt sich mit dem Panel. Bühne plain, Höhe `--plot-max-h`, die Platte
steht mittig. Die Rf-Werte stehen als Facts-Zeile („Edukt 0.30“, Wert 15/400, keine Mono-Schrift). Ziel ≤ 640 px.

### 5.10 Scope (Profil full) — B
Bühne **paper** (`--paper`, Radius m): Die Grafik ist eine Druckvorlage mit festem Weiß und bekommt so eine bewusste
Papierkante statt einer randlosen weißen Fläche (B11). Einträge als Facts-Zeile, Fehlliste als Hint `warn`. Ziel ≤ 520 px.

### 5.11 3D-Einzelansicht (generate_3d) — C
```
Koffein                                       [⤢] │ Koffein             [⤢]
3D conformer (ETKDG + force field) · C8H10N4O2    │ 3D conformer (ETKDG…
                drag to rotate · [Reset view]     │          [Reset view]
      ┌ Kuhle volle Breite × 720 ┐                │  ( Kuhle 296 × 296 )
Formula C8H10N4O2   Molar mass 194.19 g/mol       │ Formula   Molar mass
```
- Bühne `variant="3d"`, dieselbe Regel wie im Molekül-Panel. Die Kuhle ist die einzige Form (kein Rahmen, keine Fläche). Untertitel beginnt mit „3D conformer“ (Probe). Molmasse und Formel wandern aus dem Untertitel in die Facts.
- In Fill rückt der Fuß direkt unter die Facts, der Rest bleibt unten frei. Das beseitigt den Streifen aus B1.
- Ziel im Chat: 720 + ~170 ≈ 890 px (ausgenommen).

### 5.12 Protein / Antikörper — C
```
Trastuzumab Fab fragment, therapeutic antibody… [Structure|Scheme][⤢] │ Trastuzumab Fab…   [⤢]
PDB 1N8Z · chains A/B · 434 residues                                  │ PDB 1N8Z · 434 res.
[Secondary|Chain|Rainbow N→C] [Cartoon|Trace]   drag · [Reset]        │ [Structure|Scheme]
        ( Bühne volle Breite × 520, Mol* oder Spur )                  │ [Sec|Chain|Rainbow]
▬ light chain (A)  ▬ heavy chain (B)                                  │ [Cartoon|Trace][Reset]
One Fab arm of the IgG; the antigen is not shown. PDB 1N8Z (wwPDB, CC0)│ (Bühne, Rest)
```
- Der Hauptreiter Structure/Scheme sitzt im Kopf. Die Achsen Colour by und Representation sind Unterreiter in der StageBar, „Reset“ ist ein quiet Button rechts darin (nicht mehr in einer `.seg`-Spur).
- Der Untertitel nennt nur die Herkunft (PDB, Ketten, Reste). „from the complex …“ und die Fußnoten werden **eine** Hint-Zeile unter der Legende.
- Die Bedienhilfe („pinch or ⌘/Ctrl+scroll …“) steht nur im `title` der Bühne; sichtbar bleibt „drag to rotate“ in der StageBar.
- **Struktur zählt als 3D:** Bühnenhöhe im Chat 520 px (heute 280), volle Breite. Scheme nutzt dieselbe Höhe, damit der Reiterwechsel nicht springt.
- Legende als Zeile (Balken 16×4, Radius s). Inline-Styles wandern nach `styles/c-protein-3d-anki.css`. Der Fallback „3D cartoon unavailable here (no WebGL) — showing the backbone trace.“ wird Hint `warn`.
- Fuß: Files zeigt bis zu vier Dateien, zu.
- Ziel im Chat ≈ 780 px (ausgenommen); Scheme ebenso.

### 5.13 Anki-Deck — C
```
Koffein und Paracetamol                           │ Koffein und Paracetamol
2 cards · 2 images · import the .apkg into Anki   │ 2 cards · 2 images…
APKG  ~/ChemDraw-Output/anki/koffein-….apkg [⧉]   │ APKG ~/ChemDraw-Output…
┌ Front │ Back ┐ ┌ Front │ Back ┐                 │ ┌ Front │ Back ┐
```
- **Ausnahme vom Files-Schalter:** Die `.apkg` ist das Ergebnis selbst. Sie steht sichtbar als Facts-Zeile mit
  Etikett „APKG“ (12/600) und Pfad (Mono 12) samt Kopierknopf. Die Probe sucht `APKG` und `~/ChemDraw-Output/`.
- Karten: 1 px `--line`, Radius m, Vorder- und Rückseite nebeneinander, Bilder auf `--paper` mit Radius s. Höchstens 4 Karten, dann „+ N more cards“ als Hint.
- Ziel ≤ 700 px.

### 5.14 Platzhalter und Fehler — A
`ToolPlaceholder` zeigt Titel und Untertitel aus `toolinput` im echten Kopf, darunter `PanelState kind="loading"` in
der Bühnenhöhe der erwarteten Panel-Art (Raster für Batch). `ToolError` wird `PanelState kind="error"` unter einem
Kopf mit dem Tool-Titel. `HostDiagnostics` bleibt unverändert (Entwicklerhilfe).

---

## §6 Bedienungshilfen: Namen und Rollen

**Ändert sich: nichts.** Jeder Name aus `scripts/desktop-probe/checkpoints.json` bleibt mit Rolle:
`Export as PNG` · `Add a flashcard to the Anki deck …` · `Reset view` (Molekül, 3D) · `Reset` (Protein) · `Clear` ·
`3D model, drag to rotate` (Bild) · Gruppe `Continue in chat` · `Back to all structures` · `Open step N: …` ·
Reiter `Structure`/`Data`/`Study`/`PubChem`/`GHS`/`Overview`/`Step by step`/`Scheme`/`Secondary`/`Chain`/`Cartoon`/`Trace` ·
Achse `2D`/`All H`/`3D` und Gruppen-Chips als `aria-pressed` (im Baum `checkBox`) · Batch-Karten `"<name>, <formel>, <masse>"` ·
statische Texte `balanced`, `light chain (A)`, `APKG`, `~/ChemDraw-Output/`, Untertitel beginnt mit `3D conformer` und `2 cards`.

`Expand` verliert den sichtbaren Text und behält den Namen über `aria-label`. Die Pfeile der Continue-Knöpfe waren
`aria-hidden` und ändern den Namen nicht. „Reset“ beim Protein verlässt die `.seg`-Spur und bleibt `button` mit
demselben Namen.

**Neu:** `button` „Files“ mit `aria-expanded` und `aria-controls` auf die Liste (Name „Files, 2“). In der Liste je
Zeile `Copy path` (wie heute) und `Copy folder`. Die Fuß-Rückmeldung hat `role=status` (wie heute).
**Folge:** Pfade sind bei zugeklappter Liste nicht im Baum. Kein Checkpoint außer Anki sucht sie, und Anki zeigt den Pfad sichtbar (5.13).
Tastatur: Alle Reiter bleiben nach WAI-ARIA Tabs (manuelle Aktivierung). Der Files-Schalter öffnet mit Enter oder Leertaste, Escape schließt die Liste und setzt den Fokus zurück. Fokusringe nach §3.

---

## §7 Drei Pakete

**Reihenfolge:** A liefert zuerst **A0** (ein Commit, ~1 h), dann bauen A, B und C parallel. A0 enthält:
`styles/tokens.css`, `styles/frame.css` mit allen Bausteinen aus §4, `components/Panel.jsx` mit den Exporten aus §4,
die leeren Dateien `styles/b-graphics.css` und `styles/c-protein-3d-anki.css`. Die Import-Zeilen in `main.jsx` stehen
in dieser Reihenfolge: tokens, styles, frame, b, c. Außerdem verschiebt A0 den Block der `.plot-svg`-Umfärbung
**unverändert** aus `styles.css` nach `b-graphics.css` und alle `.m3d-*`, `.protein-*`, `.anki-*`, `.rotate-row`,
`.bowl`-Regeln nach `c-protein-3d-anki.css`. Ab dann gilt: Niemand außer A berührt `styles.css`, `tokens.css`, `frame.css` oder `Panel.jsx`.
Fehlt B oder C ein Baustein, meldet das Paket ihn an A und baut ihn nicht selbst.

| Paket | Dateien (ausschließlich) | Abnahme |
|---|---|---|
| **A Fundament** | `styles.css`, `styles/tokens.css`, `styles/frame.css`, `main.jsx`, `App.jsx`, `components/Panel.jsx` (neu), `Tabs`, `ViewToggle`, `ExpandButton`, `SectionHeader`, `PanelFooter`, `ContinueRow`, `CopyButton`, `ExportPngButton`, `AddToAnkiButton`, `RotateRow` (geht in StageBar auf), `ToolPlaceholder`, `ToolError`, `HostDiagnostics`, `FunctionalGroupList`, `StereoNote`, `StudyPanel`, `SourceList`, `StructureCanvas`, `AtomHighlights`, `AtomTooltip`, `Formula`, `FoundAs`; `MoleculeView`, `DatabaseView`, `BatchView`, `AmbiguousView`; `ModelContext.jsx` nur lesen; `scripts/desktop-probe/checkpoints.json` (allein A, Ziel: keine Änderung); `host/host.e2e.mjs`, `host/panel-shots.mjs` und die Tests dieser Komponenten | Chat 1000: Molekül 2D ≤ 660 px, Data ≤ 700, Batch-6 ≤ 700; 860: alle ≤ 700. 3D im Molekül-Panel: Kuhlen-Box volle Inhaltsbreite ± 4 und 720 hoch bei 1000 und 860 (nie kleiner als `60ee87b`: 968×720). Fill 320×700: die Molekül-Bühne ≥ 240 px hoch, keine waagrechte Rolle. Study in Fill: Bühne ≥ `--canvas-min` (B9). Kontraste nach §3, gemessen in beiden Themen. Kein Rahmen um `.stage`, genau eine Haarlinie (Fuß). `grep -E '#[0-9a-fA-F]{3,6}' frame.css` leer |
| **B Grafiken** | `PlotView`, `SpectrumView`, `TlcView`, `components/PlotFigure.jsx`, `ReactionView`, `MechanismView`, `utils/mechanismLayout.js`, `ScopeView`, `styles/b-graphics.css` und ihre Tests | Chat 1000: Spektrum, Titration und Spezies ≤ 620 px, DC ≤ 640, Vergleich ≤ 560, Reaktion ≤ 440, Mechanismus-Übersicht ≤ 700, Schritt ≤ 620. Plotbreite = Inhaltsbreite ± 0. Kein Inline-`style` mit Farbe. Scope dunkel: keine Fläche heller als `--paper` außerhalb der Papierbühne. Back/Next 32 hoch und beide sichtbar |
| **C 3D, Protein, Anki** | `Molecule3DView`, `ProteinView`, `components/Ball3DCanvas.jsx`, `BackboneCanvas`, `IgGScheme`, `protein/*`, `utils/atoms3d.js`, `AnkiDeckView`, `styles/c-protein-3d-anki.css` und ihre Tests | Chat 1000: Kuhle volle Inhaltsbreite ± 4 × 720 bei 1000 und 860 (heute 936×640, nicht kleiner); Protein-Bühne 520 hoch, volle Breite, in Struktur und Scheme gleich. Fill 320×700: Kuhle ≥ 280, kein Leerstreifen zwischen Facts und Fuß. Ohne WebGL weiter die Spur, nie eine leere Fläche (`test:host`). Anki ≤ 700 px, `APKG` und Pfad sichtbar. Protein: höchstens zwei Steuerzeilen bei 1000, drei bei 320 |

**Gemeinsame Abnahme** (A führt zusammen): Ein frischer `npm --prefix chemdraw_tool/ui run build` erzeugt das Bündel,
dann laufen `./test.sh`, `test:host`, `test:inspector` und die Bildserie von `host/panel-shots.mjs` in drei Größen, hell
und dunkel. Ein Desktop-Lauf (`scripts/desktop-probe/run.sh A` und `B`, zweimal grün in Folge) ist fällig, weil
Expand, Reiter und Fuß hostspezifisch bedient werden. Exportdateien unverändert: Die Golden-SVGs und
`aspirin.expected.png` bleiben unberührt. Unverändert gelten außerdem: `ModelContext` ist der einzige Sender,
`loadToolData` überall, Study verrät den Namen nirgends (auch nicht über Files, `title` oder Dateinamen), Texte englisch.
