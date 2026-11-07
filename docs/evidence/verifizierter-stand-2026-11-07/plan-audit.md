# Plan-Audit `plans/mcp-server.md` — Strang A (Opus, 07.11.2026)

Gegenstand: jeder Haken unterhalb von „Stand für Jay" bis einschließlich „Etappen"
(Planstand `feef949`, 1345 Zeilen). „Z." = Zeile im alten Plan. Urteile:
**erledigt** · **offen** · **nicht prüfbar** · **überholt** (durch spätere Entscheidung/Arbeit ersetzt).

**Bilanz:** 172 Urteile (#1–172; Sammelhaken W1/W2 und README in Server/Desktop bzw. Teile
geteilt): **94 erledigt · 68 offen · 6 nicht prüfbar · 4 überholt/gestrichen**. Davon Einzelbelege:
#1–142; blockweise: #143–172 (ältere Weiter-bei-Blöcke) sowie die Blöcke #40–45 und #101–119.
Kein Desktop-Handtest-Haken gesetzt.

Beweisarten, alle in dieser Session selbst erhoben:

- Commit: `git cat-file -e` + `git log -1` + `merge-base --is-ancestor` für alle 132 im Plan genannten Hashes, `git show --stat` für jeden in einer Einzelzeile genannten Commit;
  6 Zeichenfolgen sind keine Commits dieses Repos, siehe „nicht prüfbar"; `036a4f4`, `3d80235`, `836324b`, `98e4342`, `dd932f6` existieren, liegen aber nicht auf main.
- Test: `uv run pytest <datei>::<test> -q` selbst gelaufen. Läufe:
  (1) 22 Testdateien → `874 passed` (rc=0); (2) 25 Einzel-IDs/Dateien → `174 passed` (rc=0);
  (3) Resolver/Masse/CAS → `201 passed` (rc=0); `tests/test_masse_eval_ir.py` → `2 passed`.
  Logs: Scratchpad der Session (`pytest1.log` … `pytest3.log`).
- `datei:zeile` bzw. `grep` mit leerem Ergebnis für „fehlt".
- Nicht selbst gelaufen: `./test.sh` (gesamt), `test:host`, `handshake.sh`, Routing-Evals
  (Netz/API) — wo ein Urteil darauf ruht, steht „Fremdbeleg".

**Regel für Desktop-Handtests:** kein Haken „Desktop-Handtest" wird hier gesetzt (Strang B).
Wo die Serverseite belegt ist, wird der alte Sammelhaken in „Serverseite [x]" und
„Desktop-Handtest [ ] → Strang B" geteilt.

## 1. Tabelle Behauptung → Beweis → Urteil

### Basis-Ausbau / Wellen 1–3 / README hochwertig (Einzelbelege)

| # | Z. | Behauptung (Plan) | Beweis | Urteil |
|---|---|---|---|---|
| 1 | 902 | [x] Jay-Entscheid 06.11.: Welle 3 = zweiter Konnektor `chemdraw-pharma` | Tisch-Faden `20261106-222336` nicht gelesen (keine Tisch-Nutzung in diesem Strang); Entscheid steht wortgleich in 15 Weiter-bei-Blöcken | nicht prüfbar (Jay-Entscheid, nur Plan-Text) — bleibt [x] als Entscheidung |
| 2 | 988 | W1 generate_mechanism: Serverseite `142e581` (DoD 1–5) | `git show 142e581 --stat` (30.10., in v0.7.0); `test_server_mechanism.py::test_title_names_the_textbook_example_when_it_falls_back`, `::test_every_template_names_its_drawn_example` grün; `MVP_TOOLS` `chemdraw_tool/server.py:258` | Serverseite **erledigt** |
| 3 | 988 | … offen: Desktop-Handtest | frühere Doku `998386d`/`056cb2a` (05.11.) liegt vor `e559323`/`9662b76`/`cce71b0` | **offen → Strang B** |
| 4 | 992 | W1 generate_3d: Serverseite `044e8d6`, Zäune, 3 Routingfälle | `git show 044e8d6`; `test_structure3d.py::test_methane_becomes_tetrahedral_with_hydrogens`, `test_server_profiles.py::test_mvp_neighbours_fence_towards_newly_enabled_tools` (22 Param.) grün | Serverseite **erledigt** |
| 5 | 992 | … offen: Desktop-Handtest | — | **offen → Strang B** |
| 6 | 994 | W1 lookup: Serverseite `ed2dee2`, KEGG-Fix, leere Zeile | `git show ed2dee2`; `test_server_lookups.py::test_lookup_pathway_takes_the_exact_name_not_the_first_fuzzy_hit`, `::test_lookup_physical_skips_rows_without_a_property_name` grün | Serverseite **erledigt** |
| 7 | 994 | … offen: Desktop-Handtest | — | **offen → Strang B** |
| 8 | 1003 | W2 predict_spectrum: `3945648`, Name statt SMILES | `git show 3945648`; `test_server_spectro.py::test_a_compound_name_is_resolved_instead_of_rejected` grün | Serverseite **erledigt** |
| 9 | 1003 | … offen: Desktop-Handtest | — | **offen → Strang B** |
| 10 | 1007 | W2 generate_spectrum: `c6c847c` + `6ba60ca`, Transmission multipliziert | `git show c6c847c`, `6ba60ca`; `test_spectrum.py::test_overlapping_strong_ir_bands_never_clip_to_zero`, `test_server_profiles.py::test_mvp_spectrum_tool_claims_named_spectra_against_generic_charts` grün; `"IR"` groß: `cce71b0` + `test_server_spectrum.py::test_spectrum_type_is_case_insensitive` (4 Param.) grün | Serverseite **erledigt** |
| 11 | 1007 | … Toolwahl gegen Desktops `visualize` rot (`0c36b4b`) | nur in Desktop messbar | **offen → Strang B** (Schritt 5) |
| 12 | 1014 | W2 generate_tlc: `90cfd7b` + `d6098a9`, Fehlertexte englisch | `git show 90cfd7b`, `d6098a9`; `test_tlc.py::test_error_messages_are_english` (6 Param.) grün; Host-Fall `host.e2e.mjs:181` | Serverseite **erledigt** |
| 13 | 1014 | … Toolwahl rot (`0c36b4b`) | nur in Desktop messbar | **offen → Strang B** (Schritt 6) |
| 14 | 1018 | W2 Titration + Speziesverteilung: `6093b88`, absteigende pKa → Fehler, Pufferpunkte `a08e3cb` | `git show 6093b88`, `a08e3cb`; `test_server_plots.py::test_descending_pka_values_are_rejected`, `::test_plot_errors_are_english`, `test_ph_plots.py::test_pufferpunkte_liegen_auf_der_kurve` grün; Host-Fall `host.e2e.mjs:212-215` | Serverseite **erledigt** |
| 15 | 1018 | … Desktop 0/4 (`a6d6e86`), „Toollisten-Diskrepanz (oben)" | Verweis „oben" zeigt in einen Weiter-bei-Block; Desktop-Teil nur in Desktop messbar | **offen → Strang B** (Schritt 7) |
| 16 | 1026 | W2 calculate_ph: `71223ed`, 16 Tools / 12 Panels | `git show 71223ed`; `test_ph_calc.py::test_acetic_acid_matches_the_textbook_value`, `test_server_profiles.py::test_default_and_explicit_mvp_offer_exactly_the_mvp_tools` grün; Handshake 16/12 = Fremdbeleg `owner-abnahme.md` | Serverseite **erledigt** |
| 17 | 1026 | … offen: Desktop-Handtest + Host-Fälle/README | README-Zeile `README.md:60`, Bild `assets/calculate-ph.png` (`README.md:82`); Desktop fehlt | README **erledigt**, Desktop **offen → Strang B** (Schritt 8) |
| 18 | 1052 | W3 `desktop_config.py` + `install.sh`: zwei Einträge `chemdraw`/`chemdraw-pharma` | `grep -rn chemdraw-pharma chemdraw_tool/ install.sh scripts/ tests/` → leer; `SERVER_NAME = "chemdraw-tool"` `chemdraw_tool/desktop_config.py:33` | **offen** (nicht begonnen) |
| 19 | 1059 | W3 `.mcpb` für beide Profile | `mcpb/manifest.json` ohne zweites Profil; grep leer | **offen** |
| 20 | 1064 | W3 `handshake.sh` prüft beide Konnektoren | grep `chemdraw-pharma` in `scripts/handshake.sh` leer | **offen** |
| 21 | 1068 | W3 README „Profiles" mit zwei Konnektoren | grep in `README.md` leer; Profile nur in `docs/tools.md:140` (`CHEMDRAW_PROFILE=full`, ein Konnektor) | **offen** |
| 22 | 1072 | W3 Desktop-Wechsel abnehmen | setzt 18–21 voraus | **offen** |
| 23–28 | 1081–1086 | W3 Tools calculate_solution, calculate_content, calculate_pharmacokinetics, generate_pk_curve, generate_dose_response, generate_calibration_curve | im `full`-Profil registriert (`test_server_profiles.py::test_full_profile_keeps_the_complete_snapshot_catalog` grün), nicht in `MVP_TOOLS`; Welle-3-Arbeit (Auswahltexte/Routing für `full`) nicht begonnen | **offen** |
| 29 | 1087 | W3 generate_scope_table verschlanken (36,7 KB) | kein Commit seit Messung 30.10. gefunden (`git log --oneline --since=2026-10-30 -S scope_table -- chemdraw_tool/server.py` → leer) | **offen** |
| 30 | 1088 | W3 generate_mechanism aus Nutzersubstraten: echte Mechanismen statt Galerie | Merge `16fc11e` (04.11., „zeichnet die Substrate des Nutzers"), in v0.8.0; `tests/test_mechanism_substrate.py` grün (Lauf 1); MVP-Instructions `server.py:297-299` „draws the user's substrates within each family's limit" | **erledigt** (in den drei Familien SN1/SN2/Fischer; andere Mechanismen bewusst nicht) |
| 31 | 1091 | README: je Bereich ein echtes Bild + Profiles auf zwei Konnektoren | Bilder: `README.md:69-95` (Zeichnen: mechanism, 3d · Laborgrafik: spectrum, titration, tlc · Nachschlagen: lookup-datasheet · Rechnen: calculate-ph · Anki: anki-card), `scripts/readme_bilder.py`, `test_readme.py::test_skriptbilder_tragen_den_gesegneten_hash` grün, `1f4cb10`; Profiles: grep `chemdraw-pharma` leer | **geteilt:** Bilder **erledigt**, Profiles **offen** (hängt an Welle 3) |
| 32 | 1094 | README: `.mcpb` zuerst, `install.sh`/PyPI danach | `README.md:28-31` (Quick start = .mcpb), `README.md:99` vor PyPI `:103`; `65800df` | **erledigt** |
| 33 | 1095 | README: Werkzeugtabelle Tool · Bereich · Beispiel-Prompt · Panel | `README.md:44-60`; `65800df` (31.10.); `test_readme.py::test_tooltabelle_nennt_genau_die_mvp_tools` grün | **erledigt** |
| 34 | 1096 | Danach Shorts (`plans/vermarktung.md`) | `plans/vermarktung.md` existiert in diesem Repo nicht (`ls plans/`); Material liegt laut CLAUDE.md in `chemdraw-vermarktung` | **offen** (Verweisziel korrigiert) |

### Doku-Aktualität (Z. 283–295, bleibt im Plan)

| # | Z. | Behauptung | Beweis | Urteil |
|---|---|---|---|---|
| 35 | 285 | Inventur mechanisch prüfbarer Doku-Angaben | umgesetzt in `tests/test_docs_consistency.py` (9 Tests); Commit `9b1d8db` | **erledigt** |
| 36 | 289 | `test_docs_consistency.py` (9 Tests) | alle 9 selbst gelaufen grün (u. a. `::test_identitaetszahl_stimmt`, `::test_panelzahlen_je_profil_stimmen`) | **erledigt** |
| 37 | 291 | `release_check.py` + Test; `publish.yml` `needs: check` | `test_release_check.py::test_unreleased_mit_eintraegen_ist_rot` grün; `.github/workflows/publish.yml:21` (`check:`), `:34` (`needs: check`) | **erledigt** |
| 38 | 292 | Checkliste 1a in `docs/registry-publish.md` | `docs/registry-publish.md:114` | **erledigt** |

### Etappen (Z. 1127–1345)

| # | Z. | Behauptung | Beweis | Urteil |
|---|---|---|---|---|
| 39 | 1128 | [ ] „Geparkt, nicht löschen": sieben ungenutzte Assets | `ls assets/<name>` → alle sieben **fehlen**; gelöscht in `dde25d3` (04.11., „sieben vom README nicht mehr genutzte Bilder entfernt; Etappe C abgenommen", in v0.8.0) | **überholt** (Assets weg; Git-Historie hält sie) |
| 40–45 | 1134–1148 | Etappe 14.10: sechs [x] (Layout, Tastatur, Abnahme 6.958/40, Wheel+Desktop Koffein, `test:ui:watch`, DevTools) | Block: `adccc04` „MVP-Panel lesbar und responsiv" (14.10.), `d830726` DevTools-Doku, `chemdraw_tool/ui/package.json:16` (`test:ui:watch`), `docs/ui-pruefung.md`, `docs/produkt/panel-mvp/`, `host.e2e.mjs:309-311` (hell/dunkel × 360/980) | **erledigt** (blockweise); Zahlen 6.958/40 und Chat-ID `132254e1…` nicht nachprüfbar |
| 46 | 1152 | [ ] Routing-Befund MVP: `lookup-data-sheet` rot, Stub-Vermutung | Fall steht `evals/tool-routing/cases.yaml:232-235`; Messung braucht API (nicht gelaufen) | **offen** (nicht prüfbar ohne API) |
| 47 | 1162 | [x] mcp-2.x-Migration `c0dd24d` | `git show c0dd24d --stat` (14.10., auf main, in v0.5.0) | **erledigt** |
| 48 | 1168 | [ ] Desktop-Entwicklermenü ersetzt nur einen von zwei Prozessen | nur in Desktop messbar | **offen** (nicht prüfbar) |
| 49 | 1171 | [x] SMILES-Dateinamen-Kollisionen `20c204f` | `git show 20c204f` (20.10., in v0.5.0) | **erledigt** |
| 50 | 1175 | [ ] NCI CIR 500 auf deutsche Namen → Wikidata-Stufe; ACS-1996 | NCI-500 behandelt `cc13e47` („zählt als unbekannt"); deutsche Trivialnamen über `abee1a5` (`chemdraw_tool/de_names.py`), `test_de_names.py` grün; Wikidata-Stufe nicht gebaut; ACS-1996 nicht gebaut | **teilweise**: NCI/deutsche Namen erledigt, ACS-1996 **offen** |
| 51 | 1191 | [ ] M3 `title`/`readOnlyHint` | `grep readOnlyHint chemdraw_tool/server.py tests/__snapshots__/tools/` → leer | **offen** |
| 52 | 1192 | [ ] M2 Payload-Größen messen | kein Test/Skript gefunden | **offen** |
| 53 | 1193 | [ ] M7 Icon, `privacy_policies`, Windows; M8 | `mcpb/manifest.json:28` `platforms: darwin, linux` (Windows ausgeschlossen); kein `icon`, kein `privacy_policies` | **offen** (Windows-Teil erledigt) |
| 54 | 1194 | [ ] W-1 Nativer Look | `chemdraw_tool/ui/src/styles.css:4-8` nutzt `--color-*` des Hosts mit Fallback; Spinner `styles.css:187` statt Skelett | **offen** (teilweise) |
| 55 | 1195 | [ ] W-1b Quiz-Satz in `instructions` | `_MVP_INSTRUCTIONS` `server.py:285-319` ohne Quiz | **offen** |
| 56 | 1196 | [ ] W0 Host-Messung | nur in Desktop | **offen** |
| 57 | 1197 | [ ] W1 Reiter Struktur · Stereo · 3D · Daten | Struktur/All H/Fischer/Haworth `MoleculeView.jsx:250-252`; Stereo per „Show variants" `fd709cc` (v0.6.0), Host-Klick `host.e2e.mjs:387-394`; Data-Umschalter vorhanden; **3D fehlt** im Molekülpanel | **offen** (Rest: 3D-Knopf) |
| 58 | 1198 | [ ] W2 3D dreht von selbst | `Molecule3DView.jsx` ohne `requestAnimationFrame`/Autorotation (grep leer) | **offen** |
| 59 | 1199 | [ ] W3 Browser-Demo | kein Demo-Link im README (grep `demo`/`github.io` leer) | **offen** |
| 60 | 1200 | [ ] W4 Atom → Claude erklärt … | kein `ui/message`/`sendMessage` in `ui/src` | **offen** |
| 61 | 1201 | [ ] W5 README um den Wow-Moment | README-Neubau `65800df`/`1f4cb10` ist Galerie nach Bereichen, nicht um Reiter/Demo | **offen** (abhängig von W1–W3) |
| 62 | 1202 | [ ] W6 Blind-/Prüfmodus … | nichts gebaut | **offen** |
| 63 | 1203 | [x] M0 ext-apps 2.0.3 | `git show ac13350`, `1bacd64` (03.10.) | **erledigt** |
| 64 | 1204 | [x] W-1c Recherche Verzeichnis | `git show bcf3286`; `docs/anthropic/abgleich.md` vorhanden | **erledigt** |
| 65 | 1207 | [ ] Ausgangsbilder `docs/produkt/panel-vorher/` | Ordner fehlt (`ls docs/produkt/` → `panel-moeglichkeiten.md`, `panel-mvp`, `pk-kurve.html`) | **offen** (panel-mvp ist der 14.10.-Stand) |
| 66 | 1208 | [ ] Versuch 1 `ui/message` | grep leer | **offen** |
| 67 | 1209 | [ ] Versuch 2 Panelhöhe | nur in Desktop | **offen** |
| 68 | 1210 | [ ] Bundle-Budget-Test ≤ 650 kB | kein Test (grep `650` in `tests/` leer); `dist/index.html` heute 447.645 B | **offen** (Budget eingehalten, Test fehlt) |
| 69 | 1213 | [ ] Payload `svg_stereo`/`mol3d` | grep in `chemdraw_tool/payloads.py` leer; Stereo kommt lazy (`fd709cc`, bewusst „lazy statt im Payload") | **überholt** für Stereo (Entscheid in `fd709cc`), **offen** für 3D |
| 70 | 1214 | [ ] Panel-Reiter inkl. 3D-Komponente | wie #57 | **offen** (Rest 3D) |
| 71 | 1215 | [ ] Host-Test klickt durch vier Reiter | Host klickt Show variants (`host.e2e.mjs:390`), Fischer/Haworth (`:425`), Data (`:344-349`); kein 3D | **offen** (Rest 3D) |
| 72 | 1216 | [ ] **Jay:** 10-Sekunden-Test Ibuprofen → Stereo → 3D → Data | Stereo/Data: Strang B Schritt 1 (`auftrag.md`); 3D-Knopf fehlt | **offen → Strang B** (3D-Teil entfällt bis Knopf) |
| 73 | 1219 | [ ] Tokens in `styles.css` | `styles.css:12` `--radius`, `:190` `--radius-sm/md`, `--shadow-card`; keine Abstands-/Schriftgrößen-Tokens | **offen** (teilweise) |
| 74 | 1220 | [ ] Steckbrief einklappbar | kein `details`/collapse in `DatabaseView.jsx` | **offen** |
| 75 | 1221 | [ ] Schmal/breit: Block unter dem Bild | `styles.css:260` `@media (max-width: 619px)`; `host.e2e.mjs:325` „Schmale Ansicht stapelt Struktur und Steckbrief"; `adccc04` | **erledigt** (Grenze 620 statt 560 px) |
| 76 | 1222 | [ ] Hell/dunkel prüfen; Galerie vorher/nachher | hell/dunkel `host.e2e.mjs:309-365`; Galerie-Vergleich vorher/nachher nicht belegt (vgl. #65) | **teilweise**: hell/dunkel erledigt, Galerievergleich offen |
| 77 | 1225 | [ ] Optionsleiste Stil/Stereo/Abkürzen | keine Optionsleiste in `MoleculeView.jsx`; `render_style` nur als Tool-Parameter | **offen** |
| 78 | 1226 | [ ] Folge-Vorschläge | hängt an #66 | **offen** |
| 79 | 1227 | [ ] Eval 28/28 | braucht API; nicht gelaufen | **nicht prüfbar** |
| 80 | 1230 | [ ] 3D Dauerdrehung | wie #58 | **offen** |
| 81 | 1231 | [ ] Weiche Übergänge | nicht gefunden | **offen** |
| 82 | 1232 | [ ] Mechanismus-Autoplay | `MechanismView.jsx:292` nur „Overview/Step by step", kein Timer | **offen** |
| 83 | 1233 | [ ] Bildrate ≥ 30 fps | keine Messung | **offen** |
| 84–87 | 1236–1239 | [ ] Phase 5 Abfragemodus (`mode="quiz"`, Aufdecken, Varianten, Tests) | grep `quiz` in `chemdraw_tool/` → leer | **offen** (zurückgestellt, s. #88) |
| 88 | 1284 | [ ] **Jay:** Freigabe A1 (oder B/C)? | Herkunft: Entwurf 26.10. (Z. 1241), pausiert Jay 26.10. 23:55 für Shorts (Z. 1242), Basis-Ausbau 30.10. „Keine OC-Prüfungsfragen in dieser Runde" (Z. 894), Jay 07.11. „zunächst nur Moleküle" (Z. 1298) | **offen, zurückgestellt** (nicht veraltet; Frage wird erst nach Basis-Ausbau gestellt) |
| 89–92 | 1287–1290 | [ ] Phase 6 Prüfungsmodus | nichts gebaut | **offen** |
| 93 | 1293 | [ ] Phase 7 Reaktionen/Mechanismen abfragen | Jay 07.11. (Z. 1298) | **offen** (bewusst nach Phase 5) |
| 94 | 1296 | [x] Jay: Fachrichtung → OC-Grundlagen | Jay-Antwort 26.10. im Plan (Z. 1297) | **erledigt** (Jay-Entscheid, nur Plan-Text) |
| 95 | 1298 | [x] Jay 07.11.: Abfragemodus erst Moleküle | im Plan nachgetragen `f58eb5b` (`git show f58eb5b`) | **erledigt** (Jay-Entscheid) |
| 96 | 1321 | [ ] **Jay:** Desktop „Zeig mir Methylphenidat" → Data | Host: `host.e2e.mjs:344-349` (CAS 113-45-1, CID 4158; `5f58b5c`); Server: `werkzeug-probe.log:37-38` (`lookup_molecule_data` Methylphenidat OK, 07.11.); Desktop: Screenshot `/tmp/chemdraw-desktop-test/2026-11-07/04-methylphenidat-data.png` (07:31, Codex) **selbst angesehen**: Datenblatt mit CAS 113-45-1, PubChem CID 4158, InChIKey DUGOZIWVEXMGBE-UHFFFAOYSA-N | Beleg vorhanden, **Haken nicht gesetzt** (Desktop-Handtest → Owner/Strang B setzt); nicht mehr Jays Hand (CLAUDE.md: Handtest → Codex) |
| 97 | 1322 | [ ] `mcp-2-migration` GEPARKT, Worktree, `mcp-2-migration-v2` | Umstellung auf main `c0dd24d` (14.10., v0.5.0); `git worktree list` ohne `agent-a567…`; `git branch -a` ohne beide Branches; Tag `archiv/mcp-2-migration` → `836324b` | **überholt** |
| 98 | 1324 | [ ] Satz in `instructions`: Desktop nimmt Sandbox | `_MVP_INSTRUCTIONS` `server.py:285-319` ohne solchen Satz (der Plan nannte `:205-240`, veraltet) | **offen** |
| 99 | 1325 | [ ] Geschwindigkeit Server-Import | zurückgestellt, keine Messung | **offen** (zurückgestellt) |
| 100 | 1326 | [~] Server-Import ohne RDKit | gestrichen 08.10. | bleibt gestrichen |
| 101–119 | 1327–1345 | Etappe 02.10.: 19 [x] (Releases 0.4.3–0.4.8, Bundle-Startfix, OPSIN-Merge, Host-Test Methylphenidat, Eval 28/28, Pfade, Galerie, Legende, Mechanismus-Overview, Desktop-Test 03.10., Dateinamen) | Tags `v0.4.3`…`v0.4.8` vorhanden; alle genannten Hashes existieren auf main: `20ff181`, `adaed6c`, `022507d`, `3681f7b`, `237698f`, `9a3b8d6`, `0e39eb0`, `6c9b308`, `6763642`, `1bfedb2`, `64a0cb8`, `5c77bc5`; `tests/gallery_ui.py` existiert | **erledigt** (blockweise). Kleinigkeit: Tag `v0.4.6` zeigt auf `1bfedb2`, nicht auf `20ff181` (Release-Commit) |

### Jüngste vier „Weiter bei"-Blöcke (Z. 29–208; wandern ins Archiv, Einzelbelege hier)

| # | Z. | Behauptung | Beweis | Urteil |
|---|---|---|---|---|
| 120 | 51 | [x] Chef-Entscheid Schnitt 3: A>= statt B′ | `docs/evidence/masse-eval-2026-11/kippmessung-stereo/ergebnis.md:9,22` (A>= 0 gekippt / 4 behoben; B′ kippt citral, Citral A+B), `git show 6259e38` | **erledigt** (Entscheid belegt durch Messung) |
| 121 | 59 | [x] Messung auf `112021f` neu: 0 gekippt, 4 behoben, Holdout PubChem 0/6 | `ergebnis.md:1-4` (683 grün, Treue 0 Abweichungen, Memo 0), `:22` (mit beschlossener Referenzwertung: Holdout PubChem `0 [] / 6`). Achtung: Tabelle ohne Fixture-Korrektur `:9` zeigt `1/6/0` | **erledigt** (Zahl gilt nur „mit beschlossener Referenzwertung") |
| 122 | 64 | [x] Nicotin-Referenz `668d05b` auf (S) | `git show 668d05b --stat` (nur `tests/identity/stoffe-masse.json`); `stoffe-masse.json:5792,5802` → `SNICXCGAKADSCV-JTQLQIEISA-N` | **erledigt** |
| 123 | 72 | [x] Nicotin-Regenerationsschutz | `git show 1ea7d42` (`scripts/masse_eval.py`, `tests/test_masse_eval_identity.py`); `test_masse_eval_identity.py::test_rebuilding_list_keeps_stereo_reference_corrections` grün. Plan nennt „36 passed" — die Datei hat heute 25 Tests (+2 in `test_masse_eval_ir.py`); die 36 waren vermutlich mehrere Dateien | **erledigt** (Testzahl nicht reproduziert) |
| 124 | 76 | [ ] Opus: A>= implementieren (läuft) | `git show e559323` (07.11., `resolver.py` +65, `tests/test_resolver.py` +56); `test_resolver.py::test_spelling_variant_with_more_defined_stereo_wins`, `::test_spelling_variant_never_drops_defined_stereo`, `::test_stereo_form_rule_skips_d_l_prefixed_names` grün; `tests/test_resolver.py` gesamt grün; Owner-Abnahme `owner-abnahme.md` (ohne Hunk 2 failed) | **erledigt** — Plan-Zeile veraltet |
| 125 | 79 | [x] CAS-Fix `9662b76` abgenommen, Ibuprofen 15687-27-1 | `git show 9662b76` (`databases.py`, Fixtures `tests/__fixtures__/pubchem-cas/`); `test_databases.py::test_ibuprofen_cas_uses_sourced_identifier_not_first_synonym`, `::test_cas_section_for_different_cid_is_not_used` grün; Screenshot `/tmp/…/07-ibuprofen-data-nach-fix.png` existiert (nicht von mir angesehen; Owner hat ihn gesehen). Gate „8362 passed" nicht selbst gelaufen | **erledigt** (Code + Tests); Desktop-Teil = Fremdbeleg |
| 126 | 86 | [ ] Host-Test SN1-Titel offen | `git show cce71b0 --stat` (`host.e2e.mjs` 10 Zeilen), `feef949`; rc=0 „167 ✔" = Fremdbeleg `owner-abnahme.md` (nicht selbst gelaufen, braucht Netz) | **erledigt laut Fremdbeleg** — Plan-Zeile veraltet |
| 127 | 91 | [x] Tisch-Fäden geschlossen | Tisch in diesem Strang nicht benutzt | **nicht prüfbar** |
| 128 | 93 | [ ] 3D-Knopf bleibt W1 | `MoleculeView.jsx:250-252` ohne 3D; `generate_3d` nur Chat (`MVP_TOOLS`) | **offen** (in neuen Plan unter W1 übernommen) |
| 129 | 105 | [x] Lauf 11 gesichert, SHA256 `095e0111…` | `shasum -a 256 docs/evidence/masse-eval-2026-11/identitaet-lauf-11-vor-schnitt-1-2.json` → `095e0111a57f5086dec47de13ab6ee02ed374dfb601508bdfdcfeb1a4caced8c` | **erledigt** (Hash identisch) |
| 130 | 107 | [x] Lauf 12: 711 · 683 grün · … · 14 rot | `lauf-12-vergleich.json` vorhanden, `start_commit`-Feld; `git show f58eb5b` | **erledigt** (Einzelzahlen nur über #131 nachgezählt) |
| 131 | 111 | [x] Vergleich Lauf 11→12: 675/8/6/8/14 | `lauf-12-vergleich.json` → `uebergaenge`: `gruen→gruen 675, rot→rot 14, rot→gruen 8, rot→gelb 6, gelb→gelb 8` | **erledigt** (exakt) |
| 132 | 115 | [x] Bericht mit `masse_eval.py identitaet` erzeugt | `docs/evidence/masse-eval-2026-11/identitaet.md` vorhanden, `f58eb5b` | **erledigt** |
| 133 | 118 | [x] Jay-Entscheid 07.11. im Plan nachgetragen | Z. 1293, 1298; `f58eb5b` | **erledigt** |
| 134 | 149 | [x] `b67ceb7` Stereo-Referenzen | `git show b67ceb7 --stat` (`stereo-referenzen/{README,audit,korrekturen,vergleich,lauf-7-neuwertung}.json`) | **erledigt** |
| 135 | 153 | [x] Clindamycin-Auditsatz berichtigt | `b67ceb7` ändert `referenzkorrektur/referenz-audit.json` (3 Zeilen) | **erledigt** |
| 136 | 155 | [x] Neuwertung Lauf 7 `9b3cbbd`: 668/1/42 → 673/1/37 | `git show 9b3cbbd --stat`; Zahlen nicht nachgezählt | **erledigt** (Commit), Zahlen ungeprüft |
| 137 | 158 | [x] Gate 8213 passed | Log in `/tmp`, nicht selbst gelaufen | **nicht prüfbar** (historische Gatezahl) |
| 138 | 161 | [x] Befund 3 abgenommen (Tisch-Bericht, `/tmp`-Datei) | Tisch/`/tmp` nicht geprüft; Lauf 7 als `9b3cbbd` vorhanden | **nicht prüfbar** (Abnahme-Akt) |
| 139 | 187 | [x] Befund 4 `530e9a9` | `git show 530e9a9 --stat` (`referenzkorrektur/*`, `scripts/masse_eval.py`); `test_masse_eval_identity.py::test_chembl_name_cache_expires_and_can_be_refreshed` grün | **erledigt** |
| 140 | 189 | [x] 46 rote Fälle auditiert | `referenzkorrektur/README.md`, `referenz-audit.json` vorhanden | **erledigt** (Datei), Inhalt nicht nachgezählt |
| 141 | 191 | [x] 10 passed, Gate 8203 | heute `tests/test_masse_eval_identity.py` 25 passed (Datei gewachsen); Gate nicht selbst gelaufen | **erledigt** (Tests grün), Gatezahl nicht prüfbar |
| 142 | 194 | [x] Befund 2 Runde 3 `8978be7` | `git show 8978be7 --stat` (`resolver.py`, `tests/test_resolver.py` +119); `test_resolver.py::test_water_alone_is_a_form_conflict_not_a_correction` grün | **erledigt** |

### Ältere „Weiter bei"-Blöcke und Orchestrierung (Z. 209–889, blockweise)

| # | Block (Z.) | Haken | Beweis (blockweise) | Urteil |
|---|---|---|---|---|
| 143–145 | Kreuzabnahme Runde 2 (209) | 3 [x] (Runde 1/2, Desktop-Handtest E2) | `41da7c4`, `e228047`, `038ace4`, `236df52` existieren (06.11.); E2-Desktop: nur Doku `998386d`/`056cb2a`; „139/146 gezielte Tests" nicht reproduziert | erledigt (Commits); Testzahlen + Desktop **nicht prüfbar** |
| 146–149 | Codex-Neustart nach Befund 5 (241) | 3 [x], 1 [ ] (IR-Bericht deterministisch) | `a3f62dd` existiert; offener Haken erledigt durch `3b060db` (`tests/test_masse_eval_ir.py` +36, 2 passed) | erledigt; Z. 274 [ ] **veraltet** |
| 150–154 | Masse-Eval-Befund 1 (338) | 4 [x], 1 [ ] (Offline-Memo im Resolver) | `abee1a5`, `849d2a9`, `41da7c4`, `038ace4` existieren; `test_de_names.py` grün; Offline-Memo: kein Zeitspeicher in `resolver.py` (grep `monotonic`/`_offline_until` leer) | erledigt; Offline-Memo **offen** (in neuen Plan übernommen) |
| 155–158 | Dependabot + rdkit 2026.9 (366) | 4 [x] | `910892b`, `39e7088`, `2d8fd0b` existieren; `tests/test_layout_guard.py` (8) grün | **erledigt** |
| 159 | Etappe F (642) | 1 [x] | `chemdraw-vermarktung` Stand `c91abb2` liegt im Schwester-Repo | **nicht prüfbar** hier |
| 160–164 | Werkzeugbilanz A–D (800–820) | 5 [x] | `16fc11e`, `167c8b1`, `73b48fc`, `c776d83`, `cecb120`, `7007e14` existieren; `ea0ceb8` liegt im Repo praktikumsrechner | **erledigt** (Commits); `ea0ceb8` nicht prüfbar |
| 165–172 | Release 0.7.0 (872–881) | 8 [x] | Tag `v0.7.0` → `3016833` (04.11.); `cb4afa9`, `40723f9`, `7596c26`, `bcd6f44`, `249fca6` existieren; `docs/desktop-abnahme-0-7-0-bundle.md` vorhanden; CHANGELOG `## [0.7.0] — 2026-11-03` | **erledigt** |

Release-Rahmen: `v0.8.0` → `566a060` (05.11.), CHANGELOG `## [0.8.0] — 2026-11-05`.
Alle W1/W2-Server-Commits sind in `v0.7.0` enthalten (`git tag --contains`).

## 2. Falsch oder veraltet im Plan → korrigiert

| Plan-Zeile (alt) | Richtig | Beleg | Wo korrigiert |
|---|---|---|---|
| Z. 36 „Stereo-Klick erst nach W1 ergänzen" | Stereo-Picker „Show variants" existiert seit 0.6.0 | `fd709cc` (26.10., `git tag --contains` → v0.6.0), `host.e2e.mjs:387-394`, `chemdraw_tool/ui/src/components/StereoNote.jsx:60` | Zeile nur im Archiv (wörtlich); im Plan nicht übernommen, W1-Rest heißt nur noch „3D-Knopf" |
| Z. 40 „CI rot laut Chef, Eigentümer unklar" | CI-Lint behoben | `b708dd3` (07.11., `scripts/notebooklm/bundle.py`, `refresh.py`) | nur im Archiv; Plan führt ihn nicht mehr |
| 15× „Welle-3-Entscheid (Jay 06.11., beantwortet)" (Z. 175, 205, 236, 281, 336, 364, 376, 426, 458, 510, 541, 664, 699, 750, 870) | einmal genügt | `grep -c` → 15 (Auftrag sprach von 16) | Im Plan genau einmal (Haken unter Basis-Ausbau). Das Archiv bleibt wörtlich, enthält also weiter 15 Kopien — das ist Absicht („unverändert"), kein Verstoß |
| Z. 76 „Opus: A>= implementieren (läuft)" | gebaut und abgenommen | `e559323`, 3 Tests grün (#124) | Audit; Block im Archiv |
| Z. 86 „Host-Test SN1-Titel (offen)" | behoben | `cce71b0`, `feef949`; rc=0 Fremdbeleg | Audit; Block im Archiv |
| Z. 274 „Folgeauftrag deterministischer IR-Bericht" offen | erledigt | `3b060db`, `test_masse_eval_ir.py` 2 passed | Audit; Block im Archiv |
| Z. 1128 „Geparkt, nicht löschen: sieben Assets" | Assets sind gelöscht | `dde25d3` (04.11.) | Plan: `[~]` überholt |
| Z. 1322 „mcp-2-migration GEPARKT" | Migration auf main, Branches weg | `c0dd24d`, Tag `archiv/mcp-2-migration` | Plan: `[~]` überholt |
| Z. 1324 Verweis `server.py:205-240` | Instructions stehen `server.py:285-319` | Datei gelesen | Plan |
| Z. 1096 Verweis `plans/vermarktung.md` | Datei fehlt in diesem Repo | `ls plans/` | Plan: Verweis auf Schwester-Repo |
| Z. 1091 README-Haken als ein Block offen | Bilder je Bereich sind fertig, nur „Profiles" offen | #31 | Plan: geteilt |
| Z. 1094/1095 README `.mcpb` zuerst / Tool-Tabelle offen | erledigt | `65800df`, `README.md:28-31,44-60,99` | Plan: [x] |

**Rückfragen an Jay (drei alte):**

1. „10-Sekunden-Test" (Z. 1216): wird durch Strang B Schritt 1 beantwortet (Ibuprofen →
   Show variants → (R) → Data); der 3D-Teil entfällt, solange der 3D-Knopf fehlt. Bleibt `[ ]`.
2. „Freigabe A1" (Z. 1284): Herkunft = OC-Prüfungsfragen-Entwurf 26.10.; am selben Abend
   pausiert (Shorts zuerst), am 30.10. für den Basis-Ausbau ausgeschlossen, am 07.11. durch
   „zunächst nur Moleküle" eingeengt. **Nicht veraltet, sondern zurückgestellt** — Frage an Jay
   erst nach Welle 3/README. Bleibt `[ ]` mit `**Jay:**`.
3. „Methylphenidat → Data" (Z. 1321): Belege #96 (Host, Server, Desktop-Screenshot 07:31 selbst
   angesehen). Kein Jay-Haken mehr; Setzen bleibt Owner/Strang B vorbehalten.

**Nebenbefund für den Owner — „Stand für Jay" (nicht angefasst, Auftrag):**

- Punkt 4 (`test:host` rot) ist laut `owner-abnahme.md` erledigt (`cce71b0`+`feef949`, rc=0).
- Punkt 5 (`generate_spectrum` lehnt `"IR"` ab) ist erledigt: `cce71b0`,
  `test_server_spectrum.py::test_spectrum_type_is_case_insensitive` selbst grün.
- Punkt 9 „README hochwertig (4 Haken)": nach Audit 2 erledigt, offen nur Profiles (Welle 3) und Shorts.

## 3. Nicht prüfbar — mit Grund

| Was | Grund |
|---|---|
| `76129dfa`, `8b06750a`, `edf9eeb9`, `f31ab414` | Claude-Session-IDs, keine Commits |
| `c91abb2` (chemdraw-vermarktung), `ea0ceb8` (praktikumsrechner) | Commits in Schwester-Repos, hier nicht geprüft |
| Tisch-Fäden (geschlossen/abgenommen/Berichte #n) | Strang A nutzt den Tisch nicht (Auftrag) |
| Gatezahlen der Vergangenheit (8102, 8189, 8203, 8213, 8362, 6.958 …) | historische Läufe, Logs unter `/tmp`; nur der heutige Stand wäre reproduzierbar (Gesamt-Gate nicht gelaufen) |
| Routing-Eval-Zahlen (11/13, 12/13, 26/28, 28/28) | brauchen API-Schlüssel/`claude -p` |
| Desktop-Aussagen (Panel sichtbar, Toolwahl, Prozessersatz beim Reload, Chat `132254e1…`) | nur in Desktop; Strang B |
| `test:host` rc=0 | braucht Netz; Fremdbeleg `owner-abnahme.md` |
| Jay-Entscheide (06.11. Welle 3, 26.10. OC-Grundlagen) | stehen nur im Plan-/Tisch-Text |
