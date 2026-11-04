# Repo-Aufräumen — 04.11.2026

Ausgangsstand: `3016833e97298a6e79e2f96ee5df22c372b2d164`. Alle folgenden Vergleiche vor der Auslagerung.

## Sicherung
Bundle: `/Users/tom/Documents/archive/chemdraw-mcp-branches-2026-11-04.bundle`. Enthält sämtliche lokalen und Remote-Tracking-Refs einschließlich aller nicht gemergten Branches.
```text
The bundle contains these 27 refs:
3016833e97298a6e79e2f96ee5df22c372b2d164 refs/heads/main
836324b59b593f593907311e62e1f8596295f438 refs/heads/mcp-2-migration
a5be1e0d9a2b5b9e2c6a565d9a766fd2af1be7c8 refs/heads/worktree-agent-a89d4c26da6a9d6c2
3016833e97298a6e79e2f96ee5df22c372b2d164 refs/remotes/origin/HEAD
4e334e54afb7290812eff52cf77fa4884d3f7942 refs/remotes/origin/dependabot/uv/python-aef6c7a28b
3016833e97298a6e79e2f96ee5df22c372b2d164 refs/remotes/origin/main
836324b59b593f593907311e62e1f8596295f438 refs/remotes/origin/mcp-2-migration
dd932f62888f119f4b8bfb4b1e11347d98e913a5 refs/remotes/origin/mcp-2-migration-v2
03c08c5865499eef8f053a072e23af5ef26b99f4 refs/tags/v0.1.0
1536e3cdd9927c93db29a7942f5646c52a3c1090 refs/tags/v0.2.0
2a5d46a845b0c301e15521214ea8a3577f985170 refs/tags/v0.2.1
3f5231102b65899c6c791de0d7f005d5fb74379e refs/tags/v0.3.0
1986dd53da0bd73f26681699ad7f11bd16290847 refs/tags/v0.4.0
0afd68032afeac7171ea6ebfc9901358e21ea048 refs/tags/v0.4.1
fc604a77e5a8bccb6f3fdd1b71f6ea9f0e63c8cc refs/tags/v0.4.2
a222133ff87b8ffa63d662b24ff03db98cb92a27 refs/tags/v0.4.3
89ecf51166d2ade527733f4f48dd38cf8335a346 refs/tags/v0.4.4
3681f7be65c64489c4eddfedc4bba8289f413241 refs/tags/v0.4.5
1bfedb26ed1817e176711382bf1f3d519e41167e refs/tags/v0.4.6
16d4ed2b883f29e95aaedbd5cf6c746cc693e1f1 refs/tags/v0.4.7
8c9a0b7594fff67885091f8a5e7f5e3c5b8a36e6 refs/tags/v0.4.8
e4ce7d1d431c6ca07ad5a57e3c875072454a0aeb refs/tags/v0.5.0
745f6d65779bf9d003c83344c2686311b1f75449 refs/tags/v0.5.1
01f20e1a5b68d3a58177ad8018337d3af9948acb refs/tags/v0.5.2
b8b6326744875c3c9b0e1307f0c03bffce652123 refs/tags/v0.6.0
3016833e97298a6e79e2f96ee5df22c372b2d164 HEAD
a5be1e0d9a2b5b9e2c6a565d9a766fd2af1be7c8 worktrees/agent-a89d4c26da6a9d6c2/HEAD
The bundle records a complete history.
The bundle uses this hash algorithm: sha1
/Users/tom/Documents/archive/chemdraw-mcp-branches-2026-11-04.bundle is okay
```

## Gemergte lokale Branches
```text
$ git branch --merged main
* main
```
Nur main ist gemergt; main bleibt. Keine Branch-Löschung.

## mcp-2-migration

```text
$ git log --oneline main..mcp-2-migration
836324b Merge branch 'main' into mcp-2-migration
faff0d5 build(deps): Migration auf mcp 2.x (MCPServer statt FastMCP)
```
```text
$ git cherry main mcp-2-migration
+ faff0d59cad239f5fdd3fbd6be856f373c934685
```
```text
$ git diff --shortstat main mcp-2-migration
282 files changed, 4474 insertions(+), 22899 deletions(-)
```
Empfehlung: behalten, nicht mergen. Die Migration ist in main funktional vorhanden (`mcp>=2.3,<3`, MCPServer), aber der alte Gesamtpatch ist nicht identisch. Der historische Branch enthält außerdem andere Lockfile-/Doku-Stände. Frage an Jay: nach gesonderter inhaltlicher Abnahme archivieren und später entfernen?

## origin/mcp-2-migration-v2

```text
$ git log --oneline main..origin/mcp-2-migration-v2
dd932f6 build: Server auf mcp 2.x (MCPServer) umgestellt, mcp>=2.3,<3
```
```text
$ git cherry main origin/mcp-2-migration-v2
- dd932f62888f119f4b8bfb4b1e11347d98e913a5
```
```text
$ git diff --shortstat main origin/mcp-2-migration-v2
217 files changed, 3125 insertions(+), 16429 deletions(-)
```
Empfehlung: inhaltlich redundant; `git cherry` markiert den einzigen Commit mit `-`. `git show origin/mcp-2-migration-v2 | git patch-id --stable` stimmt mit main-Commit `c0dd24da908579935c701b0b320f2084a5e3697f` überein. Trotzdem keine Remote-Löschung: der abgestimmte Plan erlaubt in dieser Etappe nur gemergte Branches. Frage an Jay: den gesicherten Remote-Branch später entfernen?

## worktree-agent-a89d4c26da6a9d6c2

```text
$ git log --oneline main..worktree-agent-a89d4c26da6a9d6c2
a5be1e0 fix(demo): Kamera fährt schon beim Laden aufs Datenblatt
92d2f44 feat(demo): scripts/demo-short.sh – Aufnahme, Montage, MP4 1080×1920
ba1b8a7 build: Demo-Montage nicht in Wheel und sdist ausliefern
036a4f4 feat(video): Remotion-Montage für Demo-Shorts im Hochformat
32cf4bc feat(demo): Recorder schreibt optional ein Click-Log für die Shorts-Montage
```
```text
$ git cherry main worktree-agent-a89d4c26da6a9d6c2
+ 32cf4bca486326868a93a849de1111c1b47de3f6
+ 036a4f40261dadcb68f92d104462553e4eedc9e7
+ ba1b8a7700aac0a89c5dab9ddad4e3679b3c02cf
+ 92d2f447b2c9bb15fe053e4eb21b4c3f6eede5e6
+ a5be1e0d9a2b5b9e2c6a565d9a766fd2af1be7c8
```
```text
$ git diff --shortstat main worktree-agent-a89d4c26da6a9d6c2
187 files changed, 6914 insertions(+), 15612 deletions(-)
```
Empfehlung: Branch behalten, nicht pauschal mergen. Fünf eigene Kamera-/Demo-Commits sind nicht patchidentisch in main. Frage an Jay: Demo-/Kameraänderungen noch gewünscht? Falls ja, gezielt auf den heutigen Stand übertragen; andernfalls gesichert archivieren.

## origin/dependabot/uv/python-aef6c7a28b

```text
$ git log --oneline main..origin/dependabot/uv/python-aef6c7a28b
4e334e5 chore(deps): Bump the python group across 1 directory with 6 updates
```
```text
$ git cherry main origin/dependabot/uv/python-aef6c7a28b
+ 4e334e54afb7290812eff52cf77fa4884d3f7942
```
```text
$ git diff --shortstat main origin/dependabot/uv/python-aef6c7a28b
14 files changed, 245 insertions(+), 1666 deletions(-)
```
Empfehlung: behalten und separat als Dependency-Update prüfen. Der Commit aktualisiert RDKit, lxml, matplotlib, Playwright, pytest und ruff. RDKit/Matplotlib können Renderings ändern; Python- und JS-Playwright müssen zueinander passen. Frage an Jay: eigene geprüfte Dependency-Etappe beauftragen? Kein Merge im Aufräumschritt.

## Webrechner ausgelagert

Ziel: `/Users/tom/Documents/projects/praktikumsrechner` (eigenes Git-Repo).
Git kann `git mv` nicht über Repository-Grenzen ausführen. Deshalb zuerst
vollständig kopiert, jede Datei bytegleich geprüft, dann die Quell-Dateien mit
`git rm` entfernt. Auch der ignorierte `web/dist/`-Build wurde bytegleich
übernommen. Quellen und SHA-256-Hashes stehen im Ziel in `source-manifest.json`
(Quell-Commit `3016833e97298a6e79e2f96ee5df22c372b2d164`).

Mitgezogen: `web/`, die drei Web-Skripte und `tests/test_web_dateiliste.py`.
Benötigte reine Rechenmodule wurden als eigenständig gepflegte Kopie übernommen:
`chemdraw_tool/{__init__,ph_core,ph_calc,pk}.py`, `chemdraw_tool/aufgaben/*.py`.
Diese Originalmodule bleiben unverändert im MCP, wo die Werkzeuge/Tests sie weiter nutzen.
Lizenz ebenfalls kopiert. E2E nutzt jetzt ein eigenes exakt gepinntes
Playwright 1.60.0 samt Lockfile, keinen Pfad in das MCP-Checkout.

Keine `deploy-pages.yml` vorhanden. Keine aktiven Web-Verweise in README.md,
CLAUDE.md, pyproject.toml oder .github gefunden; keine Änderung nötig.
README.md und assets/ wurden von D nicht bearbeitet. Historische Planstellen
bleiben als Historie erhalten. `/web/dist/` aus der MCP-.gitignore entfernt.
Kein Web-Deployment ausgeführt.

## Worktree

`git -C .claude/worktrees/agent-a89d4c26da6a9d6c2 status --porcelain --untracked-files=all`
war leer; auch staged/unstaged Diffs leer. Der Branch ist im geprüften Bundle.
Zusätzlich kompletter Worktree einschließlich ignorierter Dateien gesichert:
`/Users/tom/Documents/archive/chemdraw-mcp-worktree-2026-11-04.tar.gz` (352 MB).
`tar -tzf …` erfolgreich: 30.588 Einträge. Anschließend `git worktree remove`
ohne `--force` erfolgreich; `git worktree list` zeigt nur noch das Hauptrepo.
Der Branch `worktree-agent-a89d4c26da6a9d6c2` bleibt erhalten.

## Neues privates Repository

`gh repo create jurimaxam-dotcom/praktikumsrechner --private --source=. --remote=origin --push`
erfolgreich, Commit `ea0ceb8c36ba50acc713a66692acab1acacd21e0` auf main gepusht.
`gh repo view --json nameWithOwner,isPrivate,url` bestätigt `isPrivate: true`:
https://github.com/jurimaxam-dotcom/praktikumsrechner . Kein Deployment.

## Prüfungen

- Neues Repo: `uv run --with pytest python -m pytest -q` → `3 passed in 0.01s`.
- Neues Repo: `npm run test:e2e` → geladen nach 1171 ms; Rechenarten einschließlich
  aller sieben PK-Aufgaben richtig, TI-Tastenweg sichtbar, Klausur 10/10,
  offline nach Neuladen lauffähig, Rechenweg nach zwei Fehlern offen,
  keine Browserfehler, 0 Anfragen an fremde Hosts. Log `/tmp/praktikumsrechner-e2e.log`.
- Erster MCP-Gatelauf rot bei 20 bestehenden Ruff-Verstößen in den zwei
  Bilanzskripten (vor Auslagerung ebenfalls im Quellstand enthalten).
  Mit Claude abgestimmte Korrektur: ungenutzten Import entfernen,
  Mehrfachanweisungen aufteilen, dynamische Bootstrap-Imports explizit
  über importlib; Reihenfolge der Umleitung vor Fixture-Import bleibt erhalten.
- HTML-Identität der Bilanz vor/nach Korrektur anhand des vorhandenen echten
  23-Tool-Laufs geprüft: `/tmp/werkzeugbilanz-vor-d.html` und
  `/tmp/werkzeugbilanz-nach-d.html` bytegleich, 1.637.448 Bytes,
  SHA-256 `4443424cc40678d383e13e2bc9f802b18b96b52b24848a2e087a18292caa54ab`.
- Zweiter MCP-Gatelauf: `./test.sh > /tmp/gate-d.log 2>&1`, Exit **0**.
  Lint grün; Backend **7487 passed, 16 skipped in 68.57s**;
  UI-Bundle frisch; Frontend einschließlich Pixel-Snapshot grün;
  Schlusszeile: `✅ Auto-Gate grün: Lint, Backend-Tests, UI-Bundle und Frontend-Tests bestanden.`
- `git diff --check` grün. Keine Produktcode-Änderung unter chemdraw_tool/ durch D.

## Noch zu entscheiden

Die vier oben genannten Branch-Fragen bleiben absichtlich offen. Keine Branches
oder Remote-Refs gelöscht. Die Aufräumetappe ist damit abgeschlossen; die
fachliche Bewertung alter Änderungen ist eine separate Entscheidung.

## Commit-Zuordnung im gemeinsamen Arbeitsbaum

Die bereits gestagten Web-Löschungen wurden während des laufenden Gates vom
parallelen C-Commit `167c8b1` mit aufgenommen (zusammen mit tests/test_readme.py).
Kein Rewrite: der gewünschte Endstand ist korrekt. D-Korrekturen:
`7007e14` (Ruff), `22d4142` (Befund und .gitignore).
Der während des Gates neu hinzugekommene C-Test wurde ergänzend separat
geprüft: `uv run pytest -q tests/test_readme.py` → **5 passed in 1.04s**
(`/tmp/gate-d-readme.log`). Keine fremden Änderungen zurückgesetzt.
