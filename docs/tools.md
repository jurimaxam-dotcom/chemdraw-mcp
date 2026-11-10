# Tools in detail

What each tool of chemdraw-mcp does, the options on the drawing tools, the
`full` profile and the known limits. The short overview with example prompts is
the [tool table in the README](../README.md#tools).

Files go to `~/ChemDraw-Output/`.

- [Draw](#draw) · [Lab graphics](#lab-graphics) · [Look up](#look-up) ·
  [Calculate](#calculate) · [Anki](#anki)
- [Options on the drawing tools](#options-on-the-drawing-tools)
- [Profiles](#profiles)
- [Limitations](#limitations)

## Draw

**Structures.** `generate_molecule` takes a name (English, IUPAC, many German
trivial names) or SMILES. Names resolve through OPSIN, PubChem and NCI, with
English, counter-ion, form and rotation-sign spellings as fallbacks, and a
direct hit is cross-checked against the other source (free form over salt
unless the name says salt, the more defined stereo form wins); a pinned
identity test checks 67 inputs against their InChIKey, and family names such
as "xylene" return an isomer picker instead of a silent guess. The panel
shows properties, functional groups and the Lipinski rule of five, with
buttons for the data sheet, PNG export, an Anki card and a rotatable 3D
model; when the name was found under another spelling, a "Found as" line
says which. Fischer and Haworth projections, the chair conformation of a
cyclohexane or pyranose ring and all-H drawings are a `view` option and
panel buttons.

**Peptides.** A three-letter sequence is built offline, even when no database
knows it: `Ala-Trp-Lys-Ser-Gly`, `ala-gly`, `D-Ala-Gly`, `Ac-Ala-Gly-NH2`,
`cyclo(Arg-Gly-Asp-D-Phe-Val)`. Free termini (H-…-OH) are the default. The
one-letter code needs the prefix `peptide:` (`peptide:AGS`, lowercase = D
residue, `peptide:Ac-AG-NH2`, `peptide:cyclo(RGDfV)`), because without it
"AGS" is a name (ATPγS) and "CCC" is propane. Linear peptides of five or more
residues are laid out as a stretched backbone. Names with a protecting group
or ester (`Boc-Ala-OH`, `Asp-Phe-OMe`) and trivial names (`Met-enkephalin`) go
to the databases as before. "X zwitterion" resolves X and charges its
α-amino and α-carboxyl group, keeping the stereo of X.

**Proteins.** Enzymes, antibodies and large peptide hormones have no readable
skeletal formula. `generate_molecule` (2D image + panel) and `generate_3d`
(rotatable panel) draw them as a **cartoon** (ribbon diagram, since E13):
α-helices as ribbons, β-strands as flat arrows pointing to the C-terminus,
loops as a thin tube, from the backbone atoms (N, Cα, C, O) of an
experimental structure (PDB) or, without one, of the AlphaFold model. The
view is the principal-axis view (longest extent horizontal, N-terminus
left, tilted when that shows less overlap; a rotation, never a mirror
image), coloured by secondary structure or — for several chains — by chain.
Bound groups near the protein (heme, metal ions, bound inhibitors)
are drawn as sticks and spheres and named in the
legend; water, buffer components, simple salts and glycans are left out.
Secondary structure comes from the entry's HELIX/SHEET records; an entry
without them (some NMR and cryo-EM files) gets its own DSSP-style
assignment (Kabsch & Sander), and the message says so. Old entries whose
annotation omits helices (1LYZ helix D, 2PTN's C-terminal helix) get those
helices filled in from the same assignment — only where the annotation says
loop over the whole computed helix of six or more residues. PNG and SVG land in
`~/ChemDraw-Output/proteine/`; title, subtitle and image always name
protein, organism and source.

**The protein panel.** The cartoon is rendered with
[Mol*](https://molstar.org) 5.13.1 (MIT; Sehnal et al. 2021), the viewer
RCSB and PDBe use, with ambient occlusion and outlines. Drag to rotate,
pinch or ⌘/Ctrl+scroll to zoom (plain scrolling keeps scrolling the chat),
right-drag to move; colour by secondary structure, chain (several chains),
rainbow N→C (always offered) or — for AlphaFold models — pLDDT confidence;
Cartoon/Trace toggle; Reset. Antibodies get a Structure | Scheme toggle: the
IgG domain scheme is drawn in the panel itself (light and dark theme); a
general antibody name opens on the scheme, an antibody with its own Fab
structure opens on the structure and marks in the scheme which Fab arm it
is. The panel follows the host's light/dark theme; the files stay light. Export
PNG saves the cartoon as shown, at three times the panel resolution. The
engine is about 2.4 MB of the panel file but only runs when a protein is
shown. If the host has no WebGL (or blocks the script), the panel keeps the
SVG backbone trace and says so — never an empty area.

- **Which entry.** One place (`resolver.protein_choice`) decides for message,
  picture and `lookup` data sheet. First a curated lab-standard table (each
  row checked against UniProt and RCSB on 10.11.2026): hen egg-white
  lysozyme (1LYZ), bovine trypsin (2PTN) and chymotrypsin (4CHA), RNase A
  (7RSA), BSA (4F5S), bovine liver catalase (8CAT), HRP (1ATJ), GFP (1GFL),
  proteinase K (2PRK), streptavidin (1STP), Taq polymerase (1TAU), human
  insulin (3I40; porcine 4INS named as the alternative), haemoglobin A
  tetramer (2HHB), horse/sperm-whale myoglobin, carbonic anhydrase II (3KS3),
  yeast/horse-liver ADH, firefly luciferase, pepsin, papain, thrombin and
  testis ACE (1UZE). An organism in the name selects the
  row ("Lysozym Huhn", "Rindertrypsin", "human lysozyme"); the message names
  the other common sources. Then gene symbols in bacterial style (`RecA`,
  `LipA`, `GroEL`: lower–lower–Upper) go to UniProt's gene field, reviewed
  entries first, with the other organisms named; everything after the
  symbol (or after "from"/"aus") filters by organism, also genus or short
  form (`RecA Bacillus`, `RecA from B. subtilis`), then unreviewed
  (TrEMBL) entries count too and are labelled so. If no entry carries the
  gene name for that organism, the entry is found by the protein name the
  other entries carry, and the message says so. All-caps abbreviations stay
  compounds (`PABA`, `ATP`, `NADH`, `DMSO`, `EDTA`). Measured cost: 0.2–0.5 s
  per gene lookup, about 0.9 s with the organism fallback.
- **Antibodies.** A table of wild-type Fab structures checked by RCSB
  title (trastuzumab 1N8Z, rituximab 4KAQ, adalimumab 4NYL, cetuximab 1YY9,
  nivolumab 5WT9, infliximab 4G3Y, omalizumab 2XA8, ofatumumab 3GIZ;
  pembrolizumab 5DK3 as intact IgG4), labelled "Fab fragment, not the full
  IgG", antigen chains left out. Any other antibody name ("anti-GFP",
  "IgG", "Antikörper", an unknown -mab) gets the architecture of an intact
  IgG (1HZH, "not <name>"). Both write the IgG domain scheme as a second
  file (heavy chain blue, light chain orange, inter-chain disulfides, N297
  glycan).
- **Limits.** No side chains; bound groups only as described above (up to
  16, none from other copies of the crystal); one model, one copy of a
  multi-copy crystal; up to 3000 residues. 3₁₀- and π-helices are drawn as
  loops. A
  predicted model says "AlphaFold model, predicted" and shows mean pLDDT;
  residues below 70 are pale in the image file, and the panel's Confidence
  colouring shows the four pLDDT classes. Without network the protein message stays,
  with the reason, and nothing is drawn.
- **Privacy.** A protein name goes to UniProt, PDBe (best structure), the
  RCSB ModelServer or the AlphaFold DB. Sources and licences: PDB (wwPDB,
  CC0, cited with the PDB ID), AlphaFold DB (CC BY 4.0; Jumper et al. 2021,
  Varadi et al. 2024), UniProt (CC BY 4.0) — each image carries its line.
- `batch_generate` and `compare_molecules` still draw no proteins; their
  message points at `generate_molecule`.

Before E8 `generate_molecule` explained instead of drawing; these rules from
E6 still decide for names outside the table:

- A name that UniProt (Swiss-Prot) lists as a protein — "lysozyme",
  "Trypsin", "hemoglobin", German "Lysozym", "Katalase", "Kollagen" — is
  answered with the entry: name, accession, organism, length and mass (marked
  as precursor when a signal peptide or propeptide is cleaved off), and a
  pointer to `lookup` with topic `biochem` (data sheet: function, EC number,
  catalysed reaction with Rhea ID, cofactors, and which structure is drawn). Enzyme names (ending in -ase or
  -zyme) are checked before the structure databases, because PubChem files a
  peptide fragment under "lysozyme" and an acyl-CoA under "alcohol
  dehydrogenase". Other names ask UniProt only after every structure source
  answered "unknown" — never when they were unreachable.
- Antibody names (INN stem -mab, "trastuzumab") get a plain sentence: a
  monoclonal antibody, a protein of about 150 kDa as a full IgG. UniProt does
  not list therapeutic antibodies under their INN, so no numbers are given.
- A name that resolves to a structure with more than 200 heavy atoms
  (insulin 404, glucagon 246, calcitonin 239) is not drawn; the message gives
  formula, mass, heavy atoms and the number of residues. Palytoxin (186),
  oxytocin and 20-residue peptides are still drawn. A SMILES or a peptide
  sequence you pass yourself is always drawn.

**Metal tetrapyrroles.** Heme, hemin, zinc protoporphyrin,
copper phthalocyanine and related complexes are drawn as in a
textbook: undistorted macrocycle, metal in the centre, bonded to the four ring
nitrogens. A nitrogen anion paired with a positive metal charge is drawn as a
plain bond (both charges cancel), any remaining nitrogen as a dative arrow
N→M; heme thus shows two lines, two arrows and no charges. The bonds exist
only in the drawing — formula, InChIKey, CAS and the SMILES used for the data
sheet are those of the database record (which lists the metal as a separate
ion). The CDXML file keeps the record's bonds, with the metal placed in the
centre. Metal-free porphyrins get the same undistorted ring. When the layout
would cross or stretch bonds (chlorophyll a, bacteriochlorophyll a, the
cobalamins), the drawing stays as before.

A small built-in table keeps the structures of a few metal tetrapyrroles
(heme b, hemin, heme d1 and related iron complexes) stable: they resolve
offline to fixed structures in one notation (carboxylic acids, Fe²⁺ with two
N⁻), so they look alike side by side and do not depend on which PubChem record
a name points to that day. Accepted names include "heme", "Häm", "protoheme",
"hemin", "Hämin".

<p align="center"><img src="../assets/caffeine.png" alt="Caffeine structure, rendered by generate_molecule" width="380"></p>

**Comparisons.** `compare_molecules` draws two to four structures side by
side, keeps the shared scaffold neutral and highlights what differs:

<p align="center"><img src="../assets/demo-compare.gif" alt="Ibuprofen, naproxen and ketoprofen side by side with differences highlighted in the chat panel" width="800"></p>

**Reaction schemes.** `generate_reaction` draws reactants, products and
conditions above and below a forward (→), equilibrium (⇌) or retrosynthetic
(⇒) arrow; formula digits are subscripted (H2SO4 → H₂SO₄):

<p align="center"><img src="../assets/demo-reaction.gif" alt="Fischer esterification with an equilibrium arrow and conditions above and below it in the chat panel" width="800"></p>

**Mechanisms — three families, drawn with your molecules.** `generate_mechanism`
draws SN2, SN1 and Fischer esterification with the substrates you name, with
curved electron-flow arrows and **Next / Back** through the intermediates. SN2
takes a methyl, primary or secondary alkyl halide with one anionic nucleophile
(OH⁻, CN⁻, I⁻, Br⁻, RO⁻, N₃⁻, RS⁻/HS⁻) and inverts a stereocentre; SN1 takes a
tertiary or benzylic halide with water, an alcohol or one of those anions (an
allylic halide is refused: its cation gives two products); Fischer takes one
carboxylic acid and one primary or secondary alcohol; its steps are joined
by ⇌ and a second solvent molecule carries the proton instead of a free H⁺.
When elimination competes (a secondary halide with a strong or bulky base,
an SN1 cation with a β-hydrogen) a note under the title says so; only the
substitution is drawn. Anything outside these limits gets an error with the
reason. Other mechanisms are not available.

<p align="center"><img src="../assets/wave1-mechanisms.png" alt="Second step of SN1, SN2 and Fischer esterification, each with curved electron-flow arrows, drawn from the step SVGs that generate_mechanism returns" width="960"></p>

**3D.** `generate_3d` embeds one conformer (ETKDGv3, then MMFF or UFF), opens a
ball-and-stick panel you drag to rotate and writes an SDF file; the same model
is behind the `3D` button of every molecule panel:

<p align="center"><img src="../assets/wave1-3d.png" alt="Ball-and-stick projection of the caffeine conformer that generate_3d embeds; the panel shows the same atoms and lets you rotate them" width="420"></p>

## Lab graphics

These tools draw the numbers they are given — peak positions, Rf values, pKa
values. For a named compound the model supplies typical literature values;
check them before they go into a report.

**Spectra.** `generate_spectrum` draws IR, NIR, Raman, UV/Vis, fluorescence,
ORD, CD, ¹H/¹³C NMR and mass spectra with the axis conventions of each type
(inverted wavenumber axis for IR, ppm from right to left for NMR, bars for MS):

<p align="center"><img src="../assets/aspirin-ir.png" alt="Schematic aspirin IR spectrum with separate ester and acid carbonyl bands" width="560"></p>

**TLC plates.** `generate_tlc` draws start line, solvent front, one labelled
lane per application point, the Rf value at every spot, and the mobile phase
and detection as a caption:

<p align="center"><img src="../assets/tlc-wave2.png" alt="TLC plate sketch with three lanes: starting material at Rf 0.30, product at 0.65, co-spot with both; mobile phase hexane/ethyl acetate 7:3" width="500"></p>

**pH curves.** `generate_titration_curve` computes pH against titrant volume
from the exact charge balance and marks equivalence points, the buffer points
at half-equivalence and an optional indicator band.
`generate_species_distribution` plots the fraction of each protonation
species across pH 0–14:

<p align="center">
  <img src="../assets/wave2-titration-acetic.png" alt="Titration curve of 0.1 M acetic acid with 0.1 M NaOH: equivalence point at 25 mL, buffer point on the curve at pH 4.76, phenolphthalein band" width="420">
  <img src="../assets/wave2-species-phosphoric.png" alt="Species distribution of phosphoric acid over pH with pKa crossovers" width="420">
</p>

## Look up

- **`lookup`** answers one question as text, picked by `topic`: `properties`
  (formula, mass, CAS, InChIKey), `safety` (GHS statements, pictograms, signal
  word), `physical` (melting and boiling point, solubility, density), `biochem`
  (ChEBI classification, UniProt entries; for a protein name a UniProt data
  sheet with function, EC number, length, mass and PDB IDs) or `pathway`
  (KEGG pathways).
- **`lookup_molecule_data`** builds the PubChem + GHS data sheet in the panel.
  The molecule panel's **Data** button calls it too, so a drawn structure is
  one click away from its data sheet.
- **`predict_spectrum`** lists the IR bands a structure should show (intensity,
  band shape), what a measured wavenumber could belong to, and how many ¹H
  signals to expect with their integral ratio. It is rule-based: no chemical
  shifts in ppm, and diastereotopic protons count as one signal.

<p align="center"><img src="../assets/lookup-datasheet.png" alt="Caffeine data sheet from lookup_molecule_data: structure on the left, PubChem properties (CID, IUPAC name, formula, molar mass, XLogP, TPSA, InChIKey) and the GHS signal word Warning with H302 on the right" width="760"></p>

Lookups need an internet connection. A missing value is not evidence that a
property or hazard is absent. The CAS number comes from PubChem's CAS section
(check digit verified, CAS Common Chemistry preferred, otherwise the majority
of sources); when the sources disagree evenly, the field stays empty.

## Calculate

**`calculate_ph`** covers weak and strong acids and bases, buffers (ratio and
capacity), buffer recipes down to weighable masses, and the ionised fraction of
a drug at a given pH. It solves the same exact charge balance that draws the
titration curve and prints the textbook approximation beside it; where the two
disagree, the answer says the approximation's assumptions no longer hold.
10⁻⁸ M HCl comes out at pH 6.98, not 8, and 2 M HCl at −0.30 with a note that
0–14 is no physical limit and that concentrated solutions follow activities,
not concentrations. You supply the pKa values.

<p align="center"><img src="../assets/calculate-ph.png" alt="Two calculate_ph answers: 0.1 M acetic acid at pH 2.88 with the exact value beside the textbook approximation, and 1e-8 M HCl at pH 6.98 with the note that −log c would wrongly give pH 8" width="760"></p>

## Anki

**`export_anki_deck`** writes a ready-to-import `.apkg` with rendered
structures: structure ↔ name drills (optionally both directions), cloze cards,
identity reactions and spectrum band assignments, with tags and
`Parent::Child` subdecks. Re-exporting a deck updates its cards instead of
duplicating them. With the AnkiConnect add-on the cards go straight into the
running Anki. `curated_deck_id` picks a small bundled starter deck instead of
your own cards. The molecule panel's **Add to Anki** button adds a single
structure card.

<p align="center"><img src="../assets/anki-card.png" alt="An Anki card from export_anki_deck: the front asks to name the aspirin structure, the back repeats the structure and answers Aspirin (acetylsalicylic acid)" width="760"></p>

## Options on the drawing tools

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
  standards, unknowns read back off it, LOD/LOQ (ICH Q2 estimate from residual
  standard deviation and slope); a sample outside the calibrated range is
  labelled as extrapolated.
- **`generate_pk_curve`** and **`generate_dose_response`** — plasma
  concentration over time (one-compartment model, single or repeated doses,
  therapeutic window) and the Hill curve with a competitive antagonist.
- **`calculate_solution`**, **`calculate_content`**,
  **`calculate_pharmacokinetics`** — what to weigh and how to dilute; content
  determinations with Grubbs test, t-test, fat characteristics and Karl
  Fischer; half-life, AUC, steady state and loading dose, each with the working.

<p align="center"><img src="../assets/scope-suzuki.png" alt="Substrate scope figure: Suzuki coupling equation with conditions on top, below it four biphenyl products labeled 3a to 3d with yields and ee/dr notes" width="760"></p>
<p align="center"><img src="../assets/pk-curve.png" alt="Plasma concentration over time for repeated oral doses, building up to steady state around Css,av 4.76 mg/L between the MEC and MTC lines of the therapeutic window" width="640"></p>
<p align="center"><img src="../assets/dose-response.png" alt="Hill curve of an agonist and the same curve shifted to the right by a competitive antagonist" width="640"></p>

To switch, set `CHEMDRAW_PROFILE` and restart the server:

```bash
uv run chemdraw-tool-server                         # mvp, the default
CHEMDRAW_PROFILE=full uv run chemdraw-tool-server   # all 23 tools
```

In Claude Desktop the two profiles are two connectors from one installation:
`chemdraw` (`mvp`) and `chemdraw-pharma` (`full`), registered by both the
extension bundles and `chemdraw-install`. Enable one per chat in the connector
menu — switching needs no restart; with both on, the model sees the default
tools twice. By hand, the entry's `"env": {"CHEMDRAW_PROFILE": "full"}` picks
the profile. An invalid profile name stops startup with an error. Two optional vault tools
(`search_vault`, `read_vault_entry`) appear only in the full profile and only
when `CHEMDRAW_VAULT_PATH` is set.

The server keeps a small log at `~/ChemDraw-Output/server.log` (rotated at 1 MB,
two older files kept). It records start-up, requests and errors, and a name
when its lookup needed a second attempt or failed. Set
`CHEMDRAW_LOG_LEVEL=DEBUG` for the full trace, which includes every lookup URL
and therefore every name you asked for.

## What leaves your machine

Drawing is local: RDKit parses, lays out and renders every structure on your
computer. Online databases are asked for names and data. In detail:

- **A structure you type is not sent to any database (default).** This covers
  a SMILES or InChI passed to any tool, and the structure behind the panel's
  Data button. What counts as a structure is the same rule everywhere: whatever
  RDKit reads as SMILES is one (`O` is water, not oxygen); InChI, CXSMILES, a
  SMILES with a label after or before it (`CCO batch 7`, `batch 7 CCO`) or
  preceded by a stereo prefix count too, and in `lookup` also a peptide sequence that can be built offline.
  The group abbreviations Me, Et, Ph, Bn, Ac, Ts, Boc, tBu, OMe and OEt are
  expanded locally where their place is unambiguous (at the start, at the end
  of the chain or a branch, or alone in parentheses), so
  `PhC(=O)CC1CCN(Boc)CC1` is drawn. An input that looks like a SMILES — a
  bracket, `=` or `#` together with an abbreviation, or `=`/`#` with an
  unreadable character — but cannot be read is refused with what was not read,
  and nothing is sent. A reaction SMILES (`A>>B`) is refused too. In `lookup`
  only, a bare run of up to five letters (`PC`, `NOS`, `CBS`, a gene symbol
  such as `RecA`) is a name, not a structure, and is sent as typed: such
  acronyms often happen to be valid SMILES, and a letters-only SMILES that
  short is at most pentane-sized. **Anything else RDKit cannot read is treated
  as a compound name and sent like one** — including `MeOH`, `Et3N` or `Boc2O`.
- **The InChIKey of a structure goes to PubChem.** `generate_molecule`,
  `batch_generate`, `lookup_molecule_data`, `lookup` and the substrate titles
  of `generate_mechanism` compute the InChIKey locally and ask PubChem for the
  record with it (name, CAS number, properties, GHS). The InChIKey is a hash:
  the structure cannot be computed back from it, but anyone who already has
  the structure can compute the same key and match it. When PubChem has no
  record for the key, CAS number, logP, TPSA and H-bond counts stay empty,
  formula and molar mass are computed locally, and the result says why
  (`lookupNote`). With a typed structure, `lookup` asks by InChIKey too, then
  uses the record's CID for `safety` and `physical` and PubChem's name for that
  record for `biochem` (ChEBI, UniProt) and `pathway` (KEGG). Without a record
  it answers with what it computed locally.
- **Compound names are sent, to resolve them.** A name goes to PubChem and
  NCI CIR (in several spellings), enzyme-like names and names no structure
  database knows also to UniProt. With Java, OPSIN reads systematic names with
  locants offline; a name without locants is cross-checked against PubChem.
  `lookup` passes a name to PubChem, ChEBI, UniProt or KEGG as typed,
  depending on `topic`. A systematic IUPAC name describes a structure as
  exactly as a SMILES does: for an unpublished compound, pass the SMILES, not
  the name.
- **Protein names go to UniProt, accession numbers and PDB IDs onward.**
  A protein, enzyme or antibody name and a gene symbol (`RecA`, with the
  organism typed after it) go to UniProt; the UniProt accession number goes
  to PDBe (best structure) and the AlphaFold DB; the PDB ID to the RCSB
  ModelServer, which returns the structure file (backbone atoms and bound groups are taken from it). Names from the curated table
  (lysozyme, trypsin, trastuzumab …) skip the search and only fetch the
  structure by its PDB ID. No structure you typed is part of these requests:
  a SMILES with a word before it (`RecA <SMILES>`) counts as a structure.

**Turning on the SMILES lookup.** In Claude Desktop, open Settings →
Extensions, then the settings of the ChemDraw MCP extension, and turn on
**Look up typed structures by SMILES** (both bundles have it). Elsewhere set
`CHEMDRAW_SMILES_LOOKUP=1` in the server's environment (`true`, `yes` and `on`
work too; anything else means off) and restart the server. With it on, two
things change: when PubChem has no record for the InChIKey, the SMILES itself
is posted to PubChem, which standardizes it itself and may find a record the
InChIKey query missed; and `lookup`
passes a typed SMILES as written to PubChem, ChEBI, UniProt or KEGG.
`chemdraw-doctor` reports the setting of its own environment; the server
writes its setting to `server.log` at startup ("SMILES lookup: off" or "on").

## Limitations

- **Without Java, names need the internet.** OPSIN is skipped and names are
  resolved online through PubChem and NCI, so only names those databases index
  are found. With Java, systematic names with locants are parsed offline;
  a name without locants is cross-checked against PubChem when the network
  is there.
- **A typed structure PubChem does not know has no database fields.** By
  default its SMILES is never sent, so a structure whose InChIKey PubChem has
  no record for is drawn without name, CAS number, logP and TPSA; formula and
  molar mass are computed locally. See
  [What leaves your machine](#what-leaves-your-machine).
- **Lab graphics are drawings of given numbers.** Spectra, TLC plates and pH
  curves show the values passed in. They measure nothing; values the model
  supplied from memory need checking. TLC spot `intensity` is a drawing hint,
  not densitometry.
- **Mechanisms are three families** (SN1, SN2, Fischer esterification), each
  within a stated substrate limit; allylic halides are refused, because the
  allyl cation gives two products and drawing one would be wrong.
- **Peptides: the 20 standard residues plus Orn, Nle, Nva, Sar and Abu,
  at most 20 residues.** Above 20 the atom labels shrink below 10 px. Not
  available: disulfide bridges, side-chain (γ/ε) isopeptide links (glutathione
  only by name), phosphorylation, and residues such as Hyp, Aib, pGlu or Cit;
  a sequence containing one is looked up by name and, if no database knows it,
  the error names the residue.
- **3D is one conformer**, a plausible geometry to look at — not a
  conformational search and not an energy statement.
- **CDXML is a side path.** It is round-trip validated, but PNG and SVG are
  the primary outputs and the ones the pixel tests cover.
- **Claude Desktop often answers knowledge questions without a tool.**
  "What is the solubility of paracetamol?", expected IR bands, a pH number or
  "compare aspirin and paracetamol" were answered from memory in 0 of 3 chats
  each (measured 2026-11-03), even though a tool fits. Drawing and figure
  requests are not affected. Adding "use ChemDraw" to the prompt made Desktop
  call `calculate_ph`, `lookup` and `compare_molecules` (2 of 2 chats each).
- **The extension targets macOS and Linux.** Windows is untested.
