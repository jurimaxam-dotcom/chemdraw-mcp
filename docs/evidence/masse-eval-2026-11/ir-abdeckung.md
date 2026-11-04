# IR-Regelabdeckung — Masse-Evaluation

Stand 2026-11-05 · `uv run python scripts/masse_eval.py ir` · offline, < 10 s

**414 Moleküle** (ein Eintrag je InChIKey aus `tests/identity/stoffe-masse.json`, SMILES aus Wikidata, nicht aus `resolve()` — der Bericht hängt also nicht vom Identitätslauf ab). Je Molekül: 43 eigene SMARTS-Gruppen (unabhängig von `_IR_TABLE` geschrieben, Liste `IR_GRUPPEN` im Skript) gegen die Gruppen, die `spectro.expected_ir_bands` (= `predict_spectrum`) meldet.

**Lücke** = Gruppe mit diagnostischer Bande ist im Molekül, aber keine passende Regel der Tabelle feuert. Gruppen ohne diagnostische Bande (tertiäres Amin, Thioether, Azo, quartäres Ammonium) zählen nie als Lücke. Keine Änderung an `spectro.py` — nur Befund.

## Lücken der Tabelle (nach Zahl betroffener Moleküle)

| Gruppe | kommt vor in | ohne passende Bande | Anteil | Regel in `_IR_TABLE`? | erwartete Bande / Ursache | Beispiele |
|---|---:|---:|---:|---|---|---|
| Heteroaromat (Ring-N/O/S) | 134 | 58 | 43% | ja, feuert hier nicht | Ringschwingungen 1400–1600; ohne Benzolring im Molekül meldet die Tabelle keine | histidine, abacavir, acetazolamide, aciclovir |
| Halogenaryl (C–F/Cl/Br/I) | 55 | 55 | 100% | nein | Ar–F 1100–1250 stark; Ar–Cl ~1090 | amiloride, amiodarone, amodiaquine, bedaquiline |
| Heteroaromat-NH (Pyrrol/Indol/Imidazol) | 47 | 47 | 100% | nein | N–H 3400–3500 (scharf) | histidine, tryptophan, L-folinic acid, aciclovir |
| Imin/Amidin/Guanidin (C=N, nicht aromatisch) | 33 | 33 | 100% | nein | C=N 1640–1690 | arginine, amiloride, aztreonam, cefixime |
| Sulfonamid | 16 | 16 | 100% | nein | S=O asym. 1330–1370, sym. 1140–1180 | acetazolamide, aztreonam, darunavir, dasabuvir |
| Fluor (aliphatisch, C–F) | 16 | 16 | 100% | nein | C–F 1000–1400, sehr stark | betamethasone, bicalutamide, delamanid, dexamethasone |
| Carbamat | 15 | 15 | 100% | nein | C=O 1690–1740; Tabelle meldet Amid UND Ester | albendazole, atazanavir, capecitabine, daclatasvir |
| β-Lactam | 14 | 14 | 100% | nein | C=O 1760–1780 — deutlich über der Amid-I-Bande | amoxicillin, ampicillin, aztreonam, benzathine benzylpenicillin |
| Alkylchlorid/-bromid/-iodid | 13 | 13 | 100% | nein | C–Cl 600–800, C–Br 500–600 | (RS)-cyclophosphamide, beclomethasone dipropionate, bendamustine, chlorambucil |
| Phosphat/Phosphonat | 9 | 9 | 100% | nein | P=O 1250–1300, P–O 950–1050 | (RS)-cyclophosphamide, fludarabine phosphate, hydroxocobalamin, ifosfamide |
| Sulfonsäure/Sulfat/Sulfonat | 6 | 6 | 100% | nein | S=O 1150–1250, 1030–1060 | atracurium besilate, aztreonam, docusate sodium, mesna |
| Carboxylat | 4 | 4 | 100% | nein | COO⁻ asym. 1550–1610, sym. ~1400 | calcium gluconate, ceftazidime, sodium calcium edetate, sodium lactate |
| Imid | 4 | 4 | 100% | nein | zwei C=O, ~1700 und ~1770 | ethosuximide, nitrofurantoin, phenobarbital, phenytoin |
| Sulfon | 3 | 3 | 100% | nein | S=O 1300–1350 und 1120–1160 | bicalutamide, dapsone, nifurtimox |
| Sulfoxid | 3 | 3 | 100% | nein | S=O ~1050 | omeprazole, pantoprazole, dimethyl sulfoxide |
| Amin sekundär | 27 | 2 | 7% | ja, feuert hier nicht | N–H 3300–3500; die Tabellenregel verlangt sp³- oder Aryl-Nachbarn, Enamin-NH (Dihydropyridin) fällt durch | nifedipine, rifabutin |
| Thiocarbonyl (Thioamid/-harnstoff) | 1 | 1 | 100% | nein | C=S 1050–1250 | ethionamide |
| Nitratester | 1 | 1 | 100% | nein | 1620–1640 und 1270–1290 | isosorbide dinitrate |
| Azid | 1 | 1 | 100% | nein | N₃ asym. ~2100, sehr stark | zidovudine |
| Formaldehyd | 1 | 1 | 100% | nein | C=O ~1745 | formaldehyde |

## Was die Tabelle bei den Lücken stattdessen meldet

Die häufigsten gemeldeten Gruppen in den betroffenen Molekülen — zeigt, ob eine Lücke still bleibt oder eine falsche Bande an ihre Stelle tritt (z. B. β-Lactam → Amid I).

| Gruppe | häufigste gemeldete Gruppen |
|---|---|
| Heteroaromat (Ring-N/O/S) | C–H (aromatic) (55), C–H (alkane, sp³) (43), N–H (primary amine) (25), O–H (alcohol) (19) |
| Halogenaryl (C–F/Cl/Br/I) | C–H (aromatic) (52), C=C (aromatic ring) (49), C–H (alkane, sp³) (49), C=O (amide, band I) (17) |
| Heteroaromat-NH (Pyrrol/Indol/Imidazol) | C–H (aromatic) (47), C–H (alkane, sp³) (37), C=C (aromatic ring) (23), N–H (primary amine) (15) |
| Imin/Amidin/Guanidin (C=N, nicht aromatisch) | C–H (alkane, sp³) (32), C–H (aromatic) (25), C=C (aromatic ring) (21), C=O (amide, band I) (16) |
| Sulfonamid | C–H (aromatic) (15), C=C (aromatic ring) (14), C–H (alkane, sp³) (13), N–H (amide) (8) |
| Fluor (aliphatisch, C–F) | C–H (alkane, sp³) (15), C–H (aromatic) (10), C=C (aromatic ring) (9), O–H (alcohol) (8) |
| Carbamat | C–O (ester) (15), C=O (ester) (15), C–H (alkane, sp³) (15), C=O (amide, band I) (15) |
| β-Lactam | O–H (carboxylic acid) (14), C=O (carboxylic acid) (14), C–H (alkane, sp³) (14), C=O (amide, band I) (14) |
| Alkylchlorid/-bromid/-iodid | C–H (alkane, sp³) (12), C=C (aromatic ring) (4), C–H (aromatic) (4), O–H (alcohol) (3) |
| Phosphat/Phosphonat | C–H (alkane, sp³) (9), C–H (aromatic) (6), O–H (alcohol) (5), C–O (ether) (5) |
| Sulfonsäure/Sulfat/Sulfonat | C–H (alkane, sp³) (6), C–H (aromatic) (4), C=C (aromatic ring) (3), C–O (ester) (2) |
| Carboxylat | C–H (alkane, sp³) (4), O–H (alcohol) (2), O–H (carboxylic acid) (1), N–H (amide) (1) |
| Imid | N–H (amide) (4), C=O (amide, band I) (4), C–H (alkane, sp³) (3), C–H (aromatic) (3) |
| Sulfon | C–H (aromatic) (3), C=C (aromatic ring) (2), C–H (alkane, sp³) (2), N–H (amide) (1) |
| Sulfoxid | C–H (alkane, sp³) (3), C=C (aromatic ring) (2), C–H (aromatic) (2), C–O (ether) (2) |
| Amin sekundär | C–O (ester) (2), C=O (ester) (2), C=C (aromatic ring) (2), C–H (alkane, sp³) (2) |
| Thiocarbonyl (Thioamid/-harnstoff) | C–H (alkane, sp³) (1), C–H (aromatic) (1) |
| Nitratester | C–H (alkane, sp³) (1), C–O (ether) (1) |
| Azid | C–H (alkane, sp³) (1), O–H (alcohol) (1), C–H (aromatic) (1), C–O (ether) (1) |
| Formaldehyd |  |

## Alle Gruppen: Vorkommen und Abdeckung

| Gruppe | diagnostisch | kommt vor in | abgedeckt | Regel(n) in `_IR_TABLE` |
|---|---|---:|---:|---|
| Carbonsäure | ja | 92 | 92 | C=O (carboxylic acid), O–H (carboxylic acid) |
| Carboxylat | ja | 4 | 0 | — keine — |
| Ester (ohne Carbamat/Carbonat) | ja | 52 | 52 | C=O (ester) |
| Keton | ja | 44 | 44 | C=O (ketone) |
| Aldehyd | ja | 7 | 7 | C=O (aldehyde) |
| Formaldehyd | ja | 1 | 0 | — keine — |
| Amid (ohne Harnstoff/Carbamat/Imid) | ja | 84 | 84 | C=O (amide, band I) |
| β-Lactam | ja | 14 | 0 | — keine — |
| Harnstoff | ja | 13 | 13 | C=O (amide, band I) |
| Carbamat | ja | 15 | 0 | — keine — |
| Imid | ja | 4 | 0 | — keine — |
| Säurehalogenid | ja | 1 | 1 | C=O (acid halide) |
| Anhydrid | ja | 1 | 1 | C=O (anhydride) |
| Nitril | ja | 6 | 6 | C≡N (nitrile) |
| Nitro | ja | 10 | 10 | N=O (nitro, antisymmetric) |
| Nitratester | ja | 1 | 0 | — keine — |
| Azid | ja | 1 | 0 | — keine — |
| Sulfonamid | ja | 16 | 0 | — keine — |
| Sulfon | ja | 3 | 0 | — keine — |
| Sulfonsäure/Sulfat/Sulfonat | ja | 6 | 0 | — keine — |
| Sulfoxid | ja | 3 | 0 | — keine — |
| Thiocarbonyl (Thioamid/-harnstoff) | ja | 1 | 0 | — keine — |
| Phosphat/Phosphonat | ja | 9 | 0 | — keine — |
| Thiol | ja | 6 | 6 | S–H (thiol) |
| Thioether | nein | 25 | — | — keine — |
| Alkohol | ja | 135 | 135 | O–H (alcohol) |
| Phenol | ja | 37 | 37 | O–H (phenol) |
| Ether (aliphatisch/aromatisch) | ja | 102 | 102 | C–O (ether) |
| Amin primär | ja | 85 | 85 | N–H (primary amine) |
| Amin sekundär | ja | 27 | 25 | N–H (secondary amine) |
| Arylamin sekundär | ja | 16 | 16 | N–H (secondary amine) |
| Amin tertiär | nein | 78 | — | — keine — |
| Ammonium quartär | nein | 7 | — | — keine — |
| Imin/Amidin/Guanidin (C=N, nicht aromatisch) | ja | 33 | 0 | — keine — |
| Azo | nein | 1 | — | — keine — |
| Heteroaromat-NH (Pyrrol/Indol/Imidazol) | ja | 47 | 0 | — keine — |
| Heteroaromat (Ring-N/O/S) | ja | 134 | 76 | C=C (aromatic ring) |
| Benzolring | ja | 212 | 212 | C=C (aromatic ring) |
| Alken (nicht aromatisch) | ja | 84 | 84 | C=C (alkene) |
| Alkin | ja | 6 | 6 | C≡C (alkyne) |
| Fluor (aliphatisch, C–F) | ja | 16 | 0 | — keine — |
| Halogenaryl (C–F/Cl/Br/I) | ja | 55 | 0 | — keine — |
| Alkylchlorid/-bromid/-iodid | ja | 13 | 0 | — keine — |

## Tabellenregeln, die in keinem der Moleküle feuern

keine

Moleküle, für die außer sp³-C–H gar keine Bande gemeldet wird: 16 ((RS)-cyclophosphamide, calcium, halothane, ifosfamide, miltefosine, nitroprusside, potassium chloride, sodium calcium edetate, carbon tetrachloride, chloroform)
