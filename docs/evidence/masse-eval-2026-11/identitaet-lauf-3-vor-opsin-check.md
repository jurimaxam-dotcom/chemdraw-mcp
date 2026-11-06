# Identität — Masse-Evaluation

Lauf 2026-11-05 · `uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json --protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`, Bericht: `uv run python scripts/masse_eval.py identitaet`

**711 Eingaben (414 Stoffe): 658 grün · 1 gelb · 52 rot.**

Erwartung: Wikidata-InChIKey, gegen ChEMBL geprüft (`tests/identity/stoffe-masse.json`). Laufzeit gesamt 12 min · Median 0.5 s · 90 % ≤ 4.5 s · langsamste 10.4 s je Eingabe (inkl. 0,3 s Pause).

## Rot nach Art

| Art | Zahl | Bedeutung |
|---|---:|---|
| stereo | 23 | gleiches Gerüst, andere Stereochemie (Racemat/Enantiomer/Isomer) |
| skelett | 17 | anderes Gerüst — falscher Stoff |
| nicht aufgelöst | 9 | Kaskade findet nichts, obwohl die Quelle den Stoff führt |
| salz | 3 | gleicher Wirkstoff, anderes Salz bzw. Gegenion (größtes Fragment gleich) |

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
| chloroxylenol | en | `OSDLLIBGSJNGJE-UHFFFAOYSA-N` | `OJFZXRZZXBFEAP-UHFFFAOYSA-N` |  | OPSIN (0,0 s, offline) zerlegt den Trivialnamen systematisch in chloro-xylen-ol und baut ein nicht-aromatisches Cyclohexadienol (CC1C(=CC=CC1(C)O)Cl) — gemeint ist PCMX, 4-Chlor-3,5-dimethylphenol. OPSIN gewinnt vor PubChem, darum fragt niemand nach. |
| doxycycline | en | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | Tautomer: gleiche Formel C22H24N2O8, PubChem modelliert die Carboximidsäure-Form; den Wikidata/ChEMBL-Schlüssel kennt PubChem nicht. Kein falscher Stoff. |
| Doxycyclin | de | `JBIWCJUYHHGXTC-AKNGSSGZSA-N` | `SGKRLCUYIXIAHR-AKNGSSGZSA-N` |  | wie doxycycline (Tautomer). |
| (−)-Ephedrin | de | `KWGRBVOPPLSCSI-WPRPVWTQSA-N` | `MWFDNXJPZUOTJB-UHFFFAOYSA-N` |  | PubChem selbst ordnet das Synonym '(−)-Ephedrin' CID 104213 zu (1-Brom-3-methyl-5-nitrobenzol; per curl auf /compound/name/…/cids nachgeprüft, mit Unicode-Minus und ASCII-Minus). Fehler im PubChem-Synonymindex; die Kaskade übernimmt den ersten Treffer ungeprüft. |
| Hydroxycobalamin | de | `YOZNUFWCRFCGIH-WZHZPDAFSA-K` | `DQOCFCZRZOAIBN-WZHZPDAFSA-L` |  | Cobalt-Komplex, PubChem-Record als Hydrat mit anderer Ladungsschreibweise — wie cyanocobalamin. |
| β-lactulose | en | `JCQLYHFGKNRPGE-FCVZTGTOSA-N` | `NBGXQZRRLOGAJF-FCVZTGTOSA-N` |  | Seit Lauf 3 über 'beta-lactulose' gefunden: gleiche Formel C12H22O11 und gleiche Stereo-Schicht, PubChem modelliert eine andere Ringform der Fructose-Einheit. Kein falscher Stoff. |
| methyldopa | en | `CJCSPKMFHVPWAR-JTQLQIEISA-N` | `QZIWDCLHLOADPK-ZETCQYMHSA-N` |  | OPSIN (offline, 0,0 s) liest 'methyl' + 'dopa' als N-Methyl-L-DOPA (CN[C@H](C(=O)O)…); Methyldopa ist α-Methyl-DOPA. Zweiter OPSIN-Fehlgriff bei einem Trivialnamen. |
| methylthioninium chloride | en | `CXKWCBBOMKCUKX-UHFFFAOYSA-M` | `UYIDWJXVRJXHKX-UHFFFAOYSA-N` |  | OPSIN baut aus 'methyl-thioninium' einen Methylthiepinium-Ring ([Cl-].CC=1[SH+]C=CC=CC=CC1) statt Methylenblau — dritter OPSIN-Fehlgriff, wieder offline in 0,0 s. |
| rifabutin | en | `ATEBXHFBFRCZMA-VXTBVIBXSA-N` | `AZFBLLCNOQPJGJ-VXTBVIBXSA-N` |  | Gleiche Formel C46H62N4O11, den erwarteten Schlüssel kennt PubChem nicht; erhalten ist PubChems Rifabutin. Tautomer-/Darstellungsunterschied der Referenz, kein falscher Stoff. |
| Risperidon | de | `RAPZEAPATHNIPO-UHFFFAOYSA-N` | `WDNMHZRFIIOXOD-UHFFFAOYSA-N` | risperidon | PubChem führt den deutschen Namen als eigenes Record CID 44402564 (C23H29FN4O2, Dihydro-Form); per curl auf /compound/name/Risperidon/cids nachgeprüft. Synonymfehler bei PubChem, wie (−)-Ephedrin. |
| tenofovir disoproxil | en | `SGOIRFVFHAKUTI-ZCFIWIBFSA-N` | `JFVZFKDSXNQEJW-CQSZACIVSA-N` | tenofovir disoproxil | Referenzfehler: Wikidata Q155954 trägt den InChIKey von Tenofovir (C9H14N5O4P), die Eingabe heißt aber Disoproxil; der Resolver liefert PubChems Tenofovir Disoproxil (C19H30N5O10P) — richtig. |
| tropicamide | en | `BGDKAVGWHJFAGW-UHFFFAOYSA-N` | `JJCZGVLYNIVKKD-UHFFFAOYSA-N` |  | OPSIN (0,0 s, offline) liest 'tropic-amide' und baut das Amid der Tropasäure (C(C(CO)c1ccccc1)(=O)N) — vierter OPSIN-Fehlgriff bei einem Trivialnamen. |
| Tropicamid | de | `BGDKAVGWHJFAGW-UHFFFAOYSA-N` | `JJCZGVLYNIVKKD-UHFFFAOYSA-N` |  | wie tropicamide (OPSIN). |
| fumaric acid | en | `BVSPPBKONISENN-SLHNCBLASA-N` | `VZCYOOQTPOCHFL-OWOJBTEDSA-N` | fumaric acid | Referenzfehler: Wikidata Q125026916 (Formel C20H33N3) ist nicht Fumarsäure; der Resolver liefert PubChems Fumaric Acid (C4H4O4). Lehrbuch-Liste beim nächsten `liste`-Lauf auf Q139857 pinnen. |
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
| sodium calcium edetate | en | `SHWNNYZBHZIQQV-UHFFFAOYSA-J` | `UEAVLBXLOZNDHT-UHFFFAOYSA-K` |  | Anderes Salz-Verhältnis (CaNa₂ erwartet, CaNa erhalten); gleicher Wirkstoff. |

## Gelb

| Eingabe | Grund |
|---|---|
| paritaprevir | Referenz unsicher, abweichend (stereo): UAUIUKWPKRJZJV-QPLHLKROSA-N statt UAUIUKWPKRJZJV-MDJGTQRPSA-N |

## Langsamste Eingaben

| Eingabe | Sekunden | Status |
|---|---:|---|
| Maleinsäure | 10.4 | gruen |
| Nicotinsäure | 10.4 | gruen |
| Acrylsäure | 10.2 | gruen |
| Glycolsäure | 9.6 | gruen |
| Ethylendiamintetraessigsäure | 9.4 | rot |
| 4-Aminosalicylsäure | 9.0 | gruen |
| γ-Aminobuttersäure | 9.0 | gruen |
| Levofolinsäure | 9.0 | gruen |
| Malonsäure | 8.9 | gruen |
| Phthalsäure | 8.8 | gruen |
