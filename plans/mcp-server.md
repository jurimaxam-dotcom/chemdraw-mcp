# MCP-Server: Panel, Werkzeuge, Releases

## Weiter bei — auf Jays Anweisung angehalten (07.11.2026)

- **README-GIF halbfertig, uncommittet:** `scripts/demo-video.sh`,
  `chemdraw_tool/ui/src/host/demo.record.mjs`, `demo-options.mjs` und
  `ui/src/utils/demoRecordingOptions.test.mjs`; Morphin-Ablauf und vollständiger
  Ladepausenschnitt vorbereitet, 5 Helper-Tests grün, **keine neue Aufnahme gestartet**,
  `assets/demo-molecule.gif` unverändert; Vorher-Bild/Logs unter
  `/tmp/chemdraw-readme-gif/2026-11-07/qa/`; Stereo-Klick erst nach W1 ergänzen.
- **Opus Schnitt 3 gebaut:** `e559323`; Codex hat Diff gelesen, **Kreuzabnahme offen**,
  noch keine eigenen Tests/Replays für diesen Commit; Nicotin-Regenerationsschutz
  `1ea7d42` fertig (36 Tests grün).
- **CI rot laut Chef:** `scripts/notebooklm/bundle.py`, Eigentümer unklar;
  hier nicht behoben oder erneut geprüft.
- **Fortsetzung nur auf neuen Auftrag:** zuerst Kreuzabnahme `e559323`, danach
  GIF-Entwurf mit echter Aufnahme und drei Standbildern; vor Jays Sichtung nichts davon committen.

## Weiter bei — Opus baut Schnitt 3 A>=; Codex prüft über Kreuz (07.11.2026)

- [x] **Chef-Entscheid Schnitt 3:** A>= bauen; B′ verworfen, weil `citral` und
  `Citral A+B` nach korrigierter Referenzwertung tatsächlich grün→rot kippen.
  Vareniclin flach und definiert gelten in dieser Kippmessung als gleichwertig.
  Der entfallende Mefloquin-Gewinn gegenüber A ist der akzeptierte Preis für
  den Stereo-Erhalt (Lincomycin/Prostacyclin); kein zusätzlicher Resolverzweig dafür.
  Beleg: `docs/evidence/masse-eval-2026-11/kippmessung-stereo/ergebnis.md`,
  `fixture_check.json`, Messcommit `6259e38`; Chef-Auftrag
  `20261107-074353-cas-9662b76-abgenommen-ci` #1.
- [x] **Messung auf Basis 112021f neu ausgewertet:** 711 Eingaben, Record↔Basis
  ohne Abweichung, 0 Memo-Fehlgriffe; Holdouts PubChem 553 / OPSIN 131.
  A>= mit beschlossener Referenzwertung: **0 grün gekippt, 4 behoben**
  (Benzylpenicillin-Benzathin, Isosorbiddinitrat, Naloxon, Vinorelbin);
  Holdout PubChem **0 gekippt / 6 behoben**, OPSIN **0 / 0**.
- [x] **Nicotin-Referenz korrigiert** (`668d05b`): `nicotine` und `Nicotin` in
  `tests/identity/stoffe-masse.json` auf (S)-Nicotin, vollständiger Key
  `SNICXCGAKADSCV-JTQLQIEISA-N`; PubChem 89594, ChEMBL3, KEGG D03365,
  Wikidata Q28086552. Die kleine `stoffe.json` enthält diese Eingaben nicht.
  Eingefrorene Lauf-12-Antworten gegen neue Fixture: **681 grün / 14 gelb / 16 rot**
  statt 683 / 14 / 14; genau die zwei Nicotin-Zeilen grün→rot, noch kein neuer Live-Lauf.
  Prüfung: `36 passed` (Masse-/Identitätsauswertung), SMILES→Key und CIP=S geprüft;
  Neuwertungsbeleg `/tmp/chemdraw-schnitt3-abnahme/nicotin-neuwertung.log`.
- [x] **Nicotin-Regenerationsschutz:** `scripts/masse_eval.py` setzt beim Neubau
  für `nicotine` und `Nicotin` die bestätigte (S)-Referenz ein;
  realer `baue_liste`-Test mit früherem flachem Wikidata-Record zuerst rot,
  danach **36 passed**, ruff grün; Belege `/tmp/chemdraw-schnitt3-abnahme/regeneration-{rot,gruen}.log`.
- [ ] **Opus:** A>= implementieren (läuft); Codex prüft den gemeldeten Commit über Kreuz.
  Prüfen: Commit-Diff, relevante Resolver-Tests und Kipp-/Holdout-Belege → erwartet:
  freigegebene A>=-Regel, 0 bisher richtige Fälle gekippt, keine B′-Regel.
- [x] **CAS-Fix `9662b76` abgenommen:** CAS aus dem quellenbelegten PUG-View-Abschnitt,
  CAS Common Chemistry bevorzugt, Quellenmehrheit statt Synonymreihenfolge;
  Offline-Stichprobe **25 Eingaben / 19 Stoffe / genau 1 Änderung** (Ibuprofen).
  Gate rc=0 (**8362 passed / 16 skipped**), CI grün laut Chef; nach Desktop-Neustart
  Ibuprofen → Data: **15687-27-1**, finales Bild
  `/tmp/chemdraw-desktop-test/2026-11-07/07-ibuprofen-data-nach-fix.png`.
  Quellen/Replay: `tests/__fixtures__/pubchem-cas/README.md` und `identity-cas.json`.
- [ ] **Host-Test SN1-Titel (offen, nicht behoben):** `test:host` erwartet wörtliche
  SMILES (`CC(C)(C)Cl + O`), während `_substrate_label`/`_smiles_title` inzwischen
  Stoffnamen liefern; vorbestehend auf `f58eb5b` reproduziert (je rc=1 in
  `/tmp/chemdraw-desktop-test/2026-11-07/cas-audit/host.log` und `host-baseline.log`);
  prüfen nach eigener Behebung: `npm --prefix chemdraw_tool/ui run test:host` → erwartet rc=0.
- [x] **Tisch-Fäden geschlossen:** `20261107-065505-chef-entscheid-zur-kippmessung`
  und `20261107-072830-desktop-handtest-claude-md`; Umsetzung/Kreuzabnahme im aktuellen Auftrag.
- [ ] **3D-Knopf bleibt W1:** im Molekülpanel noch nicht implementiert; das vorhandene
  `generate_3d`-Tool ist der Chat-Weg. Prüfen nach W1: Ibuprofen im Desktop → 3D →
  erwartetes drehbares Modell; der aktuelle Handtest nimmt diesen fehlenden Knopf nicht ab.

## Weiter bei — Codex: Lauf 12 abgeschlossen (07.11.2026)

**Nächster Schritt:** Opus setzt den beschlossenen Schnitt 3 A>= um; Codex prüft
seinen gemeldeten Commit über Kreuz (aktueller Tisch-Auftrag, siehe oben).
Schnitt 1 `0f174ea` und Schnitt 2 `3ba3ff2` sind vom Chef abgenommen.
Die folgenden Lauf-12-Zahlen dokumentieren die damalige Fixture vor `668d05b`;
clomifene als gelb `gemisch` ist weiterhin keine freigegebene Umsetzung.

- [x] Lauf 11 unverändert als `identitaet-lauf-11-vor-schnitt-1-2.json` gesichert
  (SHA256 `095e0111a57f5086dec47de13ab6ee02ed374dfb601508bdfdcfeb1a4caced8c`).
- [x] Lauf 12 in frischem Prozess auf Start-HEAD `112021f9a74603ed7122e826e9688f3969439e70`:
  **711 Eingaben · 683 grün · 9 gelb Quelle/Referenz · 3 gelb Tautomer ·
  2 gelb E/Z fehlt · 14 rot**. Exit 1 wegen der 14 roten Fälle, vollständiger Lauf.
  Fixture-SHA256 `4b213a0c332bd8e0214cb491bb27dee428750c72bc9a8da80707d4436d1ee4c3`.
- [x] Vollständiger Vergleich je Eingabe gegen Lauf 11: **675 grün→grün mit gleichem
  vollständigem Key, 8 rot→grün, 6 rot→gelb, 8 gelb→gelb, 14 rot→rot**.
  **0 grün→anders**, keine fehlenden/zusätzlichen Eingaben. Genau 14 semantisch
  geänderte Zeilen; alle Felder außer Laufzeit verglichen, Zeiten separat dokumentiert.
- [x] Bericht mit `uv run python scripts/masse_eval.py identitaet` erzeugt und
  Rohzahlen unabhängig nachgezählt. Gelb: 3 bekannte Lücken, 6 unsichere Referenzen
  (1 Salz, 2 Skelett, 3 Stereo), 3 Tautomere, 2 E/Z fehlt. Alle 14 roten Fälle Stereo.
- [x] Jay-Entscheid 07.11. überall im Plan als beantwortet nachgetragen:
  Abfragemodus zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
  Andere offene Freigaben bleiben unverändert. Kein Produktcode/keine Fixture geändert.

**Beweise:** `docs/evidence/masse-eval-2026-11/identitaet-lauf.json`,
`identitaet-lauf-11-vor-schnitt-1-2.json`, `lauf-12-vergleich.json` (vollständige
Änderungsliste, Hashes, Statusübergänge, Zeiten), `identitaet.md`;
Prozesslog `/tmp/chemdraw-identitaet-lauf-12.log`.
Befehl: `uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json
--protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`.
Prüfmethode: vollständige Eingabemenge, eigene Status-/Artzählung, voller Key/Text
aller zuvor grünen Fälle; Bericht aus genau diesen Rohdaten. Keine erneute
Gesamtgate-/Desktop-Abnahme für reine Evidence-/Planänderungen behauptet.

**Offene Tisch-Fäden:** Lauf-12-Auftrag `20261106-232415-schnitt-2-3ba3ff2-abgenommen`
(Bericht an Chef `w57:p3`); Zusatzentscheid `20261107-064504-nach-lauf-12-im`
(Bericht im selben Plan-Commit). Die erneuerte Schnitt-3-Messung auf `112021f`
und der Chef-Entscheid A>= stehen im aktuellen Opus-Abschnitt oben;
Nicotin wurde mit `668d05b` korrigiert. Der frühere Stand ohne form_variant ist historisch.
**Wartezeiten/Folgeaktion:** keine eigenen laufenden Jobs oder halbfertigen Edits;
auf konkrete Chef-Abnahme/Folgeauftrag reagieren, keine eigene Wartefrist.

**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle;
Reaktionen/Mechanismen später als Phase 7. Welle 3: zweiter Konnektor
`chemdraw-pharma` mit `full` bereits entschieden.

**Vorstufen:** Tautomer-/Referenz-Folgepunkte `5a2ea90` / `7ae85ac` / `5081b6d` /
`fc717cd` abgenommen; Lauf 11 **675 grün · 3 gelb Quelle/Referenz · 3 gelb Tautomer ·
2 gelb E/Z fehlt · 28 rot**. Neuere Schnitt-1-Referenzen erst in Lauf 12 werten.


- [x] `b67ceb7` gepusht: 711 Referenz-SMILES / 414 ursprüngliche Keys geprüft,
  411 PubChem-Recordantworten und 3 dokumentierte 404. Vier Referenzen / fünf Eingaben
  mit unabhängig bestätigter vollständiger Stereo korrigiert: Clindamycin, Cocaine,
  Vitamin-B5-Pantothensäure (beide Sprachen), alpha,alpha-Trehalose. Nicotin blieb damals unklar; seit Chef-Entscheid 07.11. und `668d05b` auf (S) korrigiert.
- [x] Alter Clindamycin-Auditsatz berichtigt: Existenz eines partiellen ChEMBL-Keys
  bestätigte keine vollständige Stereo. Alle Quellen/Entscheidungen im eigenen Evidence-Ordner.
- [x] Reine Neuwertung eingefrorener Lauf-7-Antworten (`9b3cbbd`): **668/1/42 → 673/1/37**,
  genau fünf rot→grün, 706 andere Zeilen und sämtliche Zeiten unverändert. Kein Resolverlauf.
  Aktuelle Fixture: 711 Namen / 413 unterschiedliche Keys (cocaine und Kokain jetzt gleich).
- [x] Datenprüfung fünf rot→fünf grün; alle 711 Referenz-SMILES schlüsselkonform.
  Gate rc=0: **8213 passed / 16 skipped**, `/tmp/chemdraw-stereo-referenzen-gate.log`
  (geteilter Baum mit fremdem Salzform-WIP). Eigene Leases freigegeben.
- [x] Befund 3 abgenommen: Bericht `20261106-134101-abnahme-befund-3` #3,
  eigener vollständiger Live-Lauf gegen damalige Fixture **668/1/42**, 8205/16 Gate grün;
  Ergebnis unter `/tmp/chemdraw-befund3-abnahme-aktuelle-fixture.json`, danach als Lauf 7 übernommen.

**Dateien/Beweise:** `tests/identity/stoffe-masse.json`,
`docs/evidence/masse-eval-2026-11/stereo-referenzen/{README.md,audit.json,korrekturen.json,vergleich.json,lauf-7-neuwertung.json}`,
`docs/evidence/masse-eval-2026-11/referenzkorrektur/referenz-audit.json` (Clindamycin-Berichtigung).
Prüfmethode bei Daten-Nachbesserung: externe benannte Quelle + kompletter Key, RDKit-Zentren,
Kompatibilität bekannter Stereo, Neuwertung gleicher Antworten; dann `./test.sh > log`, rc/Output berichten.
Keine E/Z-/Atropisomerie-/Metallkoordinations-Vollprüfung oder neue Resolvermessung zugesagt.
**Bekannte Grenze:** `masse_eval.py liste` kann partielle Quellobjekte erneut wählen;
Regenerationsschutz war außerhalb der erlaubten Datenpfade, als Code-Folgepunkt beim Chef gemeldet.
Fremdes Salzform-WIP in Resolver/Tests und dessen eingefrorenem Lauf nicht übernehmen.
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.
**Neustart:** `HERDR_PANE_ID` fehlt bisher in dieser Laufzeit. Skript einmal aufrufen und tatsächlichen
Fehler melden; keine fremde Pane wählen. Ältere Weiter-bei-Abschnitte unten sind historische Prüfstände.

## Weiter bei — Codex nach Befund 4, vor Kontext-Neustart (06.11.2026)

**Nächster Schritt:** Kein eigener Folgeauftrag offen. Befund 4 (`530e9a9`) ist nach Kreuzabnahme
vom Chef abgenommen und der Faden `20261106-115136-befund-4-referenzliste` geschlossen
(Chef-Planstand `a2fc4e8`, eigener Bericht #3). Erst auf neuen konkreten Tisch-Auftrag weiterarbeiten.
Keine eigene Wartefrist, laufenden Jobs oder halbfertigen Edits.
Fremdes Befund-3-WIP (`resolver.py`, `tests/test_resolver.py`, Holdout und eingefrorener Lauf 5) nicht übernehmen.

- [x] Befund 4 gebaut und gepusht: `530e9a9`, zwei unabhängig belegte Referenzkorrekturen,
  Neubau-Regressionsschutz, atomarer 7-Tage-ChEMBL-Namenscache inkl. Refresh und Fehler-Recovery.
- [x] 46 rote Fälle auditiert; keine weitere gesicherte Elternstoff-/Prodrug-/Salz-Verwechslung.
  Reine Neuwertung derselben Lauf-5-Antworten: **664/1/46 → 666/1/44**; kein neuer Resolverlauf.
- [x] Eigene Auswertungstests **10 passed**, alle acht neuen Tests rot bzw. per Mutation rot gesehen.
  Vollständiges Gate rc=0: **8203 passed / 16 skipped**, `/tmp/chemdraw-befund4-gate.log`
  (geteilter Baum enthielt zusätzlich fremdes Befund-3-WIP). Alle eigenen Datei-Leases freigegeben.
- [x] Befund 2 Runde 3 abgenommen: `8978be7`, Hydrate/Edetat/Goldthiomalat live geprüft,
  301 gespeicherte Vergleichspaare unabhängig ausgewertet, Gate **8189/16**;
  Abschlussbericht `20261106-105531-abnahme-befund-2` #6, Hop-Limit erreicht, dort nicht mehr schreiben.

**Dateien/Beweise:** `scripts/masse_eval.py` (`REFERENZ_KORREKTUREN`, `_chembl_namen`),
`tests/identity/stoffe-masse.json`, `tests/test_masse_eval_identity.py`,
`docs/evidence/masse-eval-2026-11/referenzkorrektur/README.md` und die dortigen Audit-/Laufdateien.
Prüfmethode bei Änderungen: erst passende Regression rot, gezielte Tests, dann `./test.sh > log`, rc und
Output berichten; keine Golden-/Snapshot-Anpassungen zugesagt. Metadaten-Cache warm 0,000293 s,
Resultat wie alte Funktion; ganzer Bericht 28,322 s. Kaltaufrufe und PubChem bleiben netzabhängig.
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.
**Neustart:** `HERDR_PANE_ID` fehlt hier weiterhin. Skript einmal aufrufen und Fehler melden;
keine fremde Pane adressieren. Ältere Weiter-bei-Abschnitte unten sind historisch und kein neuer Bauauftrag.

## Weiter bei — Codex nach Kreuzabnahme Runde 2 (06.11.2026)

**Nächster Schritt:** Erst bei neuem Tisch-Auftrag den Bericht der laufenden Runde 3 prüfen
(Bauer-Faden `20261106-113525-folge-zu-20261106-102746`, Chef-Auftrag zur Kreuzabnahme
`20261106-105531-abnahme-befund-2`, zuletzt #4 Codex-Bericht). Kein eigener Bauauftrag offen;
keine halbfertigen Edits, roten Tests im Fix oder laufenden eigenen Hintergrundjobs. Keine feste
Wartefrist; Folgeaktion bei Bericht: Diff und gezielte Tests unabhängig prüfen, Ergebnis an Chef.

- [x] Kreuzabnahme Runde 1: `41da7c4`/`e228047`, 139 gezielte Tests grün;
  NaPO4-Ladungsfehler und Silikat-Stöchiometriewechsel gemeldet (Abnahme-Faden #2).
- [x] Kreuzabnahme Runde 2: `038ace4`/`236df52`, 146 gezielte Tests grün;
  alte Salzfehler behoben, Holdout 117/9/0/5 aus 131 Einzelzeilen nachgerechnet,
  Lauf 5 664/1/46 bei 711 eindeutigen Eingaben bestätigt. Echter Blackhole-Test nach
  OPSIN-Warmup: Ethanol 3,013/3,017 s, Struktur-Fallback erhalten. **Nachbessern** wegen
  `potassium citrate`: wasserfrei → Monohydrat, Abnahme-Faden #4. Chef hat Runde 3 vergeben.
- [x] Desktop-Handtest E2: drei Originalprompts (SN2, Fischer, SN1) jeweils
  `generate_mechanism`, alle Erwartungen und Next/Back grün; Bericht
  `20261106-103546-etappe-e2` #4, Faden inzwischen geschlossen.
  Beweisbilder `/tmp/chemdraw-desktop-test/etappe-e2/`; keine Release-Paket-Abnahme.

**Prüfpfade für Runde 3:** `chemdraw_tool/resolver.py` (`_opsin_checked`, bislang Zeilen 484–519),
`tests/test_resolver.py`, `docs/evidence/masse-eval-2026-11/{README.md,holdout_opsin_check.json,identitaet-lauf.json}`.
Prüfmethode: `uv run pytest tests/test_resolver.py tests/test_ambiguous_names.py -q`, echte Gegenprobe
der Hydratvarianten (potassium citrate / tripotassium citrate / anhydrous / monohydrate),
Formel + Ladung + InChIKey, bisherige sechs Trivialnamen-Gewinne und Diiodtyrosin/Edetat erhalten;
kein Golden-/Test-Blessen. Keine komplette Gate-Wiederholung oder neue Desktop-Runde zugesagt.
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.
**Neustartgrenze:** `HERDR_PANE_ID` fehlt weiterhin in dieser Laufzeit. Skript einmal aufrufen,
Fehler offen melden; keine fremde Pane wählen und nicht ohne neuen Anlass Neustartschleifen starten.
Ältere Neustartabschnitte unten sind historisch; der zurückgezogene IR-Auftrag wird nicht erneut begonnen.

## Weiter bei — Codex-Neustart nach Befund 5 (06.11.2026)

**Aktuell, ersetzt den Folgeauftrag unten:** Orchestrator hat den IR-Auftrag in Faden
`20261106-104425-ir-bericht-deterministisch` #4 zurückgezogen; ein Claude-Unteragent übernimmt.
Codex baut daran nicht weiter. `tisch gib-frei scripts/masse_eval.py tests/test_masse_eval_ir.py`
ausgeführt. Plan-Prüfpunkt `6de375e` gepusht; Neustartskript scheiterte mit
`HERDR_PANE_ID: nicht in herdr — kein Neustart möglich`. Keine eigene Arbeit oder Wartefrist offen.

**Erneuter Neustart-Prüfpunkt (06.11., HEAD `e38d28d`):** IR-Folgeauftrag weiterhin unbegonnen;
keine eigenen halbfertigen Edits oder laufenden Jobs. Faden `20261106-104425-ir-bericht-deterministisch`
bleibt offen, zuletzt #3 Status zum erneuten Neustart. Drei ungetrackte Dateien
`docs/evidence/masse-eval-2026-11/{holdout_opsin_check.py,identitaet-lauf-3-vor-opsin-check.json,identitaet-lauf-3-vor-opsin-check.md}`
gehören zur parallelen Befund-2-Arbeit und bleiben unangetastet. Der fremde Commit `e38d28d` betrifft
Fischer-Protonentransfer über ein Alkoholmolekül (acht Stationen); Diff-Stat gelesen, hier nicht abgenommen.
Neustartskript nach diesem Plan-Commit aufrufen; fehlt `HERDR_PANE_ID`, Fehler melden und keine fremde Pane wählen.
Nach erfolgreichem Neustart direkt den folgenden Auftrag beginnen, keinen weiteren Neustart ohne neuen Anlass.

**Nächster Schritt:** Folgeauftrag `20261106-104425-ir-bericht-deterministisch` lesen und ausführen:
`scripts/masse_eval.py` sortiert bei häufigsten Banden Gleichstände bisher instabil. Stabil nach Bandname sortieren;
in `tests/test_masse_eval_ir.py` einen zweimal erzeugten Bericht auf Byte-Gleichheit prüfen (erst rot sehen),
`docs/evidence/masse-eval-2026-11/ir-abdeckung.md` einmal neu erzeugen, nur diese drei Dateien committen/pushen,
kurzer Bericht mit SHA in diesen neuen Faden. Vorher Leases mit Befund-2-Session abstimmen (sie bearbeitet nur IDENT_DEUTUNG im selben Skript).
Befund 5 ist vom Orchestrator Claude `f31ab414` (`w4W:p6`) abgenommen (06.11., Folgeauftrag #1: ph 51/51, 92 Tests inkl. Snapshots/Goldens).
Der Faden `20261106-103348-masse-eval-befund-5` hat Hop 6/6 erreicht: dort keine weitere Nachricht versuchen.

- [x] `a3f62dd` auf main gepusht: `chemdraw_tool/ph_core.py::exact_ph`, `ph_calc.py::_range_notes`,
  `spectro.py::_IR_TABLE`, IR-Abschnitt `scripts/masse_eval.py`, eigene Regressionen und Evidence.
  pH **48/51 → 51/51**, IR **302 → 168 Gruppen-Molekül-Lücken** bei 414 Stoffen (20 → 12 Gruppen).
- [x] TDD und Beweise: acht pH-Regressionen und 22 IR-Anforderungen rot gesehen; pH 52, IR 56 grün.
  `./test.sh` rc=0, **8102 passed / 16 skipped**, Log `/tmp/chemdraw-masse-befund5-gate.log`.
  Desktop neu gestartet; Handshake rc=0, **16 Tools / 12 Panels**, `/tmp/chemdraw-masse-befund5-handshake.log`.
  Tool-Snapshots und Golden-Bilder unverändert. Punkt 5 unten dokumentiert pH/IR als erledigt, Restlücken bleiben explizit.
- [x] Orchestrator-Abnahme: Bericht #5, Zustellung #6 im alten Faden; Abnahme im neuen Folgeauftrag bestätigt.
- [ ] Folgeauftrag deterministischer IR-Bericht wie oben. Keine eigene Hintergrundarbeit und keine zeitgebundene Folgeprüfung offen.

**Dateien zur Abnahme:** `tests/test_ph_extreme.py`, `tests/test_spectro.py`, `tests/test_masse_eval_ir.py`,
`docs/evidence/masse-eval-2026-11/{ph,ir-abdeckung,ir-quellen}.md`. IR-Unterklassen und Desktop-Befunde bleiben offen.
**Fremde Arbeit erhalten:** Befund 2 bearbeitet Resolver/Identitäts-Evidence, E2 Mechanismen; Änderungen im geteilten Arbeitsbaum
(einschließlich erneut geändertem `ir-abdeckung.md`) stammen nach unserem Commit aus parallelen Sessions und sind nicht mitzustagen.
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

## Doku-Aktualität bei jedem Release (Jay 06.11.2026, Tisch-Faden 20261106-102729-jay-06-11-readme)

- [x] Inventur: mechanisch prüfbar = Toolnamen, Options-Parameter, `lookup`-Topics, Render-Stile, Panelzahlen je Profil,
  `CHEMDRAW_*`-Variablen, `chemdraw-*`-Befehle, Repo-Pfade, Identitätszahl (README, docs/tools|installation|development.md,
  CHANGELOG [Unreleased]); release-zeitig = Tag ↔ Version, datierter + gefüllter CHANGELOG-Abschnitt, leeres [Unreleased].
  Nicht mechanisch = ob Beschreibungen/Limitations noch stimmen, freie Zahlen („About 8,000 Python tests“).
- [x] `tests/test_docs_consistency.py` (Gate, 9 Tests): Identitätszahl rot gefunden (Doku 24, stoffe.json 25) → behoben;
  übrige 8 je per Mutation rot gesehen. `docs/development.md` 7,500 → 8,000 Tests (mit Codex abgestimmt, Faden #3).
- [x] `scripts/release_check.py` + `tests/test_release_check.py`; Job `check` in `publish.yml`, `build` hängt per `needs: check` daran.
- [x] Checkliste 1a (Opus-Sichtung README+docs gegen `git diff <letzter Tag>..HEAD`) in `docs/registry-publish.md`
  § Release-Reihenfolge, per Test verankert.
- Hinweis: `release_check.py` ist heute rot (rc=1), weil [Unreleased] Einträge hat — beim nächsten Release erst verschieben.

## Orchestrierung (Jay 06.11.2026: „alles autonom, Sessions spawnen, bei zu hohem Kontext schließen, Codex nutzen, nach Tisch-/Dreier-Regeln absprechen“) — Stand 06.11. ~11:00

Chef = frische Claude-Hauptsession nach Kontext-Neustart (vorher `f31ab414`). **Dreier-Regeln:** Chef baut nicht (auch keine bauenden
Unteragenten) — jede Bau-Etappe per Faden an Opus-Bauer (`cc-oeffnen --auftrag`) oder Codex; **Abnahme über Kreuz** (Codex prüft Opus-Arbeit
und umgekehrt), Chef prüft danach Diff + Tests selbst, schließt Faden + Pane. Geteilter Arbeitsbaum: jeder `git add` nur eigene Pfade;
am Etappenende auf herrenlose Änderungen prüfen (zuletzt offen: `docs/anthropic/*`, `CHANGELOG.md` — Eigentümer klären).
**Erledigt + nachgeprüft:** Doku-Prüfung je Release `9b1d8db` · Befund 5 pH/IR `a3f62dd` (Codex) · IR-Bericht deterministisch `3b060db`.
**Offen — Fäden mit ID:**
- ✅ **Befund 2 abgenommen 06.11. ~11:50** (3 Runden): `41da7c4`/`e228047` → Salz-Fix `038ace4`/`236df52` → Kristallwasser `8978be7`
  (Gegenionen bleiben, R2 hätte Edetat/Goldthiomalat gekippt). Codex #6 ABNEHMEN (Hydrate, Chloralhydrat, 301er-Messung reproduziert);
  Chef-Gate rc=0 8189 passed. Lauf 5 664/1/46, Holdout 117/9/0/5/0 gekippt. Fäden `…102746`, `…105531`, `…113525` geschlossen, Panes pD/pE zu.
- ✅ **Befund 3 abgenommen 06.11. ~14:00:** `0285017`/`052d3fe` + Evidence `9b3cbbd`. Codex-Kreuzabnahme `…134101` ABNEHMEN (Ephedrin/Risperidon live
  richtig, Befund-2-Proben gleich, Holdout 536/3/0/14, Blackhole: +3 s nur bei Abbruch nach Direkttreffer). Chef: Diff gelesen, Gate rc=0 8205,
  **Lauf 7 = 668/1/42** selbst nachgezählt (Befund 3 + 4). Fäden + Pane pF geschlossen.
- ✅ **Salzform abgenommen 06.11. ~15:10:** `c48173d`/`61567c3`/`10e7313` (Opus-Bauer): INN ohne Salzwort → freie Form, wenn PubChem direkt Salz und Variante frei bei gleichem Stamm; `_SALT_WORD` mit Wortgrenzen. Carboplatin/Tetracyclin-Tautomere/Hydroxocobalamin/Docusat = andere Klassen. Codex-Kreuzabnahme alle Punkte ja (M1/M2/M3 rot, Holdout +Phenelzin 0 gekippt, Live-Gegenproben Befund 2/3 richtig); sein NACHBESSERN (`Bendamustinhydrochlorid` not_found) ist keine Regression — Worktree `30d8cfd` liefert dasselbe → Folgepunkt. Chef: Diff gelesen, Gate rc=0 8223, **Lauf 8 = 669/1/41** nachgezählt (nur Bendamustin rot→grün; offline gegen b67ceb7 674/1/36). Fäden `…140408`, `…150235` + Pane pG geschlossen.
- ✅ **Stereo-Referenzen abgenommen 06.11.:** `b67ceb7` (Codex), Opus-Gutachter ABNEHMEN: genau 5 Fixture-Einträge (Clindamycin, Cocaine,
  Pantothensäure de+en, Trehalose), Keys live PubChem+ChEMBL, Stereo fachlich richtig, Neuwertung **673/1/37** nachgezählt (genau 5 Zeilen),
  kein Produktcode. Nicotin bewusst unverändert. Faden geschlossen.
**Danach:** deutsche zusammengesetzte Salznamen (`Bendamustinhydrochlorid` not_found, englisch `Bendamustine hydrochloride` geht) · Hydrat-Zweig der Salzregel (Tigecyclin) ohne Unit-Test · `referenz-audit.json`: ≥ 10 weitere Einträge „Referenz bestätigt (ChEMBL-Key)“ mit derselben zu weiten Begründung wie Clindamycin prüfen · Regenerationsschutz für die Stereo-Korrekturen in `masse_eval.py` (`REFERENZ_KORREKTUREN` aus Befund 4 erweitern, sonst holt ein
Neubau der Liste die unvollständigen Records zurück) · Kann „gefunden als <englisch>“ im Ergebnis (Payload + Tool-Snapshot) · rifabutin, (S)-(−)-timolol not_found.
- ✅ **„gefunden als“ abgenommen 06.11. ~16:05:** `849d2a9` (Opus-Bauer). Codex-Kreuzabnahme: Mutationen 7/3 rot, Snapshots nur Schema, Gate grün; sein NACHBESSERN verworfen — Ephedrin wörtlich bei PubChem (meine Erwartung falsch); **Desktop-Grenze:** das Modell übersetzt „Dexamethason“ selbst ins Englische, foundAs bleibt dann leer (Screenshots `/tmp/chemdraw-desktop-test/found-as/`). Chef: Diff, Gate rc=0 8239. Fäden `…151146`, `…152425` + Pane pH zu. Plan-Haken Z.~184 damit erledigt.
- ✅ **Referenz-Audit abgenommen 06.11. ~16:35:** `bfbae23` (Regenerationsschutz im echten `baue_liste`, Mutation rot; Neuwertung 674/1/36) + Evidence-Nachbesserung `3ba7bda` (Vinblastin unsicher, Doxycyclin = Tautomer, Xylit = CID 6912 geteilt) + `51d3e10` (zwei von Codex nicht belegte „PubChem Preferred“-Sätze gestrichen — Keys gaben PUG 404). Opus-Gutachter 2 Runden; Chef grep + JSON-Parse. Fäden `…151201`, `…155948`, `…162404` + Pane pJ zu. Rest: Vinblastin-Fixture ohne `unsicher`-Flag (zählt rot) · Sulfasalazin-Begründung „Preferred-Summary“ ohne CID nicht live gegengeprüft.
- ✅ **Salznamen deutsch abgenommen 06.11. ~17:15:** `2d8aaaf`/`8e971e4` (Opus-Bauer): `de_names.salt_variant` als letzter Kaskadenschritt, found_as gesetzt. Codex-Kreuzabnahme ABNEHMEN (M1–M5 rot, Live-Fälle + 5 eigene, Lauf/Salzliste nachgezählt). Chef: Diff gelesen, Gate rc=0 8271, **Lauf 9 = 674/1/36** nachgezählt (Schlüssel = Lauf 8). Salzliste Holdout 43→100, 0 richtig→anders. Fäden `…160852`, `…175918` + Pane pK zu. Rest: 18+32 Salznamen not_found. Strukturtest und Berichtszählung separat abgenommen, siehe Folgepunkte unten.
- ✅ **Salznamen-Folgepunkte abgenommen 06.11. ~22:00:** `630b5ac` (Codex): neun Anion-Schreibweisen ergänzt, Strukturtest gegen den Anion-Teil von `resolver._SALT_WORD`, drei Verhaltenstests. Chef: Diff gelesen, **62 passed**, **Gate rc=0**. Zählung: **414 Wikidata-Stoffe / 413 unterschiedliche InChIKeys**, weil cocaine und Kokain jetzt denselben Key haben. Faden `20261106-215435-chemdraw-mcp-folgepunkte-salznam` geschlossen.
- ✅ **Tautomer/timolol abgenommen 06.11. ~22:27 — Opus `3476636` / Lauf `44edf11`:** rifabutin-Tautomere als eigene gelbe Klasse, Drehsinn neben erhaltenem R/S als letzter timolol-Kaskadenschritt. **Lauf 10 = 675 grün · 1 gelb (Quelle/Referenz) · 3 gelb (Tautomer) · 32 rot**, Chef selbst nachgezählt, Gate rc=0; Codex-Kreuzabnahme **Code-Teil ABNEHMEN**: `uv run pytest tests/test_resolver.py tests/test_identitaet_tautomer.py -q` → **159 passed**; eigene Formel-/Verknüpfungs-/Kanontautomer-Gegenproben bleiben rot, Gelb wird nie Grün. Drei eigene Live-Fälle: rifabutin → `AZFBLLCNOQPJGJ-VXTBVIBXSA-N`, gelb/tautomer; `(S)-(-)-timolol` → `BLJRIMJGRPQVNF-JTQLQIEISA-N`; `(R)-(+)-timolol` → `BLJRIMJGRPQVNF-SNVBAGLBSA-N` (jeweils PubChem bestätigt). Evidence `/tmp/chemdraw-opus-kreuz-live.json`, Faden `20261106-220250-zwei-teile-a-kreuzabnahme`.
- ✅ **Referenzentscheid abgenommen, 06.11. ~23:02:** Opus `5a2ea90`, Lauf 11 `7ae85ac`: Vinblastin beide Schreibweisen `unsicher=true` mit Begründung, Key unverändert; Sulfasalazin beide Schreibweisen gelb/`ez_fehlt`. **675 grün · 3 gelb (Quelle/Referenz) · 3 gelb (Tautomer) · 2 gelb (E/Z fehlt) · 28 rot**, nur vier rot→gelb gegenüber Lauf 10, kein neuer grüner Fall. Der Quellenwiderspruch bei Vinblastin bleibt sichtbar. Codex-Berichtsauswertung und `REFERENZ_UNSICHER` sichern Zählung und Neubau separat ab.
- ✅ **Tautomer-Folgepunkte Codex abgenommen 06.11. ~23:02 (`5081b6d` / `fc717cd`):** Berichtsteil `5081b6d` mit zwei Rot-Grün-Tests und Gate rc=0 (8288 passed / 16 skipped). Neuer Holdout: 2145 Labels / 553 Fälle, alle vollständigen Keys bytegleich zur gesicherten Vorversion, **0 richtig→anders**; Vergleich `docs/evidence/masse-eval-2026-11/holdout_pubchem_check-tautomer-vergleich.json`. E/Z-Zählung und Vinblastin-Regenerationsschutz nach Opus-Commit ergänzt (vier neue Rotprüfungen → 25 betroffene Tests grün); aktueller Bericht aus Lauf 11. **Gesamtgate rc=0: 8298 passed / 16 skipped**, Log `/tmp/chemdraw-tautomer-ez-rebuild-gate.log`. Chef-Abnahme: Diff `masse_eval.py` gelesen, 25 passed, eigenes Gate rc=0, Bericht = Lauf 11 (675/3/3/2/28). Alter Faden `20261106-222719-folgepunkte-aus-opus-3476636` geschlossen; Abnahme im Folgefaden `20261106-230209-abnahme-faden-20261106-222719`.
- ✅ **Schnitt 1 `0f174ea` + Schnitt 2 `3ba3ff2` abgenommen; Lauf 12 gemessen 07.11.:**
  **683 grün · 9 gelb Quelle/Referenz · 3 gelb Tautomer · 2 gelb E/Z fehlt · 14 rot**
  aus 711 Eingaben. Gegen Lauf 11: 8 rot→grün, 6 rot→gelb, **0 grün→anders**,
  keine fehlenden/zusätzlichen Eingaben, kompletter Key-Vergleich. Evidence:
  `docs/evidence/masse-eval-2026-11/lauf-12-vergleich.json`, Rohdaten und Bericht daneben.
  Folgeentscheid 07.11.: A>= wird gebaut, B′ verworfen (siehe aktueller Abschnitt oben);
  Lauf-12-Zahlen bleiben historische Messung vor Nicotin-Korrektur `668d05b`.
  clomifene ggf. gelb `gemisch` bisher nicht freigegeben. Zusatzentscheid Abfragemodus
  aus Faden `20261107-064504-nach-lauf-12-im` eingetragen (nur Moleküle, Phase 7 später).
**Lauf 10 vs. 9 nachgezählt:** 674 grün→grün, 32 rot→rot, 1 gelb→gelb, 3 rot→gelb (doxycycline, Doxycyclin, rifabutin), 1 rot→grün (`(S)-(−)-timolol`). Die frühere Erwartung „nur rifabutin“ ist damit durch den abgenommenen vollständigen Lauf ersetzt.
**Nächster Chef-Schritt (Stand 07.11., nach Entscheid A>=):** Opus-Commit nach Codex-Kreuzabnahme prüfen und abnehmen. Abfragemodus ist beantwortet (Jay 07.11.): zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Setup-Befund (nicht dieses Projekt):** Codex-Neustartskript scheitert ohne `HERDR_PANE_ID` → Codex startete mehrfach ohne Arbeit neu.
**Bremsen bleiben:** Release-Klick, PR-Merges, Außenkommunikation. **Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

## Weiter bei — Masse-Eval-Befund 1 erledigt: deutsche Trivialnamen (Claude, 05.11.2026 23:55)

- [x] **Befund 1 (deutsche Trivialnamen ohne PubChem-Synonym)** — `abee1a5`: `chemdraw_tool/de_names.py` (reine Funktion,
  Regeln nur aus der Vorab-Messung) + letzter Kaskadenschritt in `resolve_name` (nach NCI, aus dem Original, nur PubChem).
  Belege: Tests rot gesehen (3 failed) → 108 grün; Gate rc=0 (8036 passed). Lauf 3 über `stoffe-masse.json`:
  **658 grün · 1 gelb · 52 rot** (Lauf 2: 591/1/119), 591 grün→grün, 67 rot→grün, nicht aufgelöst 80 → 9.
  Holdout gegen Überanpassung (`docs/evidence/masse-eval-2026-11/holdout_de_namen.py`, 177 nie benutzte deutsche Eingaben):
  121 gleich · 1 Stereo · **0 anderer Stoff**. Bericht: `docs/evidence/masse-eval-2026-11/README.md` § Lauf 2 → Fix → Lauf 3.
- [x] Kann: Ergebnis vermerkt „gefunden als *Dexamethasone*“ — `849d2a9`, abgenommen 06.11. (Desktop-Grenze: Modell übersetzt selbst).

- [x] **Befund 2 (OPSIN zerlegt Trivialnamen)** — `41da7c4`: `_opsin_checked` in `resolver.py` — Name mit Lokanten bleibt
  offline, sonst PubChem gegenfragen, anderes Gerüst → PubChem; Tiebreak englische Schreibweise (Glycin); offline → OPSIN.
  Messung vorab: 233 OPSIN-Treffer, kein Trennmerkmal im Namen, uneinig 7, PubChem richtig 6. Tests: 1 rot → grün, Mutation
  (Tiebreak/Lokant-Regel aus) → 4 failed; Gate rc=0 (8059 passed). Lauf 4: **664 grün · 1 gelb · 46 rot** (Lauf 3 eingefroren als
  `identitaet-lauf-3-vor-opsin-check.*`), 6 rot→grün, kein grüner Fall gekippt; Median der OPSIN-Eingaben 0,0 → 0,5 s.
  Holdout `holdout_opsin_check.py` (131 OPSIN-Treffer aus 1119 ATC-Stoffen außerhalb der Listen): 10 behoben · **1 gekippt
  (calcium silicate, anorganische Stöchiometrie)** · 116 gleich. Bericht: `docs/evidence/masse-eval-2026-11/README.md` § Lauf 3 → Fix → Lauf 4.
- [x] **Befund 2 Nachbesserung (Codex-Abnahme NACHBESSERN, Faden `20261106-105531-abnahme-befund-2`)** — `038ace4`: OPSIN-Treffer
  ohne Kohlenstoff → keine PubChem-Gegenfrage (Messung 22 Fälle: jede Salz-Kippe C-frei, jeder Gewinn organisch). Ladungsregel
  gemessen und verworfen (kippt diiodo-L-tyrosine). Lauf 5 = Lauf 4 je Eingabe (664/1/46, Lauf 4 eingefroren `identitaet-lauf-4-vor-salzregel.*`);
  Holdout 117 gleich · 9 behoben · **0 gekippt**, Einzelfälle `holdout_opsin_check.json`; Gate rc=0 (8170). Offline-Latenz korrigiert:
  Blackhole 3,0 s je organischem Trivialnamen. Bericht `236df52`, README § Lauf 4 → Fix → Lauf 5; Tisch-Bericht Faden `20261106-102746` #5.
- [ ] Kann: gemerkter Offline-Zustand im Resolver (nach Verbindungsfehler ~60 s keine Gegenfrage) spart die 3 s im Blackhole-Fall.

**Nächster Schritt:** Befund 3 (PubChem-Synonymfehler, Formel-Plausibilität) laut Warteschlange im Abschnitt Orchestrierung.
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

## Weiter bei — Dependabot + rdkit 2026.9 + README-Politur erledigt (Session 8b06750a, 05.11.2026 23:00)

**Erledigt 05.11. abends:** PR #8 und #7 per Rebase gemergt (Squash/Merge-Commit im Repo aus). rdkit 2026.9.1 übernommen
(`2d8fd0b`): Golden-Test misst nur noch den Renderer (`910892b`, eingefrorene Koordinaten), Layout-Wächter `tests/test_layout_guard.py`
(`39e7088`) bewusst neu bestätigt, Playwright-Doppel-Pin als Test. README-Politur (Plan `chemdraw-vermarktung/plans/vermarktung.md`
§ README-Politur): Codex `7b653a6`/`722c0bc` (GIFs eng, `demo-video.sh` schneidet selbst), Opus `1f4cb10`/`3139aa5` (Galerie,
407→139 Zeilen, docs/), selbst nachgeprüft (34 Links 200, twine PASSED). Tisch-Fäden 20261105-163128, -222933, -222945, -223556 geschlossen.
**Nächster Schritt:** Masse-Eval-Befunde (Abschnitt „Release-Klick 0.8.0“ unten) als eigene Etappe · README-Änderungen gehen
erst mit dem nächsten Release auf PyPI · Kann: Galeriebilder gleich hoch (nur per Beschnitt in `assets/`).
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.


**Release 0.8.0 ist draußen (Jay 05.11. 16:15: „du darfst es machen“ — einmalige Freigabe für diesen Klick, keine Dauererlaubnis):**
`gh release create v0.8.0 --target 566a060…` → https://github.com/jurimaxam-dotcom/chemdraw-mcp/releases/tag/v0.8.0, Tag zeigt auf
`566a060309e61000f4805b508cf882aa09b559a1`. Workflow `publish.yml` Lauf 42053659782: Freigabe `pypi` per `pending_deployments`
(Environment 25767991480), Ergebnis build/publish/bundle/registry je `success`. Belege: PyPI-Index führt `chemdraw_mcp-0.8.0`
(whl sha256 `0506d628…`, sdist `95c05d4b…`), Release-Asset `chemdraw-mcp-0.8.0.mcpb`, MCP-Registry `isLatest` = 0.8.0.
Der frühere Befehl von Jays Hand war nicht gelaufen (weder Tag noch Draft vorhanden, 16:10 geprüft).

**Etappe F gestartet:** Tisch-Faden `20261105-162003-etappe-f-marketing-repo` (Claude-Session `edf9eeb9`, herdr `w4W:p4`, Split down),
Auftrag mit Vorab-Befund (**Korrektur 05.11.: `plans/vermarktung.md` war versioniert**, 24 Commits — nur `vermarktung/` und `docs/distribution/` waren unversioniert): `vermarktung/`, `plans/vermarktung.md`, `docs/distribution/` sind **unversioniert** (`.git/info/exclude`
seit 21.10.) → Kopie, kein `subtree split`; Historie hat nur Branch `worktree-agent-a89d4c26da6a9d6c2` (`chemdraw_tool/ui/video/`,
`scripts/demo-short.sh`). `vermarktung/out` 1,3 GB + `video/node_modules` bleiben draußen; `vermarktung/traffic` ist Symlink nach
`~/.local/share/chemdraw-mcp/traffic`. `ax-claude.swift`/`aufnahme-desktop.sh` gehören Codex → Abstimmung per Tisch im Auftrag.
**F abgenommen 17:05** (Faden geschlossen, Bericht #2 unabhängig geprüft: Repo PRIVATE, 62 getrackte Dateien ohne Videos/`out/`/`node_modules`,
Reste in chemdraw-mcp weg, `scripts/ax-claude.sh preflight` → `screen=1 ax=1`, `gate-f.log` grün; Haken mit Belegen unten bei „Etappe F erledigt“).

**Dependabot (17:12):** PR #8 (setup-uv 10.3.2→10.3.3, Checks grün) — Merge ist Jays Klick: `gh pr merge 8 --squash --delete-branch`
(Claude-Merge vom Auto-Modus verweigert). PR #7 (6 Python-Bumps, u. a. Playwright 1.60→1.64.1, CI rot) läuft in eigener Session,
Faden `20261105-163128-dependabot-pr-7-nach` (Session `8b06750a`); Bericht bringt die Merge-Zeile.
**PR #7 grün (05.11., 98e4342 auf dem PR-Branch):** Rot war `tests/test_render_golden.py:75` (Aspirin-Goldens), Ursache
rdkit 2026.9.1 — `Compute2DCoords` spiegelt Aspirin/Glucose, dreht Ibuprofen/Benzol (Gegenprobe: nur rdkit zurück → grün).
Fix: `rdkit<2026.9` in `pyproject.toml` (gilt auch für PyPI), Playwright npm-seitig auf 1.64.1 nachgezogen (Pixel-Snapshot hält,
Chromium 1248). Gate rc=0 (7542 passed), CI py3.11/py3.13 grün, Befund im PR-Kommentar. Merge = Jays Klick:
`gh pr merge 7 --squash --delete-branch`. Pin ist Zwischenstand, keine Lösung (kehrt bei jedem rdkit-Release wieder).
**Befund (Advisor + Messung 05.11.):** der Golden-Test misst Renderer UND RDKit-Layout zugleich. Mit eingefrorenen Aspirin-
Koordinaten rendert rdkit 2026.9.1 beide Goldens **byte-gleich** (Skript `scratchpad/frozen2.py`, Kontrolle unter 2026.3.6 ebenfalls
gleich; Molblock-Umweg verfälscht schon allein, daher Koordinaten direkt setzen). **Jay:** A) Test entkoppeln (Koordinaten als
committete Fixture, optional Layout-Wächter über paarweise Atomabstände, spiegelungsinvariant) + Pin weg + rdkit 2026.9 ·
B) Goldens jetzt neu, Pin weg · C) Pin behalten. **Entschieden: A** (Jay delegierte an den Advisor, 05.11.).
- [x] Schritt 1 auf main: `tests/__fixtures__/aspirin.coords.json` (aus rdkit 2026.3.6, Goldens unverändert), Golden-Test setzt
  die Koordinaten; Beleg: unter 2026.9.1 `4 passed`, eine Koordinate +0,3 → `2 failed`. `tests/test_dependency_pins.py` prüft
  Playwright pyproject ↔ package.json; Beleg: Mutation package.json 1.64.1 → `1 failed` „Playwright-Drift“. CLAUDE.md angepasst.
- [x] Layout-Wächter `tests/test_layout_guard.py` (Hinweis Nebenagent: ohne ihn rutscht ein gedrehtes/gespiegeltes Nutzerbild
  durch): 7 Proben, direkter Koordinatenvergleich (Spiegelung zählt), Bless `UPDATE_LAYOUT=1`. Beleg: ohne Referenz `8 failed`,
  unter rdkit 2026.9.1 genau aspirin/benzene/glucose/ibuprofen rot (`4 failed, 4 passed`), unter Lock `8 passed`.
- [x] PR #8 und #7 gemergt (05.11., per Rebase — Squash/Merge-Commit sind im Repo abgeschaltet).
- [x] Schritt 2: `rdkit<2026.9` → `"rdkit"`, `uv lock --upgrade-package rdkit` → 2026.9.1. Wächter rot bei genau aspirin/benzene/
  glucose/ibuprofen; Sichtprüfung (Aspirin + Glucose gespiegelt, Keile konsistent; Ibuprofen/Benzol Ringatome eine Position
  weiter) → `UPDATE_LAYOUT=1`. Goldens unverändert grün. Gate rc=0 (7997 passed).
**Dependabot abgenommen (17:40, Hauptsession, Faden geschlossen):** PR #7 grün (py3.11/py3.13), Ursache des Rots war rdkit 2026.9.1
(Compute2DCoords spiegelt Aspirin/Glucose → Golden-SVGs rot), nicht Playwright; Fix `98e4342` auf dem PR-Branch: `rdkit<2026.9` mit
Begründung im pyproject, Playwright beidseitig 1.64.1, Goldens/Snapshots unverändert (Branch-Diff geprüft).
**Jay:** `gh pr merge 8 --squash --delete-branch && gh pr merge 7 --squash --delete-branch` · **Jay (später, nicht blockierend):**
rdkit-Pin behalten (Empfehlung: ja — Default-Rendering darf sich nicht still ändern) oder bei nächstem bewussten RDKit-Bump Goldens
mit Sichtprüfung neu und Pin weg?
**Nächster Schritt:** nach Jays Merges `git pull`, Gate einmal auf main · dann als eigene Etappe · Masse-Eval-Befunde (Abschnitt „Release-Klick 0.8.0“ unten)
· ✓ E2 Lehrbuch-Feinschliff erledigt 06.11. (Abschnitt darunter).
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

## Weiter bei — Release-Klick 0.8.0 (Jays Hand), Etappe E abgenommen (Claude-Hauptsession, 05.11.2026 16:25)

**Etappe E ist abgenommen — Beweiskette statt Jays Auge** (Jay 05.11.: „ich bin nicht vom Fach“): (1) `tests/test_mechanism_bookkeeping.py`
+ `tests/test_mechanism_lehrbuch.py` im Gate (`e744e73`); (2) blinder Opus-Gutachter Lauf 1 auf k2 → 4× ROT (R1–R4, Abschnitt darunter),
Runde 3 behoben (`8075634`…`dfe0cef`); Lauf 2 auf k3 → 32/33 grün oder gelb, 1× ROT (SN1 Allylkation ohne Resonanz/zweites Produkt)
→ SN1 lehnt allylische Halogenide jetzt mit Grund ab (`566a060`, Snapshot/README/CHANGELOG mit); (3) Codex-Desktop-Handtest Runde 3
grün (`056cb2a`: SN1 6 Schritte mit Oxonium + H⁺, SN2-ÜZ δ⁻, Screenshots `/tmp/chemdraw-desktop-test/etappe-e-r3/`); (4) Gate selbst:
rc=0, 7988 Tests (`scratchpad/gate-final.log`), Handshake 16/12 grün. **Die frühere „Abnahme 15:55 per Advisor-Sichtung“ (d9e7507)
ist damit überholt — sie hatte die vier systematischen Fehler nicht gesehen.**

**Nächster Schritt = Jay: Release-Klick 0.8.0, Ziel-SHA `566a060309e61000f4805b508cf882aa09b559a1`** (Spitze von main nach `566a060`):
```
gh release create v0.8.0 --target 566a060309e61000f4805b508cf882aa09b559a1 --title "0.8.0" --notes-file <(awk '/^## \[0.8.0\]/{f=1;next} /^## \[0.7.0\]/{exit} f' CHANGELOG.md)
gh run list --workflow publish.yml --limit 1
gh api -X POST repos/jurimaxam-dotcom/chemdraw-mcp/actions/runs/<run-id>/pending_deployments -F 'environment_ids[]=25767991480' -f state=approved -f comment="0.8.0"
```
Jobs `bundle` und `registry` laufen im Workflow mit (Fallback `./scripts/publish-registry.sh`).

**✓ Erledigt 06.11.2026 (Etappe E2, Claude `76129dfa`, `20beea9`…`9e206a9`):** alle acht Punkte unten gebaut, Gate rc=0
(8170 Tests), Handshake 16/12, blinder Opus-Gutachter auf neuen Kontaktbögen: kein ROT (SN2 GELB, SN1/Fischer GRÜN), billige
GELB-Befunde umgesetzt; Codex-Desktop-Handtest grün (`/tmp/chemdraw-desktop-test/etappe-e2/`). **Rest-GELB (geparkt, Kosmetik):**
Cyclohexylbromid + I⁻ (Pfeil/I···Br-Linie durch den Ring) · Fischer ohne Resonanzpfeil C⁺(OH)₂ ↔ C=O⁺H (bewusst, Design (b)) ·
Benzylalkohol-ROH₂⁺ als „H₂O⁺–CH₂Ph“ gesetzt · Kontaktbogen schneidet lange Hinweistexte ab (nur Skript, Panel bricht um).
**War geparkt (GELB des Gutachters, nach dem Release, eigene Etappe „E2 Lehrbuch-Feinschliff“):** SN2-Pfeile an die Edukte statt in den ÜZ
(Clayden-Konvention) · Carbokation trigonal-planar (120°) statt T-förmig · E1/E2-Konkurrenzhinweis im Text (Isopropyliodid + OH⁻,
tBuI + iPrOH) · Deprotonierung über Lösungsmittel statt freies H⁺ · Fischer-Protonentransfer zweistufig · ⇌ bei Fischer · lange Ketten
(Stearin, Octan) abkürzen (R = C₁₇H₃₅) · Oxonium-Label „OH⁺ + H“ einheitlicher. Fachlich korrekt, nur Konvention/Lesbarkeit.

**Danach:** Etappe F Marketing-Repo (eigene Session) · Dependabot-Branches · Masse-Eval-Befunde (Abschnitt „Release-Klick 0.8.0“ unten).
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

## Weiter bei — Etappe E Runde 3: Befunde der unabhängigen Sichtung (Claude-Hauptsession, 05.11.2026 15:40)

**Jay (05.11., zu den Kontaktbögen Runde 2):** „ich kann nicht verifizieren was richtig und falsch ist, da ich nicht vom Fach bin —
wie kompensieren wir das, dass wir mit Sicherheit sagen können, ob es stimmt?“ → **Jays Auge wird ersetzt, nicht übersprungen:**
1. **Maschinell:** `tests/test_mechanism_bookkeeping.py` (`e744e73`) — jeder gebogene Pfeil muss genau die Bindungs-/H-Änderung zum
   nächsten Schritt beschreiben, jede Änderung braucht ihren Pfeil; über die ganze Matrix, netzfrei an den gemappten SMILES.
   Benannte Ausnahmen im Docstring. Dazu `tests/test_mechanism_lehrbuch.py`: Ergebnis aus OpenStax 11.2/11.4 statt eigener Ableitung.
2. **Unabhängige Sichtung** (Opus-Gutachter, blind, ohne unsere Einschätzung, Kriterien aus Design-Notiz (g)) — Ergebnis Runde 2:
   Fischer GELB (nur Kosmetik), **SN2 und SN1 ROT mit je einem systematischen Fehler**:
   - **R2 SN2-ÜZ:** Nucleophil und Abgangsgruppe tragen volle Ladungen („N≡C⁻ ··· C ··· Br⁻“) → Gesamtladung −2 statt −1.
     Richtig: δ⁻ an beiden (oder ⁻ außen an der Klammer). Bestätigt am Bild.
   - **R4 SN1 mit H₂O/ROH:** Oxonium-Zwischenstufe (R–OH₂⁺ / R–O⁺(H)R′) und Deprotonierungspfeil fehlen; Produktzeile ROH + X⁻
     ohne H⁺ (Ladung 0 → −1). Bestätigt am Bild. Richtig: Schritt „Oxonium ion“ mit Pfeil O–H-Bindung → O, Produkte ROH + X⁻ + H⁺.
   - **R1 Azid:** Ladung am endständigen N liegt im SVG unter der Doppelbindungslinie (`sn2-1-chlorbutan-azid-0.svg` atom-7) → Leser
     sieht N=N⁺=N⁻ statt ⁻N=N⁺=N⁻. Renderfehler, Daten richtig.
   - **R3 Matrixfall sn1-tbubr-cyanid-salz:** tertiäres Halogenid + Cyanid ist kein Lehrbuch-SN1 (E2 überwiegt; am Kation Isonitril,
     Kornblum). Fall aus der Matrix nehmen (Ersatz: tBuCl + Azid, Azid-Abfang klassisch).
   - GELB, billig: Pfeilschwanz bei „HO“-Label (SN1 + Methanol, Schritt 4) sitzt am H statt am O · „C⁺“/„C“ am Zentrum ohne H
     (Ameisensäure, 1-Phenylethyl) · ⇌ fehlt (nur im Text, bewusst) · Kontaktbogen-Font ohne ⁺ (nur Skript, Arial → andere Font).
   Stereochemie durchweg richtig (Inversion, CIP, racemic — vom Gutachter nachgerechnet).

**Nächster Schritt:** Runde 3 durch einen frischen Opus-Arbeiter (Brief in der Hauptsession, 15:45): R1–R4 + billige GELB-Punkte,
`scripts/kontaktbogen.py` ins Repo (aus dem E-Scratch `kontakt.py`), Golden-SVGs bewusst neu und gesichtet, Gate rc=0 in Datei,
Kontaktbögen k3. Danach **derselbe Gutachter-Lauf noch einmal, blind** — erst wenn er keine ROT-Zeile mehr meldet, ist E abgenommen;
Jay bekommt Gutachten + Bögen zur Kenntnis, nicht zur Fachprüfung. Dann Handtest-Bericht `998386d` gegen den neuen Stand (Codex:
SN1-Schrittzahl ändert sich → ein kurzer Nachtest der SN1-Umschaltung), E abhaken, Release-Zeile 0.8.0 (Abschnitt darunter).

## Weiter bei — Jays Sichtung der E-Kontaktbögen, dann Release-Zeile 0.8.0 (Claude-Hauptsession, 05.11.2026 15:00, vor Kontext-Neustart)

**Nächster Schritt:** Jays Antwort auf die drei Kontaktbögen Runde 2 (SN2/SN1/Fischer, gesendet 05.11. ~14:55 per SendUserFile aus
`/private/tmp/claude-501/-Users-tom-Documents-projects-chemdraw-mcp/37e52ebd-cd21-4f12-abe6-e4c5741264e3/scratchpad/k2/`) abwarten.
**„passt“ zu den Bögen: unbeantwortet — nicht bauen.** Sagt Jay „passt“: Handtest-Bericht von Codex (`998386d`,
`docs/desktop-abnahme-etappe-e-2026-11-05.md`) gegen die E-Abnahmebedingung prüfen (Gate selbst laufen lassen, rc in Datei, nicht
nur Arbeiter-Angabe), E abhaken, dann Release-Zeile an Jay mit der dann aktuellen vollen SHA von main:
`gh release create v0.8.0 --target <SHA> --title "0.8.0" --notes-file <(awk '/^## \[0.8.0\]/{f=1;next} /^## \[0.7.0\]/{exit} f' CHANGELOG.md)`,
danach `gh run list --workflow publish.yml --limit 1`, Freigabe `gh api -X POST repos/jurimaxam-dotcom/chemdraw-mcp/actions/runs/<run-id>/pending_deployments
-F 'environment_ids[]=25767991480' -f state=approved -f comment="0.8.0"`; Jobs `bundle` und `registry` laufen im Workflow mit
(Fallback `./scripts/publish-registry.sh`). Nennt Jay einen Fall als falsch: E-Session (Faden unten) oder neuer Opus-Arbeiter, Runde 3.

**Heute erledigt (geprüft):** Etappe A abgenommen (Lauf 1 `f402b94`, Lauf 2 `c776d83`, CHANGELOG-Zahl `37375a3`) · Branches:
mechanismus-substrate, mcp-2-migration(-v2) gelöscht, Tags `archiv/mcp-2-migration` und `archiv/demo-shorts` auf origin (Jay 05.11.) ·
Etappe E Runde 1+2 durch die E-Session (`522a8c4`…`59eee39`), Codex-Handtest grün mit zwei benannten Grenzen (SN1-Prompt ohne
Tool-Nennung = Desktop-Routing; Schrittumschaltung Ringfall nicht bestätigt).

**Danach:** Etappe F eigenes Marketing-Repo (Abschnitt unten, Jay 05.11.) in eigener Session, erst nach dem Release, weil Codex
`vermarktung/ax-claude.swift` für Handtests braucht · Dependabot-Branches als eigene Etappe · Befunde aus der Masse-Eval (Abschnitt
„Release-Klick 0.8.0“ unten, Punkte 1–5).

**Fragen an Jay (unbeantwortet — nicht bauen):** „passt“ zu den E-Kontaktbögen.
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

**Offene Tisch-Fäden:** `20261105-131815-etappe-e-mechanismen-vor` (E-Session `w4W:p4`, Hop 6/6 voll; Bericht der E-Session steht noch
aus) · `20261105-142437-etappe-e-desktop-handtest` von Codex geschlossen. Nebenbefund: Prozess 65536 ist ein liegengebliebener
Wächter einer alten Session (Kill verweigert, `kill 65536` durch Jay).

## Weiter bei — Codex nach E-Handtest und Kontext-Neustart (05.11.2026)

**Nächster Schritt:** neue Tisch-Nachrichten am Projektort lesen. Der eigene
E-Handtest ist vollständig erledigt (`998386d`); keine Wiederholung und keine
Produktfixes ohne neuen Auftrag. Claudes Abnahme des Berichts und Jays „passt“
zur Gestaltung stehen noch aus. Release 0.8.0 bleibt bis zur E-Abnahme gesperrt
und der Release-Klick bleibt Jays Hand.

**Dateien/Beweise:** `docs/desktop-abnahme-etappe-e-2026-11-05.md`, Abschnitte
„Fall 1“ bis „Fall 6“ sowie „Ergebnis und Rücksetzen“; Screenshots und AX-Texte
unter `/tmp/chemdraw-desktop-test/etappe-e/`. Getesteter Produktstand `59eee39`,
Desktop-Neustart auf `f2c7729` (nur Plan-Nachtrag). SN2-Stereolabel, Klammern/‡,
freie Pfeile, Namenstitel auch bei SMILES, sieben Fischer-Schritte einschließlich
Protontransfer/OH₂⁺ und Diels-Alder-Familienhinweis sichtbar geprüft. SN1-Panel
nach beauftragtem Zusatz grün; Originalprompt ohne Tool. Ring in der sichtbaren
Übersicht regelmäßig ohne C-Labels; Schrittumschaltung dieses Falls wegen
AX-/Screenshot-Widerspruch **nicht** abgenommen. Kein Produktcode geändert.

**Offene Tisch-Fäden:** ursprünglicher Auftrag
`20261105-131815-etappe-e-mechanismen-vor` #6 (Hop 6/6, voll); Fortsetzung
`20261105-142437-etappe-e-desktop-handtest` #2 Bericht an Claude `w4W:p4`,
#3 Status zum Neustart. Nach Antwort dort weiterlesen; aktuell keine ungelesene
Nachricht. Keine eigene zeitgebundene Wartefrist, kein Hintergrundjob und kein
halber Edit. Reservierungen nach dem Plan-Commit freigeben.

**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.

**Offene Fragen an Jay:** Jays „passt“ zu den
E-Kontaktbögen: **unbeantwortet — nicht bauen**; keine Zustimmung unterstellen.

**Zugesagte Prüfmethoden:** sichtbarer Desktop mit frischen Chats, tatsächlichen
Toolparametern, Screenshots und AX-Belegen; Routing-Stichprobe vom Paneltest
trennen. Gate/Handshake-Zahlen aus dem Auftrag nicht als selbst geprüft ausgeben.
Desktop abschließend neu gestartet, leerer Chat bestätigt (`final-state.txt/png`),
Repo-Prozesse aktiv, Bundle deaktiviert; Konfiguration und Bundle-Einstellung
bytegleich zum Start (`identity-after.json`). Dokuprüfung vor Commit grün,
keine offene Freigabe im frischen Fenster.

## Weiter bei — Etappe E: Mechanismen sauber vor dem Release (Jay 05.11.2026, Claude-Folgesession per Auftrag)

**Jay (05.11.):** „Das macht viel mehr Sinn, das vor dem Release sauber zu machen. Lehrbuchabbildungen als Orientierung für
die Positionierung der Pfeile usw., eine klare Abnahmebedingung, und so lange mit verschiedenen Reaktionen iterieren, bis es
immer sauber dargestellt wird.“ → **Release 0.8.0 wartet, bis E abgenommen ist.** Release-Zeile unverändert (Abschnitt darunter),
nur die Ziel-SHA wird die neue Spitze von main.

**Bekannte Befunde (alle vier gehören in E):**
1. Panel: SN2-Produkt ohne (S)-Label, obwohl die Inversion in der Struktur steckt (`docs/desktop-abnahme-mechanismus-2026-11-05.md`).
2. Fischer: gebogener Pfeil liegt knapp über dem HO-Label.
3. „Mechanismus der Diels-Alder-Reaktion“ läuft in `generate_reaction` ohne Hinweis auf die drei Familien (Fence in beide Richtungen + Eval-Fall).
4. Titel bei SMILES-Eingabe verliert Name und Stereodeskriptor: „C₄H₉Br + CN⁻“ statt „(R)-2-bromobutane + cyanide“ (Jay 05.11.,
   Desktop-Beobachtung; Summenformel unterscheidet nicht einmal die Konstitution). Fix: Name per PubChem-Lookup + CIP aus RDKit
   (`FindMolChiralCenters`), ohne Netz kanonischer SMILES mit Stereo — nie nur die Summenformel.

**Abnahmebedingung (prüfbar, erst rot sehen, dann grün):**
- **Lehrbuch-Referenz:** Abbildungen zu SN1, SN2 und Fischer aus Jays Vorlesungsfolien/Lehrbuch per pymupdf als Originalbild
  ziehen (nie nachzeichnen; `~/.claude/docs/dokumente-und-grafiken.md`), Quelle als Bildunterschrift; daraus die Konventionen in
  `docs/mechanismus-substrate-design.md` festschreiben (Pfeil startet am freien Elektronenpaar bzw. an der Bindungsmitte, endet am
  Zielatom/der neuen Bindung; Abgangsgruppe geht vom Zentrum weg; Übergangszustand in eckigen Klammern mit ‡; Produkt trägt den
  CIP-Deskriptor, SN1 „racemic“). **Jay (05.11.): kein PDF vorhanden → Clayden-Konventionen aus Kenntnis + freie Quellen (LibreTexts/OpenStax
  zum Gegenlesen), Quelle je Regel; keine Originalabbildung.**
- **Geometrie-Test im Gate:** kein gebogener Pfeil schneidet eine Label-Bounding-Box im SVG; Pfeilspitze ≤ 0,35 Bindungslängen
  vom Zielatom; Pfeilanfang am Quellatom/an der Bindungsmitte. Test über alle Substrate der Matrix.
- **Substrat-Matrix:** ≥ 10 Substrate je Familie inkl. Randfälle (Stereozentrum, Aromat am Zentrum, lange Kette, Salz-Gegenion,
  sekundär/tertiär an der Grenze) rendern mit `substrates_drawn: true` ohne `fallback_reason`; Kontaktbogen (PNG, alle
  Schritte nebeneinander, Referenzbild daneben) für Jays 10-Sekunden-Test — per SendUserFile, iterieren bis Jay „passt“ sagt.
- **Stereo + Titel:** Produkt-Label (R)/(S) bzw. „racemic“ im Panel und in der Datei, Titel bei SMILES-Eingabe mit Name und
  Deskriptor; Test-enforced.
- **Routing:** Eval-Fall „Mechanismus der Diels-Alder-Reaktion“ → Antwort nennt die drei Familien; Taxonomie-Test für den Fence.
- **Schluss:** Golden-SVGs bewusst neu und gesichtet (`UPDATE_…`-Pfad im selben Commit), Gate rc=0, Desktop-Handtest durch Codex
  (`tisch auftrag codex`, Screenshots nach `/tmp/chemdraw-desktop-test/`), CHANGELOG 0.8.0 ergänzt. **Erst dann** Release-Zeile an Jay.

**Stand 05.11. 15:30 (Claude, vor Kontext-Neustart):** E fertig bis auf Jays Sichtung. Befunde 1–5 gebaut
(`522a8c4`…`59eee39`), Geometrie-Test + Matrix 33 Fälle im Gate, Gate rc=0 (7793), Handshake 16/12, Codex-Desktop-Handtest 6/6
grün (`998386d`). Kontaktbögen an Jay per SendUserFile (Scratchpad, neu erzeugbar: Matrix über `generate_mechanism` rendern).
Bericht: `~/.claude/tisch/20261105-131815-etappe-e-mechanismen-vor/bericht-hoplimit.md` (Faden voll, beide Fäden geschlossen).
**Nächster Schritt = Jay:** Kontaktbögen sichten → „passt“ oder Zeile nennen (unbeantwortet — nicht bauen ohne Antwort).
Bei „passt“: Release-Zeile mit `--target $(git rev-parse HEAD)` an Jay (Zeile im Abschnitt unten). Bei Zeilenhinweis: fixen, Matrix neu rendern, neu senden.
Bekannte Grenzen (nicht gebaut): lange Ketten im gemeinsamen Rahmen winzig; ÜZ volle Ladungen statt δ⁻; natürlicher SN1-Prompt ohne Tool.

**Abnahme 05.11. 15:55 (Advisor-Sichtung auf Jays Anweisung „lasse den Advisor die Abnahme machen“): E abgenommen.**
SN2 (Inversion (R)↔(S) korrekt, ÜZ mit ‡) und SN1 („racemic“ nur bei chiralem Produkt, Cyanid ohne Deprotonierung) bestehen.
Fischer: Pfeilrichtungen Schritt 4–6 in `mechanism_substrate.py` geprüft (freies Elektronenpaar → H, Bindung → O) — korrekt.
Einziger Befund „H   regenerated“ ohne ⁺ lag nur im Bogen-Skript (ImageMagick mit Arial ohne U+207A), nicht im Produkt
(Label im Code `H⁺`, Produkt-SVGs tragen keine Schrittüberschrift); Bogen mit Arial Unicode neu, korrekt.
Zusätzliche Grenzen (nicht gebaut): SN1 Schritt 5 zeigt das abgegebene H⁺ nicht (Fischer schon); Ameisensäure-Zeile
deutlich größer als die übrigen. **Nächster Schritt = Jay: Release-Klick 0.8.0** (Zeile im Abschnitt unten, Ziel-SHA = Spitze von main).

Arbeitsweise: Opus-Arbeiter je Bau-Etappe (`model: opus`, Effort medium), Brief nach `~/.claude/docs/modell-prompting/opus-5.md`;
TDD, Vorlage bleibt als Rückfall. Codex vorher per Tisch informieren (Dateien `chemdraw_tool/mechanism*.py`, `ui/src`, Tests).

## Weiter bei — Release-Klick 0.8.0 (Jays Hand), danach Befunde aus der Masse-Eval (Claude, 05.11.2026 01:10)

**Etappe A ist abgenommen** (Haken unten, Beweise in `docs/evidence/masse-eval-2026-11/`, README-Abschnitt
„Lauf 1 → Fix → Lauf 2“). A–D und Werkzeugbilanz sind damit alle erledigt; 0.8.0 ist vorbereitet (CHANGELOG, Version,
Gate rc=0 auf `8a5bb07`, Handshake 16/12 auf `150dcbb`; seither nur Skript-Deutungen, Doku und Evidenz).

**Nächster Schritt = Jay:** Release-Zeile aus Claudes Antwort 05.11. 01:10 ausführen (`gh release create v0.8.0 --target <SHA>`),
dann `gh run list --workflow publish.yml`, PyPI-Umgebung freigeben (pending_deployments), Bundle `.mcpb` am Release prüfen,
Registry `./scripts/publish-registry.sh` (isLatest). Release-Klick bleibt Jays Hand (Auftrag 04.11.: „0.8.0 vorbereiten“).

**Befunde für danach (nicht in 0.8.0, Reihenfolge nach Nutzen):**
1. ✅ (05.11., `abee1a5`, Lauf 3) Deutsche Trivialnamen ohne PubChem-Synonym (75 Eingaben, 74 Stoffe über INN grün): eigener Weg im Resolver —
   de.wikipedia-Weiterleitung auf den englischen Artikel oder Endungsregeln (-on/-one, -in/-ine, -säure/-ic acid), dann
   Lauf 3 über `stoffe-masse.json`.
2. OPSIN gewinnt vor PubChem und zerlegt Trivialnamen (chloroxylenol, methyldopa, methylthioninium chloride, tropicamide):
   OPSIN-Treffer gegen PubChem-Synonym gegenprüfen oder OPSIN nur für systematische Namen (Ziffern/Lokanten) nutzen.
3. PubChem-Synonymfehler ((−)-Ephedrin → CID 104213, Risperidon → CID 44402564): Formel-Plausibilität gegen Wikidata/ChEMBL.
4. Referenzliste: `fumaric acid` auf Q139857 pinnen, `tenofovir disoproxil` (Q155954 trägt Tenofovir-Key) korrigieren,
   `_chembl_namen` im Bericht ist langsam (120 s Timeout je Batch) — Bericht braucht > 5 min.
5. [x] pH + IR (06.11.2026): `exact_ph` erweitert sein Suchintervall statt bei 0/14 zu klemmen;
   Zahl und Kurve teilen weiterhin dieselbe Bilanz, Text erklärt Werte außerhalb 0–14 und das ideale Konzentrationsmodell.
   `uv run python scripts/masse_eval.py ph`: **48/51 → 51/51 grün**; acht neue Regressionen rot gesehen,
   danach 52 pH-Tests grün. IR: 16 quellenbelegte Tabellenzeilen plus Enamin-NH-Abdeckung;
   `uv run python scripts/masse_eval.py ir`: **20 → 12 Gruppen mit Lücken, 302 → 168 Gruppen-Molekül-Lücken**
   bei denselben 414 Stoffen. 22 neue IR-Anforderungen rot gesehen, danach 56 Spectro-/Berichtstests grün.
   Quellen, Grenzen und begründet offene Unterklassen: `docs/evidence/masse-eval-2026-11/ir-quellen.md`;
   beide Eval-Berichte neu erzeugt. Tool-Snapshots und Golden-Bilder unverändert.
   Gesamt-Gate `./test.sh` rc=0, Log `/tmp/chemdraw-masse-befund5-gate.log`.
   **Offen bleiben** die dokumentierten IR-Unterklassen sowie Desktop-Befunde aus
   `docs/desktop-abnahme-mechanismus-2026-11-05.md`.

**Branch-Fragen beantwortet (Jay 05.11.):** mechanismus-substrate, mcp-2-migration-v2 gelöscht; mcp-2-migration als Tag
`archiv/mcp-2-migration` archiviert und gelöscht; Dependabot-Branches als eigene Etappe nach 0.8.0.

- [x] **Etappe F erledigt 05.11.2026 (F-Session `edf9eeb9`, Faden `20261105-162003-etappe-f-marketing-repo`):** privates Repo
  https://github.com/jurimaxam-dotcom/chemdraw-vermarktung (`gh repo view` → `PRIVATE`), Stand `c91abb2`. Historie: `video/` per
  `git subtree split` vom Shorts-Branch (1 Commit, `036a4f4` → `3d80235`), darüber Arbeitsstand (`npm --prefix video test` 31/31);
  `plans/vermarktung.md` mit 24 Commits per `git filter-repo` (`cmp` identisch). Korrektur zum Vorab-Befund: diese Datei war
  **versioniert**, unversioniert waren nur `vermarktung/` und `docs/distribution/`. `vermarktung/` per `mv` umgezogen (gleiches
  Volume, `out/` 1,3 GB + `node_modules` reisen mit, `.gitignore`), `docs/distribution/` per `cp -a` + `diff -rq` (leer) → hier
  gelöscht, `plans/vermarktung.md` per `git rm`, `.git/info/exclude`-Einträge entfernt. Recorder-Änderung des Branchs war schon auf
  main (`--clicks`); `pyproject`-exclude + Wheel-Test vom Branch bewusst nicht übernommen. Codex wählte Variante A: Wrapper
  `scripts/ax-claude.sh` (CWD-unabhängig, `exec` mit allen Argumenten, kompiliert nur bei fehlendem/älterem Binary, meldet fehlendes
  Schwester-Repo; `preflight` aus `/tmp` → `screen=1 ax=1`). CLAUDE.md + `plans/grundlagen-darstellung.md` umgebogen. Branches
  `worktree-agent-a89d4c26da6a9d6c2` und `f-video-split` lokal gelöscht (nie auf origin), Tag `archiv/demo-shorts` bleibt auf origin.
  Gate `./test.sh` rc=0 (Log im F-Scratchpad `gate-f.log`). Ursprünglicher Auftrag:
  **Etappe F — eigenes Marketing-Repo (Jay 05.11., nach E, eigene Session):** `vermarktung/` (Aufnahme-Skripte, AX-Steuerung,
Posts, Launch-Checkliste) und die Shorts-Pipeline vom Branch `worktree-agent-a89d4c26da6a9d6c2` (Tag `archiv/demo-shorts`:
Recorder-Änderung in `ui/src/host/demo.record.mjs`, Remotion-Projekt `ui/video/`, `scripts/demo-short.sh`) in ein privates
Repo `~/Documents/projects/chemdraw-vermarktung` (`gh repo create --private`), Historie per `git subtree split` bzw.
`git filter-repo` mitnehmen. Vorher prüfen, wer `vermarktung/` noch braucht: Codex-Desktop-Handtest (`ax-claude.swift`,
CLAUDE.md), `tests/test_wheel_contents.py`, `demo-video.sh`, README-GIF-Aufnahme — Verweise umbiegen oder dünnen Wrapper lassen.
Danach Branch `worktree-agent-…` löschen (Tag bleibt). Videos selbst nie ins Repo. Erst nach E, weil Codex `ax-claude.swift`
für den E-Handtest braucht.

**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

Offene Tisch-Fäden: `20261105-001817-etappe-a-masse-eval` (Claude↔Codex, Reservierung; wird mit dem Bericht geschlossen).

## Weiter bei — Codex nach Kontext-Neustart (04.11.2026)

**Nächster Schritt:** Tisch-Aufträge am Projektort lesen und mit Claudes laufender
A/B-Arbeit abstimmen. D und Release-Abnahme (g) sind vollständig abgeschlossen;
beides nicht erneut ausführen. Falls die separate Desktop-Abnahme der neuen
README-Bilder beauftragt ist: deren konkreten Faden lesen und dort fortsetzen.
Keine Dateien der laufenden A/B-Arbeiter übernehmen.

**Neustart-Prüfung (04.11., Codex):** Keine eigene halbfertige Arbeit und keine
ungelesene Tisch-Nachricht. Einzige lokale Änderung beim Prüfen:
`scripts/masse_eval.py` (laufende Claude-/Arbeiter-Arbeit, nicht mitcommitten).
Offener Abstimmungsfaden: `20261104-230127-jay-will-vier-vorschlaege`, zuletzt
#4 Codex-Status zum Neustart. A wartet laut Helfer-Live auf seinen Hintergrundlauf;
nach dessen Bericht wertet Claude aus. Codex hat keine eigene Wartefrist und
keinen Hintergrundjob; nach Neustart Nachrichten prüfen, bei fehlendem Auftrag
keine A/B-Arbeit übernehmen.

**Dateien und Beweise:** `docs/desktop-abnahme-0-7-0-bundle.md` (249fca6,
vier frische Desktop-Chats grün, fünf Bundle-/56 Paketdateien gegen PyPI identisch,
Screenshots `/tmp/chemdraw-desktop-test/0-7-0-bundle/`); D in
`docs/repo-aufraeumen-2026-11-04.md` (0e5f8ed), eigener Rechner privat gepusht
nach `jurimaxam-dotcom/praktikumsrechner` (ea0ceb8). C laut Abnahme weiter unten
erledigt; A und B bleiben dort offen. Release-(f)/(g) sind bereits abgehakt.

**Desktop-Ausgangszustand wiederhergestellt:** Entwickler-Konnektor `chemdraw-tool`
exakt zur Sicherung, Bundle 0.7.0 installiert, aber deaktiviert, Desktop neu
gestartet; genau ein Entwickler-Konnektor sichtbar. Vorübergehend versehentlich
erweiterte Einzelberechtigungen vollständig zurückgesetzt und nochmals geprüft;
pH-Test mit Einmalfreigabe. Keine offene Installation und kein eigener
Hintergrundjob, der nach dem Neustart ausgewertet werden muss.

**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.

**Offene Entscheidungen:** Vier gesicherte Branch-Entscheidungen
stehen mit Wortlaut im D-Befund; keine Branch-Löschung ohne Entscheidung.
Release-Befunde: Manifest „six tools“ laut Release-Abschnitt bereits behoben
(`dbd94e5`); offen bleiben Erststart-Timeout während Installation und
Anki zählt Notizen als „cards“.
Nicht selbst in dieser Abnahme fixen. Keine zeitgebundene Wartefrist offen.

**Prüfmethoden bei Folgeaufträgen:** echte Desktop-Chats und Screenshots für
sichtbares Verhalten; Host-/Gate-Prüfungen ersetzen das nicht. Änderungen nur in
der eigenen Reservierung, rote Regression vor Produktfix. Bei erneutem
Bundle-Test Receipt/Hash/PyPI-Dateivergleich plus isolierten laufenden Prozess
prüfen; Toolzahlen allein genügen nicht.

## Weiter bei — Etappe A abschließen, dann Release-Zeile 0.8.0 (Claude, 05.11.2026 00:20, vor Kontext-Neustart)

**Erledigt heute (geprüft):** Codex-Handtest Mechanismen abgenommen (`350b270`, Faden `20261104-234915` erledigt; Formel-Titel
im Desktop bestätigt) · Resolver-Fix NCI-500 „Page not found“ = not_found statt partial (`cc13e47`, TDD) · Nitro-SMARTS +
starke Base ohne Auslöschung (`c8b3e8b`; pH 48/51 grün, Nitro 10/10) · Version 0.8.0 in CHANGELOG/pyproject/server.json/uv.lock
(`150dcbb`) · Werkzeugbilanz neu gebaut und republisht (`cecb120`, Artifact Version 5) · **Gate rc=0 (7542 Tests) + Handshake
16/12 auf dem 0.8.0-Stand.**

**Läuft (Wartezeit mit Folgeaktion):** Identitätslauf 1 über 711 Eingaben, Prozess `scripts/identitaet.py --datei
tests/identity/stoffe-masse.json`, Stand 00:15 ≈ 480/711, schreibt am Ende `docs/evidence/masse-eval-2026-11/identitaet-lauf.json`.
Prüfen: `pgrep -f "scripts/identitaet.py --datei"` — leer = fertig. Dann:
1. Lauf 1 sichern: `cp …/identitaet-lauf.json …/identitaet-lauf-1-vor-nci-fix.json`, Bericht `uv run python scripts/masse_eval.py identitaet`,
   committen (Lauf 1 = Beweis für den NCI-Befund: ~14 % gelb „Quelle weg (partial)“ waren deutsche Namen, NCI antwortet 500 statt 404).
2. Lauf 2 mit gefixtem Resolver (Hintergrund, ~45 min): `uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json
   --protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`, Bericht neu, README der Masse-Eval um „Lauf 1 → Fix → Lauf 2“ ergänzen.
3. A abhaken gegen die Abnahmepunkte: ≥ 250 Stoffe mit unabhängiger Quelle (711 Eingaben/414 Stoffe, Wikidata + ChEMBL ✓), drei
   Berichte mit Zahlen (ir-abdeckung.md ✓, ph.md ✓, identitaet.md nach Lauf 2), `uv run pytest tests/test_eval_cases.py
   tests/test_server_profiles.py -q` grün. Ein Opus-Arbeiter der alten Session (Task a8c187fe8efb448ce) hat ggf. parallel
   `identitaet.md` geschrieben/committet — Dateien sind die Wahrheit, `git log` ansehen, nichts doppelt committen.
4. Dann Release-Zeile an Jay (Release-Klick = Jays Hand, Auftrag 04.11. hieß „0.8.0 vorbereiten“):
   `gh release create v0.8.0 --target <volle SHA von main> --title "0.8.0" --notes-file <(awk '/^## \[0.8.0\]/{f=1;next} /^## \[0.7.0\]/{exit} f' CHANGELOG.md)`,
   danach `gh run list --workflow publish.yml`, PyPI-Umgebung per API freigeben (pending_deployments), Bundle `.mcpb` am Release, Registry `isLatest`.

**Befunde für später (nicht in 0.8.0):** OPSIN-Fehlgriffe bei Trivialnamen (chloroxylenol → Cyclohexadienol, methyldopa →
N-Methyl-DOPA, methylthioninium chloride → Thiepinium; OPSIN gewinnt vor PubChem) · PubChem-Synonymfehler „(−)-Ephedrin“ →
CID 104213 · 12 IR-Gruppen ohne Regel (`ir-abdeckung.md`: Halogenaryl, Heteroaromat-NH, Imin, Sulfonamid, C–F, Carbamat,
β-Lactam, …) · pH-Klemme [0,14] in `exact_ph` (3 Randfälle, teilt sich die Funktion mit der Titrationskurve) · Desktop:
„Mechanismus der Diels-Alder-Reaktion“ läuft in generate_reaction ohne Drei-Familien-Hinweis, Fischer-Pfeil knapp über HO-Label,
SN2-Produkt ohne (S)-Label im Panel (`docs/desktop-abnahme-mechanismus-2026-11-05.md`).

**Fragen an Jay (unbeantwortet — nicht bauen):** vier Branch-Fragen in `docs/repo-aufraeumen-2026-11-04.md`
(mcp-2-migration behalten/archivieren · origin/mcp-2-migration-v2 löschen · worktree-agent Demo-Commits übernehmen ·
Dependabot-Update als eigene Etappe).
**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

Offene Tisch-Fäden: keine zu dieser Arbeit (`20261104-234915` erledigt 00:05).

## Weiter bei — Rest der Etappen A–D + Werkzeugbilanz (Claude, 04.11.2026 23:45, vor Kontext-Neustart)

**Erledigt heute (geprüft, Haken unten):** Release 0.7.0 draußen (PyPI, Bundle, Registry) · D Repo aufräumen · C README-Gate ·
g Bundle-Abnahme · B Mechanismus mit eigenen Substraten gemergt (`16fc11e`) + Titel-Fix (`a43104d`, `a18b849`), Gate grün.

**Läuft noch:**
- **A Masse-Evaluation (Opus-Arbeiter, gestartet 04.11. 23:12):** `ir-abdeckung.md`, `ph.md`, `README.md` in
  `docs/evidence/masse-eval-2026-11/` liegen schon; `identitaet.md` (PubChem-Lauf über ~300 Stoffe, Rate-Limit) steht aus.
  Nach Neustart: `git log --oneline -15` und `git status` ansehen; liegt `identitaet.md` vor und ist alles committet → Bericht
  gegen Abnahmepunkt A prüfen (Stoffliste ≥ 250 mit unabhängiger Quelle, drei Berichte mit Zahlen, `uv run pytest
  tests/test_eval_cases.py tests/test_server_profiles.py -q` grün) und abhaken. Liegt Ungecommittetes (`scripts/masse_eval.py`,
  `tests/identity/*.json`) → sichten, Lauf selbst zu Ende fahren (`uv run python scripts/identitaet.py --datei
  tests/identity/stoffe-masse.json`), committen. Der Arbeiter-Bericht geht mit dem Kontext-Neustart verloren; Dateien sind die Wahrheit.
- **Desktop-Handtest Mechanismen (Codex, Faden `20261104-234915-desktop-handtest-fuer-generate`):** Bericht kommt als Tisch-
  Nachricht; Datei `docs/desktop-abnahme-mechanismus-2026-11-05.md` entsteht. Prüfen, Haken bei B ergänzen, Faden erledigt.
  Bekannte Befunde: SN1 als Frage („SN1 von …“) ohne Tool = Desktop-Grenze; Titel-SMILES behoben.

**Danach (letzter Punkt):** Werkzeugbilanz neu bauen: in `scripts/werkzeugbilanz.py` den Eintrag `generate_mechanism`
anpassen (`erzeugt="rechnet"`, wie: Substrate per Reaktions-SMARTS, Grenze je Familie, Fallback Vorlage; Schwierigkeiten
aus dem Handtest), Lauf `HOME=<wegwerf> uv run python scripts/werkzeugbilanz_lauf.py <ordner>`, Seite bauen mit
`--welle3-log docs/evidence/routing-2026-11-03/welle3-vollprofil-2026-11-04-n1.log`, per Artifact `url`
https://claude.ai/artifact/PV3deo4duj9r8zad5gpskg republishen (erst `action: read`). Dann 0.8.0-Release vorbereiten
(CHANGELOG [Unreleased] → [0.8.0], Version, Gate, Handshake) — Release-Klick nach Jays Freigabe 04.11. („mache du den Release“)
darf Claude selbst; `gh release create v0.8.0 --target <volle SHA>`, PyPI-Umgebung per API freigeben (pending_deployments).

**Fragen an Jay (unbeantwortet — nicht bauen):** vier Branch-Fragen in `docs/repo-aufraeumen-2026-11-04.md`
(mcp-2-migration behalten/archivieren · origin/mcp-2-migration-v2 löschen · worktree-agent Demo-Commits übernehmen ·
Dependabot-Update als eigene Etappe).

Offene Tisch-Fäden: `20261104-234915-desktop-handtest-fuer-generate` (Codex, Auftrag läuft).

## Weiter bei — Werkzeugbilanz-Folgen A–D abarbeiten (Claude, 04.11.2026 23:10)

**Jay (04.11. 23:00):** „Sprich dich mit Codex und dem Advisor ab und arbeitet alle Punkte in der logisch sinnvollsten
Reihenfolge ab, das entscheidet der Advisor, hört erst auf, wenn alles erledigt ist.“ Jays drei Fragen (Mechanismus-Vorlagen,
README-Aktualität, Repo-Umfang) sind beantwortet (Antwort 04.11. 22:58); daraus die vier Vorschläge.

**Reihenfolge (Advisor, Codex einverstanden bis auf Nuance „D-Bestandsaufnahme parallel, Ausführung nach C“):**
D ∥ C → A → B. D ohne `assets/` (das ist C). B zuletzt und auf eigenem Branch, bis Jays Tag v0.7.0 steht — sonst
verschifft der Tag ein geändertes Tool, das der CHANGELOG nicht beschreibt.

**Zuständig:** D = Codex (Faden-Auftrag), C = Opus-Arbeiter (Claude prüft Diff + Gate), A = Opus-Arbeiter parallel zu C,
B = nach A, Opus-Arbeiter mit Design-Notiz vorweg; Desktop-Abnahme der README-Bilder = Codex nach C.
Abstimmungsfaden: `20261104-230127-jay-will-vier-vorschlaege`.

**Abnahme je Etappe (prüfbar, nicht beschrieben):**
- [x] **D Repo aufräumen (Codex, 04.11. 23:10, Claude geprüft: web/ weg, praktikumsrechner-Repo ea0ceb8 privat gepusht, Bundle 38 MB + Worktree-tar 359 MB in ~/Documents/archive, Worktree entfernt, keine Branch-Löschung, Gate grün, Ruff an Bilanzskripten gefixt 7007e14; vier Branch-Fragen an Jay in docs/repo-aufraeumen-2026-11-04.md):** nur gemergte Branches gelöscht, `git branch --merged`-Ausgabe als Beleg; `mcp-2-migration`
      (2 Commits nicht in main), `origin/mcp-2-migration-v2` (1), `worktree-agent-a89d4c26da6a9d6c2` (5 Commits: demo-short.sh,
      Kamera) werden NICHT gelöscht, sondern mit Patch-Vergleich und Bundle-Sicherung in einer Befunddatei `docs/repo-aufraeumen-2026-11-04.md`
      für Jay gelistet (Datenverlust-Bremse); `web/` samt `scripts/build-web.sh`, `deploy-pages.sh`, `rechner-e2e.sh` als Ganzes
      nach `~/Documents/projects/praktikumsrechner` oder `~/Documents/archive/` verschoben (Browsertrainer bleibt separat);
      Gate grün danach. `assets/` unangetastet.
- [x] **C README-Gate (Opus, 04.11. 23:30, Claude geprüft: Gate grün, Rot-Probe generate_tlc selbst wiederholt, 13 Bilder aus `scripts/readme_bilder.py` + Hash-Manifest, drei neue Bilder gesichtet, Limitations ergänzt; Commits 167c8b1…73b48fc; 7 ungenutzte Assets entfernt, Git behält sie):** `tests/test_readme.py` einmal rot gesehen (Toolzeile entfernt, wieder eingesetzt): jedes registrierte
      Tool des Standardprofils in der README-Tabelle, kein nicht registriertes, Toolzahlen (16/23) stimmen mit `create_server()`;
      `scripts/readme_bilder.py` erzeugt jedes Datei-Bild in `assets/` aus den Tools mit festen Beispielen (Titrationskurve mit
      Pufferpunkt auf der Kurve, neu: Look up/Calculate/Anki je ein Bild); Hash-Test im Gate wie Golden-SVGs (bewusst neu erzeugen
      per `UPDATE_README_BILDER=1`); Limitations-Absatz trägt die Desktop-Grenze aus dem CHANGELOG 0.7.0; Gate grün.
      GIFs bleiben Aufnahmen (demo-video.sh), nur Datum/Version geprüft.
- [x] **A Masse-Evaluation (Opus-Arbeiter + Claude, abgenommen 05.11. 01:10; Fixture ist `tests/identity/stoffe-masse.json` mit 711 Eingaben/414 Stoffen, `stoffe.json` bleibt unverändert; Erwartung Wikidata-InChIKey gegen ChEMBL (691/711 bestätigt); drei Berichte mit Zahlen in `docs/evidence/masse-eval-2026-11/`: `identitaet.md` Lauf 2 591 grün · 1 gelb · 119 rot (80 `not_found` = deutsche Labels ohne PubChem-Synonym, 21 stereo, 16 skelett davon 4 OPSIN-Fehlgriffe, 2 PubChem-Synonymfehler, 2 Wikidata-Referenzfehler), `ir-abdeckung.md`, `ph.md` 48/51; Lauf 1 vor NCI-Fix eingefroren `f402b94`; `pytest tests/test_eval_cases.py tests/test_server_profiles.py` 263 grün; Gate rc=0 7542 Tests):** `tests/identity/stoffe.json` von 24 auf ~300 Einträge; Erwartungswerte aus einer
      UNABHÄNGIGEN Quelle (Codex-Einwand): InChIKeys aus PubChem-Download je CID-Liste (Ph.-Eur.-Arzneistoffe / Top-200
      Wirkstoffe), nicht aus der eigenen Auflösungskette; IR-Regelabdeckung über dieselbe Menge (welche Gruppen keine Regel
      treffen) als Bericht; pH-Aufgaben (~50) gegen Lehrbuchlösungen. Ergebnis + Rot/Gelb-Zusammenfassung nach
      `docs/evidence/masse-eval-2026-11/`; bleibt außerhalb des Gates (Netz).
- [x] **B Mechanismus mit eigenen Molekülen (Opus, Branch `mechanismus-substrate`, 05.11. 00:20 gemergt `16fc11e`, Gate grün rc=0; Claude geprüft: 6 Commits, Design-Notiz, Grenzen je Familie in `mechanism_substrate.py`, README-Bild gesichtet; CHANGELOG [Unreleased] → 0.8.0; Desktop-Handtest Codex `350b270` abgenommen 05.11. 00:05):** Design-Notiz zuerst (Reaktionszentrum per
      SMARTS finden, Rest mitzeichnen, Pfeile an gefundene Atome), Unterstützungsgrenze je Familie benennen; TDD, Golden-SVGs
      gesichtet; CHANGELOG 0.8.0; Merge erst nach Tag v0.7.0.
- [x] Nach allem: Werkzeugbilanz neu bauen (`scripts/werkzeugbilanz.py`) und per url republishen (Claude 05.11. 00:10, `cecb120`, Artifact Version 5).

Bremsen bleiben: Release-Klick = Jay; Branch-Löschung nur gemergt; nichts nach außen.

## Weiter bei — Release 0.7.0 (Claude, 03.11.2026 07:50)

**Reihenfolge (Jay 02.11.):** erst 0.7.0 sauber raus → dann README sauber → Shorts zuletzt.

**Stand draußen:** GitHub, PyPI, Registry = 0.6.0 (26.10., 7 Tools). Repo bereit für 0.7.0 (`cb4afa9`:
Version, Changelog). Alte Erweiterung 0.5.1 in Desktop deaktiviert (Ursache der „7 alten Tools" 30./31.10.).

**Desktop-Messung 02.11.** (`docs/desktop-abnahme-2026-11-02.md`, je 1 Chat): 16 Tools in einem Konnektor,
12/12 Panels rendern, Routing 10/16 — ohne Tool: lookup, predict_spectrum, calculate_ph ×3, compare_molecules.

**Ursache Routing (Claude, belegt):** Desktop lädt Tools erst bei Bedarf. `run_claude.py` mit
`ENABLE_TOOL_SEARCH=true BUILTIN_TOOLS=ToolSearch` reproduziert es: die pH-Fälle 6/6 ohne Suche.
Fix `7596c26` (pH-Regel vorn in `_MVP_INSTRUCTIONS`): mit Tool-Suche 18/18, ohne 12/12.
Panel-Fixes `40723f9`: Vergleich im Dunkelmodus, Anki-Vorschau ohne Tags. Gate, Handshake 16/12, Host 167 ✔.

**Nachmessung Desktop 03.11. (Codex `bcd6f44`, Claude geprüft):** Originalprompts **0/18** — alle 6 Fälle 0 von 3,
Antworten aus dem Gedächtnis (pH 2,87 fachlich richtig). Mit Zusatz „— nutze ChemDraw" **6/6** (pH, Löslichkeit, Vergleich
je 2/2). Stichproben generate_molecule + Titrationskurve grün; Vergleich im Dunkelmodus lesbar; Anki ohne Tags.
→ Entscheidungsregel „pH weiter rot" greift: Hinweiszeile erreicht Desktops Toolwahl nicht. 0.7.0 geht raus,
Grenze + Workaround in CHANGELOG „Known limitations".
**Rückschrittkontrolle Claude Code (57 Fälle, je 2 Läufe):** mit Tool-Suche 50 + 49/57, ohne 54 + 53/57. Gegenmessung der
8 Rotfälle auf `7596c26^`: mit Suche 3/8 + 2/8, nach Fix 1/8 + 1/8 — schwaches Signal, im Rauschen; ohne Suche gleich.
Dauerhaft rot: `exam-revision` (batch_generate dazu), `reaction-in-conversation` mit Suche (nur Mechanismus).
Nebenbefund Codex: Label „Acetylsalicylsäure" im Vergleichspanel mit Lücke am Umlaut (nach 0.7.0).

**Nächster Schritt (03.11. 08:15, Jay will es jetzt): Release 0.7.0.** `publish.yml` startet bei `release: published`, ein
reiner Tag-Push reicht NICHT. Befehl (Projektordner): `gh release create v0.7.0 --title "0.7.0" --notes-file <(awk
'/^## \[0.7.0\]/{f=1;next} /^## \[0.6.0\]/{exit} f' CHANGELOG.md)` — Release = Jays Hand (Außenwirkung). Danach Actions-Lauf
prüfen (`gh run list --workflow publish.yml`), PyPI 0.7.0 + `.mcpb` am Release + Registry `isLatest`, dann (g) mit Codex.

**Werkzeugbilanz (Artifact, 04.11. neu gebaut):** https://claude.ai/artifact/PV3deo4duj9r8zad5gpskg — je Tool Dateien, Ablaufdiagramm,
Output (heutiger Lauf + Desktop-Screenshot), Toolwahl nach Name/Auftrag/Frage (CC 4 Läufe + Desktop), Mehrwert, Schwierigkeiten, Testbreite.
Generator `scripts/werkzeugbilanz.py <lauf> <ziel.html> --welle3-log …`, Lauf `scripts/werkzeugbilanz_lauf.py <ordner>`; Quellen fest im Repo
(`docs/evidence/routing-2026-11-03/`, Snapshots, Tests, Abnahme-Doku). Befund 04.11.: Auftrag 122/128, Frage 72/88 (mit Tool-Suche 31/44);
generate_mechanism = feste Vorlage (Substrate nur geprüft), predict_spectrum = 31 SMARTS-Regeln, alles andere gerechnet/live.
Historischer Nebenbefund (behoben und Desktop-abgenommen mit `9662b76` am 07.11.):
Ibuprofen kam wegen der PubChem-Synonymreihenfolge mit CAS 58560-75-1 statt 15687-27-1.

**Nach 0.7.0 — API-Eval (Jay 03.11.: „erst 0.7.0, dann"):** Runner über Anthropic-API (Opus 5.5) gegen den ECHTEN Server
(MCP-stdio-Client, Tools mit `defer_loading` + `tool_search_tool_bm25_20251119` wie Desktops Nachladen), je Fall eine
Korrektheitsprüfung (pH 2,88 ± 0,02, InChIKey, Pufferrezept 38,7/61,3 mL; Text per Modell-Richter), alle 23 Tools.
Erst 10 Kernfälle (~3 $, Kosten je Fall messen), dann Freigabe für ~60 × 3 (~20–25 $ geschätzt). Voraussetzung Jay:
API-Schlüssel (`ANTHROPIC_API_KEY` oder `ant auth login`; heute weder Key noch `ant` noch SDK da). Grenze: sagt
Desktop-Routing NICHT verlässlich voraus (CC mit Tool-Suche 18/18 vs. Desktop 0/9) — dafür bleibt Codex' Klicktest.

**Abfragemodus-Entscheid (Jay 07.11., beantwortet):** zunächst nur Moleküle; Reaktionen/Mechanismen später als Phase 7.
**Welle-3-Entscheid (Jay 06.11., beantwortet):** zweiter Konnektor `chemdraw-pharma` mit `CHEMDRAW_PROFILE=full`; Details unter Welle 3.

- [x] (a) alte Erweiterung aus, Desktop neu gestartet (Claude, 23:05)
- [x] (b) **Codex:** Desktop-Messlauf aller 16 Tools mit natürlichen Prompts (Faden `20261102-230541-desktop-abnahme-0-7`),
      Tabelle `docs/desktop-abnahme-2026-11-02.md`, Commit `1b8fded`; Messung vollständig, Abnahme rot (10/16 Routing).
- [x] (c) **Claude:** Host-Fälle für `batch_generate` und `generate_reaction` (fehlen in `host.e2e.mjs`)
- [x] (d) **Claude:** Befunde aus (b) fixen (TDD) — `40723f9`, `7596c26`
- [x] (d2) **Codex:** Desktop-Nachmessung „n von 3" je roter Fall — 0/18, mit „nutze ChemDraw" 6/6 (`bcd6f44`)
- [x] (e) **Claude:** CHANGELOG 0.7.0, Version 0.7.0 (`pyproject.toml`, `server.json`), Gate + Handshake grün
- [x] (f) Release v0.7.0 (Claude, 04.11. 23:08, Jays Freigabe „mache du den Release“): Tag auf `3016833` (kein Produktcode seit Gate 03.11.),
      Lauf 41922554381 grün: PyPI 0.7.0, `chemdraw-mcp-0.7.0.mcpb` am Release, Registry-Job grün; PyPI-Umgebung per API freigegeben
- [x] (g) Bundle 0.7.0 in Desktop abgenommen (Codex 04.11. 23:45, Jays Install-Freigabe; Claude geprüft: `docs/desktop-abnahme-0-7-0-bundle.md`
      @ 249fca6, 16 Screenshots, PyPI-Wheel bytegleich installiert, Entwickler-Konfig wiederhergestellt). Vier Stichproben grün.
      **Für 0.7.1:** Manifest „six tools“ (behoben dbd94e5) · Erstinstallation brauchte zweiten Neustart (10-s-Host-Timeout beim uv-Install) ·
      Anki-Panel zählt Notizen (14) statt Karten (16).
- danach: README-Bilder (Calculate, Anki, Look up; `wave2-titration-acetic.png` neu) · zuletzt Shorts S1/S8–S11
- Welle 3 erst nach 0.7.0; Profil-Entscheid beantwortet (Jay 06.11.): zweiter Konnektor `chemdraw-pharma` mit `full`.

Geparkt: Git-Ballast (`mcp-2-migration` + 2 Worktrees) · adjustText verworfen (scipy).

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

### Welle 1 — Reaktionen & Darstellung (Release-Kandidat danach)
- [ ] generate_mechanism — **Entscheid 30.10.:** ehrliche Lehrbuch-Galerie (SN1, SN2,
  Fischer-Ester). Titel und Beschreibung sagen „textbook example", `reaction_type` listet die drei
  Typen vollständig (kein „e.g."), die Substrate prüfen nur die Passung; Fehlermeldungen englisch.
  Serverseite fertig `142e581` (DoD 1–5); offen: Desktop-Handtest (Codex).
- [ ] generate_3d — Serverseite fertig `044e8d6` (Zäune ⇄ generate_molecule, 3 Routingfälle);
  offen: Desktop-Handtest (Codex).
- [ ] lookup — Serverseite fertig `ed2dee2`. Behobene Befunde: KEGG nahm den ersten unscharfen
  Treffer („glucose" → UDP-glucose C00029, jetzt C00031), Ausgabe halb deutsch → englisch, leere
  Zeile „| **** |" in physical, Link „CID ?". Offen: Desktop-Handtest (Codex).
  Nicht behoben, notiert: 6–10 s je Aufruf (PubChem/ChEBI/KEGG nacheinander); ChEBI-Zeitüberschreitung
  erscheint als „No ChEBI entry found" (Ausfall ≠ kein Eintrag); Familiennamen wie „xylene" →
  „not found" statt Isomerauswahl (lookup umgeht den Resolver).
- Stand Standardprofil nach Welle 1: 10 Tools, 8 Panels (Handshake grün).

### Welle 2 — Spektren & allgemeine Laborgrafik (Release-Kandidat danach)
- [ ] predict_spectrum — Serverseite fertig `3945648`; offen: Desktop-Handtest (Codex).
  Behoben: `structure="Aspirin"` scheiterte („could not be parsed"), das Modell musste SMILES
  tippen → läuft jetzt durch `resolve()`. Zäune generate_molecule/lookup → predict_spectrum.
  Notiert: Ausgabe doppelt („3 signal(s) for 8 hydrogens" in Kopf und Bullet).
- [ ] generate_spectrum — Serverseite fertig `c6c847c` + Desktop-Fix `6ba60ca`; offen:
  Desktop-Retests ausgeführt, Toolwahl weiterhin rot (`0c36b4b`). Behoben: überlappende IR-Banden (Aspirin C=O 1750/1690) addiert und
  bei 0 % abgeschnitten → Transmission multipliziert; Fehlertexte englisch; Exportknopf in
  SpectrumView (ExportPngButton). **Offen, Desktop-Befund (Codex):** „Aspirin IR-Spektrum
  schematisch" geht auch nach eigenem Auswahltext (`6ba60ca`) an Desktops eingebautes
  `visualize` — nicht weiter ohne Desktop-Messung an der Beschreibung drehen; Codex' sieben
  Fälle gesammelt auswerten. Notiert: 12–19 KB Text ans Modell (SVG inline im Payload-JSON).
- [ ] generate_tlc — Serverseite fertig `90cfd7b` (+ Exportknopf `d6098a9`); offen:
  Desktop-Handtest ausgeführt, Toolwahl rot (`0c36b4b`); Host/README `2c9a71a`. Behoben: sieben deutsche Fehlermeldungen; erster Zaun überhaupt
  (⇄ generate_reaction, → generate_spectrum), 3 Routingfälle (vorher 0). Notiert: eng
  benachbarte Flecken (0,50/0,52) überdecken ihre Rf-Beschriftung; 8–16 KB Modelltext.
- [ ] generate_titration_curve + generate_species_distribution — Serverseite fertig `6093b88`
  (+ Exportknopf PlotView `d6098a9`); Host/README `5eb9c43`, Desktop 0/4 (`a6d6e86`). Offen: Toollisten-Diskrepanz (oben); Pufferpunkte behoben `a08e3cb`. Behoben: absteigende
  pKa ([7.2, 2.1]) still gezeichnet (Pufferpunkte neben der Kurve, HA⁻ verschwand) → Fehler;
  Fehlertexte englisch. Eigene MVP-Auswahltexte ohne calculate_ph/calculate_content/
  generate_dose_response. Notiert: 17–24 KB Modelltext (Phosphorsäure); `notes` leer — das
  Modell sieht EP-Volumen/-pH nur im Bild.
- Stand Standardprofil nach Welle 2: 15 Tools, 12 Panels (Handshake grün). Randnotiz:
  generate_molecule-Auswahltext bei 2010 B — der nächste Zaun dort braucht Kürzung.
- [ ] calculate_ph — **Ausnahme** vom „Rechnen später": pH/Puffer ist Grundstudium.
  **Jay (31.10.2026):** ja, Welle 2. Serverseite fertig `71223ed` (Text-Tool, kein Panel; Zäune
  beidseitig zu Titrationskurve/Speziesverteilung, Standardprofil 16 Tools / 12 Panels).
  Offen: Desktop-Handtest + Host-Fälle/README (Codex).

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
  Einträge, fremde Einstellungen unverändert, grüner Lauf.
- [ ] `.mcpb`-Weg: beide Konnektoren mit eindeutigen Extension-IDs und festem
  Profil installierbar machen; derselbe Server/Launcher, keine konkurrierende
  automatische Registrierung. Prüfen: `uv run pytest tests/test_mcpb_start.py`
  mit neuen Fällen für beide Profile → grün; echte Desktop-Installation → beide
  Konnektoren mit 16 bzw. 23 Tools, erster Start samt Launcher abgenommen.
- [ ] `scripts/handshake.sh`: beide registrierten Konnektoren getrennt prüfen,
  erwartete Kataloge aus dem jeweiligen Profil ableiten, GUI-PATH beibehalten.
  Prüfen: `./scripts/handshake.sh` → zwei echte stdio-Handshakes, `chemdraw`
  16 Tools / 12 Panels und `chemdraw-pharma` 23 Tools / 16 Panels, Exit 0.
- [ ] README-Abschnitt „Profiles“: beide Installationswege, zwei Konnektornamen,
  Profilwerte und Wechsel im Chat beschreiben. Prüfen:
  `rg -n 'chemdraw-pharma|CHEMDRAW_PROFILE|Profiles' README.md` → beide Konnektoren und
  Profilwerte erklärt; Schritte stimmen mit Desktop-Abnahme überein.
- [ ] Desktop-Wechsel abnehmen: frischer Chat, `chemdraw` auswählen und
  Struktur zeichnen; im Menü zu `chemdraw-pharma` wechseln und `calculate_content`
  aufrufen; zurück zu `chemdraw`, Struktur zeichnen. Prüfen: Codex-Handtest mit
  Screenshots unter `/tmp/chemdraw-desktop-test/profile/` → passende Werkzeuge je
  Konnektor, erfolgreicher Hin-/Rückwechsel ohne Neustart; `./test.sh` +
  `npm --prefix chemdraw_tool/ui run test:host` → grün.

**Vertiefungs-Tools und Erweiterung:**

- [ ] calculate_solution
- [ ] calculate_content
- [ ] calculate_pharmacokinetics
- [ ] generate_pk_curve
- [ ] generate_dose_response
- [ ] generate_calibration_curve
- [ ] generate_scope_table (36,7 KB Modelltext vorher verschlanken)
- [ ] generate_mechanism aus Nutzersubstraten: echte Mechanismen statt Lehrbuch-Galerie

### README hochwertig (nach Welle 2)
- [ ] Je Bereich (Zeichnen · Laborgrafik · Nachschlagen · Rechnen · Anki) ein echtes Bild aus
  einem echten Aufruf; „Full-profile feature reference“ überarbeiten und „Profiles“
  auf die zwei Konnektoren `chemdraw`/`chemdraw-pharma` aktualisieren.
- [ ] Installationsweg Desktop-Extension (`.mcpb`) zuerst, `install.sh`/PyPI danach.
- [ ] Werkzeugtabelle: Tool · Bereich · Beispiel-Prompt · Panel ja/nein.
- [ ] Danach Shorts: `plans/vermarktung.md` § „Shorts je Workflow" (Jay 26.10.) — dort weiter.

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

## Etappen
- [ ] **Geparkt (Chef 31.10.2026: nicht löschen):** von der README (`65800df`) nicht mehr verwendete Assets —
  `assets/titration-phosphoric.png`, `species-phosphoric.png`, `ethyl-acetate-ir.png`, `tlc-esterification.png`,
  `mechanism-overview.png`, `demo-mechanism.gif`, `demo-3d.gif`. Vor einem Löschen `grep` in `docs/` und `~/Documents/projects/chemdraw-vermarktung/`.

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

- [ ] **Routing-Befund MVP (Claude, 14.10., `run_claude.py`, 11/13 grün):** zwei Fälle
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
- [ ] Desktop-Entwicklermenü „MCP-Konfiguration neu laden“ ersetzt per AppleScript einen
  von zwei laufenden Serverprozessen (57152 → 63588, 57194 blieb). Vor einem Reload-Skript
  klären, welcher Prozess einen neuen Chat bedient.
- [x] SMILES-Dateinamen-Kollisionen behoben (20.10., `20c204f`): Großschreibung und
  Stereopunktuation bleiben durch einen stabilen Fingerabdruck unterscheidbar, für
  Einzel- und Batch-Export in PNG/SVG/CDXML. Zwölf Regressionen erst rot, dann grün;
  Gate 6.976 bestanden / 16 übersprungen. Explizit gleiche Labels bleiben überschreibbar.
- [ ] Offen aus der Kernanalyse: NCI CIR antwortet live
  mit 500 auf deutsche Namen (Methylphenidat, Salicylsäure) → Kandidat Wikidata-Stufe;
  ACS-1996-Stil nur nach Designrunde.

Noch offen bleibt die persönliche Gestaltungsrückmeldung von Jay; weitere
Panelmodi und Fachfunktionen sind damit nicht freigegeben.

### Etappe 03.10.2026: Panel-Ausbau — Ansichten, Animation, Abfrage- und Prüfungsmodus

Ziel: Das Moleküle-Panel wird vom Bild zum Lernwerkzeug. **Eine** Molekülanfrage liefert alle Ansichten, man schaltet sofort um, wird durch die Optionen geführt, und kann sich selbst abfragen.

Stand 08.10.: außer M0 und der Recherche W-1c ist nichts davon gebaut (geprüft: keine `readOnlyHint`, kein `svg_stereo`, kein `mode="quiz"`, kein Bundle-Budget-Test im Code).

#### Wow-Moment zuerst (Fokusänderung 03.10. abends — gilt vor den Phasen unten)
Jay: erst das Layout im Chat, Ansichten ohne Nachfragen umschaltbar, **allgemein** für alle, die es auf GitHub ausprobieren (Chemie, Pharmazie, Biologie). Liste aller Möglichkeiten: `docs/produkt/panel-moeglichkeiten.md`.

- [ ] **M3** alle 23 Werkzeuge mit `title` und `readOnlyHint` annotieren (Snapshot-Tests mit freigeben) — fehlt: `docs/anthropic/abgleich.md:27` „✗ 0 von 23"
- [ ] **M2** Größen der Panel-Ergebnisse messen (Grenze ~150.000 Zeichen, sonst lädt das Panel nicht), Großes nachladen
- [ ] **M7** Manifest: Icon (512 px), `privacy_policies`, Windows testen oder ausschließen; **M8** README: Organisationen können Extensions sperren — fehlt: `abgleich.md:35-36`
- [ ] W-1 Nativer Look: Host-Farben/-Schrift (`--color-*`, `--font-sans`) statt eigener Tokens, Skelett statt Spinner, Tippflächen ≥ 44 pt (Baustein 13)
- [ ] W-1b Quiz-Satz in den `instructions` + Eval-Fall (Baustein 14)
- [ ] W0 Host-Messung: Zeile im Panel „Claude Desktop · Vollbild · Nachricht · Download …" (1 h) — entscheidet über W4, Phasen 5, 6
- [ ] W1 Reiter **Struktur · Stereo · 3D · Daten** von Anfang an (= Phase 1 unten)
- [ ] W2 3D dreht sich von selbst, weicher Wechsel (Teil von Phase 4 vorgezogen)
- [ ] W3 **Browser-Demo ohne Installation**, Link ganz oben im README (Hebel für Sterne)
- [ ] W4 je nach W0: Atom anklicken → Claude erklärt · Vollbild + Download · Folge-Vorschläge
- [ ] W5 README neu aufbauen um den Wow-Moment (GIF der Reiter, Demo-Link) — erst nach W1–W3, sonst verspricht es Ungebautes
- [ ] W6 danach: Blind-Modus, Prüfmodus (Phasen 5–6), Biologie-Paket, Wirkstoffklassen-Galerie
- [x] **M0** `ext-apps` 2.0.3 migriert (ac13350, 1bacd64): keine Codeänderung im Panel, Bundle 524 → 399 kB, Gate/Host-Test/Handshake grün; MCP-Fassung 2026-07-28 gelesen, nichts zu tun (`docs/anthropic/abgleich.md` §1)
- [x] W-1c Recherche: Anthropic-Verzeichnis, geht ein lokaler Server? (bcf3286, `docs/anthropic/abgleich.md:38-50`: lokal nicht als Connector einreichbar, .mcpb nicht mehr angenommen, Weg wäre Plugin-Bundle)

#### Phase 0 — Grundlage und zwei Versuche (ca. 1 Stunde)
- [ ] Ausgangsbilder: `tests/gallery_ui.py` als Vorher-Stand ablegen (`docs/produkt/panel-vorher/`)
- [ ] Versuch 1: Kann das Panel dem Chat eine Nachricht schicken (`ui/message` der AppBridge)? Im Host-Test prüfen, dann **einmal in Desktop von Hand** — davon hängt D (Folge-Vorschläge) ab
- [ ] Versuch 2: Panelhöhe in Desktop messen (wie viel Platz bleibt unter dem Chat-Text?) — davon hängt das Layout in C ab
- [ ] Bundle-Budget als Test: `dist/index.html` ≤ 650 kB, rot sonst

#### Phase 1 — Ansichtsumschalter (A) → Release 0.5.0
- [ ] Payload: `MoleculePayload` bekommt `svg_stereo` und `mol3d` (Atome/Bindungen), nur wenn nicht zu groß (Obergrenze Atomzahl, sonst leer + Hinweis)
- [ ] Panel: Reiter **Struktur · Stereo · 3D · Daten**; 3D-Ansicht als wiederverwendbare Komponente (aus `Molecule3DView` herausgelöst, gleiche Drehung)
- [ ] Tests: Host-Test klickt durch alle vier Reiter; Komponententest je Ansicht; Payload-Parität (Python ⇄ App.jsx)
- [ ] **Jay:** 10-Sekunden-Test: „Zeichne Ibuprofen" → Stereo klicken (R/S sichtbar) → 3D klicken (dreht sich) → Data

#### Phase 2 — Seitenpanel und Layout (C) → 0.5.1
- [ ] Gestaltungsgrundsätze in `styles.css` als Tokens (Abstände, Schriftgrößen, Kartenstil), nicht pro View
- [ ] Steckbrief: einklappbare Abschnitte, klarere Hierarchie, Kopierknöpfe einheitlich
- [ ] Schmal/breit: Seitenleiste wird unter 560 px ein Block unter dem Bild
- [ ] Hell/dunkel prüfen; Galerie vorher/nachher nebeneinander ansehen

#### Phase 3 — Geführte Optionen (D) → 0.6.0
- [ ] Optionsleiste: Stil (kompakt / Präsentation / Graustufen), Stereo-Beschriftung, Gruppen abkürzen — Änderung ruft das Werkzeug erneut auf (`callServerTool`), Ergebnis ersetzt das Bild
- [ ] Folge-Vorschläge unter der Struktur („Mechanismus", „Vergleichen mit …", „Karteikarte") — **nur wenn Phase-0-Versuch 1 klappt**, sonst als kopierbarer Prompt
- [ ] Eval: Tool-Wahl-Fälle unverändert grün (28/28 Basis), Beschreibungen nicht länger

#### Phase 4 — Animationen (B) → 0.6.1
- [ ] 3D: Dauerdrehung mit Pause/Weiter, stoppt bei Ziehen, respektiert `prefers-reduced-motion`, pausiert, wenn das Panel nicht sichtbar ist
- [ ] Weiche Übergänge beim Ansichtswechsel (kurz, abschaltbar)
- [ ] Mechanismus: Schritte automatisch durchlaufen (Schleife, Tempo einstellbar)
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
- [ ] **Jay:** Freigabe A1 (oder Variante B/C zuerst)?

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

- [ ] **Jay:** einmal von Hand in Desktop „Zeig mir Methylphenidat" → Data (nur noch Host-Eigenheiten, die der Nachbau `test:host` nicht kennt)
- [ ] `mcp-2-migration` (Worktree `.claude/worktrees/agent-a567114bbee585cc8`, Branch-Stand 836324b vom 02.10.): GEPARKT bis zum Desktop-Test. Die Vorbedingung „erst nach dem OPSIN-Merge" ist erfüllt (022507d); der Branch liegt jetzt 41 Commits hinter main → erneut mit main abgleichen (CHANGELOG-Konflikt), Gate + Handshake, dann mergen. Nicht nebenbei anfassen.
  - Zusätzlich liegt auf GitHub `mcp-2-migration-v2` (dd932f6 vom 14.10., Stand 30.10. 118 Commits hinter main): ein einzelner Commit „build: Server auf mcp 2.x (MCPServer) umgestellt, mcp>=2.3,<3“ direkt auf main d830726 — also eine Neuauflage der Umstellung auf frischem main statt Merge des alten Branches. Vor dem Abgleich entscheiden, welcher der beiden die Grundlage wird; der andere wird danach gelöscht.
- [ ] Hinweis in `_INSTRUCTIONS`/README: Desktop nimmt die Sandbox, wenn man den MCP nicht nennt — prüfen, ob ein Satz in `instructions` das ändert (nur in Desktop messbar). Fehlt: `chemdraw_tool/server.py:205-240` enthält keinen solchen Satz
- [ ] Geschwindigkeit (zurückgestellt): Server-Import 1,4 s (mcp 0,33 · rdkit 0,25 · matplotlib 0,25) — nur lazy laden, wenn die Handshake-Zeit unter Last wehtut; Datenblatt-Ladezeit 2,3 s (PubChem) — Vorabladen nur, falls Jay es spürt
- [~] Option: Server-Import ohne RDKit/matplotlib — gestrichen 08.10.2026, weil Dublette des Geschwindigkeits-Hakens darüber
- [x] 0.4.6 veröffentlichen: PyPI, `.mcpb`, bei Jay installiert (v0.4.6 GitHub-Release 03.10., 20ff181; PyPI steht inzwischen auf 0.4.8; `dist/chemdraw-mcp-0.4.8.mcpb`; Desktop-Test 03.10. mit 0.4.7 verbunden)
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
