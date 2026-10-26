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
- [ ] Auffindbarkeit (Messung 26.10.2026, Bericht `docs/distribution/auffindbarkeit-2026-10-26.md`): punkpeye/awesome-mcp-servers neu einreichen — PR #7814 wurde am 25.07. nur wegen fehlendem Glama-Badge geschlossen; Glama listet das Repo inzwischen (Badge vorhanden, Listung ungeclaimt). Erst Glama claimen (**Jay:** Login), dann PR mit Badge (Helfer)

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
