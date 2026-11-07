# Owner-Abnahme (Claude, 07.11.2026) — Strang C

Alles hier ist selbst gelaufen oder selbst angesehen; Befehle und Ausgaben sind nachvollziehbar.

| Behauptung | Beweis | Stand |
|---|---|---|
| Desktop-Befehl spricht MCP, 16 Tools / 12 Panels | `./scripts/handshake.sh` 07:5x: „✅ Handshake gruen: 16 Tools, 12 mit Panel“ | grün |
| Alle 16 MVP-Werkzeuge liefern echte Ergebnisse | `werkzeug-probe.log` (21 Aufrufe: 19 OK, `Blubberwasser` → `not_found` korrekt, `"IR"` → Lücke, behoben `cce71b0`) | grün |
| Bilder druckfähig und richtig | Ibuprofen, Veresterung ⇌ H₂SO₄, Morphin/Codein-Vergleich (OMe markiert) selbst angesehen | grün |
| Backend-Tests | `uv run pytest -q`: **8369 passed, 16 skipped** (vor `cce71b0`), Gate `./test.sh` rc=0 nach `b708dd3` | grün |
| Lint/CI | vorher rot: `scripts/notebooklm/bundle.py` 10 Fehler (committet `86957af`), `refresh.py` 4 (uncommittet); behoben `b708dd3`, `ruff check` „All checks passed“, `bundle.py` läuft (35 Dateien im Paket 3) | grün |
| Opus Schnitt 3 `e559323` | Diff gelesen (Regel `_n_defined_stereo` ≥, D/L-Präfix-Schutz, Komponenten-Schutz); 56 Testzeilen im selben Commit; ohne den Resolver-Hunk **2 failed** (Naloxon/Vareniclin), mit Hunk `tests/test_resolver.py` **171 passed** | abgenommen |
| `test:host` | rot an drei veralteten Erwartungen (SN1-Titel SMILES→Namen; Schritte SN1 6 / Fischer 8; `D-glucose` seit `41da7c4` Pyranosering→Haworth); nach `cce71b0`+`feef949` gegen HEAD: **rc=0, 167 ✔** | grün |
| GIF-Entwurf (Codex) | 4 Dateien als WIP committet `449ed3d`, `assets/demo-molecule.gif` unverändert, keine Aufnahme | gesichert |
| Desktop: Ibuprofen → Struktur / Show variants / Data | Screenshots Codex 07:29–07:41 selbst angesehen: `06-ibuprofen-stereo.png` (Panel, Knopf „Show variants“, Header-CAS damals 58560-75-1), `07-ibuprofen-data-nach-fix.png` (Data: CID 3672, CAS **15687-27-1**); Jays eigener Screenshot (R)-Ibuprofen CAS 51146-57-7 | belegt (vor Server-Änderung; Wiederholung läuft, Strang B) |
| Stereo-Picker existiert | `fd709cc` (26.10., Release 0.6.0), `StereoNote.jsx:60` „Show variants“ — Plan-Zeile „Stereo-Klick erst nach W1“ war falsch | korrigiert |

## Prozessfehler, die bereinigt sind

1. Plan-Zeile „kein Stereo-Klick im Panel“ (Codex 07:49, von Claude ungeprüft weitergegeben) → falsch, oben belegt.
2. CI stundenlang rot, „Eigentümer unklar“ → `b708dd3`.
3. `test:host` seit den 0.8.0-Änderungen nicht mehr gelaufen (blieb beim ersten Mechanismus stehen; dahinter zwei weitere veraltete Erwartungen) → `cce71b0`, `feef949`, rc=0.
4. Commit-Nachricht `cce71b0` nennt den aldehydo-D-glucose-Fall, der erst in `feef949` landete (Skriptfehler beim Editieren; gepusht, nicht umgeschrieben).
5. Codex-Neustart ohne `HERDR_PANE_ID` blockiert, Codex-Kontingent um ~08:35 voll (frei 11:45) → Strang B von einem Claude-Agenten über `scripts/ax-claude.sh`.
6. 72 offene chemdraw-Tisch-Fäden (20.10.–07.11.) geschlossen; keine Leases offen.
7. Arbeitsmodus: Owner-Session statt Dreier (Jay 07.11.), Memory `feedback-owner-session-statt-dreier`.

## Offen bis zu den Berichten

- Strang A (Plan-Audit, Opus): `plan-audit.md` + neu gegliederter Plan — Stichprobe ≥ 5 Beweiszeilen durch mich.
- Strang B (Desktop, Claude-Agent): `desktop-handtest.md` + Screenshots — jeden Screenshot sehe ich selbst an, bevor ein Haken fällt.
