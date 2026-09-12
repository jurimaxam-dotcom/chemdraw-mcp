# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- **The number beside a functional group counted atoms, not groups.**
  Methylphenidate showed "Ester 5" for a single ester — those were the five
  highlighted atoms. Groups are counted as matches now (aromatics as rings), and
  only matches that actually own their atoms are highlighted, so the ether
  inside an ester is no longer tagged twice.
- **The compound behind the numbers can be the wrong record.** PubChem answers
  the metformin SMILES with `[14C]metformin` (CID 152743144) instead of the
  parent record CID 4091 — same structure, same InChIKey, but no CAS number, so
  the panel simply showed none. Properties and synonyms are now fetched by
  InChIKey (computed locally by RDKit), which returns the parent record first;
  the SMILES route stays as a fallback when PubChem does not know the key.

### Changed

- **"LogP" is labelled "XLogP"** in the panel, the data sheet and `lookup`'s
  text output. The value is PubChem's computed XLogP, not a measured partition
  coefficient — RDKit's Crippen estimate for methylphenidate is 2.09 against
  PubChem's 0.2, and a number that size deserves its source in its name.

### Added

- **The panel names the PubChem record its numbers come from** ("PubChem:
  Methylphenidate (CID 4158)"). Costs no extra request, and it is the one place
  where a mis-resolved name becomes visible — below it, everything is
  consistently wrong together.
- **`scripts/identitaet.py` + `tests/identity/stoffe.json`**: 24 inputs pinned to
  their InChIKey, run live against OPSIN/PubChem/NCI. Red only for a wrong
  substance, yellow for a dead source — outside the gate, like `handshake.sh`.

## [0.4.1] — 2026-09-12

### Fixed

- **0.4.0 shipped without the chat panel.** The wheel lacked
  `chemdraw_tool/ui/dist/index.html`: a `dist/` line added to `.gitignore` for
  the release artefacts also matched the UI build folder, and hatchling filters
  wheel contents by `.gitignore`. Tools still ran and files were written, but
  every panel showed "cannot be reached". The pattern is anchored now, and a
  test builds the wheel and checks that the panel is inside.

## [0.4.0] — 2026-09-12

The tool set becomes five areas with drawn boundaries, and gains the maths a
lab report actually asks for. The trigger was a real misfire: "draw aspirin"
was answered with `generate_scope_table`, a substrate grid holding a single
cell. The model picks a tool from its name and description alone, so 22 tools
with fuzzy edges are a precision problem.

### Breaking — 22 tools become 20

Existing Claude Desktop entries keep working (`chemdraw-tool-server` stays as
a launcher alias). Saved prompts or scripts that name a removed tool need the
new name:

| Gone | Use instead |
|---|---|
| `lookup_compound`, `lookup_safety`, `lookup_physical`, `lookup_biochem`, `lookup_pathway` | `lookup` with `topic=properties / safety / physical / biochem / pathway` |
| `export_curated_deck` | `export_anki_deck` with `curated_deck_id` |
| `calculate_validation` | removed for now (the maths stays in `calculator/`) |
| `open_chemdraw_file` | removed for now (CDXML remains an output format) |

### Added — installation

- **Claude Desktop bundle (`.mcpb`).** Download
  `chemdraw-mcp-<version>.mcpb` from the release, double-click it, restart
  Claude Desktop. The bundle is a launcher, not a vendored runtime — RDKit is
  a native extension and a self-contained bundle would weigh over 100 MB per
  platform. On first start it fetches the package from PyPI via `uv`
  (installed to `~/.local/bin` if missing) and caches it; from then on the
  server starts offline. macOS and Linux. Built by `scripts/build-mcpb.sh`,
  attached to every release by CI.
- **Registry publish runs in CI** (OIDC) after the PyPI upload, so the
  registry entry can no longer lag behind the package the way it did from
  June to August.

### Fixed

- **Fresh installs from PyPI failed to start since 2026-08-26.** The `mcp`
  dependency was unpinned, `mcp` 2.0 renamed `FastMCP` to `MCPServer`, and
  `uvx chemdraw-mcp` resolved the new major — the server died on import with
  `No module named 'mcp.server.fastmcp'`. Development installs were unaffected
  because the lockfile held 1.27.1, which is why it went unnoticed. Pinned to
  `mcp>=1.27,<2`; the migration to 2.x is separate work.

- **Tool descriptions on Python 3.11/3.12 carried their docstring
  indentation.** Python 3.13 strips it at compile time, older versions do
  not, and FastMCP passes `__doc__` through unchanged — so users on 3.11
  or 3.12 got longer descriptions, five of them past the 2 KB cap that
  Claude Code truncates at, cutting the parameter docs at the end. The
  server now applies `inspect.cleandoc` itself; CI runs on 3.11 and 3.13
  so the two can no longer drift apart unnoticed.

### Added — bench maths

Every calculation returns the working, not just the number: formula, numbers
substituted, result. That is what the lab report wants, and what makes the
answer checkable.

- **`calculate_solution`** — what to weigh in, what you actually got,
  dilutions, the mixing cross, and molar masses. Handles hydrates
  (`CuSO₄·5H₂O`), which RDKit cannot parse, via the new `molmass` dependency
  (BSD-3, no dependencies of its own). Denies the impossible instead of
  computing it: diluting cannot make a solution stronger, and a mixing target
  outside its components has no solution. Warns when the portion falls below
  the resolution of an analytical balance.
- **`calculate_content`** — the content determination in the order the
  protocol prescribes: content per measurement → Grubbs outlier test → mean
  and spread → t-test against the declared content. Titration (with titer
  determination from reference titrations) and photometry; the fat
  characteristics (acid, saponification, ester, iodine value) and Karl
  Fischer water content are further methods rather than four more tools.
  A flagged outlier is reported, never silently dropped from the mean.
- **`calculate_ph`** — weak and strong acids and bases, buffers, buffer
  recipes down to weighable masses. Solved through the same exact charge
  balance that draws the titration curve, with the textbook approximation
  printed beside it; where the two disagree, the approximation has lost its
  assumptions and the output says so. 10⁻⁸ M HCl gives pH 6.98, not 8.

### Added — figures and spectra

- **`generate_calibration_curve`** — the least-squares line through your
  standards, with unknown samples read back off it and marked on the plot.
  Extrapolation beyond the calibrated range is labelled, not hidden; limits
  of detection and quantitation follow DIN 32645.
- **`predict_spectrum`** — expected IR bands for a structure (curated table
  matched by SMARTS), the possible assignments of a measured wavenumber, and
  the number of ¹H signals with their integral ratio. Deliberately
  deterministic, and it names its own limits: no ppm shifts, and
  diastereotopic protons counted as one signal.
- **`grubbs_test`** in `calculator/stats.py` — the outlier step the protocol
  form demands and the statistics module was missing.
- `PlotPayload` gained an optional `notes` list, rendered by the panel, for
  numbers that belong to a figure but not in its subtitle.

### Added — panel and routing

- **Structure ⇄ data toggle in the panel.** Both the molecule view and the
  data sheet carry the same structure data, so switching to the structure is
  instant and local; the data sheet is fetched once on click and cached.
- **Area map in the server instructions.** The five areas are explained once,
  before any tool description is read, and `generate_molecule` claims the bare
  compound name ("caffeine") in writing — previously `lookup` won it.
- **A real stdio handshake** (`scripts/handshake.sh`) starts the server the
  way Claude Desktop does and asserts the tool count; frozen tool snapshots
  (`tests/__snapshots__/tools/`) and a prompt→tool case file
  (`evals/tool-routing/cases.yaml`) pin the text the model actually reads.

### Changed

- **Tool descriptions state what they are NOT for** and name the alternative.
  `generate_scope_table` now rules out the single molecule explicitly; the
  drawing tools point at each other. Test-enforced for every confusable pair.
- **`lookup` replaces the five text lookups.** One tool, one `topic` parameter
  (`properties`, `safety`, `physical`, `biochem`, `pathway`) typed as a literal
  so the schema itself limits the choice. An unknown topic raises instead of
  quietly returning the default. `lookup_molecule_data` stays as the visual
  panel and both now cross-reference each other.
- **`export_curated_deck` became a parameter.** `export_anki_deck` takes
  `curated_deck_id`; both paths shared one payload and one panel anyway.
- **`save_png` is declared internal.** It is the server half of the panel's
  export button and stays registered so the UI can call it, but the model is
  told never to invoke it — saving a picture is the user's click.
- **Boundaries are drawn in both directions.** The tool that fails to exclude
  a case is the one that wins it, so `generate_titration_curve` and
  `generate_species_distribution` now point at `calculate_ph` as explicitly as
  it points back at them.
- **User-facing text of the `calculator/` package is English**, matching the
  rest of the tools now that a tool exposes it. Calculations and German code
  comments unchanged.

### Removed

- **`calculate_validation`** (with `ValidationPayload` and its panel view) and
  **`open_chemdraw_file`**. The Ph.Eur. math in `calculator/` and the AppleScript
  bridge in `chemdraw.py` remain, tests included, so re-wiring them is cheap.
  CDXML is untouched as an output format.

### Added

- **`tests/test_server_taxonomy.py`** — the tool set is a promise now: every
  tool belongs to exactly one area, a new one has to be entered here, and the
  count stays reviewable.
- **`tests/conftest.py`** — guards the real `~/ChemDraw-Output` against tests
  whose path redirect points nowhere. It is what makes a future split of
  `server.py` into per-area modules safe: 64 test patches target
  `chemdraw_tool.server.*`, and a silent miss would write into the user's
  own output folder.

## [0.3.0] — 2026-08-15

Two new figure types, publication-style rendering options, and a diagnosis
command. Everything that changes how drawings look is opt-in — existing calls
render byte-identically to 0.2.1.

### Added

- **`generate_tlc`** — TLC plates from Rf values. Lanes carry the name, spots
  carry the substances, so a co-spot is simply a lane with two spots. Mobile
  phase and detection method are captioned on the plate, because that is what a
  lab report asks for. Rf outside 0–1 is rejected with the lane name rather
  than silently clamped.
- **`generate_scope_table`** — substrate-scope figures like those in method
  papers: a grid of product structures with identifiers and yields, optionally
  headed by the general reaction. Unresolvable entries are reported and the
  figure is built from the rest.
- **`abbreviate_groups`** on the structure tools — condenses Ph, Bn, OAc, OMe,
  tBu and friends instead of drawing every ring out (RDKit `rdAbbreviations`).
- **`render_style`** with three profiles named after their behaviour, not after
  journals: `compact` (two-column typesetting), `presentation` (lecture slides),
  `grayscale` (black-and-white print).
- **`chemdraw-doctor`** — diagnoses an installation before it fails silently:
  RDKit rendering, Java/OPSIN, uv resolution, Desktop config, database
  reachability, output directory. Distinguishes *broken* from *absent*; exit
  code is non-zero only for real errors.
- **`chemdraw-install`** — registers the server in Claude Desktop without a
  repository clone, for users who installed from PyPI.

### Fixed

- **Resolver diagnoses network failures correctly.** Every cascade failure used
  to produce the same advice ("use a different name"), even when the network
  was down — sending users on a search that could not succeed. Errors now carry
  a kind (not found / offline / sources down / partial) and say what actually
  helps. A hanging network now fails in 6.5 s instead of 40.6 s
  (`(connect=3, read=10)` timeouts), and repeated lookups are cached.
- **`lookup_compound` dropped genuine zeros.** Benzene really has TPSA 0 and no
  hydrogen-bond donors; a truthiness check hid those rows and made measured
  zeros look unknown.
- **`lookup_compound` emitted broken Markdown** when PubChem's property call
  failed while synonyms succeeded: a table row without a table header.
- **The installer wrote a bare `"uv"`** into the Desktop config. Claude Desktop
  launches MCP servers with a minimal GUI PATH, where that does not resolve —
  the server then failed to start with no message at all. The absolute path is
  resolved and confirmed at install time.
- **The server reported the SDK version** (`1.27.1`) instead of its own in
  `serverInfo`, so users could not tell which version was running.

### Changed

- The gate now covers two failure modes it previously had: it launches the
  actual Chromium build instead of checking for a cache folder (false red), and
  it rebuilds the UI bundle and compares bytes (false green — the server serves
  `dist/`, not `src/`). Lint runs as part of it.
- A frozen golden test guards the Python renderer's default output; the pixel
  snapshot only ever covered the JavaScript rasterization.
- `package-lock.json` is versioned, and the build toolchain was patched to
  close 9 npm advisories (6 high). The shipped bundle is byte-identical.

## [0.2.1] — 2026-07-25

### Fixed

- Panel reads its payload from the content text block as well — current Claude
  Desktop strips `structuredContent`.

## [0.2.0] — 2026-06-11

- First public release: structures, reactions, mechanisms, spectra, database
  lookups, Ph.Eur. calculations, Anki export, embedded preview panel.
