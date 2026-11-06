# IR-Regelabdeckung — Masse-Evaluation

Stand 2026-11-06 · `uv run python scripts/masse_eval.py ir` · offline, < 10 s

**414 Moleküle** (ein Eintrag je InChIKey aus `tests/identity/stoffe-masse.json`, SMILES aus Wikidata, nicht aus `resolve()` — der Bericht hängt also nicht vom Identitätslauf ab). Je Molekül: 43 eigene SMARTS-Gruppen (unabhängig von `_IR_TABLE` geschrieben, Liste `IR_GRUPPEN` im Skript) gegen die Gruppen, die `spectro.expected_ir_bands` (= `predict_spectrum`) meldet.

**Lücke** = Gruppe mit diagnostischer Bande ist im Molekül, aber keine passende Regel der Tabelle feuert. Gruppen ohne diagnostische Bande (tertiäres Amin, Thioether, Azo, quartäres Ammonium) zählen nie als Lücke. Kuratierte Ergänzungen und begründet offene Klassen: [Quellen](ir-quellen.md).

## Lücken der Tabelle (nach Zahl betroffener Moleküle)

| Gruppe | kommt vor in | ohne passende Bande | Anteil | Regel in `_IR_TABLE`? | erwartete Bande / Ursache | Beispiele |
|---|---:|---:|---:|---|---|---|
| Heteroaromat (Ring-N/O/S) | 134 | 58 | 43% | ja, feuert hier nicht | Ringschwingungen 1400–1600; ohne Benzolring im Molekül meldet die Tabelle keine | histidine, abacavir, acetazolamide, aciclovir |
| Heteroaromat-NH (Pyrrol/Indol/Imidazol) | 47 | 47 | 100% | nein | N–H 3400–3500 (scharf) | histidine, tryptophan, L-folinic acid, aciclovir |
| Carbamat | 15 | 15 | 100% | nein | C=O 1690–1740; Tabelle meldet Amid UND Ester | albendazole, atazanavir, capecitabine, daclatasvir |
| β-Lactam | 14 | 14 | 100% | nein | C=O 1760–1780 — deutlich über der Amid-I-Bande | amoxicillin, ampicillin, aztreonam, benzathine benzylpenicillin |
| Imin/Amidin/Guanidin (C=N, nicht aromatisch) | 33 | 12 | 36% | ja, feuert hier nicht | C=N 1640–1690 nur für einfache Imine/Oxime; Amidine/Guanidine bleiben offen | arginine, chlorhexidine, clozapine, desmopressin |
| Sulfonsäure/Sulfat/Sulfonat | 6 | 6 | 100% | nein | S=O 1150–1250, 1030–1060 | atracurium besilate, aztreonam, docusate sodium, mesna |
| Phosphat/Phosphonat | 9 | 5 | 56% | ja, feuert hier nicht | P=O je Unterklasse 1100–1200 / 1230–1260 / 1200–1275; ionisierte/andere Substitution offen | (RS)-cyclophosphamide, hydroxocobalamin, ifosfamide, miltefosine |
| Carboxylat | 4 | 4 | 100% | nein | COO⁻ asym. 1550–1610, sym. ~1400 | calcium gluconate, ceftazidime, sodium calcium edetate, sodium lactate |
| Imid | 4 | 4 | 100% | nein | zwei C=O, ~1700 und ~1770 | ethosuximide, nitrofurantoin, phenobarbital, phenytoin |
| Sulfonamid | 16 | 1 | 6% | ja, feuert hier nicht | S=O 1335–1370 / 1155–1170 nur R–SO₂–N; Sulfamat bleibt offen | aztreonam |
| Nitratester | 1 | 1 | 100% | nein | 1620–1640 und 1270–1290 | isosorbide dinitrate |
| Formaldehyd | 1 | 1 | 100% | nein | C=O ~1745 | formaldehyde |

## Was die Tabelle bei den Lücken stattdessen meldet

Die häufigsten gemeldeten Gruppen in den betroffenen Molekülen — zeigt, ob eine Lücke still bleibt oder eine falsche Bande an ihre Stelle tritt (z. B. β-Lactam → Amid I).

| Gruppe | häufigste gemeldete Gruppen |
|---|---|
| Heteroaromat (Ring-N/O/S) | C–H (aromatic) (55), C–H (alkane, sp³) (43), N–H (primary amine) (25), O–H (alcohol) (19) |
| Heteroaromat-NH (Pyrrol/Indol/Imidazol) | C–H (aromatic) (47), C–H (alkane, sp³) (37), C=C (aromatic ring) (23), C–O (ether) (15) |
| Carbamat | C=O (amide, band I) (15), C=O (ester) (15), C–H (alkane, sp³) (15), C–H (aromatic) (15) |
| β-Lactam | C=O (amide, band I) (14), C=O (carboxylic acid) (14), C–H (alkane, sp³) (14), O–H (carboxylic acid) (14) |
| Imin/Amidin/Guanidin (C=N, nicht aromatisch) | C–H (alkane, sp³) (12), C–H (aromatic) (9), C=C (aromatic ring) (8), C=O (amide, band I) (3) |
| Sulfonsäure/Sulfat/Sulfonat | C–H (alkane, sp³) (6), C–H (aromatic) (4), C=C (aromatic ring) (3), C=O (amide, band I) (2) |
| Phosphat/Phosphonat | C–H (alkane, sp³) (5), P–O (phosphorus ester) (5), C=C (alkene) (2), C=C (aromatic ring) (2) |
| Carboxylat | C–H (alkane, sp³) (4), O–H (alcohol) (2), C=C (alkene) (1), C=N (imine / oxime) (1) |
| Imid | C=O (amide, band I) (4), N–H (amide) (4), C–H (alkane, sp³) (3), C–H (aromatic) (3) |
| Sulfonamid | C=N (imine / oxime) (1), C=O (amide, band I) (1), C=O (carboxylic acid) (1), C–H (alkane, sp³) (1) |
| Nitratester | C–H (alkane, sp³) (1), C–O (ether) (1) |
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
| Azid | ja | 1 | 1 | N₃ (azide) |
| Sulfonamid | ja | 16 | 15 | S=O (sulfonamide, antisymmetric), S=O (sulfonamide, symmetric) |
| Sulfon | ja | 3 | 3 | S=O (sulfone, antisymmetric), S=O (sulfone, symmetric) |
| Sulfonsäure/Sulfat/Sulfonat | ja | 6 | 0 | — keine — |
| Sulfoxid | ja | 3 | 3 | S=O (sulfoxide) |
| Thiocarbonyl (Thioamid/-harnstoff) | ja | 1 | 1 | C=S (thiocarbonyl) |
| Phosphat/Phosphonat | ja | 9 | 4 | P=O (phosphate), P=O (phosphonate), P=O (phosphoramide) |
| Thiol | ja | 6 | 6 | S–H (thiol) |
| Thioether | nein | 25 | — | — keine — |
| Alkohol | ja | 135 | 135 | O–H (alcohol) |
| Phenol | ja | 37 | 37 | O–H (phenol) |
| Ether (aliphatisch/aromatisch) | ja | 102 | 102 | C–O (ether) |
| Amin primär | ja | 85 | 85 | N–H (primary amine) |
| Amin sekundär | ja | 27 | 27 | N–H (secondary amine) |
| Arylamin sekundär | ja | 16 | 16 | N–H (secondary amine) |
| Amin tertiär | nein | 78 | — | — keine — |
| Ammonium quartär | nein | 7 | — | — keine — |
| Imin/Amidin/Guanidin (C=N, nicht aromatisch) | ja | 33 | 21 | C=N (imine / oxime) |
| Azo | nein | 1 | — | — keine — |
| Heteroaromat-NH (Pyrrol/Indol/Imidazol) | ja | 47 | 0 | — keine — |
| Heteroaromat (Ring-N/O/S) | ja | 134 | 76 | C=C (aromatic ring) |
| Benzolring | ja | 212 | 212 | C=C (aromatic ring) |
| Alken (nicht aromatisch) | ja | 84 | 84 | C=C (alkene) |
| Alkin | ja | 6 | 6 | C≡C (alkyne) |
| Fluor (aliphatisch, C–F) | ja | 16 | 16 | C–F (fluoro compound) |
| Halogenaryl (C–F/Cl/Br/I) | ja | 55 | 55 | C–F (fluoro compound), C–Cl (chloro compound), C–Br (bromo compound), C–I (iodo compound) |
| Alkylchlorid/-bromid/-iodid | ja | 13 | 13 | C–Cl (chloro compound), C–Br (bromo compound), C–I (iodo compound) |

## Tabellenregeln, die in keinem der Moleküle feuern

keine

Moleküle, für die außer sp³-C–H gar keine Bande gemeldet wird: 8 (calcium, nitroprusside, potassium chloride, sodium calcium edetate, cyclohexane, formaldehyde, hexane, triethylamine)
