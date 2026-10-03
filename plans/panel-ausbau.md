# Panel-Ausbau: Ansichten, Animation, Abfrage- und Prüfungsmodus (Jay, 03.10.2026)

Ziel: Das Moleküle-Panel wird vom Bild zum Lernwerkzeug. **Eine** Molekülanfrage liefert alle Ansichten, man schaltet sofort um, wird durch die Optionen geführt, und kann sich selbst abfragen.

## Deine Gedanken, sortiert

| # | Gedanke | Kern | Baut auf |
|---|---|---|---|
| A | Zwischen Ansichten umschalten (Stereo, 3D, …) | ein Payload, mehrere Ansichten, Umschalter im Kopf | — |
| B | Animationen, auch zum Schleifen | 3D-Dauerdrehung, weiche Übergänge, Mechanismus-Autoplay | A |
| C | Seitenpanel feiner und sauberer | Layout-Grundsätze statt Einzelfall-Styles | A |
| D | Durch die Tool-Optionen geführt werden | Optionsleiste (Stil, Stereo-Labels, Abkürzungen) + Folge-Vorschläge | A, C |
| E | Abfragemodus (Teile verdecken, aufdecken) | Funktionelle Gruppen/Atome abdecken, Klick deckt auf | A, C |
| F | Prüfungsmodus | feste Fragenfolge, kein Hinweis, Auswertung, Fehler → Anki | E |

Reihenfolge: **A → C → D → B → E → F.** Grund: A und C legen das Grundgerüst, von dem alles andere abhängt. B gehört nach D, weil Animationen erst Sinn haben, wenn Ansichten und Layout stehen. F ist E plus Zählen und Auswerten.

## Messungen, auf denen der Plan steht (03.10.)

- 3D-Erzeugung kostet **10–30 ms** je Molekül → alle Ansichten können **gleich im Payload** mitkommen, das Umschalten bleibt lokal und ohne Spinner (wie schon „→ Struktur"). Nur das Datenblatt (PubChem, ~2 s) bleibt beim Klick geladen.
- Das Panel kennt schon `functionalGroups` mit `atomIndices` und `AtomData` mit x/y → Abdecken pro Gruppe ist ohne neue Chemie machbar.
- Die 3D-Ansicht ist heute ein eigenes Werkzeug (`generate_3d`) mit eigener SVG-Drehlogik, kein WebGL — das bleibt so (Bundle-Größe, Panel-iframe).
- Bundle heute 524 kB; Budget für den ganzen Ausbau: **≤ 650 kB**.

## Entscheidungen, die ich getroffen habe (du kannst widersprechen)

1. **Ansichten gleich mitliefern**, nicht nachladen (siehe Messung). Zusatz: Payload wächst um wenige kB.
2. **Stereo-Ansicht = dieselbe Struktur mit CIP-Beschriftung (R/S, E/Z)**, nicht ein anderes Bild; die Server-Option `annotate_stereo` bleibt, das Panel bringt beide SVGs mit.
3. **Abfrage- und Prüfungsmodus sind Panel-Modi**, gestartet über ein Werkzeug-Argument (`mode`), nicht über neue Werkzeuge. Grund: Werkzeug-Obergrenze (23) und die Abgrenzungs-Regeln; ein neues Werkzeug nur, wenn die Tool-Wahl-Messung zeigt, dass „frag mich ab" sonst nicht ankommt.
4. **Fehler aus dem Prüfungsmodus gehen als Anki-Deck raus** (`export_anki_deck` existiert) — der Rückweg, damit das Üben nicht beim Schließen des Panels verschwindet.

## Phase 0 — Grundlage und zwei Versuche (ca. 1 Stunde)
- [ ] Ausgangsbilder: `tests/gallery_ui.py` als Vorher-Stand ablegen (`docs/produkt/panel-vorher/`)
- [ ] Versuch 1: Kann das Panel dem Chat eine Nachricht schicken (`ui/message` der AppBridge)? Im Host-Test prüfen, dann **einmal in Desktop von Hand** — davon hängt D (Folge-Vorschläge) ab
- [ ] Versuch 2: Panelhöhe in Desktop messen (wie viel Platz bleibt unter dem Chat-Text?) — davon hängt das Layout in C ab
- [ ] Bundle-Budget als Test: `dist/index.html` ≤ 650 kB, rot sonst

## Phase 1 — Ansichtsumschalter (A) → Release 0.5.0
- [ ] Payload: `MoleculePayload` bekommt `svg_stereo` und `mol3d` (Atome/Bindungen), nur wenn nicht zu groß (Obergrenze Atomzahl, sonst leer + Hinweis)
- [ ] Panel: Reiter **Struktur · Stereo · 3D · Daten**; 3D-Ansicht als wiederverwendbare Komponente (aus `Molecule3DView` herausgelöst, gleiche Drehung)
- [ ] Tests: Host-Test klickt durch alle vier Reiter; Komponententest je Ansicht; Payload-Parität (Python ⇄ App.jsx)
- [ ] 10-Sekunden-Test für Jay: „Zeichne Ibuprofen" → Stereo klicken (R/S sichtbar) → 3D klicken (dreht sich) → Data

## Phase 2 — Seitenpanel und Layout (C) → 0.5.1
- [ ] Gestaltungsgrundsätze in `styles.css` als Tokens (Abstände, Schriftgrößen, Kartenstil), nicht pro View
- [ ] Steckbrief: einklappbare Abschnitte, klarere Hierarchie, Kopierknöpfe einheitlich
- [ ] Schmal/breit: Seitenleiste wird unter 560 px ein Block unter dem Bild
- [ ] Hell/dunkel prüfen; Galerie vorher/nachher nebeneinander ansehen

## Phase 3 — Geführte Optionen (D) → 0.6.0
- [ ] Optionsleiste: Stil (kompakt / Präsentation / Graustufen), Stereo-Beschriftung, Gruppen abkürzen — Änderung ruft das Werkzeug erneut auf (`callServerTool`), Ergebnis ersetzt das Bild
- [ ] Folge-Vorschläge unter der Struktur („Mechanismus", „Vergleichen mit …", „Karteikarte") — **nur wenn Phase-0-Versuch 1 klappt**, sonst als kopierbarer Prompt
- [ ] Eval: Tool-Wahl-Fälle unverändert grün (28/28 Basis), Beschreibungen nicht länger

## Phase 4 — Animationen (B) → 0.6.1
- [ ] 3D: Dauerdrehung mit Pause/Weiter, stoppt bei Ziehen, respektiert `prefers-reduced-motion`, pausiert, wenn das Panel nicht sichtbar ist
- [ ] Weiche Übergänge beim Ansichtswechsel (kurz, abschaltbar)
- [ ] Mechanismus: Schritte automatisch durchlaufen (Schleife, Tempo einstellbar)
- [ ] Messung: Bildrate bei 50 Atomen ≥ 30 fps, sonst automatisch weniger Details

## Phase 5 — Abfragemodus (E) → 0.7.0
- [ ] `mode="quiz"` im Werkzeug; Panel zeigt die Struktur mit abgedeckten funktionellen Gruppen
- [ ] Klick deckt auf; „Wusste ich / Wusste ich nicht" pro Gruppe; Zähler
- [ ] Varianten: Name verdecken, Gruppen verdecken, nur Gerüst zeigen
- [ ] Tests: Abdeckung deckt genau die Atome der Gruppe; Aufdecken ist umkehrbar; Zustand nur im Panel (kein Server)

## Phase 6 — Prüfungsmodus (F) → 0.7.1
- [ ] Fragenfolge (N Strukturen), Fragetypen: Gruppen benennen, Name zur Struktur wählen, Stereozentren zählen/bestimmen (R/S)
- [ ] Kein Hinweis während der Prüfung, Auswertung nach Bereich (wie der Klausurmodus im Rechner)
- [ ] Fehler → Anki-Deck mit den falsch beantworteten Strukturen
- [ ] Optional: Zeitlimit

## Für jede Phase gilt
Tests zuerst und einmal rot gesehen · `./test.sh` grün · Host-Test und Galerie angesehen · CHANGELOG · README-Bild aktualisieren, wenn sich das Aussehen ändert · Release erst nach deinem Go.

## Offene Fragen an dich
- [ ] Welche Fachrichtung für die Prüfungsfragen zuerst: **Pharmazeutische Chemie** (Strukturen, funktionelle Gruppen) oder **Pharmakologie** (Wirkstoffklassen)? Empfehlung: Pharmazeutische Chemie — die Daten dafür gibt es schon.
- [ ] Soll der Abfragemodus auch **Reaktionen/Mechanismen** abdecken (Edukte verdecken)? Empfehlung: erst Moleküle, Reaktionen als Phase 7.
