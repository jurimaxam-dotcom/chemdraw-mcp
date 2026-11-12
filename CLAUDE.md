# chemdraw-mcp

## Current focus: general chemistry MVP (14.10.2026)

The default server profile is `mvp`: `generate_molecule`, `batch_generate`,
`compare_molecules`, `generate_reaction`, `export_anki_deck` (since 21.10.2026,
for the panel's Add to Anki button and the chat route), plus
`lookup_molecule_data` and `save_png` for panel support, and since 30.10.2026 `generate_mechanism`, `generate_3d`, `lookup` and (Welle 2) `predict_spectrum`, `generate_spectrum`, `generate_tlc`, `generate_titration_curve`, `generate_species_distribution`, `calculate_ph`, and since 10.11.2026 `generate_protein_or_antibody` (17 tools, 13 with a panel). Set `CHEMDRAW_PROFILE=full`
and restart to restore the full catalog (24 tools, 17 with a panel).
Other tools remain implemented and tested, but are not registered in the MVP.
The immediate goal is a reliable input → correct structure → usable export
workflow for general chemistry. Specialized pharmacy, trainer, quiz and payment
expansion is paused. The existing browser trainer remains separate.
`tests/server_catalog.py` explicitly builds the full profile for the historical
taxonomy, snapshots and payload checks; `tests/test_server_profiles.py` verifies
the actual default and explicit profiles in fresh processes. The stdio handshake
derives its expected counts from the selected profile.

Helfer reports are claims to verify, not acceptance evidence (Jay, 14.10.2026).
Independently inspect the diff and run the relevant checks before confirming
completion. Distinguish repository code, installed package/dependencies and the
running Desktop process; matching tool counts alone do not establish matching code.

MCP server for Claude Desktop that turns molecule names or SMILES into
publication-style 2D structure drawings. PNG/SVG are the primary outputs
(rendered offline via RDKit) — ChemDraw CDXML is an optional extra format,
never a runtime requirement.

## Scope: this repo builds, the sister repo markets (Jay, 11.11.2026)

This repo owns server code, tools, panel, tests, releases and the files in this tree (README, `docs/`). Everything
outward-facing — posts, profiles, directory listings, videos, clips, logo, channel research — belongs to the private
sister repo `~/Documents/projects/chemdraw-vermarktung`; its `docs/zustaendigkeit.md` is the single ownership table.
If Jay asks for marketing work here, do not do it and do not track it in this plan: hand it over at once with
`~/.claude/bin/schwester weiter "<request verbatim + context>"` and tell Jay in one line where it went. Before a
work package that touches both sides (GIFs, recordings, README header), read `~/.claude/bin/schwester stand` and
claim it with `~/.claude/bin/schwester reserviere <name>`. Marketing status lives only in the sister
plan; `plans/mcp-server.md` carries at most a pointer line.

## Helpers: what differs from the global rule (11.11.2026)

Who builds, who helps and when a second session is worth it follows the global helper-routing rule
(`~/.claude/CLAUDE.md`, section Arbeitsweise); the three-session split of early November is gone. The owner
session builds itself. Only this differs or adds here:

- **Desktop hand tests and screen recordings stay with Codex** — one Tisch order per test run with all steps,
  no status messages in between, and the `claude-desktop` lease as described under Auto-Gate.
- **A hand test is due only before a release and after a host-specific change** (Jay, 12.11.2026) — not per
  tool or feature. Host-specific means: manifest/bundle/install path, `_meta.ui`, host capabilities, CSP, ext-apps
  SDK bump, or a Desktop update that the doku-waechter flags. Everything else is accepted on the fixed
  workflow below (stages 1–4). What the hand tests of 07.11. found were routing and permission cases (model
  called no tool in 3 of 9, missing "Always allow"), not panel bugs — and **no scripted run predicts those**:
  the same three prompts are green in `run_claude.py` with Opus (measured 12.11.2026). Whether Desktop's model
  calls the tool stays a hand-test question.
- **Desktop cannot be driven over CDP** (measured 12.11.2026): started with `--remote-debugging-port=9222` it
  exits with "refusing to start — a debugging or network-override switch is present on the command line". So
  Playwright cannot attach; AX clicks via `scripts/ax-claude.sh` remain the only driver. DevTools (`⌘⌥I`,
  `allowDevTools` is on) is for diagnosis of a failing panel, never an acceptance step.
- **Review before a release** runs without a pane: `codex exec review --commit <sha> < /dev/null`. The reviewer
  only reports; the owner checks every finding against the code before taking or rejecting it.
- **A test report that found a bug is a result**, not an abort: `status: erledigt` with the finding under
  `befunde:`; what to do about it is the owner's call.

## Build / Run

```bash
./install.sh                 # one-command setup: uv + deps + Claude Desktop config
uv sync                      # deps only
uv run chemdraw-tool-server  # run the MCP server (stdio) manually
uv run chemdraw-doctor       # diagnose the installation (env, paths, network)
```

`install.sh` registers the server via `chemdraw_tool/desktop_config.py`
(idempotent merge, writes a `.bak` backup, never touches other configured MCP
servers). The config logic lives in the package, not in `scripts/`, because the
wheel ships only `chemdraw_tool` — PyPI users get `chemdraw-install` and a fully
working `chemdraw-doctor` from it. Claude Desktop launches MCP servers with a
minimal GUI PATH, so `command` must be an absolute path; the installer resolves
it and prints what it wrote.

**If a host keeps the server process alive (Claude Desktop does), restart it
after changing server code or dependencies** — a stale process mixes old
in-memory modules with new files and manifests as confusing RDKit/Boost
signature errors. Restart it yourself after such changes (`osascript -e 'quit
app "Claude"' && sleep 2 && open -a Claude`); an MCP stdio handshake
(initialize → tools/list) is the hard proof that the registered command works.

## Anthropic-Doku im Blick (Pflicht vor Panel-/Architekturarbeit)

Was Claude Desktop für MCP-Apps, Extensions und Panels anbietet, ändert sich laufend (ext-apps 2.0, neue
MCP-Fassung, neue Leitfaden-Seiten). Deshalb: **vor Panel-, Manifest- oder Architekturarbeit**
`uv run python scripts/anthropic_sync.py --check` — es meldet NEU/GEÄNDERT/WEG und neue Paketversionen. Bei
Änderungen die Seiten lesen (`--diff URL`), `docs/anthropic/abgleich.md` anpassen, **dann** bauen, dann `--update`.
Die Textkopien liegen nur lokal (`.cache/`, Anthropics Urheberrecht); im Repo stehen Fingerabdrücke und unsere
Auswertung. Ein Sitzungsstart-Hook meldet, wenn der Stand älter als 7 Tage ist.
Seit 12.11.2026 läuft derselbe Check täglich auf GitHub (`.github/workflows/doku-waechter.yml`, `--check --exit-code`): bei
einer Änderung öffnet er ein Issue mit dem Label `doku-waechter` (ein Issue je offenem Stand, schließt sich nach
`--update` + Push von selbst). Beobachtet werden auch das Desktop-Changelog, die Modellübersicht, die
Modell-Abkündigungen und die Plattform-Release-Notes (`docs/anthropic/quellen.json`); Nebenversionen von Paketen
lösen keine Meldung aus, eine neue Hauptversion schon. Der Wächter lässt Claude die Änderung gleich im Issue einordnen
(`anthropics/claude-code-action`, Geheimnis `CLAUDE_CODE_OAUTH_TOKEN`, nur lesen und kommentieren). `.github/workflows/claude.yml`
beantwortet `@claude` in Issues und PRs — nur vom Eigentümer; ein automatisches Review fremder PRs gibt es bewusst nicht.
Zwei weitere Workflows nutzen denselben Zugang nach Zeitplan (12.11.2026): `abhaengigkeiten.yml` kommentiert täglich jeden
offenen Dependabot-PR einmal je Stand (was ändert sich, trifft es einen Pin, mergen ja/nein — der Merge bleibt Handarbeit),
`zustandsbericht.yml` legt montags ein Issue mit dem Label `zustandsbericht` an, wenn etwas offen ist (rote CI, PRs, Issues;
fremde Issues werden dort eingeordnet, nie öffentlich beantwortet). **Muster für jeden weiteren Claude-Workflow:** zwei Jobs —
der mit `CLAUDE_CODE_OAUTH_TOKEN` hat nur Leserechte, Tools `Read,Grep,Glob,Write`, und schreibt eine Datei; der mit
Schreibrecht hat kein Modell, prüft die Datei (Länge, `@` entschärft, Stand unverändert) und postet. Kein
`pull_request_target`, eine Shell-Vorprüfung entscheidet, ob das Modell überhaupt startet.

## Fixed workflow: which check when (Jay, 12.11.2026)

No mouse until stage 5. Research behind it (12.11.2026): the ext-apps repo itself tests panels with Playwright
behind a reference host, none of five surveyed server repos tests against a real client, and Anthropic's own
guidance ends in a manual check in the real client.

1. **While editing:** `npm --prefix chemdraw_tool/ui run test:ui:watch`, and for the panel
   `npm --prefix chemdraw_tool/ui run build:watch` — `chem_app_ui()` reads `dist/` on every `resources/read`,
   so the next tool call shows the new panel without a server restart. A watch rebuild is **not** byte-identical
   to a clean build (measured: 3,000.67 vs 2,996.67 kB for the same source): stop the watch and run
   `npm --prefix chemdraw_tool/ui run build` before committing, or the gate goes red on the bundle.
2. **Before every commit:** `./test.sh`.
3. **After a panel or tool change:** `test:host`, `./scripts/handshake.sh`, and
   `npm --prefix chemdraw_tool/ui run test:inspector` — every panel tool rendered by a host we did not write
   (MCP Inspector 2.15.0 web, deep link, real server over HTTP via `scripts/dev_http.py`).
4. **Before a release, scripted:** `uv run python evals/tool-routing/run_claude.py --echt` (Claude Code calls
   the real server once per panel tool: tool call, error-free result, no denied call) and the stub run of the
   routing cases.
5. **Before a release and after a host-specific change, by hand:** one Codex run in Desktop (see Helpers) for
   what only Desktop shows — the panel is visible, the permission dialog, and whether the model calls the tool.

`evals/panel-beispiele.json` feeds stages 3 and 4 (arguments, prompt and a ready selector per panel tool);
`tests/test_panel_beispiele.py` keeps it in sync with the registration, so a new panel tool needs an entry.
`scripts/dev_http.py` is a development launcher bound to 127.0.0.1 and deliberately no wheel entry point: the
server writes files and has a destructive tool, so HTTP without auth is not a product feature.

## Auto-Gate (the project's green/red)

```bash
./test.sh                                     # lint + backend + bundle + frontend
npm --prefix chemdraw_tool/ui run test:watch  # JS unit tests in watch mode
./scripts/handshake.sh                        # real stdio handshake (needs network)
npm --prefix chemdraw_tool/ui run test:host   # panel in a sandboxed iframe behind a real AppBridge host + real server (needs network)
uv run python scripts/identitaet.py           # name → right molecule (needs network)
```

One-time frontend setup: `cd chemdraw_tool/ui && npm install && npx playwright install chromium`

`handshake.sh` sits **outside** the gate because its first run downloads the MCP
Inspector. It is the only check that starts the server the way Claude Desktop
does — the absolute command out of `claude_desktop_config.json` — and asserts
the two numbers the Python side predicts (default MVP: 17 tools, 13 with a panel;
full profile: 24 tools, 17 with a panel).
`test:host` is the stand-in for "type it into Claude Desktop and look": it embeds the built UI the way Desktop does (srcdoc iframe, `sandbox="allow-scripts"`), connects through the SDK's `AppBridge`, runs the real server, clicks Data for methylphenidate (CAS 113-45-1, cache on second switch) and Add to Anki (the host rewrites `deliver` from `open` to `apkg`, so no Anki starts; the file lands in a throwaway HOME). It cannot see which tool the model picks (`evals/tool-routing`) or Desktop's own host quirks. **What only Desktop shows (the hand test) goes to Codex, not Jay** (Jay, 26.10.2026): one `tisch auftrag codex` per test run, carrying every step at once — prompt, clicks, expected result per step and screenshots to `/tmp/chemdraw-desktop-test/` (see "Helpers" below); Codex drives the GUI via `scripts/ax-claude.sh` (needs the private sister repo `~/Documents/projects/chemdraw-vermarktung`, which holds `ax-claude.swift` and the marketing material since 05.11.2026). Jay gets the result, not the chore. **Claude Desktop is one shared resource: one driver at a time** (Jay, 10.11.2026, after two helpers typed into the same window and spoiled a take). Before any GUI action on Desktop — `ax-claude`, typing, clicks, window or settings changes, restart — run `~/.claude/bin/tisch leases` in `~/Documents/projects/chemdraw-vermarktung` and reserve there: `tisch reserviere claude-desktop --minuten <n>`; a foreign lease on `claude-desktop` or on a recording folder under `out/` means hands off, ask through the Tisch instead. Check every helper session in both repos (`herdr agent list`), not only the own pane. Release with `tisch gib-frei` when done. In-process tests cannot see the two failure modes that have actually cost time
here: a stale server process and a GUI PATH that cannot find `uv`.

The gate is built against two failure modes that cost more than a real test
failure:

- **false red** — the dependency guard launches the actual Chromium build
  instead of checking that the cache folder exists (an existing folder with the
  wrong build killed the gate with the very stacktrace the guard exists to
  prevent). Playwright is pinned to one exact version on both sides.
- **false green** — the server serves `chemdraw_tool/ui/dist/`, not `src/`, so
  the gate rebuilds the bundle and compares bytes. `package-lock.json` is
  versioned to keep that comparison deterministic across machines.

Two frozen renderings guard against silent visual drift, and **neither may be
regenerated to make a diff disappear**:

- `tests/__fixtures__/*.golden.svg` — the Python renderer's default output
  (both paths: UI preview and file export). The input coordinates are frozen in
  `aspirin.coords.json`, so an RDKit *layout* change (rdkit 2026.9 mirrors
  aspirin) no longer turns it red — it measures the renderer only. Regenerate
  only for an intentional rendering change or an RDKit *drawing-code* change,
  and look at the result; never touch the coordinate fixture to do so.
  The layout half is guarded separately: `tests/test_layout_guard.py` pins
  where `generate_2d` puts the atoms for seven probes (direct comparison, so a
  mirror counts). Red there means an RDKit update turns or mirrors what users
  get — look at before/after, then bless deliberately with `UPDATE_LAYOUT=1`
  in the commit that moves the version.
  Playwright's double pin is test-enforced too (`tests/test_dependency_pins.py`).
- `chemdraw_tool/ui/src/utils/__fixtures__/aspirin.expected.png` — the JS
  rasterization, machine-specific, `npm run test:e2e:update` once per machine.

`identitaet.py` is the same idea one step earlier, and it is the only check
on the step that can make everything else *consistently* wrong: if `resolve()`
picks the wrong record, drawing, formula, mass and CAS all agree — for the
wrong substance. `tests/identity/stoffe.json` pins input → InChIKey for 57
entries (plus 3 broken SMILES that must fail as `invalid_smiles`) (German trivial names, IUPAC names, raw SMILES, a salt, `O` for water)
and the runner separates **red** (resolved to something else) from **yellow**
(a source is down, or a documented gap) — a check that goes red because PubChem
hiccups is a check that gets ignored. It paid for itself on the first run:
PubChem answered the metformin SMILES with its `[14C]` record (no CAS), which is
why properties are now fetched by InChIKey. The SMILES route behind it is
opt-in since E12 (`CHEMDRAW_SMILES_LOOKUP`, the bundles' `user_config` checkbox):
by default a typed structure (SMILES, InChI) goes to no database, only its
InChIKey does — `lookup` included. `tests/test_smiles_privacy.py` catches every
`requests` call per tool and goes red on a SMILES or InChI in URL or body.
"Glucose" (like Xylol, Kresol, Toluidin, Butanol) is now pinned as `ambiguous`:
`generate_molecule` returns an isomer picker instead of silently choosing one.

A third frozen set covers the text the model actually reads:
`tests/__snapshots__/tools/*.json` pins each tool's name, description and schemas.
A diff is red on purpose — a reworded description changes which tool the model
picks. Bless it deliberately with `UPDATE_TOOLSNAPS=1 uv run pytest
tests/test_tool_snapshots.py`, in the same commit that changes the text.

## The five tool areas (where a new tool goes)

The model picks a tool from its name and description alone, so a fuzzy boundary
is a precision bug, not cosmetics — "draw aspirin" once landed in
`generate_scope_table` and produced a one-cell grid. Since then the tool set is
a tested promise in `tests/test_server_taxonomy.py`:

| Area | Tools | What belongs here |
|---|---|---|
| Draw | generate_molecule · compare_molecules · batch_generate · generate_reaction · generate_mechanism · generate_scope_table · generate_3d · generate_protein_or_antibody | structures and reactions |
| Lab graphics | generate_spectrum · generate_tlc · generate_titration_curve · generate_species_distribution · generate_calibration_curve · generate_pk_curve · generate_dose_response | measured data as a diagram |
| Look up | lookup · lookup_molecule_data · predict_spectrum | facts about a substance, from a database or derived from its structure |
| Calculate | calculate_solution · calculate_content · calculate_ph · calculate_pharmacokinetics | a number **and** the working behind it |
| Anki | export_anki_deck | flashcard decks |

Outside the areas sits exactly one tool: `save_png`, the server half of the
panel's export button. It stays registered because the UI calls it by name
(`ExportPngButton.jsx`), and its description marks it internal so the model
never calls it on its own — saving a picture is the user's click.

**Adding a tool means picking an area and entering it in the taxonomy test.**
The test fails on an unlisted tool by design. Two more rules keep the set
selectable: any tool confusable with an existing one must carry a
`Not this tool for: … — use X` line naming the alternative (also test-enforced),
and the count has a ceiling that is only ever raised deliberately, with the
reason written into the test (16 → 18 for the calculating area, → 19 for the
calibration curve, → 20 for the spectrum prediction, → 21 for pharmacokinetics, → 23 for the pharmacology curves, → 24 for
`generate_protein_or_antibody`, because Claude Desktop routes on tool names alone before its
tool search: 0 of 8 protein requests reached the server without one).

**Delimit in both directions.** The tool that fails to exclude a case is the
one that wins it. `generate_titration_curve` therefore points at
`calculate_ph` just as much as the other way round — a one-sided fence
reproduces the aspirin misfire with new names.

**A fence does not help against an underspecified prompt.** A bare compound
name ("caffeine") names no tool's job, so it goes to whichever description
sounds most like it — which is why `lookup` used to win it with the sentence
"the right choice whenever the user just asks 'what is X'". The answer is not a
sharper fence but a stated default: `generate_molecule` claims the bare name in
writing, and the server's `instructions=` says so once before any tool
description is read. Both are test-enforced.

Two more rules follow from the same measurements
([research report](https://claude.ai/code/artifact/6fa21f2d-6223-4637-90e1-ad4b1cf99ea7)):

- **Describe, never advertise.** A superlative moves a tool's usage share
  measurably (7.48 : 1 for one appended sales sentence, arXiv:2505.18135)
  *without* improving accuracy — it steals calls from its neighbours. The
  taxonomy test greps for the usual phrases.
- **Stay under 2 KB per description.** Claude Code truncates there, from the
  end. Cut the parameter docs, never a fence.

Prefer a parameter over a new tool when the output is the same kind of thing.
That is why the five text lookups are one `lookup` with a `topic` literal, the
curated decks are a `curated_deck_id` parameter, and the fat characteristics
(acid/saponification/iodine value, Karl Fischer) are `method` values of
`calculate_content` rather than four more tools.

**Prompt → tool is a test, not a story.** `evals/tool-routing/cases.yaml` holds
the cases; `tests/test_eval_cases.py` keeps them in sync with the tool list
without touching the network and goes red when a fence has no case. The scored
run needs an API key — see `evals/README.md`.

## Architecture

```
chemdraw_tool/
├── resolver.py            — parse-first (SMILES wins if it parses: "O" is water,
│                            not O₂), then a 5-step name cascade: OPSIN (offline,
│                            needs Java; degrades gracefully) → PubChem →
│                            PubChem transliterated (ä→ae) → NCI CIR ×2.
│                            Errors carry a `kind`: not_found / offline /
│                            sources_down / partial / invalid_smiles /
│                            ambiguous (family names → isomer picker) / protein
│                            (UniProt entry instead of a structure; enzyme names
│                            checked first) — the message tells the user
│                            what actually helps. generate_molecule adds
│                            too_large (name → over 200 heavy atoms)
├── generator.py           — RDKit 2D coordinates; structure switches: linear
│                            peptides (CoordGen), metal tetrapyrroles (metal in
│                            the ring centre; N–M bonds only via
│                            coordination_drawing, which every renderer calls)
├── image_export.py        — PNG/SVG file rendering (primary output path)
├── svg_renderer.py        — SVG for the embedded UI preview (shared BOND_LINE_WIDTH)
├── render_style.py        — named render profiles (compact/presentation/grayscale)
│                            + group abbreviation; "" always means today's look
├── spectrum.py            — schematic spectra from peak lists (matplotlib → PNG/SVG)
├── tlc.py                 — TLC plates from Rf values (lanes × spots)
├── scope.py               — substrate-scope figures (structure grid + captions)
├── cdxml_writer.py        — RDKit mol → ChemDraw CDXML (optional format)
├── layout.py              — reaction scheme layout (arrows, +, conditions)
├── mechanism*.py          — reaction mechanism definitions/coords/rendering
├── structure3d.py         — 3D conformer for the rotatable viewer
├── protein_catalog.py     — which protein entry: lab-standard table, antibody
│                            table, gene symbols (RecA), organism in the name;
│                            ProteinChoice feeds message, image and data sheet
├── protein_structure.py   — backbone N/Cα/C/O + bound groups (heme, metals,
│                            inhibitors; no water/buffer) from RCSB ModelServer /
│                            PDBe best structure / AlphaFold DB (mmCIF parser)
├── protein_ss.py          — DSSP-style H/E/C when an entry has no HELIX/SHEET
├── protein_view.py        — view rotation (choose_frame) + panel format
│                            (Base64 int16 Cα / int8 O offsets, ~12 chars/residue)
├── protein_render.py      — 2D cartoon PNG/SVG (protein_cartoon.py geometry)
├── igg_scheme.py          — 2D IgG domain scheme for antibody answers
├── databases.py           — PubChem / ChEBI / KEGG / UniProt lookups
├── ph_plots.py            — titration curves + species distribution
├── anki_export.py         — .apkg decks with rendered images
├── curated_decks.py       — bundled starter decks
├── validator.py           — input validation + CDXML round-trip validation
├── solution.py            — weighing, dilution, mixing cross, molar mass
│                            (molmass — it parses hydrates, RDKit cannot)
├── ph_calc.py             — pH/buffer numbers; shares `ph_plots.exact_ph`
│                            with the curve, so figure and number agree
├── calibration.py         — least squares, read-back, LOD/LOQ (ICH Q2: 3,3·s(y)/a)
├── calibration_plot.py    — the calibration figure (reuses ph_plots helpers)
├── spectro.py             — expected IR bands (curated table × SMARTS) and
│                            ¹H signal counts; no ppm shifts on purpose
├── calculator/            — Ph.Eur. content determination + fat characteristics
│                            (titration, photometry, stats incl. Grubbs,
│                            fat_values); pure functions behind calculate_content
├── payloads.py            — Pydantic models for MCP structured output;
│                            each `type` needs a matching case in App.jsx
├── png_writer.py          — client-rendered PNG → file
├── vault.py               — optional notes lookup (only if CHEMDRAW_VAULT_PATH)
├── prompts.py             — MCP prompts (study_compound, practice_mechanism,
│                            exam_flashcards, compare_compounds); mvp tools only
├── privacy.py             — may a typed structure go online? (CHEMDRAW_SMILES_LOOKUP,
│                            default off; read on every call)
├── chemdraw.py            — macOS AppleScript bridge (no tool right now; CDXML
│                            stays available as an output format)
├── desktop_config.py      — Claude Desktop registration (chemdraw-install)
├── doctor.py              — installation diagnosis (chemdraw-doctor)
├── server.py              — MCPServer (mcp 2.x, stdio) + tool definitions;
│                            `_INSTRUCTIONS` is the area map the client may put
│                            in the system prompt — the one place the five
│                            areas are explained once instead of 20 times
└── ui/                    — embedded MCP App UI (React/Vite, served as resource)
```

Pipeline: input (name/SMILES) → resolver → RDKit 2D → image_export (PNG/SVG)
[→ cdxml_writer if requested] → `~/ChemDraw-Output/`

Output formats: `generate_*` tools accept `formats=["png","svg","cdxml"]`,
default `["png","svg"]`. CDXML only on explicit request, and only for actual
structures (a TLC plate or scope figure is not one).

**Adding a panel tool is a five-link chain** — miss one and the panel silently
shows nothing: renderer → payload model with a `type` default → tool with
`meta=_UI_META` → View component + `case` in `ui/src/App.jsx` → rebuild the
bundle. Tests enforce every link (panel tools are derived from the MCPServer
registration, payload types are compared against App.jsx cases in both
directions, the gate checks bundle freshness). Removing one walks the same
chain backwards — and the bundle rebuild is just as mandatory.

**The panel switches between structure and data sheet**, so which of the two
tools the model picked matters less. The two directions cost different things
and are therefore built differently:

- **→ structure is always local.** `MoleculePayload` and `DatabasePayload`
  both carry `atoms` and `functionalGroups` (same types on purpose — both
  views feed the same `StructureCanvas`). RDKit computes them from the mol
  object that is already in hand; no network, no spinner.
- **→ data is fetched on click**, once, then cached, via
  `app.callServerTool({name: "lookup_molecule_data", …})` — the same bridge
  `ExportPngButton` uses. Only successes are cached, so a failure stays
  retryable, and a user who switches back mid-flight keeps their view (a
  `wanted` ref decides, not the arriving response).

**The panel talks to Claude through two channels, both gated on host capabilities (12.11.2026).**
`components/ContinueRow.jsx` sends one user message per click (`app.sendMessage`, only inside the click
handler) and does not render at all without the host capability `message`; its sentences are pure functions in
`utils/followUps.js` and offer only what the server can deliver (a mechanism button needs a carboxylic acid, a
primary/secondary alcohol or a halide on an sp3 carbon). `ModelContext.jsx` is the **single owner** of
`app.updateModelContext`: views only report their text (`utils/modelContext.js`), the provider sends the full
state, debounced, because the host keeps only the last update — a second sender would overwrite the first. A
view that is hidden (parent structure behind the stereo-variant list) must report `""`, and the view that
replaces it must report itself, or the host keeps the stale text. Hover is a preview, a click pins a group or
atom (`pinnedGroup`); hover must never clear the pin. The Study tab (`components/StudyPanel.jsx`, molecule view
only, opt-in) covers name, key facts and groups — nothing in that mode may leak the name (tooltips, `title`,
`aria-label`, file paths). `test:host` switches the capabilities on and off and sends `toolinput` before
`toolresult` (placeholder in `components/ToolPlaceholder.jsx`).

**Tool titles, annotations and prompts live next to the registration.** `_TOOL_LABELS` in `server.py` gives
every tool a human `title` and honest `ToolAnnotations` (a tool that writes under `~/ChemDraw-Output` is not
read-only; `export_anki_deck` is destructive because it updates notes in Anki); a new tool needs an entry, and
`tests/test_tool_annotations.py` lists the writing tools explicitly. `save_png` carries
`_meta.ui.visibility: ["app"]` without a `resourceUri`, so it stays registered and counted but is not a panel
tool. `chemdraw_tool/prompts.py` holds four study prompts; they may name only tools of the `mvp` profile
(`tests/test_prompts.py`).

A component test for an async panel path is worthless outside `act()`: the
follow-up render never flushes and the test passes while the bug is live.
`src/__tests__/harness.mjs` wraps clicks; resolving a deferred promise must be
wrapped too.

Test output paths are redirected with `monkeypatch.setattr` against
`chemdraw_tool.server.<DIR>`. `tests/conftest.py` compares the real
`~/ChemDraw-Output` before and after the suite, so a redirect that points
nowhere fails loudly instead of quietly writing into the user's folder.

**The protein panel carries a 3D engine — and a fallback that must survive.**
`ui/src/protein/cartoonEngine.js` (Mol* 5.13.1, MIT, pinned exactly; notices in
`THIRD_PARTY_LICENSES`) is built by `vite.config.js` into a separate IIFE and
embedded as `<script type="text/plain" id="chem-cartoon-engine">`; only
`protein/loadEngine.js` executes it, when a protein is shown. Measured
10.11.2026: panel file 0.47 → 2.96 MB (0.13 → 0.85 MB gzip), molecule panel
start ~30 → ~55 ms (a plain import cost 210 ms — never import Mol* from the
main bundle). The engine path uses no eval, Worker or blob URL; `test:host`
runs the panel under the ext-apps default CSP. **Fallback rule:** the SVG
backbone trace (`BackboneCanvas`) shows while the engine loads and stays when
it fails (no WebGL, blocked script, engine error) — never an empty area. Both
are tested: `proteinView.test.mjs` (forced failure, fake engine) and
`test:host` (real Mol* in Chromium, plus a run with WebGL removed).
Colours: `ui/src/protein/colors.js` mirrors `protein_render.py` (SS, element
colours) — change both. `ui/src/components/IgGScheme.jsx` redraws
`igg_scheme.py` for the panel with theme variables; a content change to the
scheme belongs in both.

## Conventions

- Python 3.11+, package manager: `uv`
- Tests: pytest, TDD (red first — no production code without a failing test)
- UI preview and exported files must stay visually consistent
  (shared constants like `BOND_LINE_WIDTH`; parity is test-enforced per style)
- New rendering options are opt-in; the default output must not change
- User-facing text (tools, docstrings, README, doctor output) is English;
  code comments and commits are German
- Dependencies: rdkit, lxml, requests, mcp, Pillow, matplotlib, py2opsin,
  genanki, molmass (OPSIN needs a JRE at runtime; without one the resolver
  degrades to PubChem/NCI — never make Java a hard requirement). Weigh every
  new dependency against what it drags in: `molmass` earned its place with
  zero required dependencies of its own, while `chempy`, `pint` and `mendeleev`
  were rejected for pulling in scipy/pandas/sympy-sized trees.
