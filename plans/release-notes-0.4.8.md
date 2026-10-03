### Fixed

- **A figure without a title no longer overwrites the previous one.** TLC plates,
  scope figures, spectra, calibration curves and reaction schemes used a fixed
  file name when no title was given, so the second untitled figure replaced the
  first. Now the name carries a short fingerprint of the inputs: different inputs
  give a different file, the same inputs give the same file (repeating does not
  fill the folder). With a title nothing changes. The new pharmacokinetics and
  dose-response figures follow the same rule, with the parameters in the name.
