# Durchgehende Workflows (Jay, 21.10.2026)

Ziel: Jeder Workflow läuft im echten Claude Desktop vom Tippen bis zum Ergebnis in der
Zielanwendung, ohne Umweg.

Stand Panel heute: Struktur/Daten-Umschalter, „Export PNG", Kopierknöpfe an den Daten.
`export_anki_deck` + zwei kuratierte Decks + `AnkiDeckView` existieren, aber nur im Profil `full`.

## Faden 1: Lernen – Molekül → Anki
„Hey Claude, draw me ibuprofen" → Panel in Sekunden → Knopf **Add to Anki** am Panel → Anki öffnet
sich mit der Karte.
- [x] Knopf im MoleculeView: ruft per `app.callServerTool` ein Server-Tool, das eine .apkg mit
      genau diesem Molekül baut (Vorderseite Struktur, Rückseite Name/Formel) und sie mit dem
      Standardprogramm öffnet (macOS `open` → Anki importiert). Kein AnkiConnect-Zwang.
- [x] `export_anki_deck` zurück ins MVP (Chat-Weg „mach mir Karten zu den Analgetika"),
      Profil-/Taxonomie-/Snapshot-Tests, Handshake-Zahlen anpassen
- [x] Desktop-Neustart und Test durch Jay im NORMALEN Chat bestanden (24.10.2026 23:55, Desktop 3.6556.2): Panel mit Structure, Data, Export PNG, Add to Anki sichtbar; Log zeigt tools/call, dann resources/read. Die Inkognito-Einschränkung vom 21.10. gilt nicht mehr; Issues anthropics/claude-ai-mcp 1168 und 1069 bleiben Beobachtungspunkt.

### Faden 1b: eigene Karten (Jay 21.10., nach dem Standardknopf)
- [ ] Rückseite selbst füllen: im Chat Hinweise/Merksätze diktieren („schreib dazu: hemmt COX-1/2")
      → Karte erstellen → exportieren. Chat-Weg kann `export_anki_deck` schon (Claude schreibt `back.text`);
      im Panel: Hinweisfeld vor „Add to Anki"
- [ ] Ziel-Deck wählen statt festem „ChemDraw": Deckname mit Unterdecks (`Pharmakologie::NSAIDs`),
      zuletzt genutztes merken. Bestehende Decks auflisten geht nur mit AnkiConnect (Add-on) → optional,
      ohne Add-on Deckname eintippen
- [ ] Mehr Kartenformate: Name→Struktur (umgekehrt), funktionelle Gruppen markieren, Lückentext,
      Reaktion; Auswahl am Knopf (Formate gibt es in `AnkiCard` schon: reversed, cloze, reaction)

## Faden 2: Praktikumsbericht – Molekül → Word
Panel → Knopf **Copy for Word** → in Word einfügen, Bild in Druckqualität.
- [ ] Weg klären: Bild in die Zwischenablage über den Server (macOS: osascript, PNG in hoher
      Auflösung), weil die Sandbox des Panels Bild-Zwischenablage nicht sicher erlaubt
- [ ] Knopf + Test, Jay prüft in Word

## Faden 3: Tiefer ins Molekül
Auswahlknöpfe im Panel: andere Darstellungen (Stereo R/S, 3D, funktionelle Gruppen, Daten).
- [ ] Designrunde am iPad: welche Knöpfe, wo (Ablauf `~/.claude/docs/designrunden-ipad.md`)
- [ ] Bauen nach dem Entwurf
