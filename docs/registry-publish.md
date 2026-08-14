# Registry-Publish: warum er zweimal vergessen wurde und wie er automatisch wird

Der Eintrag in der offiziellen MCP-Registry ist ein **Snapshot**. Ein Edit an
`server.json` plus Commit ändert ihn nicht — nur ein expliziter Publish-Lauf tut
das. Genau deshalb lieferte die Registry von Juni bis August 2026 weiter die
Version 0.2.0 mit dem Panel-Bug aus, obwohl PyPI längst 0.2.1 hatte und
`server.json` im Repo ebenfalls.

## Von Hand (Stand heute)

```bash
./scripts/publish-registry.sh   # Login + Publish + Verifikation in einem Lauf
```

Das Skript prüft vorher, ob die Version überhaupt auf PyPI liegt (sonst lehnt
die Registry ab), und meldet am Ende, ob der Eintrag wirklich steht — die
Erfolgsmeldung von `publish` allein ist kein Beweis.

Einzelschritte, falls etwas hakt:

```bash
mcp-publisher login github      # Device-Flow, interaktiv; der Code läuft nach
                                # wenigen Minuten ab — erst starten, wenn man
                                # den Browser wirklich gleich bedient
mcp-publisher publish           # liest server.json aus dem CWD
```

Danach verifizieren — nicht auf die Erfolgsmeldung verlassen:

```bash
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=jurimaxam" \
  | python3 -c "import json,sys; [print(s['server']['version'], s['_meta']['io.modelcontextprotocol.registry/official']['isLatest']) for s in json.load(sys.stdin)['servers']]"
```

`isLatest: True` muss an der neuen Version stehen.

**Reihenfolge ist Pflicht:** erst PyPI, dann Registry. Die Registry prüft beim
Publish, ob das referenzierte PyPI-Paket in der angegebenen Version existiert —
läuft der Publish vorher, scheitert die Validierung.

## Automatisch (empfohlen)

In GitHub Actions braucht es keinen interaktiven Login: `mcp-publisher login
github-oidc` authentifiziert über das OIDC-Token des Workflows. Damit hängt der
Registry-Eintrag am Release statt an jemandes Erinnerung.

Der folgende Job gehört ans Ende von `.github/workflows/publish.yml`, hinter den
bestehenden `publish`-Job. Er ist hier abgelegt statt eingebaut, weil der
OAuth-Token dieser Arbeitsumgebung keine Workflow-Dateien schreiben darf
(`gh auth refresh -s workflow` hebt das auf).

```yaml
  registry:
    needs: publish
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v6

      # Die Registry validiert die PyPI-Referenz — erst warten, bis die
      # Version wirklich abrufbar ist, sonst schlägt der Publish fehl.
      - name: Wait for PyPI
        run: |
          VERSION=$(python3 -c "import json;print(json.load(open('server.json'))['version'])")
          for i in $(seq 1 30); do
            if curl -sf -o /dev/null "https://pypi.org/pypi/chemdraw-mcp/$VERSION/json"; then
              echo "chemdraw-mcp $VERSION ist auf PyPI"; exit 0
            fi
            sleep 10
          done
          echo "::error::chemdraw-mcp $VERSION nach 5 min nicht auf PyPI"; exit 1

      - name: Install mcp-publisher
        run: |
          curl -sSL "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_amd64.tar.gz" \
            | tar xz mcp-publisher
          sudo mv mcp-publisher /usr/local/bin/

      - name: Publish to MCP registry
        run: |
          mcp-publisher login github-oidc
          mcp-publisher publish

      - name: Verify the entry is live
        run: |
          VERSION=$(python3 -c "import json;print(json.load(open('server.json'))['version'])")
          LATEST=$(curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=jurimaxam" \
            | python3 -c "import json,sys;print(next((s['server']['version'] for s in json.load(sys.stdin)['servers'] if s['_meta']['io.modelcontextprotocol.registry/official']['isLatest']), 'keine'))")
          [ "$LATEST" = "$VERSION" ] || { echo "::error::Registry meldet $LATEST statt $VERSION"; exit 1; }
          echo "Registry liefert $LATEST aus"
```

Einmalige Voraussetzung auf Registry-Seite: Der GitHub-Namensraum
`io.github.jurimaxam-dotcom/*` muss dem Repository gehören — das ist durch den
bestehenden Eintrag bereits erfüllt.

## Release-Reihenfolge im Ganzen

1. Version in `pyproject.toml` **und** `server.json` (Top-Level *und*
   `packages[0].version`) ziehen, CHANGELOG ergänzen, committen, pushen.
2. CI abwarten (`gh run watch`).
3. `gh release create vX.Y.Z` — löst `publish.yml` und damit PyPI aus.
4. PyPI-Landung abwarten.
5. Registry publizieren (automatisch per Job oben, sonst von Hand).
6. `isLatest` verifizieren.
