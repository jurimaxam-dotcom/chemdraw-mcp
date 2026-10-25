# Durchgehende Workflows (Jay, 21.10.2026)

Ziel: Jeder Workflow läuft im echten Claude Desktop vom Tippen bis zum Ergebnis in der
Zielanwendung, ohne Umweg.

Stand Panel heute: Struktur/Daten-Umschalter, „Export PNG", Kopierknöpfe an den Daten.
`export_anki_deck` ist seit 0.5.1 auch im Standardprofil (`mvp`); der Panel-Knopf
„Add to Anki“ ist verfügbar. 0.5.2 macht das Struktur-PNG auf der Karte transparent.

Launch-Reihenfolge (Jay, 25.10.2026): Faden 1 reicht für den ersten Post. Faden 2 Word
und Faden 3 folgen nach Launch, Stück für Stück. Auch die Rückkehr ins Standardprofil
(3D → Mechanismus → Laborgrafiken, je Minor-Release) beginnt nach dem ersten Post.

## Faden 1: Lernen – Molekül → Anki
„Hey Claude, draw me ibuprofen" → Panel in Sekunden → Knopf **Add to Anki** am Panel → Anki öffnet
sich mit der Karte.
- [x] Knopf im MoleculeView: ruft per `app.callServerTool` ein Server-Tool, das eine .apkg mit
      genau diesem Molekül baut (Vorderseite Struktur, Rückseite Name/Formel) und sie mit dem
      Standardprogramm öffnet (macOS `open` → Anki importiert). Kein AnkiConnect-Zwang.
- [x] `export_anki_deck` zurück ins MVP (Chat-Weg „mach mir Karten zu den Analgetika"),
      Profil-/Taxonomie-/Snapshot-Tests, Handshake-Zahlen anpassen
- [x] Desktop-Neustart und Test durch Jay im NORMALEN Chat bestanden (24.10.2026 23:55, Desktop 3.6556.2): Panel mit Structure, Data, Export PNG, Add to Anki sichtbar; Log zeigt tools/call, dann resources/read. Die Inkognito-Einschränkung vom 21.10. gilt nicht mehr; Issues anthropics/claude-ai-mcp 1168 und 1069 bleiben Beobachtungspunkt.
- [x] Release 0.5.1 veröffentlicht 25.10.2026 (PyPI, Registry isLatest, Bundle); enthält Knopf, Anki im MVP und die neue Karte nach Design-Entwurf. 0.5.2 25.10.: transparente Struktur.
- [x] **Jay:** Abnahme 0.5.1 in Desktop — bestanden 25.10.2026 08:57, Jay: Karte in Anki sieht gut aus; Desktop mit Extension 0.5.1 + PyPI-Wheel (Neustart 08:56). Auftrag war: Bundle von releases/tag/v0.5.1 installieren, Desktop neu starten, „draw caffeine" → Add to Anki, Karte in Anki prüfen (vorn nur Struktur + Which molecule?, hinten Name/Formel/CAS, Nachtmodus invertiert). Entwurf: https://claude.ai/artifact/14Uyj5FjntQPpT9QxqiAvG. Danach Vertrieb (plans/vermarktung.md: Preview hochladen, Aufnahme-Recht, Short-Neuaufnahme).
  - [x] Befund 25.10.: Bundle-Tool-Verzeichnis war eine stale lokale 0.5.1 vom 21.10. (find-links auf `dist/`, alte Karte; run.sh prüft nur den Versionsstring). Ersetzt durch PyPI 0.5.1 (Backup `tools/chemdraw-mcp.alt-20261021`): `anki_export.py` sha256 47da78cc…ef06c, 10006 Bytes = Repo 745f6d6; Receipt ohne find-links; caffeine-Deck geprüft (vorn Bild + Which molecule?, hinten Name/Formel/CAS 58-08-2 live aus PubChem, nightMode-CSS); Handshake über Extension-run.sh 7/6 grün. Extension-Manifest steht noch auf 0.5.0, bis Jay das .mcpb installiert.

### Faden 1b: eigene Karten (Jay 21.10., nach dem Standardknopf)
- [ ] Rückseite selbst füllen: im Chat Hinweise/Merksätze diktieren („schreib dazu: hemmt COX-1/2")
      → Karte erstellen → exportieren. Chat-Weg kann `export_anki_deck` schon (Claude schreibt `back.text`);
      im Panel: Hinweisfeld vor „Add to Anki"
- [ ] Ziel-Deck wählen statt festem „ChemDraw": Deckname mit Unterdecks (`Pharmakologie::NSAIDs`),
      zuletzt genutztes merken. Bestehende Decks auflisten geht nur mit AnkiConnect (Add-on) → optional,
      ohne Add-on Deckname eintippen
- [ ] Mehr Kartenformate: Name→Struktur (umgekehrt), funktionelle Gruppen markieren, Lückentext,
      Reaktion; Auswahl am Knopf (Formate gibt es in `AnkiCard` schon: reversed, cloze, reaction)

## Faden 2: Praktikumsbericht – Molekül → Word (nach Launch)
Panel → Knopf **Copy for Word** → in Word einfügen, Bild in Druckqualität.
- [ ] Weg klären: Bild in die Zwischenablage über den Server (macOS: osascript, PNG in hoher
      Auflösung), weil die Sandbox des Panels Bild-Zwischenablage nicht sicher erlaubt
- [ ] Knopf + Test, Jay prüft in Word

## Faden 3: Tiefer ins Molekül (nach Launch)
Auswahlknöpfe im Panel: andere Darstellungen (Stereo R/S, 3D, funktionelle Gruppen, Daten).
- [ ] Designrunde am iPad: welche Knöpfe, wo (Ablauf `~/.claude/docs/designrunden-ipad.md`)
- [ ] Bauen nach dem Entwurf
