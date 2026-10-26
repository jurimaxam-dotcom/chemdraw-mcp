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
  - [ ] Desktop-Abnahme durch Codex (Auftrag siehe Tisch-Faden)
