# Publishing to the MCP Registry

The registry is a published snapshot: editing `server.json` does not change the live entry.

## Automatic publication

`.github/workflows/publish.yml` builds and publishes both `chempane` and the `chemdraw-mcp`
compatibility package. Its `registry` job runs after PyPI publication and uses
`mcp-publisher login github-oidc` to publish `io.github.chempane/chempane` from
`chempane/chempane`. A personal GitHub device login cannot publish this organization namespace.
Both PyPI projects need the same Trusted Publisher (repository, workflow and environment).
PyPI supports [one publisher for multiple projects](https://docs.pypi.org/trusted-publishers/internals/#why-is-the-pypi-project-to-publisher-relationship-many-many).

After the workflow completes, verify the exact name, version and `isLatest` flag:

```bash
./scripts/publish-registry.sh
```

The script first checks PyPI, then the registry. If the organization entry is missing,
it fails and points to the release workflow instead of attempting an unsupported personal login.
For a failed `registry` job, rerun that job after fixing its cause; do not republish PyPI distributions.

## Release-Reihenfolge im Ganzen

1. Version in `pyproject.toml` **und** `server.json` (Top-Level *und*
   `packages[0].version`) ziehen, CHANGELOG ergänzen (`[Unreleased]` in den
   datierten Abschnitt `## [X.Y.Z] — JJJJ-MM-TT` verschieben), committen, pushen.
   Vorab lokal: `uv run python scripts/release_check.py --tag vX.Y.Z` — derselbe
   Check läuft als Job `check` in `publish.yml` und hält den Release bei einem
   Befund an, zusammen mit `tests/test_readme.py` und
   `tests/test_docs_consistency.py` (Toolnamen, Parameter, Zahlen, Pfade).
1a. **Doku-Sichtung (nicht mechanisch prüfbar, Pflicht vor jedem Release):** ein
   frischer Opus-Agent liest `README.md`, `docs/tools.md`,
   `docs/installation.md`, `docs/development.md` und den neuen
   CHANGELOG-Abschnitt gegen
   `git diff $(git describe --tags --abbrev=0)..HEAD -- chempane/`
   und meldet je Satz, der nicht mehr stimmt: Datei:Zeile, Aussage, Beleg im
   Diff. Fragen an ihn: Beschreibt jeder Absatz noch, was das Tool tut? Fehlt
   eine neue Funktion, ein neuer Parameter oder eine neue Grenze? Stehen
   Grenzen unter *Limitations*, die nicht mehr gelten? Stimmen ungeprüfte
   Zahlen („About 8,000 Python tests“, Messwerte mit Datum)? Befunde beheben,
   bevor getaggt wird; eine README-Änderung erreicht PyPI erst mit dem Release.
2. CI abwarten (`gh run watch`).
3. `gh release create vX.Y.Z` — löst `publish.yml` und damit PyPI aus.
4. PyPI-Landung abwarten.
5. Registry-Publish im `registry`-Job prüfen; `./scripts/publish-registry.sh` verifiziert den Eintrag.
6. `isLatest` verifizieren.
