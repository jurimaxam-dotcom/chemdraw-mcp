# For developers

Where to start if you want to read, test or change the code. This page only
points the way; the details are in [development.md](development.md) and
[CONTRIBUTING.md](../CONTRIBUTING.md).

## Set up and run the gate

```bash
git clone https://github.com/jurimaxam-dotcom/chemdraw-mcp.git && cd chemdraw-mcp
uv sync
cd chemdraw_tool/ui && npm install && npx playwright install chromium && cd -
./test.sh
```

`./test.sh` is the one green/red check: lint, about 10,000 Python tests, bundle
freshness and the JavaScript unit and browser tests. Outside the gate, each
needing network:

- `./scripts/handshake.sh`: a real stdio handshake with the command Claude
  Desktop has registered; checks the tool counts per profile.
- `npm --prefix chemdraw_tool/ui run test:host`: the panel in a sandboxed
  iframe behind a real AppBridge host and the real server.
- `uv run python scripts/identitaet.py`: name → InChIKey for the pinned list in
  `tests/identity/stoffe.json`.

## Where things are

- `chemdraw_tool/server.py`: the MCP server and every tool definition; the
  profile split (`MVP_TOOLS`) and the server instructions.
- `chemdraw_tool/resolver.py`: input → structure (SMILES first, then OPSIN,
  PubChem, NCI; peptides, proteins and fixed names).
- `chemdraw_tool/ui/`: the panel, a React app served as an MCP App resource.
  The server serves the built `dist/`, so rebuild after changing `src/`.
- The architecture overview, the pipeline and the five tool areas are in
  [development.md](development.md) and in `CLAUDE.md` at the repository root.

## Rules that are tested

- Tests first; a failing test before production code.
- Tool names, descriptions and schemas are frozen as snapshots
  (`tests/__snapshots__/tools/`); a reworded description changes which tool the
  model picks.
- A new tool is entered in one of five areas in `tests/test_server_taxonomy.py`.
- Golden SVGs and the layout guard catch drawing drift; they are never
  regenerated just to make a diff go away.
- The docs are checked too: tool names, counts, environment variables,
  commands, repository paths and every relative link and image in the user
  pages (`tests/test_docs_consistency.py`, `tests/test_readme.py`,
  `tests/test_user_docs.py`).

## Limits

- The gate runs in-process. A stale Claude Desktop process or a launcher that
  the minimal GUI PATH cannot find shows up only in `./scripts/handshake.sh`
  or a hand test.
- The panel's behaviour inside Claude Desktop itself is checked by hand.
