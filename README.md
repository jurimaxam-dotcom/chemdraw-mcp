# chemdraw-mcp

<!-- mcp-name: io.github.jurimaxam-dotcom/chemdraw-mcp -->

[![CI](https://github.com/jurimaxam-dotcom/chemdraw-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/jurimaxam-dotcom/chemdraw-mcp/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/jurimaxam-dotcom/chemdraw-mcp)](https://github.com/jurimaxam-dotcom/chemdraw-mcp/releases)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/chemdraw-mcp)](https://pypi.org/project/chemdraw-mcp/)
[![GitHub stars](https://img.shields.io/github/stars/jurimaxam-dotcom/chemdraw-mcp?style=social)](https://github.com/jurimaxam-dotcom/chemdraw-mcp/stargazers)

chemdraw-mcp is an MCP server that lets Claude draw chemistry: structures,
reaction schemes, textbook mechanisms, spectra, TLC plates and pH curves,
rendered locally with RDKit and matplotlib as PNG and SVG files.
Each drawing also opens an interactive panel in the chat — hover a functional
group, switch to the PubChem data sheet, rotate a 3D model, export or add an
Anki card. It is free and open source (Apache-2.0) and needs no API key, no
sign-up and no ChemDraw licence.

<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/demo-molecule.gif" alt="The chemdraw-mcp panel: aspirin with its functional groups highlighted on hover, then the PubChem data sheet" width="640"></p>
<p align="center"><sub>"Draw aspirin" in Claude Desktop. Demo edited to shorten the PubChem loading wait.</sub></p>

| Without | With chemdraw-mcp |
|---|---|
| Claude describes a structure in words or writes SMILES you paste elsewhere | the structure appears in the chat, as files ready for a report |
| figures drawn by hand in ChemDraw or ChemSketch | one sentence per figure, one style across the whole report |
| molar mass, CAS number and hazards from three websites | one data sheet from PubChem, or one value as text |
| a pH worked out with an approximation you cannot check | the exact value with the textbook approximation beside it |

## Quick start

1. **[Download the Claude Desktop extension](https://github.com/jurimaxam-dotcom/chemdraw-mcp/releases/latest)**
   (`chemdraw-mcp-<version>.mcpb`), double-click it and confirm in Claude Desktop.
2. Open a **new chat** and say *"Use the ChemDraw MCP: draw caffeine"*.
3. Try a prompt from the [tool table](#tools) below.

Other ways in (PyPI, cloning the repository, editing the config by hand) are
under [Installation](#installation).

## Tools

The default profile registers 16 tools in five areas. Each description says
which neighbouring tool to use instead, so the model can tell a drawing from a
lookup from a calculation. Files go to `~/ChemDraw-Output/`.

| Area | Tool | Example prompt | Panel |
|---|---|---|---|
| **Draw** | `generate_molecule` | *"Draw caffeine"* | yes |
| | `batch_generate` | *"Draw aspirin, caffeine and paracetamol, each as its own file"* | yes |
| | `compare_molecules` | *"What is the difference between ibuprofen and naproxen?"* | yes |
| | `generate_reaction` | *"Draw the esterification of acetic acid with ethanol as a reaction equation"* | yes |
| | `generate_mechanism` | *"Show me the SN2 mechanism step by step"* | yes |
| | `generate_3d` | *"Show methane as a rotatable 3D model"* | yes |
| **Lab graphics** | `generate_spectrum` | *"Draw the IR spectrum of aspirin"* | yes |
| | `generate_tlc` | *"TLC of my esterification: educt at Rf 0.3, product at 0.65, co-spot shows both"* | yes |
| | `generate_titration_curve` | *"Which indicator fits the titration of phosphoric acid with NaOH? Show me the curve."* | yes |
| | `generate_species_distribution` | *"Draw the species distribution of phosphoric acid over the whole pH range"* | yes |
| **Look up** | `lookup` | *"What is the CAS number of paracetamol?"* | text |
| | `lookup_molecule_data` | *"Give me a data sheet for ibuprofen"* | yes |
| | `predict_spectrum` | *"Which IR bands should aspirin show?"* | text |
| **Calculate** | `calculate_ph` | *"What is the pH of 0.1 M acetic acid, pKa 4.76?"* | text |
| **Anki** | `export_anki_deck` | *"I have an exam on NSAIDs on Friday and need to know the structures"* | — |

The 16th tool, `save_png`, is the server half of the panel's export button. It
runs when you click that button and is never called by the model on its own.

### Draw

**Structures.** `generate_molecule` takes a name (English, IUPAC, many German
trivial names) or SMILES. Names resolve through OPSIN, PubChem and NCI; a
pinned identity test checks 24 inputs against their InChIKey, and family names
such as "xylene" return an isomer picker instead of a silent guess. The panel
shows properties, functional groups and the Lipinski rule of five, with
buttons for the data sheet, PNG export and an Anki card. Fischer and Haworth
projections and all-H drawings are a `view` option.

<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/caffeine.png" alt="Caffeine structure, rendered by generate_molecule" width="380"></p>

**Comparisons.** `compare_molecules` draws two to four structures side by
side, keeps the shared scaffold neutral and highlights what differs:

<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/demo-compare.gif" alt="Ibuprofen, naproxen and ketoprofen side by side with differences highlighted in the chat panel" width="640"></p>

**Reaction schemes.** `generate_reaction` draws reactants, products and
conditions above and below a forward (→), equilibrium (⇌) or retrosynthetic
(⇒) arrow; formula digits are subscripted (H2SO4 → H₂SO₄):

<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/demo-reaction.gif" alt="Fischer esterification with an equilibrium arrow and conditions above and below it in the chat panel" width="640"></p>

**Mechanisms — a textbook gallery, not a mechanism engine.** `generate_mechanism`
shows three fixed examples: SN1 (2-bromopropane + water), SN2 (bromomethane +
hydroxide) and Fischer esterification (acetic acid + methanol), with curved
electron-flow arrows and **Next / Back** through the intermediates. Substrates
you name are checked for compatibility with the mechanism; they are not drawn
into it. Other mechanisms are not available.

<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/wave1-mechanisms.png" alt="MCP panels for the SN1, SN2 and Fischer esterification textbook examples, each showing the second step with curved electron-flow arrows" width="960"></p>

**3D.** `generate_3d` embeds one conformer (ETKDGv3, then MMFF or UFF), opens a
ball-and-stick panel you drag to rotate and writes an SDF file:

<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/wave1-3d.png" alt="Caffeine conformer rendered by generate_3d in the interactive ball-and-stick panel" width="480"></p>

### Lab graphics

These tools draw the numbers they are given — peak positions, Rf values, pKa
values. For a named compound the model supplies typical literature values;
check them before they go into a report.

**Spectra.** `generate_spectrum` draws IR, NIR, Raman, UV/Vis, fluorescence,
ORD, CD, ¹H/¹³C NMR and mass spectra with the axis conventions of each type
(inverted wavenumber axis for IR, ppm from right to left for NMR, bars for MS):

<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/aspirin-ir.png" alt="Schematic aspirin IR spectrum with separate ester and acid carbonyl bands" width="560"></p>

**TLC plates.** `generate_tlc` draws start line, solvent front, one labelled
lane per application point, the Rf value at every spot, and the mobile phase
and detection as a caption:

<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/tlc-wave2.png" alt="TLC plate sketch with three lanes: starting material at Rf 0.30, product at 0.65, co-spot with both; mobile phase hexane/ethyl acetate 7:3" width="500"></p>

**pH curves.** `generate_titration_curve` computes pH against titrant volume
from the exact charge balance and marks equivalence points, the buffer points
at half-equivalence and an optional indicator band.
`generate_species_distribution` plots the fraction of each protonation
species across pH 0–14:

<p align="center">
  <img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/wave2-titration-acetic.png" alt="Titration curve of acetic acid: equivalence point at 25 mL, buffer point at pH 4.76, phenolphthalein band" width="420">
  <img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/wave2-species-phosphoric.png" alt="Species distribution of phosphoric acid over pH with pKa crossovers" width="420">
</p>

### Look up

- **`lookup`** answers one question as text, picked by `topic`: `properties`
  (formula, mass, CAS, InChIKey), `safety` (GHS statements, pictograms, signal
  word), `physical` (melting and boiling point, solubility, density), `biochem`
  (ChEBI classification, UniProt entries) or `pathway` (KEGG pathways).
- **`lookup_molecule_data`** builds the PubChem + GHS data sheet in the panel.
  The molecule panel's **Data** button calls it too, so a drawn structure is
  one click away from its data sheet (second half of the demo at the top).
- **`predict_spectrum`** lists the IR bands a structure should show (intensity,
  band shape), what a measured wavenumber could belong to, and how many ¹H
  signals to expect with their integral ratio. It is rule-based: no chemical
  shifts in ppm, and diastereotopic protons count as one signal.

Lookups need an internet connection. A missing value is not evidence that a
property or hazard is absent.

### Calculate

**`calculate_ph`** covers weak and strong acids and bases, buffers (ratio and
capacity), buffer recipes down to weighable masses, and the ionised fraction of
a drug at a given pH. It solves the same exact charge balance that draws the
titration curve and prints the textbook approximation beside it; where the two
disagree, the answer says the approximation's assumptions no longer hold.
10⁻⁸ M HCl comes out at pH 6.98, not 8. You supply the pKa values.

### Anki

**`export_anki_deck`** writes a ready-to-import `.apkg` with rendered
structures: structure ↔ name drills (optionally both directions), cloze cards,
identity reactions and spectrum band assignments, with tags and
`Parent::Child` subdecks. Re-exporting a deck updates its cards instead of
duplicating them. With the AnkiConnect add-on the cards go straight into the
running Anki. `curated_deck_id` picks a small bundled starter deck instead of
your own cards. The molecule panel's **Add to Anki** button adds a single
structure card.

### Options on the drawing tools

- **`formats`** — `["png","svg"]` by default; add `"cdxml"` for ChemDraw on
  `generate_molecule`, `generate_reaction` and `batch_generate`. Figures that
  are not structures (spectra, TLC plates) reject CDXML with an error.
- **`abbreviate_groups=True`** — draws common substituents as Ph, Bn, OMe, OAc,
  tBu, CO₂H, Boc, Ts, TBS.
- **`render_style`** — `"compact"` for small figures in a two-column layout,
  `"presentation"` for slides, `"grayscale"` for black-and-white printing.
  Empty means the default look.
- **`annotate_stereo=True`** — prints CIP descriptors (R/S, E/Z) on the drawing
  (`generate_molecule`, `batch_generate`).

## Profiles

| Profile | Tools | Contents |
|---|---|---|
| `mvp` (default) | 16, 12 with a panel | the five areas above |
| `full` | 23, 16 with a panel | adds a substrate-scope figure, a calibration curve, pharmacology curves and three more calculators |

The `full` profile adds:

- **`generate_scope_table`** — the substrate-scope figure of the methodology
  literature: general equation with conditions on top, products below with
  identifier, yield and optional ee/dr.
- **`generate_calibration_curve`** — least-squares line through your
  standards, unknowns read back off it, LOD/LOQ (DIN 32645); a sample outside
  the calibrated range is labelled as extrapolated.
- **`generate_pk_curve`** and **`generate_dose_response`** — plasma
  concentration over time (one-compartment model, single or repeated doses,
  therapeutic window) and the Hill curve with a competitive antagonist.
- **`calculate_solution`**, **`calculate_content`**,
  **`calculate_pharmacokinetics`** — what to weigh and how to dilute; content
  determinations with Grubbs test, t-test, fat characteristics and Karl
  Fischer; half-life, AUC, steady state and loading dose, each with the working.

<details>
<summary>Example figures from the full profile</summary>

<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/scope-suzuki.png" alt="Substrate scope figure: Suzuki coupling equation with conditions on top, below it four biphenyl products labeled 3a to 3d with yields and ee/dr notes" width="760"></p>
<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/pk-curve.png" alt="Plasma concentration over time for repeated oral doses, building up to steady state inside a therapeutic window" width="640"></p>
<p align="center"><img src="https://raw.githubusercontent.com/jurimaxam-dotcom/chemdraw-mcp/main/assets/dose-response.png" alt="Hill curve of an agonist and the same curve shifted to the right by a competitive antagonist" width="640"></p>

</details>

To switch, set `CHEMDRAW_PROFILE` and restart the server:

```bash
uv run chemdraw-tool-server                         # mvp, the default
CHEMDRAW_PROFILE=full uv run chemdraw-tool-server   # all 23 tools
```

For Claude Desktop, add `"env": {"CHEMDRAW_PROFILE": "full"}` to the server
entry in `claude_desktop_config.json` and restart Claude Desktop. An invalid
profile name stops startup with an error. Two optional vault tools
(`search_vault`, `read_vault_entry`) appear only in the full profile and only
when `CHEMDRAW_VAULT_PATH` is set.

## Installation

Pick **one** route — installing twice registers the server twice and the model
sees every tool doubled. Afterwards restart Claude Desktop and ask
*"draw caffeine"*.

### 1. Claude Desktop extension (macOS, Linux)

Download `chemdraw-mcp-<version>.mcpb` from the
[latest release](https://github.com/jurimaxam-dotcom/chemdraw-mcp/releases/latest),
double-click it and confirm in Claude Desktop, then restart Claude Desktop once.
The first start fetches the package from PyPI via [uv](https://docs.astral.sh/uv/),
every file checked against hashes pinned at release time (a missing uv is
downloaded at a fixed version and its SHA-256 verified). That is about 40 MB
and takes a minute; later starts are offline.

If your organization manages Claude Desktop, it may block extensions or allow
only listed ones — then use route 2.

### 2. From PyPI

Needs [uv](https://docs.astral.sh/uv/):

```bash
uv tool install chemdraw-mcp
chemdraw-install
```

`chemdraw-install` adds the Claude Desktop entry with the absolute path of the
installed launcher, backs up the config first, leaves other MCP servers
untouched and prints what it registered.

<details>
<summary>3. From a clone (to read or change the code)</summary>

```bash
git clone https://github.com/jurimaxam-dotcom/chemdraw-mcp.git
cd chemdraw-mcp && ./install.sh
```

`install.sh` installs uv if missing, syncs the dependencies and registers the
server the same way `chemdraw-install` does.

</details>

<details>
<summary>4. Editing the config by hand</summary>

Add this to `claude_desktop_config.json` under `mcpServers` (macOS:
`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
"chemdraw-tool": {
  "command": "/opt/homebrew/bin/uvx",
  "args": ["chemdraw-mcp"]
}
```

Claude Desktop starts MCP servers with a minimal PATH, not your login shell.
A bare `"uvx"` cannot be found there and the server fails without a message.
Put the absolute path that `which uvx` prints on your machine into `command`.

</details>

### Optional extras

- **A Java runtime** (e.g. `brew install openjdk`) lets
  [OPSIN](https://github.com/dan2097/opsin) parse systematic IUPAC names
  offline, including names no database indexes. Without Java, names are
  resolved online through PubChem and NCI.
- **The AnkiConnect add-on** lets `export_anki_deck` add cards to a running
  Anki. Without it you import the `.apkg` file yourself.
- **ChemDraw** is never required. Request `formats=["cdxml"]` to continue
  editing a structure there.

### Something not working? Run the doctor

```bash
chemdraw-doctor                            # after "uv tool install chemdraw-mcp"
uv run chemdraw-doctor                     # in a clone
uvx --from chemdraw-mcp chemdraw-doctor    # without installing anything
```

It checks the six things that make the server look dead in the chat — RDKit
rendering, the Java/OPSIN runtime, the `uv` path, the Claude Desktop entry, the
name databases and the output directory — and prints the command that fixes
each problem. Results are `[OK]`, `[LIMITED]` (works, but restricted), `[FAIL]`
or `[NOTE]` (does not apply). The exit code stays 0 while the server is usable.
From a PyPI install the `uv` and Claude Desktop checks report `[NOTE]`, because
they belong to the repository installer.

If the server code or a dependency changed, restart Claude Desktop: it keeps
the server process running, and an old process mixed with new files fails in
confusing ways.

## Limitations

- **Without Java, names need the internet.** OPSIN is skipped and names are
  resolved online through PubChem and NCI, so only names those databases index
  are found. SMILES input never touches the network.
- **Lab graphics are drawings of given numbers.** Spectra, TLC plates and pH
  curves show the values passed in. They measure nothing; values the model
  supplied from memory need checking. TLC spot `intensity` is a drawing hint,
  not densitometry.
- **Mechanisms are three fixed examples** (SN1, SN2, Fischer esterification).
- **3D is one conformer**, a plausible geometry to look at — not a
  conformational search and not an energy statement.
- **CDXML is a side path.** It is round-trip validated, but PNG and SVG are
  the primary outputs and the ones the pixel tests cover.
- **The extension targets macOS and Linux.** Windows is untested.

## How it works

```
name / SMILES
   │
   ▼
resolver ──► OPSIN (systematic IUPAC names, offline) ──► PubChem / NCI (names)  ·  direct parse (SMILES)
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

## Development

Python 3.11+, package manager `uv`.

```bash
uv sync                      # backend dependencies
cd chemdraw_tool/ui && npm install && npx playwright install chromium  # frontend, once
./test.sh                    # the gate: lint, pytest, bundle freshness, JS unit and browser tests
```

About 7,500 Python tests plus JavaScript unit and headless-Chromium tests,
written test-first. Frozen renderings guard the drawing output, a pinned
identity list guards name resolution, and snapshots of every tool description
guard which tool the model picks.

## Feedback, bugs and wishes

- **Something broke?** [Open a bug report](https://github.com/jurimaxam-dotcom/chemdraw-mcp/issues/new?template=bug_report.yml) —
  the form asks for the output of `chemdraw-doctor`.
- **Missing something in your course?** [Tell us what you would draw or calculate](https://github.com/jurimaxam-dotcom/chemdraw-mcp/issues/new?template=feature_request.yml) —
  the subject and the exam question help more than a feature name.
- **Wrong chemistry?** Use the bug form and name the compound and the figure.
- **A question, or something you made with it?** [Discussions](https://github.com/jurimaxam-dotcom/chemdraw-mcp/discussions).
- **It worked for you?** A ⭐ on the repository helps other students find it.

## License

Apache-2.0 — see [LICENSE](LICENSE). Copyright 2026 jurimaxam-dotcom.

> **Disclaimer:** This is an unofficial, independent project, not affiliated
> with or endorsed by Revvity. *ChemDraw* is a trademark of Revvity Signals
> Software, Inc. This tool does not include or require ChemDraw; it can
> optionally export files in the open CDXML format.
