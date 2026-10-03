# Abgleich: was Anthropic veröffentlicht — und wo wir stehen

Stand 03.10.2026. **Das ist unsere Auswertung in eigenen Worten**, keine Kopie. Die Quellen stehen in
`quellen.json`, ihre Fingerabdrücke in `stand.json`. Wer diese Datei anfasst, hat vorher
`uv run python scripts/anthropic_sync.py --check` laufen lassen und die geänderten Seiten gelesen.

Pflege-Regel: Ändert sich eine Quelle, wird **hier** die Zeile angepasst, dann erst gebaut, dann
`--update`. Maßnahmen-Nummern (M…) tauchen in `plans/panel-ausbau.md` auf.

## 1. Versionen (das `--check` meldet sie jedes Mal)

| Baustein | unser Stand | neueste | Folge |
|---|---|---|---|
| `@modelcontextprotocol/ext-apps` | **^2.0.3** (migriert 03.10.2026) | 2.0.3 | **M0 erledigt:** Protokoll auf dem Draht unverändert (2.x-Panels laufen in 1.x-Hosts und umgekehrt, vom Hersteller getestet). Gebrochen waren nur Abhängigkeiten (`client` ^2 statt `sdk` ^1, `zod` ^4.2, Node ≥ 20); unser Panel braucht dafür **keine Codeänderung** (nutzt ext-apps an einer Stelle: `useApp`). Bundle 524 → 399 kB. 2.0.1 bis 2.0.3 sind Beispiel-Patches, an der Bibliothek ändert sich nichts. |
| MCP-Spezifikation | – | Fassung **2026-07-28** | **M0b erledigt:** zustandslos (kein `initialize` mehr), `server/discover`, Pflichtfeld `resultType`, Cache-Hinweise `ttlMs`/`cacheScope`, Roots/Sampling/Logging als veraltet markiert. Das setzt das Python-`mcp` 2.x für uns um (Plan mcp-2-migration, geparkt); ältere Server bleiben nutzbar (Clients behandeln fehlendes `resultType` als vollständig). Für uns jetzt nichts zu tun; Sampling nutzen wir nicht. |
| Python `mcp` | `>=1.27,<2` | 2.3.0 | siehe Plan „mcp-2-migration" (geparkt) |
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

**Folge:** Unsere Doppelklick-Extension bleibt der Weg für das Panel im Chat. Ein Verzeichnis-Eintrag brächte Reichweite,
aber kein Panel im Chat. **Entscheidung offen für Jay:** Eine **gehostete Variante** (Server im Netz, mit Panel in allen Oberflächen
und Verzeichnis-Eintrag möglich) wäre ein anderes Produkt: RDKit läuft dann bei uns, nicht beim Nutzer, mit Kosten und
Betrieb. Nicht jetzt; hier festgehalten, damit es nicht verloren geht.

Zwei Dinge aus den Prüfkriterien, die nur bei einer Einreichung zählen: Beschreibungen dürfen Claudes Verhalten nicht
lenken (unsere `instructions` „Reach for these tools …" tun das bewusst und sind gemessen); Diagramme und Charts sind erlaubt.

## 4. Was das für die Reihenfolge der Arbeit heißt

1. **M0 ext-apps 2.0 und neue MCP-Fassung lesen** — bevor das Panel weiter wächst, sonst bauen wir auf der alten Hauptversion weiter.
2. **M1 nativer Look**, **M3 Annotationen**, **M2 Größenmessung** — klein, jeder für sich prüfbar.
3. Danach die Reiter und der Rest aus `plans/panel-ausbau.md`.
