# README als Produkt-Schaufenster (Jay 07.11.2026, 10:58)

> Jay: „Das Readme soll hochprofessionell sein — ein GIF mit Stereo, normal und H-Ansicht durchklicken,
> eines mit 3D, das alte GIF neu, coolere Moleküle, wir müssen das Produkt anpreisen. Codex zur
> Design-Hilfe, eine Opus-Session, strukturierte Arbeitsaufträge, Sessions im Griff.“
> Owner: Claude (Fable, Session `session_01RTLSKdWLwo7wdP4s56df4b`). Ein Plan je Thema: dieser.
> Punkt 9/10 in `plans/mcp-server.md` verweisen hierher.

## Stand (Owner pflegt; Helfer-Berichte sind Behauptungen bis zur Prüfung)

| Auftrag | Wer | Status | Abnahme durch Owner |
|---|---|---|---|
| A GIFs (3 Stück) + Design-Review | Codex, Tisch `20261107-104104-readme-gif-3d-chip` | **pausiert 11:20 (Jay: „lass“)** — Codex brach nach 3 unterbrochenen Blöcken ab: Space-Wechsel während Jays Bedienung, AX findet dann nichts (Belege `/tmp/chemdraw-desktop-test/2026-11-07/readme/`, Thalidomid (S)-Keil + CAS 841-67-8 bestätigt). Design-Review wartet auf Opus-Branch. Alternative bei Jays Ja: Aufnahme im Playwright-Host (`test:host`-Aufbau, echtes Panel, echter Server, kein Desktop-Rahmen) | Dateien selbst ansehen (Frames, Größe), Protokoll-Screenshots |
| B README-Text als Produktseite | Opus 5.5 (Agent, Worktree, Branch `readme-showcase`) | **gemerged 11:32** (Opus `56707ab`, Gates grün; Owner: Diff gelesen, Stichproben Export/Anki/MAX_OPEN_STEREO/Mechanismen am Code bestätigt; drei HTML-Slots für die GIFs offen) | erledigt |
| C Zusammenbau + Gate + Desktop-Blick | Claude (Owner) | wartet auf A und B | README auf GitHub rendern (gh-Vorschau), Bilder prüfen |
| D Design-Kritik Panel-UI + 3D (Jay 11:02: „3D cleaner und eindrucksvoller, Panel mit allen Tools besser sortiert“) | Opus 5.5 (Agent, Worktree, nur Bericht) | **Bericht gemerged 11:36** (`docs/design/panel-kritik-2026-11-07.md`, Opus `3eb1a05`; Owner: Stichproben am Code) | Top 5 an Jay; bei Ja: Bild für die iPad-Runde, dann Bau in Etappen mit DOM-/Host-Tests; **kein Code vor Jays Zustimmung** |

## Molekülwahl (Owner, geprüft 10:56 am Resolver: Stereozentren / Schweratome)

| GIF | Molekül | Warum | Geprüft |
|---|---|---|---|
| `demo-views.gif` (Skelett → All H → Show variants → (S) → Keil → Data) | **Thalidomid** | 1 offenes Stereozentrum, Varianten-Klick zeigt genau die Entscheidung, an der die Geschichte hängt | stereo=1, unspecified=1, 19 Schweratome |
| `demo-3d.gif` (Zeichnen → 3D → Drehen) | **Morphin** | starrer pentacyclischer Käfig, 5 Stereozentren — in 2D flach, in 3D ein Gerüst | stereo=5, 21 Schweratome |
| `demo-molecule.gif` (neu: Hover über funktionelle Gruppen → Data) | **Capsaicin** | Amid, Phenol, Ether, Alken — vier Gruppen zum Aufleuchten; „das Molekül, das Chili scharf macht“ | 22 Schweratome |
| Ersatz, falls eines hakt | Adrenalin (stereo 1), LSD (24), Testosteron (21) | | geprüft |

Aspirin/Ibuprofen bleiben in Tests und Fixtures; im README-Schaufenster kommen sie nicht mehr vor.

## Auftrag A — Codex: drei GIFs + Design-Review (Tisch-Faden oben)

Ergebnis: `assets/demo-views.gif`, `assets/demo-3d.gif`, `assets/demo-molecule.gif` (ersetzt das alte), je
≤ 800 px breit, ≤ 10 s, ≤ 3 MB, Panel-Ausschnitt statt Vollbild, Pausen vor jedem Klick (≥ 0,8 s), letzter
Frame hält 2 s. Aufnahme in Claude Desktop per `aufnahme-desktop.sh`/AX (Schwester-Repo). Pflicht-Vorprüfung:
Bundle enthält `data-layout-3d`, Desktop jünger als `dist/index.html`, Handshake grün. Chips der Zeichenfläche
sind keine AXButtons (Koordinate aus Screenshot). Keine Bearbeitung außer Zuschnitt und Kürzung von Wartezeiten
(Caption sagt das). Danach: Design-Review der README-Fassung von Opus (nach Owner-Signal im Faden): Hierarchie,
Hero, Bildgrößen, GitHub-Dark/Light, Mobil; Befunde mit Zeile, alle melden.
Nicht anfassen: `README.md`, `chemdraw_tool/`, `plans/`. Commit nur `assets/`. Bericht im Tisch-Schema.

## Auftrag B — Opus: README-Text als Produktseite (Worktree, Branch `readme-showcase`)

Ergebnis: `README.md` neu geschnitten als Landingpage: Headline + ein Satz Nutzen · Hero mit den drei GIFs
(Dateinamen oben; solange die neuen GIFs fehlen, bleiben die bestehenden Dateien referenziert und die
Zielzeile steht als HTML-Kommentar daneben — `tests/test_readme.py` verlangt existierende Bilder) · „Was du
bekommst“ in drei Blöcken (Struktur + Ansichten + Stereo · 3D · Daten/Anki/Export) · Prompts zum Ausprobieren mit
den Molekülen oben · Tool-Tabelle, Installation, Profiles (16/23) und alle Zahlen bleiben wahr und
test-gedeckt. Englisch, keine erfundenen Behauptungen, keine Superlative ohne Beleg, keine Gedankenstriche.
Gate: `uv run pytest tests/test_readme.py` + `./test.sh` grün. Commit auf dem Branch, kein Push auf main.

## Auftrag C — Owner: Zusammenbau

1. Opus-Diff lesen, Zahlen gegen Code prüfen, Branch mergen. 2. Codex-GIFs ansehen (jeden Frame-Lauf einmal),
Dateinamen in README eintragen, HTML-Kommentare entfernen. 3. Codex-Design-Review einarbeiten, was trägt.
4. Gate + README-Render-Check, Commit, Push. 5. `plans/mcp-server.md` Punkt 9 abhaken mit Beleg.

## Abnahmekriterien (für alle drei)

- Jedes Bild/GIF stammt aus einem echten Lauf in Claude Desktop (Caption nennt Prompt und Klicks).
- Jede Zahl im README (Toolzahl, Panels, Profile) ist test-gedeckt (`tests/test_readme.py`, Taxonomie-Tests).
- Kein Satz verspricht etwas, das der Code nicht tut (Owner liest jede Behauptung gegen `server.py`/UI).

## Auftrag D — Opus: Design-Kritik Panel-UI und 3D (nur lesen, nur Bericht)

Ergebnis: `docs/design/panel-kritik-2026-11-07.md` mit (1) Ist-Aufnahme der Panel-Oberfläche je View
(MoleculeView, Molecule3DView, Database, Reaction, Mechanism, Spectrum, TLC, Titration, Species, Anki, Ambiguous,
Batch/Compare) — welche Knöpfe/Chips/Abschnitte, in welcher Reihenfolge, was doppelt oder uneinheitlich ist;
(2) Nielsen-Heuristiken 0–4 je View; (3) 3D: was die Kuhle eindrucksvoller und cleaner macht (Licht, Schatten,
Hintergrund dunkel/hell je Theme, Atomgrößen, Bindungsdarstellung, Drehgefühl, Auto-Rotation beim ersten
Einblenden, Vollbild-Umschalter), jeweils mit Aufwand S/M/L und Datei:Zeile; (4) ein Vorschlag für eine
einheitliche Panel-Grammatik (Kopf · Haupt-Fläche · Chips · Kernwerte · Aktionen) als ASCII-Skizze pro Panel-Typ.
Alle Befunde melden, nicht filtern. Kein Code ändern.

## Codex-Session (Jay 10:58)

Codex läuft nicht (Tisch: „kein herdr-Pane“). Start: `cc --codex chemdraw-mcp` (herdr-Workspace, rechte Pane)
— Jays Hand oder Owner per `cc-oeffnen`, sobald das Kontingent frei ist (11:45). Der Tisch-Faden liegt bereit.

## Panel-Umbau in Etappen (Jay 11:40: „Alle fünf bauen, 3D zuerst“)

Quelle je Etappe: `docs/design/panel-kritik-2026-11-07.md` (Top 5). Je Etappe ein frischer Opus-Arbeiter im
Worktree, TDD (DOM-Test erst rot), Gate `./test.sh` + `test:host` grün, Owner liest den Diff, merged, Desktop-Blick
mit Screenshot nach `docs/evidence/…/screenshots/` sobald der Desktop frei ist. Kein Push vom Arbeiter.

| Etappe | Inhalt (Rang im Bericht) | Dateien | Status |
|---|---|---|---|
| E1 | 3D-Look: Kuhle als eine Form je Theme ohne helles Quadrat, Farben/Schatten je Theme (1) · Bindungen in Atomfarben mit Tiefe, Doppel-/Dreifach-/Aromatenbindungen, Atomgrößen nach Element (2) | `components/Ball3DCanvas.jsx`, `styles.css`, Tests | **gemerged 12:06** (Opus `ec8bdee`, 12 Tests erst rot, DOM 116 grün nach Merge; Bundle neu gebaut; Gate rc=0 + test:host rc=0 auf main 12:12; Host-Bild `screenshots/24-host-3d-e1-kuhle.jpg` Owner gesehen und an Jay geschickt; Desktop-Blick zusammen mit E2) |
| E4 | Stille Fehler: Batch zeigt `failed` an, Scope im Dark Mode lesbar (5) | `App.jsx`, `styles.css` (38 Regeln), Tests | **gemerged 11:55** (Opus `361e1a4`, 2 Tests erst rot, DOM 104 grün; Hinweis: Spektrum/DC hängen nur am matplotlib-Leerzeichen `stroke: #000000`, Klassen `.spectrum-svg`/`.tlc-svg` als Ausnahme wären robuster — später) |
| E2 | Ansicht-Achse „2D · All H · Fischer · Haworth · 3D“ unter der Fläche, Spinner bei `aria-busy`, Stereo-Zeile/Gruppen in 3D ausgeblendet, sanfte Anfangsdrehung mit Stopp beim Anfassen, `onPointerCancel` (3) | `MoleculeView.jsx`, `Ball3DCanvas.jsx`, Tests, Host-E2E | **gemerged 12:38** (Opus `40bf3bf`, 9 Tests, DOM 125 grün; Gate rc=0 + test:host rc=0 (177 Prüfungen) auf main 12:48; neuer Knopf „2D“, Achse `div.seg.view-axis`; Nebenwirkung: Molecule3DView dreht beim Einblenden mit) |
| E3 | `PanelFooter`: Pfad links, Aktionen rechts, in allen Panels; Export PNG in 3D exportiert die Drehlage (Host-Prüfung Z. 432 bewusst umdrehen) (4); **dazu sichtbare Rückmeldung nach Export PNG** (Desktop-Handtest 08:39: Datei landet still in `~/ChemDraw-Output/png/`, keine Zwischenablage im Panel-iframe; README-Satz 12:22 umgedreht) | alle `*View.jsx`, neue Komponente, Host-E2E | nach E2 | **gemerged 13:28** (Opus `36f52b1`, 21+4 Tests, DOM 146 grün; 3D-Export löst CSS-Variablen auf, exportiertes PNG vom Arbeiter mit Farben gesehen; Gate rc=0 + test:host rc=0 (185 Prüfungen) auf main; **Desktop-Blick E1–E3 belegt 12:19** (`screenshots/26–28`, Owner gesehen). Server-Lücken: `lookup_molecule_data`/`generate_mechanism` ohne `files`, `save_png`-Fehlertext deutsch |

**Codex Design-Review README (11:14, Faden `20261107-111238-…`, eingearbeitet 11:58):** Quick start nach oben, ein Hero, 3D-Bild 440 px mit „Cropped screenshot“, drei Prompts + `<details>`, Galerie `<details>`, kürzere Einleitung. Offen: Tool-Tabelle zweispaltig (#8), für neue Aufnahmen gleiche Panelbreite/Theme/eng ums Panel (#5/#6). Codex konnte GitHub nicht live rendern (kein Browser) — Owner-Blick auf github.com steht aus.

**Jay 12:20 — Hero als Zweier-Split:** links Ansichten/Varianten durchklicken (`demo-views.gif`), rechts 3D-Drehung (`demo-3d.gif`) als Flaggschiffe; im README seit 12:22 als Tabelle mit den alten Bildern als Platzhalter.

## Auftrag A2 — Opus: GIF-Aufnahme im Playwright-Host (ersetzt die Desktop-Aufnahme, Jay „lass“ 11:20)

Skript `chemdraw_tool/ui/src/host/readme-gifs.mjs` (npm-Script `readme:gifs`), baut auf dem Host-Aufbau von
`host.e2e.mjs` auf (srcdoc-iframe, AppBridge, echter Server), Dark Theme, feste Panelbreite 600 px, nimmt mit
Playwright-Video auf und schneidet per ffmpeg (Palette, ≤ 800 px breit, ≤ 10 s, ≤ 3 MB) drei GIFs:
`demo-views.gif` (Thalidomid: Skelett → All H → Skelett → Show variants → (S) → Data), `demo-3d.gif` (Morphin: 3D-Chip → Modell →
Drehung per Pointer-Drag), `demo-molecule.gif` (Capsaicin: Hover über Gruppen → Data). Caption im README sagt dann
„recorded in the panel test host“ statt „in Claude Desktop“. Endgültiger Lauf erst nach E2/E3-Merge (Chip-Reihe ändert sich). **12:58: A2 gemerged** (Opus `b0b9f88`; GIFs 209 KB / 1,3 MB / 215 KB, Owner hat Kontaktbögen von views und 3d gesehen; Hero zeigt die zwei GIFs, Capsaicin unter „Data“). Nach E3: `npm --prefix chemdraw_tool/ui run readme:gifs` neu, dann Codex-Abgleich (Faden `20261107-114301-…`).

## Auftrag A3 — Hero-GIFs final (nach E3-Merge; Jay 13:10/13:14)

- **Ein Molekül für beide Hero-GIFs:** Thalidomid (1 offenes Stereozentrum → Show variants; 3D zeigt die zwei Ringe
  verdreht). Links: 2D → All H → Show variants → (S) → Data. Rechts: 3D-Chip → Modell → Drehung. Capsaicin bleibt
  unter „Data“.
- **Skalierung sauber:** beide GIFs exakt gleiche Maße (gleicher Panel-Ausschnitt, gleiche Höhe, z. B. 600×700),
  Hero als zwei `<img width="49%">` (seit 13:12), kein Scrollbalken bei 700 px Spaltenbreite (Playwright-Check bei
  Viewport 1100 und 1500).
- **Hell/Dunkel je GitHub-Modus:** je GIF eine helle und eine dunkle Fassung (`demo-views-light.gif`/`-dark.gif`,
  `demo-3d-light.gif`/`-dark.gif`), eingebunden per `<picture><source media="(prefers-color-scheme: dark)" srcset=…><img src=… light></picture>`;
  `readme-gifs.mjs` bekommt `--theme light|dark` (Dark heute über `data-theme="dark"`).
- Danach: Codex-Abgleich (Faden `20261107-114301-…`) mit Commit-SHA, Playwright-Screenshots hell/dunkel als Beleg.
- **gestartet 13:30** (Opus, Worktree; sechs GIFs light/dark, README auf `<picture>`).

**Release-Entscheid (Hinweis 13:12):** das vorbereitete `v0.9.0` auf `e2e1137` liefert das alte Panel (kleine Kuhle,
alte Chip-Reihe), das README zeigt das neue. Empfehlung: **ein** Release `0.9.0` vom aktuellen main nach E3-Merge,
Desktop-Blick und Welle-3-Haken 5 (Konnektor-Migration per `./install.sh`, Handshake 2 Konnektoren); CHANGELOG
`[Unreleased]` wandert in `[0.9.0]`. Klick bleibt Jays Hand.

## Auftrag C2 — Owner: README richtig clean (Jay 12:47, nach Release 0.9.0)

Reihenfolge (eine Hand in der Datei; erst nach A3-Merge):
1. [x] A3 mergen (13:05; Neuaufnahme auf E3-Stand 13:25, `024d6c1`, Hero 600×880): Hero `<picture>` hell/dunkel, gleiche Maße, Capsaicin-GIF unter Data; alte Dateinamen bleiben als Kopien.
2. [x] Alle HTML-TODO-Kommentare raus (13:10); Hero-Kommentar auf eine Zeile (Quelle: `readme:gifs`).
3. [x] Prompts/Tool-Tabelle (13:12: vier Prompts gekürzt, drei Dubletten raus): Tabelle bleibt vierspaltig (test-gedeckt, `| \`tool\` |`-Regex), Beispielprompts kürzen (max. ~60 Zeichen), keine Toolnamen in den drei Hero-Prompts.
4. [x] Texte (3D-Absatz auf Thalidomid; keine Gedankenstriche gefunden): keine Gedankenstriche, keine Superlative, einheitliche Backticks für Knopfnamen (`3D`, `All H`, `Data`), Aspirin/Ibuprofen nur noch in Galerie/Tests.
5. [x] Playwright-Screenshots hell/dunkel auf github.com (13:42, Owner gesehen: beide Hero-GIFs gleich hoch, kein Überlauf, Theme greift; Belege `docs/evidence/…/readme/github-hero-{light,dark}.jpg`) bei 700 px, 900 px und 1400 px Spaltenbreite (lokale HTML-Vorschau über `gh api /markdown`), ansehen: Hero gleich hoch, kein Überlauf, Galerie ausklappbar.
6. [~] Codex-Abgleich (Signal mit `024d6c1` um 13:30 im Faden `20261107-114301-…`) (Faden `20261107-114301-…`) mit Commit-SHA, Befunde einarbeiten.
7. [ ] Gate + CI grün, Push; README-Stand als Beleg in `docs/evidence/…/readme-2026-11-07.md` (Screenshots).

## Shorts aus den GIFs (Jay 13:05: „anschließend mit den GIFs die Shorts erstellen“)

Nach README-Abnahme: derselbe Host-Aufbau (`readme-gifs.mjs`) rendert die drei Szenen als 9:16-Clips (Viewport
1080×1920 skaliert, Panel mittig, mp4 per ffmpeg statt GIF, 1080p, 12–20 s, ohne Mauszeiger-Kreis oder mit größerem).
Schnitt, Text-Overlays, Musik und Veröffentlichung gehören nach `chemdraw-vermarktung` (dort liegt die Shorts-Planung);
Auftrag an Codex per `tisch` mit den fertigen Clips als Rohmaterial. Erst nach C2 Punkt 7.
