# Masse-Evaluation 2026-11

Drei Läufe über viele Stoffe bzw. Aufgaben, jeder mit Erwartungswerten aus einer Quelle
**außerhalb** des geprüften Codes. Alle stehen außerhalb des Auto-Gates (`./test.sh`).

| Lauf | misst | Befehl | Dauer | Netz |
|---|---|---|---|---|
| Identität | Name → richtiger Stoff (InChIKey) über die echte Kaskade OPSIN → PubChem → NCI | `uv run python scripts/identitaet.py --datei tests/identity/stoffe-masse.json --protokoll docs/evidence/masse-eval-2026-11/identitaet-lauf.json`, dann `uv run python scripts/masse_eval.py identitaet` | ca. 30–60 min (deutsche Namen ~7 s, OPSIN-Treffer < 0,1 s) | ja (PubChem, NCI; ≤ 5 Anfragen/s durch 0,3 s Pause + 10 s Backoff) |
| IR-Abdeckung | Welche funktionellen Gruppen keine Regel in `spectro._IR_TABLE` treffen | `uv run python scripts/masse_eval.py ir` | < 10 s | nein |
| pH | `ph_calc` und die Kopfzeile von `calculate_ph` gegen 51 Aufgaben | `uv run python scripts/masse_eval.py ph` | < 5 s | nein |

Berichte: [`identitaet.md`](identitaet.md), [`ir-abdeckung.md`](ir-abdeckung.md), [`ph.md`](ph.md).
Rohprotokoll des Identitätslaufs: `identitaet-lauf.json`.

## Lauf 1 → Fix → Lauf 2 (Identität, 04./05.11.2026)

| | Lauf 1 (vor NCI-Fix) | Lauf 2 (mit `cc13e47`) |
|---|---|---|
| Resolver | Prozessstart 04.11. 23:19:34, alter Code im Speicher; Fix-Commit 05.11. 00:04:42 | Repo-Stand mit Fix (`inspect.getsource` geprüft) |
| Ergebnis | 591 grün · 80 gelb · 40 rot | 591 grün · 1 gelb · 119 rot |
| Laufzeit | 62 min (Backoff 10 s + Wiederholung je „Quelle weg“) | 37 min |
| Dateien | `identitaet-lauf-1-vor-nci-fix.{json,md}` | `identitaet-lauf-2-vor-de-namen.{json,md}` |

Übergänge je Eingabe: 591 grün→grün, 40 rot→rot, 1 gelb→gelb (paritaprevir, Referenz `unsicher`),
**79 gelb→rot**. Diese 79 waren „Quelle weg (partial)“: NCI CIR meldet einen unbekannten Namen als
HTTP 500 mit Body „Page not found“, der Resolver hielt das für einen Quellenausfall und riet „retry“.
Seit dem Fix heißt es ehrlich `not_found` — der Lauf zählt das als rot, weil die Quelle den Stoff führt.
Der Fix ändert die Nutzer-Meldung, nicht die Auflösung: 75 der 80 `not_found` sind deutsche
Wikidata-Labels ohne PubChem-Synonym (5 englische mit Präfix oder Sonderzeichen: (RS)-ketamine, (RS)-methadone, (S)-(−)-timolol, β-lactulose, nitroprusside); 74 der 77 betroffenen Stoffe
sind über ihre englische/INN-Eingabe grün. Befund für später: deutsche Trivialnamen brauchen einen
eigenen Weg (de.wikipedia-Weiterleitung oder Endungsregeln -on/-one, -in/-ine, -säure/-ic acid).
→ umgesetzt als Endungsregeln, siehe nächster Abschnitt.

## Lauf 2 → Fix → Lauf 3 (Identität, 05.11.2026)

Fix `abee1a5`: `chemdraw_tool/de_names.py` schreibt einen deutschen Trivialnamen ins Englische um
(INN-Endungen -on/-id/-in/-at/-im/-an, -säure → „ic acid“ samt deutscher Stämme, Kation vorn/Anion
hinten, Racemat-Präfix, griechische Buchstaben). Der Resolver fragt PubChem damit **erst nach allen
anderen Quellen** — ein in Lauf 2 aufgelöster Name nimmt denselben Weg.

| | Lauf 2 | Lauf 3 (mit `abee1a5`) |
|---|---|---|
| Ergebnis | 591 grün · 1 gelb · 119 rot | **658 grün · 1 gelb · 52 rot** |
| nicht aufgelöst | 80 (de 75 · en 5) | 9 (de 7 · en 2) |
| Laufzeit | 37 min | 12 min (Median 0,5 s; PubChem antwortete schneller, kein Codeeffekt belegt) |
| Dateien | `identitaet-lauf-2-vor-de-namen.{json,md}` | `identitaet-lauf.json`, `identitaet.md` |

Übergänge je Eingabe: 591 grün→grün (**kein grüner Fall gekippt**), 67 rot→grün, 52 rot→rot,
1 gelb→gelb. Von den 52 roten wechselten 4 von „nicht aufgelöst“ zu „gefunden, aber abweichend“:
L-Scopolamin und Pantothensäure (Stereo, wie ihre englischen Eingaben), Docusat (freie Säure statt
Na-Salz) und β-Lactulose (gleiche Formel, andere Ringform) — gedeutet in `identitaet.md`, kein falscher Stoff.

**Überanpassung geprüft (Holdout).** Die Regeln wurden an genau den 80 Fällen eingestellt, an denen
Lauf 3 misst. Darum zusätzlich `holdout_de_namen.py`: die Regeln über die 177 deutschen Eingaben, die
schon in Lauf 2 direkt grün waren (nie zum Einstellen benutzt), Variante an PubChem, InChIKey gegen
Wikidata. Ergebnis 05.11.: 133 mit Variante → **121 gleich · 1 Stereo (Nicotin → Nicotine) ·
0 anderer Stoff** · 11 unbekannt; 44 ohne Variante. Offen: das Ergebnis sagt dem Nutzer nicht, dass
über die englische Schreibweise gefunden wurde.

## Lauf 3 → Fix → Lauf 4 (Identität, 06.11.2026)

Befund 2: OPSIN gewann vor PubChem und zerlegte Trivialnamen systematisch — „tropic-amide“
(Tropasäureamid), „methyl-dopa“ (N-Methyl-DOPA), „chloro-xylen-ol“ (nicht-aromatischer Ring),
„methyl-thioninium“ (Thiepinium-Ring). **Messung vor dem Fix** über alle 233 OPSIN-Treffer aus
`stoffe-masse.json` und `stoffe.json`: 226 richtiges Gerüst, 7 falsch (davon fumaric acid ein
Referenzfehler). Ein Trennmerkmal im Namen gibt es nicht — 225 der 233 Treffer tragen keine Ziffer,
darunter alle Fehlgriffe und 218 richtige. Gegenprobe PubChem: Gerüst uneinig bei 7, PubChem richtig
bei 6; der siebte ist **Glycin** (PubChems deutsches Synonym zeigt auf den Fotoentwickler
N-(4-Hydroxyphenyl)glycin, OPSIN hat recht). Tiebreak gemessen an allen 7: PubChems Synonymliste
der OPSIN-Struktur trennt nicht (Glycine führt „Glycin“ nicht), die englische Schreibweise
(`english_variant`: Glycin → Glycine) trennt 7/7.

Fix `41da7c4` (`_opsin_checked` in `chemdraw_tool/resolver.py`): Name mit Lokanten (Ziffer, Klammer,
`N,N-`/`O-`/`o-`/`m-`/`p-`) → OPSIN offline wie bisher, nie ins Netz. Sonst PubChem gegenfragen; nur
ein anderes Gerüst (erster InChIKey-Block) zählt; bestätigt die englische Schreibweise OPSIN, bleibt
OPSIN; sonst gewinnt PubChems Record. Kennt PubChem den Namen nicht oder ist offline → OPSIN.

| | Lauf 3 | Lauf 4 (mit `41da7c4`) |
|---|---|---|
| Ergebnis | 658 grün · 1 gelb · 52 rot | **664 grün · 1 gelb · 46 rot** |
| rot „skelett“ / „salz“ | 17 / 3 | 12 / 2 |
| Laufzeit | 12 min, Median 0,51 s | 13 min, Median 0,54 s |
| Median der 222 OPSIN-Eingaben | 0,0 s (offline) | **0,5 s** (ein PubChem-Aufruf mehr) |
| Dateien | `identitaet-lauf-3-vor-opsin-check.{json,md}` | `identitaet-lauf.json`, `identitaet.md` |

Übergänge: 658 grün→grün (**kein grüner Fall gekippt**), 6 rot→grün (chloroxylenol, methyldopa,
methylthioninium chloride, sodium calcium edetate, tropicamide, Tropicamid), 46 rot→rot. Der Preis
ist die Latenz: ein Trivialname, den OPSIN kennt („ethanol“), kostet jetzt einen PubChem-Aufruf
(~0,5 s) statt 0,0 s. ~~Offline bleibt er so schnell wie vorher~~ — falsch, korrigiert in § Lauf 4 → Fix → Lauf 5.

**Überanpassung geprüft (Holdout).** `holdout_opsin_check.py` nimmt Wikidata-Arzneistoffe mit
ATC-Code (≥ 15 Wikipedia-Sprachen, genau ein InChIKey), die in keiner der beiden Listen stehen:
1119 Stoffe, davon 131 mit OPSIN-Treffer. Ergebnis 06.11.: **116 gleich und richtig · 10 neu behoben**
(u. a. chlorobutanol, diethyltoluamide, aminocaproic acid, aminophenazone, magnesium oxide) ·
**1 gekippt** · 4 vorher wie nachher falsch (Salze/Komplexe: aluminium chlorohydrate, sodium chlorite,
iron(II) gluconate, magnesium citrate). Gekippt ist **calcium silicate**: OPSIN baut Ca₂SiO₄
(= Wikidata), PubChems Record zum Namen ist Ca(H₃SiO₄)₂ — anorganische Stöchiometrie, die Quellen
modellieren verschieden. Bewusst nicht wegjustiert (eine Regel für einen Holdout-Fall wäre die
Überanpassung, die der Holdout messen soll). *Nachtrag: Codex' Kreuzabnahme fand dahinter ein Muster
(Salze), behoben in § Lauf 4 → Fix → Lauf 5.*

## Lauf 4 → Fix → Lauf 5 (Identität, Salze, 06.11.2026)

Codex-Kreuzabnahme (Faden `20261106-105531-abnahme-befund-2`, Verdikt NACHBESSERN): die Gegenprüfung
übernahm PubChem bei anderem Gerüst ohne Salzprüfung — `resolve_name('sodium phosphate')` lieferte das
Anion `[O-]P(=O)([O-])[O-].[Na+]` (Ladung −2) statt Na₃PO₄; Silikate kippten in der Stöchiometrie.
**Messung** an 22 Fällen (Codex' 14 Salze + Silikate/MgO + die 6 Gewinne aus Lauf 4 + Glycin): jede
Salz-Kippe war **kohlenstofffrei**, jeder Gewinn **organisch**. Startpunkt „geladene PubChem-Antwort →
OPSIN“ gemessen und **verworfen**: deckt nichts über die Kohlenstoffregel hinaus ab und kippt im Holdout
`diiodo-L-tyrosine` (PubChem: richtiges Gerüst als Anion; OPSIN: N,N-Diiod) zurück auf den falschen Stoff.

Fix `038ace4`: OPSIN-Treffer ohne Kohlenstoff → OPSIN, **kein Netzaufruf** (Zusammensetzung aus dem
Namen, wie vor Befund 2). Kein Name ist verdrahtet.

| | Lauf 4 | Lauf 5 (mit `038ace4`) |
|---|---|---|
| Ergebnis | 664 grün · 1 gelb · 46 rot | **664 grün · 1 gelb · 46 rot**, je Eingabe identisch (auch der erhaltene Schlüssel) |
| Laufzeit | 13 min, Median 0,54 s | 14 min, Median 0,61 s (Netzschwankung; kein Codepfad wurde langsamer) |
| Dateien | `identitaet-lauf-4-vor-salzregel.{json,md}` | `identitaet-lauf.json`, `identitaet.md` |

**Regressionstabelle** (`resolve_name` live, 06.11.; „Quelle“ = wessen Antwort zurückkommt):

| Name | Formel | Ladung | InChIKey | Quelle |
|---|---|---:|---|---|
| sodium phosphate | Na3O4P | 0 | `RYFMWSXOAZQYPI-UHFFFAOYSA-K` | OPSIN |
| trisodium phosphate | Na3O4P | 0 | `RYFMWSXOAZQYPI-UHFFFAOYSA-K` | OPSIN |
| calcium silicate | Ca2O4Si | 0 | `JHLNERQLKQQLRZ-UHFFFAOYSA-N` | OPSIN |
| sodium silicate | Na4O4Si | 0 | `POWFTOSLLWLEBN-UHFFFAOYSA-N` | OPSIN |
| potassium silicate | K4O4Si | 0 | `RLQWHDODQVOVKU-UHFFFAOYSA-N` | OPSIN |
| magnesium silicate | Mg2O4Si | 0 | `HCWCAKKEBCNQJP-UHFFFAOYSA-N` | OPSIN |
| magnesium oxide | MgO | 0 | `AXZKOIWUVFPNLO-UHFFFAOYSA-N` | OPSIN |
| calcium phosphate | Ca3O8P2 | 0 | `QORWJWZARLRLPR-UHFFFAOYSA-H` | OPSIN |
| magnesium phosphate | Mg3O8P2 | 0 | `GVALZJMUIHGIMD-UHFFFAOYSA-H` | OPSIN |
| sodium carbonate | CNa2O3 | 0 | `CDBYLPFSWZWCQE-UHFFFAOYSA-L` | OPSIN |
| calcium carbonate | CCaO3 | 0 | `VTYYLEPIZMXCLO-UHFFFAOYSA-L` | OPSIN |
| sodium chlorite | ClNaO2 | 0 | `WEKMZMIIYLFEIJ-UHFFFAOYSA-N` | OPSIN |
| calcium sulfate | CaO4S | 0 | `OSGAYBCDTDRGGQ-UHFFFAOYSA-L` | OPSIN |
| aluminium sulfate | Al2O12S3 | 0 | `DIZPMCHEQGEION-UHFFFAOYSA-H` | OPSIN |
| calcium sulfite | CaO3S | 0 | `GBAOBIBJACZTNA-UHFFFAOYSA-L` | OPSIN |
| chloroxylenol | C8H9ClO | 0 | `OSDLLIBGSJNGJE-UHFFFAOYSA-N` | PubChem |
| methyldopa | C10H13NO4 | 0 | `CJCSPKMFHVPWAR-JTQLQIEISA-N` | PubChem |
| methylthioninium chloride | C16H18ClN3S | 0 | `CXKWCBBOMKCUKX-UHFFFAOYSA-M` | PubChem |
| sodium calcium edetate | C10H12CaN2Na2O8 | 0 | `SHWNNYZBHZIQQV-UHFFFAOYSA-J` | PubChem |
| tropicamide / Tropicamid | C17H20N2O2 | 0 | `BGDKAVGWHJFAGW-UHFFFAOYSA-N` | PubChem |
| Glycin | C2H5NO2 | 0 | `DHMQDGOQFOQNFH-UHFFFAOYSA-N` | OPSIN (Tiebreak) |

Carbonate (C-haltig) erreichen die Gegenprüfung, PubChem bestätigt dort das Gerüst → OPSIN bleibt.

**Holdout neu** (`holdout_opsin_check.py`, Einzelfälle in `holdout_opsin_check.json`): 1119 ATC-Stoffe,
131 OPSIN-Treffer → **117 gleich und richtig · 9 neu behoben · 0 gekippt** · 5 vorher wie nachher
abweichend. calcium silicate ist wieder Ca₂SiO₄ (= Wikidata, PubChem CID 14941). **magnesium oxide**
war in Lauf 4 als „behoben“ gezählt: beide Antworten sind MgO, nur die Schreibweise unterscheidet sich
(`[Mg+2].[O-2]` vs. Wikidatas `O=[Mg]`) — kein Stoffwechsel, also weder Gewinn noch Verlust. Neu behoben
ist diiodo-L-tyrosine (Gerüst richtig, PubChem liefert das Anion).

**Offline-Latenz, korrigiert.** Der Resolver kennt keinen gemerkten Offline-Zustand; jeder organische
Trivialname, den OPSIN kennt, fragt PubChem einmal (danach greift der Ergebnis-Cache). Gemessen 06.11.
ohne Mock (`_PUBCHEM_URL` umgebogen): **Blackhole-Host 3,0 s** je Name (Connect-Timeout aus
`_TIMEOUT = (3, 10)`), **DNS-Fehler 0,07 s**, Name mit Lokanten oder ohne Kohlenstoff 0,0 s. Vor Befund 2
waren es überall 0,0 s.

### Nachbesserung: Kristallwasser ist ein Formkonflikt (06.11.2026)

Codex-Abnahme #4 fand **potassium citrate**: OPSIN baut das wasserfreie Salz C₆H₅K₃O₇, PubChem
führt unter dem Namen das Monohydrat C₆H₇K₃O₈ (CID 2735208); die Gegenprüfung wertete das als
Gerüstkorrektur und schaltete still um. Vorgabe des Orchestrators: ein Formkonflikt (gleiche organische
Grundstruktur, nur Wasser/Gegenionen/Ladung anders) behält OPSIN. Vorab gemessen über **301 OPSIN-Treffer**
mit Kohlenstoff ohne Lokant (alle Lauf-5-Eingaben, Holdout, Codex' Gegenproben plus Hydratnamen), drei Regeln:

| Regel | Vergleich | weicht von heute ab bei | Ergebnis |
|---|---|---|---|
| R0 (bisher) | 1. InChIKey-Block der ganzen SMILES | — | potassium citrate → Monohydrat |
| **R1 (gebaut)** | dasselbe ohne Wasser-Komponenten | nur potassium citrate | wasserfrei ✓, sonst gleich |
| R2 (Vorschlag) | größte organische Komponente | potassium citrate, **sodium calcium edetate, gold monosodium thiomalate** | kippt zwei Gewinne |

R2 widerlegt den Teil „Gegenionen“: Bei Edetat baut OPSIN NaCa-EDTA (eine Carbonsäure protoniert),
richtig ist Na₂Ca (Wikidata SHWNNYZBHZIQQV); bei Goldthiomalat baut OPSIN ein Au³⁺-Dimer, richtig ist
Au⁺/Na⁺ (LTEMOXGFFHXNNS). Dort entscheidet die Gegenionen-Zusammensetzung über den Stoff, PubChem hat
recht. Darum zieht `_skeleton` nur Wasser ab. Mutation R2 statt R1 → 2 Tests rot (genau diese beiden).

Live (ohne Mock): potassium citrate C₆H₅K₃O₇ QEEAPRPFLLJWCF · potassium citrate monohydrate C₆H₇K₃O₈
PJAHUDTUZRZBKM · tripotassium citrate C₆H₅K₃O₇; Edetat, Goldthiomalat, diiodo-L-tyrosine, die Lauf-4-Gewinne,
Glycin, sodium phosphate und 14 organische Salze (Citrate, Acetate, Tartrat, Lactat, Oxalat, Bicarbonat)
unverändert. **Kein Lauf 6:** R1 ändert eine Entscheidung nur bei einer Wasser-Komponente; unter allen
Lauf-5-Eingaben gibt es keine solche Abweichung (Messung oben). Holdout neu: 117 gleich · 9 behoben ·
**0 gekippt** · 5 beide abweichend, alle 131 Einzelfälle identisch zum vorigen Stand.

## Lauf 5 → Fix → Lauf 6 (PubChem-Synonymfehler, Befund 3, 06.11.2026)

**Diagnose.** Beide gemeldeten Fälle sind **ein einziger CID** mit verirrtem Depositor-Synonym, kein
Mehrfachtreffer und keine Stereo-Frage (`/compound/name/<n>/cids/JSON`):

| Eingabe | CIDs | Record | Synonyme | richtig wäre |
|---|---|---|---:|---|
| (−)-Ephedrin | `[104213]` | 1-Bromo-3-methyl-5-nitrobenzene, C₇H₆BrNO₂ — nur `(-)-ephedrin` passt | 35 | „Ephedrin“/„(−)-ephedrine“ → CID 9294 (136 Synonyme) |
| Risperidon | `[44402564]` (auch `name_type=word`) | Dihydro-Analogon C₂₃H₂₉FN₄O₂, Titel „Risperidon“ | 5 | „risperidone“ → CID 5073 (282 Synonyme) |

Dieselbe Klasse wie Glycin in Befund 2 (deutsches Synonym → falscher Record), nur schweigt hier OPSIN
und der PubChem-Direkttreffer war unangefochten. Wikidata/ChEMBL zur Laufzeit war nicht nötig: die
englische Schreibweise beim selben Dienst reicht.

**Messung** (alle 711 Eingaben; Variante = `english_variant` ohne Stereo-Klammerpräfix `(−)/(+)/(S)/(RS)/(E)`):
139 nehmen den PubChem-direkt-Weg und haben eine Variante; Name und Variante uneinig bei 5, **die Variante
richtig bei 4, der Originalname bei 0** (rifabutin: beide falsch). Holdout (`holdout_pubchem_check.py`,
Wikidata-ATC-Stoffe mit englischem und deutschem Label, nicht in den Listen; 2145 Labels, **553 im
Geltungsbereich**) trennte zwei Klassen:

| Klasse | Fälle | Stammmolekül gleich? |
|---|---|---|
| Synonymfehler (anderer Stoff) | (−)-Ephedrin, Risperidon, rifabutin · Holdout: Cinnarizin (→ Clofibrat-Ester), Entacapon (→ Aldehyd-Vorstufe), Clorazepat | nein |
| Salzform (Gegenion/Protonierung) | Bendamustin (direkt HCl), Hydroxycobalamin · Holdout: Centrophenoxin (Variante HCl), Phenelzin (direkt Sulfat), Carboplatin/carboplatin | ja |

| Regel | Lauf 6 | Holdout (553) |
|---|---|---|
| R1: Variante gewinnt bei anderem Gerüst inkl. Gegenionen (`_skeleton`) | 668 grün, +4 | 6 behoben · **1 gekippt** (Centrophenoxin → HCl-Salz) — **verworfen** |
| **R2 (gebaut): Variante gewinnt nur bei anderem Stammmolekül** (`_parent_skeleton`, größte organische Komponente) | **666 grün, +2** | **3 behoben · 0 gekippt** · 536 gleich richtig · 14 beide falsch |

R1 kippte Salzformen in beide Richtungen, je nachdem, welche Form der Depositor der Variante hinterlegt
hat — Zufall, kein Regelgewinn. Fix `_pubchem_checked` + `_parent_skeleton` in `chemdraw_tool/resolver.py`:
nach einem PubChem-Direkttreffer einmal die Variante fragen; anderes Stammmolekül → Variante; gleiches,
unbekannt oder Netz weg → Direkttreffer. `_skeleton` (OPSIN-Gegenprüfung) bleibt unverändert, dort
tragen Gegenionen Information (Edetat, Goldthiomalat). Kein Name verdrahtet.

| | Lauf 5 | Lauf 6 (mit R2) |
|---|---|---|
| Ergebnis | 664 grün · 1 gelb · 46 rot | **666 grün · 1 gelb · 44 rot** |
| Übergänge | — | 664 grün→grün (**kein grüner Fall gekippt**), 2 rot→grün ((−)-Ephedrin, Risperidon), 44 rot→rot |
| Laufzeit | 14 min, Median 0,61 s | 16 min, Median 0,73 s (R1-Lauf derselben Codepfade: 0,65 s — Netzschwankung plus ein Aufruf) |
| Dateien | `identitaet-lauf-5-vor-befund-3.{json,md}` | `identitaet-lauf.json`, `identitaet.md` |

Lauf 6 lief gegen die Fixture **vor Befund 4** (Stand `8978be7`; `530e9a9` mit den Referenzkorrekturen
landete während des Laufs), damit nur Befund 3 den Unterschied macht. `identitaet.md` ist gegen dieselbe
Fixture erzeugt.

**Preis.** Jeder PubChem-Direkttreffer mit Variante kostet einen Aufruf mehr (139 von 711 Eingaben),
**auch englische -in-Namen** („Aspirin“ fragt „Aspirine“) — `english_variant` kennt die Sprache der
Eingabe nicht. Danach greift der Ergebnis-Cache. Offline unverändert: ohne Direkttreffer keine Variantenprobe.

**Offen:** rifabutin bleibt rot (beide Formen falsch, jetzt anderer Schlüssel); Bendamustin bleibt rot
als Salzform („INN ohne Salzwort → PubChem liefert das Hydrochlorid“, Vorschlag für einen eigenen Befund);
`(S)-(−)-timolol` bleibt `not_found` — die Präfixregel greift nur nach einem Direkttreffer, der
Rückfallpfad über `english_variant` ist unverändert.

## Woher die Erwartung kommt

- **Stoffliste** `tests/identity/stoffe-masse.json` — 711 Eingaben für 414 Stoffe. Auswahl:
  alle Wikidata-Objekte mit Rolle „WHO essential medicines" (P2868 = Q35456) und genau einem
  InChIKey, dazu eine eigene Liste von Lehrbuch-Grundstoffen (Aminosäuren, Lösungsmittel,
  Säuren/Basen, Zucker, Vitamine, Naturstoffe; `LEHRBUCH` in `scripts/masse_eval.py`).
  Erwartungs-InChIKey = Wikidata P235 (https://query.wikidata.org/sparql), gegengeprüft gegen
  ChEMBL (https://www.ebi.ac.uk/chembl/api/data/molecule): 691 von 711 Eingaben führt ChEMBL
  unter genau diesem Schlüssel, 6 sind `unsicher` (ChEMBL widerspricht → nie rot).
  Eingaben je Stoff: INN (P2275), englisches Label, deutsches Label (= de.wikipedia).
  Verworfen und begründet im Feld `verworfen`: Kombinationspräparate, Objekte mit mehreren
  InChIKeys (Referenz selbst mehrdeutig), anorganische Stoffe/Metallkomplexe.
  Neu bauen: `uv run python scripts/masse_eval.py liste` (~3 min, Wikidata ist langsam).
  Die kuratierte `stoffe.json` bleibt unverändert und der Standard von `identitaet.py`.
- **IR**: eigene SMARTS-Liste (`IR_GRUPPEN`, 43 Gruppen, mit „hat diagnostische Bande ja/nein"),
  angewandt auf die Wikidata-SMILES — nicht auf `resolve()`, damit der Bericht nicht vom
  Identitätslauf abhängt.
- **pH** `tests/identity/ph-aufgaben.json` — 51 Aufgaben. Referenz = sympy, Ladungsbilanz als
  Polynom in [H⁺], einzige positive reelle Wurzel. Unabhängig in Formulierung, Methode und Code,
  nicht in der Physik (es gibt nur eine Ladungsbilanz). 23 Aufgaben tragen zusätzlich einen
  Lehrbuch-Ankerwert, den die Referenz auf ±0,02 treffen muss. Neu rechnen:
  `uv run --with sympy python scripts/masse_eval.py ph-referenz` (sympy ist keine Projektabhängigkeit).

## Grenzen

- Misst **Identität, Regellücken und Zahlen** — nicht Bildqualität, Layout, Panel oder welche
  Tool-Wahl das Modell trifft (dafür `evals/tool-routing`).
- Identität: Wikidata-Labels sind nicht immer das, was Studierende tippen; deutsche Labels
  decken Trivialnamen nur teilweise ab. Ein Rot der Art `stereo`/`ladung` ist oft eine Frage,
  welche Form ein Name meint (Racemat, Salz), nicht ein falscher Stoff — `identitaet.md` trennt das.
- IR: „Lücke" heißt, keine Regel feuert; ob eine gefeuerte Regel den richtigen Bereich nennt,
  prüft der Lauf nur dort, wo die eigene Liste eine bessere Gruppe kennt (β-Lactam, Carbamat).
- pH: ideale Lösung (Aktivität = Konzentration), pKw = 14, 25 °C — wie `ph_calc` selbst.
