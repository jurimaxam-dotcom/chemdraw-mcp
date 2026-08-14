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
- [ ] **A1 Gate-Härtung**: Guard prüft konkreten Chromium-Executable statt
      Cache-Ordner · Python-Playwright pinnen/aussortieren · ruff ins Gate
      + 9 Fehler fixen · `npm run build`-Diff-Check gegen `dist`
- [ ] **A2 Installer**: `shutil.which("uv")` → Absolutpfad in Desktop-Config
      (Fallback `"uv"`), README-`uvx` gleiche Klasse, Tests nachziehen
- [ ] **B1 Resolver-UX**: Fehlertaxonomie (Netzfehler ≠ nicht gefunden),
      `(connect=3, read=10)`-Timeouts, `lru_cache` auf Namensauflösung
- [ ] **B2 Testlücken**: 5 `lookup_*`-Tools mit eingefrorenen Mock-Responses ·
      Panel-Liste aus Tool-Manager statt 13er-Konstante · Payload-`type` ↔
      `App.jsx`-Case-Paritätstest
- [ ] Gate grün + Commits pro Workstream

## Welle 2 — Features (sequenziell, gleiche heiße Dateien)
- [ ] **Gruppen-Kontraktion** via RDKit `rdAbbreviations` (opt-in)
- [ ] **Journal-Stil-Presets** (benannte Render-Profile statt loser Parameter)
- [ ] **TLC-Platten** aus Rf-Listen (Gattung wie `spectrum.py`)
- [ ] **Substrate-Scope-Tabellen** (Journal-Figur pro Call)
- [ ] **`chemdraw-doctor`** Diagnose-Kommando (JRE, Pfade, Desktop-Config)

## Welle 3 — Endspiel
- [ ] README neu (zeigt die neuen Features, UX-First)
- [ ] CLAUDE.md-Architekturblock in EINEM Pass (fehlende Module,
      5-Stufen-Kaskade, parse-first)
- [ ] CHANGELOG + Version 0.3.0 (pyproject + server.json + Tag)
- [ ] Release: PyPI + `mcp-publisher publish` + `isLatest`-Check
- [ ] Smoke-Test als Beweis: echter MCP-stdio-Handshake (Claude Desktop ist
      auf dieser Maschine NICHT installiert — Befund 14.08., Memory korrigieren)
