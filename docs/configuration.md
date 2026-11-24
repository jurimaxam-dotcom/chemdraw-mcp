# Configuration

The three profiles, the environment variables the server reads, the setting in
the Claude Desktop extension, and where the server keeps files.

## Profiles

| Profile | Connector in Claude Desktop | Tools | Contents |
|---|---|---|---|
| `mvp` (default) | `chempane` | 18, 13 with a panel | drawing, lab graphics, lookup, `calculate_ph`, Anki |
| `pharma` | `chempane-pharma` | 9, 4 with a panel | the substrate-scope figure, calibration curve, pharmacokinetic and dose-response curves, and calculators for solutions, content determination and pharmacokinetics — only what `full` adds to `mvp` — plus the panel's two internal helpers |
| `full` | none (by hand) | 25, 17 with a panel | everything: `mvp` and `pharma` in one server |

Both connectors come from one installation: the extension route ships two
bundles (`chemdraw-mcp-<version>.mcpb` and `chemdraw-mcp-pharma-<version>.mcpb`),
and `chempane-install` writes both entries. **Both can be on at once**: they
complement each other, and the model sees every tool once. Turning one on or
off needs no restart. Up to 0.10.0, `chemdraw-pharma` started with `full`; if
you used only that connector, enable `chempane` as well, or set
`CHEMPANE_PROFILE=full` in an entry of your own. Re-running the installer
migrates an old `chemdraw-pharma` entry; `chempane-doctor` points it out.
What the seven extra tools do: [tools.md](tools.md#profiles) and
[Lab graphics](lab-graphics.md#only-in-the-full-profile).

Outside Claude Desktop, or in a config you write by hand, the profile is the
environment variable `CHEMPANE_PROFILE`:

```bash
uv run chempane                         # mvp, the default
CHEMPANE_PROFILE=pharma uv run chempane # the seven extra tools
CHEMPANE_PROFILE=full uv run chempane   # all 25 tools
```

An unknown profile name stops the server at start-up with an error.

## Upgrading from chemdraw-mcp

`pip install -U chemdraw-mcp`, `uv tool upgrade chemdraw-mcp` and `uvx chemdraw-mcp` keep working through a compatibility package. The four old commands and `CHEMDRAW_*` variables remain supported until 1.0; `CHEMPANE_*` takes precedence. Run `chempane-install` to migrate the connector names, then restart Desktop and check the new connectors' tool permissions. Your environment settings are kept and a `.vor-chempane.bak` backup is written.

New installations use `~/chempane-output`. If `~/ChemDraw-Output` exists and the new folder does not, the old folder stays in use; no files are moved. The bundle filenames and Anki deck/model identities stay unchanged.

## Environment variables

| Variable | Values | Effect |
|---|---|---|
| `CHEMPANE_PROFILE` | `mvp` (default), `pharma`, `full` | which tools are registered |
| `CHEMPANE_SMILES_LOOKUP` | `1`, `true`, `yes`, `on`; anything else is off | also send a typed SMILES to PubChem and `lookup` sources ([Privacy](privacy.md#opt-in-look-up-by-smiles)) |
| `CHEMPANE_LOG_LEVEL` | a Python log level, e.g. `DEBUG`; default `INFO` | `DEBUG` writes every lookup URL, and so every name, to the log |
| `CHEMPANE_VAULT_PATH` | a folder of Markdown notes | `pharma` and `full` profiles only: adds the two tools `search_vault` and `read_vault_entry` for your own notes |

Restart the server after changing one; Claude Desktop keeps it running.

## Claude Desktop extension settings

Settings → Extensions → chempane has one setting, **Look up typed
structures by SMILES** (off by default). It sets `CHEMPANE_SMILES_LOOKUP` for
the server. Both bundles have it.

## Files and folders

| What | Where |
|---|---|
| Drawings, decks, conformers | `~/chempane-output/` (existing `~/ChemDraw-Output/` stays in use; subfolders in [Getting started](getting-started.md#where-the-files-go)) |
| Server log | `~/chempane-output/server.log`, rotated at 1 MB, two older files kept |
| Extension installation | `~/.local/share/chemdraw-mcp-bundle/` (or under `$XDG_DATA_HOME`), one `env-<version>` folder per version; a version not started for 30 days is removed |
| Claude Desktop config (routes 2 and 3) | macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`; Linux: `~/.config/Claude/claude_desktop_config.json`; a `.bak` copy is written before the first change |

## A config entry by hand

Claude Desktop starts MCP servers with a minimal PATH, so `command` must be an
absolute path (`which uvx` prints it):

```json
"chempane": {
  "command": "/opt/homebrew/bin/uvx",
  "args": ["chempane"],
  "env": {"CHEMPANE_PROFILE": "mvp"}
}
```

More in [installation.md](installation.md#4-editing-the-config-by-hand).

## Limits

- There is no setting for the output folder.
- The profile is fixed per server process; the two connectors are two
  processes.
- The vault tools exist only in the `pharma` and `full` profiles and only with
  `CHEMPANE_VAULT_PATH` set.
