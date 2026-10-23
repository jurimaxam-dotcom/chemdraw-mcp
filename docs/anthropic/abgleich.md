# Abgleich: was Anthropic veröffentlicht — und wo wir stehen

Stand 24.10.2026; Remote-Panels und lokale Desktop-Pfade erneut geprüft (Abschnitt 5).
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
| `@modelcontextprotocol/ext-apps` | **^2.0.3** (migriert 03.10.2026) | 2.0.3 | **M0 erledigt:** Protokoll auf dem Draht unverändert (2.x-Panels laufen in 1.x-Hosts und umgekehrt, vom Hersteller getestet). Gebrochen waren nur Abhängigkeiten (`client` ^2 statt `sdk` ^1, `zod` ^4.2, Node ≥ 20); unser Panel braucht dafür **keine Codeänderung** (nutzt ext-apps an einer Stelle: `useApp`). Bundle 524 → 399 kB. 2.0.1 bis 2.0.3 sind Beispiel-Patches, an der Bibliothek ändert sich nichts. |
| MCP-Spezifikation | – | Fassung **2026-07-28** | **M0b erledigt:** zustandslos (kein `initialize` mehr), `server/discover`, Pflichtfeld `resultType`, Cache-Hinweise `ttlMs`/`cacheScope`, Roots/Sampling/Logging als veraltet markiert. Das setzt das Python-`mcp` 2.x für uns um (Plan mcp-2-migration, geparkt); ältere Server bleiben nutzbar (Clients behandeln fehlendes `resultType` als vollständig). Für uns jetzt nichts zu tun; Sampling nutzen wir nicht. |
| Python `mcp` | `>=2.3,<3`; installiert 2.3.0 | 2.3.0 | Arbeitsbaum und installierte Umgebung am 24.10. geprüft; die Release-Dateien sind fremde, uncommittete Arbeit. Die Meldung „neuere Nebenversion“ des Prüfers vergleicht `2.3` mit `2.3.0` und belegt hier kein Update. |
| `@anthropic-ai/mcpb` (Bau) | 2.1.2 | 2.1.2 | aktuell |

## 2. Fähigkeiten und Regeln im Abgleich

Status: ✓ erfüllt · ◐ teilweise · ✗ fehlt · ? ungeprüft · ⚠ Spannung

| # | Was Anthropic sagt | Quelle | Unser Stand | Maßnahme |
|---|---|---|---|---|
| 1 | Panel soll Claudes Farben und Schrift (Anthropic Sans) übernehmen: durchsichtiger Hintergrund, `color-scheme`-Meta, Host-Variablen über die mitgelieferten Helfer, Rahmen vom Host | theming, design-guidelines | ✗ eigene Variablen, kein Meta, kein `prefersBorder` | **M1** (größter Hebel für „sauberer") |
| 2 | Ergebnisse ab ca. 150.000 Zeichen werden bei aktiver Code-Sandbox als Datei abgelegt, das Panel lädt dann **gar nicht** | troubleshooting | ? nie gemessen | **M2:** Größen messen (3D-SVG, Mechanismus, Plots, Stapel), Großes per `callServerTool` nachladen |
| 3 | Werkzeuge brauchen `title` und `readOnlyHint`/`destructiveHint` (für die Einreichung Pflicht, auch sonst Konvention) | submission | ✗ 0 von 23 | **M3:** alle 23 annotieren (alle lesend bzw. schreiben nur nach `~/ChemDraw-Output`) — im Tool-Snapshot sichtbar |
| 4 | Ressource trägt MIME `text/html;profile=mcp-app` | quickstart | ✓ | — |
| 5 | Für lokale stdio-Server gibt es kein `ui.domain` — das Feld darf nicht gesetzt sein | troubleshooting | ✓ nicht gesetzt | — |
| 6 | Jeder Aufruf öffnet ein eigenes Panel, alte bleiben aktiv und können weiter an Claude schicken; Ablösung über Schlüssel `{createdAt, seq}` aus dem Server + `BroadcastChannel` | instance-supersession | n/a (Panels ohne Zustand) | **M5** erst beim Quiz-/Prüfmodus |
| 7 | `ui/open-link` zeigt **immer** ein Bestätigungsfenster; die Ausnahmeliste gilt nur für Verzeichnis-Connectors | external-links | ? Links im Panel prüfen | Hinweis im README; Ziel-URL im Panel klar anzeigen |
| 8 | Vollbild (`ui/request-display-mode`), Karussell (3–8 Karten), Skelett statt Spinner, 44-pt-Tippflächen, Sicherheitsränder | design-guidelines | ✗ | **M6** (Plan Phase 2–4) |
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
Anthropics [Testanleitung](https://claude.com/docs/connectors/building/testing.md) bestätigt:
„Custom connectors use the exact same runtime as directory connectors“ und empfiehlt
den Tunnelweg auch für MCP Apps. Ein Directory-Listing ist somit keine Voraussetzung.

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
