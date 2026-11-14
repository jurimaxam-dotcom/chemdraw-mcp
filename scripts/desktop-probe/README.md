# desktop-probe

Testfassung (14.11.2026): Claude Desktop per XCUIAutomation prüfen, in kleinen Checkpoints.
Der feste Ablauf in `CLAUDE.md` ist davon noch unberührt.

```bash
scripts/desktop-probe/run.sh A            # je Panel-Tool ein neuer Prompt ans Modell
scripts/desktop-probe/run.sh B            # Checkpoints am vorhandenen Chat, kein neuer Prompt
scripts/desktop-probe/run.sh B generate_molecule generate_3d   # einzelne Tools
```

Braucht Xcode (gemessen mit 27.2), `xcodegen` und ein laufendes Claude Desktop mit dem
chemdraw-Konnektor. Während des Laufs gehört der Bildschirm dem Test: Ein Wechsel in eine andere
App macht Checkpoints rot. `run.sh` reserviert die Lease `claude-desktop` im Schwester-Repo und gibt
sie am Ende frei; bei fremder Lease startet es nicht.

## Die zwei Stufen

| | Stufe A | Stufe B |
|---|---|---|
| Fragt | Ruft das Modell das Tool, kommt ein Rechte-Dialog, erscheint das Panel? | Baut Desktop das Panel beim Wiederöffnen auf, und reagieren die Bedienelemente? |
| Neuer Prompt | ja, aus `evals/panel-beispiele.json` | nein |
| Kostet | einen Chat je Tool im Konto, rund 30 s je Tool | rund 15–50 s je Tool |
| Ergebnis schwankt | ja, das Modell entscheidet | nein |

Stufe A merkt sich je Tool den Chat-Titel (im Container des Test-Runners); Stufe B öffnet den Chat
darüber. Ohne vorherigen A-Lauf meldet B „erst run.sh A <tool>“.

## Dateien

- `Tests/Probe.swift` — Checkpoint, Anhänge, Panel-Anker, Zustand zwischen A und B
- `Tests/StufeA.swift`, `Tests/StufeB.swift` — eine Testmethode je Panel-Tool
- `checkpoints.json` — die Schritte von Stufe B je Tool (und der Prompt für `export_anki_deck`)
- `run.sh` — Lease, Projekt erzeugen, Testplan schreiben, Lauf, Export
- `bericht.py` — baut aus den Anhängen `bericht.md`/`bericht.json`, Exit 1 bei Rot
- `out/<zeit>-<stufe>/` — nicht versioniert: `bericht.md`, `bilder/` (nur das Panel), `video/`
  (ganzer Bildschirm, ein Film je Tool), `baeume/` (Elementbäume), `ergebnis.xcresult`

Ein neues Panel-Tool braucht: Eintrag in `evals/panel-beispiele.json`, je eine `test_<tool>`-Zeile
in beiden Stufen, die Schritte in `checkpoints.json`.

## Regeln, die aus Fehlläufen stammen

- **Über Bedienungshilfen-Namen suchen, nicht über sichtbaren Text.** Der Knopf mit der Aufschrift
  „Export PNG“ heißt „Export as PNG“. Die Namen stehen im Elementbaum (`baeume/`), nicht im Bild.
- **Panel-Anker ist die WebView `MCP-UI Proxy`** im Chat. Die Gruppe darum heißt mal
  `<server> embed`, mal `<server>: <Titel>`.
- **Neuer Chat über das Menü** (File > New Chat), danach prüfen, dass der alte Chat weg ist. Das
  Antwortfeld eines offenen Chats trägt denselben Namen wie das Eingabefeld eines neuen; ohne die
  Prüfung landet der Prompt im alten Chat und der Lauf ist falsch grün.
- **Vor jedem Klick in den sichtbaren Bereich rollen.** Ein Klick auf ein nicht treffbares Element
  bricht den ganzen Test ab. Einträge unterhalb des sichtbaren Bereichs stehen mit 1 px Höhe im Baum.
- **Nie klicken:** die Knöpfe unter „Continue in chat“ (jeder schreibt eine Nachricht) und
  „Add a flashcard to the Anki deck …“ (ändert Anki).
- **Aufnahmen nie ins Repo.** Videos und Bäume zeigen die Seitenleiste mit privaten Chat-Titeln.
  Für draußen taugen nur die Bilder unter `bilder/` (Ausschnitt des Panels); die Verwertung gehört
  dem Schwester-Repo.

## Genutzte Apple-Doku

- `XCUIApplication(bundleIdentifier:)`, `activate()`, `wait(for:timeout:)` — fremde App steuern
- `XCUIElement.waitForExistence(timeout:)`, `waitForNonExistence(timeout:)` — Warten ohne Schleife
- `descendants(matching:)` + `matching(NSPredicate)` + `firstMatch` — Suche innerhalb des Panels
- `XCTContext.runActivity(named:block:)` — ein Checkpoint = eine Aktivität im Testbericht
- `XCTAttachment` mit `lifetime = .keepAlways`, `XCUIScreenshotProviding.screenshot()` — Bilder und
  Bäume aus der Sandbox des Runners holen (`xcrun xcresulttool export attachments`)
- `xcodebuild -only-testing:Ziel/Klasse/Methode` (man xcodebuild) — einzelne Tools wählen
- WWDC25/344 „Record, replay, and review: UI automation with Xcode“ — Videoaufnahme je Lauf; der
  Testplan-Schlüssel `preferredScreenCaptureFormat: screenRecording` ist gemessen, nicht dokumentiert
