# Bundle-Abnahme 0.11.0 in Claude Desktop — 17.11.2026

**Das veröffentlichte `chemdraw-mcp-0.11.0.mcpb` zeichnet Koffein im neu gestalteten Panel, das 3D-Modell dreht sich
mit der Maus. Im ersten Chat nach dem Update war die Extension für diesen Chat ausgeschaltet, obwohl sie in den
Einstellungen „Running“ zeigte.**

Gemessen von Codex (Tisch-Faden `20261117-105217-bundle-abnahme-0-11`, Claude Desktop 5.11492.5, Modell Opus 5.5
Medium), vom Owner geprüft: Hash selbst nachgerechnet und mit dem Digest des Release-Assets verglichen, Panel-Bild,
Prozessliste und Versionsdatei selbst angesehen. Die Bilder liegen lokal (`/tmp/chemdraw-desktop-test/bundle-0.11.0/`)
und nicht im Repo, weil sie die Seitenleiste mit privaten Chat-Titeln zeigen.

| Schritt | Befund | Beleg |
|---|---|---|
| Download vom Release v0.11.0 | SHA-256 `f4fe2c2ae008703b0215d9d207c489141f663f40f66e50fb8c7e2613e728700c`, gleich dem Digest des Release-Assets | `shasum -a 256`, `gh release view v0.11.0 --json assets` |
| Installation | Update der vorhandenen, ausgeschalteten Extension 0.10.0 → 0.11.0; nur das Standard-Bündel, kein leeres Profil | `B-installed.png`, `B-installed-version.txt` |
| Aktivieren, Neustart | Server lief beim ersten Prozesscheck, nach dem Neustart „Running“ | `B-running.png` |
| Gezielter Prompt, erster Versuch | Modell findet die Extension nicht: im Konnektor-Menü des Chats war sie aus | `B-first-no-extension.png` |
| Derselbe Prompt nach Anhaken im Chat-Menü | Konnektor „ChemDraw MCP (unofficial) · generate_molecule“, neues Panel: Reiter Structure/Data/Study rechts im Kopf, Formula/Molar mass/CAS unter der Zeichnung, Continue in chat, Files 2, Export PNG, Add to Anki | `B-new-panel.png` |
| 3D, echter Mauszug | Modell dreht von der Vorderansicht zur Seitenansicht | `B-before-drag.png` → `B-after-drag.png` |
| Herkunft des Servers | `…/chemdraw-mcp-bundle/env-0.11.0/bin/chemdraw-mcp`, Parent `run.sh` im Extension-Ordner | `B-runtime.txt` |
| Endzustand | Extension wieder ausgeschaltet, 0.11.0 bleibt installiert; `chemdraw` und `chemdraw-pharma` laufen, Konfiguration unverändert | `B-final-disabled.png`, `B-config-comparison.txt` |

Gezielter Prompt wörtlich: „Use the ChemDraw MCP (unofficial) desktop extension, not chemdraw or chemdraw-pharma, to
draw caffeine.“ Kein Freigabedialog beim erfolgreichen Versuch.

## Folge

- `docs/getting-started.md` nennt jetzt den Namen, unter dem die Extension im Konnektor-Menü steht, und was zu tun
  ist, wenn Claude sie trotz „Running“ nicht findet.
- Anders als bei 0.10.0 erschien das Panel ohne weiteren Neustart nach dem ersten Tool-Aufruf.

## Grenzen

- Kein leeres Profil: ob eine Erstinstallation die Extension im ersten Chat von selbst einschaltet, ist nicht gemessen.
- Das pharma-Bündel wurde nicht installiert; sein Digest am Release ist
  `1c271db37a431bb22e118452742c0c32b185db5c428e0542baa0c8bd7858f358`.
