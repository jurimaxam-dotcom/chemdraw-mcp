# Contributing to chemdraw-mcp

Thanks for looking. Bug reports, wrong structures, missing names and small
fixes are all welcome. Questions and ideas belong in
[Discussions](https://github.com/jurimaxam-dotcom/chemdraw-mcp/discussions);
concrete bugs and tasks in Issues.

## Setup

```bash
git clone https://github.com/jurimaxam-dotcom/chemdraw-mcp.git
cd chemdraw-mcp
uv sync                                    # Python deps (Python 3.11+, uv)
cd chemdraw_tool/ui && npm install && npx playwright install chromium && cd -
./test.sh                                  # the gate: lint + backend + bundle + frontend
```

`./install.sh` additionally registers the server in Claude Desktop. Restart
Claude Desktop after changing server code — it keeps the old process alive.

## How changes are made here

- **Tests first.** Write a failing test, see it red, then change the code.
  `./test.sh` must be green before a pull request.
- **A wrong molecule is the worst bug.** If you touch name resolution, add the
  case to `tests/identity/stoffe.json` (input → expected InChIKey) and run
  `uv run python scripts/identitaet.py` (needs network).
- **Tool descriptions are tested text.** The model picks a tool from its name
  and description alone. A new tool must be entered in
  `tests/test_server_taxonomy.py` (one of the five areas in `CLAUDE.md`).
  If you change a description on purpose, bless the snapshot in the same
  commit: `UPDATE_TOOLSNAPS=1 uv run pytest tests/test_tool_snapshots.py`.
- **Frozen renderings are not regenerated to make a diff disappear.**
  `tests/__fixtures__/*.golden.svg` changes only for an intended rendering
  change, and you look at the result.
- **Panel changes need a rebuilt bundle** (`chemdraw_tool/ui/dist/`); the gate
  checks that it matches `src/`.
- **Rendering defaults stay as they are.** New options are opt-in.

User-facing text (tool descriptions, README, doctor output) is English. Code
comments and commit messages in this repo are mostly German; English is fine
in contributions.

## Good first contributions

Issues labelled `good first issue` are small and come with the file to start
from. Adding identity cases or tool-routing cases
(`evals/tool-routing/cases.yaml`) needs no rendering knowledge at all.

## License

By contributing you agree that your contribution is licensed under the
project's [Apache-2.0 license](LICENSE).
