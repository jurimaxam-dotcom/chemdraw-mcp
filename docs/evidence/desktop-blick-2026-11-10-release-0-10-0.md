# Desktop-Blick nach Release 0.10.0 — 10.11.2026

**4/4 Toolwahlen richtig, 4/4 Panels sichtbar. Offen: Drehen des Lysozym-Cartoons per Maus in Desktop nicht bestätigt.**

Gemessen von Codex (Tisch-Faden `20261110-183355-desktop-blick-nach-release`), Screenshots vom Owner
einzeln angesehen. Geprüft wurde der **Repo-Start** (`uv --directory … run chemdraw-tool-server`,
Serverprozesse ab 18:33:28 CET), **nicht das installierte `.mcpb`**. HEAD `3d4ba62`; gegenüber dem
Release-Commit `f4afc86` nur `plans/mcp-server.md` geändert. Modell Opus 5.5 Medium, je Prompt ein neuer Chat.

| Nr. | Uhrzeit CET | Prompt wörtlich | Tool | Erwartung | Befund | Screenshot |
|---|---|---|---|---|---|---|
| 1 | 18:35 | Draw capsaicin | generate_molecule | Chips genau Ether, Amide, Phenol, Aromatic ring; kein Secondary amine | trifft: Ether 1, Amide 1, Phenol 1, Aromatic ring 1 | `01-result.png` |
| 2 | 18:36 | Draw caffeine | generate_molecule | Amide 3, Aromatic ring; kein Tertiary amine | trifft: Amide 3, Aromatic ring 2 | `02-result.png` |
| 3 | 18:37 | Draw lysozyme | generate_protein_or_antibody | drehbarer Cartoon | Cartoon sichtbar (1LYZ, Kette A, 129 Reste; Secondary/Rainbow, Cartoon/Trace, Reset); **Drehung nicht bestätigt** | `03-before.png`, `03-rotated-final.png` |
| 4 | 18:39 | Draw trastuzumab | generate_protein_or_antibody | Structure/Scheme-Umschalter | trifft: Fab-Cartoon (1N8Z, Ketten A/B) → IgG-Schema „Shown structure: this Fab arm“ → zurück | `04-structure.png`, `04-scheme.png`, `04-structure-return.png` |

## Die offene Stelle

Drei synthetische Ziehversuche (CUA) im Lysozym-Panel, der erste lag außerhalb des Cartoons, zwei im
Cartoon. `03-before.png` und `03-rotated-final.png` zeigen dieselbe Lage. Nicht ermittelt, ob die
Ziehereignisse das Panel erreichen. Das ist **keine belegte Regression und kein belegtes Funktionieren**:

- Dafür, dass es am Messweg liegt: `test:host` zieht mit echten Mausereignissen im sandboxed iframe
  und prüft „Ziehen dreht den Cartoon“ (`chemdraw_tool/ui/src/host/host.e2e.mjs:222–227`).
- Was fehlt: ein Zug mit echter Maus in Claude Desktop. Das ist Teil von Jays Handgriff am
  veröffentlichten Bundle („Draw lysozyme“, einmal ziehen).

Die Screenshots liegen unter `/tmp/chemdraw-desktop-test/release-0-10-0/` und bleiben außerhalb des
Repos (sie zeigen die Seitenleiste mit privaten Chat-Titeln).

## Nachtrag 18:48 — Drehung bestätigt

Zweiter Versuch von Codex (Faden `20261110-184651-bundle-abnahme-0-10`, Teil A) im selben Chat, diesmal
mit einem Mauszug auf Ereignisebene (CGEvent: leftMouseDown, mehrere leftMouseDragged, leftMouseUp):
**der Cartoon dreht sich.** Vom Owner im Bild verglichen: `03-before.png` (Faltblatt rechts, Helices
links) gegen `bundle-0-10-0/A-drag.png` (Faltblatt links, Helices rechts). Laut Codex wirken auch
Trace/Cartoon und ⌘+Scroll (`A-trace.png`, `A-cartoon.png`, `A-zoom.png`). Die drei wirkungslosen Züge
davor lagen am Messweg (CUA-Zug), nicht am Panel. Stand: Repo-Start, nicht das Bundle.
