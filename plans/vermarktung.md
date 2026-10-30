# Vermarktung: vom README bis zum Post (Jay, 19.10.2026)

Grundlage: `docs/distribution/vermarktung-recherche-2026-10.md` (Teardown + Evidenz),
Entwürfe seit Juli: `docs/distribution/posts-2026-07.md` (keiner davon gepostet).

**Leitsatz:** Claude automatisiert alles bis kurz vor dem Absenden: Produkt, Bilder,
Videos, Texte, Messung. Absenden ist Jays Klick, etwa 5 Minuten pro Kanal.
Vollautomatisches Posten ist ausgeschlossen, aus drei Gründen:
- Außenkommunikation ist eine Bremse in `CLAUDE.md`.
- r/chemistry verlangt eine Modmail-Freigabe, r/ClaudeAI mehr als 100 Karma und eine
  Erklärung. Bot-Werbung führt zur Sperre.
- Gekaufte oder organisierte Reichweite schadet laut He et al. langfristig.

## Nächste Session (25.10.2026, nach Abnahme 0.5.1)
1. [x] **Jay-Klick:** Social Preview hochladen (`vermarktung/social-preview.png`, Repo-Settings) — Social Preview hochgeladen 25.10.2026 über Chrome in Jays GitHub-Sitzung, in Repo-Settings sichtbar
2. [x] Helfer: Release-Notes v0.5.1 um ein echtes Kartenbild ergänzen — Karten-HTML aus der `.apkg` mit Playwright rendern, hell + Nachtmodus, kein erfundenes UI; `gh release upload` + Platzhalter im damaligen 0.5.1-Entwurf ersetzen (heute `vermarktung/posts-0.5.2.md`) — erledigt: Release v0.5.1 trägt anki-card-0.5.1-light.png und -dark.png als Assets, Bild-URLs in Zeile 1–2 des Live-Bodys, Platzhalter im damaligen 0.5.1-Entwurf ersetzt (Opus, Faden 20261025-090353)
3. [x] Helfer: Etappe 5 Traffic-Snapshot — `gh api` traffic views/clones/referrers → `vermarktung/traffic/<datum>.json`, launchd täglich — erledigt 25.10.: launchd de.jay.chemdraw-traffic täglich 09:00, Skript ~/.local/bin/chemdraw-traffic-snapshot.sh, Daten ~/.local/share/chemdraw-mcp/traffic/<datum>.json (außerhalb Documents, weil macOS Hintergrundprozessen Documents verweigert), vermarktung/traffic ist Symlink dorthin; Kickstart exit 0, Log ~/.claude/logs/chemdraw-traffic.log; erste Datei 2026-10-25.json: Werte sind rollierende 14-Tage-Aggregate (Codex, Faden 20261025-090414, Bericht vermarktung/traffic-snapshot-bericht-2026-10-25.md)
4. [x] Helfer: Anthropic-Plugin-Portal-Bedingungen in der Primärdoku prüfen — geprüft 25.10., Primärdoku live: Directory nimmt lokale MCPB-Server nicht mehr an (Zitat »the directory no longer accepts local MCP servers packaged as desktop extensions (MCPB)«, claude.com/docs/connectors/building/submission.md); Einzel-Connector muss remote über HTTPS laufen; Alternative Plugin-Bundle aus GitHub (.claude-plugin/plugin.json), läuft aber nur in Cowork und Claude Code, Chat/Desktop-Chat ignoriert lokale Server (claude.com/docs/plugins/platform-support.md). Details im Codex-Bericht.

## Nächste Session (nach 25.10.2026, Weg C)
1. [ ] **Jay:** später für den Short: Aufnahme-Recht Terminal + YouTube-Kanal; keine Bedingung für den ersten Text-/Bild-Post
2. [x] Helfer: Anki-Karte transparentes Struktur-PNG (Kasten-Befund), danach Release-Bilder neu rendern und Assets ersetzen — 25.10.: Fix f09e707, Release v0.5.2 (01f20e1) mit anki-card-0.5.2-{light,dark}.png, publish.yml Run 40182594742 grün: PyPI 0.5.2, chemdraw-mcp-0.5.2.mcpb, Registry isLatest; v0.5.1 unverändert
3. [x] Helfer: Short neu gerendert (25.10.): `vermarktung/out/short-2026-10-25/chemdraw-short.mp4`, 1080×1920, 16,63 s; Remotion-Cursor, 1,4 s Wartezeitschnitt, Audio-Slot mit Blenden fertig; ohne Ton, bis Jay `vermarktung/video/public/musik.mp3` ablegt (Codex, Faden 20261025-101217).
4. [x] Helfer: Post-Entwürfe auf 0.5.2 umgestellt: `vermarktung/posts-0.5.2.md`; Release, PyPI und Karten-Assets geprüft. Jays Klickfolge: `vermarktung/launch-checkliste.md`.
5. [ ] **Jay:** erster Post mit Faden 1 nach den 0.5.2-Entwürfen: Show HN am Di 27.10.2026 um 15:00 MEZ (14:00 UTC), danach X/Bluesky an einem anderen Tag. Faden 2 Word und Short sind keine Launch-Bedingung.

Entscheidung Jay, 25.10.2026: Vertrieb startet mit Faden 1 allein. Faden 2 Word und
Faden 3 folgen nach dem ersten Post, Stück für Stück; die bisherige Bedingung
„Faden 1 + 2“ entfällt, damit offene Erweiterungen den Start nicht verschieben.

## Etappe 1: Feinschliff Produkt → Release 0.5.0
- [ ] `lookup-data-sheet` (12/13): mit einem Stub prüfen, der echten Datenblatt-Text liefert
- [ ] Bundle frisch installieren und Smoke-Test: Koffein → Datenblatt → PNG-Export — geht erst nach dem Publish (Bundle pinnt `==0.5.0` von PyPI); bis dahin `test:host` grün (20.10.) — jetzt möglich, 0.5.1 auf PyPI (25.10.)
- [x] Release 0.5.0 veröffentlicht (21.10., Jays Auftrag „release du“): PyPI, `.mcpb`, Registry grün; PyPI-sdist/Wheel/Bundle nachgeprüft ohne private Inhalte
- [x] Repo-Audit 20.10.: sdist-Erlaubnisliste, private Produktdoku nach `leben`, alte GIFs mit `/Users/tom` ersetzt, Panel komplett englisch, Layoutfix Vergleich (Codex + Claude p3 gegengeprüft)

## Sicherheitsscan 29.10.2026 — offene Haken (Bericht `docs/evidence/sicherheitsscan-2026-10-29.md`)
- [ ] **Jay:** B4 Installationsweg des Bundles entscheiden. Heute lädt `mcpb/server/run.sh` uv per `curl | sh` ohne Rückfrage und löst alle Abhängigkeiten außer `chemdraw-mcp` frisch von PyPI auf (`uv.lock` greift nicht; ebenso `install.sh`). Optionen, Empfehlung zuerst:
  (a) Release-Job erzeugt `uv export --format requirements-txt --hashes` aus `uv.lock`, das Bundle installiert mit `--constraints` bzw. `--require-hashes`; fehlt uv, bricht `run.sh` mit klarer Meldung ab statt still zu installieren — sicherste Variante, Erststart braucht vorinstalliertes uv.
  (b) wie (a), aber uv in fester Version per SHA-256 statt `curl | sh` nachladen — kein Komfortverlust, etwas mehr Pflege beim uv-Update.
  (c) so lassen — kein Aufwand, Lieferkette bleibt offen.
- [ ] **Jay:** PyPI-Publish absichern (B2/F1): auf pypi.org → chemdraw-mcp → Publishing beim Trusted Publisher Environment `pypi` eintragen. GitHub-Teil ERLEDIGT 30.10.2026: Environment `pypi` hat Required reviewer jurimaxam-dotcom, Ruleset „main schützen“ (id 26189605) sperrt Force-Push und Löschen. Workflow nutzt `environment: pypi` (f910a4d) → jedes Release wartet schon jetzt auf deinen Klick „Approve“; der PyPI-Eintrag bindet den Publisher zusätzlich an genau dieses Environment.
- [ ] B1-Rest: `export_anki_deck(deliver="ankiconnect")` importiert ohne Dialog; Vorschlag aus dem Bericht: nur nach Klick im Panel. Kartentext ist seit 6004d11 escaped, Risiko damit klein.

## Etappe 2: Landingpage
- [x] README-Oberkante in dieser Reihenfolge (4ae09b6):
  - Einzeiler
  - Demo-GIF
  - drei Nutzen-Punkte
  - Download `.mcpb` und eine `uvx`-Zeile
  - Gegenüberstellung „Without / With“
  - Profile weiter nach unten
- [x] `gh repo edit`: Homepage auf `/releases/latest`, Topics `claude-desktop` `mcpb` `mcp-apps`
- [x] Social Preview vorbereitet (25.10.2026): `vermarktung/social-preview.png`, 1280×640 PNG, Ibuprofen aus vorhandenem SVG, visuell geprüft
- [x] **Jay:** Social Preview hochladen (1280×640, liefert Claude als PNG) — hochgeladen 25.10.2026 über Chrome in Jays GitHub-Sitzung, in Repo-Settings sichtbar

## Etappe 3: Content-Fabrik (automatisch je Release)
- [x] `scripts/demo-video.sh` (505ba8d): Host-Nachbau mit Playwright-`recordVideo` und ffmpeg, fünf Szenen. Ausgaben:
  - README-GIF
  - 9:16-Short mit 15–30 s für YouTube Shorts, TikTok und Reels
  - quadratische Fassung für Reddit und Bluesky
- [x] Post-Entwürfe für 0.5.2 aktualisiert (25.10.2026): `vermarktung/posts-0.5.2.md` — YouTube DE/EN, X/Bluesky (4 Posts), Show HN; 0.5.2 auf PyPI und Release-Bilder bestätigt, Faden 1 mit 0.5.1 durch Jay abgenommen; echte Desktop-/Anki-Gegenprobe mit 0.5.2 noch [prüfen]. Entwürfe, keine automatisierte Content-Pipeline.
- [x] Release-Notes mit Bild — v0.5.1 trägt `anki-card-0.5.1-light.png` und `-dark.png` (Opus, Faden 20261025-090353)
- [x] Release-Notes-Text für 0.5.2 mit echten Release-Bildern und Desktop-Neustart-Hinweis aktualisiert (25.10.2026), in `vermarktung/posts-0.5.2.md`; entspricht dem veröffentlichten Fix für transparente Kartenstrukturen.

## Danach: Features einzeln zurück ins Standardprofil (nach Launch, je Minor-Release, je Routing-Fall + Demo-GIF)
- [x] Anki-Export zurück im Standardprofil — erledigt mit 0.5.1 (25.10.)
- [ ] Nach dem ersten Post: 0.6.0 mit 3D-Ansicht → danach Mechanismus → danach Laborgrafiken, jeweils ein eigenes Minor-Release. Bestätigt durch Jay am 25.10.2026; keine Launch-Bedingung.

## Stand 21.10.2026 (Übergabe für die nächste Session)
- [x] Release 0.5.1 veröffentlicht 25.10.: PyPI 0.5.1, Registry isLatest, Bundle 3265 B (Run 40137831565); Handshake gegen PyPI-Version 7 Tools / 6 Panel
- [x] Panel in Desktop mit 0.5.0 bestätigt (Jays Screenshot). Die ersten Fehlschläge lagen daran, dass Desktop nach der `.mcpb`-Installation nicht neu gestartet war. Gegenprobe mit 0.4.8 zeigte dasselbe Bild.
- [x] README/Release-Notes: Satz „nach der Installation Claude Desktop einmal neu starten“ — README im Bundle-Abschnitt ergänzt; veröffentlichte Release-Notes v0.5.1 per `gh release view` bestätigt (25.10.2026).
- [x] Erstes Short gerendert; liegt seit 21.10. nur lokal in `vermarktung/` (Skript `vermarktung/demo-short.sh`, Montage `vermarktung/video/`, 9 Tests grün). Plan + `docs/distribution/` ebenfalls lokal, per `.git/info/exclude` ausgeschlossen
- [ ] Alte Fassungen aus der öffentlichen Git-Historie entfernen? (Force-Push, **Jay:** entscheiden; Codex hat die Historie schon gescannt)
- [ ] **Jay:** Gestaltungsrückmeldung zum Short (Aufhänger-Text, dunkles Schema, Tempo)
- [x] Short technisch fertig (25.10.): echter Remotion-Cursor (`cursor.ts`), PubChem-Pause von 1,99 auf ca. 0,6 s gekürzt (42 Quellframes ausgelassen); Musik-Prop mit Lautstärke + Ein-/Ausblenden, Audio-Test-Render bestätigt. Endfassung ohne Ton: `vermarktung/video/public/musik.mp3` fehlt (YouTube Audio Library: Jay). 15 Tests in `vermarktung/video` grün, weiterhin separat vom Gate; `./test.sh` Exit 0. MP4 + geprüfte `check-*s.png`: `vermarktung/out/short-2026-10-25/`.
- [ ] Szenen Reaktion und Anki-Import: Anki nur per Cap (`brew install --cask cap`, Deeplink-Steuerung, 29 $/Jahr bei kommerzieller Nutzung) + osascript; Recherche-Verdikt: Remotion + Kamera aus ashrafchowdury/programatic-demo (MIT), Screen Studio verworfen
- [x] Anthropic-Abgleich geprüft (25.10.2026): `anthropic_sync.py --check` meldet 0 neu / 0 geändert / 0 weg; inhaltliche Auswertung vom 24.10. in `docs/anthropic/abgleich.md` weiter gültig, kein neuer Anpassungsbedarf; Stand per `--update` übernommen.

## Etappe 3b: hochwertige Videos (Jay 19.10.: Reddit raus, Shorts und Videos rein)
- [ ] Remotion (React → MP4) als Schnittwerkzeug: eine Quelle, Formate 16:9 und 9:16;
  Moleküle aus unserem eigenen SVG-Renderer animieren
- [ ] Echte Aufnahmen aus Claude Desktop (nie KI-generierte Oberfläche, die würde täuschen)
- [ ] Flow (Google AI Pro) nur für Intro-B-Roll und Musik (Flow Music)
- [x] Stimme: keine — Untertitel-Text + Flow-Musik (Jay 19.10.2026)
- [ ] **Jay:** Bildschirmaufnahme-Recht für das Terminal freigeben, YouTube-Kanal anlegen

## Etappe 4: Verbreitung (Jays Klick, 2 Posts pro Woche, nie am selben Tag)
- [ ] YouTube Short (eigener Kanal; der Upload ist Jays Klick)
- [ ] Show HN: Vorschlag Di 27.10.2026, 15:00 MEZ (14:00 UTC); Planfenster Di–Do, 12–17 UTC = 13–18 Uhr MEZ nach der Zeitumstellung am 25.10. (im Sommer 14–19 Uhr MESZ). Kein belegtes Reichweitenversprechen.
- [ ] Bluesky/X-Thread mit Bildern, RDKit erwähnen
- [x] **Jay:** Entscheidung Directory: (a) Plugin-Bundle für Cowork/Code einreichen, (b) Remote-HTTPS-Variante des Servers bauen, (c) Directory auslassen und bei GitHub/PyPI/.mcpb bleiben — Jay 25.10.2026: Weg C, Directory auslassen; Panel im Desktop-Chat ist das Kernmerkmal, nur Weg C behält es kostenlos. Remote-HTTPS bleibt spätere Option, falls Nutzer die App-Suche vermissen. Diagramm: https://claude.ai/artifact/GCRB45BTEVHYXVfZEUsHo9
- [ ] Etappe-5-Hinweis: Traffic-Zahlen sind 14-Tage-Aggregate, Post-Wirkung nur über die tägliche UTC-Zeitreihe in views/clones ablesbar
- [x] Glama Build & Release: 26.10. 09:52 Build-Test 01a17768 grün (1 min 17 s, Build steps mit libxrender1 libxext6 vor `uv sync`, Container antwortet auf tools/list), Release 0.1.0 „Latest“ 09:55, Auto-Release bei GitHub-Releases an; Übersicht zeigt Deploy + Try in Browser (Claude, Chrome)
- [x] Glama Related Servers 26.10.: ChemMCP (OSU-NLP-Group), pubchem-mcp-server (cyanheads), ChemGlyph; ChatMol ist nicht auf Glama gelistet, ChemGlyph statt dessen. Try in Browser: Sandbox verbunden, 7 Tools, `generate_molecule` „caffeine“ zeichnet im Panel (C8H10N4O2, CAS 58-08-2), Data-Knopf lädt PubChem CID 2519. Discovery score danach 67 % (vorher 33 %); offen: Coherence/TDQS rechnet Glama noch
- [ ] Glama-Kategorien umstellen (Messung 26.10.: „Research & Data“ bei 13 von 17 Chemie-Treffern, ChemMCP 74⭐ trägt sie): Biology & Medicine → Research & Data; Education & Learning Tools + Data Visualization bleiben. Beschreibung auf die 7 MVP-Tools kürzen (nennt noch Spektren/Titration/3D). **Jay:** „stell um“
- [ ] **Jay:** `bash vermarktung/klicks.sh` ausführen (PR, Issues, Glama, mcpservers.org in einem Lauf)
- [ ] **Jay:** Glama claimen (https://glama.ai/mcp/servers/jurimaxam-dotcom/chemdraw-mcp → Claim), dann PR-Befehl aus `vermarktung/punkpeye-eintrag.md` freigeben — Branch `add-chemdraw-mcp-glama` liegt fertig im Fork-Klon `~/GitHub/awesome-mcp-servers` (3c691e44). Ungeprüft: ob Glama für die Checks ein Dockerfile verlangt (Messung 26.10.2026, `docs/distribution/auffindbarkeit-2026-10-26.md`)
- [ ] **Jay:** mcpservers.org/submit ausfüllen (wong2-Liste nimmt nur noch das Formular; mcpservers.org steht in Bing auf Platz 1 und 7 für „chemistry mcp server“) – 5 min
- [ ] **Jay:** 3 Issues aus `vermarktung/issues-entwuerfe.md` anlegen, Studentenstatus im Education-Dashboard prüfen, Repo bei GitHub Community Exchange als „Collaborate“ einreichen (CONTRIBUTING.md ist da, 4c1c59a)

## Etappe 5: Messen
- [x] Täglicher Snapshot von Traffic und Referrern in eine Datei. GitHub behält nur 14 Tage;
  ohne Snapshot gehen ältere Messwerte verloren; auch mit Snapshots ist die Wirkung einzelner Posts nur näherungsweise sichtbar. — erledigt 25.10.: launchd de.jay.chemdraw-traffic täglich 09:00, Skript ~/.local/bin/chemdraw-traffic-snapshot.sh, Daten ~/.local/share/chemdraw-mcp/traffic/<datum>.json (außerhalb Documents, weil macOS Hintergrundprozessen Documents verweigert), vermarktung/traffic ist Symlink dorthin; Kickstart exit 0, Log ~/.claude/logs/chemdraw-traffic.log; erste Datei 2026-10-25.json: Werte sind rollierende 14-Tage-Aggregate (Codex, Faden 20261025-090414, Bericht vermarktung/traffic-snapshot-bericht-2026-10-25.md)

- [x] Sterne-Zeitpunkte und Profile erfassen (26.10.): Quellfassung `scripts/traffic-snapshot.sh`, installierte identische Kopie `~/.local/bin/chemdraw-traffic-snapshot.sh` (alte Fassung als `.bak-20261026`). Stargazer mit `Accept: application/vnd.github.star+json`, `per_page=100` und `--paginate`; Login, starred_at, created_at, followers, public_repos, location, company, bio. Rohdaten ausschließlich in `~/.local/share/chemdraw-mcp/traffic/`, im Projekt nur Symlink. Traffic wird vor dem Zusatzabruf atomar gesichert; Stern- und Profilfehler werden markiert und verlieren die Traffic-Messung nicht.
- [x] Echten launchd-Lauf vor dem Show HN nachgewiesen: 26.10. 08:15:36–08:15:50 MEZ, `last exit code = 0`, `2026-10-26.json` enthält 24 Sterne / 0 Profilfehler, Traffic-Messzeit `2026-10-26T07:15:39Z`. Beim ersten Prüfen um 08:11 war der 09:00-Termin noch nicht fällig; kein aktueller Scheduler-Defekt belegt. Täglich 09:00 bleibt unverändert konfiguriert.
- [x] Auswertung: `uv run python scripts/sterne-auswertung.py --output vermarktung/sterne-bericht-2026-10-26.md` erzeugt die Tabelle für alle 24 Sterne. Keine Bio-Texte im Bericht. GitHub liefert keinen Referrer pro Stern: 14-Tage-Nettoänderungen sind keine Tagesbesucher; Top-10-Abgänge haben unbekannten Bestand. Ein fehlendes Zeitintervall bleibt unbekannt. Profilregeln markieren Hinweise, keine belegten unechten Konten. Historische Sterne vor Messbeginn bleiben ohne Herkunftsaussage.
- [x] Prüfnachweis: `uv run pytest -q tests/test_traffic_snapshot.py tests/test_sterne_auswertung.py` erst 5 rot (fehlende Implementierung), dann 5 grün; `./test.sh` vollständig grün. Testdaten prüfen mehrere API-Seiten, Ausfall der Sternliste, einzelnen Profilfehler, negative/entfallene Referrer, fehlende Zeitabdeckung und fehlende Bio-Texte im Bericht.
- [ ] Nach dem regulären 09:00-Lauf am 27.10. vor dem Show HN (15:00 MEZ) Log/Datei prüfen; nach dem Post Bericht neu erzeugen. Kickstarts sind als echte Hintergrund-Vorabproben belegt, ein zukünftiger Kalenderlauf noch nicht.

Ablage-Präzisierung (Tisch-Antworten 26.10., #3/#6): Dieser Plan wird jetzt als gemeinsamer Repo-Stand versioniert (einschließlich Opus' Etappe-4-Eintrag); dies ersetzt die ältere lokale Plan-Regel am Dateiende. Rohdaten und Berichte in `vermarktung/` bleiben lokal und werden nicht committet.

## Workflow-Videos (Jay 21.10.: durchgehende Fäden, Plan plans/workflows.md)
- [ ] Je Faden eine echte Aufnahme aus Claude Desktop (Chatseite sichtbar: tippen → Panel → Anki/Word) → Short in `vermarktung/`
- [~] Launch erst mit Faden 1 + 2 — gestrichen durch Jay am 25.10.2026: Faden 1 reicht für den ersten Post; Word und weitere Features folgen nach Launch. Workflow-Videos werden später ergänzt.

## Prüfung 25.10.2026: Short und Entwürfe

- [x] Short-Bestand und Restaufwand geprüft: `vermarktung/short-upload-check-2026-10-25.md` (Musik, Cursor, Wartezeitschnitt, Anki-Szene, Exportkontrolle); 9 lokale Montage-Tests grün.
- [~] MP4 vom 21.10. wiederfinden — überholt am 25.10.: neuer Render liegt in `vermarktung/out/short-2026-10-25/chemdraw-short.mp4` (siehe Short-Bericht oben).
- [ ] **Jay:** 0.5.2 in Desktop/Anki kurz gegen die Release-Bilder prüfen; Faden 1 mit 0.5.1 bereits abgenommen. Für den späteren Short den tatsächlich gezeigten Ablauf kontrollieren. Text-/Bild-Launch wartet nicht auf ein neues Video.
- [x] Anki-Karte: Struktur-PNG liegt als schwarzer (Nacht) bzw. weißer (hell) Kasten auf dem Kartenhintergrund; Fix = transparentes PNG im Export (anki_export/AddToAnkiButton), sichtbar in vermarktung/release-bild/*.png — 25.10.: `render_molecule_png`/`render_reaction_png(transparent=True)` nur aus `anki_export`, Medien-PNG RGBA mit Alpha-0-Ecke (`tests/test_anki_export.py`), Datei-Export bleibt weiß

Vermarktung und dieser Plan bleiben per `.git/info/exclude` ausschließlich lokal;
kein Commit, kein Upload dieser lokalen Dateien. Launch mit Faden 1 allein (Jay, 25.10.2026);
Faden 2/3 und Feature-Rückkehr folgen nach dem ersten Post. Nur `plans/workflows.md`
ist getrackt und wird für diesen Auftrag committet (Tisch-Antwort #3).

## Shorts je Workflow (Jay 26.10.2026 23:55: „zuerst die Shorts nochmal sauber, zu jedem Workflow ein Short“)
Nur Entwurf: kein Rendern, Desktop nicht anfassen, solange Codex dort abnimmt. Aufnahme-Pipeline
(`aufnahme-desktop.sh`, `ax-claude.swift`) gehört Codex, Montage `vermarktung/video/` (Remotion, Komposition
`DesktopWorkflow`). Alle Shorts: 9:16, 1080×1920, 30 fps, 15–30 s, echte Desktop-Pixel, englischer Prompt.

### Vorgehen (Jay 27.10.2026 00:00): „Erst ein Test-Short für den Ablauf, wir brauchen ein Schema, nach dem dann alle erstellt werden“
- [x] **Schema** festlegen und in `vermarktung/video/SCHEMA.md` + Props-Typ gießen: feste Abschnitte mit Dauer
      (Aufhänger · Prompt tippen · Panel erscheint · Beats · Schluss-Bild · Abspann), Schrift, Farben, Musik, Ausschnitt,
      Aufnahme-Checkliste (Sprache EN, Version 0.6.0, kein Name im Bild). Ein Short = nur ein Datensatz.
      — 27.10.: `SCHEMA.md` + `ShortDaten`/`pruefeShort` (`src/lib/schema.ts`), Beats `src/lib/beats.ts`, Datensatz
      `src/shorts/s1-anki.ts` → Komposition `Schema-S1`; `npm --prefix vermarktung/video test` 30/30 (neu 10, vorher rot);
      v2-Schnitt + Kamera mit altem Code als Orakel identisch, nur der Aufhänger wächst mit der Wortzahl.
- [ ] **Test-Short** nach dem Schema (gerendert 27.10.: `vermarktung/out/test-short-schema/s1-anki.mp4`, 24,53 s, 1080×1920/30, stumm, + 4 Standbilder; offen: Jays Sichtprüfung): S1 Anki (fertige Aufnahme reicht für den Ablauf-Test) → Jays Sichtprüfung → Schema
      anpassen, bis es passt.
- [ ] Erst danach S2–S7 als Datensätze aufnehmen und rendern.

### a) Workflows, die in 0.6.0 laufen (Beleg)
| # | Workflow | Beleg |
|---|---|---|
| W1 | Name → Panel → Gruppen-Hover | Desktop-Aufnahme 25.10. (short-desktop-v2), Jay-Abnahme 0.5.1 |
| W2 | → Add to Anki → Karte in Anki | Jay-Abnahme 0.5.1 (24./25.10.), Kartenbild 0.5.2 |
| W3 | → Data (Datenblatt, GHS nach Quelle) | test:host (Methylphenidat), Glama-Sandbox (Koffein, CID 2519); **Desktop-Handtest offen** |
| W4 | → Export PNG | Codex-Desktop-Abnahme Etappe 4 (Faden 20261026-182553) |
| W5 | Familienname → Isomer-Auswahl („xylene“) | test:host + Gate; **Desktop ungeprüft** |
| W6 | Stereo-Hinweis → Show variants → (S) mit Keil | Codex-Desktop-Abnahme 5 (Ibuprofen) |
| W7 | Reaktion → Bilanz-Badge → Apply coefficients | Codex-Desktop-Abnahme 5 (Knallgas) |
| W8 | Zucker/Aminosäure → Fischer · Haworth · All H | Codex-Desktop-Abnahme Etappe 4 (Glucose, L-Alanin) |
Nicht als Short: `compare_molecules`/`batch_generate` (kein Desktop-Beleg), Chat-Weg Anki-Deck (kein Panel-Moment).
W3 und W5 erst nach einer Desktop-Probe drehen.

### b) Drehbücher (Prompt · Klicks · Aufhänger · Schluss-Bild)
- [ ] **S1 Anki (W1+W2, ersetzt short-desktop-v2)** · `draw caffeine` · Hover 2 Chips je 1,2 s → Add to Anki → Importieren
      → Karte in Anki umdrehen (vorn Struktur, hinten Name/Formel/CAS) · Aufhänger „From a name to a flashcard in 10 seconds“
      · Schluss: fertige Karte im Nachtmodus, dann Abspann. ~22 s
- [ ] **S2 Datenblatt (W3)** · `draw methylphenidate` · Data → langsamer Scroll über GHS-Block → zurück Structure ·
      Aufhänger „Structure and safety data, same panel“ · Schluss: GHS-Piktogramme + CAS. ~18 s
- [ ] **S3 Export (W4)** · `draw ibuprofen` · Export PNG → Finder-Fenster mit der Datei (Quick Look) · Aufhänger
      „Publication-style structures, offline“ · Schluss: PNG in Quick Look, weißer Grund. ~15 s
- [ ] **S4 Isomere (W5)** · `draw xylene` · Auswahl mit 3 Bildchen → Klick para → Struktur · Aufhänger „Xylene is three
      molecules. It asks which.“ · Schluss: p-Xylol gezeichnet, Rückweg-Leiste sichtbar. ~16 s
- [ ] **S5 Stereo (W6)** · `draw ibuprofen` · Stereo-Hinweis hovern (Zentrum leuchtet) → Show variants → (S) ·
      Aufhänger „One stereocenter, two drugs“ · Schluss: (S)-Ibuprofen mit Keil + Label. ~18 s
- [ ] **S6 Reaktion (W7)** · `draw the reaction H2 + O2 -> H2O as typed, don't balance it` (sonst setzt Sonnet die
      Koeffizienten selbst, Befund Abnahme 5) · Badge „not balanced“ → Apply coefficients · Aufhänger „It checks your
      equation“ · Schluss: 2 H₂ + O₂ → 2 H₂O mit grünem „balanced“. ~16 s
- [ ] **S7 Projektionen (W8)** · `draw beta-D-glucose` · Haworth → All H → Structure · Aufhänger „Skeletal, Haworth,
      every H — one click each“ · Schluss: Haworth-Ring. ~18 s (nicht „show the Haworth projection“ — Desktop
      antwortet dann mit seinem eigenen Visualizer)

### c) Gemeinsame Fixes vor dem nächsten Dreh (Befund an short-desktop-v2 + short-2026-10-25)
- [~] **Jay 27.10.: Name darf im Bild stehen** (kein Blocker mehr). War: **Persönlicher Name im Bild:** prompt.png zeigt „Guten Abend, Juri“ (Desktop-Begrüßung) → vor dem Tippen in einen
      bestehenden leeren Chat wechseln oder Begrüßung aus dem Ausschnitt nehmen. Blocker für jeden Upload.
- [ ] **Sprachmix:** Desktop-UI deutsch („Guten Abend“, Anki „Importieren“), Panel englisch, Titel „Aspirin
      (Acetylsalicylsäure)“ → Desktop- und Anki-Sprache für die Aufnahme auf Englisch, oder Ausschnitt ohne Host-Text.
- [ ] **Version:** Aufnahme zeigt Extension 0.5.1 → vor dem Dreh Extension 0.6.0 installieren, Manifest-Version in
      `aufnahme-desktop.sh` als Pflicht prüfen (Abbruch bei ≠ Release), Bundle-Hash wie im Memo „stale Installation“.
- [ ] **Anki-Schluss leer:** anki.png ist ein angeschnittener Importdialog („…ort“, Schalter, kein Kontext); keine Karte
      zu sehen → Import bestätigen und die Karte zeigen, Dialog nicht als Schluss-Bild.
- [ ] **Überlagerung im Panel:** hover.png zeigt den Desktop-Scroll-Pfeil (↓) über dem Gruppen-Detail → Chat so scrollen,
      dass das Panel unten frei endet, oder Ausschnitt oberhalb enden lassen.
- [~] **Jay 27.10.: Test-Short und erste Fassung ohne Ton.** War: **Kein Ton:** `vermarktung/video/public/` ist leer, `musik.mp3` fehlt seit 25.10. → **Jay:** einen Track aus der
      YouTube Audio Library wählen (gilt dann für alle Shorts).
- [x] **Aufhänger je Short** (27.10.: `hook`/`prompt` im Datensatz; Remotion-Hälfte erledigt): `HOOK_TEXT`/`PROMPT_TEXT` sind Konstanten in `timeline.ts` („Still drawing molecules by
      hand?“, „draw aspirin“) → als Props je Short, damit S1–S7 eine Komposition teilen.
- [x] **Marks je Short** (27.10.: Beat-Liste + Adapter `beatsFromMarks`; offen Codex-Hälfte: `aufnahme-desktop.sh` schreibt `beats.json`): `DesktopWorkflow`-Marks sind auf den Aspirin-Ablauf (3 Hover + Anki) zugeschnitten → generische
      Beat-Liste (Klick/Hover/Halten) aus dem Aufnahme-Log statt fester Feldnamen; zwei Teilaufnahmen + Normalisierung
      (v2-Bericht) vermeiden, indem das Fenster vorher richtig steht.
- [ ] Alt-Short `short-2026-10-25` (Host-Nachbau, gesetzte Eingabezeile) nicht mehr verwenden — ersetzt durch echte
      Desktop-Aufnahmen; **Jay:** Gestaltungsrückmeldung zum Short (oben) gilt dann für S1.
Reihenfolge: c) Fixes (Codex Pipeline, Claude Remotion-Props) → S1 drehen → Jays Sichtprüfung → S5, S6, S7, S3 → S2/S4
nach Desktop-Probe.
