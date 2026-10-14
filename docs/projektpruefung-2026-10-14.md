# Projektprüfung vom 14.10.2026

Ausgangsstand: `b88a4e2`, sauberer Arbeitsbaum. Auftrag: autonome Einschätzung von Ziel, Struktur, Werkzeugen und Auffälligkeiten. Breite Code- und Dokumentationsprüfung mit drei getrennten Teilprüfungen und aktuellen Testläufen; kein vollständiger Security- oder wissenschaftlicher Fachreview. Kein Produktionscode geändert.

## Urteil und Ziel

Den gemeinsamen Chemie- und Rechenkern behalten. Zuerst die nachgewiesenen Fehler beheben und die Auslieferung absichern; den nächsten Funktionsausbau auf ein Produkt konzentrieren.

Das Repository enthält inzwischen zwei Produkte:

| | Chemie-MCP | Praktikumsrechner |
|---|---|---|
| Einstieg | Claude Desktop, lokale Installation | Browser, Pyodide, auch offline |
| Versprechen | Aus einer Anfrage eine brauchbare Struktur, Grafik oder Rechnung erzeugen | Aufgaben rechnen, Rückmeldung und Rechenweg erhalten |
| Zielgruppe laut Unterlagen | Chemie, Pharmazie, teilweise Biologie | Zunächst Pharmazie-Praktikum und Prüfung |
| Geschäftsmodell laut Plan | Kostenloses Open-Source-Werkzeug | Geplanter Semesterpass; noch nicht validiert |

`plans/produkt.md` benennt den Browsertrainer ausdrücklich als verkaufbares Produkt. README und Paketbeschreibung erklären hauptsächlich den MCP. Gleichzeitig plant `plans/mcp-server.md` eine weitere Lernplattform im Panel. Meine Einschätzung: Hier fehlt aktuell vor allem eine gemeinsame Priorität. Für ein Verkaufsziel sollte der vorhandene Trainer in einen kleinen Nutzertest gehen, bevor weitere Themen, Quizmodi oder Zahlungsinfrastruktur entstehen. Für ein Open-Source-Ziel sollten Installation, Identität der Ergebnisse und der erste sichtbare Nutzen Vorrang haben. Ein sofortiger Repo-Split ist dafür unnötig.

## Was an der Struktur trägt

- **Eine fachliche Quelle:** `ph_core.py`, `pk.py` und weitere reine Rechenmodule werden von Zahlen, Diagrammen und Browseraufgaben wiederverwendet. Pyodide vermeidet eine zweite Formelsammlung in JavaScript.
- **Passender Werkzeugzuschnitt:** 23 MCP-Tools in fünf Bereichen; explizite Abgrenzungen, Default für bloße Stoffnamen, Schemasnapshots und Routingfälle. Die bloße Zahl ist kein Grund zum Entfernen. Neue Lernmodi passen eher als Parameter oder Panelzustand in bestehende Tools.
- **Pragmatischer Stack:** RDKit für Strukturen, Matplotlib für wissenschaftliche Grafiken, React/Vite für das eingebettete Panel. Im geprüften Bestand gibt es keinen Anlass für einen Frameworkwechsel oder ein zusätzliches Backend für den Trainer.
- **Gezielte Qualitätsgrenzen:** Default-Renderings, UI-/Export-Parität, Molekülidentität, Tooltexte, Output-Verzeichnisse und Bundle-Frische haben eigene Prüfungen. Installation und Diagnose werden als Paketfunktionen ausgeliefert.

Der größte strukturelle Engpass ist `chemdraw_tool/server.py` mit 3.101 Zeilen. Dort treffen Registrierung, Beschreibung, Validierung, fachliche Abläufe, Dateinamen, Datenanreicherung und Ausgabeformatierung zusammen. Die beobachtete Doppelarbeit ist konkret: Nullwerte werden in zwei Ansichten verschieden behandelt; Einzel- und Batchpfad wiederholen Teile der Molekülverarbeitung. Erst gemeinsame Dateibenennung und Eigenschaftsabbildung herauslösen, danach gegebenenfalls Toolbereiche. Ein großer Neuaufbau ist nicht begründet.

## Priorisierte Fehler und Lücken

### 1. Ergebnisse müssen ihre Identität behalten

**Exportdateien verschiedener Moleküle überschreiben sich — reproduziert.**
`server.py:399–403` entfernt beim Sluggen Bindungszeichen; `generate_molecule` verwendet das Ergebnis direkt (`:466–474`). `CC` und `C=C` schreiben beide `cc.svg`. Der zweite Aufruf verändert damit die Datei, auf die das erste Ergebnis verweist. Reproduktion in einem temporären Output-Verzeichnis mit gemockter Datenanreicherung. Struktur-Fingerabdruck und relevante Darstellungsparameter sollten Bestandteil der Benennung sein; explizite Überschreibsemantik getrennt festlegen.

**Ein wiederverwendetes Panel kann das Datenblatt des alten Moleküls zeigen — reproduziert.**
`ui/src/main.jsx:16–18` übernimmt neue Toolergebnisse. `App.jsx:16` rendert `MoleculeView` ohne Identitätsschlüssel; dessen `sheet`-Cache (`MoleculeView.jsx:25,55–57`) bleibt bei neuen SMILES bestehen. jsdom-Reproduktion: Aspirin → Data → dieselbe App mit Caffeine neu rendern. Ergebnis: Caffeine im Kopf, Aspirin-CAS `50-78-2` im Datenblatt, nur ein Datenabruf. Das betrifft erneute Ergebnisse im selben Panel; ob Desktop diesen Ablauf im konkreten normalen Chat erzeugt, wurde nicht live geprüft. Komponentenidentität und laufende Requests an den Stoff binden.

### 2. Der Trainer verwirft seine eigene angezeigte Lösung

**70 von 120 Tangentenaufgaben — aktuell reproduziert.**
`web/praktikumsrechner/index.html:283–289` zeigt diese Lösungen mit zwei Nachkommastellen. Die Toleranz in `aufgaben/pharmakokinetik.py:258` ist teilweise enger. Beispiel Seed 0: tatsächliche Lösung `-0.47722280600916983`, angezeigt `-0,48`, Toleranz `0.002386114030045849`; die Anzeige wird abgelehnt.

Reproduktion im Projektordner:

```bash
uv run python - <<'PY'
from chemdraw_tool.aufgaben.pharmakokinetik import tangente_aufgabe
from chemdraw_tool.aufgaben.basis import pruefe

bad = []
for seed in range(120):
    a = tangente_aufgabe(seed)
    shown = f'{a["loesung"]:.2f}'
    if not pruefe(a, shown):
        bad.append(seed)
print(f'{len(bad)}/120 angezeigte Antworten abgelehnt')
PY
```

Der Browser-E2E-Test bleibt grün, weil er für PK-Aufgaben vier Nachkommastellen aus der internen Lösung eingibt (`scripts/rechner-e2e.sh`). Er prüft damit einen anderen Weg als das Abschreiben der sichtbaren Lösung. Präzision und zulässige Rundung brauchen einen gemeinsamen Vertrag und einen Test über die sichtbare Ausgabe.

### 3. Gute lokale Tests sichern nicht jeden Auslieferungsweg

- **Release ohne Pflichtgate:** `.github/workflows/publish.yml:14–35` baut und veröffentlicht unabhängig vom CI-Testjob. Ein roter Commit oder altes UI-Bundle wird nicht durch diesen Workflow verhindert. Zusätzlich hängt der Bundle-Job `:39–52` nicht am erfolgreichen PyPI-Publish. Empfohlene Reihenfolge: grüner Testlauf für denselben Commit → Wheel bauen und installiert prüfen → PyPI verfügbar → Launcher und Registry.
- **Trainer außerhalb CI:** `ci.yml:56–57` startet `test.sh`; dieses enthält den Browsertrainer-E2E nicht. Ein eigener CI-Job für Änderungen an Aufgabenmodulen, Weboberfläche und Web-Build würde den vorhandenen Test tatsächlich als Abnahme nutzen.
- **Leere Routingauswahl ist grün:** `uv run python evals/tool-routing/run_claude.py audit-no-such-case` liefert `0/0 grün`, Exit 0. Ursache: Filter `:68–70`, Erfolgsentscheidung `:94–95`. Unbekannte Fall-IDs müssen scheitern. Zudem übernehmen Claude-Stub und promptfoo-Weg die Server-Instructions nicht gleich; ihre Resultate sind nicht unmittelbar vergleichbar.
- **Doctor kann vor der Diagnose abbrechen:** `doctor.py:37` importiert `resolver`, dieser RDKit auf Modulebene. Ein simulierter RDKit-Importfehler bricht bereits den Doctor-Import ab, bevor dessen Renderingdiagnose greifen kann.

### 4. Weitere Befunde für gezielte Folgearbeit

- **Nullwerte verschwinden:** `server.py:331–338` behandelt `XLogP=0`, `TPSA=0`, HBD/HBA `0` als fehlend. Mit gemocktem Datensatz reproduziert. Der Datenblattpfad nutzt bereits `is not None`. `_build_lipinski` kann bei unvollständigen Kriterien trotzdem `passes=True` liefern; Unbekanntes sollte sichtbar bleiben.
- **Lokales Zeichnen wartet auf optionale Datenbankabfragen:** `generate_molecule` ruft vor der Rückgabe immer `_enrich_properties` auf (`server.py:482`). Bei ausbleibenden Ergebnissen sind bis zu drei aufeinanderfolgende Versuche möglich; im Batch pro Molekül erneut. Zeichnen bleibt lokal, aber die Antwortzeit hängt dadurch trotzdem am Netz. Ein gemockter Ausfall bestätigt die drei Versuche; keine reale Ausfalllatenz gemessen.
- **Numerische Randfälle:** `ph_calc.py:258` verliert bei starken Basen durch Subtraktion fast gleicher Zahlen Präzision. Im akzeptierten Eingabebereich geben 10, 12 und 15 mol/L denselben Wert zurück, 20 löst `ValueError` aus. `ph_core.py:48` begrenzt die Bisektion still auf pH 0–14, ohne Vorzeichenwechsel zu prüfen. Das sind Grenzen des implementierten Idealmodells und der Eingabevalidierung; keine Aussagen über die reale Chemie konzentrierter Lösungen. Niedriger priorisieren als die alltäglichen Identitäts- und Rundungsfehler.
- **Kalibrierwarnung:** `server.py:1017` zeigt den Hinweis auf schlechtes R² nur ohne unbekannte Proben. Gerade mit Proben verschwindet er. Statisch geprüft, nicht im Panel reproduziert.
- **Panelbedienung:** feste 360-px-Höhe und 25-%-Seitenleiste in `MoleculeView`, teils 9-px-Schrift; Gruppenhervorhebung nur per Maus in `FunctionalGroupList.jsx`. Enges Layout und Tastaturbedienung gezielt prüfen. Das ist ein Codebefund, keine aktuelle visuelle Desktop-Abnahme.
- **Service Worker:** `web/praktikumsrechner/sw.js:17–18` löscht alle anderen Cache-Namen desselben Origins. Nur frühere eigene `praktikumsrechner-*`-Caches löschen; relevant, sobald weitere Apps auf demselben Origin liegen.
- **Dokumentation:** Eval-Doku und Bundlebeschreibung nennen teilweise noch 20 statt 23 Tools. Kein `STATUS.md` vorhanden; der Einstieg in zwei Produkte erfordert README plus beide Pläne. Eine kurze gemeinsame Einstiegsseite wäre hilfreich. Der geparkte MCP-2-Worktree existiert weiterhin; im Rahmen dieser Prüfung nicht verändert.

## Aktuelle Prüfergebnisse und Grenzen

| Prüfung | Ergebnis vom 14.10.2026 |
|---|---|
| `./test.sh` | Grün: Ruff, 6.936 Python-Tests bestanden, 16 übersprungen; Bundle bytegleich; 18 JS-Utility-, 17 DOM- und 2 Browser-Rastertests bestanden |
| `./scripts/rechner-e2e.sh` | Grün: sechs Bereiche, alle sieben PK-Typen, TI-Tastenweg, Klausur 10/10, Offline-Neuladen; 0 Anfragen an fremde Hosts im getesteten Ablauf |
| `npm --prefix chemdraw_tool/ui run test:host` | Grün: Sandbox/AppBridge/echter Server, Methylphenidat-CAS 113-45-1, zweiter Wechsel aus Cache |
| `./scripts/handshake.sh` | Grün: 23 Tools, 16 Panels; ausdrücklich Fallback `uv run chemdraw-tool-server`, kein passender Eintrag in der Desktop-JSON gefunden |
| `uv run python scripts/anthropic_sync.py --check` | Exit 0; meldet eine geänderte Quelle (`plugins/org-sync.md`); keine Baseline übernommen und keine Migration vorgenommen |

Der Handshake belegt in diesem Lauf einen frischen stdio-Start aus der Shell. Er beweist weder die tatsächlich laufende Desktop-Extension noch deren GUI-Umgebung oder das Fehlen eines veralteten Prozesses. Ein fehlender JSON-Eintrag schließt eine Installation als Desktop-Extension nicht aus.

Nicht durchgeführt: neuer bezahlter Modell-Routinglauf, vollständiger Live-Identitätstest aller Stoffe, erneute visuelle Desktop-Abnahme, Nutzertest oder Preisvalidierung. Die grünen Tests widerlegen die gezielt reproduzierten Fehler nicht; sie zeigen die konkreten fehlenden Abnahmefälle.

## Empfohlene Reihenfolge

1. Ergebnisidentität und Eingabevertrag reparieren: Dateikollisionen, alter Datenblattcache, sichtbare gerundete Antwort. Jeweils erst roten Regressionstest zeigen.
2. Bestehende Prüfungen verbindlich machen: Release an denselben grünen Commit binden, Wheel-Smoke, Trainer-CI, leere Evals ablehnen. Kleinere Daten- und Diagnosefehler mitnehmen.
3. Vorhandenen Browsertrainer mit wenigen echten Zielnutzern prüfen. Die im Produktplan offenen Entscheidungen zu Sichtung, Kanal und Impressum bleiben echte Voraussetzungen; kein Deploy im Rahmen dieses Audits.
4. Erst nach dieser Rückmeldung weiteren Panel-/Trainerumfang priorisieren. Den gemeinsamen Fachkern behalten; technische Extraktionen an nachgewiesener Doppelarbeit ausrichten.
