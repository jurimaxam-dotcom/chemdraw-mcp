# Routing schärfen + Umschalter im Panel

Auftrag Jay, 15.08.2026. Grundlage: Recherchebefund
https://claude.ai/code/artifact/6fa21f2d-6223-4637-90e1-ad4b1cf99ea7

**Kernbefund:** Nicht die Toolzahl schadet, sondern semantische Nähe. Der
Coffein-Fall ist ein unterspezifizierter Prompt, kein Zaun-Problem — dagegen
hilft nur eine erklärte Default-Regel.

## Welle 1 — Beschreibungen und Server-Landkarte (20ebf06)

- [x] `instructions=` am FastMCP-Konstruktor: Bereichskarte + „Do not use for"
- [x] `generate_molecule`: Default-Regel für den blanken Stoffnamen
- [x] `lookup`: „what is X" entschärfen, Superlativ streichen
- [x] Zäune zwischen Zeichnen ↔ Nachschlagen in BEIDE Richtungen
- [x] Zäune auf Trigger-Bedingungen umstellen (wenn-dann statt „use X")
- [x] 6 Beschreibungen unter 2 KB — Beschreibungen gesamt 31.683 → 27.583 B

## Welle 2 — Umschalter Struktur ⇄ Daten

- [x] `DatabasePayload`: `atoms`, `functionalGroups`, `name`, `smiles` (d06a2f6)
- [x] `lookup_molecule_data` füllt die Felder aus dem vorhandenen Mol (d06a2f6)
- [x] `StructureCanvas` aus `MoleculeView` herauslösen (af9a656) — plus
      `SourceList`, damit das Datenblatt nicht doppelt existiert
- [x] Segment-Control in beiden Views (af9a656); „Struktur" lokal, „Daten"
      per `callServerTool`, einmal geholt und gecacht
- [x] Bundle neu gebaut, Frische-Test grün
- [x] Nacharbeit (9f9d898): Reiter auf Englisch (Projektkonvention), und der
      Rückwechsel während des Ladens gewinnt gegen die eintreffende Antwort.
      Der Test dafür war erst grün — das Auflösen lief außerhalb von `act()`.

## Welle 3 — Beweise

- [x] `scripts/handshake.sh` (adaaea1) — grün gefahren: 20 Tools, 14 mit Panel.
      Befund: `--cli <cmd> -- --method …`, der Inspector trennt an `--`;
      ohne das verschluckt uv die Optionen.
- [x] Tool-Snapshots (adaaea1) — Name + Beschreibung + Schema als Golden,
      `UPDATE_TOOLSNAPS=1` segnet bewusst neu; rot gesehen in drei Varianten
      (fehlend, abweichend, verwaist)
- [x] Prompt→Tool-Fallsammlung (6393ca5) — 21 Fälle, runner-unabhängig;
      `tests/test_eval_cases.py` hält sie ohne Netz mit der Toolliste synchron

## Offen / bewusst nicht

- **Eval-Lauf** braucht `ANTHROPIC_API_KEY` (nicht gesetzt). `claude plugin
  eval` wäre die bessere Wahl, ist aber early-access-gesperrt (CLI 2.1.233).
- **Umbenennung nach Bereichs-Präfix** (`generate_` deckt zwei Bereiche) —
  wäre inhaltlich richtig, ist aber ein Breaking Change gegen die auf PyPI
  liegende 0.3.0 und bräuchte eine Alias-Schicht.

## Gate — abgeschlossen 15.08.2026

```
./test.sh              → 948 passed, 16 skipped · Bundle frisch · Exit 0
./scripts/handshake.sh → 20 Tools, 14 mit Panel (nach Desktop-Neustart)
```

Claude Desktop wurde nach den Server-Änderungen neu gestartet; der Handshake
gegen den registrierten absoluten Command ist der Beweis, nicht die Annahme.
