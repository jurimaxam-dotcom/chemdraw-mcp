# Referenzkorrektur — Befund 4, 06.11.2026

## Ergebnis und Grenze

Lauf 5 aus Commit `236df52` bleibt als Messung unverändert. Nur die Erwartung wird gegen
**dieselben gespeicherten Antworten** neu bewertet: **664/1/46 → 666/1/44** (grün/gelb/rot).
Kein Resolveraufruf und kein neuer Netz-Identitätslauf; damit kann Befund 3 die Zähler nicht
nebenbei verbessern. Ergebnis: `identitaet-lauf.json`, Änderungen: `vergleich.json`.
Der neu erzeugte Bericht `identitaet.md` enthält diese Neuwertung, keinen neu gemessenen Resolverlauf.
Die alten Laufzeiten stammen ausdrücklich aus Lauf 5.

## Belegte Änderungen

| Eingabe | falsche Referenz | korrigierte Referenz | unabhängige Gegenprobe |
|---|---|---|---|
| fumaric acid | Q125026916, BVSPPBKONISENN-SLHNCBLASA-N, C20H33N3 (Alkaloid) | [Q139857](https://www.wikidata.org/wiki/Q139857), VZCYOOQTPOCHFL-OWOJBTEDSA-N, C4H4O4 | [CHEMBL503160](https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL503160.json), gleicher Key; [PubChem 444972](https://pubchem.ncbi.nlm.nih.gov/compound/444972) |
| tenofovir disoproxil | Q155954, SGOIRFVFHAKUTI-ZCFIWIBFSA-N, C9H14N5O4P (Tenofovir) | [Q27132753](https://www.wikidata.org/wiki/Q27132753), JFVZFKDSXNQEJW-CQSZACIVSA-N, C19H30N5O10P (Prodrug) | [CHEMBL1538](https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL1538.json), gleicher Key; [PubChem 5481350](https://pubchem.ncbi.nlm.nih.gov/compound/5481350) |

ChEMBL per direktem ID-/InChIKey-Endpunkt live nachgeprüft; Formel, stereospezifisches SMILES
und daraus berechneter RDKit-InChIKey stimmen überein. Wikidata Q155954 heißt zwar auf Englisch
„tenofovir disoproxil“, führt aber Tenofovirs Schlüssel: der Name darf nicht die Elternstruktur erben.
Tenofovir selbst bleibt SGOIRFVFHAKUTI-ZCFIWIBFSA-N. Disoproxil-Fumarat
([Q27132754](https://www.wikidata.org/wiki/Q27132754), VCMJCVGFSROFHV-WZGZYPNHSA-N) ist ebenfalls
nicht die gesuchte salzfreie Prodrug. Deutsches „Fumarsäure“ war schon korrekt.

`REFERENZ_KORREKTUREN` in `scripts/masse_eval.py` bindet beide Eingaben an die überprüften
Referenzdaten, auch beim nächsten `liste`-Neubau. Die Struktur kommt aus ChEMBL, nicht aus dem Resolver.
Regression mit absichtlich falsch beschrifteten Quellenobjekten verhindert den Rückfall.

## Prüfung aller 46 roten Eingaben

Die vollständige Einzelliste steht in `referenz-audit.json`; sie enthält die ursprünglichen Keys,
Formeln, Wikidata-Links und ChEMBL-Antworten. Keine Referenz wurde einfach an die Resolverausgabe angepasst.

46 Eingaben stehen für 37 verschiedene Erwartungsschlüssel. 37 Eingaben haben einen
live bestätigten identischen ChEMBL-Key (30 verschiedene ChEMBL-IDs abgefragt). ChEMBL-Bestätigung
beweist die Strukturzuordnung der ID; sie beseitigt keine mehrdeutigen Namen oder partiellen Stereoangaben.

Weitere **gesicherte** Salz-/Prodrug-/Elternstoff-Verwechslungen der Referenz wurden nicht gefunden.
Bendamustin: ChEMBL bestätigt freie Base, Auflösung liefert Hydrochlorid. Docusat: ChEMBL bestätigt
Natriumsalz, Auflösung liefert freie Säure; beides bleibt rot. Cefixim Anhydrat und Metamizol
(freie Säure) sind unter genau dieser Form bei ChEMBL bestätigt. Benzylpenicillin-Benzathin enthält
beide Penicillin-Komponenten und Benzathin in der Referenz; der erhaltene Key verliert Stereo.

Ohne ChEMBL-Key-Nachweis bleiben Modellgrenzen ausdrücklich stehen: Prussian blue/Berliner Blau,
Hydroxycobalamin, Megluminantimoniat, Nitroprussid, Cyanocobalamin und Trehalose. Wikidata-Seiten
[Q421894](https://www.wikidata.org/wiki/Q421894), [Q73972](https://www.wikidata.org/wiki/Q73972),
[Q2757969](https://www.wikidata.org/wiki/Q2757969) und [Q420031](https://www.wikidata.org/wiki/Q420031)
benennen das erwartete Komplex-/Wirkstoffobjekt. PubChem findet die gespeicherten Schlüssel für
Hydroxycobalamin (CID 44475014), Megluminantimoniat (64953), Cyanocobalamin (24892734) und
Trehalose (22814150); Nitroprussid und Prussian blue nicht. Das ist **kein** ausreichender Beleg,
ihre Referenzen umzubiegen. Stereo-, Tautomer-, Polymer- und Komplexdarstellungen bleiben als eigene
Unsicherheiten sichtbar; Povidon-Iod ist ein Monomer-/Polymermodell, kein belegter neuer Prodrugtausch.

## ChEMBL-Namen: Ursache und Cache

Vorher: pro Bericht alle Schlüssel erneut in 40er-Batches mit 120-s-Timeout und 0,5-s-Pause abfragen.
Kein Cache, daher konnten wiederholte Berichte dieselben Quellenausfälle erneut abwarten.
Die frühere Verzögerung von >5 min ließ sich am 06.11. nicht erneut beobachten: der bestehende
29er-Batch antwortete bei der Vergleichsmessung zügig. Es gibt deshalb keine behauptete
„5 min → …“-Messung.

Neu: erfolgreicher Batch bestätigt Namen **und** fehlende Namen für sieben Tage in
`.cache/masse-eval/chembl-namen.json` (ignoriert, atomar ersetzt). Netzwerkfehler werden nicht
negativ gespeichert; kaputter oder nicht schreibbarer Cache verhindert keine Namensabfrage.
Cold-Request-Timeout/Batchgröße bleiben unverändert, damit kein bisher erreichbares Ergebnis
nur durch einen kürzeren Timeout verschwindet. Der Cache speichert ausschließlich Berichtsmetadaten,
keine Strukturentscheidung und keinen Erwartungsschlüssel.

Erzwungen neu laden: `uv run python scripts/masse_eval.py identitaet --refresh-names`.

Vergleich desselben 29er-Schlüsselsatzes mit der unveränderten alten Funktion aus `8978be7`: alt 1.0792 s,
neu kalt 1.4076 s, neu warm 0.000293 s. Alle drei Resultate identisch,
13 Namen; ein Warmaufruf macht keine HTTP-Abfrage (Regressionstest). Das misst nur
`_chembl_namen`, nicht den ganzen Bericht: dessen PubChem-Nachklassifizierung kann weiter Netzzeit kosten.

## Reproduzierbarkeit und Prüfungen

- `uv run pytest tests/test_masse_eval_identity.py tests/test_masse_eval_ir.py -q`.
- Vor dem Fix: fünf neue Tests rot (Referenzen, Neubau, wiederholter Metadatenaufruf, Refresh),
  danach CLI-Refresh einzeln rot. Die beiden vorher grünen Ausfalltests zusätzlich per Mutation
  rot gesehen: Netzwerkfehler negativ speichern → Wiederholungstest rot; kaputten Cache nicht
  abfangen → JSONDecodeError. Mutationen ausschließlich im Speicher eines weggeworfenen Prozesses.
- Gemessener vollständiger Berichtslauf nach der Neuwertung: **28,322 s**, rc=0.
  Der warme ChEMBL-Namenscache war befüllt; PubChem-Nachklassifizierung bleibt ungecacht.
  Vollständiges Gate: `./test.sh > /tmp/chemdraw-befund4-gate.log 2>&1`,
  **rc=0, 8203 passed / 16 skipped in 49,55 s**, Lint + Bundle + Frontend + Pixelvergleich grün.
  Der geteilte Arbeitsbaum enthielt dabei zusätzlich die parallelen Befund-3-Edits;
  sie gehören nicht zu diesem Commit. Eigene gezielte Prüfungen: **10 passed in 1,21 s**.

Die reine Referenz-Neuwertung ist unabhängig reproduzierbar: Ausgangsliste mit
`git show 236df52:docs/evidence/masse-eval-2026-11/identitaet-lauf.json` laden; für jede Zeile den
aktuellen Fixture-Key vergleichen. Nur bei geändertem Erwartungskey darf sich die Zeile ändern.
In beiden betroffenen Zeilen war `erhalten` bereits exakt der korrigierte Key; Status wird grün,
`text` dieser Key, `art`/`erhalten` entfallen wie bei jedem ursprünglichen grünen Ergebnis.
Alle übrigen 709 Zeilen bleiben byteinhaltlich gleich; ursprüngliche Zeiten bleiben erhalten.
