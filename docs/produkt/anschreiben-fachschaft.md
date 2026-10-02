# Entwurf: Anschreiben an eine Pharmazie-Fachschaft

Jay sendet, Claude entwirft (Außenkommunikation). Platzhalter in [eckigen Klammern].
Ziel: 3–5 Studierende aus dem 1.–4. Semester für einen 10-Minuten-Test.
Erst senden, wenn der Link öffentlich ist. Vorher:
1. `web/praktikumsrechner/impressum.html` ausfüllen: Name, ladungsfähige Anschrift, E-Mail (§ 5 DDG).
   Das Deploy-Skript bricht ab, solange dort Platzhalter stehen.
2. `cd ~/Documents/projects/chemdraw-mcp && ./scripts/deploy-pages.sh`. Es gibt den Link aus oder sagt,
   welche Einstellung fehlt.

---

**Betreff:** 10 Minuten für einen Übungsrechner zu Quanti, pH und Mechanismen?

Hallo liebe Fachschaft Pharmazie [Standort],

ich heiße [Vorname] und baue einen Übungsrechner für das Grundstudium. Er erzeugt zu jeder
Aufgabe neue Zahlen und zeigt den ganzen Rechenweg, Schritt für Schritt. Abgedeckt sind:

- Gehaltsbestimmung, Faktorbestimmung gegen Urtiter, Sollverbrauch, Titrationsäquivalent
- pH von Säuren, Basen und Puffern
- Löslichkeitsprodukt, auch mit gleichionigem Zusatz
- SN1, SN2 oder E2: welcher Weg bei welchem Substrat und Reagenz

Er läuft im Browser, ohne Anmeldung: [Link]

Ich suche 3–5 Leute aus dem 1. bis 4. Semester, die ihn 10 Minuten lang an Aufgaben aus
ihrem eigenen Praktikum ausprobieren und mir danach sagen, was fehlt oder falsch ist. Dafür
gibt es den Semesterpass gratis, sobald er kostenpflichtig wird.

Könnt ihr das in eure Semestergruppen weitergeben? Wer mitmachen will, schreibt einfach an
[Mailadresse].

Viele Grüße
[Vorname]

---

## Warum so

- **Konkret statt Werbung:** Genannt werden Aufgabentypen, die im Grundstudium wirklich drankommen
  (`docs/produkt/pruefungen-pharmazie-2026-10.md`), keine Superlative.
- **Kleine Bitte:** 10 Minuten und 3–5 Leute. Eine Fachschaft leitet so etwas eher weiter als eine
  Umfrage.
- **Gegenleistung:** Der Semesterpass gratis kostet nichts, solange niemand zahlt, und bindet die
  ersten Nutzer.
- **Erster Kandidat Marburg:** 43,3 % Misserfolg in Fächergruppe I im Herbst 2025, der höchste Wert
  der 9 Standorte. Dort ist der Leidensdruck belegt.
  Kontakt laut Recherche: https://fachschaft-pharmazie-marburg.de
