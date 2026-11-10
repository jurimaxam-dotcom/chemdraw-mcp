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

About 9,800 Python tests plus JavaScript unit and headless-Chromium tests,
written test-first. Frozen renderings guard the drawing output, a pinned
identity list guards name resolution, and snapshots of every tool description
guard which tool the model picks.

The README images in `assets/` come from `scripts/readme_bilder.py`, not from
hand edits; `tests/test_readme.py` pins their hashes.
The three panel GIFs (`demo-views`, `demo-3d`, `demo-molecule`) are recorded in the
panel test host at 600 px, each in a light and a dark version (`assets/demo-<scene>-light.gif`,
`-dark.gif`; the README picks one via `<picture>`/`prefers-color-scheme`):
`npm --prefix chemdraw_tool/ui run readme:gifs` records all scenes in both themes;
`-- views 3d --theme dark` limits scenes and theme, `--molecule NAME` swaps the molecule.
The two hero scenes share one fixed 600×880 crop. The script needs network and turns red
on width, duration, size, frame rate, a cut-off panel part or unequal hero sizes. The old
names `demo-views.gif`, `demo-3d.gif` and `demo-molecule.gif` stay as copies of the light
versions because PyPI and older release notes link them.

`npm --prefix chemdraw_tool/ui run panel:clips` (`readme:gifs --video`) records the same scenes
and click sequences as raw footage for YouTube Shorts: one H.264/yuv420p MP4 per scene and theme,
30 fps, 1080 px wide (captured at device scale factor 2, i.e. 1200 px, then scaled), panel height
without border (views 1080×1602, 3d 1080×1584, molecule 1080×1494), longer holds than the GIFs
(1.2 s before each click, 3 s final state), 12–25 s. Next to each `<scene>-<theme>.mp4` it writes
`<scene>-<theme>.beats.json` (click and hover times in seconds, as a flat map and as the `Beat[]`
list the Remotion montage reads) and a 360 px preview still at 40 %. Output goes to
`~/Documents/projects/chemdraw-vermarktung/out/panel-clips/` (not versioned there). The script checks
codec, pixel format, frame rate, size and duration with ffprobe and turns red on any deviation.
