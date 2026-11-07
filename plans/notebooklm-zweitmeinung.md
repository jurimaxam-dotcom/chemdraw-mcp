# NotebookLM als Zweitmeinung und Lernhilfe (Jay, 07.11.2026)

Ziel: NotebookLM + Jays Gemini-Kontingent (Zweitkonto mit Pro-Abo) regelmäßig für chemdraw-mcp nutzen – als Ideengeber aus Außenquellen und als Lernhilfe für Jay, ohne seine Urteile über den Code ungeprüft zu übernehmen.

## Befund, auf dem das aufbaut (07.11., globale Session)
- Code-Urteile von NotebookLM: etwa ⅓ falsch (Tests „fehlen“, „Prototyp 0.1.0“, schon vorhandenes MCPB als Hebel). Grund: es liest Ausschnitte und hält Nichtgefundenes für nicht vorhanden.
- Aussagen aus Webquellen (FreeChemDraw-Doku, CovaSyn, MolecularIQ-Benchmark, Datensouveränität): fast alle richtig.
- Podcasts 30.10.: 22 Lobstellen ohne Inhalt, Laufzeit-Prüfung/100 %/offline erfunden. Details: chemdraw-vermarktung `docs/notebooklm-2026-11/`.
- Daraus: **Generator + Prüfer.** NotebookLM schlägt vor, Claude/Codex prüft gegen das Repo. Zweitmeinung zur Codequalität bleibt bei Codex (Tisch, /codex:adversarial-review).
- Fragen mit Dateipfad („was macht resolver.py bei einem deutschen Namen?“) beantwortet NotebookLM zuverlässig.

## Bestand
- Notebook „chemdraw-mcp — nur Code, Stand 06.11.2026 (641d246)“, id 06bc06da-c40c-46d3-9b2d-409eb935b37d (Eigentümer: MCP-Konto, Bearbeiter: Zweitkonto): 3 Code-Pakete + 46 Webquellen + Bericht + Prüfvermerk-Notiz; Chat-Persona = strenger Reviewer.
- `scripts/notebooklm/bundle.py` + LIESMICH (Faktencheck-Regel).
- notebooklm-MCP ist am MCP-Konto angemeldet (`server_info`: profile "default"); Zweitkonto bisher nur per Chrome.

## Haken
- [ ] Profil-Prüfung: Kann die notebooklm-CLI ein zweites Profil für das Zweitkonto anlegen (`notebooklm login` mit Profil)? Dann wird das Pro-Kontingent per MCP skriptbar. Login braucht Jay → Jay-Haken mit genauem Befehl.
- [ ] GitHub-First für das Bündeln: repomix / gitingest gegen bundle.py – Verdikt Einbinden/Abkupfern/Ignorieren.
- [ ] Refresh-Ablauf: nach jedem Release die 3 Code-Quellen tauschen (ein Befehl/Skript), Notebook-Titel mit Commit.
- [ ] Konkurrenz-Radar: Deep Research ins Notebook (quartalsweise), dazu `data-table` „wer kann welches Werkzeug“ (chemdraw-mcp, ChemMCP, FreeChemDraw, CovaSyn, PubChem-MCP); jede Zeile gegen die Originalseite geprüft.
- [ ] Lernhilfe für Jay: `critique`- oder `debate`-Audio aus den Code-Quellen (nicht deep-dive) und ein Experiment Mindmap/Quiz aus Code – an einer Datei, die Jay als Nächstes ändert (Regel „Lernen nur an Aufgaben“). Mindmap/Quiz aus Code ist ungetestet.
- [ ] Code-Befunde aus der Prüfung in `plans/mcp-server.md` übernehmen (mit der dort aktiven Session per Tisch abstimmen): `__init__.__version__` 0.1.0 vs pyproject 0.8.0 (Versionstest prüft es nicht) · kein dauerhafter Cache in databases.py (nur lru_cache resolver.py) · README/server.json „lokal/offline“ ehrlich formulieren (PubChem/NCI-Abfragen) · Schalter ohne Netzabfragen · Paracetamol-Amid als „Sek. Amin“ (svg_renderer.py:162) · Routing 10/16 vor neuen Werkzeugen.
- Kontonamen bewusst nicht in diesem öffentlichen Repo; Zuordnung steht im privaten Repo chemdraw-vermarktung, docs/notebooklm-2026-11/LIESMICH.md.
