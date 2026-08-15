# Routing schärfen + Umschalter im Panel

Auftrag Jay, 15.08.2026. Grundlage: Recherchebefund
https://claude.ai/code/artifact/6fa21f2d-6223-4637-90e1-ad4b1cf99ea7

**Kernbefund:** Nicht die Toolzahl schadet, sondern semantische Nähe. Der
Coffein-Fall ist ein unterspezifizierter Prompt, kein Zaun-Problem — dagegen
hilft nur eine erklärte Default-Regel.

## Welle 1 — Beschreibungen und Server-Landkarte

- [ ] `instructions=` am FastMCP-Konstruktor: Bereichskarte + „Do not use for"
- [ ] `generate_molecule`: Default-Regel für den blanken Stoffnamen
- [ ] `lookup`: „what is X" entschärfen, Superlativ streichen
- [ ] Zäune zwischen Zeichnen ↔ Nachschlagen in BEIDE Richtungen
- [ ] Zäune auf Trigger-Bedingungen umstellen (wenn-dann statt „use X")
- [ ] 6 Beschreibungen unter 2 KB (gekürzt wird die Parameter-Doku, nie ein Zaun)

## Welle 2 — Umschalter Struktur ⇄ Daten

- [ ] `DatabasePayload`: `atoms`, `functionalGroups`, `name`, `smiles`
- [ ] `lookup_molecule_data` füllt die Felder aus dem vorhandenen Mol
- [ ] `StructureCanvas` aus `MoleculeView` herauslösen (Hover + Highlights)
- [ ] Segment-Control in beiden Views; „Daten" lädt per `callServerTool` nach
- [ ] Bundle neu bauen, Frische-Test grün

## Welle 3 — Beweise

- [ ] `scripts/handshake.sh`: echter stdio-Handshake gegen den registrierten Command
- [ ] Tool-Snapshots: Name + Beschreibung + Schema als Golden, Diff = rot
- [ ] Prompt→Tool-Eval-Gerüst (promptfoo; `claude plugin eval` ist gesperrt)

## Gate

`./test.sh` grün, Bundle frisch, Handshake bestätigt 20 Tools / 14 Panels.
