# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

The tool set becomes five areas with drawn boundaries, and gains the maths a
lab report actually asks for. The trigger was a real misfire: "draw aspirin"
was answered with `generate_scope_table`, a substrate grid holding a single
cell. The model picks a tool from its name and description alone, so 22 tools
with fuzzy edges are a precision problem.

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
