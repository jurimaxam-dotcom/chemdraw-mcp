# MCP-Server — Verlauf bis 07.11.2026 (archiviert)

> Archiviert 07.11.2026 (Plan-Audit, Strang A): alle „Weiter bei"-Blöcke und der Abschnitt
> „Orchestrierung" aus `plans/mcp-server.md` (Stand `feef949`), **wörtlich und in Originalreihenfolge**.
> **Zeilen hier sind Behauptungen der jeweiligen Agenten (Chef/Opus/Codex/Claude), nicht geprüft.**
> Geprüfte Urteile und Korrekturen: `docs/evidence/verifizierter-stand-2026-11-07/plan-audit.md`.
> Bekannt falsch hier u. a.: „Stereo-Klick erst nach W1" (falsch, `fd709cc`), „CI rot laut Chef"
> (behoben `b708dd3`), „Opus: A>= (läuft)" (gebaut `e559323`), „Host-Test SN1-Titel offen" (`cce71b0`).
> Der Absatz „Welle-3-Entscheid (Jay 06.11., beantwortet)" steht hier 15-mal, weil die Blöcke unverändert sind.

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
- **Neustart-Handoff:** keine unbeantwortete Frage an Jay, keine terminierten Wartezeiten
  oder ausstehenden Hintergrundresultate; nicht selbsttätig fortsetzen, bis ein neuer Auftrag kommt.
  Zugesagte Beweise bei Fortsetzung: Diff + eigene Resolver-Tests/Replay für `e559323`,
  danach echtes Host-/Server-GIF ohne Ladeframes und drei visuell geprüfte Standbilder.

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

