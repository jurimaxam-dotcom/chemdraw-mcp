# Stereo-Referenzen — Audit 06.11.2026

## Ergebnis

**Vier Referenzen / fünf Eingaben korrigiert.** Nur die Erwartung wird gegen dieselben
711 Antworten aus Lauf 7 (`9b3cbbd`) neu bewertet: **668 grün / 1 gelb / 42 rot →
673 grün / 1 gelb / 37 rot**. Kein Resolverlauf, keine Änderung an Resolver oder Reportcode.
Nach der Korrektur stehen die 711 Eingaben für 413 statt 414 unterschiedliche Referenzkeys:
`cocaine` und das schon vorher korrekte deutsche `Kokain` sind jetzt derselbe vollständige Stoff.
Die vollständigen Beobachtungen und gemessenen Zeiten bleiben erhalten; alle 706 anderen
Ergebniszeilen bleiben gleich. `vergleich.json` nennt genau die fünf Statuswechsel,
`lauf-7-neuwertung.json` enthält alle 711 Zeilen. Der gemeinsame Lauf 7 wird nicht überschrieben.

## Methode und Auswahlgrenze

Alle **711 Referenz-SMILES** mit RDKit `FindMolChiralCenters(includeUnassigned=True,
useLegacyImplementation=False)` geprüft. Die 711 Einträge haben **414 verschiedene Referenzkeys**;
aliase desselben Keys haben identische definierte/unbestimmte Element-Zentrum-Zahlen.
PubChem-Abfragen wurden nach einem englischen/INN-Namen aus der Fixture gewählt (Fallback englisches
Label, erst danach deutsch), **nie nach dem vom Resolver erhaltenen Key**. Zuerst Referenzen aus den
42 roten Fällen, danach die übrigen. Alle Namen und Abfrage-URLs stehen in `audit.json`.

Ergebnis: 414 Referenzen abgefragt, 411 mit Record-Antwort, 3 mit HTTP 404 (nitroprusside,
povidone-iodine, γ-aminobutyric acid). Diese drei haben schon im Referenz-SMILES keine gefundenen
unbestimmten Zentren; ihre Stoffidentität ist damit nicht bestätigt. Bei clomifene (3 Records)
und sodium calcium edetate (5 Records) wird die Mehrdeutigkeit vollständig festgehalten;
keiner dieser Fälle dient als Stereo-Korrektur. Es gab keine Timeout-Lücke.

Vorher haben **49 Referenzkeys** mindestens ein unbestimmtes potentielles Zentrum; das sind
**keine 49 bewiesenen Fehler**. Dazu zählen Racemate, Mischungen und N/P/S-Zentren. 365 haben
kein unbestimmtes tetraedrisches Zentrum. Nach den vier Korrekturen bleiben 45 Keys mit
unbestimmten potentiellen Zentren: 42 stehen beim namensbasierten PubChem-Record ebenso,
3 bleiben ausdrücklich unklar (Nicotin, Cyanocobalamin, Vinblastin).

Für jede Korrektur verlangt: eindeutige namensbasierte PubChem-Antwort, gleicher Konnektivitätsblock,
mehr definierte C-Zentren, keine unbestimmten C-Zentren im Ziel, und die bekannten Konfigurationen
bleiben kompatibel (`HasSubstructMatch(..., useChirality=True)`). Zusätzlich bestätigt ein
unabhängiger benannter ChEMBL-Record exakt denselben vollständigen Key. Referenz-SMILES stammen
für die korrigierten Einträge aus ChEMBL, nicht aus dem Resolver. Entscheidungen sind damit
vor der Betrachtung seiner gespeicherten Antwort begründet.

RDKit-Atomindizes sind **SMILES-lokal**, nicht zwischen zwei Records direkt vergleichbar.
Gezählt werden daher Elemente und CIP-Status; Graphvergleich prüft die bereits bekannte Stereo.
Die Suche untersucht atomare tetraedrische Zentren; sie ist kein vollständiger Audit von
E/Z-Isomerie, Atropisomerie, Metall-Koordination oder Racemat-Zusammensetzungen. Bereits vollständig
markierte, aber widersprüchlich konfigurierte Records werden nicht automatisch umgebogen.

## Belegte Korrekturen

| Eingabe | alter Key | neuer Key | definierte / unbestimmte Zentren | unabhängige Quellen |
|---|---|---|---|---|
| clindamycin | `KDLRVYVGXIQJDK-NOWPCOIGSA-N` | `KDLRVYVGXIQJDK-AWPVFWJPSA-N` | 7/2 → 9/0 | [PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/446598) · [ChEMBL](https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL1753.json) |
| cocaine | `ZPUCINDJVBIVPJ-PFSRBDOWSA-N` | `ZPUCINDJVBIVPJ-LJISPDSOSA-N` | 2/2 → 4/0 | [PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/446220) · [ChEMBL](https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL370805.json) · [ChEBI](https://www.ebi.ac.uk/chebi/CHEBI:27958) |
| pantothenic acid / Pantothensäure | `GHOKWGTUZJEAQD-UHFFFAOYSA-N` | `GHOKWGTUZJEAQD-ZETCQYMHSA-N` | 0/1 → 1/0 | [PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/6613) · [ChEMBL](https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL1594.json) · [ChEBI](https://www.ebi.ac.uk/chebi/CHEBI:46905) |
| trehalose | `HDTRYLNUVZCQOY-MFAKQEFJSA-N` | `HDTRYLNUVZCQOY-LIZSDCNHSA-N` | 8/2 → 10/0 | [PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/7427) · [ChEMBL](https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL1236395.json) · [ChEBI](https://www.ebi.ac.uk/chebi/CHEBI:16551) |

**Clindamycin:** CID 29029 liefert weiterhin NOWPCOIGSA, 7 definierte und 2 unbestimmte
Zentren; CID 446598 „Clindamycin“ AWPVFWJPSA, 9 definierte und 0 unbestimmte. Es fehlen beide
C-Zentren der Seitenkette (in den Referenz-SMILES Atome 12 und 24). Der vorherige Audit-Satz
„Referenz bestätigt (ChEMBL-Key)“ war zu weitgehend: CHEMBL376185 bestätigte nur, dass ein
Record dieses partiellen Keys existiert. **Die Vollständigkeit der Stereochemie war nicht belegt.**
Der Eintrag in `../referenzkorrektur/referenz-audit.json` ist berichtigt; seine alten Werte bleiben
als historische Messung stehen. Neuer benannter ChEMBL-Hauptrecord: CHEMBL1753.

**Cocaine:** Der alte Record hat nur 2 von 4 C-Zentren festgelegt. PubChem 446220,
CHEMBL370805 und ChEBI:27958 definieren denselben natürlichen Stoff vollständig; die beiden
bereits markierten Zentren bleiben kompatibel.

**Pantothensäure:** Gemeint ist in dieser Fixture die Vitamin-B5-Referenz (Gruppe Vitamin/Cofaktor).
PubChem 6613 und CHEMBL1594 führen dafür die R-Form; ChEBI:46905 bestätigt den Key und Vitamin-B5-Bezug.
Der alte ChEMBL-Record CHEMBL2110806 heißt ausdrücklich „PANTOTHENIC ACID, RACEMIC“.
ChEBI:7916 ist die übergeordnete stereounbestimmte Pantothensäure; diese Familie bleibt als eigener
Begriff legitim, ist aber nicht die jetzt ausdrücklich dokumentierte Vitamin-B5-Erwartung.
Die Quellenzeile wird daher auf die spezifischen neuen Records umgestellt, statt fälschlich
zu behaupten, Wikidata Q179894 bestätige bereits den vollständigen R-Key. Der Inputname bleibt gleich.

**Trehalose:** PubChem 7427, CHEMBL1236395 und ChEBI:16551 belegen α,α-Trehalose
mit beiden definierten anomeren C-Zentren. Diese benannte Lehrbuch-Referenz ersetzt den Record,
der beide anomeren Positionen offenließ. Der allgemeine Trehalose-Oberbegriff ist breiter;
die Fixture benennt ihre gewählte vollständige Erwartung ausdrücklich in `notiz`/Quellen.

## Unklar statt automatischer Enantiomerenwahl

- **Nicotin:** PubChem 89594 / CHEMBL3 führen SNICXCGAKADSCV-JTQLQIEISA-N (S-Form).
  [ChEBI:18723](https://www.ebi.ac.uk/chebi/CHEBI:18723) definiert „nicotine“ dagegen explizit
  als Racemat aus R und S; die Fixture hat SNICXCGAKADSCV-UHFFFAOYSA-N. Deshalb bleiben
  `nicotine` und `Nicotin` unverändert und der Namens-/Mischungs-Konflikt ist **unklar** dokumentiert.
  Kein stiller Wechsel von einem bisherigen grünen Fall zu einer ausgewählten S-Form.
- **Vinblastin:** Der offene RDKit-Zentrumskandidat ist N, auch der PubChem-Record lässt ein Zentrum
  offen. Die Key-Abweichung betrifft bereits definierte Konfigurationen, nicht zwei fehlende
  Seitenketten-C-Zentren wie bei Clindamycin. Kein belegter Korrekturgrund in diesem Auftrag.
- **Cyanocobalamin:** PubChem-Record und Referenz haben verschiedene Konnektivitäts-/Koordinationsmodelle;
  die Anzahl offener Zentren allein ist kein Stereo-Beweis. Keine Änderung.

Die übrigen 42 Referenzkeys mit offenen Zentren entsprechen im abgefragten PubChem-Record
exakt demselben Key und denselben Zentrumzahlen. Das ist kein universeller Beweis eines Racemats,
sondern **kein Beleg für eine zusätzlich festzulegende Stereo**. Gerade bei N/P/S oder
Mischungen wäre blindes „alle ? setzen“ falsch. Alle Einzelmessungen stehen in `audit.json`.

## Die 42 roten Eingaben aus Lauf 7

| Eingabe | Ref: definiert / offen | PubChem: definiert / offen | Bewertung |
|---|---|---|---|
| L-scopolamine | 6 / 0 | 5 / 1 | kein unbestimmtes Zentrum; unverändert |
| L-Scopolamin | 6 / 0 | 5 / 1 | kein unbestimmtes Zentrum; unverändert |
| Prussian blue | 0 / 0 | 0 / 0 | kein unbestimmtes Zentrum; unverändert |
| Berliner Blau | 0 / 0 | 0 / 0 | kein unbestimmtes Zentrum; unverändert |
| Bendamustin | 0 / 0 | 0 / 0 | kein unbestimmtes Zentrum; unverändert |
| Benzylpenicillin-Benzathin | 6 / 0 | 6 / 0 | kein unbestimmtes Zentrum; unverändert |
| Cefixim Anhydrat | 2 / 0 | 2 / 0 | kein unbestimmtes Zentrum; unverändert |
| clindamycin | 7 / 2 | 9 / 0 | Referenz korrigiert; dieselbe Antwort jetzt grün |
| clomifene | 0 / 0 | 0 / 0 | kein unbestimmtes Zentrum; unverändert |
| Docusat | 0 / 3 | 0 / 3 | offene Zentren quellenkonform; unverändert |
| doxycycline | 6 / 0 | 6 / 0 | kein unbestimmtes Zentrum; unverändert |
| Doxycyclin | 6 / 0 | 6 / 0 | kein unbestimmtes Zentrum; unverändert |
| Hydroxycobalamin | 14 / 1 | 14 / 1 | offene Zentren quellenkonform; unverändert |
| Isosorbiddinitrat | 4 / 0 | 4 / 0 | kein unbestimmtes Zentrum; unverändert |
| β-lactulose | 9 / 0 | 9 / 0 | kein unbestimmtes Zentrum; unverändert |
| Mefloquin | 0 / 2 | 0 / 2 | offene Zentren quellenkonform; unverändert |
| N-Methylglucaminantimonat | 4 / 0 | 4 / 0 | kein unbestimmtes Zentrum; unverändert |
| Naloxon | 4 / 0 | 4 / 0 | kein unbestimmtes Zentrum; unverändert |
| nitroprusside | 0 / 0 | — / — | kein unbestimmtes Zentrum; unverändert |
| Nitroprussid | 0 / 0 | — / — | kein unbestimmtes Zentrum; unverändert |
| penicillamine | 1 / 0 | 1 / 0 | kein unbestimmtes Zentrum; unverändert |
| Penicillamin | 1 / 0 | 1 / 0 | kein unbestimmtes Zentrum; unverändert |
| Povidon-Iod | 0 / 0 | — / — | kein unbestimmtes Zentrum; unverändert |
| rifabutin | 9 / 0 | 9 / 0 | kein unbestimmtes Zentrum; unverändert |
| sulfasalazine | 0 / 0 | 0 / 0 | kein unbestimmtes Zentrum; unverändert |
| Sulfasalazin | 0 / 0 | 0 / 0 | kein unbestimmtes Zentrum; unverändert |
| (S)-(−)-timolol | 1 / 0 | 1 / 0 | kein unbestimmtes Zentrum; unverändert |
| tranexamic acid | 2 / 0 | 0 / 2 | kein unbestimmtes Zentrum; unverändert |
| Tranexamsäure | 2 / 0 | 0 / 2 | kein unbestimmtes Zentrum; unverändert |
| vinblastine | 9 / 1 | 9 / 1 | unklar / unverändert |
| Vinblastin | 9 / 1 | 9 / 1 | unklar / unverändert |
| Vinorelbin | 8 / 1 | 8 / 1 | offene Zentren quellenkonform; unverändert |
| Metamizol (freie Säure) | 0 / 0 | 0 / 0 | kein unbestimmtes Zentrum; unverändert |
| Citral A+B | 0 / 0 | 0 / 0 | kein unbestimmtes Zentrum; unverändert |
| cocaine | 2 / 2 | 4 / 0 | Referenz korrigiert; dieselbe Antwort jetzt grün |
| Adrenalin | 1 / 0 | 1 / 0 | kein unbestimmtes Zentrum; unverändert |
| Ethylendiamintetraessigsäure | 0 / 0 | 0 / 0 | kein unbestimmtes Zentrum; unverändert |
| cyanocobalamin | 13 / 2 | 14 / 1 | unklar / unverändert |
| pantothenic acid | 0 / 1 | 1 / 0 | Referenz korrigiert; dieselbe Antwort jetzt grün |
| Pantothensäure | 0 / 1 | 1 / 0 | Referenz korrigiert; dieselbe Antwort jetzt grün |
| trehalose | 8 / 2 | 10 / 0 | Referenz korrigiert; dieselbe Antwort jetzt grün |
| Xylit | 3 / 0 | 2 / 1 | kein unbestimmtes Zentrum; unverändert |

## Dateien und Reproduktion

- `audit.json`: alle 414 Referenzen, 711 Namen, Priorität, Quellennamen/URLs, vollständige
  PubChem-Antworten, RDKit-Zentren, Konnektivitäts- und Kompatibilitätsprüfung, Entscheidung.
- `korrekturen.json`: fünf komplette Vorher/Nachher-Einträge mit Keys, SMILES, Quellen und Zentren.
- `lauf-7-neuwertung.json` + `vergleich.json`: ausschließlich Referenz-Neuwertung von `9b3cbbd`.
- Ausgangsfixture: `git show d58b274:tests/identity/stoffe-masse.json`.
- Quellabfrage je Record: `/rest/pug/compound/name/<URL-kodierter Fixture-Name>/property/Title,MolecularFormula,InChIKey,IsomericSMILES,AtomStereoCount,DefinedAtomStereoCount,UndefinedAtomStereoCount/JSON`.
  Zwei gleichzeitige Anfragen, mindestens 0,35 s zwischen Starts; 411 erfolgreich, 3 ehrliche 404.
- Unabhängige Gegenprobe: ChEMBL-Molekülendpunkte der oben verlinkten IDs, vollständiger Key
  aus ihrem SMILES per RDKit nachgerechnet. Atomindizes/Zentrumzahlen mit RDKit erneut berechenbar.
- Vorher-Prüfung der fünf spezifischen Erwartungen: **5 rot von 5** (`/tmp/chemdraw-stereo-reference-red.log`).
  Nachher: **5 grün**, alle fünf Keys/Formeln aus ChEMBL-SMILES konsistent, bekannte Stereo kompatibel.
  Nur Daten geändert; kein neuer Produktionscode, daher keine Änderung an Testimplementierungen.

Wichtig für einen späteren `masse_eval.py liste`-Neubau: dessen Wikidata/ChEMBL-Auswahl kann die
partiellen Quellobjekte wieder auswählen. Der Auftrag erlaubte ausschließlich Fixture und Evidence;
`masse_eval.py` wurde deshalb nicht geändert. Die vollständigen Quellenkorrekturen in `korrekturen.json`
sind die wiederanwendbare Datenbasis, keine Behauptung eines neuen automatischen Regenerationsschutzes.

Gate: `./test.sh > /tmp/chemdraw-stereo-referenzen-gate.log 2>&1` → **rc=0,
8213 passed / 16 skipped in 50,50 s**, Lint, Bundle, Frontend und Pixelvergleich grün.
Der geteilte Arbeitsbaum enthielt dabei fremde Salzform-Edits in `resolver.py` und
`tests/test_resolver.py`; diese sind nicht Bestandteil dieses Daten-Commits.
Anschließende reine Quellen-/Erwartungsnotizen ändern keine Struktur oder Wertung.
