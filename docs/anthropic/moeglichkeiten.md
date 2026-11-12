# Möglichkeiten: wie Server, Panel, Claude und Nutzer zusammenspielen

Stand 11.11.2026. Reine Bestandsaufnahme, baut auf `abgleich.md` (Abschnitte 2 und 6) auf, ohne ihn zu
wiederholen. Gelesen: alle `.cache/anthropic/*.md`, dazu die aktuellen Fassungen der sechs neuen
MCP-Apps-Seiten (`--diff`), die SDK-Typen von ext-apps 2.0.3 (`app.d.ts`, `spec.types.d.ts`, `react/*.d.ts`),
das installierte Python-`mcp` 2.3.0, die Spezifikation 2026-07-28 (Tools, Ressourcen, Prompts, Elicitation)
und das Desktop-Log `~/Library/Logs/Claude/mcp-server-chemdraw.log` (nur gelesen).

**Spalte „Lokal?“** = geht das bei unserem lokalen stdio-Server in Claude Desktop:
**ja (Doku)** = Anthropic beschreibt es ohne Remote-Bedingung · **ja (gemessen)** = bei uns beobachtet ·
**nein** = Quelle schließt es aus (Zitat) · **ungeprüft** = keine Quelle für den lokalen Fall, Messweg genannt.
Wichtig: `getting-started` nennt die Remote-Bedingung ausdrücklich nur für drei Dinge — „app tools, entry points,
and embedded websites need a connector that's backed by a remote server“. Für Seitenpanel, Nachrichten und
Downloads steht keine solche Bedingung; Seitenpanel, App-Tools und Einstiegspunkte sind zusätzlich „available to
a limited set of organizations, and not in every conversation“. Dass das Seitenpanel auf dem Gerät des
Besitzers erscheint, ist seine Beobachtung vom 11.11., keine Messung. GS sagt außerdem, Desktop starte die
Beispielserver lokal, und nur App-Tools, Einstiegspunkte und eingebettete Seiten seien mit eigenem Remote-Server zu testen.

**Stand 12.11.2026 (`c45fdff`):** gebaut sind inzwischen `sendMessage` (Zeile „Continue in chat“), `updateModelContext` (ein Besitzer, `ModelContext.jsx`), Layout nach gemeldeter Größe und `requestDisplayMode`, `toolinput`/`toolcancelled` (Platzhalter), Tool-`title` und Annotationen (24 von 24), `visibility: ["app"]` für `save_png` und vier Prompts. Die Spalte „Nutzen wir?“ in den Tabellen darunter zeigt für diese Zeilen noch den alten Stand; ob Desktop sie lokal ausführt, misst der Handtest U5.

**Spalte „Nutzen wir?“** gilt für Commit `0413183`. Im Arbeitsbaum liegt am 11.11. fremde, uncommittete Arbeit an
M10 (`useHostLayout.js`, `HostDiagnostics.jsx`, `requestDisplayMode` in `MoleculeView.jsx`) — nicht Teil dieser Recherche.

**Quellenkürzel:** DM display-modes · SM send-messages · DF download-files · AT app-tools · EP entry-points ·
ES embedded-sites · GS getting-started · DG design-guidelines · TS troubleshooting · IS instance-supersession ·
EL external-links · BI connectors/building/index · RC review-criteria · MB mcpb · WB what-to-build ·
PS plugins/platform-support · SDK ext-apps-Typen · SPEC MCP 2026-07-28 · PY Python-`mcp` 2.3.0 · LOG Desktop-Log.

## 1. Übersicht aller Wege

### Server → Claude (was das Modell sieht)

| Weg | Was er tut | Quelle | Lokal? | Nutzen wir? | Idee fürs Produkt | Aufwand | Haken |
|---|---|---|---|---|---|---|---|
| `instructions` | Ein Text vor allen Tool-Beschreibungen | PY, CLAUDE.md | ungeprüft, ob Desktop sie vor der Tool-Suche zeigt | ja, Bereichskarte | — | — | gemessen ist nur: vor der Tool-Suche kommen nur Namen an (CLAUDE.md, 0 von 8 am 10.11.) |
| Tool-Beschreibung + Schema | Wahl und Aufruf durch das Modell | SPEC tools | ja (gemessen) | ja, Snapshots | — | — | 2-KB-Kappung, semantische Nähe |
| Tool-`title` | Anzeigename für Menschen | SPEC tools, RC | ungeprüft (Anzeige) | nein (Snapshot hat kein `title`) | „Strukturformel zeichnen“ statt `generate_molecule` in der Freigabe | 1 h | Snapshot-Änderung je Tool |
| Annotationen `readOnlyHint`/`destructiveHint` | RC: „These determine auto-permissions in Claude. Read-only tools can run without per-call confirmation“ | RC, SPEC | Claude allgemein belegt, lokal ungeprüft | nein (0 von 24, abgleich Nr. 3 zählt noch 23) | Weniger Freigabe-Klicks bei Zeichnen/Nachschlagen | 2 h | Schreibende Tools (`~/ChemDraw-Output`, Anki) ehrlich als nicht-lesend markieren |
| Tool-/Server-`icons` | Bild neben Tool bzw. Server | SPEC, PY (`icons=`) | ungeprüft | nein | Erkennbarkeit in Konnektor-Liste | 1 h | nur mit Datei/URL; Desktop-Anzeige unbekannt |
| `structuredContent` + `outputSchema` | Maschinenlesbares Ergebnis neben dem Text | SPEC | ja (gemessen) | ja, 13 Panel-Tools (MVP) / 17 (voll) | — | — | Ergebnis ab ~150 000 Zeichen landet in der Sandbox, Panel lädt nicht (TS) |
| Bild-Inhalt im Ergebnis | `image`-Block, das Modell sieht das Bild | BI („image-based tool results“) | Claude allgemein belegt, lokal ungeprüft | nein: kein `image`-Block im Ergebnis | Claude prüft die eigene Zeichnung („stimmt die Stereochemie?“) und erklärt am Bild | 0,5 Tag | Tokenkosten je Aufruf; nur als Option |
| `resource_link` / eingebettete Ressource | Verweis bzw. Inhalt einer Ressource im Ergebnis | SPEC tools | ungeprüft | nein | Ausgabedatei als Ressource verlinken | 0,5 Tag | DF: Claude holt Links für Downloads nicht |
| Inhalts-Annotationen `audience`/`priority` | Block nur für Nutzer oder nur fürs Modell | SPEC resources | ungeprüft | nein | lange Datenblätter `audience: user`, Kurzfassung fürs Modell | 0,5 Tag | ob Desktop filtert, unbekannt |
| Fehler als Ergebnis (`isError`) | Modell korrigiert sich selbst | SPEC tools | ja (gemessen) | ja, `ToolError` mit `kind` | — | — | — |
| Prompts | Vom Nutzer gewählte Vorlagen („Slash-Befehle“) | SPEC prompts, BI („Your server can expose … prompts“) | Desktop fragt `prompts/list` ab (LOG: 29×), Anzeige ungeprüft | nein | „Stoff lernen“, „Mechanismus üben“, „Klausur-Karteikarten“ als feste Abläufe | 0,5 Tag | Auffindbarkeit im Desktop-Menü unbekannt |
| Ressourcen | Daten, die Nutzer oder Host anhängen | SPEC resources, BI | Desktop fragt `resources/list` ab (LOG: 29×), Anzeige ungeprüft | nur die `ui://`-Ressource | Kuratierte Decks oder Reagenzientabellen zum Anhängen | 0,5 Tag | Anwendungsgesteuert, Desktop entscheidet |
| Ressourcen-Vorlagen | Parametrisierte URIs (`chem://stoff/{name}`) | SPEC resources, PY | ungeprüft (kein `resources/templates/list` im LOG) | nein | Datenblatt als anhängbare Ressource | 0,5 Tag | Nutzen hängt an Desktop-UI |
| Completion | Autovervollständigung für Prompt-Argumente | SPEC prompts, PY (`completion()`) | ungeprüft | nein | Stoffnamen beim Prompt-Argument vorschlagen | 0,5 Tag | nur mit Prompts sinnvoll |
| Elicitation (Formular) | Server fragt den Nutzer mitten im Aufruf | SPEC elicitation, PY (`ctx.elicit`) | ungeprüft | nein | Isomeren-Wahl (Glucose, Xylol) als Formular statt Panel | 1 Tag | 2026-07-28 ersetzt sie durch `input_required`-Rundreise; Panel-Auswahl gibt es schon |
| Fortschritt (`report_progress`) | Zwischenstand bei langen Aufrufen | SPEC, PY | ungeprüft | nein | „OPSIN … PubChem …“ bei 5-s-Namensauflösung | 2 h | Anzeige in Desktop unbekannt |
| Liste geändert (`notify_tools_changed`) | Toolliste zur Laufzeit ändern | SPEC, PY | ungeprüft | nein | — | — | frühere eigene Beobachtung: Toolsets zur Laufzeit wirken unter Desktop nicht |
| Server-`website_url`, `title` | Metadaten im Handshake | PY | ungeprüft | nur `version` | Link zur Doku in der Konnektor-Liste | 0,5 h | Anzeige unbekannt |
| Sampling (Server fragt Claudes Modell) | `sampling/createMessage` | SPEC, BI | **nein**: „Claude doesn't yet support … Sampling“ | nein | — | — | veraltet seit 2026-07-28 |
| Roots | Client nennt Arbeitsordner | SPEC | ungeprüft | nein | — | — | veraltet seit 2026-07-28 |
| Logging an den Client | `notifications/message` | SPEC, PY (`ctx.log`) | ungeprüft | nein, `server.log` | — | — | veraltet seit 2026-07-28 |
| Ressourcen-Abos | Client folgt Änderungen einer Ressource | SPEC, BI | **nein**: BI nennt „Resource subscriptions“ nicht unterstützt | nein | — | — | — |

### Panel → Claude/Chat

| Weg | Was er tut | Quelle | Lokal? | Nutzen wir? | Idee fürs Produkt | Aufwand | Haken |
|---|---|---|---|---|---|---|---|
| `app.sendMessage` | Panel schreibt eine Nutzernachricht, nur nach Klick | SM, SDK | ja (Doku); Host-Fähigkeit `message` am Gerät ungeprüft | nein (M11, Plan U3) | „Mechanismus zeigen“, „Erkläre diese Gruppe“, „Quiz mich“ | 1 Tag | Nutzer bestätigt oft; ≤ 8000 Zeichen; Ergebnis beweist nicht, dass Claude las |
| `app.updateModelContext` | Panel-Zustand für den nächsten Zug in Claudes Kontext | SDK, IS | ja (Doku, nur SDK-Typ + IS); Fähigkeit ungeprüft; Inhaltsarten laut `updateModelContext`-Fähigkeit (Text, Bild, `structuredContent`) | nein (M12, U4) | Angeklicktes Atom/Gruppe, aktive Ansicht, Quiz-Stand | 1 Tag | Host schickt nur das letzte Update, erst mit der nächsten Nachricht |
| `app.createSamplingMessage` | Panel nutzt Claudes Modell direkt | SDK | ungeprüft; BI sagt server-seitig „Claude doesn't yet support … Sampling“ | nein | — | — | Spezifikation markiert Sampling als veraltet |
| `app.sendLog` | Log an den Host, nicht in den Chat | SDK | ungeprüft | nein | Panel-Fehler in Desktop-Log statt verloren | 1 h | Logging in 2026-07-28 veraltet |
| `app.openLink` | Externe Seite öffnen | EL, SDK | ja (Doku): „locally configured servers always show“ den Bestätigungsdialog | nein | PubChem-/UniProt-Eintrag öffnen | 2 h | Dialog bei jedem Klick |

### Claude → Panel

| Weg | Was er tut | Quelle | Lokal? | Nutzen wir? | Idee fürs Produkt | Aufwand | Haken |
|---|---|---|---|---|---|---|---|
| `toolresult` | Ergebnis kommt im Panel an | SDK | ja (gemessen) | ja, einziger Eingang | — | — | — |
| Host-Kontext `toolInfo`, `userAgent` | Welches Tool das Panel erzeugte, welcher Host | SDK | ungeprüft | nein | Ein Panel, das ohne Ergebnis schon weiß, ob es Mechanismus oder Molekül wird | 1 h | `toolInfo` optional |
| `toolinput` | Vollständige Argumente vor dem Ergebnis | SDK | ungeprüft | nein | Stoffname sofort als Titel, Skelett statt „Waiting for data…“ | 2 h | — |
| `toolinputpartial` | Gestreamte Teil-Argumente („geheiltes“ JSON) | SDK, MCP-Überblick („streaming tool inputs“) | ungeprüft | nein | Batch-Raster füllt sich, während Claude Namen schreibt | 0,5 Tag | Nur für Vorschau, letzter Eintrag kann abgeschnitten sein |
| `toolcancelled` | Aufruf abgebrochen | SDK | ungeprüft | nein | Ladezustand sauber beenden | 1 h | — |
| `hostcontextchanged` | Theme, Größe, Modus, Sprache ändern sich | SDK, DM | ja (Doku) | teilweise: nur Stilvariablen | siehe „Anzeige und Platz“ | — | — |
| App-Tools (`app.registerTool`) | Claude bedient das offene Panel | AT | **nein**: „Claude doesn't call the tools of a view from a local server“ | nein | Claude markiert die Carbonylgruppe, dreht das 3D-Modell | 2 Tage + Remote | nur Remote, nur Teil der Organisationen |
| `onteardown` | Aufräumen vor dem Entfernen | IS, SDK | ungeprüft (IS: Web sendet es nicht, iOS nur beim Verlassen) | nein | — | — | nicht verlässlich |

### Panel ↔ Server

| Weg | Was er tut | Quelle | Lokal? | Nutzen wir? | Idee fürs Produkt | Aufwand | Haken |
|---|---|---|---|---|---|---|---|
| `app.callServerTool` | Panel ruft ein Server-Tool ohne Claude | SDK, TS | ja (gemessen: Daten-Knopf, Anki, 3D, Export) | ja | Großes nachladen statt im ersten Ergebnis (TS-Empfehlung) | — | kostet keine Modell-Tokens; das Tool muss registriert sein |
| `_meta.ui.visibility: ["app"]` | Tool nur fürs Panel, nicht fürs Modell | SDK (`McpUiToolMeta`), PY (`Visibility`), EP nennt das Feld | ungeprüft | nein | `save_png` dem Modell entziehen: 17 → 16 sichtbare Tools (`lookup_molecule_data` bleibt, die `instructions` schicken das Modell dorthin) | 2 h | Filter setzt der Host, `tools/list` sieht gleich aus; Taxonomie-Test anpassen |
| `serverTools.listChanged`, `sendToolListChanged` | Host/Panel melden geänderte Toollisten | SDK | ungeprüft | nein | — | — | nur mit App-Tools sinnvoll (Remote) |
| Panel holt selbst aus dem Netz (`csp.connectDomains`/`resourceDomains`) | `fetch` aus dem Panel an freigegebene Ursprünge | DG, SDK (`sandbox.csp`) | ungeprüft (gewährte Liste am Gerät) | nein, alles läuft über `callServerTool` | — | — | der Server-Weg hält die SMILES-Privatsphäre (`privacy.py`) an einer Stelle |
| `app.readServerResource` / `listServerResources` | Panel liest Server-Ressourcen über den Host | SDK (`serverResources`) | ungeprüft | nein | Mol*-Strukturdaten als Ressource statt Tool-Antwort | 0,5 Tag | Host muss `serverResources` melden |
| Server-Zustand per Handle | ID im Ergebnis, nächste Aufrufe tragen sie | SPEC tools („Stateful Tools“) | ja (protokollneutral) | nein | Quiz-Sitzung oder Karteikarten-Stapel über mehrere Aufrufe | 1 Tag | Ablösung alter Panels (IS) mitdenken |

### Anzeige und Platz

| Weg | Was er tut | Quelle | Lokal? | Nutzen wir? | Idee fürs Produkt | Aufwand | Haken |
|---|---|---|---|---|---|---|---|
| Seitenpanel / Vollbild (Host-Knopf) | Claude bietet Vergrößern über dem Panel an | DM, DG | ja (Doku), Teil der Organisationen | ja, ungewollt: Knopf erscheint, Layout reagiert nicht | — | — | Panel meldet in beiden Orten `fullscreen` |
| `containerDimensions` | Größe des Containers je Modus | DM, SDK | ja (Doku) | nein (M10, U2) | Molekül füllt das Seitenpanel, kompakt unter 600 px | 1 Tag | Chat: `maxHeight`, Panel: `height` erst nach Messung |
| `requestDisplayMode` | Eigener Vergrößern-Knopf | DM | ja (Doku), nur aus Klick mit Fokus | nein | Knopf nur, wenn `availableDisplayModes` `fullscreen` enthält | 2 h | eigenes Chat-Fenster bietet nur `inline` |
| `availableDisplayModes` (App) | Was das Panel kann | DM | ja (Doku) | nein, bewusst undeklariert | `["fullscreen"]` allein → Karte im Chat statt Panel | 1 h | gilt für alle 13 Panel-Tools zugleich |
| `preferredDisplayMode` | Öffnet ohne Klick im Seitenpanel | DM (Claude-Erweiterung) | ja (Doku), unser `instance.resource(meta=…)` landet laut PY auch am `resources/read`-Inhalt | nein (abgleich Nr. 16 offen) | Nur für Mechanismus/Protein sinnvoll | 2 h + 2. Ressource | eine gemeinsame Ressource → träfe auch TLC und Anki |
| `pip` | Bild-im-Bild | SDK | **nein**: DG „Claude offers `inline` and `fullscreen`“ | nein | — | — | abgleich Nr. 8 nennt `pip` noch |
| Ablösung im Seitenpanel | Neuer Aufruf ersetzt das Panel, altes fällt in den Chat | DM, IS | ja (Doku) | n/a | Alte Panels zeigen „ältere Ansicht“ statt still weiterzusenden | 0,5 Tag | 15-s-Frist für `initialized` beim Ersetzen im Vollbild |
| `safeAreaInsets`, `platform`, `deviceCapabilities` | Ränder, Gerät, Touch/Hover | SDK, DG | ungeprüft (Werte am Gerät) | nein | Hover-Erklärungen auf Touch als Antippen | 2 h | — |
| `locale`, `timeZone` | Sprache des Nutzers | SDK | ungeprüft | nein | Panel-Beschriftung deutsch für deutschsprachige Studierende | 1 Tag | Tool-Texte bleiben Englisch (Konvention) |
| Größe melden (`sendSizeChanged`, Auto-Resize) | Panel meldet seine Höhe im Chat | SDK | ja (gemessen) | ja, `useApp`-Standard | — | — | im Vollbild Höhe nicht aus dem Inhalt ableiten (M10) |
| Stilvariablen, Schrift, `prefersBorder` | Claudes Look übernehmen | DG, theming, SDK (`useHostFonts`) | ja (Doku) | teilweise: `useHostStyleVariables`, keine Host-Schrift, kein `prefersBorder` | M1 abschließen | 0,5 Tag | — |
| `app.requestTeardown` | Panel bittet ums Schließen | SDK | ungeprüft | nein | — | — | kein erkennbarer Nutzen |
| `experimental` (Host und App) | Freie Erweiterungsfelder | SDK | ungeprüft | nein | — | — | nichts Dokumentiertes von Claude |
| `downloadFile` | Datei über Claudes Dialog speichern | DF | ja (Doku), Fähigkeit am Gerät ungeprüft | nein | SVG/PNG/CDXML/`.apkg` dort speichern, wo der Nutzer will | 0,5 Tag | `.js` u. a. gesperrt; `save_png` funktioniert heute |
| `_meta.ui.permissions` | Kamera, Mikrofon, Ort, Zwischenablage | SDK, ES | ungeprüft, ob gewährt (`sandbox.permissions`) | ja: `clipboardWrite` | — | — | Zwischenablage-Kopie kann still fehlen |
| Eingebettete Seiten (`frameDomains`) | Fremde Website im Panel | ES | **nein**: „Local server — Claude blocks the origin“ | nein | — | — | — |

### Verteilung und Einstieg

| Weg | Was er tut | Quelle | Lokal? | Nutzen wir? | Idee fürs Produkt | Aufwand | Haken |
|---|---|---|---|---|---|---|---|
| `claude_desktop_config.json` | Lokaler Eintrag per Installer | GS | ja (gemessen) | ja | — | — | Desktop-Neustart nach Codeänderung |
| Desktop-Extension (`.mcpb`) | Doppelklick-Installation, `user_config`-Maske | MB | ja (gemessen) | ja, ohne Icon (Manifest hat kein `icon`) | Icon 512 px | 2 h | Verzeichnis nimmt `.mcpb` nicht mehr an (abgleich §3) |
| Plugin mit lokalem Server | Server + Skills als Paket | WB, PS | **nein im Chat**: lokal „runs in Claude Code and in a Cowork session …, not in chat“ | nein | — | — | Panel lebt im Chat |
| Custom Connector (Remote, Tunnel) | HTTPS-URL in Claude eintragen | GS, TS, abgleich §5 | — (Remote) | nein | Voraussetzung für App-Tools, Einstiegspunkte, Web/iOS | 2–3 Tage + Betrieb | Hosting, ohne Anmeldung offen für alle mit URL |
| Einstiegspunkte (Artifacts-Seite) | App ohne Claude-Frage öffnen, anheften | EP | **nein**: „the connector is remote, not a local server“ | nein | „Chemie-Zeichenbrett“ direkt öffnen | 1 Tag + Remote | verifiziert oder eigen, Teil der Organisationen |
| WebMCP-Brücke (ext-apps 2.1.0) | laut abgleich §6 neu am 10.11. | abgleich §6 | ungeprüft | nein | — | — | nicht gelesen; vor Nutzung Release-Notizen prüfen |

## 2. Rangliste: größter Nutzen je Aufwand

1. **Knöpfe zum Weitermachen (`sendMessage`)** — *geht heute lokal (Doku; Host-Fähigkeit `message` am Gerät ungeprüft)*. Nutzer klickt unter Aspirin „Mechanismus der Esterhydrolyse“ → Claude bekommt den Satz als Nachricht (nach Bestätigung) und ruft `generate_mechanism` auf. Der Lernpfad verlängert sich ohne Tippen, Freitext bleibt im Chat (DG).
2. **Auswahl an Claude melden (`updateModelContext`)** — *geht heute lokal (Doku nur SDK-Typ und IS; Fähigkeit am Gerät ungeprüft)*. Nutzer klickt im Panel die Estergruppe an und tippt „warum ist die reaktiv?“ → Claude weiß aus dem Kontext, welche Gruppe gemeint ist, und erklärt genau diese. Hebt den Wert von Rang 1, weil sich Knöpfe auf die Auswahl beziehen können.
3. **Layout nach gemeldeter Größe + eigener Vergrößern-Knopf (M10)** — *geht heute lokal (Doku), Seitenpanel nur für einen Teil der Organisationen; gemeldete Werte am Gerät ungeprüft*. Nutzer zieht Morphin ins Seitenpanel → die Struktur füllt die Fläche, während er im Chat weiterfragt. Ohne diese Arbeit zeigt das Seitenpanel heute eine 320-px-Zeichnung in einer großen Fläche.
4. **Tool-`title` und `readOnlyHint`** — *ungeprüft (Wirkung lokal)*, Aufwand zwei Stunden. Nutzer fragt nach Coffein → das Nachschlagen läuft ohne Freigabe-Klick, die Freigabe für Schreibendes zeigt einen lesbaren Namen. Messen: nach dem Setzen in Desktop zählen, ob die Freigabe-Abfrage für lesende Tools entfällt.
5. **Interne Tools nur fürs Panel (`visibility: ["app"]`)** — *ungeprüft*. Nutzer klickt „Daten“ → das Panel holt das Datenblatt wie heute, aber Claude sieht `save_png` nicht mehr als Wahlmöglichkeit und kann es nicht mehr ungefragt aufrufen. Messen: nur im Desktop-Handtest (Claude nach seinen Tools fragen), weil der Host filtert und `tools/list` gleich bleibt.
6. **Skelett beim Aufruf (`toolinput`/`toolinputpartial`)** — *ungeprüft*. Nutzer fragt nach zehn Steroiden → das Panel zeigt sofort zehn beschriftete Platzhalter, die sich füllen. Ersetzt „Waiting for data…“, das bei 5 s Namensauflösung wie ein Hänger wirkt. Messen: im Panel mitloggen, ob Desktop vor `toolresult` überhaupt `toolinput` schickt.

Nur mit Remote-Konnektor: **App-Tools** wären der größte Einzelnutzen („Claude markiert im offenen Panel die chirale Achse“), kosten aber Hosting und sind auch dann nur für einen Teil der Organisationen frei.

**Messweg für alles „ungeprüft“ (eine Etappe, U5):** eine Diagnosezeile im Panel (im Arbeitsbaum entsteht gerade `HostDiagnostics.jsx`), die `getHostVersion()`,
`getHostCapabilities()` (`message`, `updateModelContext`, `downloadFile`, `serverResources`, `sampling`,
`sandbox.permissions`) und `getHostContext()` (`availableDisplayModes`, `containerDimensions`, `locale`, `platform`)
einmal je Ort (Chat, Seitenpanel, Vollbild) ausgibt; dazu server-seitig `ctx.client_capabilities` beim ersten
Aufruf ins `server.log` schreiben — das Desktop-Log zeigt den `initialize`-Inhalt nicht (`params { metadata: undefined }`).
Das trennt, was der Host meldet, von dem, was er tut (abgleich §5: beide Verbindungen meldeten UI, eine renderte nicht).

## 3. Bewusst nicht

- **Sampling (Server oder Panel):** BI sagt „Claude doesn't yet support … Sampling“, die Spezifikation 2026-07-28 markiert es als veraltet.
- **Roots:** veraltet seit 2026-07-28; Pfade gehen über Parameter und Konfiguration, wie heute `~/ChemDraw-Output`.
- **MCP-Logging an den Client:** veraltet seit 2026-07-28; wir loggen schon nach `server.log` (stderr-Weg der Spezifikation).
- **Eingebettete Seiten:** für lokale Server blockiert (ES), und eine fremde Seite im Panel würde laut ES Zwischenablage-Rechte kosten.
- **`pip`:** Claude bietet ihn laut DG nicht an.
- **Elicitation statt Isomeren-Panel:** die Auswahl im Panel gibt es schon und sie zeigt Strukturen; ein Textformular wäre ein Rückschritt.
- **Ressourcen-Abonnements:** BI nennt sie nicht unterstützt.
- **`requestTeardown`:** Panels ohne Zustand haben nichts aufzuräumen.

## 4. Widersprüche zum bisherigen Stand

- Beobachtung zu `abgleich.md` §1 („zustandslos, kein `initialize` mehr“): Desktop schickt weiter `initialize` (LOG 2026-11-11T08:21:04Z); welche Fassung es aushandelt, steht nicht im Log.
- `abgleich.md` Nr. 8 nennt `pip` als Modus; DG sagt jetzt „Claude offers `inline` and `fullscreen`“.
- `abgleich.md` Nr. 3 zählt 23 Tools ohne Annotationen; heute sind es 24 (voll) bzw. 17 (MVP), weiterhin ohne `title`/Annotationen.
- `abgleich.md` §1 nennt ext-apps 2.0.3 als neueste; `--check` meldet 2.0.4 und 2.1.0 (10.11.). Die neuen Seiten sind lokal noch nicht per `--update` übernommen.
