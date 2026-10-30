# Bundle-Installation: feste uv-Version und gelockte Abhängigkeiten

Sicherheitsscan B4 (29.10.2026), umgesetzt 30.10.2026 nach Jays Entscheidung (b).

## Was beim ersten Start des Bundles passiert

1. `mcpb/server/run.sh` sucht ein vorhandenes uv (Homebrew, `~/.local/bin`, PATH)
   und nimmt es.
2. Gibt es keins, lädt `uv-holen.sh` die feste Version aus `uv-checksums.txt` von
   GitHub-Releases. Die SHA-256 muss übereinstimmen, sonst bricht der Start ab und
   nichts wird ausgeführt. Ablage: `~/.local/share/chemdraw-mcp-bundle/uv/uv-<version>/`.
   `install.sh` nutzt dieselbe Funktion.
3. `uv venv --python 3.12` legt `env-<version>` an. Fehlt Python 3.12, lädt uv ein
   verwaltetes Python und prüft dessen Hash selbst; dafür ist die feste uv-Version zuständig.
4. `uv pip install --require-hashes -r requirements.lock` installiert genau den Stand
   aus `uv.lock`, jede Datei hashgeprüft, dazu chemdraw-mcp mit den SHA-256 der
   PyPI-Dateien. Schlägt das fehl, bricht der Start ab. Ein Rückfall auf `uv tool run`
   existiert nicht mehr, weil der ohne Hashes auflöst.

`uv tool install` kam nicht in Frage: es ignoriert Hashes in `--constraints` und in
`--with-requirements` (gemessen mit uv 0.11.11: ein falscher Hash installierte trotzdem).

`requirements.lock` erzeugt `scripts/build-mcpb.sh` aus `uv export --frozen --no-default-groups
--no-emit-project` und hängt die Zeile für chemdraw-mcp aus der PyPI-JSON-API an. Das Bundle
lässt sich deshalb erst bauen, wenn die Version auf PyPI liegt. Der Release-Job ist entsprechend
angeordnet (`bundle` läuft nach `publish`).

## Folge: Sicherheitsupdates brauchen ein Release

Das Bundle installiert keine neueren Abhängigkeiten mehr als die, mit denen es gebaut wurde.
Hat zum Beispiel Pillow eine Lücke, bleibt sie bei allen Bundle-Nutzern bestehen, bis eine neue
chemdraw-mcp-Version erscheint. Dependabot (`.github/dependabot.yml`, Ökosystem `uv`) öffnet dafür
wöchentlich einen PR auf `uv.lock`. Bei Sicherheitsmeldungen ist dieser PR der Anlass für ein
kleines Release.

## uv-Version heben

```bash
./scripts/uv-pruefsummen.sh 0.14.0      # holt .sha256, lädt und prüft jedes Asset, schreibt uv-checksums.txt
uv run pytest tests/test_mcpb_start.py
./scripts/build-mcpb.sh                 # danach Bundle kalt starten, siehe unten
```

Kalt starten ohne vorhandenes uv: Bundle entpacken, dann mit leerem `HOME` und
`CHEMDRAW_MCP_UV=-` (ignoriert vorhandenes uv) `sh server/run.sh` starten und einen Handshake
(initialize → tools/list) schicken. Erwartet: „uv <version> geprüft“ im stderr, 7 Tools.

Unterstützt sind macOS (arm64, x86_64) und Linux-glibc (aarch64, x86_64), passend zu
`compatibility.platforms` im Manifest. Auf anderen Systemen bricht `uv-holen.sh` mit dem Hinweis
ab, uv selbst zu installieren.
