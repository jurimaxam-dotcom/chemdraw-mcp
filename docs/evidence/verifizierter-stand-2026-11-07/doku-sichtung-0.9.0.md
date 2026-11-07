# Doku-Sichtung vor Release 0.9.0 (07.11.2026, Pflichtschritt 1a)

**Urteil: nein, nicht release-fähig.** Grund: eine sichtbare Ausgabe hat sich geändert (CAS von Ibuprofen 58560-75-1 → 15687-27-1) und fehlt im CHANGELOG, ebenso pH außerhalb 0–14, neue IR-Regeln und „Found as“. Außerdem ist ein CHANGELOG-Satz falsch („exactly the same path“). README/tools.md/installation.md: keine Zahl falsch.

Gelesen: README.md, docs/tools.md, docs/installation.md, docs/development.md, CHANGELOG.md § [0.9.0], gegen `git diff v0.8.0..HEAD -- chemdraw_tool/` (26 Dateien, 28 Code-Commits).
Format: `Datei:Zeile · Aussage · Beleg · Sicherheit · Schwere`

## Falsch
- CHANGELOG.md:39–40 · „Names that resolved before take exactly the same path as before.“ · PubChem-Direkttreffer werden jetzt gegen die Schreibvariante geprüft und können wechseln: Synonymfehler, Salz → freie Form („Bendamustin“), definiertere Stereoform („Naloxon“) (resolver.py `_pubchem_checked`, `resolve_name_route` Z. ~1168; Commits 0285017, c48173d, e559323); OPSIN-Treffer ohne Lokanten ebenso (`_opsin_checked`, steht nur unter Fixed). Stimmt nur für den Englisch-Schritt allein · sicher · falsch

## Fehlt (CHANGELOG 0.9.0)
- CHANGELOG.md:9–55 · CAS-Auswahl neu: aus dem PUG-View-Abschnitt „CAS“, Prüfziffer, CAS Common Chemistry zuerst, Mehrheit der Quellen, bei Gleichstand leer (vorher erstes Synonym) · databases.py `_valid_cas`, `_cas_from_view`, `_synonyms_and_cas`; tests/identity/stoffe.json:19 (Ibuprofen 58560-75-1 → 15687-27-1); Commit 9662b76 · sicher · fehlt
- CHANGELOG.md:9–55 · pH außerhalb 0–14: `exact_ph` erweitert das Bisektionsintervall über 0/14 hinaus (Titrationskurve, calculate_ph), calculate_ph hängt einen Satz an („A pH outside 0–14 is possible…“) · ph_core.py (`while f(lo) < 0` …), ph_calc.py `_range_notes`; gemessen `strong_acid_ph(2.0)` = −0,301 + Satz; Commit a3f62dd · sicher · fehlt
- CHANGELOG.md:9–55 · predict_spectrum: 17 neue IR-Regeln (C–F/Cl/Br/I, Sulfonamid, Sulfon, Sulfoxid, C=S, Azid, Imin/Oxim, P=O/P–O) und Regel „sekundäres Amin“ schließt Amide/Sulfonamide jetzt aus · spectro.py Z. 76 (SMARTS) und Z. 278–314; Commit a3f62dd · sicher · fehlt
- CHANGELOG.md:9–55 · `foundAs` im Ergebnis von generate_molecule/batch_generate/lookup_molecule_data, Zeile „Found as “…”“ im Molekül- und im Datenpanel · payloads.py:84, :293; FoundAs.jsx; SectionHeader.jsx; MoleculeView.jsx; tests/__snapshots__/tools/{generate_molecule,batch_generate,lookup_molecule_data}.json (+foundAs); Commit 849d2a9 · sicher · fehlt
- CHANGELOG.md:34–42 · Nicht genannte Schritte der Namenskaskade: 6 Form-Zusatz (Anhydrat / (freie Säure) / A+B), 8 nur das Gegenion auf Englisch („Cefalotin sodium“), 9 Drehsinn neben R/S weg („(S)-(−)-timolol“ → „(S)-timolol“); außerdem griechische Buchstaben, Halogen-Bindevokal (Fluorcytosin → Fluorocytosine), Tautomer zählt nicht als anderer Stoff · resolver.py Docstring `resolve_name_route` Schritte 6–9, `_rotation_variant`, `_same_tautomer`; de_names.py `form_variant`, `salt_variant`, `_GREEK`, `_HALOGEN` · sicher · fehlt
- CHANGELOG.md:9–55 · Salz → freie Form und Stereoform-Regel als Verhaltensänderung („Bendamustin“ liefert die freie Base statt HCl-Salz, wenn der Name kein Salzwort trägt) · resolver.py `_pubchem_checked` (Salzform- und Stereoform-Befund), `_SALT_WORD` · sicher · fehlt
- CHANGELOG.md:9–55 · „D-Glucose“ liefert seit der OPSIN-Gegenprobe den Pyranosering (Haworth) statt der offenen Kette mit Fischer-Knopf · Commit 41da7c4; plans/mcp-server.md:9 und :27 (host-Test auf `aldehydo-D-glucose` umgestellt, feef949) · wahrscheinlich · fehlt
- CHANGELOG.md:13–19 · Export PNG ist in der 3D-Ansicht ausgeblendet; 3D-Chip erscheint auch bei Molekülen ohne All-H/Fischer/Haworth-Knopf; Fehler „Click 3D again to retry“ · MoleculeView.jsx (`svg && !show3d && <ExportPngButton`, `(views.length > 0 || query)`, `CONFORMER_LOAD_ERROR`) · sicher · fehlt
- CHANGELOG.md:9–55 · Abhängigkeits-Pin playwright 1.60.0 → 1.64.1 (pyproject.toml, ui/package.json); rdkit < 2026.9 (Commit ec19023) · `git diff v0.8.0..HEAD -- pyproject.toml`; ec19023 liegt nach v0.8.0 · sicher · fehlt (Entwickler-Ebene)
- CHANGELOG.md:30–32 · E2-Hinweis auch für sperriges tert-Alkoxid an primärem Halogenid, E1-Hinweis bei SN1 mit β-H · mechanism_substrate.py `competition_notes`, `E2_BULKY_NOTE`, `E1_NOTE` (CHANGELOG nennt nur das Beispiel Isopropyliodid + OH⁻) · sicher · unscharf

## Fehlt/unscharf (Nutzerdoku)
- docs/tools.md:21–23 · Panel-Knöpfe „data sheet, PNG export and an Anki card“, Ansichten nur als `view`-Option · 3D-Chip im Molekülpanel (MoleculeView.jsx `toggle3d`) fehlt; „Found as“ fehlt · sicher · fehlt
- docs/tools.md:50–51 · 3D: „generate_3d … opens a ball-and-stick panel“ · erreichbar jetzt auch über den 3D-Chip im Molekülpanel (MoleculeView.jsx) · sicher · fehlt
- docs/tools.md:38–46 · Mechanismen ohne E1/E2-Hinweis, ⇌ bei Fischer, Lösungsmittel als Protonenakzeptor · payloads.py:314–317 (`notes`, `reversible`); MechanismView.jsx `StepArrow({reversible})`, `mech-note` · sicher · fehlt
- docs/tools.md:17–19 · „Names resolve through OPSIN, PubChem and NCI“ · zusätzlich englische Schreibweise, Gegenion-, Form- und Drehsinn-Varianten und Gegenprobe OPSIN↔PubChem (resolver.py `resolve_name_route`) · sicher · unscharf
- docs/tools.md:182–184 · Limitation „Without Java, names need the internet“ (impliziert: mit Java offline) · mit Java fragen organische Namen ohne Lokanten jetzt PubChem zur Gegenprobe (`_opsin_checked`, `_SYSTEMATIC_MARK`); offline gilt OPSINs Antwort · wahrscheinlich · unscharf
- docs/installation.md:63–66 · Java „lets OPSIN parse systematic IUPAC names offline“ · stimmt für Namen mit Lokanten; Trivialnamen ohne Lokanten gehen zusätzlich ins Netz (`_opsin_checked`) · wahrscheinlich · unscharf
- docs/tools.md:100–101, :180–202 · Limitations nennen nicht, dass CAS bei uneinigen Quellen jetzt leer bleibt · databases.py `_cas_from_view` (`return winners[0] if len(winners) == 1 else None`) · sicher · fehlt
- docs/tools.md:105–110 · calculate_ph ohne Hinweis auf Werte außerhalb 0–14 und Aktivitäts-Satz · ph_calc.py `_range_notes` · sicher · fehlt
- docs/development.md:11 · Diagramm Resolver = OPSIN → PubChem/NCI · ohne Gegenprobe und Schreibvarianten (de_names.py neu, resolver.py +363 Zeilen) · sicher · fehlt
- docs/development.md:33 · „About 8,000 Python tests“ · 8389 gesammelt (Zahlen unten) · sicher · unscharf
- README.md:40 · „16 tools in five areas“ · nur 15 liegen in den Bereichen, save_png steht außerhalb (README.md:62 erklärt es selbst; CLAUDE.md „Outside the areas sits exactly one tool“) · sicher · unscharf

## Unscharf (CHANGELOG-Wortlaut)
- CHANGELOG.md:40–42 · 591 → 681 wird dem Englisch-Schritt zugeschrieben („this moves“) · Englisch-Schritt allein: Lauf 3 = 658 (docs/evidence/masse-eval-2026-11/README.md:43); der Rest kommt aus OPSIN-Gegenprobe, Salz-/Form-/Drehsinn-Varianten, Stereoregel · sicher · unscharf
- CHANGELOG.md:41–42 · „591 to 681 correct identities“ · 591 = Lauf 2 (05.11., Stand mit cc13e47 ⊂ v0.8.0) gegen die alte Fixture; 681 = eingefrorene Lauf-12-Antworten gegen die korrigierte Fixture (Nicotin, früher fumaric acid/tenofovir, Stereo-Referenzen), „noch kein neuer Live-Lauf“ (plans/archiv/mcp-server-verlauf-2026-11.md:50–51); der letzte Live-Lauf identitaet.md:5 (07.11.) sagt 683 grün; beide vor e559323 (A>=, laut Kippmessung +4). Kein Lauf auf HEAD · sicher (Herkunft) / unsicher (Zahl auf HEAD) · unscharf
- CHANGELOG.md:28–29 · „`current_step` numbers after step 3 shift by one“ · current_step ist 1-basiert (server.py:3765); alter Schritt 4 „Proton transfer“ wird zu 4+5, ab altem Schritt 5 verschiebt sich die Nummer um eins · wahrscheinlich · unscharf
- CHANGELOG.md:29–30 · „long alkyl chains are labelled C₁₇H₃₅“ · gekürzt wird ab 5 C (Pentyl), mechanism_renderer.py `CHAIN_MIN = 5`, nur unverzweigt/endständig · sicher · unscharf
- CHANGELOG.md:52–53 · Locant-Liste „digits, brackets, N-/O-/o-/m-/p-“ · Regex umfasst auch S-, P- und N,N- (`_SYSTEMATIC_MARK`); kohlenstofffreie Namen werden nie geprüft; Englisch-Variante kann OPSIN bestätigen · sicher · unscharf

## Geprüft und stimmig (keine Befunde)
README Quick start/Installation/Pfade, tools.md Profile/Optionen/Lookups/Anki, installation.md Routen/Doctor, CHANGELOG 3D-Knopf (Cache, explizite H, SDF), SN2/SN1/Fischer-Wortlaut, spectrum_type `.strip().lower()` (server.py:983), Beispiele der Englisch-Varianten. Tool-Beschreibungen (Snapshots) unverändert, nur Output-Schemas (+foundAs, +notes, +reversible).

## Selbst belegte Zahlen
- Tools je Profil: `uv run python scratchpad/count.py` (list_tools je CHEMDRAW_PROFILE, Panel = meta.ui) → `mvp 16 12` · `full 23 16` ✓
- Tests: `uv run pytest --collect-only -q | tail -1` → `8389 tests collected in 1.53s` (Doku: „about 8,000“)
- Snapshots: `ls tests/__snapshots__/tools/ | wc -l` → `23` ✓ (= Vollprofil); `git diff --stat v0.8.0..HEAD -- tests/__snapshots__/` → 4 Dateien, 28 Zeilen, nur Schema-Felder
- Version: `grep -n '^version' pyproject.toml` → `3:version = "0.9.0"`; server.json Z. 6 und 15 → `0.9.0` ✓
- Identität 25: tests/identity/stoffe.json → 31 Einträge = 25 mit InChIKey + 3 ambiguous + 3 invalid_smiles ✓
- 591/711 = 83,1 %, 681/711 = 95,8 % ≈ 96 % ✓ (Rechnung); Herkunft siehe Befund oben
- pH: `strong_acid_ph(1e-8)` → `6.978…` ✓ (tools.md:110 „6.98“); `weak_acid_ph(0.1, 4.76)` → `2.88` ✓; `strong_acid_ph(2.0)` → `-0.301` + Bereichssatz
- Mechanismen (build_steps): Fischer 8 · SN1 6 · SN2 3 Schritte ✓ (CHANGELOG „8 instead of 7“; v0.8.0 hatte 7 Labels)
- Englisch-Varianten: Dexamethason→Dexamethasone, Amilorid→Amiloride, Lamivudin→Lamivudine, Maleinsäure→Maleinic acid, Bernsteinsäure→succinic acid, Natriumlactat→sodium lactate, Alcuroniumchlorid→Alcuronium chloride, (RS)-Ketamin→Ketamine ✓
- Pfade: server.py:91–98 → `~/ChemDraw-Output/{einzelmolekuele,spektren,dc-platten,scope,anki,diagramme,3d}` ✓
- Desktop-Messung tools.md:196–201: docs/desktop-abnahme-2026-11-02.md:72–95 (Nachmessung 03.11., 0 von 3) und :147–149 (2 von 2 mit „nutze ChemDraw“) ✓
