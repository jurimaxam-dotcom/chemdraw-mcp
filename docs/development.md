# Development

How chemdraw-mcp is built and tested. Python 3.11+, package manager `uv`.

## How it works

```
name / SMILES
   │
   ▼
resolver ──► OPSIN (systematic IUPAC names, offline) ──► PubChem / NCI (names, plus English / salt / form spellings)  ·  direct parse (SMILES)
   │         direct hits are cross-checked against the other source (de_names.py, resolver.py)
   │
   ▼
RDKit 2D coordinates ──► validation (sanity, round-trip)
   │
   ├──► image_export   → PNG + SVG files          (primary, offline)
   ├──► svg_renderer   → interactive chat preview (MCP App resource)
   └──► cdxml_writer   → ChemDraw CDXML           (optional, on request)
```

The lab graphics (`spectrum.py`, `tlc.py`, `ph_plots.py`) render with
matplotlib; the panel is a React app served by the server as an MCP App
resource.

## Setup and tests

```bash
uv sync                      # backend dependencies
cd chemdraw_tool/ui && npm install && npx playwright install chromium  # frontend, once
./test.sh                    # the gate: lint, pytest, bundle freshness, JS unit and browser tests
```

About 8,400 Python tests plus JavaScript unit and headless-Chromium tests,
written test-first. Frozen renderings guard the drawing output, a pinned
identity list guards name resolution, and snapshots of every tool description
guard which tool the model picks.

The README images in `assets/` come from `scripts/readme_bilder.py`, not from
hand edits; `tests/test_readme.py` pins their hashes.
The three panel GIFs (`demo-views`, `demo-3d`, `demo-molecule`) are recorded in the
panel test host, dark theme at 600 px: `npm --prefix chemdraw_tool/ui run readme:gifs`
(needs network; checks width, duration and size of each GIF).
