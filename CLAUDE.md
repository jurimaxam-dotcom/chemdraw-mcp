# chemdraw-mcp

MCP server for Claude Desktop that turns molecule names or SMILES into
publication-style 2D structure drawings. PNG/SVG are the primary outputs
(rendered offline via RDKit) — ChemDraw CDXML is an optional extra format,
never a runtime requirement.

## Build / Run

```bash
./install.sh                 # one-command setup: uv + deps + Claude Desktop config
uv sync                      # deps only
uv run chemdraw-tool-server  # run the MCP server (stdio) manually
uv run chemdraw-doctor       # diagnose the installation (env, paths, network)
```

`install.sh` registers the server via `chemdraw_tool/desktop_config.py`
(idempotent merge, writes a `.bak` backup, never touches other configured MCP
servers). The config logic lives in the package, not in `scripts/`, because the
wheel ships only `chemdraw_tool` — PyPI users get `chemdraw-install` and a fully
working `chemdraw-doctor` from it. Claude Desktop launches MCP servers with a
minimal GUI PATH, so `command` must be an absolute path; the installer resolves
it and prints what it wrote.

**If a host keeps the server process alive (Claude Desktop does), restart it
after changing server code or dependencies** — a stale process mixes old
in-memory modules with new files and manifests as confusing RDKit/Boost
signature errors. Restart it yourself after such changes (`osascript -e 'quit
app "Claude"' && sleep 2 && open -a Claude`); an MCP stdio handshake
(initialize → tools/list) is the hard proof that the registered command works.

## Auto-Gate (the project's green/red)

```bash
./test.sh                                     # lint + backend + bundle + frontend
npm --prefix chemdraw_tool/ui run test:watch  # JS unit tests in watch mode
./scripts/handshake.sh                        # real stdio handshake (needs network)
```

One-time frontend setup: `cd chemdraw_tool/ui && npm install && npx playwright install chromium`

`handshake.sh` sits **outside** the gate because its first run downloads the MCP
Inspector. It is the only check that starts the server the way Claude Desktop
does — the absolute command out of `claude_desktop_config.json` — and asserts
the two numbers the Python side predicts (currently 20 tools, 14 with a panel).
In-process tests cannot see the two failure modes that have actually cost time
here: a stale server process and a GUI PATH that cannot find `uv`.

The gate is built against two failure modes that cost more than a real test
failure:

- **false red** — the dependency guard launches the actual Chromium build
  instead of checking that the cache folder exists (an existing folder with the
  wrong build killed the gate with the very stacktrace the guard exists to
  prevent). Playwright is pinned to one exact version on both sides.
- **false green** — the server serves `chemdraw_tool/ui/dist/`, not `src/`, so
  the gate rebuilds the bundle and compares bytes. `package-lock.json` is
  versioned to keep that comparison deterministic across machines.

Two frozen renderings guard against silent visual drift, and **neither may be
regenerated to make a diff disappear**:

- `tests/__fixtures__/*.golden.svg` — the Python renderer's default output
  (both paths: UI preview and file export). Regenerate only for an intentional
  rendering change or an RDKit bump, and look at the result.
- `chemdraw_tool/ui/src/utils/__fixtures__/aspirin.expected.png` — the JS
  rasterization, machine-specific, `npm run test:e2e:update` once per machine.

A third frozen set covers the text the model actually reads:
`tests/__snapshots__/tools/*.json` pins each tool's name, description and schemas.
A diff is red on purpose — a reworded description changes which tool the model
picks. Bless it deliberately with `UPDATE_TOOLSNAPS=1 uv run pytest
tests/test_tool_snapshots.py`, in the same commit that changes the text.

## The five tool areas (where a new tool goes)

The model picks a tool from its name and description alone, so a fuzzy boundary
is a precision bug, not cosmetics — "draw aspirin" once landed in
`generate_scope_table` and produced a one-cell grid. Since then the tool set is
a tested promise in `tests/test_server_taxonomy.py`:

| Area | Tools | What belongs here |
|---|---|---|
| Draw | generate_molecule · compare_molecules · batch_generate · generate_reaction · generate_mechanism · generate_scope_table · generate_3d | structures and reactions |
| Lab graphics | generate_spectrum · generate_tlc · generate_titration_curve · generate_species_distribution · generate_calibration_curve | measured data as a diagram |
| Look up | lookup · lookup_molecule_data · predict_spectrum | facts about a substance, from a database or derived from its structure |
| Calculate | calculate_solution · calculate_content · calculate_ph | a number **and** the working behind it |
| Anki | export_anki_deck | flashcard decks |

Outside the areas sits exactly one tool: `save_png`, the server half of the
panel's export button. It stays registered because the UI calls it by name
(`ExportPngButton.jsx`), and its description marks it internal so the model
never calls it on its own — saving a picture is the user's click.

**Adding a tool means picking an area and entering it in the taxonomy test.**
The test fails on an unlisted tool by design. Two more rules keep the set
selectable: any tool confusable with an existing one must carry a
`Not this tool for: … — use X` line naming the alternative (also test-enforced),
and the count has a ceiling that is only ever raised deliberately, with the
reason written into the test (16 → 18 for the calculating area, → 19 for the
calibration curve, → 20 for the spectrum prediction).

**Delimit in both directions.** The tool that fails to exclude a case is the
one that wins it. `generate_titration_curve` therefore points at
`calculate_ph` just as much as the other way round — a one-sided fence
reproduces the aspirin misfire with new names.

**A fence does not help against an underspecified prompt.** A bare compound
name ("caffeine") names no tool's job, so it goes to whichever description
sounds most like it — which is why `lookup` used to win it with the sentence
"the right choice whenever the user just asks 'what is X'". The answer is not a
sharper fence but a stated default: `generate_molecule` claims the bare name in
writing, and the server's `instructions=` says so once before any tool
description is read. Both are test-enforced.

Two more rules follow from the same measurements
([research report](https://claude.ai/code/artifact/6fa21f2d-6223-4637-90e1-ad4b1cf99ea7)):

- **Describe, never advertise.** A superlative moves a tool's usage share
  measurably (7.48 : 1 for one appended sales sentence, arXiv:2505.18135)
  *without* improving accuracy — it steals calls from its neighbours. The
  taxonomy test greps for the usual phrases.
- **Stay under 2 KB per description.** Claude Code truncates there, from the
  end. Cut the parameter docs, never a fence.

Prefer a parameter over a new tool when the output is the same kind of thing.
That is why the five text lookups are one `lookup` with a `topic` literal, the
curated decks are a `curated_deck_id` parameter, and the fat characteristics
(acid/saponification/iodine value, Karl Fischer) are `method` values of
`calculate_content` rather than four more tools.

**Prompt → tool is a test, not a story.** `evals/tool-routing/cases.yaml` holds
the cases; `tests/test_eval_cases.py` keeps them in sync with the tool list
without touching the network and goes red when a fence has no case. The scored
run needs an API key — see `evals/README.md`.

## Architecture

```
chemdraw_tool/
├── resolver.py            — parse-first (SMILES wins if it parses: "O" is water,
│                            not O₂), then a 5-step name cascade: OPSIN (offline,
│                            needs Java; degrades gracefully) → PubChem →
│                            PubChem transliterated (ä→ae) → NCI CIR ×2.
│                            Errors carry a `kind`: not_found / offline /
│                            sources_down / partial — the message tells the user
│                            what actually helps
├── generator.py           — RDKit 2D coordinates
├── image_export.py        — PNG/SVG file rendering (primary output path)
├── svg_renderer.py        — SVG for the embedded UI preview (shared BOND_LINE_WIDTH)
├── render_style.py        — named render profiles (compact/presentation/grayscale)
│                            + group abbreviation; "" always means today's look
├── spectrum.py            — schematic spectra from peak lists (matplotlib → PNG/SVG)
├── tlc.py                 — TLC plates from Rf values (lanes × spots)
├── scope.py               — substrate-scope figures (structure grid + captions)
├── cdxml_writer.py        — RDKit mol → ChemDraw CDXML (optional format)
├── layout.py              — reaction scheme layout (arrows, +, conditions)
├── mechanism*.py          — reaction mechanism definitions/coords/rendering
├── structure3d.py         — 3D conformer for the rotatable viewer
├── databases.py           — PubChem / ChEBI / KEGG / UniProt lookups
├── ph_plots.py            — titration curves + species distribution
├── anki_export.py         — .apkg decks with rendered images
├── curated_decks.py       — bundled starter decks
├── validator.py           — input validation + CDXML round-trip validation
├── solution.py            — weighing, dilution, mixing cross, molar mass
│                            (molmass — it parses hydrates, RDKit cannot)
├── ph_calc.py             — pH/buffer numbers; shares `ph_plots.exact_ph`
│                            with the curve, so figure and number agree
├── calibration.py         — least squares, read-back, LOD/LOQ (DIN 32645)
├── calibration_plot.py    — the calibration figure (reuses ph_plots helpers)
├── spectro.py             — expected IR bands (curated table × SMARTS) and
│                            ¹H signal counts; no ppm shifts on purpose
├── calculator/            — Ph.Eur. content determination + fat characteristics
│                            (titration, photometry, stats incl. Grubbs,
│                            fat_values); pure functions behind calculate_content
├── payloads.py            — Pydantic models for MCP structured output;
│                            each `type` needs a matching case in App.jsx
├── png_writer.py          — client-rendered PNG → file
├── vault.py               — optional notes lookup (only if CHEMDRAW_VAULT_PATH)
├── chemdraw.py            — macOS AppleScript bridge (no tool right now; CDXML
│                            stays available as an output format)
├── desktop_config.py      — Claude Desktop registration (chemdraw-install)
├── doctor.py              — installation diagnosis (chemdraw-doctor)
├── server.py              — FastMCP server (stdio) + tool definitions;
│                            `_INSTRUCTIONS` is the area map the client may put
│                            in the system prompt — the one place the five
│                            areas are explained once instead of 20 times
└── ui/                    — embedded MCP App UI (React/Vite, served as resource)
```

Pipeline: input (name/SMILES) → resolver → RDKit 2D → image_export (PNG/SVG)
[→ cdxml_writer if requested] → `~/ChemDraw-Output/`

Output formats: `generate_*` tools accept `formats=["png","svg","cdxml"]`,
default `["png","svg"]`. CDXML only on explicit request, and only for actual
structures (a TLC plate or scope figure is not one).

**Adding a panel tool is a five-link chain** — miss one and the panel silently
shows nothing: renderer → payload model with a `type` default → tool with
`meta=_UI_META` → View component + `case` in `ui/src/App.jsx` → rebuild the
bundle. Tests enforce every link (panel tools are derived from the FastMCP
registration, payload types are compared against App.jsx cases in both
directions, the gate checks bundle freshness). Removing one walks the same
chain backwards — and the bundle rebuild is just as mandatory.

Test output paths are redirected with `monkeypatch.setattr` against
`chemdraw_tool.server.<DIR>`. `tests/conftest.py` compares the real
`~/ChemDraw-Output` before and after the suite, so a redirect that points
nowhere fails loudly instead of quietly writing into the user's folder.

## Conventions

- Python 3.11+, package manager: `uv`
- Tests: pytest, TDD (red first — no production code without a failing test)
- UI preview and exported files must stay visually consistent
  (shared constants like `BOND_LINE_WIDTH`; parity is test-enforced per style)
- New rendering options are opt-in; the default output must not change
- User-facing text (tools, docstrings, README, doctor output) is English;
  code comments and commits are German
- Dependencies: rdkit, lxml, requests, mcp, Pillow, matplotlib, py2opsin,
  genanki, molmass (OPSIN needs a JRE at runtime; without one the resolver
  degrades to PubChem/NCI — never make Java a hard requirement). Weigh every
  new dependency against what it drags in: `molmass` earned its place with
  zero required dependencies of its own, while `chempy`, `pint` and `mendeleev`
  were rejected for pulling in scipy/pandas/sympy-sized trees.
