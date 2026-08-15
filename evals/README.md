# Evals: Prompt → Tool

Der Server hat 20 Tools. Welches davon das Modell bei welcher Frage wählt, war
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

## Lauf

Braucht einen Anthropic-API-Schlüssel in der Umgebung — die Claude-Code-
Anmeldung reicht **nicht**, promptfoo spricht die API direkt an.

```bash
export ANTHROPIC_API_KEY=…
uv run python evals/tool-routing/export_tools.py > evals/tool-routing/tools.json
uv run python evals/tool-routing/build_config.py
npx promptfoo@latest eval -c evals/tool-routing/promptfooconfig.yaml
```

Zwei Dinge, ohne die der Lauf wertlos ist:

- **Alle 20 Tools werden angeboten**, nicht nur das erwartete. Bietet man nur
  das richtige an, kann das Modell nicht danebengreifen und jeder Fall ist
  tautologisch grün. `build_config.py` hängt deshalb immer den vollen Export an.
- **Jeder Fall hat eine Negativseite** (`forbidden`). Ohne sie geht ein Fall
  auch dann durch, wenn das Modell zusätzlich das falsche Tool ruft.

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
