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

Recherche-Ergebnis (Scout + Repo-Analyse): Der größte Hebel lag im eigenen
Repo — `calculator/` war verwaist. Neuer Bereich **Rechnen**, Obergrenze
bewusst 16 → 18.

- [x] **`calculate_solution`** (a0fcb57) — Einwaage, Konzentration, Verdünnung,
      Mischungskreuz, Molmasse. Neue Abhängigkeit `molmass` für Hydrate.
- [x] **`calculate_content`** (3ad3716) — Gehaltsbestimmung Titration/Photometrie
      mit Grubbs-Ausreißertest, Statistik, t-Test. Bringt `calculator/` ans Netz.
- [x] **`calculate_ph`** (16cd075) — pH, Puffer, Pufferansatz; exakte
      Ladungsbilanz neben der Lehrbuchnäherung.
- [x] **Fettkennzahlen + Karl-Fischer** (5076df0) — als Methoden von
      `calculate_content`, kostet keinen Tool-Platz.
- [x] **`generate_calibration_curve`** (7f74734) — Regression, Rückrechnung
      unbekannter Proben, NWG/BG. Dabei die Gegenrichtung der Abgrenzung
      nachgezogen (pH-Diagramme → `calculate_ph`).
- [x] **`predict_spectrum`** (e1feb4b) — IR-Banden aus der Struktur,
      Wellenzahl-Zuordnung, ¹H-Signalzahl. Text, damit die Bandenliste an
      `generate_spectrum` weitergereicht werden kann.
- [x] Doku nachziehen (8d31e02) — CLAUDE.md, README, CHANGELOG, Memory
- [x] Toolkarte-Artifact auf den Endstand gebracht
- [x] stdio-Handshake: 20 Tools, Claude Desktop neu gestartet

**Bewusst NICHT gemacht:**
- **Datei-Split von `server.py`** in Bereichs-Module. 64 Testpatches zielen auf
  `chemdraw_tool.server.*`; ein Split bricht sie still und lässt Tests in Jays
  echten Ausgabeordner schreiben. Der Wächter in `tests/conftest.py` macht den
  Umbau nachträglich sicher — nur ist er unsichtbar und riskant, während die
  Bereiche als getesteter Vertrag schon existieren.
- **Gleichungen ausgleichen** (Stöchiometrie). Passt in keinen Bereich gut,
  bräuchte einen eigenen Platz. Nächster Kandidat, falls gewünscht.
- **Release.** Version steht weiter auf 0.3.0; der Umbau ist ein Breaking
  Change und wäre 0.4.0 — aber erst auf Jays Ansage.

**Vertagt** (machbar, aber nicht um 4 Uhr autonom):
- **Ph.-Eur.-Identitätsreaktionen als Nachschlagewerk** — der Inhalt shippt
  schon als kuratiertes Deck `pheur-identity-basics`; nur die Lookup-Form
  fehlt. Arzneibuch-Referenzdaten unbeaufsichtigt zu verfassen hat ein
  Korrektheitsrisiko, das niemand gegenliest.
- **Struktur → IUPAC-Name** — `lookup(topic="properties")` liefert den
  IUPAC-Namen für PubChem-bekannte Stoffe bereits; für selbstgezeichnete
  Zwischenprodukte gibt es offline nichts Leichtgewichtiges.
- **Elektrochemie (Nernst) und Gasgesetze** — im Pharmazie-Praktikum nur
  indirekt; erst bauen, wenn Jay sie wirklich braucht.

**Verworfen** (mit Begründung, damit es nicht wiederkommt):
- pKa-Vorhersage aus der Struktur — nur ML mit Modell-Download; die einzige
  regelbasierte Bibliothek (`dimorphite-dl`) pinnt `rdkit<2026`, das Projekt
  läuft auf 2026.03.2.
- NMR-Verschiebungen in ppm — ebenfalls nur ML. Die deterministische
  Teilmenge (Signalzahl, Integralverhältnis) ist das, was Klausuren fragen.
- Periodensystem-/Einheiten-Bibliotheken (`mendeleev`, `pint`) — schwere
  Abhängigkeiten für Wissen, das das Modell ohnehin hat.
- `chempy` fürs Ausgleichen von Gleichungen — zieht sympy/pyodesys/pulp nach;
  das Nullraum-Verfahren sind ~50 Zeilen mit `fractions.Fraction`.
