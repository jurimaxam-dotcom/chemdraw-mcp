# Grundlagen zuerst: Schreibweisen und Gleichungen (Jay, 26.10.2026)

Jay: „ich will erst die Grundlagen abdecken.“ Reihenfolge = Grundlage → Spezialfall. Nichts davon ist schon freigegeben
zum Bauen; Jay gibt je Etappe frei. Bausteine von heute: Isomer-Auswahl (0a1d29a), Stereo-Warnung (42768a8),
Reaktionsbilanz (3525cdf). Regeln aus CLAUDE.md: MVP bleibt 7 Tools (Parameter/Panel-Knopf statt Tool), opt-in, TDD,
Golden-SVGs nie zum Grünmachen neu erzeugen. Desktop-Test läuft über den Repo-Server (siehe plans/konkurrenz-verbesserungen.md).

## Arbeitsweise ab 26.10.: Claude baut, Codex testet in Desktop (Jay)
Jay: „entwickle autonom mit ihm weiter … sprecht euch ab“. Je Etappe: Claude baut (TDD, Gate, test:host, Desktop-Neustart)
→ `tisch auftrag codex` mit dem Desktop-Test (Prompt, Klicks, Erwartung, Screenshots nach /tmp/chemdraw-desktop-test/)
→ Codex steuert Desktop (AX-Klicks, Developer-Einstellungen: MCP-Log, Server neu laden), meldet ja/nein je Schritt
→ Claude fixt Befunde, Codex testet erneut. Jay bekommt das Ergebnis am Etappenende, keine Handtests.
Eigentum: Codex `vermarktung/ax-claude.swift`, `vermarktung/aufnahme-desktop.sh` und ein wiederholbares Desktop-Testskript;
Claude Server/UI/Tests. Bremsen bleiben: Release, Posts, Außenkommunikation = Jays Hand.
Codex' Bedingungen (Faden 20261026-180450, #2): Testauftrag nennt Commit, exakte Prompts, Klickfolge, Sollzustände
und ob ein Desktop-Neustart nötig ist. Während einer Abnahme fasst Claude Desktop nicht an (kein Neustart, keine
Bedienung); Repo-Änderungen vor einem angekündigten Neustart abstimmen. Codex prüft gesendete Argumente im MCP-Log
(`~/Library/Logs/Claude/mcp-server-chemdraw-tool.log`) und startet Desktop nach Serveränderungen voll neu (kein Hot-Reload).

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
  - [x] Modell setzt `coefficients` schon beim ersten Aufruf selbst; der Knopf wurde nicht gebraucht. Widerspricht „nie ungefragt“?
        **Jay:** (a) Auswahl liegt beim Nutzer. Umgesetzt 26.10.: Parameter-Text „Set only when the user asks for a
        balanced equation …“, Eval-Fall `draw-reaction-as-typed` mit neuem Feld `forbidden_args: [coefficients]`.
  - [x] Unter den Molekülen steht der SMILES-Eingabetext ([H][H], O=O, O) statt eines Namens/einer Formel → bei SMILES-Eingabe Summenformel (H₂, O₂, H₂O) als Label
        — Gebaut 26.10. (fdaacd1): Panel + CDXML (face="32"); PNG/SVG der Reaktion hatten nie Beschriftungen, bleiben so
  - [ ] Knopf „Apply coefficients“ einmal in Desktop von Hand klicken (bisher nur DOM-Test + test:host ohne diesen Pfad)

## Etappe 3: Stereo-Auswahl R/S, E/Z (S–M)
- [x] Stereo-Hinweis bekommt „Show variants“: alle Stereoisomere (EnumerateStereoisomers, Obergrenze 3 Zentren = 8) als Vorschaubilder mit R/S- bzw. E/Z-Label, Klick zeichnet mit Keilen — Muster der Isomer-Auswahl
  - Gebaut 26.10.: Parameter `stereo_variants` an generate_molecule (lazy, nur per Klick oder auf Bitte — eager hätte
    bis zu 8 Vorschaubilder in jeden Modellkontext gelegt; Payload ist schon 29 KB Text). Antwort = AmbiguousPayload,
    Knopf neben dem Hinweis, Vorschau mit CIP-Annotation, Meso zählt einmal. Eval-Fälle `draw-racemate-as-typed`,
    `all-stereoisomers`; test:host klickt Methylphenidat → 4 Varianten → (S,S) mit Keilen.
  - [ ] Jays Handtest in Desktop: „Zeichne Ibuprofen“ → Show variants → (S) klicken

## Etappe 4: Fischer-/Haworth-Projektion (M–L, später)
- [x] Erst messen, ob RDKit/eine Bibliothek das kann (github-first); sonst eigener Zeichner nur für Zucker/Aminosäuren
  - Verdikt 26.10. (Scout): **Eigenbau.** RDKit 2026.03.6 hat keine Projektions-API (nur `rdDepictor.SetRingSystemTemplates`,
    normales Layout). CDK `FischerRecognition`, Indigo `haworth_projection_finder`, Kekule.js nur *Erkennung*.
    `pychemprojections` (BSD-3, 17★) nur Fischer, keine Ringe, parst den SMILES-String → ignorieren.
  - Regel (gemessen, ohne CIP/3D): `Chem.AddHs`, Chiralitätstag in fester Nachbarreihenfolge lesen
    (`cw ^ parity(GetBonds-Reihenfolge → Zielreihenfolge)`). Fischer: Hauptkette von C1 (Carbonyl/COOH oben), Ziel
    (oben, unten, X, H), gleich Referenz D-Glycerinaldehyd ⇒ X rechts. Stimmt für D-Glc RLRR, D-Gal RLLR, D-Rib RRR,
    D-Fru (C3–5) LRR, L-Ala/L-Ser NH₂ links. Haworth: Ring ab Ring-O über das anomere C im Uhrzeigersinn (O hinten
    rechts), Ziel (Vorgänger, Nachfolger, s0, s1), gleich Referenz β-D-Glcp ⇒ s0 oben. Stimmt für α/β-Glc, β-Gal, β-Ribf.
  - Prototypen: `plans/anhang/fischer-prototyp.py.txt`, `plans/anhang/haworth-prototyp.py.txt` (Skizzen, nicht lint-fest).
- [x] Bauen: `chemdraw_tool/projection.py` (keine neue Dependency), Panel-Umschalter „Fischer“/„Haworth“ nur bei passenden
      Stoffen (offenkettige Zucker/Aminosäuren bzw. Pyranose/Furanose), opt-in, Standardausgabe unverändert.
      Fischer: Kreuzkoordinaten als Conformer → bestehender svg_renderer, ohne Keile. Haworth: feste Ring-Koordinaten,
      dicke Vorderkante als eigenes SVG, Substituenten als senkrechte Striche (OH, H, CH₂OH). TDD mit den neun Fällen
      oben + α-Anomer als Gegenprobe gegen CIP (selbst getipptes SMILES kippt das Anomer still).
      Offene Bauentscheidung für die bauende Session: Ringzucker in Fischer (Ring öffnen) oder klarer Hinweis.
  - Gebaut 26.10.: Payload `svgFischer`/`svgHaworth`/`projectionNote` (eager wie „All H“, nur bei passenden Stoffen,
    Fehler kostet nur den Knopf), Knöpfe „Fischer“/„Haworth“ neben „All H“, drei Ansichten schließen einander aus,
    Export nimmt die sichtbare. Kein neues Tool, kein Parameter, Beschreibung unverändert.
  - Abweichung vom Plan: Fischer nicht als Conformer im RDKit-Renderer, sondern eigenes SVG mit Formeltext
    (CHO, CH₂OH, COOH, HO/H) wie im Lehrbuch — Skelett-Ecken an den Kettenenden wären unlesbar.
  - **Entscheidung Ringzucker → Hinweis, kein Ringöffnen.** Ringöffnen zeichnet einen anderen Stoff als den
    eingegebenen und verwirft das Anomer still (dieselbe Fehlerklasse wie die SMILES-Stereo-Falle). Teuer ist es nicht:
    „D-glucose“ löst OPSIN schon offenkettig auf, nur „beta-D-glucose“ kommt als Ring. Die Haworth-Ansicht sagt dann
    in einem Satz, wie man die Fischer-Projektion bekommt.
  - Befund: Der Prototyp-SMILES „b-Fru-f“ war das α-Anomer (C2 = S). Test nutzt OPSINs β-D-Fructofuranose (C2 = R).
  - Umfang: Aldosen/Ketosen/Aldon-/Uronsäuren offen; 16 proteinogene Aminosäuren (Ile/Thr fehlen: zweites Zentrum
    stünde als Formeltext ohne Seite); Pyranose/Furanose mit H/OH/CH₂OH/CH₃/NH₂, offenes Anomer als Schlangenlinie.
    Glykoside (Saccharose, Methylglucosid) und Alditole bekommen nichts.
  - [ ] Später, nur auf Ansage: Parameter `projection` für die Chat-Route und die Dateien auf der Platte; Ile/Thr mit
        zweitem Kreuz; Glykoside in Haworth
  - [x] Desktop-Abnahme durch Codex 26.10. (Faden 20261026-182553): Knöpfe, Fischer, Haworth, L-Alanin, Export-PNG,
        Dunkelmodus, Ibuprofen ohne Projektion — alles ja.
  - [ ] Befund Codex: Desktop-Modell (Sonnet 5.5) schreibt bei „Zeichne D-Glucose“ selbst SMILES + annotate_stereo statt
        name_or_smiles=„D-glucose“ (auch L-Alanin, beta-D-Glucose). Diesmal stimmte die Stereochemie, aber das ist die
        SMILES-Stereo-Falle: Routing-/Beschreibungsthema, nicht Etappe 4. Kandidat: Eval-Fall „Namen nicht selbst in SMILES übersetzen“.

## Payload schlank halten (Jay 26.10.2026)
Messung: „All H“ (`svgAllH` + `atomsAllH`) ist 55–60 % jeder Molekül-Antwort (Ibuprofen 17,5 von 29,4 KB, Koffein 17,0 von
31,1 KB). Desktop verwirft structuredContent, das Modell liest den ganzen Text. **Jay: „Erst auf Klick“.** Regel: Was nur
auf Klick gebraucht wird, kommt per Klick (wie Stereo-Varianten und Datenblatt), nie eager ins Payload.
- [x] All H, Fischer, Haworth lazy: Panel holt die Ansicht per `callServerTool` beim ersten Klick, cacht sie; das Payload
      trägt nur, OB es die Ansicht gibt (Flags/Knopf-Sichtbarkeit), nicht die SVGs. Beschreibung < 2 KB, Snapshot segnen,
      test:host anpassen. Abnahme: Ibuprofen-Antwort < 15 KB (vorher 29,4), Klick auf All H < 1 s.
  - Gebaut 26.10.: Payload trägt `views` + `viewRequest` (resolve-SMILES, damit Atomreihenfolge und Highlights
    gleich bleiben, plus annotate_stereo/render_style); Parameter `view` an generate_molecule („Panel-internal“),
    ohne Dateien, ohne Netz. Gemessen: Ibuprofen 27,0 → 9,3 KB (model_dump_json), Methylphenidat-Text 13,5 KB,
    All H per Klick 71 ms in test:host, zweiter Klick aus dem Cache. Fehlschlag bleibt sichtbar und wiederholbar.
  - Befund Desktop-Abnahme 2 (Faden 20261026-184042): Modell setzte bei „Zeichne beta-D-Glucose“ `view=haworth` selbst →
    Panel ohne Titel, Knöpfe, Hinweis. Fix 26.10.: ein view-Aufruf liefert jetzt ein vollständiges, lokales Panel
    (Skelettformel, Gruppen, Formel/Masse aus RDKit, kein PubChem, keine Dateien) plus `initialView`/`viewSvg`; das Panel
    startet auf der Ansicht. Beschreibung: view nur, wenn der Nutzer die Projektion nennt; Eval-Fall `draw-sugar-as-typed`
    (forbidden_args: view). Codex' übrige Punkte ja: Ibuprofen 10,9 KB, +1 Aufruf beim Klick, Cache, Export.
  - [ ] Desktop-Abnahme 3 (Codex): „Zeichne beta-D-Glucose“ und „Zeige die Haworth-Projektion von beta-D-Glucose“
- Prüfungsfragen (OC): kein achtes Tool — Panel-Modus oder Parameter, Fragenbestand als Datendatei.

## Übergabe 26.10.2026 abends (Haupt-Session → frische Session)
Fertig und in Desktop von Codex abgenommen: Etappe 1–3 (All H, Koeffizienten nur auf Wunsch, SMILES-Labels als Formel,
Show variants, Zurück-Leiste a475eae). Etappe 4 Fischer/Haworth (f20b31a, 7cf2f71) und Lazy-Umbau (ddc2f4c) gebaut von
Session ec41d68c (Faden 20261026-181107-grundlagen-etappe-4-fischer); Desktop-Abnahmen durch Codex laufen in den Fäden
20261026-182553 (Etappe 4) und 20261026-184042 (Lazy; erste Messung Ibuprofen 10,9 KB statt 29,4 KB).
Nächste Schritte für die neue Haupt-Session:
1. Beide Codex-Berichte abnehmen (Screenshots selbst ansehen, nicht nur glauben), Befunde an die bauende Session oder selbst fixen.
2. Thema „Prüfungsfragen“: Jay entschied OC-Grundlagen zuerst (plans/mcp-server.md); kein achtes Tool.
3. Kleinigkeit, offen für Jay: bei Kleinstmolekülen steht die Formel doppelt (Zeichnung „H₂O“ + Label „H₂O“).
Arbeitsweise unverändert: Claude baut, Codex testet in Desktop (§ Arbeitsweise oben).
