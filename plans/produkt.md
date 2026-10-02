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
- [ ] Jay: `git merge opsin-jvm` (Auto-Modus blockt Merge ohne Review)
- [ ] Release 0.4.3 (Titer-Fix in calculate_content) — Jays Go
- [ ] Veröffentlichen für den Nutzertest (kostenlos, ohne Bezahlung: GitHub Pages ginge; mit Bezahlung: Cloudflare Pages) — Jays Go
- [ ] Stufe 2 Pharmazie: Mechanismus-Übungen für die OC-Eingangsklausur
- [ ] Jay: 10-Minuten-Nutzertest + Preisfrage (29 € pro Semester?)
- [ ] Bezahlweg (erst wenn der Nutzertest „ja“ sagt)
