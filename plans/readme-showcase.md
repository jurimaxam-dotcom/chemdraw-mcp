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
| D Design-Kritik Panel-UI + 3D (Jay 11:02: „3D cleaner und eindrucksvoller, Panel mit allen Tools besser sortiert“) | Opus 5.5 (Agent, Worktree, nur Bericht) | gestartet 11:03 | Bericht lesen, Vorschläge zu einem Bild für die iPad-Runde verdichten (`~/.claude/docs/designrunden-ipad.md`); **kein Code vor Jays Zustimmung** |

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
