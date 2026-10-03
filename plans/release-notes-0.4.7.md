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
