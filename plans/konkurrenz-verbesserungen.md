# Verbesserungen aus der Konkurrenz-Zerlegung (Jay, 26.10.2026)

Jay: „nicht 1 zu 1 – inspirieren lassen und unseren gezielt besser machen.“ Auswahl Jay 26.10.: **alle 6**.
Quellen (nur lokal, `docs/distribution/` ist gitignored): `docs/distribution/zerlegung-zeichnen-2026-10-26.md`,
`docs/distribution/zerlegung-daten-2026-10-26.md`. Fremd-Klone (nur lesen, nie ausführen): `~/GitHub/konkurrenz/`.
Keinen Fremdcode kopieren; TanmayGarg2009_chem hat keine Lizenz → nicht einmal Code ansehen nötig.

Regeln aus CLAUDE.md gelten: TDD (rot zuerst), Golden-SVGs nie zum Grünmachen neu erzeugen, neue Render-Optionen
opt-in, Tool-Snapshots bewusst mit `UPDATE_TOOLSNAPS=1` im selben Commit, Panel-Kette (Payload ↔ App.jsx ↔ Bundle),
Beschreibungen < 2 KB, MVP bleibt 7 Tools (alles als Parameter/besseres Ergebnis, kein neues Tool). Gate `./test.sh`
grün je Etappe, Exit-Code nicht verpipen. Nach Server-Änderung Claude Desktop neu starten + Handshake.

## Etappe 1: Kaputtes SMILES nie in die Namenssuche (S)
- [x] Rot: `stoffe.json`/Resolver-Test — `c1cccc1` muss Fehler `kind="invalid_smiles"` geben (heute: still Cyclopentan via NCI), `C1CCC` und `CN(C)(C)C` ebenso statt „Verbindung instabil“/„Name unbekannt“
- [x] `resolver.py:resolve()`: SMILES-artig + Parse-Fehler → nicht in die Namenskaskade; Meldung mit RDKit-Fehlerstelle; Reparaturvorschlag (Großschreibung, `[N+]`) nur als Text-Angebot, nie automatisch zeichnen

## Etappe 2: Mehrdeutige Namen zeigen alle Isomere (S–M)
- [x] Rot: `xylene`/`Xylol`/`cresol`/`Kresol`/`toluidine` → `kind="ambiguous"` mit Kandidaten (heute: OPSIN wählt still ortho)
- [x] Kuratierte Familien DE+EN in `resolver.py` VOR OPSIN (Xylol, Kresol, Toluidin, Butanol, Glucose offenkettig/Pyranose — offene Frage aus `stoffe.json`)
  - **Jay:** `D-Glucose` löst weiter offenkettig auf (nicht in der Familientabelle) — sollen auch dort die Ringformen angeboten werden?
- [x] `generate_molecule` antwortet mit den Kandidaten; Panel zeigt o/m/p als Vorschaubilder, Klick ruft `generate_molecule` über `callServerTool` (Muster `ExportPngButton`/Data-Knopf)

## Etappe 3: Pfeiltypen + Text unter dem Pfeil (S)
- [ ] `generate_reaction`: Parameter `arrow` (`forward`|`equilibrium`|`retro`, Standard forward) + `conditions_below`; Formeln in Bedingungen tiefstellen (H2SO4 → H₂SO₄)
- [ ] Durch alle Pfade: `image_export.py`, `svg_renderer.py`, `layout.py`/`cdxml_writer.py` (Pfeiltyp in CDXML), Reaktionsansicht `ui/src`, Bundle neu
- [ ] README-Demo Fischer-Veresterung auf Gleichgewichtspfeil umstellen

## Etappe 4: Unbestimmte Stereozentren markieren (S)
- [ ] RDKit `FindPotentialStereo` in `generator.py` → Warnung im `MoleculePayload`; Panel hebt betroffene Atome mit dem vorhandenen Hover-Highlight hervor (Bezug: Memory „manual-smiles-stereo-trap“)

## Etappe 5: GHS-Datenblatt nach Quelle geordnet (S–M)
- [ ] Messung zuerst: Koffein CID 2519 (heute 18 flache Zeilen, 4 Signalwörter) und NaCl („Not Classified“?)
- [ ] `databases.py`: nach `ReferenceNumber` gruppieren, Zustimmungs-% lesen, „Not Classified“ als eigener Befund; Leitquelle vorn (EU-harmonisiert, sonst ECHA-Aggregat), H-Sätze nach % sortiert, Rest zugeklappt
- [ ] `payloads.py` (`DatabaseSource` je Quelle), DataSheet-View, Test

## Etappe 6: Reaktionsbilanz-Prüfung (M)
- [ ] `chemdraw_tool/reaction_balance.py` (eigene Umsetzung: Elementmatrix, rationaler Nullraum mit `fractions.Fraction`, keine neue Abhängigkeit)
- [ ] Aus `generate_reaction` aufrufen; Panel-Badge („ausgeglichen“ / „rechts fehlt H₂O“ / vorgeschlagene Koeffizienten); nie die Zeichnung still ändern

## Zur Auswahl (Nachtrag 26.10., NICHT freigegeben — nicht bauen ohne Jays Ja)
- Gleiche Bindungslänge über alle Abbildungen als opt-in-Stil `acs1996` (gemessen: Ethanol 423 px vs. Cholesterin 84 px im selben PNG)
- Herkunfts- und Prüfzeile im Panel (Quelle, InChIKey, Warnungen) — überschneidet sich mit Etappe 4
- Vorschaubild als Fallback ohne Panel (vorher messen, ob Desktop doppelt zeigt)
- Layout-Integritätstest (kein Atom in einem Ring), CoordGen nur wenn messbar besser
- Resonanzstrukturen (nach dem MVP)

## Später / blockiert
- Struktur→Name (einzige frisch belegte Nachfrage): Orthonym pinnt exakt rdkit 2026.3.5 / lxml 6.1.3 + JVM — erst wenn das gelöst ist, dann nur optional wie OPSIN.

## Abschluss
- [ ] Gate grün, Desktop neu gestartet, Handshake 7 Tools/6 Panel, Release-Notiz-Entwurf (Release selbst = Jays Klick)
