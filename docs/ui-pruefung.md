# UI prüfen und Fehler eingrenzen

Stand 14.10.2026: überarbeitete MVP-UI im echten Desktop-Chat selbst geprüft:
Koffein-Struktur, HBD 0, Data mit CID 2519/CAS 58-08-2 und PNG-Export erfolgreich.
Der exportierte PNG-Inhalt stimmt pixelweise mit der Ausgangsabnahme überein.
Der vollständige Testlauf besteht mit 6.958 Python- und 40 Frontendtests.
Layoutbelege: [schmal hell](produkt/panel-mvp/schmal-hell.png),
[breit dunkel](produkt/panel-mvp/breit-dunkel.png),
[Datenblatt schmal](produkt/panel-mvp/daten-schmal-hell.png).

Alle Projektbefehle laufen aus `~/Documents/projects/chemdraw-mcp`.

## Schnelle automatische Schleife

```bash
npm --prefix chemdraw_tool/ui run test:ui:watch
```

Beobachtet die React-DOM-Tests und wiederholt sie nach Änderungen. Sie prüfen
unter anderem Ansichtswechsel, Fehlerzustände, Molekülidentität und Bedienung.
Die Schleife wurde tatsächlich gestartet und durch eine Änderung des
Dateizeitstempels von `MoleculeView.jsx` ausgelöst: die elf betroffenen Tests
liefen automatisch erneut grün. Anschließend wurde der Watchprozess beendet.
Die bestehenden Utility-Tests haben separat `npm --prefix chemdraw_tool/ui run test:watch`.

Nach Layoutänderungen Bundle bauen und den echten Server hinter dem nachgebauten
Host prüfen:

```bash
npm --prefix chemdraw_tool/ui run build
npm --prefix chemdraw_tool/ui run test:host
```

Dieser Browser-Test verwendet die SDK-AppBridge und ein Sandbox-iframe. Er
prüft Struktur und Datenblatt hell/dunkel bei 360 und 980 px, explizite
Host-Themes, horizontales Abschneiden, Datenabruf und Cache. Screenshots landen
im temporären Verzeichnis als `chem-ui-*.png` bzw. `chem-ui-data-*.png`.
Der PubChem-Abruf braucht Netz; ein fehlschlagender Abruf ist von einem
Layoutfehler zu unterscheiden. Diese Prüfungen führen keine Modellaufrufe aus.

Vor einem abgeschlossenen Schritt zusätzlich `./test.sh`: Lint, vollständiger
Pythonbestand, bytegleicher Bundle-Neubau, DOM-/Utilitytests und eingefrorener
PNG-Vergleich. `dist/` wird ausgeliefert, nicht `src/`.

## Was Claude Desktop zur Diagnose anbietet

In der tatsächlich installierten App geprüft am 14.10.2026:
**Einstellungen → Entwickler → ChemDraw MCP (unofficial)** zeigt den Status,
den `/bin/sh`-Starter und „Protokolle anzeigen“.

Die für dieses Projekt relevanten Dateien sind:

- `~/Library/Logs/Claude/mcp.log` — Verbindungen und Hostfehler.
- `~/Library/Logs/Claude/mcp-server-ChemDraw MCP (unofficial).log` — stderr des Servers.
- `~/ChemDraw-Output/server.log` — zusätzliches Logging unseres Servers.

Zum laufenden Mitlesen:

```bash
tail -n 40 -F "$HOME/Library/Logs/Claude/mcp-server-ChemDraw MCP (unofficial).log"
```

Logs sind Diagnosematerial: Eine erfolgreiche Anfrage beweist noch keine sichtbare,
richtige Darstellung. Die derzeitigen SDK-Debugzeilen nennen teils nur
`CallToolRequest`, nicht den konkreten Toolnamen. Für eine Abnahme daher auch
CAS/CID, sichtbare Ansicht und Export prüfen.

Die offizielle MCP-Dokumentation beschreibt außerdem Chrome DevTools über
`~/Library/Application Support/Claude/developer_settings.json` mit
`"allowDevTools": true` und anschließend `⌘⌥I`. Auf ausdrücklichen Auftrag von Jay
am 14.10.2026 aktiviert: die zuvor nicht vorhandene Datei angelegt, Claude komplett
neu gestartet, das neue Menü **Entwickler** und das tatsächliche Fenster
**Developer Tools - https://claude.ai/new** mit **Console** und **Network** geprüft.
Das Entwicklermenü bietet außerdem „MCP-Protokolldatei öffnen“ und
„MCP-Konfiguration neu laden“. Bei späteren Änderungen vorhandene
JSON-Einstellungen erhalten und vorher sichern. Console und Network
helfen bei Host-/iframe-Fehlern, ersetzen aber keine Testassertionen.

Quellen: [MCP-Debugging](https://modelcontextprotocol.io/docs/tools/debugging),
[Claude Desktop: lokale MCP-Server](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).
Der [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) bietet
zusätzlich eine maschinenlesbare CLI für Protokolltests; `scripts/handshake.sh`
nutzt sie bereits.

## Installation und sichtbare Abnahme

Ein frischer Repo-Test aktualisiert weder das installierte Wheel noch einen
laufenden Desktop-Prozess. Nach einer Installation den Code aus der installierten
Umgebung mit ihrem eigenen Python und `-I` prüfen; sonst kann das aktuelle
Projektverzeichnis versehentlich den Repo-Code importieren. Danach Desktop
vollständig beenden und neu öffnen. Keine zweite MCP-Registrierung neben der
bestehenden Extension anlegen.

Der normale `handshake.sh` kann mangels passendem JSON-Eintrag auf den Repo-Start
zurückfallen. Für den Installationsnachweis deshalb den tatsächlich in den
Entwicklereinstellungen angezeigten Extension-Starter verwenden.

Sichtbarer Test: neuer Chat → „Nutze den ChemDraw-MCP: Zeichne caffeine mit dem
Label Koffein“ → Structure → Data → zurück → Export PNG. Erfolg heißt:
Struktur sichtbar, CID 2519, CAS 58-08-2, HBD 0; der Export bestätigt Speichern
oder Kopieren und liefert ein überprüfbares Bild.
