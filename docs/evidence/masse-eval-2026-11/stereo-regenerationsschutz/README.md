# Stereo-Referenzen: Regenerationsschutz und Live-Audit

Stand 06.11.2026. Diese Evidence schließt zwei Lücken nach dem Stereo-Audit:

1. `masse_eval.py liste` darf die fünf in b67ceb7 korrigierten Eingaben nicht wieder mit den unvollständigen Wikidata-Records erzeugen.
2. Ältere Berichte, die einen gespeicherten InChIKey allein mit „Referenz bestätigt (ChEMBL-Key)“ bewerteten, wurden erneut auf Stereochemie geprüft.

## Regenerationsschutz

`scripts/masse_eval.py:REFERENZ_KORREKTUREN` enthält nun Korrekturen für Clindamycin, cocaine, Pantothensäure (englisches und deutsches Label) und Trehalose. Die Strukturen und Quellen stammen aus [`stereo-referenzen/korrekturen.json`](../stereo-referenzen/korrekturen.json):

| Eingabe | Erwarteter InChIKey |
|---|---|
| clindamycin | `KDLRVYVGXIQJDK-AWPVFWJPSA-N` |
| cocaine | `ZPUCINDJVBIVPJ-LJISPDSOSA-N` |
| pantothenic acid | `GHOKWGTUZJEAQD-ZETCQYMHSA-N` |
| Pantothensäure | `GHOKWGTUZJEAQD-ZETCQYMHSA-N` |
| trehalose | `HDTRYLNUVZCQOY-LIZSDCNHSA-N` |

Test-first-Beleg:

- Vor dem Produktionsfix: `uv run pytest -q tests/test_masse_eval_identity.py::test_rebuilding_list_keeps_stereo_reference_corrections` → rot. Der Builder erzeugte für `clindamycin` weiterhin `KDLRVYVGXIQJDK-NOWPCOIGSA-N`, während die b67-Fixture `KDLRVYVGXIQJDK-AWPVFWJPSA-N` erwartet.
- Nach dem Fix: `uv run pytest -q tests/test_masse_eval_identity.py` → `9 passed`.

Der Regressionstest ruft `baue_liste()` mit den historischen unvollständigen Quellrecords auf und vergleicht alle fünf generierten Schlüssel mit der echten Fixture. Damit prüft er den Builder-Pfad ohne Resolverlauf oder Netz.

## Live-Audit des alten ChEMBL-Key-Urteils

`referenzkorrektur/referenz-audit.json` enthielt 33 Einträge mit der alten Begründung „Referenz bestätigt (ChEMBL-Key)“. Das sind 26 verschiedene ChEMBL-Records, weil mehrere deutsche/englische Labels dieselbe Quelle teilen. Im `stereo-referenzen/audit.json` gibt es keinen Eintrag mit dieser Begründung; dessen Urteile benennen bereits ausdrücklich, ob unbestimmte tetraedrische Zentren vorliegen und welche Schlussfolgerung daraus folgt.

Für jede der 33 Eingaben wurden PubChem PUG REST mit dem exakten Fixture-Namen und mit dem bevorzugten ChEMBL-Namen sowie der zugehörige ChEMBL-Molecule-Record live abgefragt. RDKit prüfte ChEMBL-SMILES mit `FindMolChiralCenters(includeUnassigned=True, useLegacyImplementation=False)`. Die vollständigen Antworten, Query-URLs, Keys, Formeln, Stereo-Zähler und Einzelfallbewertungen stehen in [`live-audit.json`](live-audit.json).

### Tatsächliche Korrekturen

- **cocaine**: Der alte ChEMBL-Record `CHEMBL19151` hat zwei unbestimmte C-Zentren. PubChem CID 446220 und ChEMBL `CHEMBL370805` liefern gemeinsam den vollständig definierten Key `ZPUCINDJVBIVPJ-LJISPDSOSA-N`; ChEBI:27958 stimmt damit überein. Das Fixture war bereits in b67ceb7 korrigiert. Die ältere Referenzaudit-Zeile ist jetzt entsprechend berichtigt.
- **pantothenic acid / Pantothensäure**: `CHEMBL2110806` ist ausdrücklich als racemische Pantothensäure benannt und bestätigt den alten Key ohne definiertes Zentrum. PubChem CID 6613, ChEMBL `CHEMBL1594` und ChEBI:46905 stimmen für R-Pantothensäure auf `GHOKWGTUZJEAQD-ZETCQYMHSA-N`. Beide alten Audit-Zeilen wurden auf die belegte Auswahl des R-Vitamers umgestellt.
- **clindamycin** war schon vor diesem Faden berichtigt: `CHEMBL376185` bestätigt nur den alten Key mit zwei unbestimmten C-Zentren. Der aktuelle benannte PubChem-Record CID 446598 und ChEMBL `CHEMBL1753` stimmen auf `KDLRVYVGXIQJDK-AWPVFWJPSA-N`.

### Unklare oder abweichende Datenquellen

- **Vinblastin** bleibt unverändert und explizit unklar. ChEMBL `CHEMBL22969` und ChEBI:27375 führen den bisherigen Key `JXLYSJRDGCGARV-XQKSVPLYSA-N`. PubChem CID 13342 definiert zwar neun stereogene Zentren, wechselt aber zugleich ein bereits festgelegtes C-Zentrum. Beide Strukturen lassen das N-Zentrum offen. Daher ist kein sicherer Ersatz belegt; die allgemeine Auditbegründung wurde präzisiert.
- **Mefloquin**: ChEMBL `CHEMBL416956` und PubChem Preferred „Mefloquine“ haben denselben unbestimmten Key mit zwei Zentren. Die PUG-Suche für das deutsche Fixture-Label trifft dagegen das einzelne (-)-Enantiomer. Das rechtfertigt keinen Austausch einer unspezifizierten/racemischen Referenz.
- **Vinorelbin**: ChEMBL markiert ein N im RDKit-Scan unbestimmt; PubChem CID 5311497 und ChEMBL liefern trotzdem denselben Key, und PubChem meldet acht definierte Atom-Stereozentren. Kein unbestimmtes C-Zentrum festgestellt.
- **Doxycyclin**, **Isosorbiddinitrat**, **Ephedrin**, **Naloxon** und **Risperidon**: Die PUG-Suche nach dem jeweiligen deutschen/kurzen Fixture-Namen liefert teils einen anderen Datensatz (Ephedrin CID 104213 ist 1-bromo-3-methyl-5-nitrobenzene). Die bevorzugten PubChem-Records für den englischen Hauptnamen stimmen mit ChEMBL und dem vorhandenen Key überein.
- **Xylit**: ChEMBL `CHEMBL96783` und die PubChem Preferred Reference Collection führen `HEBKCHPVOIAQTA-SCDXWVJYSA-N`. Die PUG-REST-Antwort für CID 6912 liefert stattdessen `HEBKCHPVOIAQTA-NGQZWQHPSA-N` mit einem unbestimmten Zentrum. Der direkte API-Record und die PubChem Preferred Summary widersprechen sich; die etablierte Referenz wird deshalb nicht geändert.
- **Rifabutin**: ChEMBL, ChEBI:45367 und PubChem Reference Collection unterstützen `ATEBXHFBFRCZMA-VXTBVIBXSA-N`, während die PUG-Namenssuche einen abweichenden Einzel-CID-Key liefert. Unverändert, Diskrepanz markiert.
- **Tranexamsäure**: PubChem CID 5526 ist generisch und ohne Stereo; ChEMBL und ChEBI:48669 definieren ausdrücklich die trans-Form und bestätigen den vorhandenen Key.
- Bei **Benzylpenicillin-Benzathin** hat ChEMBL den gespeicherten vollständigen Stereo-Key; der PubChem-Record lässt sechs Zentren offen. Das ist kein Beleg, die vollständige ChEMBL-Referenz zu schwächen.
- **Povidon-Iod** und **Citral A+B** lieferten keinen diskreten PubChem-Record zum genauen Namen. Sie wurden nicht umgebogen. Die Einzelfallgrenzen sind im JSON dokumentiert.

Die übrigen Live-Abgleiche bestätigen entweder den gespeicherten Stereo-Key direkt über den benannten PubChem- und ChEMBL-Record oder zeigen keine tetraedrischen Zentren. Keine weitere Korrektur war durch zwei passende, unabhängige Strukturquellen gedeckt.

## Eingefrorener Lauf 8

`identitaet-lauf.json` wurde **nicht erneut ausgeführt**. Nur die schon gespeicherten Resolverantworten wurden mit den aktuellen Fixture-Keys verglichen:

- vorher im eingefrorenen Bericht: `669 grün · 1 gelb · 41 rot`
- nach Bewertung gegen die b67-Fixture: `674 grün · 1 gelb · 36 rot`
- genau fünf Zeilen wechselten rot→grün: clindamycin, cocaine, pantothenic acid, Pantothensäure und trehalose

Zähler, Quell-/Fixture-Hashes und die fünf Zeilen Deltas: [`lauf-8-neuwertung.json`](lauf-8-neuwertung.json). Die aktuelle Fixture ist bytegleich mit `b67ceb7:tests/identity/stoffe-masse.json`.
