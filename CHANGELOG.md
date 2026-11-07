# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Second connector `chemdraw-pharma`.** Claude Desktop now gets two
  connectors from one installation: `chemdraw` with the default profile
  (16 tools) and `chemdraw-pharma` with the full profile (23 tools: the
  substrate-scope figure, calibration curve, pharmacology curves and the
  pharmacy calculators). Pick one per chat in the connector menu; switching
  needs no restart. `chemdraw-install` and `install.sh` write both entries
  with the profile pinned in `env`, the release ships a second bundle
  `chemdraw-mcp-pharma-<version>.mcpb` with its own extension ID and the
  same launcher (`scripts/mcpb_manifest.py` derives it from the base
  manifest), and `scripts/handshake.sh` checks every registered connector
  against the tool count of its profile.

### Changed

- **The 3D model fills the panel.** The `3D` chip now gives the ball-and-stick
  model the full panel width as a square (key facts move below it), and the
  molecule is scaled by its bounding radius instead of its largest axis value,
  so a flat molecule fills the bowl and a diagonal one no longer pokes out of
  it when rotated.
- **The single `chemdraw-tool` entry is migrated.** The installer replaces it
  with the two connectors (the backup keeps the old entry); `chemdraw-doctor`
  reports an old entry, a missing second connector and an unstartable
  command separately.

## [0.9.0] — 2026-11-07

### Added

- **3D button in the molecule panel.** Next to All H / Fischer / Haworth the
  structure view now has a `3D` chip: the first click calls `generate_3d`
  for the molecule on screen and swaps the drawing for the rotatable
  ball-and-stick viewer (explicit hydrogens, SDF written as usual), a second
  click or any 2D chip returns to the drawing; the conformer is cached, so
  switching back and forth costs one call. Before, 3D was only reachable
  through the chat. Export PNG is hidden while the 3D model is shown (it
  would export the 2D drawing), the chip is there for every molecule, and a
  failed load says so and can be retried.

- **"Found as" in the panel.** When a name was found under a different
  spelling (Dexamethason → Dexamethasone, a salt resolved to its free form),
  `generate_molecule`, `batch_generate` and `lookup_molecule_data` return
  `foundAs`, and the molecule and data panels show it under the title.

- **17 more IR rules in `predict_spectrum`.** C–F/C–Cl/C–Br/C–I,
  sulfonamide, sulfone and sulfoxide S=O, thiocarbonyl C=S, azide, imine/oxime
  C=N and the P=O/P–O bands of phosphates and related groups. The secondary
  amine rule no longer fires on amides and sulfonamides.

### Changed

- **CAS numbers come from PubChem's CAS section, checked and by majority.**
  Before, the first synonym that looked like a CAS number was taken, which
  gave ibuprofen the deprecated 58560-75-1. Now the number comes from the
  compound's CAS section, must pass the check digit, prefers the CAS Common
  Chemistry entry and otherwise the number most sources agree on; when the
  sources disagree evenly, the field stays empty instead of guessing.
  Ibuprofen now reports 15687-27-1.

- **pH values outside 0–14.** `calculate_ph` and the titration curve no
  longer clamp to 0–14: 2 M HCl gives pH −0.30 and the answer carries a note
  that the interval is not a physical limit and that activities, not
  concentrations, set the measured pH of concentrated solutions.

- **Mechanisms follow textbook conventions more closely.** SN2 draws the
  curved arrows on the reactants and the transition state without arrows; the
  SN1 carbocation is drawn trigonal planar; a second solvent molecule (water or
  the alcohol) takes the proton instead of a free H⁺, so SN1 with water ends in
  ROH + X⁻ + H₃O⁺; the Fischer esterification moves the proton in two steps via
  the alcohol and now has 8 steps instead of 7 (the old proton transfer,
  step 4, is now steps 4 and 5, so later `current_step` numbers shift by
  one); unbranched terminal alkyl chains of five carbons or more are
  labelled (C₁₇H₃₅) instead of drawn out. The mechanism result carries
  `notes` — E2 competes for a secondary halide with a strong base
  (isopropyl iodide + OH⁻) or a bulky base such as tert-butoxide, E1 for an
  SN1 cation with a β-hydrogen — and `reversible` (Fischer), and the panel
  shows both: the note under the title, ⇌ between the steps.

- **German trivial names resolve more often.** When no source knows a German
  name, the resolver now tries its English spelling as a last step: drug-name
  endings (Dexamethason → dexamethasone, Amilorid → amiloride, Lamivudin →
  lamivudine), acids (Maleinsäure → maleinic acid, Bernsteinsäure → succinic
  acid), salts (Natriumlactat → sodium lactate, Alcuroniumchlorid → alcuronium
  chloride) and a racemate prefix ((RS)-Ketamin → ketamine). Further
  spellings are tried on the way: Greek letters, the halogen vowel
  (Fluorcytosin → fluorocytosine), a form suffix (anhydrate, "(free acid)",
  A+B), only the counter-ion in English (Cefalotin sodium) and the optical
  rotation sign dropped next to R/S ((S)-(−)-timolol → (S)-timolol).

- **Direct hits are cross-checked.** A PubChem hit is compared with the
  English spelling and an OPSIN hit without locants with PubChem; when they
  disagree, the resolver prefers the free form over a salt unless the name
  carries a salt word (Bendamustin → the base, not the hydrochloride), the
  more defined stereo form (Naloxon) and PubChem's skeleton over OPSIN's
  guess, while a tautomer does not count as a different substance. As a
  consequence "D-glucose" now resolves to PubChem's pyranose ring (Haworth
  button) instead of the open chain; the open chain is "aldehydo-D-glucose".
  On the project's 711-name evaluation (German trivial names, IUPAC names,
  SMILES; `docs/evidence/masse-eval-2026-11/`) all resolver changes together
  take the correct identities from 591 (0.8.0, run of 2026-11-05) to 683
  (run of 2026-11-07, 83 % → 96 %); a handful of reference entries were
  corrected between the two runs, and the last resolver commit came after
  the second.

- **RDKit 2026.9.1; some drawings change orientation.** The lock moves from
  RDKit 2026.3.6 to 2026.9.1, whose 2D layout mirrors or rotates a few
  molecules compared with 0.8.0 (aspirin and glucose mirrored horizontally,
  ring atoms of ibuprofen and benzene one position on). The structures are
  chemically identical and the new layout is the checked reference now.
  Playwright moves 1.60.0 → 1.64.1 on both the Python and the JavaScript
  side.

### Fixed

- **`generate_spectrum` accepts the spectrum type in any case.** The
  description lists "IR, NIR, Raman, UV/Vis", so the model sends `"IR"` —
  which the lookup table rejected. The type is now trimmed and lower-cased.

- **Trivial names no longer get split like systematic names.** OPSIN read
  "tropicamide" as tropic acid amide, "methyldopa" as N-methyl-DOPA and
  "chloroxylenol" as a non-aromatic ring. A carbon-containing name without
  locants (no digits, brackets or N-/N,N-/O-/S-/P-/o-/m-/p- prefixes) is now
  checked against PubChem; when the skeletons differ, PubChem's record wins.
  Names with locants stay offline, and without network OPSIN's answer is used
  as before.

## [0.8.0] — 2026-11-05

### Added

- **Mechanisms with your own molecules** (`generate_mechanism`): the steps are
  now drawn with the substrates you pass, not a fixed example. The reaction
  centre is found per family, intermediates and products are derived from your
  molecules, and the arrows point at their atoms. SN2 inverts a stereocentre
  ((R)-2-bromobutane + cyanide gives the (S)-nitrile); SN1 marks a stereogenic
  product as racemic. Each family has a stated limit:
  - SN2: methyl, primary or secondary alkyl chloride, bromide or iodide with
    one anionic nucleophile (OH⁻, CN⁻, I⁻, Br⁻, RO⁻, N₃⁻, RS⁻/HS⁻).
  - SN1: tertiary or benzylic alkyl halide with water, an alcohol or one of
    those anions.
  - Fischer esterification: one carboxylic acid with one primary or secondary
    alcohol.
- Result fields `substrates_drawn` and `fallback_reason`: without substrates,
  or if the drawing fails, the textbook example is shown and the result says so.
- The SN2 product step names the configuration of the new stereocentre
  ("Products, (S)" for (R)-2-bromobutane + cyanide), computed by CIP rules on
  the product rather than read off the wedge.

### Changed

- Substrates outside a family's limit now get an error that names the reason
  (for example "tertiary halide — … use sn1") instead of a SMARTS pattern;
  counter-ions such as Na⁺ are ignored.
- The SN1 textbook example is now 2-bromo-2-methylpropane + water (a secondary
  halide is outside the SN1 limit).
- SN1 refuses allylic halides (also tertiary allylic ones) with the reason: the
  allyl cation is delocalised, so water attacks at both ends and two products
  form; drawing only one of them would be wrong.
- The curved arrow from a breaking bond to the leaving group ends beside the
  atom instead of under its label.
- Mechanism titles for SMILES input show a name with its stereodescriptor
  ("(R)-2-bromobutane + cyanide") instead of the molecular formula, which did
  not even tell constitutional isomers apart. Simple ions are named offline;
  other names come from PubChem (3 s timeout, cached per process). Offline the
  title shows the SMILES with its descriptor, and the mechanism is still drawn.
- `generate_reaction` states that curved-arrow mechanisms exist only for SN1,
  SN2 and Fischer esterification: for any other mechanism (Diels–Alder) the
  net scheme is drawn and the answer says that the arrows are not.

### Fixed

- Fischer esterification follows the textbook sequence (Clayden, ch. 10):
  protonation, attack of the alcohol, proton transfer to an OH, loss of water
  as –OH₂⁺ while the remaining OH re-forms C=O⁺H, deprotonation that returns
  H⁺ (7 steps instead of 6, so `current_step=6` is now the deprotonation).
  Water no longer leaves from a neutral OH. The textbook examples are now
  built from the same derivation as your own substrates, which also removes
  the stretched C–O bond in the SN2 example.
- The curved arrow from a breaking bond to its leaving group is a full arc
  past the atom instead of a short hook.
- SN2 transition state: nucleophile and leaving group carry δ⁻ instead of two
  full negative charges ("N≡C⁻ ··· C ··· Br⁻" added up to −2 instead of −1;
  Clayden, ch. 15). Brackets and ‡ stay.
- SN1 with water or an alcohol goes through the oxonium ion (R–OH₂⁺ or
  R–O⁺(H)R′) with its own deprotonation arrow, and the products list H⁺
  (6 steps instead of 5, so `current_step=5` is now the oxonium ion; anionic
  nucleophiles keep 5 steps). The last step was "Product (after
  deprotonation)" and showed ROH + X⁻ without the proton.
- A charge on an atom whose bond leaves to the right is drawn on the left:
  the terminal N of azide read as N=N⁺=N⁻ because the "⁻" sat under the double
  bond.
- Curved arrows from "HO" or "H₂O" start at the O, not at the H; a labelled
  carbon shows its hydrogen ("CH⁺" in the 1-phenylethyl cation, "CH" in the
  2-bromobutane transition state).
- Mechanism titles: PubChem names are written in running-text case
  ("tert-butyl chloride", not "tert-BUTYL CHLORIDE"), keeping stereodescriptors
  and N-/O-/S-/D-/L- prefixes; "(2R)-2-chloropentane" becomes
  "(R)-2-chloropentane" when there is one stereocentre. A salt such as
  `CC[O-].[Na+]` is named by its reacting ion ("ethoxide") instead of showing
  the raw SMILES; methanethiolate, methoxide, ethoxide and tert-butoxide are
  named offline.
- All steps of a mechanism share one frame, so a step no longer looks larger or
  smaller than its neighbours when each is shown at the same width.
- Mechanisms with the reaction centre in a ring (cyclohexyl bromide,
  1-bromo-1-methylcyclohexane) keep a regular ring in every step: the SN2
  transition state no longer folds the ring into a bicyclic-looking shape, and
  no ring carbon is labelled "C".
- Names unknown to every database are reported as "not found" again. NCI CIR
  answers an unknown name with HTTP 500 and the body "Page not found", which
  counted as a source outage: every German trivial name PubChem does not index
  got "retry once the connection is stable" instead of "use the English name"
  (found by the identity run over 711 inputs, where 79 of them, 11 %, turned yellow for it).
- `predict_spectrum` reports the two nitro bands again (1500–1560 and
  1345–1385 cm⁻¹). The rule's SMARTS only matched the uncharged `N(=O)=O`
  form, while RDKit stores every nitro group charge-separated, so the rule
  never fired (0 of 10 nitro compounds in the IR coverage run). Nitrate esters
  (O–NO₂) are deliberately not counted as nitro.
- `calculate_ph` for concentrated strong bases: 10 M NaOH gave pH 15.05
  instead of 15.00 because the quadratic solution subtracted two nearly equal
  numbers; the rationalised form has no cancellation.

## [0.7.0] — 2026-11-03

The default profile grows from 7 to 16 tools: mechanisms, 3D, look-ups,
spectra, TLC plates, pH curves and pH numbers join drawing and Anki.

### Added

- **Reaction mechanisms** (`generate_mechanism`): SN1, SN2 and Fischer
  esterification as textbook examples, step by step with curved arrows.
  Other mechanisms are not drawn — the tool says so instead of guessing.
- **Rotatable 3D model** (`generate_3d`): drag to rotate in the panel.
- **Look-ups as text** (`lookup`): properties, GHS safety, physical data,
  biochemistry and pathways from PubChem, ChEBI, UniProt and KEGG.
- **Expected spectra** (`predict_spectrum`): IR bands for a structure, the
  groups behind a measured wavenumber, ¹H signal count and integral ratio.
  Deterministic; no ppm shifts.
- **Spectrum figures** (`generate_spectrum`): IR, NMR, MS and UV/Vis from
  peak lists, with an Export PNG button.
- **TLC plates** (`generate_tlc`): lanes, spots and co-spot from Rf values.
- **Titration curves and species distribution**
  (`generate_titration_curve`, `generate_species_distribution`).
- **pH numbers with the working** (`calculate_ph`): weak/strong acids and
  bases, buffers, buffer recipes and ionisation, exact charge balance next
  to the textbook approximation.

### Fixed

- Titration curves: half-equivalence markers sit on the curve's exact pH
  instead of on the pKa.
- Compare panel in dark mode: the shared scaffold was drawn white on the
  white figure background.
- Anki deck preview showed card HTML literally (`<i>vor</i>`).
- Export PNG button on TLC plates, spectra and plot figures.
- Anki card text is escaped; only `<b> <i> <sub> <sup> <br>` and entities
  pass. Panel source links accept http/https only.

### Changed

- Server instructions route a pH, buffer or ionisation number to
  `calculate_ph`. With on-demand tool loading (Claude Code tool search)
  this moved the pH cases from 6/12 to 18/18.
- Desktop bundle: uv is fetched with a checksum, dependencies are
  hash-locked; CI actions are pinned to commit SHAs.

### Known limitations

- In Claude Desktop, knowledge-style questions are often answered from
  memory without calling a tool, even when one fits: "What is the
  solubility of paracetamol?", expected IR bands, pH numbers, "compare
  aspirin and paracetamol" (measured 0 of 3 chats each, 2026-11-03).
  Drawing requests ("draw ibuprofen") and figure requests are not affected.
  Naming the tool helps: adding "use ChemDraw" to the prompt made Desktop
  call `calculate_ph`, `lookup` and `compare_molecules` (2 of 2 chats each).

## [0.6.0] — 2026-10-26

### Added

- **All H view.** A button under the structure switches between the skeletal
  formula and a drawing with every hydrogen; Export PNG takes the visible one.
- **Fischer and Haworth projections.** Open-chain sugars and amino acids get
  a Fischer button, pyranoses and furanoses a Haworth button. Drawn in the
  textbook style (CHO, CH₂OH, HO/H). Isoleucine, threonine, glycosides and
  alditols are not covered; a ring sugar explains how to get its Fischer form
  instead of silently opening the ring.
- **Stereoisomers to choose from.** "Show variants" next to the stereo hint
  lists every stereoisomer of the open centers (up to 3) with R/S or E/Z
  labels; one click draws it with wedges. Parameter `stereo_variants`.
- **Apply coefficients.** The balance badge's suggestion can be applied with
  one click ("2 H₂ + O₂ → 2 H₂O"). Parameter `coefficients`, set only when
  the user asks for a balanced equation.
- Parameter `view` (`fischer`, `haworth`, `all_h`) opens the molecule panel
  on that drawing.

- **Isomer picker for family names.** "xylene", "Kresol", "toluidine",
  "butanol" or "Glucose" no longer silently become one isomer. The panel
  shows every candidate as a small picture; one click draws it.
- **Equilibrium and retrosynthesis arrows** in `generate_reaction`
  (`arrow="equilibrium"|"retro"`), plus text below the arrow
  (`conditions_below`). Formulas in conditions are subscripted (H₂SO₄).
  CDXML carries the arrow type.
- **Balance check for reactions.** The panel shows whether the drawn
  equation is balanced, what is missing, or suggested coefficients. The
  drawing itself is never changed.
- **Unspecified stereocenters and E/Z bonds are flagged** in the molecule
  and data panels; hover highlights the atoms.

### Changed

- **Smaller responses.** All H, Fischer and Haworth are fetched on the first
  click instead of riding along in every answer (ibuprofen: 27 KB → 9 KB of
  text the model has to read).
- **GHS safety data grouped by source.** The EU harmonised classification
  (or the ECHA aggregate) leads, hazard statements are sorted by agreement,
  "not classified" is its own finding, other sources are collapsed. A source
  whose record name does not match the substance is never used as the lead.

### Fixed

- **Reactions entered as SMILES are labelled with their formula** (H₂, O₂,
  H₂O) instead of the SMILES text.
- **Broken SMILES are reported, not guessed.** `c1cccc1` used to come back
  as cyclopentane via a name lookup; now it fails with the RDKit cause, the
  position and a suggested fix (nothing is drawn).

### Known limitations

- In Claude Desktop a request that names the projection ("show the Haworth
  projection of …") is usually answered by Desktop's built-in visualizer:
  Desktop decides before it loads this server's tools. "Draw beta-D-glucose"
  opens the panel, whose Haworth button gives the projection.

## [0.5.2] — 2026-10-25

### Fixed

- **Anki card: the structure sits directly on the card.** The picture now has
  a transparent background, so there is no white box in light mode and no
  black box in night mode. Exported PNG/SVG files keep their white background.

## [0.5.1] — 2026-10-24

### Added

- **Add to Anki button on the molecule panel.** One click adds a flashcard for
  that molecule (structure on the front, name and formula on the back) to the
  Anki deck "ChemDraw"; on macOS Anki opens and imports it. Clicking again for
  the same molecule updates the card instead of duplicating it.
- **`export_anki_deck` is part of the default profile** (now 7 tools, 6 with a
  panel) and accepts `deliver="open"` to open the deck file in Anki on macOS.
- **Cleaner Anki card:** front shows only the structure, back name, formula and
  CAS; night-mode aware.

## [0.5.0] — 2026-10-20

### Changed

- **Panel text is English throughout.** The data sheet now reads *IUPAC name,
  Molecular formula, Molar mass, H-bond donors/acceptors, CAS No.*, and the
  loading lines read *Connecting… / Waiting for data…*.
- **Mechanism titles show the names you typed** ("acetic acid + ethanol")
  instead of the resolved SMILES.
- **New README demos**, recorded from the real panel and server
  (`scripts/demo-video.sh` also writes 9:16 and 1:1 videos).
- **Runs on the `mcp` 2.x Python SDK** (pinned `mcp>=2.3,<3`, tested with
  2.3.0). `FastMCP` became `MCPServer`, and the server version is now a
  constructor argument. What a client sees is unchanged in both profiles: the
  same tools with byte-identical names, descriptions and schemas, the same panel
  tools, `serverInfo.version` still the package version, and structured output
  still also arrives as a JSON text block. Error messages that tell the user
  what to do (a name that did not resolve, sources offline, invalid input) still
  reach the client — mcp 2.1+ would otherwise replace them with a generic
  "Error executing tool".
- **The MVP panel is easier to read and use.** Molecule names and facts have a
  clearer hierarchy, structures and details stack on narrow panels, and the data
  sheet keeps labels beside their values. The UI follows host fonts and theme,
  shows an explicit PNG export label and supports keyboard group highlighting.
  Updating the molecule in an existing panel now discards the previous data-sheet
  cache. Chemical drawing and exported PNG pixels remain unchanged.
- **MVP is the default server profile.** Four drawing workflows remain active:
  individual structures, batches, comparisons and reaction schemes, with data
  sheets and PNG export as panel support (six registered tools). Other tools are
  not registered and cannot be called. Set `CHEMDRAW_PROFILE=full` and restart
  to restore the complete catalog. Tool descriptions and server instructions
  match the selected profile; the full catalog and its snapshots remain tested.
- **The panel runs on `ext-apps` 2.0.** The wire protocol between Claude Desktop and
  the panel is unchanged (2.x panels run in 1.x hosts and the other way round), so
  nothing changes for users. The bundled panel is about a quarter smaller
  (524 kB to 399 kB) because the old SDK and zod 3 are no longer part of it.

### Added

- **Pharmacokinetics practice problems** in the Praktikumsrechner: half-life from
  clearance and Vd, concentration after an i.v. dose, mean steady-state
  concentration, loading dose, accumulation factor and the uncharged fraction at a
  given pH — each with the working. The drug is "Wirkstoff X" with made-up values,
  so no invented number passes as real drug data. Every solution is checked against
  the same formulas as `calculate_pharmacokinetics`.

### Fixed

- **Comparison and plot panels use their full height again.** The panel
  heading grew vertically in column layouts and squeezed the image into a strip.
- **The source package (sdist) ships only the package**, README, licence and
  changelog — an allowlist instead of a blocklist, so local working files can
  never end up on PyPI.

## [0.4.8] — 2026-10-03

### Fixed

- **A figure without a title no longer overwrites the previous one.** TLC plates,
  scope figures, spectra, calibration curves and reaction schemes used a fixed
  file name when no title was given, so the second untitled figure replaced the
  first. Now the name carries a short fingerprint of the inputs: different inputs
  give a different file, the same inputs give the same file (repeating does not
  fill the folder). With a title nothing changes. The new pharmacokinetics and
  dose-response figures follow the same rule, with the parameters in the name.

## [0.4.7] — 2026-10-03

### Added

- **`generate_pk_curve` and `generate_dose_response`** — the two pharmacology
  figures. The first draws plasma concentration over time (single dose or
  repeated doses with the build-up to steady state, oral or i.v., with the
  therapeutic window); the second draws the Hill curve on a log axis with a
  competitive antagonist shifting it to the right. Both use the panel that
  already shows titration curves, and share their formulas with
  `calculate_pharmacokinetics`, so figure and number agree.
- **`calculate_ph` knows the degree of ionisation.** New `topic` "ionisation":
  give the pKa, the pH of the medium and whether the drug is an acid or a base;
  it returns the charged and uncharged fractions (Henderson-Hasselbalch), the
  logic behind absorption in the stomach versus the gut.
- **`calculate_pharmacokinetics`** — pharmacokinetics in the one-compartment
  model, with the working: half-life, concentration over time, AUC, tmax and
  Cmax after an oral dose, accumulation and steady state, loading and
  maintenance dose. Give Vd plus any one of ke, half-life or clearance; values
  that contradict each other are named instead of one being picked silently.

### Changed

- **Mechanism overview is readable.** Every step is drawn with the same bond
  length, so a wide picture (a product plus a far-away bromide) no longer shrinks
  its atoms while a narrow one grows. The overview is now one step per row with
  downward arrows instead of a wrapping row, and the SN2 transition state keeps
  its three fragments apart so the dashed partial bonds and curved arrows no
  longer run through the atom labels.

## [0.4.6] — 2026-10-02

### Fixed

- **An interrupted first start no longer blocks the next one.** If Claude Desktop
  cancelled the bundle's first-time install midway, the install lock stayed behind
  and the next start waited up to 10 minutes for it. The start script now releases
  the lock when it is stopped (TERM/INT/HUP), and records its PID in the lock, so a
  lock whose owner has died — even by `kill -9` — is taken over immediately.
- **The species-distribution legend no longer covers the curves.** It sat inside
  the axes and hid the end of the last curve; it now stands beside them.

### Changed

- **Panels show `~/ChemDraw-Output/…` instead of the full home path** under saved
  figures and decks (the full path stays as a tooltip).
- **A data-sheet request no longer fans out into extra tool calls.** The
  `lookup_molecule_data` description now says the sheet already holds the
  properties and GHS data it lists. In a measured prompt-to-tool run this cut the
  calls for "data sheet with everything" from 6–8 to 4.

## [0.4.5] — 2026-10-02

### Changed

- **Name lookups no longer wait seconds for OPSIN first.** OPSIN (the offline
  IUPAC-name parser that runs before any network lookup) used to start a new
  Java VM for every name — about 2–6 s each, paid in full by every trivial name
  like "methylphenidate" before PubChem was even asked. OPSIN now runs as one
  long-lived Java process that answers name by name: after the first start
  (about 1.5 s) a name takes 1–15 ms instead of 2 s. Behaviour is unchanged —
  systematic names still resolve offline, Java stays optional, and if the
  long-lived process cannot start, the old one-VM-per-name path takes over.

## [0.4.4] — 2026-10-02

### Fixed

- **A freshly installed bundle could not find its own release.** Right after
  0.4.3 went out, uv answered from its cached copy of the PyPI index ("there is
  no version of chemdraw-mcp==0.4.3") and Claude Desktop failed to start the
  server. The bundle now refreshes the index for chemdraw-mcp when it installs
  (and in the fallback). The normal start does not call uv at all, so this
  costs nothing after the first launch.

## [0.4.3] — 2026-10-02

### Fixed

- **The Claude Desktop bundle failed to start in about one launch out of four.**
  Desktop's log showed 11 of 38 launches timing out on `initialize` (median
  answer 21.6 s, Desktop gives up at ~55 s). Part of it was `uv tool run`
  rebuilding its throwaway environment after every `uv cache clean` (≈50 MB from
  PyPI). The bundle now installs once into its own tool directory, which survives
  cache cleaning and leaves a global `uv tool install chemdraw-mcp` alone, and
  then starts the server directly: 1.6 s after a cleared cache instead of 15.4 s.
  Desktop starts two instances at once; a lock keeps the second from tearing
  down the first one's fresh install (measured: 1 of 3 parallel cold starts
  survived before, 3 of 3 now).

- **`calculate_content` inverted the titer from a reference titration.** A
  titrant 2 % stronger than nominal (t = 1.02) came out as t ≈ 0.98, so every
  sample corrected with it read about 4 % low. The titer is now declared
  content / apparent content of the reference, and a test builds the reference
  readings from a known titer and checks the round trip.

- **The panel's Data button failed for every molecule.** PubChem no longer
  returns `CanonicalSMILES`, so the molecule payload carried no SMILES and the
  button asked for the data sheet by display name ("Methylphenidat") — which
  does not resolve. The payload now always carries the resolved SMILES, and
  `lookup_molecule_data` fetches its record by InChIKey like the molecule panel
  does, instead of sending a SMILES to PubChem's name endpoint (HTTP 404).

## [0.4.2] — 2026-10-01

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
