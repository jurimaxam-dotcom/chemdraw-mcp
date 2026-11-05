# Identität — Masse-Evaluation

Lauf 2026-11-05 · `uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json --protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`, Bericht: `uv run python scripts/masse_eval.py identitaet`

**711 Eingaben (414 Stoffe): 591 grün · 1 gelb · 119 rot.**

Erwartung: Wikidata-InChIKey, gegen ChEMBL geprüft (`tests/identity/stoffe-masse.json`). Laufzeit gesamt 37 min · Median 3.5 s · 90 % ≤ 7.0 s · langsamste 15.4 s je Eingabe (inkl. 0,3 s Pause).

## Rot nach Art

| Art | Zahl | Bedeutung |
|---|---:|---|
| nicht aufgelöst | 80 | Kaskade findet nichts, obwohl die Quelle den Stoff führt |
| stereo | 21 | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| skelett | 16 | anderes Gerüst — falscher Stoff |
| salz | 2 | gleicher Wirkstoff, anderes Salz bzw. Gegenion (größtes Fragment gleich) |

Nicht aufgelöst nach Sprache der Eingabe: de 75 · en 5

## Alle roten Fälle

### nicht aufgelöst

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| (RS)-Cyclophosphamid | de | `CMSMOCZEIVJLDB-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| 4-Aminosalicylsäure | de | `WUBBRNOQWQTFEX-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Levofolinsäure | de | `VVIAGPKUTFNRDU-STQMWFEESA-N` | `—` |  | nicht aufloesbar (not_found) |
| L-Scopolamin | de | `STECJAGHUSJQJN-FWXGHANASA-N` | `—` |  | nicht aufloesbar (not_found) |
| Alcuroniumchlorid | de | `CPYGBGOXCJJJGC-GKLGUMFISA-L` | `—` |  | nicht aufloesbar (not_found) |
| Amilorid | de | `XSDQTOBWRPYKKA-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Amiodaron | de | `IYIKLHRQXLHMJQ-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Artesunat | de | `FIHJKUPKCHIPAT-AHIGJZGOSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Atracurium-Besilat | de | `XXZSQOVSEBAPGS-UHFFFAOYSA-L` | `—` |  | nicht aufloesbar (not_found) |
| Beclometasondipropionat | de | `KUVIULQEHSCUHY-XYWKZLDCSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Bedaquilin | de | `QUIJNHUBAXPXFS-XLJNKUFUSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Betamethason | de | `UREBDLICKHMUKA-DVTGEIKXSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Bicalutamid | de | `LKJPYSCBVHEWIU-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Calciumgluconat | de | `NEEHYRZPVYRGPP-IYEMJOQQSA-L` | `—` |  | nicht aufloesbar (not_found) |
| Cefixim Anhydrat | de | `OKBVVJOGVLARMR-QSWIMTSFSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Ceftazidim | de | `ORFOPKXBNMVMKC-DWVKKRMSSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Clofazimin | de | `WDQPAMHFFCXSNU-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Clomipramin | de | `GDLIGKIOYRNHDA-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Cyclizin | de | `UVKZSORBKUEBAZ-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Dacarbazin | de | `FDKXTQMXEQVLRF-ZHACJKMWSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Dexamethason | de | `UREBDLICKHMUKA-CXSFZGCWSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Amidotrizoesäure | de | `YVPYQUNUQOZFHG-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Didanosin | de | `BXZVVICBKDXVGW-NKWVEPMBSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Diethylcarbamazin | de | `RCKMWOKWVGPNJF-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Diloxanidfuroat | de | `BDYYDXJSHYEDGB-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Docusat | de | `APSBXTVYXVQYAB-UHFFFAOYSA-M` | `—` |  | nicht aufloesbar (not_found) |
| Emtricitabin | de | `XQSPYNMVSIKCOC-NTSWFWBYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Ethionamid | de | `AEOCXXJPGCBFJA-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Ethosuximid | de | `HAPOVYFOVVWLRS-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Etoposid | de | `VJJPUSNTGOMMGY-MRVIYFEKSA-N` | `—` |  | nicht aufloesbar (not_found) |
| 5-Fluorcytosin | de | `XRECTZIEBJDKEO-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Fludarabin-Phosphat | de | `GIUYCYHIANZCFB-FJFJXFQQSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Fludrocortison | de | `AAXVEMMRQDVLJB-BULBTXNYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Gemcitabin | de | `SDUQYLNIPVEERB-QPPQHZFASA-N` | `—` |  | nicht aufloesbar (not_found) |
| Glibenclamid | de | `ZNNLBTZKUZBEKO-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| gliclazid | de | `BOVGTQGAOIONJV-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Hydroxychloroquin | de | `XXSMGPRMXLTPCZ-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Isofluran | de | `PIWKPBJCKXDKJR-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| (RS)-ketamine | en | `YQEZLKZALYSWHR-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| (RS)-Ketamin | de | `YQEZLKZALYSWHR-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| β-lactulose | en | `JCQLYHFGKNRPGE-FCVZTGTOSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Lamivudin | de | `JTEGQNOMFQHVDC-NKWVEPMBSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Lamotrigin | de | `PYZRQGJRPPTADH-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Loperamid | de | `RDOIQAHITMMDAJ-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Loratadin | de | `JCCNYMKQOSZNPW-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Medroxyprogesteronacetat | de | `PSGAAPLEWMOORI-PEINSRQWSA-N` | `—` |  | nicht aufloesbar (not_found) |
| N-Methylglucaminantimonat | de | `XOGYVDXPYVPAAQ-SESJOKTNSA-M` | `—` |  | nicht aufloesbar (not_found) |
| (RS)-methadone | en | `USSIQXCVUWKGNF-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| (RS)-Methadon | de | `USSIQXCVUWKGNF-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Metoclopramid | de | `TTWJBBZEZQICBI-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Nevirapin | de | `NQDJXKOVJZTUJA-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Nifedipin | de | `HYIMSNHJOBLJNT-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| nitroprusside | en | `ASPOIVQEUUCDQT-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Nitroprussid | de | `ASPOIVQEUUCDQT-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Oxamniquin | de | `XCGYUJZMCCFSRP-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Povidon-Iod | de | `CPKVUHPKYQGHMW-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Pyridostigmin | de | `RVOLLAQWKVFTGE-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Silbersulfadiazin | de | `UEJSSZHHYBHCEL-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Natriumlactat | de | `NGSFWBMYFKHRBD-UHFFFAOYSA-M` | `—` |  | nicht aufloesbar (not_found) |
| Spironolacton | de | `LXMSZDCAJNLERA-ZHYRCANASA-N` | `—` |  | nicht aufloesbar (not_found) |
| meso-Dimercaptobernsteinsäure | de | `ACTRVOBWPAIOHC-XIXRPRMCSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Natriumthiopental | de | `AWLILQARPMWUHA-UHFFFAOYSA-M` | `—` |  | nicht aufloesbar (not_found) |
| (S)-(−)-timolol | en | `BLJRIMJGRPQVNF-JTQLQIEISA-N` | `—` |  | nicht aufloesbar (not_found) |
| Ulipristalacetat | de | `OOLLAFOLCSJHRE-ZHAKMVSLSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Vecuronium-Bromid | de | `VEPSYABRBFXYIB-PWXDFCLTSA-M` | `—` |  | nicht aufloesbar (not_found) |
| Xylometazolin | de | `HUCJFAOMUPXHDK-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Zoledronsäure | de | `XRASPMIURGNCCH-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Diphenhydramin | de | `ZZVUWRFHKOJYTH-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Metamizol (freie Säure) | de | `LVWZTYCIRDMTEY-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Torasemid | de | `NGBFQHCMQULJNZ-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Citral A+B | de | `WTEVQBCEXWBHNA-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| γ-Aminobuttersäure | de | `BTCSSZJGUNDROE-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Acrylsäure | de | `NIXOWILDQLNWCW-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Ethylendiamintetraessigsäure | de | `KCXVZYZYPLLWCC-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Glycolsäure | de | `AEMRFAOFKBGASW-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Maleinsäure | de | `VZCYOOQTPOCHFL-UPHRSURJSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Malonsäure | de | `OFOBLEOULBTSOW-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Phthalsäure | de | `XNGIFLGASWRNHJ-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Nicotinsäure | de | `PVNIIMVLHYAWGP-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |
| Pantothensäure | de | `GHOKWGTUZJEAQD-UHFFFAOYSA-N` | `—` |  | nicht aufloesbar (not_found) |

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
| doxycycline | en | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | Tautomer: gleiche Formel C22H24N2O8, PubChem modelliert die Carboximidsäure-Form; den Wikidata/ChEMBL-Schlüssel kennt PubChem nicht. Kein falscher Stoff. |
| Doxycyclin | de | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | wie doxycycline (Tautomer). |
| (−)-Ephedrin | de | `KWGRBVOPPLSCSI-WPRPVWTQSA-N` | `MWFDNXJPZUOTJB-UHFFFAOYSA-N` |  | PubChem selbst ordnet das Synonym '(−)-Ephedrin' CID 104213 zu (1-Brom-3-methyl-5-nitrobenzol; per curl auf /compound/name/…/cids nachgeprüft, mit Unicode-Minus und ASCII-Minus). Fehler im PubChem-Synonymindex; die Kaskade übernimmt den ersten Treffer ungeprüft. |
| Hydroxycobalamin | de | `YOZNUFWCRFCGIH-WZHZPDAFSA-K` | `DQOCFCZRZOAIBN-WZHZPDAFSA-L` |  | Cobalt-Komplex, PubChem-Record als Hydrat mit anderer Ladungsschreibweise — wie cyanocobalamin. |
| methyldopa | en | `CJCSPKMFHVPWAR-JTQLQIEISA-N` | `QZIWDCLHLOADPK-ZETCQYMHSA-N` |  | OPSIN (offline, 0,0 s) liest 'methyl' + 'dopa' als N-Methyl-L-DOPA (CN[C@H](C(=O)O)…); Methyldopa ist α-Methyl-DOPA. Zweiter OPSIN-Fehlgriff bei einem Trivialnamen. |
| methylthioninium chloride | en | `CXKWCBBOMKCUKX-UHFFFAOYSA-M` | `UYIDWJXVRJXHKX-UHFFFAOYSA-N` |  | OPSIN baut aus 'methyl-thioninium' einen Methylthiepinium-Ring ([Cl-].CC=1[SH+]C=CC=CC=CC1) statt Methylenblau — dritter OPSIN-Fehlgriff, wieder offline in 0,0 s. |
| rifabutin | en | `ATEBXHFBFRCZMA-VXTBVIBXSA-N` | `AZFBLLCNOQPJGJ-VXTBVIBXSA-N` |  | Gleiche Formel C46H62N4O11, den erwarteten Schlüssel kennt PubChem nicht; erhalten ist PubChems Rifabutin. Tautomer-/Darstellungsunterschied der Referenz, kein falscher Stoff. |
| Risperidon | de | `RAPZEAPATHNIPO-UHFFFAOYSA-N` | `WDNMHZRFIIOXOD-UHFFFAOYSA-N` | risperidon | PubChem führt den deutschen Namen als eigenes Record CID 44402564 (C23H29FN4O2, Dihydro-Form); per curl auf /compound/name/Risperidon/cids nachgeprüft. Synonymfehler bei PubChem, wie (−)-Ephedrin. |
| tenofovir disoproxil | en | `SGOIRFVFHAKUTI-ZCFIWIBFSA-N` | `JFVZFKDSXNQEJW-CQSZACIVSA-N` | tenofovir disoproxil | Referenzfehler: Wikidata Q155954 trägt den InChIKey von Tenofovir (C9H14N5O4P), die Eingabe heißt aber Disoproxil; der Resolver liefert PubChems Tenofovir Disoproxil (C19H30N5O10P) — richtig. |
| tropicamide | en | `BGDKAVGWHJFAGW-UHFFFAOYSA-N` | `JJCZGVLYNIVKKD-UHFFFAOYSA-N` |  | OPSIN (0,0 s, offline) liest 'tropic-amide' und baut das Amid der Tropasäure (C(C(CO)c1ccccc1)(=O)N) — vierter OPSIN-Fehlgriff bei einem Trivialnamen. |
| Tropicamid | de | `BGDKAVGWHJFAGW-UHFFFAOYSA-N` | `JJCZGVLYNIVKKD-UHFFFAOYSA-N` |  | wie tropicamide (OPSIN). |
| fumaric acid | en | `BVSPPBKONISENN-SLHNCBLASA-N` | `VZCYOOQTPOCHFL-OWOJBTEDSA-N` | fumaric acid | Referenzfehler: Wikidata Q125026916 (Formel C20H33N3) ist nicht Fumarsäure; der Resolver liefert PubChems Fumaric Acid (C4H4O4). Lehrbuch-Liste beim nächsten `liste`-Lauf auf Q139857 pinnen. |
| cyanocobalamin | en | `FDJOLVPMNUYSCM-UVKKECPRSA-L` | `RMRCNWBMXRMIRW-WZHZPDAFSA-L` |  | Gleiche Formel C63H88CoN14O14P; Cobalt-Komplex, von Wikidata und PubChem verschieden modelliert (wie Prussian blue). PubChems Titel des Erhaltenen: Cyanocobalamin. |

### salz

| Eingabe | Sprache | erwartet | erhalten | ChEMBL-Name des Erhaltenen | Deutung |
|---|---|---|---|---|---|
| Bendamustin | de | `YTKUWDBFDASYHO-UHFFFAOYSA-N` | `ZHSKUOZOLHMKEA-UHFFFAOYSA-N` | bendamustine hydrochloride | PubChem führt den deutschen Namen beim Hydrochlorid — Salz statt Wirkstoff. |
| sodium calcium edetate | en | `SHWNNYZBHZIQQV-UHFFFAOYSA-J` | `UEAVLBXLOZNDHT-UHFFFAOYSA-K` |  | Anderes Salz-Verhältnis (CaNa₂ erwartet, CaNa erhalten); gleicher Wirkstoff. |

## Gelb

| Eingabe | Grund |
|---|---|
| paritaprevir | Referenz unsicher, abweichend (stereo): UAUIUKWPKRJZJV-QPLHLKROSA-N statt UAUIUKWPKRJZJV-MDJGTQRPSA-N |

## Langsamste Eingaben

| Eingabe | Sekunden | Status |
|---|---:|---|
| Acrylsäure | 15.4 | rot |
| Pantothensäure | 15.2 | rot |
| meso-Dimercaptobernsteinsäure | 15.1 | rot |
| Amidotrizoesäure | 14.4 | rot |
| Metamizol (freie Säure) | 14.4 | rot |
| Glycolsäure | 14.3 | rot |
| Nicotinsäure | 14.2 | rot |
| γ-Aminobuttersäure | 14.2 | rot |
| Maleinsäure | 14.2 | rot |
| Zoledronsäure | 14.2 | rot |
