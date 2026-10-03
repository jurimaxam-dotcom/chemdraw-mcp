
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

