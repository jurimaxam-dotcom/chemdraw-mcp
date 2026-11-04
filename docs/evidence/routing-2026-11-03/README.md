# Routing-Messung 03.11.2026 (Claude Code, 57 Fälle)

Läufe von `uv run python evals/tool-routing/run_claude.py` gegen den Attrappen-Server
(`stub_server.py`, Standardprofil, 16 Tools) nach Fix `7596c26`. Je Fall steht, welches Tool
das Modell gerufen hat; ✔ = erwartetes Tool und kein verbotenes.

| Datei | Modus | Ergebnis |
|---|---|---|
| `lauf1-ohne-toolsuche.log` | alle Tools im Kontext | 54/57 |
| `lauf2-ohne-toolsuche.log` | alle Tools im Kontext | 53/57 |
| `lauf1-mit-toolsuche.log` | `ENABLE_TOOL_SEARCH=true` (Tools werden wie in Desktop nachgeladen) | 50/57 |
| `lauf2-mit-toolsuche.log` | dito | 49/57 |
| `rotfaelle-vor-fix-7596c26-mit-toolsuche.log` | Gegenmessung der 8 Rotfälle auf `7596c26^` | 4/8 |

Die Messung misst nur die Toolwahl, nicht die Richtigkeit der Antwort. Sie ist nicht
deterministisch; ein einzelner roter Fall gehört wiederholt. Desktop-Messungen mit echtem
Server: `docs/desktop-abnahme-2026-11-02.md`. Ursprünglich lagen die Logs nur im Scratchpad
(`/private/tmp/claude-501/…`); hierher kopiert am 04.11.2026, damit die Werkzeugbilanz-Seite
eine feste Quelle hat.
