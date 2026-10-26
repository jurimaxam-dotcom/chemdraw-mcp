# Grundlagen zuerst: Schreibweisen und Gleichungen (Jay, 26.10.2026)

Jay: „ich will erst die Grundlagen abdecken.“ Reihenfolge = Grundlage → Spezialfall. Nichts davon ist schon freigegeben
zum Bauen; Jay gibt je Etappe frei. Bausteine von heute: Isomer-Auswahl (0a1d29a), Stereo-Warnung (42768a8),
Reaktionsbilanz (3525cdf). Regeln aus CLAUDE.md: MVP bleibt 7 Tools (Parameter/Panel-Knopf statt Tool), opt-in, TDD,
Golden-SVGs nie zum Grünmachen neu erzeugen. Desktop-Test läuft über den Repo-Server (siehe plans/konkurrenz-verbesserungen.md).

## Etappe 1: Alle H-Atome zeigen (S)
- [x] Panel-Umschalter „Skeletal ↔ all H“ am Molekül-Panel; Server liefert zweites SVG (RDKit AddHs) oder Parameter `explicit_h`; Export folgt der Ansicht
  - Gebaut 26.10.: Payload `svgAllH`/`atomsAllH` (AddHs mit addCoords, Schweratom-Indizes bleiben), Knopf „All H“ unter
    der Struktur, PNG-Export nimmt die sichtbare Zeichnung. Bei `abbreviate_groups` kein Umschalter.
  - Verworfen 26.10.: gleicher Ausschnitt für beide Ansichten. Jay will, dass die Skelettformel die Fläche füllt; der Größenwechsel beim Umschalten ist gewollt.
  - [ ] Später, nur auf Ansage: Parameter `explicit_h` für die Chat-Route („mit allen H“) und die Dateien auf der Platte

## Etappe 2: Koeffizienten in die Gleichung übernehmen (S–M)
- [x] Bilanz-Badge mit Vorschlag bekommt Knopf „Apply coefficients“ → `generate_reaction` mit Koeffizienten (neuer Parameter, z. B. `coefficients`), Zeichnung zeigt „2 H₂ + O₂ → 2 H₂O“; nie ungefragt
  - Gebaut 26.10.: Parameter `coefficients` (eine Zahl je Stoff, 1 wird nicht gezeichnet) in PNG/SVG/CDXML und Panel;
    Bilanz zählt mit Koeffizienten; Payload `request` wiederholt den Aufruf. Eigene Datei je Koeffizientensatz.

- Befunde Desktop-Test 26.10. (Jay, Bild „Knallgasreaktion“):
  - [ ] Modell setzt `coefficients` schon beim ersten Aufruf selbst; der Knopf wurde nicht gebraucht. Widerspricht „nie ungefragt“?
        Jay entscheidet: so lassen (Modell erklärt es im Text) oder Beschreibung „only when the user asks for a balanced equation“
  - [ ] Unter den Molekülen steht der SMILES-Eingabetext ([H][H], O=O, O) statt eines Namens/einer Formel → bei SMILES-Eingabe Summenformel (H₂, O₂, H₂O) als Label
  - [ ] Knopf „Apply coefficients“ einmal in Desktop von Hand klicken (bisher nur DOM-Test + test:host ohne diesen Pfad)

## Etappe 3: Stereo-Auswahl R/S, E/Z (S–M)
- [ ] Stereo-Hinweis bekommt „Show variants“: alle Stereoisomere (EnumerateStereoisomers, Obergrenze 3 Zentren = 8) als Vorschaubilder mit R/S- bzw. E/Z-Label, Klick zeichnet mit Keilen — Muster der Isomer-Auswahl

## Etappe 4: Fischer-/Haworth-Projektion (M–L, später)
- [ ] Erst messen, ob RDKit/eine Bibliothek das kann (github-first); sonst eigener Zeichner nur für Zucker/Aminosäuren
