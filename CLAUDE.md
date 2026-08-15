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
```

One-time frontend setup: `cd chemdraw_tool/ui && npm install && npx playwright install chromium`

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

## The four tool areas (where a new tool goes)

The model picks a tool from its name and description alone, so a fuzzy boundary
is a precision bug, not cosmetics — "draw aspirin" once landed in
`generate_scope_table` and produced a one-cell grid. Since then the tool set is
a tested promise in `tests/test_server_taxonomy.py`:

| Area | Tools | What belongs here |
|---|---|---|
| Draw | generate_molecule · compare_molecules · batch_generate · generate_reaction · generate_mechanism · generate_scope_table · generate_3d | structures and reactions |
| Lab graphics | generate_spectrum · generate_tlc · generate_titration_curve · generate_species_distribution | measured data as a diagram |
| Look up | lookup · lookup_molecule_data | database queries |
| Anki | export_anki_deck | flashcard decks |

Outside the areas sits exactly one tool: `save_png`, the server half of the
panel's export button. It stays registered because the UI calls it by name
(`ExportPngButton.jsx`), and its description marks it internal so the model
never calls it on its own — saving a picture is the user's click.

**Adding a tool means picking an area and entering it in the taxonomy test.**
The test fails on an unlisted tool by design. Two more rules keep the set
selectable: any tool confusable with an existing one must carry a
`Not this tool for: … — use X` line naming the alternative (also test-enforced),
and the set stays at 16 or fewer without a deliberate decision.

Prefer a parameter over a new tool when the output is the same kind of thing —
that is why the five text lookups are one `lookup` with a `topic` literal, and
the curated decks are a `curated_deck_id` parameter.

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
├── calculator/            — Ph.Eur. content-determination math (pure functions;
│                            no tool exposes it right now — kept because the
│                            math is tested and re-wiring it is cheap)
├── payloads.py            — Pydantic models for MCP structured output;
│                            each `type` needs a matching case in App.jsx
├── png_writer.py          — client-rendered PNG → file
├── vault.py               — optional notes lookup (only if CHEMDRAW_VAULT_PATH)
├── chemdraw.py            — macOS AppleScript bridge (no tool right now; CDXML
│                            stays available as an output format)
├── desktop_config.py      — Claude Desktop registration (chemdraw-install)
├── doctor.py              — installation diagnosis (chemdraw-doctor)
├── server.py              — FastMCP server (stdio) + tool definitions
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
  genanki (OPSIN needs a JRE at runtime; without one the resolver degrades to
  PubChem/NCI — never make Java a hard requirement)
