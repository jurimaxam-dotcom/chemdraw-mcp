# MCP-Server: Panel, Werkzeuge, Releases

## Weiter bei — Owner-Session nach Kontext-Neustart (07.11.2026, 09:15)

- **Geprüft 07.11. 09:04 (Owner):** Rechte-Dialoge **nicht geklickt** — Sidebar zeigt beide Chats „Awaiting input“, AX-Dump beider Chats: „Waiting for approval: chemdraw-tool: Generate mechanism/Generate titration curve“ mit Decline · Always allow (⇧⌘↩) · Allow once; `~/ChemDraw-Output/server.log` (DEBUG) seit 08:47:37 still, Desktop-Fenster war geschlossen (Prozess 18854 lebt, nicht neu gestartet). Screenshots `/tmp/chemdraw-desktop-test/2026-11-07/verifiziert/14-sn2-dialog-0905.png`, `15-titration-dialog-0905.png`. Beide Chats stehen jetzt offen vorn. `mcp-user-tool-toggles.json` (30.10.) ist **kein** Rechtestand (listet generate_3d/spectrum/tlc, die heute ohne Dialog liefen).
- **Nächster Schritt:** sobald Jay in Claude Desktop die zwei Rechte-Dialoge („Generate mechanism“, „Generate titration curve“ → Always allow) geklickt hat, Strang B Schritte 2 und 7 wiederholen (Claude-Agent per `scripts/ax-claude.sh`, Screenshots nach `/tmp/chemdraw-desktop-test/2026-11-07/verifiziert/`, Owner sieht sie an, dann Haken in Welle 1/2). Danach Release 0.9.0 vorbereiten (Version heben, CHANGELOG, `.mcpb`, `./scripts/publish-registry.sh` erst nach Jays Klick).
- **Offene Fragen an Jay — unbeantwortet, nicht bauen:** (1) Soll „D-Glucose“ im Panel wieder die offene Kette mit Fischer-Knopf liefern (heute Pyranosering + Haworth, seit `41da7c4`)? (2) Release-Klick 0.9.0 bleibt Jays Hand. (3) Anki-Import-Dialog für `~/ChemDraw-Output/anki/chemdraw.apkg` steht offen (seine Sammlung).
- **Erledigt und belegt (07.11.):** Punkte 1–5 unter „Stand für Jay“; Plan-Audit Strang A (`c21a7fc`); Desktop-Handtest Strang B 4/9 (`9047570`); Owner-Abnahme `docs/evidence/verifizierter-stand-2026-11-07/owner-abnahme.md`; Fahrplan-Artifact v3.
- **Prüfmethoden, die gelten:** kein Desktop-Haken ohne selbst gesehenen Screenshot; fremde Plan-Zeilen sind Behauptungen (Commit/Test/Datei:Zeile zeigen); Gate `./test.sh` + `test:host` + `./scripts/handshake.sh` vor jedem Release-Schritt.
- **Routing-Fälle (später, nicht jetzt):** „Welche IR-Banden erwarte ich für Aspirin?“, „pH von 0,1 M Essigsäure“, „Schlag Ibuprofen nach“ → Modell antwortete ohne Werkzeug; Fälle in `evals/tool-routing/cases.yaml` prüfen/ergänzen, erst messen, dann an Beschreibungen drehen.
- **Tisch:** keine offenen Fäden (72 geschlossen), keine Leases. Codex-Kontingent frei ab 11:45. Arbeitsmodus Owner-Session (Memory `feedback-owner-session-statt-dreier`).

## Stand für Jay — 07.11.2026, 08:30 (Claude, selbst gemessen; Abschnitte darunter = Verlauf)

**Läuft (Beweise heute):** Release 0.8.0 (05.11.) · Handshake mit dem Desktop-Befehl grün (16 Tools / 12 Panels) ·
`pytest` 8369 passed / 16 skipped · 21 echte Aufrufe gegen alle 16 MVP-Tools: 19 OK, 1 korrekter Fehler
(`not_found`), 1 Lücke (unten) · Bilder geprüft (Ibuprofen, Veresterung ⇌, Morphin/Codein-Vergleich) ·
Panel kann: Skelett · All H · Fischer/Haworth · Stereo-Varianten mit Keil (R/S-Picker) · Data · Export PNG · Add to Anki ·
Namensauflösung **681/711 = 96 %** (05.11. Lauf 2: 591 = 83 %).

**Offen — rot oder unfertig (Reihenfolge = Abarbeitung):**
1. [x] CI/Gate rot: Lint in `scripts/notebooklm/bundle.py` — behoben `b708dd3` (ruff grün, Skript läuft).
2. [x] Opus-Commit `e559323` geprüft (Claude 07.11.): Diff gelesen, seine 56 Testzeilen ohne den Fix rot (2 failed), mit Fix `171 passed` in test_resolver.
3. [x] README-GIF-Entwurf als WIP gesichert `449ed3d` (keine Aufnahme, Assets unverändert); Aufnahme folgt unter „Danach“.
4. [x] `test:host` grün gegen HEAD `feef949`: **rc=0, 167 Prüfungen** (vorher drei veraltete Erwartungen: SN1-Titel SMILES→Namen, Schritte SN1 6/Fischer 8, „D-glucose“ seit `41da7c4` Pyranosering→Haworth; Fischer-Fall jetzt `aldehydo-D-glucose`, `cce71b0`/`feef949`). **Nebenbefund für Jay:** soll „D-Glucose“ im Panel wieder die offene Kette mit Fischer-Knopf liefern? Heute: Ring + Haworth.
5. [x] `generate_spectrum` nimmt `"IR"` wie `"ir"` (`cce71b0`, Test `test_spectrum_type_is_case_insensitive` erst rot, dann grün).
6. [ ] 3D-Knopf im Molekülpanel fehlt (W1-Rest); `generate_3d` geht nur über den Chat.
7. [ ] Desktop-Handtests der W1/W2-Tools (Strang B, 07.11., Screenshots in `docs/evidence/verifizierter-stand-2026-11-07/screenshots/`, Owner hat 07/09/10/06 selbst gesehen): **4 von 9 belegt** (Ibuprofen-Kette, 3D, Spektrum — Desktop wählte diesmal `generate_spectrum`, nicht `visualize` —, DC) · **2 warten auf Jays Rechte-Klick** (Mechanismus, Titration: Werkzeug + Argumente stimmen, Dialog „Always allow“) · **3 nicht belegt, weil das Modell kein Werkzeug rief** (IR-Vorhersage, pH, Lookup → Routing-Fälle, keine Produktfehler). Nebenbefunde: Export PNG schreibt nach `~/ChemDraw-Output/png/` ohne sichtbare Rückmeldung; Spektrum-Labels 1750/1690 überlappen.
8. [ ] Welle 3: zweiter Konnektor `chemdraw-pharma` (5 Haken, nicht begonnen).
9. [ ] README hochwertig: 2 von 4 erledigt (`.mcpb` zuerst, Tool-Tabelle — `65800df`); offen: Profiles mit `chemdraw-pharma`, danach Shorts (`chemdraw-vermarktung`).

**Arbeitsmodus (Jay 07.11.):** Dreier aufgelöst — eine Owner-Session (Claude) baut selbst und vergibt abgegrenzte Aufträge an Codex/Opus; keine Kreuzabnahme, Plan je Etappe.

**Plan-Audit 07.11.:** 172 Urteile — 94 erledigt · 68 offen · 6 nicht prüfbar · 4 überholt; Beweise in `docs/evidence/verifizierter-stand-2026-11-07/plan-audit.md`, Verlauf in `plans/archiv/mcp-server-verlauf-2026-11.md`.

**Nächste Schritte:** (1) Strang B abnehmen, dann Punkt 6 (3D-Knopf) in dieser Session → Gate + CI grün → **Release 0.9.0** (Resolver 83 → 96 %, Jays Klick) ·
(2) GIF + README-Bilder · (3) 3D-Knopf · (4) Welle 3. **Gestoppt:** Masse-Eval-Langschwanz (14 rot von 711) —
06.11. 14:00 → 07.11. brachten ~90 Commits und ~300 Tisch-Nachrichten nur noch +13 grün.

> Neu gegliedert 07.11.2026 (Plan-Audit, Strang A): „Stand für Jay" unverändert. Alle „Weiter bei"-Blöcke und
> „Orchestrierung" stehen wörtlich in `plans/archiv/mcp-server-verlauf-2026-11.md` (ungeprüfte Behauptungen);
> Urteile mit Beweis je Haken: `docs/evidence/verifizierter-stand-2026-11-07/plan-audit.md`.

## Basis-Ausbau: Wellen 1/2 im Standardprofil, Welle 3 als zweiter Konnektor (Jay 06.11.2026)

> Auftrag Jay 30.10.: die 16 fürs Release zurückgenommenen Tools sauber wieder ins
> Standardprofil holen (`MVP_TOOLS`, `chemdraw_tool/server.py:258`), danach README hochwertig,
> danach Shorts. **Keine OC-Prüfungsfragen in dieser Runde.**
> Reihenfolge umgestellt 30.10. (Jay): nach Breitenwirkung in drei Wellen — Strukturansichten
> stehen, jetzt Reaktionen/Mechanismen; Rechnen ist Vertiefung und kommt später. Je Welle ein
> Release-Kandidat.
>
> Aufteilung: **Opus** = `server.py`, Tool-Snapshots, `cases.yaml`, Python-Tests ·
> **Codex** = Fälle in `host.e2e.mjs`, README-Bilder, Desktop-Handtest.

- [x] **Jay-Entscheid 06.11.2026:** Welle 3 als zweiter Konnektor `chemdraw-pharma`
  (`CHEMDRAW_PROFILE=full`); `chemdraw` bleibt `mvp`. Kein drittes Profil,
  `CHEMDRAW_PROFILE` bleibt. Beleg: Tisch-Faden `20261106-222336-jay-entscheid-06-11` #1.

**Definition of Done je Tool** (jeder Tool-Haken unten heißt: alle Punkte erfüllt).
Schritt 3 zur Aufnahme in `MVP_TOOLS` gilt nur für Wellen 1/2. Welle 3 bleibt
im bereits vorhandenen `full`-Profil; dort Auswahltexte/Zäune und Routing prüfen,
keine Aufnahme der sieben Vertiefungs-Tools ins MVP. Ältere Aufträge oben zur
Rückkehr aller Tools ins Standardprofil sind insoweit durch den Entscheid 06.11. ersetzt.

1. Ist-Zustand im Vollprofil messen: `CHEMDRAW_PROFILE=full`, ein echter Aufruf über den Server;
   bei Panel-Tools zusätzlich das Panel in `test:host` (heute deckt `src/host/host.e2e.mjs` nur
   `generate_molecule` ab → je Panel-Tool einen Host-Fall ergänzen).
2. Befunde fixen, TDD (Test erst rot, dann grün).
3. Freischalten: Name in `MVP_TOOLS` · Eintrag in `_MVP_SUMMARIES` (Auswahltext ohne Verweis auf
   noch abgeschaltete Tools) · Zeile in `_MVP_INSTRUCTIONS` · `MVP`-Menge in
   `tests/test_server_profiles.py` · Handshake-Erwartung (`./scripts/handshake.sh`, Zahl leitet
   sich aus dem Profil ab — nach dem Lauf prüfen).
   **Rückwärtszäune der Nachbarn:** die `_MVP_SUMMARIES` von `generate_molecule`,
   `batch_generate`, `generate_reaction` (und jedem anderen Nachbarn) bekommen wieder ihre
   „Not this tool for: … (use <neues Tool>)"-Zeile — `test_server_profiles.py` prüft nur
   `mentioned <= MVP`, nicht dass der Zaun zurückkommt; je Zaun ein Test.
   **Mitwandernde Texte:** Satz „Other features are temporarily disabled" in `_MVP_INSTRUCTIONS`
   (bleibt für die sieben nur in `full` verfügbaren Tools zutreffend) · Testname `test_default_and_explicit_mvp_offer_exactly_seven_tools`
   · Zahlen „7 tools, 6 with a panel" in `CLAUDE.md` und README § Profiles.
4. Routing-Fall in `evals/tool-routing/cases.yaml` mit `expect` und `forbidden` (Regel dort: drei
   verschiedenartige Prompts je kritischem Tool); `tests/test_eval_cases.py` grün.
5. Tool-Snapshot bewusst segnen (`UPDATE_TOOLSNAPS=1 uv run pytest tests/test_tool_snapshots.py`)
   im selben Commit wie der Textwechsel; 2-KB-Grenze (`MAX_DESCRIPTION_BYTES`) bleibt grün.
6. README-Abschnitt mit echtem Bild aus einem echten Aufruf (kein Mock).
7. Codex-Handtest in Desktop per `tisch auftrag codex` (Prompt, Klicks, Erwartung je Schritt,
   Screenshots nach `/tmp/chemdraw-desktop-test/`); Gate `./test.sh` + `test:host` + Handshake grün.

**Rahmen, der für alle gilt**

- Toolzahl-Obergrenze: `tests/test_server_taxonomy.py:127` (`<= 23`). Die 16 Tools passen
  hinein; kein neues Tool in dieser Runde, sonst Grenze bewusst mit Begründung heben.
- Desktop nach jeder Server-Änderung neu starten (CLAUDE.md); Handshake ist der harte Beweis.
- Release-Kandidat je Etappe: Version heben, `.mcpb` bauen, Registry-Publish nicht vergessen
  (`./scripts/publish-registry.sh`); der Release-Klick bleibt Jays Hand.

**Messung 30.10.2026 (Vollprofil, `create_server("full")`)** — alle Modultests grün:

| Tool | Beschreibung | Panel | Modultests | Routing-Fälle (`expect`) |
|---|---|---|---|---|
| generate_3d | 614 B | ja | 5 grün (`test_structure3d`) + `test_server_anki` | **0** |
| generate_mechanism | 851 B | ja | 41 grün | 2 |
| generate_scope_table | 1964 B | ja | 57 grün | 1 |
| lookup | 1143 B | nein | 68 grün (databases + server_lookups/_lookup_ui) | 3 |
| predict_spectrum | 1349 B | nein | 32 grün (`spectro`) | 1 |
| generate_spectrum | 1606 B | ja | 36 grün | 1 |
| generate_tlc | 1833 B | ja | 37 grün | **0** |
| generate_titration_curve | 1167 B | ja | 19 grün (ph_plots + server_plots, mit species) | 1 |
| generate_species_distribution | 967 B | ja | (s. o.) | **0** |
| generate_calibration_curve | 1459 B | ja | 26 grün | 1 |
| generate_pk_curve | 1290 B | ja | 10 grün (`server_pk_plots`, mit dose) | 1 |
| generate_dose_response | 1125 B | ja | (s. o.) | 2 |
| calculate_solution | 2030 B | nein | 36 grün | 1 |
| calculate_ph | 1994 B | nein | 39 grün | 2 |
| calculate_content | **2041 B** | nein | 84 grün (calculator_* + server_content) | 1 |
| calculate_pharmacokinetics | 1803 B | nein | 35 grün | 3 |

Bekannte Baustellen aus der Messung:
- **2-KB-Kante:** `calculate_content` 2041 B, `calculate_solution` 2030 B, `calculate_ph` 1994 B,
  `generate_scope_table` 1964 B — unter 2048, aber jede neue Abgrenzungszeile kippt sie.
  Parameter-Doku kürzen, nie die Abgrenzung.
- **Routing-Lücken:** `generate_3d`, `generate_tlc`, `generate_species_distribution` haben keinen
  `expect`-Fall; alle übrigen nur 1–3, meist weniger als die geforderten drei verschiedenartigen.
- **Host-Test** kennt nur `generate_molecule`; die 12 Panel-Tools sind dort ungeprüft.
- `test_server_profiles.py` prüft `panel == MVP - {"save_png"}` — wächst automatisch mit, wenn
  die `MVP`-Menge gepflegt wird.
- Modultests grün heißt nicht „in Desktop richtig": Messung in Punkt 1 der DoD ist Pflicht.

Echte Aufrufe 30.10. (DoD 1, vor jedem Fix):
- `generate_mechanism`: zeichnet **immer** das feste Lehrbuchbeispiel des Templates
  (sn2: CH₃Br + OH⁻); nur der Titel übernimmt die Nutzer-Substrate. Beleg: `["CBr","[OH-]"]` und
  `["CCCCBr","[SH-]"]` liefern byte-gleiche SVGs, Titel „SN2: CCCCBr + [SH-]". Zwei
  Fehlermeldungen deutsch (`server.py` ~3479/3493). 12 KB Text ans Modell.
- `generate_3d`: Ibuprofen 0,5 s, 6,4 KB Text, `type: molecule3d` — sauber. Das Molekül-Panel hat
  **keine** 3D-Ansicht (Achse nur Skelett/All H/Fischer/Haworth, `MoleculeView.jsx:248`); das Tool
  bringt also den Chat-Weg und ist der einzige Weg zu 3D. Ein 3D-Knopf im Molekül-Panel (lazy wie
  All H) wäre eigene Arbeit — der 10-Sekunden-Test unten („3D klicken") setzt ihn voraus.
- `generate_scope_table`: 0,1 s, aber 36,7 KB Text ans Modell (Grid-SVG inline), wächst mit den
  Einträgen.

### Welle 1 — Reaktionen & Darstellung

> Geprüft 07.11.2026 (Plan-Audit): Belege in Klammern. Desktop-Handtests setzt nur Strang B.
> Alle drei Server-Commits sind in `v0.7.0` enthalten.

- [x] generate_mechanism Serverseite: ehrliche Lehrbuch-Galerie SN1/SN2/Fischer, englische Fehler,
  DoD 1–5 (`142e581`; `test_server_mechanism.py::test_title_names_the_textbook_example_when_it_falls_back`)
- [ ] generate_mechanism Desktop-Handtest → Strang B Schritt 2 (frühere Doku `998386d` liegt vor den **Stand 07.11.: Werkzeug + Argumente richtig, Desktop zeigt Rechte-Dialog „Always allow“ — Klick ist Jays Hand (`screenshots/06-sn2-rechte-dialog.jpg`)**
  Server-Änderungen vom 07.11.)
- [x] generate_3d Serverseite: Zäune ⇄ generate_molecule, 3 Routingfälle (`044e8d6`;
  `test_structure3d.py::test_methane_becomes_tetrahedral_with_hydrogens`,
  `test_server_profiles.py::test_mvp_neighbours_fence_towards_newly_enabled_tools`)
- [x] generate_3d Desktop-Handtest — belegt 07.11. 08:45, `generate_3d` gewählt, drehbares Kugel-Stab-Panel (`screenshots/07-3d.jpg`, Owner gesehen) → Strang B Schritt 3
- [ ] 3D-Knopf im Molekülpanel (lazy wie All H); heute nur Chat-Weg über `generate_3d`
  (fehlt: `chemdraw_tool/ui/src/MoleculeView.jsx:250-252` kennt nur Skelett/All H/Fischer/Haworth).
  Stereo-Klick ist **nicht** offen: „Show variants" seit 0.6.0 (`fd709cc`).
- [x] lookup Serverseite: KEGG exakter Name, englische Ausgabe, keine leeren Zeilen (`ed2dee2`;
  `test_server_lookups.py::test_lookup_pathway_takes_the_exact_name_not_the_first_fuzzy_hit`)
- [ ] lookup Desktop-Handtest → Strang B Schritt 9 **Stand 07.11.: Modell antwortete aus eigenem Wissen mit eigener Grafik, kein Werkzeug (`screenshots/13*`) → Routing-Fall**
  Notiert, nicht behoben: 6–10 s je Aufruf; ChEBI-Zeitüberschreitung erscheint als „No ChEBI entry
  found"; Familiennamen („xylene") → „not found" statt Isomerauswahl (lookup umgeht den Resolver).

### Welle 2 — Spektren & allgemeine Laborgrafik

- [x] predict_spectrum Serverseite: nimmt Namen über `resolve()` (`3945648`;
  `test_server_spectro.py::test_a_compound_name_is_resolved_instead_of_rejected`).
  Notiert: Ausgabe doppelt („3 signal(s) for 8 hydrogens" in Kopf und Bullet).
- [ ] predict_spectrum Desktop-Handtest → Strang B Schritt 4 **Stand 07.11.: Modell antwortete aus eigenem Wissen, rief kein Werkzeug (`screenshots/08*`) → Routing-Fall für `evals/tool-routing`**
- [x] generate_spectrum Serverseite: Transmission multipliziert, Exportknopf, eigener Auswahltext,
  `"IR"` groß/klein egal (`c6c847c`, `6ba60ca`, `cce71b0`;
  `test_spectrum.py::test_overlapping_strong_ir_bands_never_clip_to_zero`,
  `test_server_spectrum.py::test_spectrum_type_is_case_insensitive`)
- [x] generate_spectrum Desktop-Toolwahl — belegt 07.11. 08:47: Desktop wählte `generate_spectrum`, nicht `visualize` (`screenshots/09-spektrum.jpg`, Owner gesehen; Beschriftungen 1750/1690 überlappen) gegen eingebautes `visualize` (rot laut `0c36b4b`) → Strang B Schritt 5;
  nicht weiter an der Beschreibung drehen ohne Desktop-Messung. Notiert: 12–19 KB Modelltext.
- [x] generate_tlc Serverseite: englische Fehler, erster Zaun, 3 Routingfälle, Exportknopf
  (`90cfd7b`, `d6098a9`, Host `2c9a71a`; `test_tlc.py::test_error_messages_are_english`)
- [x] generate_tlc Desktop-Toolwahl — belegt 07.11. 08:47: `generate_tlc`, Rf 0,30/0,60 + Co-Spot (`screenshots/10-dc.jpg`, Owner gesehen) (rot laut `0c36b4b`) → Strang B Schritt 6.
  Notiert: Flecken 0,50/0,52 überdecken ihre Rf-Beschriftung; 8–16 KB Modelltext.
- [x] generate_titration_curve + generate_species_distribution Serverseite: absteigende pKa → Fehler,
  Pufferpunkte auf der Kurve, englische Fehler (`6093b88`, `a08e3cb`, Host `5eb9c43`;
  `test_server_plots.py::test_descending_pka_values_are_rejected`,
  `test_ph_plots.py::test_pufferpunkte_liegen_auf_der_kurve`).
  Notiert: 17–24 KB Modelltext; `notes` leer — EP-Volumen/-pH nur im Bild.
- [ ] Titration/Speziesverteilung Desktop-Handtest (zuletzt 0/4 laut `a6d6e86`) → Strang B Schritt 7 **Stand 07.11.: Werkzeug + Parameter richtig, Rechte-Dialog offen — Jays Klick (`screenshots/11-titration-rechte-dialog.jpg`)**
- [x] calculate_ph Serverseite (Jay 31.10.: Welle 2): Text-Tool, Zäune beidseitig, 16 Tools / 12 Panels
  (`71223ed`; `test_ph_calc.py::test_acetic_acid_matches_the_textbook_value`,
  `test_server_profiles.py::test_default_and_explicit_mvp_offer_exactly_the_mvp_tools`);
  README-Zeile und Bild (`README.md:60`, `assets/calculate-ph.png`)
- [ ] calculate_ph Desktop-Handtest → Strang B Schritt 8 **Stand 07.11.: Modell rechnete selbst (pH 2,88 richtig), rief kein Werkzeug (`screenshots/12*`) → Routing-Fall**
- Randnotiz: generate_molecule-Auswahltext bei ~2010 B — der nächste Zaun dort braucht Kürzung.

### Welle 3 — Vertiefung: zweiter Konnektor (nach 0.7.0)

**Ziel / Jay-Entscheid 06.11.2026:** Claude Desktop bietet zwei Konnektoren aus
demselben Serverpaket: `chemdraw` mit `CHEMDRAW_PROFILE=mvp` (16 Tools / 12 Panels)
und `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full` (23 Tools / 16 Panels).
Nach Einrichtung wechselt Jay im Konnektor-Menü des Chats ohne Desktop-Neustart.
Die erstmalige Registrierung/Installation ist davon getrennt abzunehmen.
**Grenzen:** nur zwei bestehende Profile, kein drittes Profil; MVP bleibt unverändert.
Umsetzung erst nach 0.7.0 (Reihenfolge Jay 02.11.; Release-Haken oben erfüllt).
Der Menüwechsel ist das gewünschte Verhalten, noch keine bestätigte Desktop-Abnahme.

**Abgleich 06.11.2026:** `create_server("mvp").list_tools()` und
`create_server("full").list_tools()` nachgezählt: **16 + genau 7 = 23**, MVP ist
Teilmenge von full. Die sieben Namen der Differenz sind exakt die sieben
Tool-Haken unten. `generate_mechanism` ist schon im MVP; Nutzersubstrate erweitern
dieses Tool und erhöhen die Toolzahl nicht. Deshalb entspricht MVP + Welle 3 dem
bestehenden `full`-Profil. Anthropic-Doku-Check: 0 neu / 0 geändert / 0 weg;
Paket-Nebenversionen separat gemeldet, keine Abhängigkeit hier verändert.

**Konnektoren einrichten und abnehmen (noch nicht gebaut):**

- [ ] `chemdraw_tool/desktop_config.py` + `install.sh`: zwei Einträge `chemdraw`
  (`env.CHEMDRAW_PROFILE=mvp`) und `chemdraw-pharma` (`full`) idempotent registrieren;
  absolute Startbefehle, Backup und fremde Server erhalten. Bestehendes `chemdraw-tool`
  kontrolliert migrieren, damit kein dritter ChemDraw-Eintrag bleibt.
  Prüfen: `uv run pytest tests/test_install_config.py tests/test_desktop_config_shipped.py`
  nach neuen Rot-Grün-Fällen für zweimalige Installation/Migration → zwei passende
  Einträge, fremde Einstellungen unverändert, grüner Lauf. (offen: `grep -rn chemdraw-pharma chemdraw_tool/ install.sh` leer; `desktop_config.py:33` nur `chemdraw-tool`)
- [ ] `.mcpb`-Weg: beide Konnektoren mit eindeutigen Extension-IDs und festem
  Profil installierbar machen; derselbe Server/Launcher, keine konkurrierende
  automatische Registrierung. Prüfen: `uv run pytest tests/test_mcpb_start.py`
  mit neuen Fällen für beide Profile → grün; echte Desktop-Installation → beide
  Konnektoren mit 16 bzw. 23 Tools, erster Start samt Launcher abgenommen. (offen: `mcpb/manifest.json` kennt ein Profil)
- [ ] `scripts/handshake.sh`: beide registrierten Konnektoren getrennt prüfen,
  erwartete Kataloge aus dem jeweiligen Profil ableiten, GUI-PATH beibehalten.
  Prüfen: `./scripts/handshake.sh` → zwei echte stdio-Handshakes, `chemdraw`
  16 Tools / 12 Panels und `chemdraw-pharma` 23 Tools / 16 Panels, Exit 0. (offen: kein zweiter Konnektor in `scripts/handshake.sh`)
- [ ] README-Abschnitt „Profiles“: beide Installationswege, zwei Konnektornamen,
  Profilwerte und Wechsel im Chat beschreiben. Prüfen:
  `rg -n 'chemdraw-pharma|CHEMDRAW_PROFILE|Profiles' README.md` → beide Konnektoren und
  Profilwerte erklärt; Schritte stimmen mit Desktop-Abnahme überein. (offen: `grep chemdraw-pharma README.md` leer)
- [ ] Desktop-Wechsel abnehmen: frischer Chat, `chemdraw` auswählen und
  Struktur zeichnen; im Menü zu `chemdraw-pharma` wechseln und `calculate_content`
  aufrufen; zurück zu `chemdraw`, Struktur zeichnen. Prüfen: Codex-Handtest mit
  Screenshots unter `/tmp/chemdraw-desktop-test/profile/` → passende Werkzeuge je
  Konnektor, erfolgreicher Hin-/Rückwechsel ohne Neustart; `./test.sh` +
  `npm --prefix chemdraw_tool/ui run test:host` → grün. (offen: setzt die vier Haken davor voraus)

**Vertiefungs-Tools und Erweiterung:**

- [ ] calculate_solution (offen: nur im `full`-Profil, Welle-3-Texte/Routing nicht begonnen)
- [ ] calculate_content (offen: nur im `full`-Profil, Welle-3-Texte/Routing nicht begonnen)
- [ ] calculate_pharmacokinetics (offen: nur im `full`-Profil, Welle-3-Texte/Routing nicht begonnen)
- [ ] generate_pk_curve (offen: nur im `full`-Profil, Welle-3-Texte/Routing nicht begonnen)
- [ ] generate_dose_response (offen: nur im `full`-Profil, Welle-3-Texte/Routing nicht begonnen)
- [ ] generate_calibration_curve (offen: nur im `full`-Profil, Welle-3-Texte/Routing nicht begonnen)
- [ ] generate_scope_table (36,7 KB Modelltext vorher verschlanken) (offen: kein Commit seit 30.10.)
- [x] generate_mechanism aus Nutzersubstraten: echte Mechanismen statt Lehrbuch-Galerie, je Familie SN1/SN2/Fischer mit Grenze (Merge `16fc11e`, in v0.8.0; `tests/test_mechanism_substrate.py`; `server.py:297-299`)

### README hochwertig (nach Welle 2)
- [x] Je Bereich (Zeichnen · Laborgrafik · Nachschlagen · Rechnen · Anki) ein echtes Bild aus einem
  echten Aufruf; Referenzteile nach `docs/` (`1f4cb10`; `README.md:69-95`, `scripts/readme_bilder.py`,
  `test_readme.py::test_skriptbilder_tragen_den_gesegneten_hash`)
- [ ] „Profiles" auf die zwei Konnektoren `chemdraw`/`chemdraw-pharma` aktualisieren — hängt an Welle 3
  (offen: `grep chemdraw-pharma README.md` leer; Profile heute nur `docs/tools.md:140`)
- [x] Installationsweg Desktop-Extension (`.mcpb`) zuerst, PyPI danach (`65800df`; `README.md:28-31`, `:99` vor `:103`)
- [x] Werkzeugtabelle: Bereich · Tool · Beispiel-Prompt · Panel (`65800df`; `README.md:44-60`,
  `test_readme.py::test_tooltabelle_nennt_genau_die_mvp_tools`)
- [ ] Danach Shorts je Workflow (Jay 26.10.) — Material und Plan im Schwester-Repo `chemdraw-vermarktung`
  (`plans/vermarktung.md` gibt es in diesem Repo nicht). Vorher README-GIF aus dem WIP `449ed3d` fertig aufnehmen.

## Doku-Aktualität bei jedem Release (Jay 06.11.2026, Tisch-Faden 20261106-102729-jay-06-11-readme)

- [x] Inventur (`9b1d8db`): mechanisch prüfbar = Toolnamen, Options-Parameter, `lookup`-Topics, Render-Stile, Panelzahlen je Profil,
  `CHEMDRAW_*`-Variablen, `chemdraw-*`-Befehle, Repo-Pfade, Identitätszahl (README, docs/tools|installation|development.md,
  CHANGELOG [Unreleased]); release-zeitig = Tag ↔ Version, datierter + gefüllter CHANGELOG-Abschnitt, leeres [Unreleased].
  Nicht mechanisch = ob Beschreibungen/Limitations noch stimmen, freie Zahlen („About 8,000 Python tests“).
- [x] `tests/test_docs_consistency.py` (Gate, 9 Tests, am 07.11. alle 9 grün): Identitätszahl rot gefunden (Doku 24, stoffe.json 25) → behoben;
  übrige 8 je per Mutation rot gesehen. `docs/development.md` 7,500 → 8,000 Tests (mit Codex abgestimmt, Faden #3).
- [x] `scripts/release_check.py` + `tests/test_release_check.py`; Job `check` in `publish.yml`, `build` hängt per `needs: check` daran (`test_release_check.py::test_unreleased_mit_eintraegen_ist_rot`; `publish.yml:21,34`).
- [x] Checkliste 1a (Opus-Sichtung README+docs gegen `git diff <letzter Tag>..HEAD`) in `docs/registry-publish.md`
  § Release-Reihenfolge, per Test verankert (`docs/registry-publish.md:114`).
- Hinweis: `release_check.py` ist heute rot (rc=1), weil [Unreleased] Einträge hat — beim nächsten Release erst verschieben.

> Fokusentscheidung 14.10.2026: erst den allgemeinen Chemie-Kern stabilisieren.
> MVP als Standard: Einzelstrukturen, Batch, Vergleich, Reaktionsschema; Datenblatt
> und PNG-Export als Unterstützung (6 Tools). `CHEMDRAW_PROFILE=full` schaltet den
> erhaltenen Vollumfang wieder zu. Die Ausbauphasen unten bleiben dokumentiert,
> sind aber bis zur Abnahme des Kerns zurückgestellt. Keine weitere Fachvertiefung,
> Quiz-/Trainer- oder Bezahlfunktionen in dieser Etappe.
>
> Umgesetzt 14.10.: Profilumschaltung und passende Tooltexte, getrennte Tests für
> MVP und Vollbestand, profilabhängige Routing-Evals. Gate: 6.953 Python-Tests,
> 37 Frontendtests grün; Host-Test grün. Lokale Bundle-Installation aus dem
> aktuellen Wheel aktualisiert, Desktop neu gestartet; echter Extension-Start:
> 6 Tools / 5 Panels, installiertes Vollprofil: 23 Tools. Noch kein neuer öffentlicher
> Release. Sichtbarer Abnahmeschritt: neuer Desktop-Chat → „Nutze den ChemDraw-MCP:
> zeichne Koffein“ → Data → PNG-Export. Die Fehler aus
> `docs/projektpruefung-2026-10-14.md` sind damit noch nicht behoben.
>
> Unabhängig nachgeprüft 14.10. nach Claudes Kernpflege (`e17eb61`, `243b1e5`):
> Gate 6.958 Python / 37 Frontend grün, Host grün, Identität 22 grün / 2 gelb.
> Nullwerte korrigiert; PubChem-URL-Umstellung ist eine Bereinigung (alte Aliase
> antworten live weiterhin mit 200). Lokales Desktop-Wheel anschließend aus dem
> geprüften Repo aktualisiert, isoliert auf Codegleichheit und Nullwerte geprüft;
> Desktop neu gestartet. Einzelheiten und Grenzen im Prüfbericht.

> Zusammengelegt 08.10.2026 aus `plans/archiv/panel-ausbau.md` (03.10.) und dem MCP-Teil von
> den privaten Produktplan (`leben/plans/chemdraw-produkt.md`) (02.10.). Frühere, abgeschlossene Etappen: `plans/archiv/repo-level-up.md`
> (14.08.), `routing-und-umschalter.md` (15.08.), `studi-funktionen.md` (15.08.).
> Gate je Schritt: `./test.sh` grün · `npm --prefix chemdraw_tool/ui run test:host` · `./scripts/handshake.sh`.
> Vor Panel-/Manifestarbeit: `uv run python scripts/anthropic_sync.py --check` (CLAUDE.md).

## Aus dem Verlauf übernommen (07.11.2026)

- [ ] Kann: gemerkter Offline-Zustand im Resolver (nach Verbindungsfehler ~60 s keine Gegenfrage) spart 3 s im Blackhole-Fall (offen: kein Zeitspeicher in `chemdraw_tool/resolver.py`; aus Archiv „Masse-Eval-Befund 1")
- [~] Masse-Eval-Langschwanz (14 rot von 711, alle Stereo) — gestoppt 07.11.2026 (Jay, siehe „Stand für Jay"); Belege `docs/evidence/masse-eval-2026-11/lauf-12-vergleich.json`

## Etappen
> Geprüft 07.11.2026 (Plan-Audit). Belege je Haken in Klammern oder in `docs/evidence/verifizierter-stand-2026-11-07/plan-audit.md` (Spalte „Z." = Zeile im alten Plan `feef949`). Blockweise erledigt: Etappe 14.10. (`adccc04`, `c0dd24d`, `20c204f`), Etappe 02.10. (Tags `v0.4.3`–`v0.4.8`).

- [~] **Geparkt (Chef 31.10.2026: nicht löschen):** von der README (`65800df`) nicht mehr verwendete Assets — überholt 07.11.2026: die sieben Dateien wurden am 04.11. gelöscht (`dde25d3`, Etappe C); Git-Historie hält sie.

### Etappe 14.10.2026: vorhandene MVP-Oberfläche autonom verbessern

- [x] Molekül- und Datenblattlayout lesbar, schmal gestapelt, breit mit eigener
  Informationsspalte; klare Exportbeschriftung, Hostschrift und Hosttheme.
- [x] Funktionelle Gruppen per Tastatur bedienbar; Molekülwechsel verwirft das
  fremde Datenblatt. Drei neue DOM-Regressionen zuerst rot, dann grün.
- [x] Unabhängige Abnahme: `./test.sh` mit 6.958 Python- und 40 Frontendtests grün;
  `test:host` prüft Struktur und Datenblatt hell/dunkel bei 360/980 px sowie
  explizite Host-Themes. Default-Pixelreferenz unverändert.
- [x] Lokales Wheel installiert und Bundle-Codegleichheit geprüft; Desktop
  neu gestartet; neuer Chat `132254e1-49e3-41b1-8bba-5f79198cae7e` zeigt Koffein,
  HBD 0 und Datenblatt mit CAS 58-08-2/CID 2519. Exportknopf bestätigt
  `~/ChemDraw-Output/png/Koffein-2.png`; Bild pixelgleich zur Ausgangsabnahme.
- [x] Automatische DOM-Schleife `test:ui:watch` ergänzt; Entwickleroptionen,
  Logs und Prüfschichten in `docs/ui-pruefung.md` dokumentiert. DevTools nicht
  ungefragt aktiviert. Layoutbelege: `docs/produkt/panel-mvp/`.
- [x] Anschließend auf Jays ausdrücklichen Auftrag DevTools aktiviert; neuer
  Entwickler-Menüpunkt und geöffnetes DevTools-Fenster mit Console/Network selbst
  sichtbar geprüft. Die Konfiguration liegt lokal außerhalb des Repositories.

- [ ] **Routing-Befund MVP (Claude, 14.10., `run_claude.py`, 11/13 grün):** (offen, braucht API; Fall `evals/tool-routing/cases.yaml:232-235`) zwei Fälle
  3 von 3 stabil rot — `lookup-data-sheet` ruft nach `lookup_molecule_data` zusätzlich
  das verbotene `generate_molecule`; `explain-why-acidic` („Warum ist Acetylsalicylsäure
  sauer?“) landet bei `generate_reaction` statt `generate_molecule`. Betrifft
  `_MVP_SUMMARIES`/Instructions; erst nach dem mcp-2-Branch angehen (Konfliktgefahr).
  **19.10.:** `explain-why-acidic` grün (Eigenschaftsfrage zu einem Stoff → generate_molecule,
  Zaun in generate_reaction); Gesamtlauf 12/13. `lookup-data-sheet` blieb nach drei
  Formulierungen (Summary beider Tools + Instructions) rot und ist zurückgenommen.
  Vermutung: Die Attrappe in `stub_server.py` liefert kein Datenblatt, also zeichnet das Modell
  nach. Prüfen mit einem Stub, der echten Datenblatt-Text zurückgibt.
- [x] **mcp-2.x-Migration** (14.10., `c0dd24d` auf main): `MCPServer`, `version=` im
  Konstruktor, `ValueError` → `ToolError` (Resolver-Meldungen kommen lesbar an, Test neu).
  Lokal nachgeprüft nach Rebase: Gate 6.964 grün, `test:host` grün, Routing 11/13 wie vorher,
  Handshake 6/5. Lief NICHT in der Cloud: `isolation: remote` fiel still auf einen lokalen
  Worktree zurück. Offen: Desktop-Wheel neu installieren + Smoke-Test; Entscheidung, ob
  auch andere Fehler (z. B. `OSError` beim Schreiben) als Klartext durchgereicht werden.
- [ ] Desktop-Entwicklermenü „MCP-Konfiguration neu laden“ ersetzt per AppleScript einen (offen, nur in Desktop messbar)
  von zwei laufenden Serverprozessen (57152 → 63588, 57194 blieb). Vor einem Reload-Skript
  klären, welcher Prozess einen neuen Chat bedient.
- [x] SMILES-Dateinamen-Kollisionen behoben (20.10., `20c204f`): Großschreibung und
  Stereopunktuation bleiben durch einen stabilen Fingerabdruck unterscheidbar, für
  Einzel- und Batch-Export in PNG/SVG/CDXML. Zwölf Regressionen erst rot, dann grün;
  Gate 6.976 bestanden / 16 übersprungen. Explizit gleiche Labels bleiben überschreibbar.
- [ ] Offen aus der Kernanalyse: ACS-1996-Stil nur nach Designrunde (offen). Erledigt daraus: NCI-500 zählt als unbekannt (`cc13e47`), deutsche Trivialnamen (`abee1a5`, `tests/test_de_names.py`); Wikidata-Stufe damit nicht mehr nötig. Alter Text: NCI CIR antwortet live
  mit 500 auf deutsche Namen (Methylphenidat, Salicylsäure) → Kandidat Wikidata-Stufe;
  ACS-1996-Stil nur nach Designrunde.

Noch offen bleibt die persönliche Gestaltungsrückmeldung von Jay; weitere
Panelmodi und Fachfunktionen sind damit nicht freigegeben.

### Etappe 03.10.2026: Panel-Ausbau — Ansichten, Animation, Abfrage- und Prüfungsmodus

Ziel: Das Moleküle-Panel wird vom Bild zum Lernwerkzeug. **Eine** Molekülanfrage liefert alle Ansichten, man schaltet sofort um, wird durch die Optionen geführt, und kann sich selbst abfragen.

Stand 08.10.: außer M0 und der Recherche W-1c ist nichts davon gebaut (geprüft: keine `readOnlyHint`, kein `svg_stereo`, kein `mode="quiz"`, kein Bundle-Budget-Test im Code).

#### Wow-Moment zuerst (Fokusänderung 03.10. abends — gilt vor den Phasen unten)
Jay: erst das Layout im Chat, Ansichten ohne Nachfragen umschaltbar, **allgemein** für alle, die es auf GitHub ausprobieren (Chemie, Pharmazie, Biologie). Liste aller Möglichkeiten: `docs/produkt/panel-moeglichkeiten.md`.

- [ ] **M3** alle 23 Werkzeuge mit `title` und `readOnlyHint` annotieren (Snapshot-Tests mit freigeben) — offen: `grep readOnlyHint chemdraw_tool/server.py` leer; `docs/anthropic/abgleich.md:35` „✗ 0 von 23"
- [ ] **M2** Größen der Panel-Ergebnisse messen (Grenze ~150.000 Zeichen, sonst lädt das Panel nicht), Großes nachladen (offen: kein Messtest gefunden)
- [ ] **M7** Manifest: Icon (512 px), `privacy_policies`, Windows testen oder ausschließen; **M8** README: Organisationen können Extensions sperren — fehlt: `abgleich.md:35-36` (Windows ausgeschlossen: `mcpb/manifest.json:28`; Icon/`privacy_policies` offen)
- [ ] W-1 Nativer Look: Host-Farben/-Schrift (`--color-*`, `--font-sans`) statt eigener Tokens, Skelett statt Spinner, Tippflächen ≥ 44 pt (Baustein 13) (teilweise: `styles.css:4-8` nutzt Host-`--color-*`; Spinner statt Skelett offen)
- [ ] W-1b Quiz-Satz in den `instructions` + Eval-Fall (Baustein 14) (offen: `_MVP_INSTRUCTIONS` `server.py:285-319` ohne Quiz)
- [ ] W0 Host-Messung: Zeile im Panel „Claude Desktop · Vollbild · Nachricht · Download …" (1 h) — entscheidet über W4, Phasen 5, 6
- [ ] W1 Reiter **Struktur · Stereo · 3D · Daten** von Anfang an (= Phase 1 unten) (teilweise: Skelett/All H/Fischer/Haworth `MoleculeView.jsx:250-252`, Stereo „Show variants" `fd709cc`, Data vorhanden; Rest: 3D)
- [ ] W2 3D dreht sich von selbst, weicher Wechsel (Teil von Phase 4 vorgezogen) (offen: keine Autorotation in `Molecule3DView.jsx`)
- [ ] W3 **Browser-Demo ohne Installation**, Link ganz oben im README (Hebel für Sterne)
- [ ] W4 je nach W0: Atom anklicken → Claude erklärt · Vollbild + Download · Folge-Vorschläge
- [ ] W5 README neu aufbauen um den Wow-Moment (GIF der Reiter, Demo-Link) — erst nach W1–W3, sonst verspricht es Ungebautes
- [ ] W6 danach: Blind-Modus, Prüfmodus (Phasen 5–6), Biologie-Paket, Wirkstoffklassen-Galerie
- [x] **M0** `ext-apps` 2.0.3 migriert (ac13350, 1bacd64): keine Codeänderung im Panel, Bundle 524 → 399 kB, Gate/Host-Test/Handshake grün; MCP-Fassung 2026-07-28 gelesen, nichts zu tun (`docs/anthropic/abgleich.md` §1)
- [x] W-1c Recherche: Anthropic-Verzeichnis, geht ein lokaler Server? (bcf3286, `docs/anthropic/abgleich.md:38-50`: lokal nicht als Connector einreichbar, .mcpb nicht mehr angenommen, Weg wäre Plugin-Bundle)

#### Phase 0 — Grundlage und zwei Versuche (ca. 1 Stunde)
- [ ] Ausgangsbilder: `tests/gallery_ui.py` als Vorher-Stand ablegen (`docs/produkt/panel-vorher/`) (offen: Ordner fehlt; `docs/produkt/panel-mvp/` ist der Stand 14.10.)
- [ ] Versuch 1: Kann das Panel dem Chat eine Nachricht schicken (`ui/message` der AppBridge)? Im Host-Test prüfen, dann **einmal in Desktop von Hand** — davon hängt D (Folge-Vorschläge) ab
- [ ] Versuch 2: Panelhöhe in Desktop messen (wie viel Platz bleibt unter dem Chat-Text?) — davon hängt das Layout in C ab
- [ ] Bundle-Budget als Test: `dist/index.html` ≤ 650 kB, rot sonst (offen: kein Test; `dist/index.html` am 07.11. 447.645 B)

#### Phase 1 — Ansichtsumschalter (A) → Release 0.5.0
- [~] Payload: `MoleculePayload` bekommt `svg_stereo` und `mol3d` — für Stereo überholt durch Lazy-Entscheid in `fd709cc` („Show variants" lädt nach); `mol3d` bleibt Teil des 3D-Knopfs (Welle 1)
- [ ] Panel: Reiter **Struktur · Stereo · 3D · Daten**; 3D-Ansicht als wiederverwendbare Komponente (aus `Molecule3DView` herausgelöst, gleiche Drehung) (Rest: 3D, siehe Welle 1)
- [ ] Tests: Host-Test klickt durch alle vier Reiter; Komponententest je Ansicht; Payload-Parität (Python ⇄ App.jsx) (teilweise: Host klickt Show variants `host.e2e.mjs:390`, Fischer/Haworth `:425`, Data `:344-349`; 3D fehlt)
- [x] 10-Sekunden-Test — belegt 07.11. 08:38–08:40: Show variants → (R) → Data CAS 51146-57-7 → Export PNG → Anki-Import-Dialog (`screenshots/01…05`, `desktop-handtest.md`) „Zeichne Ibuprofen" → Stereo (Show variants) → Data: geht an Strang B Schritt 1 (Codex-Screenshots), nicht an Jay; 3D-Schritt erst mit 3D-Knopf

#### Phase 2 — Seitenpanel und Layout (C) → 0.5.1
- [ ] Gestaltungsgrundsätze in `styles.css` als Tokens (Abstände, Schriftgrößen, Kartenstil), nicht pro View (teilweise: `--radius*`, `--shadow-card` in `styles.css:12,190`; Abstände/Schriftgrößen fehlen)
- [ ] Steckbrief: einklappbare Abschnitte, klarere Hierarchie, Kopierknöpfe einheitlich
- [x] Schmal/breit: Seitenleiste wird unter 620 px (Plan: 560) ein Block unter dem Bild (`adccc04`; `styles.css:260`, `host.e2e.mjs:325`)
- [ ] Hell/dunkel prüfen (erledigt: `host.e2e.mjs:309-365`); Galerie vorher/nachher nebeneinander ansehen (offen)

#### Phase 3 — Geführte Optionen (D) → 0.6.0
- [ ] Optionsleiste: Stil (kompakt / Präsentation / Graustufen), Stereo-Beschriftung, Gruppen abkürzen — Änderung ruft das Werkzeug erneut auf (`callServerTool`), Ergebnis ersetzt das Bild
- [ ] Folge-Vorschläge unter der Struktur („Mechanismus", „Vergleichen mit …", „Karteikarte") — **nur wenn Phase-0-Versuch 1 klappt**, sonst als kopierbarer Prompt
- [ ] Eval: Tool-Wahl-Fälle unverändert grün (28/28 Basis), Beschreibungen nicht länger (nicht prüfbar ohne API)

#### Phase 4 — Animationen (B) → 0.6.1
- [ ] 3D: Dauerdrehung mit Pause/Weiter, stoppt bei Ziehen, respektiert `prefers-reduced-motion`, pausiert, wenn das Panel nicht sichtbar ist
- [ ] Weiche Übergänge beim Ansichtswechsel (kurz, abschaltbar)
- [ ] Mechanismus: Schritte automatisch durchlaufen (Schleife, Tempo einstellbar) (offen: `MechanismView.jsx:292` nur Overview/Step by step)
- [ ] Messung: Bildrate bei 50 Atomen ≥ 30 fps, sonst automatisch weniger Details

#### Phase 5 — Abfragemodus (E) → 0.7.0
- [ ] `mode="quiz"` im Werkzeug; Panel zeigt die Struktur mit abgedeckten funktionellen Gruppen
- [ ] Klick deckt auf; „Wusste ich / Wusste ich nicht" pro Gruppe; Zähler
- [ ] Varianten: Name verdecken, Gruppen verdecken, nur Gerüst zeigen
- [ ] Tests: Abdeckung deckt genau die Atome der Gruppe; Aufdecken ist umkehrbar; Zustand nur im Panel (kein Server)

##### Entwurf „Prüfungsfragen OC-Grundlagen“ (26.10.2026, nur Entwurf — Jay gibt je Etappe frei)
**Pausiert (Jay 26.10. 23:55): zuerst die Shorts sauber, je Workflow ein Short (plans/vermarktung.md § Shorts je Workflow).**
Rahmen: Jay 26.10. OC-Grundlagen zuerst (funktionelle Gruppen, Isomerie, R/S, Reaktionstypen); MVP bleibt 7 Tools →
Parameter oder Panel-Knopf, kein achtes Tool. Ausgangspunkt ist Modus E (verdecken, aufdecken).

Was schon da ist (Bestand 26.10.):
- `MoleculePayload.functionalGroups` (`name`, `atomIndices`, `count`; SMARTS-Liste in `svg_renderer._FUNCTIONAL_GROUPS`
  plus „Aromat“, Namen deutsch; gemessen: Aspirin → Carbonsäure, Ester, Aromat) + `atoms` (`AtomData` idx/x/y) → genau das, was Abdecken braucht; `StructureCanvas` hebt
  per `groups`/`highlightAtoms` schon Atomlisten hervor, `FunctionalGroupList` listet sie.
- Isomerie: `AmbiguousPayload.candidates` (Isomer-Auswahl, 0a1d29a) und `stereo_variants` (max. 3 Stereoisomere als
  Auswahl) liefern fertige Antwortmengen für „welches Isomer ist das?“.
- R/S: `stereoWarnings` kennt nur **offene** Zentren; CIP-Labels der bestimmten Zentren stehen nur in der Zeichnung
  (`annotate_stereo`), **nicht** als Daten im Payload → für R/S-Fragen fehlt ein Feld (z. B. `AtomData.cip`).
- Reaktionstypen: `ReactionPayload` + `balance`; kein Typ-Etikett (Substitution/Addition/…) vorhanden.
- Abfrage-Ausgang: `export_anki_deck` + `curated_decks` (2 Decks, `VERIFIED_STRUCTURES` mit Formel-Gate) →
  „Falsch beantwortet → Karteikarten“ ohne neuen Server-Weg; `AddToAnkiButton` im Panel.

Bauvarianten:
- **A (Empfehlung) — Panel-Knopf „Quiz“ am Molekül-Panel, kein neuer Parameter.** Jede `generate_molecule`-Antwort
  kann abgefragt werden: Klick „Quiz“ deckt alle `functionalGroups` ab (graue Flächen über `atomIndices`), Klick auf eine
  Fläche → Auswahl aus 3–4 Gruppennamen (Distraktoren aus der SMARTS-Liste), dann Aufdecken. Zustand nur im Panel.
  Vorteil: null Änderung an Tool-Text/Snapshots/Evals, Daten liegen schon im Payload, sofort für jedes Molekül.
  Nachteil: Lernender muss erst „Zeichne X“ sagen; keine Fragenfolge.
- **B — Parameter `mode="quiz"` an `generate_molecule`** (wie Phase 5 geplant): Modell kann „frag mich Aspirin ab“
  direkt ins Quiz schicken, Panel startet abgedeckt. Kostet: Beschreibungsänderung (Snapshot neu segnen,
  Eval-Fall für „frag mich ab“ vs. „zeichne“), Routing-Risiko gegen `export_anki_deck`.
- **C — Fragenbestand als Datendatei + `curated_deck_id`-artiger Schlüssel** (`oc-grundlagen-1`: 15–20 geprüfte
  Lehrbuchmoleküle je Thema, Formel-Gate wie `VERIFIED_STRUCTURES`), abgespielt über `batch_generate` oder A/B.
  Eigentliche Fragenfolge (= Phase F). Groß; erst sinnvoll, wenn A sich im Gebrauch bewährt.
Reihenfolge: **A → (B, nur wenn Jay „frag mich ab“ im Chat will) → C**. Themen in A-Reihenfolge: funktionelle Gruppen
(Daten da) → Isomerie (Kandidaten da) → R/S (braucht `cip`-Feld) → Reaktionstypen (braucht Typ-Etikett, zuletzt).

**Voraussetzung A0 (Inhaltsfehler, vor jedem Quiz):** `extract_functional_groups` meldet bei Paracetamol
`['Amid', 'Sek. Amin', 'Phenol', 'Aromat']` — der Amid-Stickstoff zählt zusätzlich als sekundäres Amin. Im Panel ein
Schönheitsfehler, im Quiz falscher Lernstoff. Fix: Amin-SMARTS ohne Carbonyl-Nachbar (`[NX3H1;!$(NC=O)]…`), Test mit
Paracetamol/Lidocain zuerst rot; Golden-SVGs prüfen (Gruppen färben nur im Panel, Export vermutlich unberührt).

Erste prüfbare Etappe (A1, Vorschlag): Knopf „Quiz“ im Molekül-Panel, deckt alle funktionellen Gruppen ab, Klick deckt
eine auf (noch ohne Antwortauswahl), „Alle zeigen“ setzt zurück.
- Tests zuerst: Komponententest „Abdeckung = genau die `atomIndices` der Gruppe“, „Aufdecken umkehrbar“, Molekül ohne
  Gruppen → Knopf fehlt; `test:host` klickt Quiz bei Aspirin (3 Gruppen) durch. Bundle-Budget bleibt ≤ 650 kB.
- Kein Python-Code, kein Tool-Text, keine Golden-SVG berührt → Gate + Host-Test + Codex-Desktop-Test.
- 10-Sekunden-Test: „Zeichne Aspirin“ → Quiz → drei graue Flächen → eine anklicken → „Ester“ erscheint.
- [ ] **Jay:** Freigabe A1 (oder Variante B/C zuerst)? — zurückgestellt, nicht veraltet: pausiert 26.10. für Shorts, Basis-Ausbau 30.10. ohne OC-Fragen, Jay 07.11. „zunächst nur Moleküle". Erst nach Welle 3/README stellen.

#### Phase 6 — Prüfungsmodus (F) → 0.7.1
- [ ] Fragenfolge (N Strukturen), Fragetypen: Gruppen benennen, Name zur Struktur wählen, Stereozentren zählen/bestimmen (R/S)
- [ ] Kein Hinweis während der Prüfung, Auswertung nach Bereich (wie der Klausurmodus im Rechner)
- [ ] Fehler → Anki-Deck mit den falsch beantworteten Strukturen
- [ ] Optional: Zeitlimit

#### Phase 7 — Abfragemodus für Reaktionen/Mechanismen (Jay 07.11.2026)
- [ ] Nach dem Molekül-Abfragemodus: Reaktionen/Mechanismen ergänzen (Edukte verdecken). Keine Umsetzung in Phase 5.

#### Offene Fragen an Jay
- [x] **Jay:** Welche Fachrichtung für die Prüfungsfragen zuerst: **Pharmazeutische Chemie** (Strukturen, funktionelle Gruppen) oder **Pharmakologie** (Wirkstoffklassen)? Empfehlung: Pharmazeutische Chemie — die Daten dafür gibt es schon.
  - **Jay 26.10.2026: OC-Grundlagen zuerst** (funktionelle Gruppen, Isomerie, R/S, Reaktionstypen) — breiteste Zielgruppe (Chemie, Bio, Medizin, Pharmazie, Schule), passt zu „Grundlagen zuerst“. Pharmazeutische Chemie danach als Aufbau, Pharmakologie zuletzt.
- [x] **Jay 07.11.2026, beantwortet:** Abfragemodus zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7 (Edukte verdecken).

#### Grundlagen der Etappe (unverändert vom 03.10.)

| # | Gedanke | Kern | Baut auf |
|---|---|---|---|
| A | Zwischen Ansichten umschalten (Stereo, 3D, …) | ein Payload, mehrere Ansichten, Umschalter im Kopf | — |
| B | Animationen, auch zum Schleifen | 3D-Dauerdrehung, weiche Übergänge, Mechanismus-Autoplay | A |
| C | Seitenpanel feiner und sauberer | Layout-Grundsätze statt Einzelfall-Styles | A |
| D | Durch die Tool-Optionen geführt werden | Optionsleiste (Stil, Stereo-Labels, Abkürzungen) + Folge-Vorschläge | A, C |
| E | Abfragemodus (Teile verdecken, aufdecken) | Funktionelle Gruppen/Atome abdecken, Klick deckt auf | A, C |
| F | Prüfungsmodus | feste Fragenfolge, kein Hinweis, Auswertung, Fehler → Anki | E |

Reihenfolge der Phasen: **A → C → D → B → E → F.**

Messungen (03.10.): 3D-Erzeugung kostet 10–30 ms je Molekül → alle Ansichten kommen gleich im Payload mit, nur das Datenblatt (PubChem, ~2 s) lädt beim Klick. Das Panel kennt schon `functionalGroups` mit `atomIndices` und `AtomData` mit x/y. 3D bleibt SVG-Drehlogik, kein WebGL. Bundle heute **399 kB** (nach M0, CHANGELOG.md:14; am 03.10. noch 524 kB); Budget für den ganzen Ausbau **≤ 650 kB**.

Entscheidungen (Jay kann widersprechen): 1. Ansichten mitliefern, nicht nachladen. 2. Stereo-Ansicht = dieselbe Struktur mit CIP-Beschriftung, `annotate_stereo` bleibt. 3. Abfrage- und Prüfungsmodus sind Panel-Modi über ein Argument `mode`, keine neuen Werkzeuge. 4. Fehler aus dem Prüfungsmodus gehen als Anki-Deck raus (`export_anki_deck`).

Für jede Phase: Tests zuerst und einmal rot gesehen · `./test.sh` grün · Host-Test und Galerie angesehen · CHANGELOG · README-Bild aktualisieren, wenn sich das Aussehen ändert · Release erst nach Jays Go.

### Etappe 02.10.2026: MCP verfeinern und Releases 0.4.3–0.4.8 (aus den privaten Produktplan (`leben/plans/chemdraw-produkt.md`))

- [ ] Desktop „Zeig mir Methylphenidat" → Data — Beleg liegt vor, Haken setzt Owner/Strang B: Host `host.e2e.mjs:344-349` (`5f58b5c`), Server `docs/evidence/verifizierter-stand-2026-11-07/werkzeug-probe.log:37-38`, Desktop-Screenshot `/tmp/chemdraw-desktop-test/2026-11-07/04-methylphenidat-data.png` (07.11. 07:31: CAS 113-45-1, CID 4158). Nicht mehr Jays Hand (Handtest → Codex, CLAUDE.md).
- [~] `mcp-2-migration` (Worktree `.claude/worktrees/agent-a567114bbee585cc8`, Branch-Stand 836324b vom 02.10.) — überholt 07.11.2026: Umstellung liegt auf main (`c0dd24d`, 14.10., v0.5.0); Worktree und beide Branches weg (`git worktree list`, `git branch -a`), alter Stand als Tag `archiv/mcp-2-migration`. Alter Text: GEPARKT bis zum Desktop-Test.
  - (überholt, s. o.) Zusätzlich lag auf GitHub `mcp-2-migration-v2`: Branch gelöscht, Commit `dd932f6` noch erreichbar (nicht auf main).
- [ ] Hinweis in `_INSTRUCTIONS`/README: Desktop nimmt die Sandbox, wenn man den MCP nicht nennt — prüfen, ob ein Satz in `instructions` das ändert (nur in Desktop messbar). Offen: `chemdraw_tool/server.py:285-319` (`_MVP_INSTRUCTIONS`) enthält keinen solchen Satz
- [ ] Geschwindigkeit (zurückgestellt): Server-Import 1,4 s (mcp 0,33 · rdkit 0,25 · matplotlib 0,25) — nur lazy laden, wenn die Handshake-Zeit unter Last wehtut; Datenblatt-Ladezeit 2,3 s (PubChem) — Vorabladen nur, falls Jay es spürt
- [~] Option: Server-Import ohne RDKit/matplotlib — gestrichen 08.10.2026, weil Dublette des Geschwindigkeits-Hakens darüber
- [x] 0.4.6 veröffentlichen: PyPI, `.mcpb`, bei Jay installiert (v0.4.6 GitHub-Release 03.10., 20ff181; PyPI steht inzwischen auf 0.4.8; `dist/chemdraw-mcp-0.4.8.mcpb`; Desktop-Test 03.10. mit 0.4.7 verbunden) — Tag `v0.4.6` zeigt auf `1bfedb2`
- [x] **Jay:** `gh release create v0.4.6` (`gh release list`: v0.4.6 am 2026-10-03)
- [x] Run.sh-Sperre verwaist bei abgebrochener Installation: trap auf TERM/INT/HUP, PID-Datei, tote PID sofort übernehmen (Release 0.4.6, 20ff181)
- [x] Bundle-Startfix: feste Installation statt `uv tool run` (adaed6c)
- [x] Release 0.4.3 (Titer, Daten-Knopf, Bundle-Start + Sperre) und 0.4.4 (Index-Refresh im Bundle), 02.10.
- [x] OPSIN gemergt (022507d), 0.4.5 veröffentlicht (3681f7b) und bei Jay installiert (Desktop verbunden 21:36, 20 Tools)
- [x] Data-Knopf Methylphenidat automatisiert: `npm --prefix chemdraw_tool/ui run test:host` (AppBridge-Host + echter Server, 02.10.). Computer use auf die Claude-Desktop-App selbst ist gesperrt
- [x] Messung: `evals/tool-routing/run_claude.py` (Tool-Wahl über claude -p, Attrappen-Server) — 24/28 → 26/28
- [x] `lookup_molecule_data`: 6–8 Folgeaufrufe → 4 bei „Datenblatt mit allem" (237698f)
- [x] `test:host` schreibt nicht mehr ins echte `~/ChemDraw-Output` (9a3b8d6)
- [x] Entschieden (02.10.): `reaction-in-conversation` — Reaktion + Mechanismus ist gute Antwort, `forbidden` nur noch generate_molecule; `draw-scope-real` mit Strukturen im Prompt. Eval 28/28 in drei Wiederholungen (0e39eb0)
- [x] Dateipfade im Panel mit `~` gekürzt (6 Views), Tooltip hat den vollen Pfad (6c9b308)
- [x] Design-Galerie: `uv run python tests/gallery_ui.py` → <Temp-Ordner chem-gallery-*>/sheet.png (13 Panel-Typen nebeneinander) (6c9b308)
- [x] Speziesverteilung: Legende neben der Achse (6763642, Test rot gesehen)
- [x] Geprüft, kein Fehler: Kalibrierkurve-Titel doppelt (der Titel im Bild gehört in die exportierten Dateien); Reaktion ohne Titel (Edukte/Produkte/Bedingungen sind beschriftet)
- [x] Mechanismus-Overview: gleiche Bindungslänge, Spalte statt Zeile, SN2-TS mit Platz für Teilbindungen (1bfedb2, Release 0.4.7)
- [x] Desktop-Test 03.10.: 0.4.7 verbunden, `generate_pk_curve` kam an, Zahlen stimmen (Css,av 4,74 mg/L, R 1,43). Desktop lädt MCP-Tools erst nach und nimmt sonst die Sandbox — Prompt mit „Nutze den ChemDraw-MCP" wirkt
- [x] Dateinamen von `generate_pk_curve`/`generate_dose_response` tragen ohne `drug` die Parameter (64a0cb8)
- [x] (0.4.8) Gleiches Überschreiben bei TLC, Scope, Kalibrierkurve, Reaktion ohne Titel und bei Titration — Dateiname aus den Eingaben ableiten, je mit Test (5c77bc5)
