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
- [ ] Release 0.5.0 mit `.mcpb` — Entwurf liegt auf GitHub (Commit 3912e95), Bundle-Job hängt jetzt an `publish`. **Jay:** „Publish release“ klicken
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
