# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

The tool set becomes four areas with drawn boundaries. The trigger was a real
misfire: "draw aspirin" was answered with `generate_scope_table`, a substrate
grid holding a single cell. The model picks a tool from its name and
description alone, so 22 tools with fuzzy edges are a precision problem.

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
  whose path redirect points nowhere.

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
