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
