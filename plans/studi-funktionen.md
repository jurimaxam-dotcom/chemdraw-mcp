# Studi-Funktionen anbauen — Auftrag Jay, 15.08.2026 (Nachtlauf)

**Auftrag:** „Fixe bis alles sauber läuft, dann entwickle neue Funktionen in
diesen Strukturen die vorhanden sind, die unmittelbar für Studenten nützlich
sind. Recherchiere dazu, baue so lange bis du keine Idee mehr hast."

**Rahmen:** Autonom, keine Rückfragen. Jeder Anbau geht in einen der vier
Bereiche und wird in `tests/test_server_taxonomy.py` eingetragen — das ist die
strukturelle Trennung, an die angebaut wird.

## Bereiche (Stand nach dem Umbau)

| Bereich | Tools |
|---|---|
| Zeichnen | generate_molecule, compare_molecules, batch_generate, generate_reaction, generate_mechanism, generate_scope_table, generate_3d |
| Laborgrafik | generate_spectrum, generate_tlc, generate_titration_curve, generate_species_distribution |
| Nachschlagen | lookup, lookup_molecule_data |
| Anki | export_anki_deck |
| (intern) | save_png |

## Regeln für jeden Anbau

- TDD: erst der rote Test, dann der Code.
- Panel-Tool = Fünf-Glieder-Kette (Renderer → Payload mit `type` → Tool mit
  `meta=_UI_META` → View + `case` in App.jsx → Bundle neu bauen).
- Neues Tool in `test_server_taxonomy.py` eintragen, sonst rot — so gewollt.
- Abgrenzungszeile („Not this tool for: … — use X") ist Pflicht, sobald das
  Tool mit einem bestehenden verwechselbar ist.
- Default-Ausgabe bestehender Tools darf sich nicht ändern.
- Nach jedem fertigen Tool: `./test.sh` grün, dann committen.

## Fortschritt

### Vorarbeit
- [x] Taxonomie-Umbau 22 → 15 Tools (Commit 45ea3a7)
- [x] Wächter gegen Schreiben in den echten Ausgabeordner (Commit 51d072c)
- [x] stdio-Handshake: 15 Tools bewiesen, Claude Desktop neu gestartet
- [x] Doku nachziehen (CLAUDE.md, README, CHANGELOG) — Commit d121cb3
- [x] Gegenprobe: `generate_molecule("Aspirin")` schreibt wieder nach
      `einzelmolekuele/`, nicht nach `scope/`
- [ ] Recherche auswerten (Scout + Repo-Analyse)

### Neue Funktionen
_(wird aus der Recherche gefüllt)_
