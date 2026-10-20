# Durchgehende Workflows (Jay, 21.10.2026)

Ziel: Jeder Workflow läuft im echten Claude Desktop vom Tippen bis zum Ergebnis in der
Zielanwendung, ohne Umweg.

Stand Panel heute: Struktur/Daten-Umschalter, „Export PNG", Kopierknöpfe an den Daten.
`export_anki_deck` + zwei kuratierte Decks + `AnkiDeckView` existieren, aber nur im Profil `full`.

## Faden 1: Lernen – Molekül → Anki
„Hey Claude, draw me ibuprofen" → Panel in Sekunden → Knopf **Add to Anki** am Panel → Anki öffnet
sich mit der Karte.
- [ ] Knopf im MoleculeView: ruft per `app.callServerTool` ein Server-Tool, das eine .apkg mit
      genau diesem Molekül baut (Vorderseite Struktur, Rückseite Name/Formel) und sie mit dem
      Standardprogramm öffnet (macOS `open` → Anki importiert). Kein AnkiConnect-Zwang.
- [ ] `export_anki_deck` zurück ins MVP (Chat-Weg „mach mir Karten zu den Analgetika"),
      Profil-/Taxonomie-/Snapshot-Tests, Handshake-Zahlen anpassen
- [ ] Desktop-Neustart, 10-Sekunden-Test durch Jay

## Faden 2: Praktikumsbericht – Molekül → Word
Panel → Knopf **Copy for Word** → in Word einfügen, Bild in Druckqualität.
- [ ] Weg klären: Bild in die Zwischenablage über den Server (macOS: osascript, PNG in hoher
      Auflösung), weil die Sandbox des Panels Bild-Zwischenablage nicht sicher erlaubt
- [ ] Knopf + Test, Jay prüft in Word

## Faden 3: Tiefer ins Molekül
Auswahlknöpfe im Panel: andere Darstellungen (Stereo R/S, 3D, funktionelle Gruppen, Daten).
- [ ] Designrunde am iPad: welche Knöpfe, wo (Ablauf `~/.claude/docs/designrunden-ipad.md`)
- [ ] Bauen nach dem Entwurf
