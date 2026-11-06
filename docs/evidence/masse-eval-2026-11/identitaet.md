# Identität — Masse-Evaluation

Lauf 2026-11-06 · `uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json --protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`, Bericht: `uv run python scripts/masse_eval.py identitaet`

**711 Eingaben (413 Stoffe): 674 grün · 1 gelb · 36 rot.**

Erwartung: Wikidata-InChIKey, gegen ChEMBL geprüft (`tests/identity/stoffe-masse.json`). Laufzeit gesamt 13 min · Median 0.6 s · 90 % ≤ 4.0 s · langsamste 18.6 s je Eingabe (inkl. 0,3 s Pause).

## Rot nach Art

| Art | Zahl | Bedeutung |
|---|---:|---|
| stereo | 18 | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| nicht aufgelöst | 9 | Kaskade findet nichts, obwohl die Quelle den Stoff führt |
| skelett | 8 | anderes Gerüst — falscher Stoff |
| salz | 1 | gleicher Wirkstoff, anderes Salz bzw. Gegenion (größtes Fragment gleich) |

Nicht aufgelöst nach Sprache der Eingabe: de 7 · en 2

## Alle roten Fälle

### stereo

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| L-scopolamine | en | `STECJAGHUSJQJN-FWXGHANASA-N` | `STECJAGHUSJQJN-USLFZFAMSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| L-Scopolamin | de | `STECJAGHUSJQJN-FWXGHANASA-N` | `STECJAGHUSJQJN-USLFZFAMSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Benzylpenicillin-Benzathin | de | `BVGLIYRKPOITBQ-ANPZCEIESA-N` | `BVGLIYRKPOITBQ-UHFFFAOYSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
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
| Adrenalin | de | `UCTWMZQNUQWSLP-VIFPVBQESA-N` | `UCTWMZQNUQWSLP-UHFFFAOYSA-N` | racepinephrine | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Xylit | de | `HEBKCHPVOIAQTA-SCDXWVJYSA-N` | `HEBKCHPVOIAQTA-NGQZWQHPSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |

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

### skelett

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| Prussian blue | en | `DNMNDNSFJMUUFM-UHFFFAOYSA-N` | `DCYOBGZUOMKFPA-UHFFFAOYSA-N` |  | Eisen-Cyanid-Gerüst; Wikidata und PubChem modellieren den Komplex verschieden — kein Zeichenfall. |
| Berliner Blau | de | `DNMNDNSFJMUUFM-UHFFFAOYSA-N` | `DCYOBGZUOMKFPA-UHFFFAOYSA-N` |  | wie Prussian blue. |
| doxycycline | en | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | Tautomer: gleiche Formel C22H24N2O8, PubChem modelliert die Carboximidsäure-Form; den Wikidata/ChEMBL-Schlüssel kennt PubChem nicht. Kein falscher Stoff. |
| Doxycyclin | de | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | wie doxycycline (Tautomer). |
| Hydroxycobalamin | de | `YOZNUFWCRFCGIH-WZHZPDAFSA-K` | `DQOCFCZRZOAIBN-WZHZPDAFSA-L` |  | Cobalt-Komplex, PubChem-Record als Hydrat mit anderer Ladungsschreibweise — wie cyanocobalamin. |
| β-lactulose | en | `JCQLYHFGKNRPGE-FCVZTGTOSA-N` | `NBGXQZRRLOGAJF-FCVZTGTOSA-N` |  | Seit Lauf 3 über 'beta-lactulose' gefunden: gleiche Formel C12H22O11 und gleiche Stereo-Schicht, PubChem modelliert eine andere Ringform der Fructose-Einheit. Kein falscher Stoff. |
| rifabutin | en | `ATEBXHFBFRCZMA-VXTBVIBXSA-N` | `ZWBTYMGEBZUQTK-PVLSIAFMSA-N` |  | Gleiche Formel C46H62N4O11, den erwarteten Schlüssel kennt PubChem nicht; erhalten ist PubChems Rifabutin. Tautomer-/Darstellungsunterschied der Referenz, kein falscher Stoff. |
| cyanocobalamin | en | `FDJOLVPMNUYSCM-UVKKECPRSA-L` | `RMRCNWBMXRMIRW-WZHZPDAFSA-L` |  | Gleiche Formel C63H88CoN14O14P; Cobalt-Komplex, von Wikidata und PubChem verschieden modelliert (wie Prussian blue). PubChems Titel des Erhaltenen: Cyanocobalamin. |

### salz

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| Docusat | de | `APSBXTVYXVQYAB-UHFFFAOYSA-M` | `HNSDLXPSAYFUHK-UHFFFAOYSA-N` | docusate | Seit Lauf 3 über die englische Schreibweise 'Docusate' gefunden: PubChem liefert die freie Sulfonsäure (C20H38O7S), Wikidata erwartet das Natrium-Anion. Gleicher Wirkstoff, kein falscher Stoff. |

## Gelb

| Eingabe | Grund |
|---|---|
| paritaprevir | Referenz unsicher, abweichend (stereo): UAUIUKWPKRJZJV-QPLHLKROSA-N statt UAUIUKWPKRJZJV-MDJGTQRPSA-N |

## Langsamste Eingaben

| Eingabe | Sekunden | Status |
|---|---:|---|
| N-Methylglucaminantimonat | 18.6 | rot |
| γ-Aminobuttersäure | 9.1 | gruen |
| Malonsäure | 8.9 | gruen |
| Maleinsäure | 8.6 | gruen |
| Phthalsäure | 8.4 | gruen |
| Acrylsäure | 8.4 | gruen |
| Ethylendiamintetraessigsäure | 8.4 | rot |
| Glycolsäure | 8.4 | gruen |
| 4-Aminosalicylsäure | 8.4 | gruen |
| Zoledronsäure | 8.3 | gruen |
