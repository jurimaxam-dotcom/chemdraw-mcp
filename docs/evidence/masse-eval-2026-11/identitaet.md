# Identität — Masse-Evaluation

Lauf 2026-11-05 · `uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json --protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`, Bericht: `uv run python scripts/masse_eval.py identitaet`

**711 Eingaben (414 Stoffe): 591 grün · 80 gelb · 40 rot.**

Erwartung: Wikidata-InChIKey, gegen ChEMBL geprüft (`tests/identity/stoffe-masse.json`). Laufzeit gesamt 62 min · Median 3.5 s · 90 % ≤ 24.2 s · langsamste 44.0 s je Eingabe (inkl. 0,3 s Pause).

## Rot nach Art

| Art | Zahl | Bedeutung |
|---|---:|---|
| stereo | 21 | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| skelett | 16 | anderes Gerüst — falscher Stoff |
| salz | 2 | gleicher Wirkstoff, anderes Salz bzw. Gegenion (größtes Fragment gleich) |
| nicht aufgelöst | 1 | Kaskade findet nichts, obwohl die Quelle den Stoff führt |

## Alle roten Fälle

### stereo

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| L-scopolamine | en | `STECJAGHUSJQJN-FWXGHANASA-N` | `STECJAGHUSJQJN-USLFZFAMSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
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
| trehalose | en | `HDTRYLNUVZCQOY-MFAKQEFJSA-N` | `HDTRYLNUVZCQOY-LIZSDCNHSA-N` | trehalose | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| Xylit | de | `HEBKCHPVOIAQTA-SCDXWVJYSA-N` | `HEBKCHPVOIAQTA-NGQZWQHPSA-N` |  | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |

### skelett

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| Prussian blue | en | `DNMNDNSFJMUUFM-UHFFFAOYSA-N` | `DCYOBGZUOMKFPA-UHFFFAOYSA-N` |  | Eisen-Cyanid-Gerüst; Wikidata und PubChem modellieren den Komplex verschieden — kein Zeichenfall. |
| Berliner Blau | de | `DNMNDNSFJMUUFM-UHFFFAOYSA-N` | `DCYOBGZUOMKFPA-UHFFFAOYSA-N` |  | wie Prussian blue. |
| chloroxylenol | en | `OSDLLIBGSJNGJE-UHFFFAOYSA-N` | `OJFZXRZZXBFEAP-UHFFFAOYSA-N` |  | OPSIN (0,0 s, offline) zerlegt den Trivialnamen systematisch in chloro-xylen-ol und baut ein nicht-aromatisches Cyclohexadienol (CC1C(=CC=CC1(C)O)Cl) — gemeint ist PCMX, 4-Chlor-3,5-dimethylphenol. OPSIN gewinnt vor PubChem, darum fragt niemand nach. |
| doxycycline | en | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | anderes Gerüst — falscher Stoff |
| Doxycyclin | de | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | anderes Gerüst — falscher Stoff |
| (−)-Ephedrin | de | `KWGRBVOPPLSCSI-WPRPVWTQSA-N` | `MWFDNXJPZUOTJB-UHFFFAOYSA-N` |  | PubChem selbst ordnet das Synonym '(−)-Ephedrin' CID 104213 zu (1-Brom-3-methyl-5-nitrobenzol; per curl auf /compound/name/…/cids nachgeprüft, mit Unicode-Minus und ASCII-Minus). Fehler im PubChem-Synonymindex; die Kaskade übernimmt den ersten Treffer ungeprüft. |
| Hydroxycobalamin | de | `YOZNUFWCRFCGIH-WZHZPDAFSA-K` | `DQOCFCZRZOAIBN-WZHZPDAFSA-L` |  | anderes Gerüst — falscher Stoff |
| methyldopa | en | `CJCSPKMFHVPWAR-JTQLQIEISA-N` | `QZIWDCLHLOADPK-ZETCQYMHSA-N` |  | OPSIN (offline, 0,0 s) liest 'methyl' + 'dopa' als N-Methyl-L-DOPA (CN[C@H](C(=O)O)…); Methyldopa ist α-Methyl-DOPA. Zweiter OPSIN-Fehlgriff bei einem Trivialnamen. |
| methylthioninium chloride | en | `CXKWCBBOMKCUKX-UHFFFAOYSA-M` | `UYIDWJXVRJXHKX-UHFFFAOYSA-N` |  | OPSIN baut aus 'methyl-thioninium' einen Methylthiepinium-Ring ([Cl-].CC=1[SH+]C=CC=CC=CC1) statt Methylenblau — dritter OPSIN-Fehlgriff, wieder offline in 0,0 s. |
| rifabutin | en | `ATEBXHFBFRCZMA-VXTBVIBXSA-N` | `AZFBLLCNOQPJGJ-VXTBVIBXSA-N` |  | anderes Gerüst — falscher Stoff |
| Risperidon | de | `RAPZEAPATHNIPO-UHFFFAOYSA-N` | `WDNMHZRFIIOXOD-UHFFFAOYSA-N` | risperidon | anderes Gerüst — falscher Stoff |
| tenofovir disoproxil | en | `SGOIRFVFHAKUTI-ZCFIWIBFSA-N` | `JFVZFKDSXNQEJW-CQSZACIVSA-N` | tenofovir disoproxil | anderes Gerüst — falscher Stoff |
| tropicamide | en | `BGDKAVGWHJFAGW-UHFFFAOYSA-N` | `JJCZGVLYNIVKKD-UHFFFAOYSA-N` |  | anderes Gerüst — falscher Stoff |
| Tropicamid | de | `BGDKAVGWHJFAGW-UHFFFAOYSA-N` | `JJCZGVLYNIVKKD-UHFFFAOYSA-N` |  | anderes Gerüst — falscher Stoff |
| fumaric acid | en | `BVSPPBKONISENN-SLHNCBLASA-N` | `VZCYOOQTPOCHFL-OWOJBTEDSA-N` | fumaric acid | anderes Gerüst — falscher Stoff |
| cyanocobalamin | en | `FDJOLVPMNUYSCM-UVKKECPRSA-L` | `RMRCNWBMXRMIRW-WZHZPDAFSA-L` |  | anderes Gerüst — falscher Stoff |

### salz

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| Bendamustin | de | `YTKUWDBFDASYHO-UHFFFAOYSA-N` | `ZHSKUOZOLHMKEA-UHFFFAOYSA-N` | bendamustine hydrochloride | PubChem führt den deutschen Namen beim Hydrochlorid — Salz statt Wirkstoff. |
| sodium calcium edetate | en | `SHWNNYZBHZIQQV-UHFFFAOYSA-J` | `UEAVLBXLOZNDHT-UHFFFAOYSA-K` |  | gleicher Wirkstoff, anderes Salz bzw. Gegenion (größtes Fragment gleich) |

### nicht aufgelöst

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| nitroprusside | en | `ASPOIVQEUUCDQT-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |

## Gelb

| Eingabe | Grund |
|---|---|
| (RS)-Cyclophosphamid | Quelle weg (partial) |
| 4-Aminosalicylsäure | Quelle weg (partial) |
| Levofolinsäure | Quelle weg (partial) |
| L-Scopolamin | Quelle weg (partial) |
| Alcuroniumchlorid | Quelle weg (partial) |
| Amilorid | Quelle weg (partial) |
| Amiodaron | Quelle weg (partial) |
| Artesunat | Quelle weg (partial) |
| Atracurium-Besilat | Quelle weg (partial) |
| Beclometasondipropionat | Quelle weg (partial) |
| Bedaquilin | Quelle weg (partial) |
| Betamethason | Quelle weg (partial) |
| Bicalutamid | Quelle weg (partial) |
| Calciumgluconat | Quelle weg (partial) |
| Cefixim Anhydrat | Quelle weg (partial) |
| Ceftazidim | Quelle weg (partial) |
| Clofazimin | Quelle weg (partial) |
| Clomipramin | Quelle weg (partial) |
| Cyclizin | Quelle weg (partial) |
| Dacarbazin | Quelle weg (partial) |
| Dexamethason | Quelle weg (partial) |
| Amidotrizoesäure | Quelle weg (partial) |
| Didanosin | Quelle weg (partial) |
| Diethylcarbamazin | Quelle weg (partial) |
| Diloxanidfuroat | Quelle weg (partial) |
| Docusat | Quelle weg (partial) |
| Emtricitabin | Quelle weg (partial) |
| Ethionamid | Quelle weg (partial) |
| Ethosuximid | Quelle weg (partial) |
| Etoposid | Quelle weg (partial) |
| 5-Fluorcytosin | Quelle weg (partial) |
| Fludarabin-Phosphat | Quelle weg (partial) |
| Fludrocortison | Quelle weg (partial) |
| Gemcitabin | Quelle weg (partial) |
| Glibenclamid | Quelle weg (partial) |
| gliclazid | Quelle weg (partial) |
| Hydroxychloroquin | Quelle weg (partial) |
| Isofluran | Quelle weg (partial) |
| (RS)-ketamine | Quelle weg (partial) |
| (RS)-Ketamin | Quelle weg (partial) |
| β-lactulose | Quelle weg (partial) |
| Lamivudin | Quelle weg (partial) |
| Lamotrigin | Quelle weg (partial) |
| Loperamid | Quelle weg (partial) |
| Loratadin | Quelle weg (partial) |
| Medroxyprogesteronacetat | Quelle weg (partial) |
| N-Methylglucaminantimonat | Quelle weg (partial) |
| (RS)-methadone | Quelle weg (partial) |
| (RS)-Methadon | Quelle weg (partial) |
| Metoclopramid | Quelle weg (partial) |
| Nevirapin | Quelle weg (partial) |
| Nifedipin | Quelle weg (partial) |
| Nitroprussid | Quelle weg (partial) |
| Oxamniquin | Quelle weg (partial) |
| paritaprevir | Referenz unsicher, abweichend (stereo): UAUIUKWPKRJZJV-QPLHLKROSA-N statt UAUIUKWPKRJZJV-MDJGTQRPSA-N |
| Povidon-Iod | Quelle weg (partial) |
| Pyridostigmin | Quelle weg (partial) |
| Silbersulfadiazin | Quelle weg (partial) |
| Natriumlactat | Quelle weg (partial) |
| Spironolacton | Quelle weg (partial) |
| meso-Dimercaptobernsteinsäure | Quelle weg (partial) |
| Natriumthiopental | Quelle weg (partial) |
| (S)-(−)-timolol | Quelle weg (partial) |
| Ulipristalacetat | Quelle weg (partial) |
| Vecuronium-Bromid | Quelle weg (partial) |
| Xylometazolin | Quelle weg (partial) |
| Zoledronsäure | Quelle weg (partial) |
| Diphenhydramin | Quelle weg (partial) |
| Metamizol (freie Säure) | Quelle weg (partial) |
| Torasemid | Quelle weg (partial) |
| Citral A+B | Quelle weg (partial) |
| γ-Aminobuttersäure | Quelle weg (partial) |
| Acrylsäure | Quelle weg (partial) |
| Ethylendiamintetraessigsäure | Quelle weg (partial) |
| Glycolsäure | Quelle weg (partial) |
| Maleinsäure | Quelle weg (partial) |
| Malonsäure | Quelle weg (partial) |
| Phthalsäure | Quelle weg (partial) |
| Nicotinsäure | Quelle weg (partial) |
| Pantothensäure | Quelle weg (partial) |

## Langsamste Eingaben

| Eingabe | Sekunden | Status |
|---|---:|---|
| Betamethason | 44.0 | gelb |
| Pantothensäure | 41.3 | gelb |
| Acrylsäure | 40.8 | gelb |
| meso-Dimercaptobernsteinsäure | 39.4 | gelb |
| Phthalsäure | 39.3 | gelb |
| Zoledronsäure | 39.2 | gelb |
| Malonsäure | 39.2 | gelb |
| Ethylendiamintetraessigsäure | 39.2 | gelb |
| γ-Aminobuttersäure | 39.0 | gelb |
| 4-Aminosalicylsäure | 38.9 | gelb |
