# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project uses [Semantic Versioning](https://semver.org/).

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
