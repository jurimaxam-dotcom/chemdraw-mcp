# Release audit — 2026-10-20

Scope: tracked files, all local Git refs/history, repository hygiene and Python
maintainability before 0.5.0. Claude owns release metadata, README, demo recording
and `chemdraw_tool/ui/`; changes in those areas require his own verification.
History was not rewritten; no branch or worktree was removed.

## Fixed by Codex

| Commit | Change | Evidence |
|---|---|---|
| `6a89263` | Ignore local `.tisch/`, `.env` and `.env.*`, retaining example/template files | Previously `git check-ignore` did not exclude them; now it does. Full `./test.sh`: exit 0, 6,964 passed / 16 skipped. |
| `20c204f` | Distinguish raw SMILES export filenames with a stable fingerprint | Twelve regressions failed first, then passed: E/Z butene and benzene/cyclohexane, individual and batch calls, PNG/SVG/CDXML. Full gate: exit 0, 6,976 passed / 16 skipped. Named compounds and explicit labels keep readable names. |

The accompanying documentation cleanup makes business/insurance/funding
checklists generic and removes `docs/.seen`, a local two-path reading marker.
It does not validate or update the legal/financial claims in those older notes.
The documentation cleanup also passed `./test.sh` (exit 0, 6,976 passed /
16 skipped) in a temporary copy of `20c204f` plus the cleanup, with the
committed UI, while Claude continued changing the shared UI working tree.
This is not a combined acceptance test of his later release/UI changes.

## Release findings requiring follow-through

1. **P1: source archive includes untracked local files.**
   `uv build --sdist --offline --out-dir /tmp/chemdraw-sdist-audit-20261020`
   succeeded, but its 310 members included `.radar-inbox/Kohulan--ChemAudit.md`
   (untracked), `.claude/settings.json`, `docs/.seen` and internal plans.
   Reproduced independently by inspecting the tar archive. Claude replaced
   the sdist file selection with an explicit allowlist. A second independent
   offline build to `/tmp/chemdraw-sdist-audit-after-20261020` contains 121
   members, including the UI bundle, and no agent/inbox/plan/document paths.
   This fixes distribution leakage in the working tree; the release owner
   still needs to commit and gate that change. Public internal documents
   remain in the Git repository even though they no longer ship in the sdist.
2. **P2: personal user paths in UI fixtures/harness, including history.**
   `.repro-harness/payload-desktop.json`, `payload.json` and `run.mjs` originated
   in `b532286`; `src/utils/displayPath.test.mjs` in `6c9b308`.
   Claude is removing the obsolete harness and replacing the test username.
   Removal in the current tree does not remove the historical copies.
   The interim handoff note repeated the user path in `813caa1`; its current
   wording has also been neutralized. A targeted final working-tree grep finds
   no remaining literal real-user home path from these findings.
3. **P2: historical personal assignments in business checklists.**
   `docs/produkt/recht-steuer-zahlung-2026-10.md`, introduced in `adaed6c`,
   and `plans/produkt.md` assigned insurance/funding/tax tasks to an individual.
   Current wording has been neutralized. These were planning suggestions, not
   evidence of actual benefit receipt, insurance status or a diagnosis.

At audit start, privacy review enumerated 924 unique historical text blobs over
192 commits across all local refs, plus 27 historical image blobs for metadata. Pattern
checks found no recognized API tokens/private keys, literal credential
assignments, private emails, actual postal addresses, medical records or private
university documents. `gitleaks` was unavailable; this was a historical
blob/pattern inspection, not a guarantee that arbitrary secrets cannot exist.
Author/committer identities use the public handle and GitHub noreply address.
The two other email matches are vendor support and a dependency copyright.
Images have no EXIF; some contain ordinary Matplotlib Software metadata.
Optional vault support and pharmaceutical sample data are product features,
not personal notes found by this audit.

## Hygiene and maintainability

- The `mcp-2-migration` worktree is clean. `git log main..mcp-2-migration`
  still lists `faff0d5` and merge `836324b`; `git cherry` does not mark the
  former patch as already applied. However, main's `c0dd24d` independently
  implements MCPServer, constructor versioning and the error wrapper, with
  additional fixes. Do not merge the old branch wholesale or call it fully
  merged. Keep it until its owner approves archival/removal.
- No tracked caches, environment files, office documents, private study files
  or generated release archives were found. Tracked media mostly demonstrate
  the product; the bundled UI and frozen fixtures are intentional.
- Removal candidates, not deleted: `scripts/gen_titrations.py` (one-off
  generator, writes at module import), `assets/anki-deck-panel.png` and
  `assets/fischer-esterification.png` (no references from other tracked text;
  external links cannot be ruled out). The optional `chemdraw.py` bridge is
  referenced only by its tests and intentionally documented as dormant.
- Keep installer compatibility wrappers, GIF generators, browser exercise
  modules, full-profile modules, tool snapshots and rendering goldens.
- `uv run ruff check chemdraw_tool --exclude chemdraw_tool/ui`: exit 0.
  No type checker is installed/configured, so typing is not verified.
- Defer dispatcher extraction: `calculate_content` is 236 lines (complexity
  18), `calculate_ph` 206, `calculate_solution` 159; reaction layout is 177.
  Optional Ruff C901 flags 13 functions. No identical function bodies longer
  than 12 lines were found; PubChem synonym response parsing repeats three
  short blocks in `databases.py` and is a later helper-extraction candidate.
- Remaining export limits: identical explicit labels can still overwrite
  files; overlong filenames are not handled by the narrow SMILES fix.

## Runtime proof boundary

`npm --prefix chemdraw_tool/ui run test:host`: exit 0, including data-sheet
layout/theme checks and second-switch caching, before Claude's subsequent UI
layout change. `./scripts/handshake.sh`: exit 0, six tools / five panels,
**but the script used its repository fallback** because no matching stdio
entry was present in the Desktop config. This proves repository stdio startup;
it does not prove the installed Desktop extension or its running process.
The earlier Tisch shorthand describing a registered-command handshake was
incorrect. Installation/restart/visible acceptance remains with the release.

## Decisions for the owner

Keep or rewrite the public Git history containing the user-path/checklist
references; no rewrite was attempted. Decide which internal documentation and
unused assets should remain public. Confirm release archive exclusions and
perform a new installed-Desktop smoke test after the final release build.
