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

## Etappe 1: Feinschliff Produkt → Release 0.5.0
- [ ] `lookup-data-sheet` (12/13): mit einem Stub prüfen, der echten Datenblatt-Text liefert
- [ ] Bundle frisch installieren und Smoke-Test: Koffein → Datenblatt → PNG-Export — geht erst nach dem Publish (Bundle pinnt `==0.5.0` von PyPI); bis dahin `test:host` grün (20.10.)
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
- [ ] **Jay:** Social Preview hochladen (1280×640, liefert Claude als PNG)

## Etappe 3: Content-Fabrik (automatisch je Release)
- [x] `scripts/demo-video.sh` (505ba8d): Host-Nachbau mit Playwright-`recordVideo` und ffmpeg, fünf Szenen. Ausgaben:
  - README-GIF
  - 9:16-Short mit 15–30 s für YouTube Shorts, TikTok und Reels
  - quadratische Fassung für Reddit und Bluesky
- [ ] Post-Entwürfe je Release aus `CHANGELOG.md` und Bildern, je Kanal nach dessen Regeln
- [ ] Release-Notes mit Bild

## Danach: Features einzeln zurück ins Standardprofil (je Minor-Release, je Routing-Fall + Demo-GIF)
- [ ] 0.6.0: 3D-Ansicht · danach Mechanismus · Anki-Export · Laborgrafiken

## Stand 21.10.2026 (Übergabe für die nächste Session)
- [x] Panel in Desktop mit 0.5.0 bestätigt (Jays Screenshot). Die ersten Fehlschläge lagen daran, dass Desktop nach der `.mcpb`-Installation nicht neu gestartet war. Gegenprobe mit 0.4.8 zeigte dasselbe Bild.
- [ ] README/Release-Notes: Satz „nach der Installation Claude Desktop einmal neu starten“
- [ ] Erstes Short gerendert (Branch `worktree-agent-a89d4c26da6a9d6c2`, 5 Commits, nicht gemergt; Skript `scripts/demo-short.sh`, Remotion in `chemdraw_tool/ui/video/`). Merge mit Skill `branch-abschliessen`
- [ ] **Jay:** Gestaltungsrückmeldung zum Short (Aufhänger-Text, dunkles Schema, Tempo)
- [ ] Short fertig: Musik (YouTube Audio Library), echter Cursor in Remotion (`cursor.ts`), PubChem-Wartezeit (~2 s) kürzen, Video-Tests in `ui/video` (9, `npm test`) noch nicht im Gate
- [ ] Szenen Reaktion und Anki-Import: Anki nur per Cap (`brew install --cask cap`, Deeplink-Steuerung, 29 $/Jahr bei kommerzieller Nutzung) + osascript; Recherche-Verdikt: Remotion + Kamera aus ashrafchowdury/programatic-demo (MIT), Screen Studio verworfen
- [ ] `anthropic_sync.py --check` meldet geänderte MCP-Apps-Seiten (troubleshooting, getting-started, mcpb …): lesen, `docs/anthropic/abgleich.md` anpassen

## Etappe 3b: hochwertige Videos (Jay 19.10.: Reddit raus, Shorts und Videos rein)
- [ ] Remotion (React → MP4) als Schnittwerkzeug: eine Quelle, Formate 16:9 und 9:16;
  Moleküle aus unserem eigenen SVG-Renderer animieren
- [ ] Echte Aufnahmen aus Claude Desktop (nie KI-generierte Oberfläche, die würde täuschen)
- [ ] Flow (Google AI Pro) nur für Intro-B-Roll und Musik (Flow Music)
- [x] Stimme: keine — Untertitel-Text + Flow-Musik (Jay 19.10.2026)
- [ ] **Jay:** Bildschirmaufnahme-Recht für das Terminal freigeben, YouTube-Kanal anlegen

## Etappe 4: Verbreitung (Jays Klick, 2 Posts pro Woche, nie am selben Tag)
- [ ] YouTube Short (eigener Kanal; der Upload ist Jays Klick)
- [ ] Show HN: Di–Do, 12–17 UTC (14–19 Uhr MESZ), mit Demo
- [ ] Bluesky/X-Thread mit Bildern, RDKit erwähnen
- [ ] Anthropic-Plugin-Portal (seit 25.09.2026): Bedingungen in der Primärdoku prüfen

## Etappe 5: Messen
- [ ] Täglicher Snapshot von Traffic und Referrern in eine Datei. GitHub behält nur 14 Tage;
  ohne Snapshot lässt sich nicht trennen, welcher Post gewirkt hat.
