# Verkaufbares Produkt aus dem Rechenkern (Jay, 01.10.2026)

Entscheidungsseite: https://claude.ai/artifact/ML6Pefc5Ge27FPCsbRik8E (Quelle: `docs/produkt/hebelkarte.html`)
Recherche: `docs/produkt/` (Markt, Chemie/Medizin; Pharmazie folgt)

Empfehlung (Stand 02.10.): Zuerst ein Pharmazie-Praktikums- und Prüfungsrechner mit frisch erzeugten Aufgaben und Rechenweg, im Browser, als Semesterpass für 29–49 €. Zweite Stufe: Rechentrainer für Allgemeine Chemie im 1. Semester. Dritte Stufe: Sponsor- oder Campuslizenz ab 50 Zahlenden. Der MCP-Server ist nicht das Produkt.

- [x] Recherche Markt + Chemie/Medizin (01.10.)
- [x] Entscheidungsseite v1 (02.10.)
- [x] Pharmazie-Recherche einarbeiten, Seite republishen (02.10.)
- [ ] Jay: Kanal nennen (Fachschaft oder 2–3 Pharmazie-Studis, Sem. 1–4) — Prüfstein B
- [x] GitHub-First: Pyodide einbinden, Numbas-Muster abkupfern, keine deutsche Konkurrenz gefunden (02.10.)
- [x] Erster Teil: web/praktikumsrechner, 4 Titrations- + 5 pH-Typen, E2E grün (02.10.)
- [x] Mechanismus-Entscheider (SN1/SN2/E2) + Löslichkeitsprodukt (3 Typen) (02.10.)
- [x] Chemie-Gutachten: 9 Befunde behoben, je mit Test (c8ff96e)
- [x] Zweitgutachten: alle 4 Generatoren „lieferbar“, Befunde behoben (5ede28b)
- [x] Anschreiben-Entwurf Fachschaft: docs/produkt/anschreiben-fachschaft.md (Jay sendet)
- [x] Recht/Steuer/Zahlung recherchiert: docs/produkt/recht-steuer-zahlung-2026-10.md
- [x] DSGVO: Schriften + Pyodide selbst gehostet, E2E zählt 0 fremde Hosts (c6077fc)
- [x] Bundle-Startfix: feste Installation statt uv tool run (adaed6c) — braucht Release
- [ ] Hosting: Cloudflare Pages statt GitHub Pages (GH verbietet kommerzielle Transaktionen) — Jays Konto/Go
- [ ] Jay: Gewerbe anmelden, ELSTER-Fragebogen (Kleinunternehmer), Krankenkasse/BAföG informieren
- [ ] Stripe Managed Payments (MoR) aktivieren — Jays Login; Frage an Stripe: Widerrufsbutton beim MoR?
- [ ] Worker: Zahlung prüfen → signiertes Token bis Semesterende, Widerrufsfunktion (§ 356a BGB) — Claude, ~1 Tag
- [ ] Impressum, Datenschutz, Widerrufsbelehrung, 2 Checkboxen (§ 356 Abs. 6 BGB) — Jay entscheidet die Adresse
- [ ] Jay: Prototyp lokal ansehen (10-Sekunden-Test)
- [ ] Jay: `git merge --no-edit opsin-jvm` — Probe-Merge sauber (main schon eingemergt, 6fbf437), Gate dort grün
- [x] Release 0.4.3 (Titer, Daten-Knopf, Bundle-Start + Sperre) und 0.4.4 (Index-Refresh im Bundle) veröffentlicht, 02.10.
- [x] OPSIN gemergt, 0.4.5 veröffentlicht und bei Jay installiert (Desktop verbunden 21:36, 20 Tools)
- [x] **0.4.6 Code fertig (02.10.), Release offen:** Die run.sh-Sperre verwaist, wenn Desktop den Start mitten in der Installation abbricht (bei Jay passiert, 02.10. 21:08). Fix: trap auf TERM/INT/HUP gibt die Sperre frei, eine PID-Datei in der Sperre, eine tote PID heißt sofort übernehmen statt erst nach 10 min. Test mit nachgebautem uv, dessen Installation per kill abgebrochen wird.
- [x] Data-Knopf Methylphenidat automatisiert: `npm --prefix chemdraw_tool/ui run test:host` (AppBridge-Host + echter Server, 02.10.). Computer use auf die Claude-Desktop-App selbst ist gesperrt
- [ ] Jay: einmal von Hand in Desktop „Zeig mir Methylphenidat“ → Data (nur noch Host-Eigenheiten, die der Nachbau nicht kennt)
- [ ] `mcp-2-migration`: GEPARKT bis zum Desktop-Test. Auf main 3e056e0 abgeglichen (836324b, Gate grün, Handshake 2,06 s mit mcp 2.2.0). Nach dem OPSIN-Merge erneut mit main abgleichen (CHANGELOG-Konflikt), dann erst mergen
- [x] Klausurmodus (d772e01) und Offline-Modus per Service Worker (fbd37be)
- [x] Lösungsrechnen als 5. Bereich (e674c23)
- [ ] Veröffentlichen für den Nutzertest: `./scripts/deploy-pages.sh` (GitHub Pages, kostenlos, öffentlich) — Jays Go. Ein Artifact geht nicht, weil es keine .zip ausliefert (Pyodide-Stdlib)
- [ ] Option: Server-Import ohne RDKit/matplotlib (spart warm ~0,8 s, unter Last mehr) — zurückgestellt
- [ ] Stufe 2 Pharmazie: Mechanismus-Übungen für die OC-Eingangsklausur
- [ ] Jay: 10-Minuten-Nutzertest + Preisfrage (29 € pro Semester?)
- [ ] Bezahlweg (erst wenn der Nutzertest „ja“ sagt)
- [ ] 0.4.6 veröffentlichen: Version in pyproject/server.json/uv.lock, PyPI, neues .mcpb bauen (`scripts/build-mcpb.sh`), bei Jay installieren — Jays Go

## MCP verfeinern (Jay /goal, 02.10.2026): kleinster Eingriff, größter Hebel zuerst
- [x] Messung: `evals/tool-routing/run_claude.py` (Tool-Wahl über claude -p, Attrappen-Server) — 24/28 → 26/28
- [x] `lookup_molecule_data`: 6–8 Folgeaufrufe → 4 bei „Datenblatt mit allem“ (ein Satz Beschreibung)
- [x] `test:host` schreibt nicht mehr ins echte `~/ChemDraw-Output`
- [x] Entschieden (02.10.): `reaction-in-conversation` — Reaktion + Mechanismus ist gute Antwort, `forbidden` nur noch generate_molecule; `draw-scope-real` mit Strukturen im Prompt. Eval 28/28 in drei Wiederholungen der Fälle
- [x] Dateipfade im Panel mit `~` gekürzt (6 Views), Tooltip hat den vollen Pfad
- [x] Design-Galerie: `uv run python tests/gallery_ui.py` → /tmp/chem-gallery/sheet.png (13 Panel-Typen nebeneinander)
- [x] Speziesverteilung: Legende neben der Achse (6763642, Test rot gesehen)
- [x] Geprüft, kein Fehler: Kalibrierkurve-Titel doppelt (der Titel im Bild gehört in die exportierten Dateien); Reaktion ohne Titel (Edukte/Produkte/Bedingungen sind beschriftet)
- [ ] Mechanismus-Overview (größter Design-Block, ~halber Tag): uneinheitliche Strukturgrößen (Br⁻ winzig, HO⁻ groß), Übergangszustand-Beschriftung überlagert den Pfeilbogen (`mechanism_coords.py`), viel Leerraum. Zuerst Golden-Test für die Koordinaten, dann Layout
- [ ] Geschwindigkeit: Server-Import 1,4 s (mcp 0,33 · rdkit 0,25 · matplotlib 0,25) — nur lazy laden, wenn die Handshake-Zeit unter Last wehtut; Datenblatt-Ladezeit 2,3 s (PubChem) — Vorabladen nur falls Jay es spürt
