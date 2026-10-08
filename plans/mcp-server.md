# MCP-Server: Panel, Werkzeuge, Releases

> Zusammengelegt 08.10.2026 aus `plans/archiv/panel-ausbau.md` (03.10.) und dem MCP-Teil von
> `plans/produkt.md` (02.10.). Frühere, abgeschlossene Etappen: `plans/archiv/repo-level-up.md`
> (14.08.), `routing-und-umschalter.md` (15.08.), `studi-funktionen.md` (15.08.).
> Gate je Schritt: `./test.sh` grün · `npm --prefix chemdraw_tool/ui run test:host` · `./scripts/handshake.sh`.
> Vor Panel-/Manifestarbeit: `uv run python scripts/anthropic_sync.py --check` (CLAUDE.md).

## Etappen

### Etappe 03.10.2026: Panel-Ausbau — Ansichten, Animation, Abfrage- und Prüfungsmodus

Ziel: Das Moleküle-Panel wird vom Bild zum Lernwerkzeug. **Eine** Molekülanfrage liefert alle Ansichten, man schaltet sofort um, wird durch die Optionen geführt, und kann sich selbst abfragen.

Stand 08.10.: außer M0 und der Recherche W-1c ist nichts davon gebaut (geprüft: keine `readOnlyHint`, kein `svg_stereo`, kein `mode="quiz"`, kein Bundle-Budget-Test im Code).

#### Wow-Moment zuerst (Fokusänderung 03.10. abends — gilt vor den Phasen unten)
Jay: erst das Layout im Chat, Ansichten ohne Nachfragen umschaltbar, **allgemein** für alle, die es auf GitHub ausprobieren (Chemie, Pharmazie, Biologie). Liste aller Möglichkeiten: `docs/produkt/panel-moeglichkeiten.md`.

- [ ] **M3** alle 23 Werkzeuge mit `title` und `readOnlyHint` annotieren (Snapshot-Tests mit freigeben) — fehlt: `docs/anthropic/abgleich.md:27` „✗ 0 von 23"
- [ ] **M2** Größen der Panel-Ergebnisse messen (Grenze ~150.000 Zeichen, sonst lädt das Panel nicht), Großes nachladen
- [ ] **M7** Manifest: Icon (512 px), `privacy_policies`, Windows testen oder ausschließen; **M8** README: Organisationen können Extensions sperren — fehlt: `abgleich.md:35-36`
- [ ] W-1 Nativer Look: Host-Farben/-Schrift (`--color-*`, `--font-sans`) statt eigener Tokens, Skelett statt Spinner, Tippflächen ≥ 44 pt (Baustein 13)
- [ ] W-1b Quiz-Satz in den `instructions` + Eval-Fall (Baustein 14)
- [ ] W0 Host-Messung: Zeile im Panel „Claude Desktop · Vollbild · Nachricht · Download …" (1 h) — entscheidet über W4, Phasen 5, 6
- [ ] W1 Reiter **Struktur · Stereo · 3D · Daten** von Anfang an (= Phase 1 unten)
- [ ] W2 3D dreht sich von selbst, weicher Wechsel (Teil von Phase 4 vorgezogen)
- [ ] W3 **Browser-Demo ohne Installation**, Link ganz oben im README (Hebel für Sterne)
- [ ] W4 je nach W0: Atom anklicken → Claude erklärt · Vollbild + Download · Folge-Vorschläge
- [ ] W5 README neu aufbauen um den Wow-Moment (GIF der Reiter, Demo-Link) — erst nach W1–W3, sonst verspricht es Ungebautes
- [ ] W6 danach: Blind-Modus, Prüfmodus (Phasen 5–6), Biologie-Paket, Wirkstoffklassen-Galerie
- [x] **M0** `ext-apps` 2.0.3 migriert (ac13350, 1bacd64): keine Codeänderung im Panel, Bundle 524 → 399 kB, Gate/Host-Test/Handshake grün; MCP-Fassung 2026-07-28 gelesen, nichts zu tun (`docs/anthropic/abgleich.md` §1)
- [x] W-1c Recherche: Anthropic-Verzeichnis, geht ein lokaler Server? (bcf3286, `docs/anthropic/abgleich.md:38-50`: lokal nicht als Connector einreichbar, .mcpb nicht mehr angenommen, Weg wäre Plugin-Bundle)

#### Phase 0 — Grundlage und zwei Versuche (ca. 1 Stunde)
- [ ] Ausgangsbilder: `tests/gallery_ui.py` als Vorher-Stand ablegen (`docs/produkt/panel-vorher/`)
- [ ] Versuch 1: Kann das Panel dem Chat eine Nachricht schicken (`ui/message` der AppBridge)? Im Host-Test prüfen, dann **einmal in Desktop von Hand** — davon hängt D (Folge-Vorschläge) ab
- [ ] Versuch 2: Panelhöhe in Desktop messen (wie viel Platz bleibt unter dem Chat-Text?) — davon hängt das Layout in C ab
- [ ] Bundle-Budget als Test: `dist/index.html` ≤ 650 kB, rot sonst

#### Phase 1 — Ansichtsumschalter (A) → Release 0.5.0
- [ ] Payload: `MoleculePayload` bekommt `svg_stereo` und `mol3d` (Atome/Bindungen), nur wenn nicht zu groß (Obergrenze Atomzahl, sonst leer + Hinweis)
- [ ] Panel: Reiter **Struktur · Stereo · 3D · Daten**; 3D-Ansicht als wiederverwendbare Komponente (aus `Molecule3DView` herausgelöst, gleiche Drehung)
- [ ] Tests: Host-Test klickt durch alle vier Reiter; Komponententest je Ansicht; Payload-Parität (Python ⇄ App.jsx)
- [ ] **Jay:** 10-Sekunden-Test: „Zeichne Ibuprofen" → Stereo klicken (R/S sichtbar) → 3D klicken (dreht sich) → Data

#### Phase 2 — Seitenpanel und Layout (C) → 0.5.1
- [ ] Gestaltungsgrundsätze in `styles.css` als Tokens (Abstände, Schriftgrößen, Kartenstil), nicht pro View
- [ ] Steckbrief: einklappbare Abschnitte, klarere Hierarchie, Kopierknöpfe einheitlich
- [ ] Schmal/breit: Seitenleiste wird unter 560 px ein Block unter dem Bild
- [ ] Hell/dunkel prüfen; Galerie vorher/nachher nebeneinander ansehen

#### Phase 3 — Geführte Optionen (D) → 0.6.0
- [ ] Optionsleiste: Stil (kompakt / Präsentation / Graustufen), Stereo-Beschriftung, Gruppen abkürzen — Änderung ruft das Werkzeug erneut auf (`callServerTool`), Ergebnis ersetzt das Bild
- [ ] Folge-Vorschläge unter der Struktur („Mechanismus", „Vergleichen mit …", „Karteikarte") — **nur wenn Phase-0-Versuch 1 klappt**, sonst als kopierbarer Prompt
- [ ] Eval: Tool-Wahl-Fälle unverändert grün (28/28 Basis), Beschreibungen nicht länger

#### Phase 4 — Animationen (B) → 0.6.1
- [ ] 3D: Dauerdrehung mit Pause/Weiter, stoppt bei Ziehen, respektiert `prefers-reduced-motion`, pausiert, wenn das Panel nicht sichtbar ist
- [ ] Weiche Übergänge beim Ansichtswechsel (kurz, abschaltbar)
- [ ] Mechanismus: Schritte automatisch durchlaufen (Schleife, Tempo einstellbar)
- [ ] Messung: Bildrate bei 50 Atomen ≥ 30 fps, sonst automatisch weniger Details

#### Phase 5 — Abfragemodus (E) → 0.7.0
- [ ] `mode="quiz"` im Werkzeug; Panel zeigt die Struktur mit abgedeckten funktionellen Gruppen
- [ ] Klick deckt auf; „Wusste ich / Wusste ich nicht" pro Gruppe; Zähler
- [ ] Varianten: Name verdecken, Gruppen verdecken, nur Gerüst zeigen
- [ ] Tests: Abdeckung deckt genau die Atome der Gruppe; Aufdecken ist umkehrbar; Zustand nur im Panel (kein Server)

#### Phase 6 — Prüfungsmodus (F) → 0.7.1
- [ ] Fragenfolge (N Strukturen), Fragetypen: Gruppen benennen, Name zur Struktur wählen, Stereozentren zählen/bestimmen (R/S)
- [ ] Kein Hinweis während der Prüfung, Auswertung nach Bereich (wie der Klausurmodus im Rechner)
- [ ] Fehler → Anki-Deck mit den falsch beantworteten Strukturen
- [ ] Optional: Zeitlimit

#### Offene Fragen an Jay
- [ ] **Jay:** Welche Fachrichtung für die Prüfungsfragen zuerst: **Pharmazeutische Chemie** (Strukturen, funktionelle Gruppen) oder **Pharmakologie** (Wirkstoffklassen)? Empfehlung: Pharmazeutische Chemie — die Daten dafür gibt es schon.
- [ ] **Jay:** Soll der Abfragemodus auch **Reaktionen/Mechanismen** abdecken (Edukte verdecken)? Empfehlung: erst Moleküle, Reaktionen als Phase 7.

#### Grundlagen der Etappe (unverändert vom 03.10.)

| # | Gedanke | Kern | Baut auf |
|---|---|---|---|
| A | Zwischen Ansichten umschalten (Stereo, 3D, …) | ein Payload, mehrere Ansichten, Umschalter im Kopf | — |
| B | Animationen, auch zum Schleifen | 3D-Dauerdrehung, weiche Übergänge, Mechanismus-Autoplay | A |
| C | Seitenpanel feiner und sauberer | Layout-Grundsätze statt Einzelfall-Styles | A |
| D | Durch die Tool-Optionen geführt werden | Optionsleiste (Stil, Stereo-Labels, Abkürzungen) + Folge-Vorschläge | A, C |
| E | Abfragemodus (Teile verdecken, aufdecken) | Funktionelle Gruppen/Atome abdecken, Klick deckt auf | A, C |
| F | Prüfungsmodus | feste Fragenfolge, kein Hinweis, Auswertung, Fehler → Anki | E |

Reihenfolge der Phasen: **A → C → D → B → E → F.**

Messungen (03.10.): 3D-Erzeugung kostet 10–30 ms je Molekül → alle Ansichten kommen gleich im Payload mit, nur das Datenblatt (PubChem, ~2 s) lädt beim Klick. Das Panel kennt schon `functionalGroups` mit `atomIndices` und `AtomData` mit x/y. 3D bleibt SVG-Drehlogik, kein WebGL. Bundle heute **399 kB** (nach M0, CHANGELOG.md:14; am 03.10. noch 524 kB); Budget für den ganzen Ausbau **≤ 650 kB**.

Entscheidungen (Jay kann widersprechen): 1. Ansichten mitliefern, nicht nachladen. 2. Stereo-Ansicht = dieselbe Struktur mit CIP-Beschriftung, `annotate_stereo` bleibt. 3. Abfrage- und Prüfungsmodus sind Panel-Modi über ein Argument `mode`, keine neuen Werkzeuge. 4. Fehler aus dem Prüfungsmodus gehen als Anki-Deck raus (`export_anki_deck`).

Für jede Phase: Tests zuerst und einmal rot gesehen · `./test.sh` grün · Host-Test und Galerie angesehen · CHANGELOG · README-Bild aktualisieren, wenn sich das Aussehen ändert · Release erst nach Jays Go.

### Etappe 02.10.2026: MCP verfeinern und Releases 0.4.3–0.4.8 (aus `plans/produkt.md`)

- [ ] **Jay:** einmal von Hand in Desktop „Zeig mir Methylphenidat" → Data (nur noch Host-Eigenheiten, die der Nachbau `test:host` nicht kennt)
- [ ] `mcp-2-migration` (Worktree `.claude/worktrees/agent-a567114bbee585cc8`, Branch-Stand 836324b vom 02.10.): GEPARKT bis zum Desktop-Test. Die Vorbedingung „erst nach dem OPSIN-Merge" ist erfüllt (022507d); der Branch liegt jetzt 41 Commits hinter main → erneut mit main abgleichen (CHANGELOG-Konflikt), Gate + Handshake, dann mergen. Nicht nebenbei anfassen.
- [ ] Hinweis in `_INSTRUCTIONS`/README: Desktop nimmt die Sandbox, wenn man den MCP nicht nennt — prüfen, ob ein Satz in `instructions` das ändert (nur in Desktop messbar). Fehlt: `chemdraw_tool/server.py:205-240` enthält keinen solchen Satz
- [ ] Geschwindigkeit (zurückgestellt): Server-Import 1,4 s (mcp 0,33 · rdkit 0,25 · matplotlib 0,25) — nur lazy laden, wenn die Handshake-Zeit unter Last wehtut; Datenblatt-Ladezeit 2,3 s (PubChem) — Vorabladen nur, falls Jay es spürt
- [~] Option: Server-Import ohne RDKit/matplotlib — gestrichen 08.10.2026, weil Dublette des Geschwindigkeits-Hakens darüber
- [x] 0.4.6 veröffentlichen: PyPI, `.mcpb`, bei Jay installiert (v0.4.6 GitHub-Release 03.10., 20ff181; PyPI steht inzwischen auf 0.4.8; `dist/chemdraw-mcp-0.4.8.mcpb`; Desktop-Test 03.10. mit 0.4.7 verbunden)
- [x] **Jay:** `gh release create v0.4.6` (`gh release list`: v0.4.6 am 2026-10-03)
- [x] Run.sh-Sperre verwaist bei abgebrochener Installation: trap auf TERM/INT/HUP, PID-Datei, tote PID sofort übernehmen (Release 0.4.6, 20ff181)
- [x] Bundle-Startfix: feste Installation statt `uv tool run` (adaed6c)
- [x] Release 0.4.3 (Titer, Daten-Knopf, Bundle-Start + Sperre) und 0.4.4 (Index-Refresh im Bundle), 02.10.
- [x] OPSIN gemergt (022507d), 0.4.5 veröffentlicht (3681f7b) und bei Jay installiert (Desktop verbunden 21:36, 20 Tools)
- [x] Data-Knopf Methylphenidat automatisiert: `npm --prefix chemdraw_tool/ui run test:host` (AppBridge-Host + echter Server, 02.10.). Computer use auf die Claude-Desktop-App selbst ist gesperrt
- [x] Messung: `evals/tool-routing/run_claude.py` (Tool-Wahl über claude -p, Attrappen-Server) — 24/28 → 26/28
- [x] `lookup_molecule_data`: 6–8 Folgeaufrufe → 4 bei „Datenblatt mit allem" (237698f)
- [x] `test:host` schreibt nicht mehr ins echte `~/ChemDraw-Output` (9a3b8d6)
- [x] Entschieden (02.10.): `reaction-in-conversation` — Reaktion + Mechanismus ist gute Antwort, `forbidden` nur noch generate_molecule; `draw-scope-real` mit Strukturen im Prompt. Eval 28/28 in drei Wiederholungen (0e39eb0)
- [x] Dateipfade im Panel mit `~` gekürzt (6 Views), Tooltip hat den vollen Pfad (6c9b308)
- [x] Design-Galerie: `uv run python tests/gallery_ui.py` → /tmp/chem-gallery/sheet.png (13 Panel-Typen nebeneinander) (6c9b308)
- [x] Speziesverteilung: Legende neben der Achse (6763642, Test rot gesehen)
- [x] Geprüft, kein Fehler: Kalibrierkurve-Titel doppelt (der Titel im Bild gehört in die exportierten Dateien); Reaktion ohne Titel (Edukte/Produkte/Bedingungen sind beschriftet)
- [x] Mechanismus-Overview: gleiche Bindungslänge, Spalte statt Zeile, SN2-TS mit Platz für Teilbindungen (1bfedb2, Release 0.4.7)
- [x] Desktop-Test 03.10.: 0.4.7 verbunden, `generate_pk_curve` kam an, Zahlen stimmen (Css,av 4,74 mg/L, R 1,43). Desktop lädt MCP-Tools erst nach und nimmt sonst die Sandbox — Prompt mit „Nutze den ChemDraw-MCP" wirkt
- [x] Dateinamen von `generate_pk_curve`/`generate_dose_response` tragen ohne `drug` die Parameter (64a0cb8)
- [x] (0.4.8) Gleiches Überschreiben bei TLC, Scope, Kalibrierkurve, Reaktion ohne Titel und bei Titration — Dateiname aus den Eingaben ableiten, je mit Test (5c77bc5)
