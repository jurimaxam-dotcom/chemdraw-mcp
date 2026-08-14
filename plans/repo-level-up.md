# Repo Level-Up — Auftrag Jay, 14.08.2026

Ziel: präzise User-Experience und pure Nützlichkeit. Autonomer Lauf mit
Opus-Subagenten, Advisor an den schwierigen Stellen.

Leitplanken für ALLE Wellen:
- Rendering-Änderungen sind **opt-in, Default = heutiges Verhalten** —
  sonst kippt der e2e-Pixel-Snapshot. Snapshot regenerieren ist verboten.
- `BOND_LINE_WIDTH`-Parität UI ↔ Export bleibt test-enforced.
- Neues Panel-Tool = `_UI_META` + `App.jsx`-Case + Bundle-Rebuild.
- TDD: rot zuerst. Code fixen, nie den Test.

## Welle 0 — Vorarbeit
- [x] Plan-File angelegt
- [x] Repo-Hygiene geprüft (kein Müll committed, .gitignore ok)
- [x] Memory-Stubs regeneriert (18 Stück — zwei Themen waren heute schon mit
      echtem Volltext nachgefüllt; Verweis-Abgleich leer = Systemkarte grün)
- [x] **A2 Installer** erledigt (siehe Welle 1)

## Welle 1 — Fundament (Audit-Befunde #1–#5)
- [x] **A1 Gate-Härtung**: Guard prüft konkreten Chromium-Executable statt
      Cache-Ordner · Python-Playwright pinnen/aussortieren · ruff ins Gate
      + 9 Fehler fixen · `npm run build`-Diff-Check gegen `dist`
- [x] **A2 Installer**: `shutil.which("uv")` → Absolutpfad in Desktop-Config
      (Fallback `"uv"`), README-`uvx` gleiche Klasse, Tests nachziehen
- [x] **B1 Resolver-UX**: Fehlertaxonomie (Netzfehler ≠ nicht gefunden),
      `(connect=3, read=10)`-Timeouts, `lru_cache` auf Namensauflösung
- [x] **B2 Testlücken**: 5 `lookup_*`-Tools mit eingefrorenen Mock-Responses ·
      Panel-Liste aus Tool-Manager statt 13er-Konstante · Payload-`type` ↔
      `App.jsx`-Case-Paritätstest
- [x] Gate grün (446 Tests) + 6 Commits pro Workstream
- [x] Bonus: 2 Produktionsbugs gefixt (Nullwerte, kaputtes Markdown),
      9 npm-Schwachstellen zu, Lockfile versioniert, CI auf npm ci

## Welle 2 — Features (sequenziell, gleiche heiße Dateien)
- [x] **Gruppen-Kontraktion** via RDKit `rdAbbreviations` (opt-in)
- [x] **Journal-Stil-Presets** (benannte Render-Profile statt loser Parameter)
- [x] **TLC-Platten** aus Rf-Listen (Gattung wie `spectrum.py`)
- [x] **Substrate-Scope-Tabellen** (Journal-Figur pro Call)
- [x] **`chemdraw-doctor`** Diagnose-Kommando (JRE, Pfade, Desktop-Config)

- [x] Bonus: Golden-Test für den Python-Renderer, `chemdraw-install` für
      PyPI-Nutzer, serverInfo meldet die eigene Version

## Welle 3 — Endspiel
- [x] README neu (Einstieg geschärft, Galerie erweitert, Limitations ehrlich)
- [x] CLAUDE.md-Architekturblock in EINEM Pass (7 fehlende Module,
      5-Stufen-Kaskade, parse-first, Panel-Kette, Gate-Philosophie)
- [x] CHANGELOG + Version 0.3.0 (pyproject + server.json + Tag v0.3.0)
- [x] Release: GitHub-Release -> PyPI 0.3.0 live (verifiziert)
- [ ] **OFFEN (braucht Jay):** `mcp-publisher login github` + `publish`
      — Token abgelaufen, Login ist interaktiv. Dauerhafte Lösung als
      Workflow-Vorlage in `docs/registry-publish.md`
- [x] Smoke-Test: stdio-Handshake (22 Tools, 15 Panel, Aspirin gezeichnet,
      Bundle ausgeliefert) + Doctor aus frischer PyPI-Installation grün
