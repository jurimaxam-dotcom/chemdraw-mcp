# Identität — Masse-Evaluation

Lauf 2026-11-07 · `uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json --protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`, Bericht: `uv run python scripts/masse_eval.py identitaet`

**711 Eingaben (415 Wikidata-Stoffe, 414 unterschiedliche InChIKeys): 683 grün · 9 gelb (Quelle/Referenz) · 3 gelb (Tautomer) · 2 gelb (E/Z fehlt) · 14 rot.**

Erwartung: Wikidata-InChIKey, gegen ChEMBL geprüft (`tests/identity/stoffe-masse.json`). Laufzeit gesamt 16 min · Median 0.7 s · 90 % ≤ 4.6 s · langsamste 10.4 s je Eingabe (inkl. 0,3 s Pause).

## Rot nach Art

| Art | Zahl | Bedeutung |
|---|---:|---|
| stereo | 14 | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |

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
| tranexamic acid | en | `GYDJEQRTZSCIOI-LJGSYFOKSA-N` | `GYDJEQRTZSCIOI-UHFFFAOYSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Tranexamsäure | de | `GYDJEQRTZSCIOI-LJGSYFOKSA-N` | `GYDJEQRTZSCIOI-UHFFFAOYSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Vinorelbin | de | `GBABOYUKABKIAF-IELIFDKJSA-N` | `GBABOYUKABKIAF-GHYRFKGUSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Adrenalin | de | `UCTWMZQNUQWSLP-VIFPVBQESA-N` | `UCTWMZQNUQWSLP-UHFFFAOYSA-N` | racepinephrine | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Xylit | de | `HEBKCHPVOIAQTA-SCDXWVJYSA-N` | `HEBKCHPVOIAQTA-NGQZWQHPSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |

## Gelb nach Art

| Art | Zahl |
|---|---:|
| Quelle/Referenz | 9 |
| Tautomer | 3 |
| E/Z fehlt | 2 |

## Gelb

| Eingabe | Grund |
|---|---|
| Docusat | Referenz unsicher, abweichend (salz): HNSDLXPSAYFUHK-UHFFFAOYSA-N statt APSBXTVYXVQYAB-UHFFFAOYSA-M |
| doxycycline | Tautomer der Referenz: SGKRLCUYIXIAHR-AKNGSSGZSA-N statt JBIWCJUYHHGXTC-AKNGSSGZSA-N |
| Doxycyclin | Tautomer der Referenz: SGKRLCUYIXIAHR-AKNGSSGZSA-N statt JBIWCJUYHHGXTC-AKNGSSGZSA-N |
| Hydroxycobalamin | Referenz unsicher, abweichend (skelett): DQOCFCZRZOAIBN-WZHZPDAFSA-L statt YOZNUFWCRFCGIH-WZHZPDAFSA-K |
| nitroprusside | bekannte Luecke, weiterhin unauffindbar |
| Nitroprussid | bekannte Luecke, weiterhin unauffindbar |
| paritaprevir | Referenz unsicher, abweichend (stereo): UAUIUKWPKRJZJV-QPLHLKROSA-N statt UAUIUKWPKRJZJV-MDJGTQRPSA-N |
| Povidon-Iod | bekannte Luecke, weiterhin unauffindbar |
| rifabutin | Tautomer der Referenz: AZFBLLCNOQPJGJ-VXTBVIBXSA-N statt ATEBXHFBFRCZMA-VXTBVIBXSA-N |
| sulfasalazine | E/Z der Referenz fehlt: NCEXYHBECQHGNR-UHFFFAOYSA-N statt NCEXYHBECQHGNR-QZQOTICOSA-N |
| Sulfasalazin | E/Z der Referenz fehlt: NCEXYHBECQHGNR-UHFFFAOYSA-N statt NCEXYHBECQHGNR-QZQOTICOSA-N |
| vinblastine | Referenz unsicher, abweichend (stereo): JXLYSJRDGCGARV-CFWMRBGOSA-N statt JXLYSJRDGCGARV-XQKSVPLYSA-N |
| Vinblastin | Referenz unsicher, abweichend (stereo): JXLYSJRDGCGARV-CFWMRBGOSA-N statt JXLYSJRDGCGARV-XQKSVPLYSA-N |
| cyanocobalamin | Referenz unsicher, abweichend (skelett): RMRCNWBMXRMIRW-WZHZPDAFSA-L statt FDJOLVPMNUYSCM-UVKKECPRSA-L |

## Langsamste Eingaben

| Eingabe | Sekunden | Status |
|---|---:|---|
| Ethylendiamintetraessigsäure | 10.4 | gruen |
| meso-Dimercaptobernsteinsäure | 10.2 | gruen |
| Malonsäure | 9.9 | gruen |
| Pantothensäure | 9.5 | gruen |
| Maleinsäure | 9.4 | gruen |
| 4-Aminosalicylsäure | 9.3 | gruen |
| Glycolsäure | 9.3 | gruen |
| Metamizol (freie Säure) | 9.2 | gruen |
| Acrylsäure | 9.2 | gruen |
| Zoledronsäure | 9.1 | gruen |
