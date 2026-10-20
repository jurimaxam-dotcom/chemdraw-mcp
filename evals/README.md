# Evals: Prompt → Tool

Der Server bietet standardmäßig das MVP-Profil mit sieben Tools an;
`CHEMDRAW_PROFILE=full` schaltet alle 23 Tools frei. Welches davon das Modell
bei welcher Frage wählt, war
bisher Anekdote: „Zeichne Aspirin" landete einmal bei `generate_scope_table`,
ein blankes „Coffein" bei `lookup`. Hier wird daraus ein Testfall.

## Was hier liegt

| Datei | Rolle |
|---|---|
| `tool-routing/cases.yaml` | **Die Wahrheit.** Prompt, erwartetes Tool, verbotene Tools, Begründung. Runner-unabhängig gepflegt. |
| `tool-routing/export_tools.py` | Kippt die echten Tool-Definitionen aus dem laufenden Server nach `tools.json`. |
| `tool-routing/build_config.py` | Baut aus beidem `promptfooconfig.yaml`. |
| `tests/test_eval_cases.py` | Hält die Fälle **ohne Netz** mit der Toolliste synchron — läuft im normalen Gate mit. |

`tools.json` und `promptfooconfig.yaml` sind erzeugt und deshalb nicht
versioniert; sie wären am Tag nach der nächsten Beschreibungsänderung falsch.

## Lauf ohne API-Schlüssel: über Claude Code

```bash
uv run python evals/tool-routing/run_claude.py [fall-id …]   # MODEL=sonnet für ein anderes Modell
```

Fährt dieselben Fälle über `claude -p` mit der Claude-Code-Anmeldung. Das Modell sieht
alle Tools samt `instructions` des gewählten Serverprofils, aber `stub_server.py` führt nichts
aus (kein Schreiben nach `~/ChemDraw-Output`, kein Netz). Hooks und CLAUDE.md des Nutzers
sind abgeschaltet (`--setting-sources project`) — ohne das diskutiert das Modell den
Arbeitsordner statt ein Tool zu wählen (gemessen 02.10.: 10/28 statt 24/28). Ein roter
Fall ist ein Befund über Beschreibungen, nicht automatisch ein Fehler im Fall: ein Prompt
ohne Strukturen („vier Produkte meiner Suzuki-Kupplung") wird zu Recht mit einer Rückfrage
beantwortet. Der Lauf ist nicht deterministisch; ein einzelner roter Fall gehört
wiederholt, bevor man Beschreibungen ändert. Nicht im Gate (Modellaufruf, ~3 min).

Ohne Fall-IDs laufen nur Fälle, deren erwartetes Tool im gewählten Profil verfügbar
ist. Explizite unbekannte oder deaktivierte Fall-IDs brechen mit Exit 2 ab;
eine leere Auswahl wird niemals als `0/0 grün` gewertet. Die vollständige
historische Fallsammlung bleibt in `cases.yaml` erhalten:

```bash
CHEMDRAW_PROFILE=full uv run python evals/tool-routing/run_claude.py
```

## Lauf mit promptfoo

Braucht einen Anthropic-API-Schlüssel in der Umgebung — die Claude-Code-
Anmeldung reicht **nicht**, promptfoo spricht die API direkt an.

```bash
export ANTHROPIC_API_KEY=…
uv run python evals/tool-routing/export_tools.py > evals/tool-routing/tools.json
uv run python evals/tool-routing/build_config.py
npx promptfoo@latest eval -c evals/tool-routing/promptfooconfig.yaml
```

Zwei Dinge, ohne die der Lauf wertlos ist:

- **Alle Tools des gewählten Profils werden angeboten**, nicht nur das erwartete. Bietet man nur
  das richtige an, kann das Modell nicht danebengreifen und jeder Fall ist
  tautologisch grün. `build_config.py` hängt deshalb immer den vollständigen Export
  an und übernimmt nur Fälle, deren erwartetes Tool im Export enthalten ist.
  Fehlen passende Fälle, bricht der Generator ab. Für die historische Vollsuite
  den Export mit dem folgenden Befehl erzeugen; der anschließende Generator
  richtet sich nach dieser Datei.
- **Jeder Fall hat eine Negativseite** (`forbidden`). Ohne sie geht ein Fall
  auch dann durch, wenn das Modell zusätzlich das falsche Tool ruft.

Für den vollständigen Export:

```bash
CHEMDRAW_PROFILE=full uv run python evals/tool-routing/export_tools.py > evals/tool-routing/tools.json
```

## Neue Fälle

Drei *verschiedenartige* Prompts pro kritischem Tool — drei Umformulierungen
desselben Satzes beweisen nur, dass ein Wortlaut trifft. Jede Abgrenzung aus
`NEEDS_DELIMITATION` (in `tests/test_server_taxonomy.py`) braucht mindestens
einen Fall; `tests/test_eval_cases.py` erzwingt das und wird rot, wenn ein
Zaun ohne Fall bleibt.

## Warum nicht `claude plugin eval`

Inhaltlich die bessere Wahl: der Grader `tool_used` bildet die beidseitige
Regel deterministisch ab (`min: 1` für „muss rufen", `max: 0` für „darf nicht
rufen"), ohne LLM-Judge und ohne Grading-Kosten. Auf dieser Maschine ist es
gesperrt:

```
$ claude plugin eval
`plugin eval` is currently in early access
```

Die Freischaltung läuft pro Organisation. Sobald sie da ist, wandern dieselben
Fälle aus `cases.yaml` in einen anderen Runner — deshalb ist die Datei
bewusst frei von promptfoo-Syntax.
