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
```

`install.sh` registers the server in Claude Desktop via
`scripts/install_claude_config.py` (idempotent merge, writes a `.bak` backup,
never touches other configured MCP servers).

**After changing server code or dependencies, restart Claude Desktop** —
it keeps the server process alive, and a stale process mixes old in-memory
modules with new files (manifests as confusing RDKit/Boost signature errors).

## Auto-Gate (the project's green/red)

```bash
./test.sh                                     # full pipeline: backend + frontend
npm --prefix chemdraw_tool/ui run test:watch  # JS unit tests in watch mode
```

One-time frontend setup: `cd chemdraw_tool/ui && npm install && npx playwright install chromium`

The e2e test rasters a real RDKit SVG in headless Chromium and compares an
exact pixel snapshot. The snapshot is machine-specific: regenerate once per
machine with `npm --prefix chemdraw_tool/ui run test:e2e:update` — never
regenerate it just to make a diff disappear.

## Architecture

```
chemdraw_tool/
├── resolver.py            — SMILES detection + name→SMILES cascade:
│                            OPSIN (offline, needs Java; degrades gracefully)
│                            → PubChem → NCI
├── generator.py           — RDKit 2D coordinates
├── image_export.py        — PNG/SVG file rendering (primary output path)
├── svg_renderer.py        — SVG for the embedded UI preview (shared BOND_LINE_WIDTH)
├── spectrum.py            — schematic spectra from peak lists (matplotlib → PNG/SVG)
├── cdxml_writer.py        — RDKit mol → ChemDraw CDXML (optional format)
├── layout.py              — reaction scheme layout (arrows, +, conditions)
├── mechanism*.py           — reaction mechanism definitions/coords/rendering
├── databases.py           — PubChem / ChEBI / KEGG / UniProt lookups
├── validator.py           — input validation + CDXML round-trip validation
├── calculator/            — Ph.Eur. content-determination math (pure functions)
├── payloads.py            — Pydantic models for MCP structured output
├── chemdraw.py            — optional macOS AppleScript bridge to ChemDraw
├── server.py              — FastMCP server (stdio) + tool definitions
└── ui/                    — embedded MCP App UI (React/Vite, served as resource)
```

Pipeline: input (name/SMILES) → resolver → RDKit 2D → image_export (PNG/SVG)
[→ cdxml_writer if requested] → `~/ChemDraw-Output/`

Output formats: `generate_*` tools accept `formats=["png","svg","cdxml"]`,
default `["png","svg"]`. CDXML only on explicit request.

## Conventions

- Python 3.11+, package manager: `uv`
- Tests: pytest, TDD (red first — no production code without a failing test)
- UI preview and exported files must stay visually consistent
  (shared constants like `BOND_LINE_WIDTH`; parity is test-enforced)
- Dependencies: rdkit, lxml, requests, mcp, Pillow, matplotlib, py2opsin
  (OPSIN needs a JRE at runtime; without one the resolver degrades to
  PubChem/NCI — never make Java a hard requirement)
