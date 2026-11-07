# Kippmessung Schnitt 3 — Stereo-Gegenproben (Stand 07.11.2026, Messbasis 112021f mit Schnitt 2)

Nur gemessen, kein Resolver-Commit. Schalter sind Monkeypatches in `mess.py`.

## Ablauf

Nachmessen: `git worktree add --detach .claude/worktrees/kipp2 112021f` (die Skripte zeigen auf diesen Pfad),
danach `git worktree remove .claude/worktrees/kipp2`.

1. `mess.py record` — ein Live-Lauf mit unverändertem Resolver im Worktree auf `112021f`
   (711 Masse-Eingaben + Holdout PubChem 553 + Holdout OPSIN 131). Jede Quellenantwort → `memo.json`.
2. `mess.py replay` — offline aus dem Memo, je Variante `_pubchem_checked`/`_opsin_checked` ersetzt.
   `replay.json` (2,8 MB) ist nicht eingecheckt; es entsteht aus `memo.json` neu.
3. `auswertung.py` → `ergebnis.json` / `ergebnis.md`. `fixture_check.py` → `fixture_check.json`.

Gates: Treue record↔basis **0 Abweichungen** in allen drei Mengen, **0** Memo-Fehlgriffe.
Basis grün **683** = Lauf 11 (675, fest aus `git show 112021f:…/identitaet-lauf.json`) + 8 neu grün
durch Schnitt 1/2, nichts verloren.

## Regeln

- **A**: `_pubchem_checked` tauscht auch bei gleichem Gerüst, wenn Block 1+2 des Stammmoleküls abweichen
  — nur ohne Stereo-/D-/L-Präfix im Namen, Variante nicht mehr Komponenten.
- **A>=** (Chef 07.11.): A, nur wenn die Variante mindestens so viele definierte Stereoelemente hat.
- **A⊇** (Zusatzspalte): A, nur wenn die Variante nichts verliert und nichts widerspricht
  (flach→definiert oder Obermenge).
- **B / B′**: `_opsin_checked` nimmt PubChem bei abweichendem Block 2; B′ nur bei ≥ Stereoelementen.

## Ergebnis (Fixtures wie im Repo)

| Variante | grün gekippt | rot→grün | Holdout PubChem gekippt/behoben/beide falsch | Holdout OPSIN |
|---|---|---|---|---|
| A | 0 | 5 | 5 / 6 / 2 | 0 |
| **A>=** | **0** | **4** | **1 / 6 / 0** | 0 |
| A⊇ | 0 | 2 | 1 / 6 / 0 | 0 |
| B′ | 4 | 3 | 0 | 0 |
| A>=+B′ | 4 | 7 | 1 / 6 / 0 | 0 |

„Definiertere Form“ ist als ≥ gemessen; strikt > würde Isosorbiddinitrat und Vinorelbin
(gleich viele Elemente, Widerspruch) sperren. Benzylpenicillin-Benzathin und Isosorbiddinitrat sind neu gegenüber der
Vortagsmessung, weil die Basis jetzt Schnitt 2 enthält, nicht wegen der Regel.
A>= behält Benzylpenicillin-Benzathin, Isosorbiddinitrat, Naloxon, Vinorelbin; verliert gegenüber A nur
Mefloquin (direkt definiert, Fixture flach — Spiegelfall zu Lincomycin/Prostacyclin, die die Zählregel
schützt). Der eine Holdout-Kipp ist Vareniclin (s. u., Schreibweise, kein anderer Stoff).

## Fixture-Prüfung (`fixture_check.json`, nur Vorschlag — Fixtures unverändert)

| Stoff | Fixture | Befund | Quellen | Vorschlag |
|---|---|---|---|---|
| Nicotin / nicotine | flach | Arzneistoff = (S)-Nicotin | PubChem CID 89594 „Nicotine" (S), ChEMBL3 (S), KEGG D03365 Nicotine (USP) (S), Wikidata Q28086552 „(−)-nicotine"; nur Q12144 flach | → `SNICXCGAKADSCV-JTQLQIEISA-N` |
| Citral / Citral A+B | flach | Gemisch Geranial + Neral, flach richtig | ChEBI 23316 (Definition: Gemisch beider Isomere), Wikidata Q60176530 flach vs. Q410888 = Geranial, PubChem CID 8843 „Citral (cis + trans)" | bleibt; PubChems Name „citral" → CID 638011 (Geranial) ist ein Synonymfehler |
| Lincomycin | definiert | richtig | PubChem 3000540, ChEMBL1447, KEGG D00223 | bleibt |
| Prostacyclin | definiert | richtig | PubChem 5282411, ChEMBL1139, KEGG D00106 | bleibt |
| Vareniclin | flach | flach = definiert: Brückenkopf-Zentren erzwungen, Spiegelbild hat denselben Key (meso, RDKit-Probe) | PubChem 5310966 + ChEMBL1076903 definiert; KEGG D08669 + Wikidata Q411330 flach | beide Keys als richtig zählen |
| Mefloquin | flach | Fixture deckt sich mit PubChem 4046, ChEMBL416956, Wikidata Q736270 (KEGG D04895: relativ definiert) | — | bleibt |

## Mit vorgeschlagenen Fixtures

| Variante | gekippt | behoben | Holdout PubChem gekippt/behoben |
|---|---|---|---|
| A | 0 | 5 | 4 (Lincomycin ×2, Prostacyclin ×2) / 6 |
| **A>=** | **0** | **4** | **0 / 6** |
| A⊇ | 0 | 2 | 0 / 6 |
| B′ | 2 (citral, Citral A+B) | 5 (Penicillamin ×2, Adrenalin, Nicotin ×2) | 0 / 0 |
| A>=+B′ | 2 (citral, Citral A+B) | 9 | 0 / 6 |

B′ bleibt auch mit korrigierten Fixtures nicht kippfrei: die Citral-Kippen sind echt (PubChem-Synonymfehler,
den die Stereo-Zählung für richtig hält).

## Empfehlung

Bauen: **A>=** — 0 Kippen in allen drei Mengen (mit Vareniclin als Schreibweise), 4 + 6 Gewinne.
Getrennt davon: Nicotin-Fixture auf (S) korrigieren (Referenzentscheid) — ehrlicher Preis: Basis grün
683 → 681, weil der Resolver heute flaches Nicotin liefert; nur B′ holt es zurück. B′ nicht bauen, solange der
Citral-Synonymfehler nicht abgefangen ist.
