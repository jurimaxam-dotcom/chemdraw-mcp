# Identität — reine Referenz-Neuwertung von Lauf 5

Baseline: Commit `236df52`, `docs/evidence/masse-eval-2026-11/identitaet-lauf.json`. Keine neue Resolvermessung; dieselben Antworten mit zwei unabhängig korrigierten Erwartungswerten. Laufzeiten unverändert aus Lauf 5. Methode und Quellen: [README.md](README.md).

**711 Eingaben (414 Stoffe): 666 grün · 1 gelb · 44 rot.**

Erwartung: Wikidata-InChIKey, gegen ChEMBL geprüft (`tests/identity/stoffe-masse.json`). Laufzeit gesamt 14 min · Median 0.6 s · 90 % ≤ 4.4 s · langsamste 10.3 s je Eingabe (inkl. 0,3 s Pause).

## Rot nach Art

| Art | Zahl | Bedeutung |
|---|---:|---|
| stereo | 23 | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| skelett | 10 | anderes Gerüst — falscher Stoff |
| nicht aufgelöst | 9 | Kaskade findet nichts, obwohl die Quelle den Stoff führt |
| salz | 2 | gleicher Wirkstoff, anderes Salz bzw. Gegenion (größtes Fragment gleich) |

Nicht aufgelöst nach Sprache der Eingabe: de 7 · en 2

## Alle roten Fälle

### stereo

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| L-scopolamine | en | `STECJAGHUSJQJN-FWXGHANASA-N` | `STECJAGHUSJQJN-USLFZFAMSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| L-Scopolamin | de | `STECJAGHUSJQJN-FWXGHANASA-N` | `STECJAGHUSJQJN-USLFZFAMSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Benzylpenicillin-Benzathin | de | `BVGLIYRKPOITBQ-ANPZCEIESA-N` | `BVGLIYRKPOITBQ-UHFFFAOYSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| clindamycin | en | `KDLRVYVGXIQJDK-NOWPCOIGSA-N` | `KDLRVYVGXIQJDK-AWPVFWJPSA-N` | clindamycin | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| clomifene | en | `GKIRPKYJQBWNGO-UHFFFAOYSA-N` | `GKIRPKYJQBWNGO-QPLCGJKRSA-N` | zuclomiphene | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Isosorbiddinitrat | de | `MOYKHGMNXAOIAT-JGWLITMVSA-N` | `MOYKHGMNXAOIAT-OMMKOOBNSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Mefloquin | de | `XEEQGYMUWCZPDN-UHFFFAOYSA-N` | `XEEQGYMUWCZPDN-DOMZBBRYSA-N` | (s,r)-mefloquine | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Naloxon | de | `UZHSEJADLWPNLE-GRGSLBFTSA-N` | `UZHSEJADLWPNLE-BIAVLDQUSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| penicillamine | en | `VVNCNSJFMMFHPL-VKHMYHEASA-N` | `VVNCNSJFMMFHPL-GSVOUGTGSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Penicillamin | de | `VVNCNSJFMMFHPL-VKHMYHEASA-N` | `VVNCNSJFMMFHPL-GSVOUGTGSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| sulfasalazine | en | `NCEXYHBECQHGNR-QZQOTICOSA-N` | `NCEXYHBECQHGNR-UHFFFAOYSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Sulfasalazin | de | `NCEXYHBECQHGNR-QZQOTICOSA-N` | `NCEXYHBECQHGNR-UHFFFAOYSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| tranexamic acid | en | `GYDJEQRTZSCIOI-LJGSYFOKSA-N` | `GYDJEQRTZSCIOI-UHFFFAOYSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Tranexamsäure | de | `GYDJEQRTZSCIOI-LJGSYFOKSA-N` | `GYDJEQRTZSCIOI-UHFFFAOYSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| vinblastine | en | `JXLYSJRDGCGARV-XQKSVPLYSA-N` | `JXLYSJRDGCGARV-CFWMRBGOSA-N` | vinblastine | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Vinblastin | de | `JXLYSJRDGCGARV-XQKSVPLYSA-N` | `JXLYSJRDGCGARV-CFWMRBGOSA-N` | vinblastine | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Vinorelbin | de | `GBABOYUKABKIAF-IELIFDKJSA-N` | `GBABOYUKABKIAF-GHYRFKGUSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| cocaine | en | `ZPUCINDJVBIVPJ-PFSRBDOWSA-N` | `ZPUCINDJVBIVPJ-LJISPDSOSA-N` | cocaine | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Adrenalin | de | `UCTWMZQNUQWSLP-VIFPVBQESA-N` | `UCTWMZQNUQWSLP-UHFFFAOYSA-N` | racepinephrine | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| pantothenic acid | en | `GHOKWGTUZJEAQD-UHFFFAOYSA-N` | `GHOKWGTUZJEAQD-ZETCQYMHSA-N` | pantothenic acid | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Pantothensäure | de | `GHOKWGTUZJEAQD-UHFFFAOYSA-N` | `GHOKWGTUZJEAQD-ZETCQYMHSA-N` | pantothenic acid | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| trehalose | en | `HDTRYLNUVZCQOY-MFAKQEFJSA-N` | `HDTRYLNUVZCQOY-LIZSDCNHSA-N` | trehalose | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Xylit | de | `HEBKCHPVOIAQTA-SCDXWVJYSA-N` | `HEBKCHPVOIAQTA-NGQZWQHPSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |

### skelett

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| Prussian blue | en | `DNMNDNSFJMUUFM-UHFFFAOYSA-N` | `DCYOBGZUOMKFPA-UHFFFAOYSA-N` |  | Eisen-Cyanid-Gerüst; Wikidata und PubChem modellieren den Komplex verschieden — kein Zeichenfall. |
| Berliner Blau | de | `DNMNDNSFJMUUFM-UHFFFAOYSA-N` | `DCYOBGZUOMKFPA-UHFFFAOYSA-N` |  | wie Prussian blue. |
| doxycycline | en | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | Tautomer: gleiche Formel C22H24N2O8, PubChem modelliert die Carboximidsäure-Form; den Wikidata/ChEMBL-Schlüssel kennt PubChem nicht. Kein falscher Stoff. |
| Doxycyclin | de | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | wie doxycycline (Tautomer). |
| (−)-Ephedrin | de | `KWGRBVOPPLSCSI-WPRPVWTQSA-N` | `MWFDNXJPZUOTJB-UHFFFAOYSA-N` |  | PubChem selbst ordnet das Synonym '(−)-Ephedrin' CID 104213 zu (1-Brom-3-methyl-5-nitrobenzol; per curl auf /compound/name/…/cids nachgeprüft, mit Unicode-Minus und ASCII-Minus). Fehler im PubChem-Synonymindex; die Kaskade übernimmt den ersten Treffer ungeprüft. |
| Hydroxycobalamin | de | `YOZNUFWCRFCGIH-WZHZPDAFSA-K` | `DQOCFCZRZOAIBN-WZHZPDAFSA-L` |  | Cobalt-Komplex, PubChem-Record als Hydrat mit anderer Ladungsschreibweise — wie cyanocobalamin. |
| β-lactulose | en | `JCQLYHFGKNRPGE-FCVZTGTOSA-N` | `NBGXQZRRLOGAJF-FCVZTGTOSA-N` |  | Seit Lauf 3 über 'beta-lactulose' gefunden: gleiche Formel C12H22O11 und gleiche Stereo-Schicht, PubChem modelliert eine andere Ringform der Fructose-Einheit. Kein falscher Stoff. |
| rifabutin | en | `ATEBXHFBFRCZMA-VXTBVIBXSA-N` | `AZFBLLCNOQPJGJ-VXTBVIBXSA-N` |  | Gleiche Formel C46H62N4O11, den erwarteten Schlüssel kennt PubChem nicht; erhalten ist PubChems Rifabutin. Tautomer-/Darstellungsunterschied der Referenz, kein falscher Stoff. |
| Risperidon | de | `RAPZEAPATHNIPO-UHFFFAOYSA-N` | `WDNMHZRFIIOXOD-UHFFFAOYSA-N` | risperidon | PubChem führt den deutschen Namen als eigenes Record CID 44402564 (C23H29FN4O2, Dihydro-Form); per curl auf /compound/name/Risperidon/cids nachgeprüft. Synonymfehler bei PubChem, wie (−)-Ephedrin. |
| cyanocobalamin | en | `FDJOLVPMNUYSCM-UVKKECPRSA-L` | `RMRCNWBMXRMIRW-WZHZPDAFSA-L` |  | Gleiche Formel C63H88CoN14O14P; Cobalt-Komplex, von Wikidata und PubChem verschieden modelliert (wie Prussian blue). PubChems Titel des Erhaltenen: Cyanocobalamin. |

### nicht aufgelöst

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| Cefixim Anhydrat | de | `OKBVVJOGVLARMR-QSWIMTSFSA-N` | `—` |  | nicht aufloesbar (not_found) |
| N-Methylglucaminantimonat | de | `XOGYVDXPYVPAAQ-SESJOKTNSA-M` | `—` |  | nicht aufloesbar (not_found) |
| nitroprusside | en | `ASPOIVQEUUCDQT-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Nitroprussid | de | `ASPOIVQEUUCDQT-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Povidon-Iod | de | `CPKVUHPKYQGHMW-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| (S)-(−)-timolol | en | `BLJRIMJGRPQVNF-JTQLQIEISA-N` | `—` |  | nicht aufloesbar (not_found) |
| Metamizol (freie Säure) | de | `LVWZTYCIRDMTEY-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Citral A+B | de | `WTEVQBCEXWBHNA-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Ethylendiamintetraessigsäure | de | `KCXVZYZYPLLWCC-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |

### salz

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| Bendamustin | de | `YTKUWDBFDASYHO-UHFFFAOYSA-N` | `ZHSKUOZOLHMKEA-UHFFFAOYSA-N` | bendamustine hydrochloride | PubChem führt den deutschen Namen beim Hydrochlorid — Salz statt Wirkstoff. |
| Docusat | de | `APSBXTVYXVQYAB-UHFFFAOYSA-M` | `HNSDLXPSAYFUHK-UHFFFAOYSA-N` | docusate | Seit Lauf 3 über die englische Schreibweise 'Docusate' gefunden: PubChem liefert die freie Sulfonsäure (C20H38O7S), Wikidata erwartet das Natrium-Anion. Gleicher Wirkstoff, kein falscher Stoff. |

## Gelb

| Eingabe | Grund |
|---|---|
| paritaprevir | Referenz unsicher, abweichend (stereo): UAUIUKWPKRJZJV-QPLHLKROSA-N statt UAUIUKWPKRJZJV-MDJGTQRPSA-N |

## Langsamste Eingaben

| Eingabe | Sekunden | Status |
|---|---:|---|
| Zoledronsäure | 10.3 | gruen |
| Amidotrizoesäure | 10.0 | gruen |
| Levofolinsäure | 9.5 | gruen |
| Malonsäure | 9.4 | gruen |
| 4-Aminosalicylsäure | 9.1 | gruen |
| Phthalsäure | 8.9 | gruen |
| γ-Aminobuttersäure | 8.8 | gruen |
| Glycolsäure | 8.7 | gruen |
| Nicotinsäure | 8.6 | gruen |
| Metamizol (freie Säure) | 8.6 | rot |
