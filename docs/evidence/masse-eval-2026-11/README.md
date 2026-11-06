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
(~0,5 s) statt 0,0 s; offline bleibt er so schnell wie vorher.

**Überanpassung geprüft (Holdout).** `holdout_opsin_check.py` nimmt Wikidata-Arzneistoffe mit
ATC-Code (≥ 15 Wikipedia-Sprachen, genau ein InChIKey), die in keiner der beiden Listen stehen:
1119 Stoffe, davon 131 mit OPSIN-Treffer. Ergebnis 06.11.: **116 gleich und richtig · 10 neu behoben**
(u. a. chlorobutanol, diethyltoluamide, aminocaproic acid, aminophenazone, magnesium oxide) ·
**1 gekippt** · 4 vorher wie nachher falsch (Salze/Komplexe: aluminium chlorohydrate, sodium chlorite,
iron(II) gluconate, magnesium citrate). Gekippt ist **calcium silicate**: OPSIN baut Ca₂SiO₄
(= Wikidata), PubChems Record zum Namen ist Ca(H₃SiO₄)₂ — anorganische Stöchiometrie, die Quellen
modellieren verschieden. Bewusst nicht wegjustiert (eine Regel für einen Holdout-Fall wäre die
Überanpassung, die der Holdout messen soll).

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
