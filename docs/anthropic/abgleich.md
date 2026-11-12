# Abgleich: was Anthropic veröffentlicht — und wo wir stehen

Stand 12.11.2026: `--check` 6 neu (ausgewertet in Abschnitt 6), 10 geändert — ausgewertet in Abschnitt 7;
ext-apps 2.0.4 und 2.1.0 gelesen, kein Bump nötig (Abschnitt 1).
Davor: Stand 06.11.2026 (Etappe E2, Mechanismus-Panel): `--check` 0 neu, 19 geändert, 0 weg — gelesen:
MCP-Apps-Schnellstart und `apps/build` nur Formatierung bzw. Node ≥ 20 im Beispiel (unser Panel baut
schon mit Node ≥ 20), Spezifikation `server/tools` nur ein verschobenes `annotations`-Beispiel;
ext-apps 2.0.4 ist ein Beispiel-Patch. Keine Folge für Hinweiszeile und ⇌ im Mechanismus-Panel.
Davor: Stand 24.10.2026; Remote-Panels und lokale Desktop-Pfade erneut geprüft (Abschnitt 5).
`--check`: 0 neue, 58 geänderte, 0 entfernte Seiten. Überwiegend Link-/Exportformatierung,
aber auch inhaltliche Änderungen an Verzeichnis-Veröffentlichung und OAuth-Verwaltung.
Keine Server-, Panel- oder Abhängigkeitsänderung in dieser Etappe.
**Das ist unsere Auswertung in eigenen Worten**, keine Kopie. Die Quellen stehen in
`quellen.json`, ihre Fingerabdrücke in `stand.json`. Wer diese Datei anfasst, hat vorher
`uv run python scripts/anthropic_sync.py --check` laufen lassen und die geänderten Seiten gelesen.

Pflege-Regel: Ändert sich eine Quelle, wird **hier** die Zeile angepasst, dann erst gebaut, dann
`--update`. Maßnahmen-Nummern (M…) tauchen in `plans/panel-ausbau.md` auf.

## 1. Versionen (das `--check` meldet sie jedes Mal)

| Baustein | unser Stand | neueste | Folge |
|---|---|---|---|
| `@modelcontextprotocol/ext-apps` | **^2.0.3** (migriert 03.10.2026; installiert 2.0.3) | **2.1.0** (10.11.2026) | **12.11.: kein Bump nötig.** 2.0.4 ändert nur Beispiele und Abhängigkeiten der Beispiele, keine Bibliotheks-API. 2.1.0 bringt die WebMCP-Brücke (Panel-Tools aus `App.registerTool` ↔ `document.modelContext`, ohne neue Nachrichten auf dem Draht, abschaltbar mit `webMcpBridge: false`) und lockert im Spezifikationsentwurf die Pflicht zum doppelten Sandbox-iframe. Wir registrieren keine App-Tools (lokal ohnehin wirkungslos, Nr. 20); `^2.0.3` würde 2.1.0 beim nächsten `npm install` ohne Lockfile-Pin zulassen, das Lockfile hält 2.0.3. **M0 erledigt:** Protokoll auf dem Draht unverändert (2.x-Panels laufen in 1.x-Hosts und umgekehrt, vom Hersteller getestet). Gebrochen waren nur Abhängigkeiten (`client` ^2 statt `sdk` ^1, `zod` ^4.2, Node ≥ 20); unser Panel braucht dafür **keine Codeänderung** (nutzt ext-apps an einer Stelle: `useApp`). Bundle 524 → 399 kB. 2.0.1 bis 2.0.3 sind Beispiel-Patches, an der Bibliothek ändert sich nichts. |
| MCP-Spezifikation | – | Fassung **2026-07-28** | **M0b erledigt:** zustandslos (kein `initialize` mehr), `server/discover`, Pflichtfeld `resultType`, Cache-Hinweise `ttlMs`/`cacheScope`, Roots/Sampling/Logging als veraltet markiert. Das setzt das Python-`mcp` 2.x für uns um (Plan mcp-2-migration, geparkt); ältere Server bleiben nutzbar (Clients behandeln fehlendes `resultType` als vollständig). Für uns jetzt nichts zu tun; Sampling nutzen wir nicht. |
| Python `mcp` | `>=2.3,<3`; installiert 2.3.0 | 2.3.0 | Arbeitsbaum und installierte Umgebung am 24.10. geprüft; die Release-Dateien sind fremde, uncommittete Arbeit. Die Meldung „neuere Nebenversion“ des Prüfers vergleicht `2.3` mit `2.3.0` und belegt hier kein Update. |
| `@anthropic-ai/mcpb` (Bau) | 2.1.2 | 2.1.2 | aktuell |

## 2. Fähigkeiten und Regeln im Abgleich

Status: ✓ erfüllt · ◐ teilweise · ✗ fehlt · ? ungeprüft · ⚠ Spannung

| # | Was Anthropic sagt | Quelle | Unser Stand | Maßnahme |
|---|---|---|---|---|
| 1 | Panel soll Claudes Farben und Schrift (Anthropic Sans) übernehmen: durchsichtiger Hintergrund, `color-scheme`-Meta, Host-Variablen über die mitgelieferten Helfer, Rahmen vom Host | theming, design-guidelines | ✗ eigene Variablen, kein Meta, kein `prefersBorder` | **M1** (größter Hebel für „sauberer") |
| 2 | Ergebnisse ab ca. 150.000 Zeichen werden bei aktiver Code-Sandbox als Datei abgelegt, das Panel lädt dann **gar nicht** | troubleshooting | ? nie gemessen | **M2:** Größen messen (3D-SVG, Mechanismus, Plots, Stapel), Großes per `callServerTool` nachladen |
| 3 | Werkzeuge brauchen `title` und `readOnlyHint`/`destructiveHint` (für die Einreichung Pflicht, auch sonst Konvention) | submission | ✓ 24 von 24 (12.11.2026, `8a81068`: `_TOOL_LABELS` in `server.py`; schreibende Tools nicht lesend, `export_anki_deck` destructive) | erledigt — Wirkung auf Freigabe-Klicks misst der Handtest U5 |
| 4 | Ressource trägt MIME `text/html;profile=mcp-app` | quickstart | ✓ | — |
| 5 | Für lokale stdio-Server gibt es kein `ui.domain` — das Feld darf nicht gesetzt sein | troubleshooting | ✓ nicht gesetzt | — |
| 6 | Jeder Aufruf öffnet ein eigenes Panel, alte bleiben aktiv und können weiter an Claude schicken; Ablösung über Schlüssel `{createdAt, seq}` aus dem Server + `BroadcastChannel` | instance-supersession | n/a (Panels ohne Zustand) | **M5** erst beim Quiz-/Prüfmodus |
| 7 | `ui/open-link` zeigt **immer** ein Bestätigungsfenster; die Ausnahmeliste gilt nur für Verzeichnis-Connectors | external-links | ? Links im Panel prüfen | Hinweis im README; Ziel-URL im Panel klar anzeigen |
| 8 | Vollbild (`ui/request-display-mode`), Karussell (3–8 Karten), Skelett statt Spinner, 44-pt-Tippflächen, Sicherheitsränder. Claude bietet nur `inline` und `fullscreen` (Seitenpanel meldet ebenfalls `fullscreen`); `pip` nennt die Seite seit 12.11. nicht mehr | design-guidelines, display-modes | ◐ eigener Vergrößern-Knopf und Layout nach gemeldeter Größe gebaut (bis `c45fdff`), Platzhalter aus `toolinput`; Karussell, Tippflächen, Sicherheitsränder offen | **M6** (Plan Phase 2–4) |
| 9 | Claude baut eigene Inline-Grafiken und Auswahlfragen (Quiz mit Antippen) | Blog „interactive visuals" | wir regen es nicht an | **M9:** ein Satz in den `instructions`, im Eval messen |
| 10 | Desktop-Extension (.mcpb): Node.js wird empfohlen, Plattformen `darwin`/`win32`, Icon 512 px (mind. 256), `user_config` für Einstellungen | mcpb | ◐ Python-Server; Plattformen `darwin`, `linux`; **kein Icon**; kein Windows | **M7:** Icon, Windows-Test oder Windows ausdrücklich ausschließen |
| 11 | Organisationen können Extensions sperren oder auf eine Liste beschränken | add-unlisted | nicht im README | **M8:** ein Satz im README |
| 12 | `privacy_policies` (Manifest ≥ 0.2, HTTPS) und README-Abschnitt „Privacy Policy" — verlangt die Einreichung lokaler Connectors | submission | ✗ | **M7b**, klein, auch ohne Einreichung gute Praxis |

## 3. Verzeichnis und Verteilung — geprüfte Lage

Belegt am Originaltext (03.10.2026):

- **Als eigenständiger Connector ist ein lokaler Server nicht einreichbar** — das Verzeichnis verlangt eine HTTPS-URL.
- **Desktop-Extensions (.mcpb) nimmt das Verzeichnis nicht mehr an**; Listings dafür gelten als veraltet.
- Der Weg für lokale Server ist ein **Plugin-Bundle** aus einem öffentlichen GitHub-Repository. Aber: Ein lokaler Server aus einem Plugin
  **läuft in Claude Code und in Cowork-Sitzungen, nicht im normalen Chat** — dort, wo unser Panel heute erscheint.
- Die offene MCP-Registry macht einen Server in Claude **nicht** sichtbar; nur ein Verzeichnis-Eintrag lässt Claude ihn vorschlagen.

**Folge (präzisiert am 24.10.):** Die Doppelklick-Extension ist ein dokumentierter lokaler Panel-Weg,
hat aber einen gemeldeten Desktop-Routingfehler (Abschnitt 5). Die Aussage „kein Panel im Chat“ oben
betrifft lokale Plugin-Server, nicht Remote-Connectors: Diese können auch ohne Verzeichnis-Eintrag
als Custom Connector Panels in Web und Desktop liefern. Eine **gehostete Variante** wäre eine eigene
Betriebsentscheidung; zum Entwicklertest reicht auch ein lokal laufender HTTP-Server mit öffentlichem
Tunnel. In diesem Abgleich wurde weder Hosting eingerichtet noch ein Tunnel geöffnet.

Zwei Dinge aus den Prüfkriterien, die nur bei einer Einreichung zählen: Beschreibungen dürfen Claudes Verhalten nicht
lenken (unsere `instructions` „Reach for these tools …" tun das bewusst und sind gemessen); Diagramme und Charts sind erlaubt.

## 4. Was das für die Reihenfolge der Arbeit heißt

1. **M0 ext-apps 2.0 und neue MCP-Fassung lesen** — bevor das Panel weiter wächst, sonst bauen wir auf der alten Hauptversion weiter.
2. **M1 nativer Look**, **M3 Annotationen**, **M2 Größenmessung** — klein, jeder für sich prüfbar.
3. Danach die Reiter und der Rest aus `plans/panel-ausbau.md`.

- 21.10.2026: 12 Spezifikationsseiten (tools, resources, changelog, stdio, deprecated) als GEÄNDERT gemeldet; Stichprobe tools.md/changelog.md: nur Umstellung MDX → Markdown (`<Note>` → `> [!NOTE]`), kein inhaltlicher Unterschied. Kein Handlungsbedarf für die Panel-Knöpfe (Faden 1, plans/workflows.md).

## 5. Nachprüfung am 24.10.2026: Remote-Connector und lokales Panel

### Umfang der Quellenänderung

Die fünf Pflichtseiten wurden vollständig gelesen: [Custom Connector hinzufügen](https://claude.com/docs/connectors/custom/add-unlisted.md),
[Panel-Fehlersuche](https://claude.com/docs/connectors/building/mcp-apps/troubleshooting.md),
[MCP-Apps-Einstieg](https://claude.com/docs/connectors/building/mcp-apps/getting-started.md),
[Connector testen](https://claude.com/docs/connectors/building/testing.md) und
[MCP-Standard: App bauen](https://modelcontextprotocol.io/extensions/apps/build.md).
Der verkürzte Auftragspfad `mcp-apps/getting-started.md` entspricht im Quellenindex
`connectors/building/mcp-apps/getting-started.md`.

`--diff URL` für alle fünf sowie `authentication.md` und `submission.md`:
Die Pflichtseiten ändern Links von relativen Pfaden zu absoluten Markdown-URLs;
die MCP-Bauanleitung exportiert zusätzlich Bildunterschriften. Darüber hinaus wurden
die alten und aktuellen Texte aller 58 erfassten Seiten verglichen. Inhaltliche
Reständerungen liegen in vier Seiten: `authentication.md`, `directory-vs-custom.md`,
`managing-your-listing.md`, `submission.md`:

- **OAuth-Verwaltung:** Anthropic-gehaltene Client-ID/Secrets werden nun im Entwicklerportal
  eingetragen und bearbeitet; dokumentiert sind Vorrangregeln zwischen Organisations-,
  Entwickler- und Anthropic-Client sowie Einschränkungen älterer Verbindungen. Custom
  Connectors verwenden das im Verzeichnisportal hinterlegte Client-Secret nicht.
- **Verzeichnis:** Listings mit mehreren URLs oder URL-Muster können erst mit dem
  Verified-Label veröffentlicht werden. Das betrifft keine einzelne Custom-Connector-URL.

Quellen: [Authentifizierung](https://claude.com/docs/connectors/building/authentication.md),
[Custom vs. Verzeichnis](https://claude.com/docs/connectors/building/directory-vs-custom.md),
[Listing verwalten](https://claude.com/docs/connectors/building/managing-your-listing.md),
[Einreichung](https://claude.com/docs/connectors/building/submission.md).
Damit ist „nur Massen-Formatänderung“ für den gesamten Abgleich falsch; für die fünf
Pflichtseiten wurde keine neue Funktionsaussage gefunden. Die Paketstände bleiben
ext-apps 2.0.3, mcpb 2.1.2 und Python mcp 2.3.0.

### a) Remote-MCP per HTTPS, ohne Anmeldung: Panels in Web und Desktop?

**Ja, als dokumentierter Weg.** Die [MCP-Bauanleitung, „Testing with Claude“](https://modelcontextprotocol.io/extensions/apps/build.md#testing-with-claude)
sagt ausdrücklich: „[Claude](https://claude.ai) (web) and [Claude Desktop](https://claude.ai/download) support MCP Apps.“
Sie führt anschließend über eine öffentliche Tunnel-URL zu **Add custom connector**;
ihr HTTP-Beispiel implementiert keine Authentifizierung.
Anthropics [Testanleitung](https://claude.com/docs/connectors/building/testing.md) bestätigt
dieselbe Laufzeit für Custom- und Verzeichnis-Connectors — seit 12.11. „with an exception for MCP Apps“
(eingebettete Seiten, Einstiegspunkte; Abschnitt 7) — und empfiehlt den Tunnelweg auch für MCP Apps. Ein Directory-Listing ist somit keine Voraussetzung.

Die [Custom-Connector-Anleitung, „Choose authentication settings“](https://claude.com/docs/connectors/custom/add-unlisted.md#choose-authentication-settings)
nennt eine HTTPS-MCP-Adresse und die Option **No sign-in**: „anyone with access to the server URL can use the connector“.
Folgerung aus diesen Quellen: OAuth ist keine Panel-Voraussetzung. Das bestätigt den
vorgesehenen Integrationsweg, noch keinen realen chemdraw-Paneltest in beiden Clients.
Anthropics Testanleitung empfiehlt für öffentliche Tunnel weiterhin Authentifizierung.
Die MCP-Bauanleitung beschränkt Custom Connectors noch auf bezahlte Tarife; die aktuellen
Anthropic-Seiten nennen auch Free (dort ein Custom Connector). Bei diesem Widerspruch
gilt für die Tarifauskunft die aktuelle Anbieter-Dokumentation.

### b) Lokale stdio-Server, Cowork und `local-agent-mode`

**Offiziell weiterhin dokumentiert, mit offenem Fehlerbericht zum Host-Routing.**
Anthropics [MCP-Apps-Einstieg](https://claude.com/docs/connectors/building/mcp-apps/getting-started.md)
zeigt lokale `npx … --stdio`-Einträge in `claude_desktop_config.json` und sagt nach
der Freigabe: „the MCP App renders inline in the conversation“.
Die [Fehlersuche](https://claude.com/docs/connectors/building/mcp-apps/troubleshooting.md#ui-domain-validation-fails)
behandelt lokale stdio-Connectors ausdrücklich; ohne Server-URL muss `ui.domain` entfallen.
Keine der fünf Pflichtseiten dokumentiert ein absichtliches Verwerfen von `_meta.ui`
oder verspricht eine funktionierende Panel-Weiterleitung über `local-agent-mode`/Cowork.

[Issue #1069](https://github.com/anthropics/claude-ai-mcp/issues/1069) ist am Prüftag offen.
Der ursprüngliche Windows-Bericht beschreibt, dass die lokale Bridge Tool-Metadaten
neu aufbaut: „The server's `_meta.ui` is not carried over.“ Die Resource wird deshalb
nicht angefordert; derselbe Server rendere über den HTTP-Custom-Connector-Weg.
Ein [macOS-Bericht vom 15.10.](https://github.com/anthropics/claude-ai-mcp/issues/1069#issuecomment-6203695984)
für Desktop 2.42304.0 unterscheidet zwei Verbindungen zur gleichen Python-stdio-Extension:
`claude-ai` fordert die UI an und rendert, `local-agent-mode-<name>` dagegen nicht;
das Log dazu lautet „text only, no view“. Beide melden UI-Fähigkeit im Handshake.
Der Bericht beobachtet einen Wechsel im selben Chat sowie funktionierende Panels im
Inkognito-Chat. Ein [weiterer macOS-Kommentar](https://github.com/anthropics/claude-ai-mcp/issues/1069#issuecomment-6201871260)
vermutet einen Zusammenhang mit dem automatischen Chat-/Cowork-Wechsel.

**Beweisgrenze:** Das sind konkrete Nutzerberichte, keine Anthropic-Bestätigung der
Ursache, kein zugesagter Fix und keine hier wiederholte Messung an Jays Desktop.
Insbesondere sind „stdio grundsätzlich nicht unterstützt“ und „Cowork verwirft immer
`_meta.ui`“ nicht belegt. Nächste technische Abnahme: denselben Panel-Aufruf je Clientpfad
mit `resources/read ui://…` im Serverlog und sichtbarem Panel prüfen; ein erfolgreicher
Handshake oder Referenzhost allein beweist diese Desktop-Strecke nicht.

**Nachtrag 12.11.:** Die Panel-Fehlersuche empfiehlt jetzt selbst genau diesen Vergleich („App stays invisible
with no cause found“): lokalen Server zusätzlich per Streamable HTTP als Custom Connector anbinden und denselben
Aufruf auf beiden Verbindungen vergleichen, Tunnel ohne Anmeldung sofort wieder schließen. Unser Server spricht
nur stdio (`mcp.run(transport="stdio")`); der Vergleich bräuchte einen HTTP-Startmodus — erst, wenn der Handtest
U5 ein unsichtbares Panel ohne Ursache zeigt.

## 6. Nachprüfung am 11.11.2026: Seitenpanel, Vollbild und vier neue Panel-Schnittstellen

`--check` meldete 6 neue und 10 geänderte Seiten; ext-apps 2.1.0 (10.11.) bringt nur die WebMCP-Brücke. Gelesen:
`display-modes`, `app-tools`, `send-messages`, `download-files`, `entry-points`, `instance-supersession`, dazu die
Diffs von `design-guidelines` und `troubleshooting`. Anlass: Jays Desktop zeigt das Panel seit dem Update im Seitenpanel.

| # | Was Anthropic sagt | Quelle | Unser Stand am 11.11. | Maßnahme |
|---|---|---|---|---|
| 13 | Drei Orte: Chat (`inline`), Seitenpanel und Vollbild (beide melden `fullscreen`). Ohne `availableDisplayModes` gilt ein Panel als „kann beides“, Claude zeigt dann selbst einen Vergrößern-Knopf | display-modes | Knopf erscheint, Layout wertet nichts aus: Zeichenfläche fest 320 px, Breite bei 1000 px gedeckelt | **M10:** Layout nach `containerDimensions`, nicht nach Modus; `availableDisplayModes` bleibt undeklariert |
| 14 | `containerDimensions`: im Chat `width` + `maxHeight`, in `fullscreen` `width` + `height`; bei jedem `hostcontextchanged` neu auslegen. Seitenpanel öffnet mit halber Chatbreite, Minimum etwa 320 px; `safeAreaInsets` an der Chat-Kante | display-modes, design-guidelines | nicht gelesen | **M10:** Höhe füllen nur, wenn `height` gemeldet ist; der Chat-Weg bleibt inhaltsgroß (Auto-Resize) |
| 15 | `requestDisplayMode("fullscreen")` nur aus Klick/Tastendruck mit Fokus; öffnet das Seitenpanel, wo es eines gibt. Ohne Seitenpanel soll das Panel einen eigenen Vollbild-Knopf behalten | display-modes | kein eigener Knopf | **M10:** Knopf nur, wenn der Host `fullscreen` anbietet und das Panel `inline` ist |
| 16 | `_meta.ui.preferredDisplayMode: "fullscreen"` an der Ressource öffnet das Panel ohne Klick im Seitenpanel (Claude-Erweiterung, nicht Teil der Spezifikation) | display-modes | nicht gesetzt | **offen:** alle 13 Panel-Tools teilen eine Ressource, es träfe auch TLC und Anki. Erst nach dem Handtest entscheiden |
| 17 | Ein neuer Tool-Aufruf desselben Konnektors ersetzt das Panel im Seitenpanel; das alte fällt in den Chat zurück (`inline`) und bleibt aktiv | display-modes, instance-supersession | Panels je Ergebnis, kein gemeinsamer Zustand | Modellkontext und Nachrichten nur aus einem Klick senden, dann gewinnt das zuletzt bediente Panel; keine `BroadcastChannel`-Wahl |
| 18 | `app.sendMessage`: nur aus Klick, nur Text, höchstens 8000 Zeichen; der Nutzer bestätigt oder schickt selbst ab. Ein Ergebnis ohne Fehler belegt nicht, dass Claude gelesen hat | send-messages | nicht genutzt | **M11:** Knöpfe zum Weitermachen, nur wenn der Host `message` anbietet; Knopf bleibt wiederholbar |
| 19 | `app.updateModelContext` legt Panel-Zustand in Claudes Kontext | SDK, instance-supersession | nicht genutzt | **M12:** Auswahl (Gruppe/Atom) und Ansicht melden, nur wenn der Host es anbietet |
| 20 | App-Tools (`app.registerTool`): Claude verändert das offene Panel. **Nur bei Remote-Konnektoren** – „Claude doesn't call the tools of a view from a local server“ – und nur für einen Teil der Organisationen | app-tools | lokal (stdio) | **entfällt**, solange der Server lokal läuft; wird mit einem Remote-Konnektor (Abschnitt 5a) neu bewertet |
| 21 | Einstiegspunkte auf der Artifacts-Seite: nur Remote-Konnektoren, verifiziert oder eigen | entry-points | lokal | entfällt |
| 22 | `app.downloadFile`: Datei speichern über einen Claude-Dialog; `<a download>` und `blob:` gehen in der Sandbox nicht. Vorher `getHostCapabilities().downloadFile` prüfen | download-files | Export geht über `save_png` nach `~/ChemDraw-Output` | zurückgestellt: `save_png` funktioniert, kein Auftrag |

Ungeprüft bleibt, was Jays Desktop tatsächlich anbietet (`getHostCapabilities()`, `hostContext` je Ort): das klärt der
Desktop-Handtest. Bis dahin ist jede neue Schnittstelle hinter ihrer Fähigkeitsprüfung gebaut.

## 7. Nachprüfung am 12.11.2026: zehn geänderte Seiten

Alle zehn per `--diff` gelesen. Gemeinsamer Kern: Seitenpanel, App-Tools, Einstiegspunkte und eingebettete Seiten
sind in die Bestandsseiten eingearbeitet; Einstiegspunkte und eingebettete Seiten gibt es bei Verzeichnis-Connectors
nur noch mit Verified-Label. Für einen lokalen, nicht gelisteten Server folgt daraus wenig.

| Seite | Was sich geändert hat | Folge für uns |
|---|---|---|
| mcp-apps/getting-started | Neue Übersicht „What an MCP App can do“; Remote-Pflicht für App-Tools, Einstiegspunkte, eingebettete Seiten. Freigabe heißt jetzt **Allow once** / **Always allow**; steht die Berechtigung im Eingabefeld auf **Auto**, zeigt Claude das Panel ohne Rückfrage | **Handtest U5:** Freigabe-Dialog mit den neuen Namen beschreiben und die Einstellung **Auto** notieren, sonst ist die Wirkung der Annotationen (Nr. 3) nicht von „Auto“ zu trennen |
| mcp-apps/troubleshooting | Neuer Abschnitt: unsichtbares Panel ohne Ursache → lokalen Server zusätzlich per HTTP als Custom Connector vergleichen | in §5b nachgetragen; HTTP-Startmodus erst bei Bedarf |
| mcp-apps/design-guidelines | Seitenpanel-Abschnitt (≈ halbe Chatbreite, min. ≈ 320 px, meldet `fullscreen`); Modi nur noch `inline`/`fullscreen`, kein `pip`; CSP-Felder erklärt, `baseUriDomains` wird ignoriert, `frameDomains` nur mit Freigabe | Nr. 8 korrigiert; Seitenpanel deckt §6 (Nr. 13–15) schon ab. Wir setzen keine CSP-Felder — ohne Folge |
| testing | „exact same runtime“ → Ausnahme für MCP Apps (eingebettete Seiten, Einstiegspunkte); bei Team/Enterprise trägt ein Owner den Custom Connector ein | §5a korrigiert; sonst ohne Folge |
| directory-vs-custom | Zwei Zeilen: eingebettete Seiten und Einstiegspunkte im Verzeichnis nur mit Verified-Label, als Custom ohne Listing | gelesen, ohne Folge (lokal, kein Listing) |
| review-criteria | Label ändert jetzt, ob eingebettete Seiten und Einstiegspunkte verfügbar sind | gelesen, ohne Folge |
| verification | gleiche Aussage wie review-criteria: das Label wirkt auch auf Funktionen, nicht nur auf die Anzeige | gelesen, ohne Folge |
| custom/add-unlisted | Dialog neu: Name + URL, dann Anmeldeart (Vorschläge als **Detected** markiert), danach **Connect**; Option „No sign-in“ und Free-Tarif bleiben | gelesen, ohne Folge; §5a bleibt richtig (wichtig erst für einen Remote-Test) |
| enterprise-managed-auth | Test eines gelisteten Servers unter anderer URL bzw. per Mail-Freischaltung | gelesen, ohne Folge (keine Anmeldung, kein Listing) |
| mcp-apps/quickstart | ein neuer Link unter „Next steps“ | gelesen, ohne Folge |
