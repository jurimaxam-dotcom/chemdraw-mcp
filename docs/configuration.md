# Configuration

The two profiles, the environment variables the server reads, the setting in
the Claude Desktop extension, and where the server keeps files.

## Profiles

| Profile | Connector in Claude Desktop | Tools | Contents |
|---|---|---|---|
| `mvp` (default) | `chemdraw` | 17, 13 with a panel | drawing, lab graphics, lookup, `calculate_ph`, Anki |
| `full` | `chemdraw-pharma` | 24, 17 with a panel | adds the substrate-scope figure, calibration curve, pharmacokinetic and dose-response curves, and calculators for solutions, content determination and pharmacokinetics |

Both connectors come from one installation: the extension route ships two
bundles (`chemdraw-mcp-<version>.mcpb` and `chemdraw-mcp-pharma-<version>.mcpb`),
and `chemdraw-install` writes both entries. **Enable one connector per chat**
in the connector menu; with both on, the model sees the default tools twice.
Switching needs no restart. What the `full` profile adds:
[tools.md](tools.md#profiles) and [Lab graphics](lab-graphics.md#only-in-the-full-profile).

Outside Claude Desktop, or in a config you write by hand, the profile is the
environment variable `CHEMDRAW_PROFILE`:

```bash
uv run chemdraw-tool-server                         # mvp, the default
CHEMDRAW_PROFILE=full uv run chemdraw-tool-server   # all 24 tools
```

An unknown profile name stops the server at start-up with an error.

## Environment variables

| Variable | Values | Effect |
|---|---|---|
| `CHEMDRAW_PROFILE` | `mvp` (default), `full` | which tools are registered |
| `CHEMDRAW_SMILES_LOOKUP` | `1`, `true`, `yes`, `on`; anything else is off | also send a typed SMILES to PubChem and `lookup` sources ([Privacy](privacy.md#opt-in-look-up-by-smiles)) |
| `CHEMDRAW_LOG_LEVEL` | a Python log level, e.g. `DEBUG`; default `INFO` | `DEBUG` writes every lookup URL, and so every name, to the log |
| `CHEMDRAW_VAULT_PATH` | a folder of Markdown notes | `full` profile only: adds the two tools `search_vault` and `read_vault_entry` for your own notes |

Restart the server after changing one; Claude Desktop keeps it running.

## Claude Desktop extension settings

Settings → Extensions → ChemDraw MCP has one setting, **Look up typed
structures by SMILES** (off by default). It sets `CHEMDRAW_SMILES_LOOKUP` for
the server. Both bundles have it.

## Files and folders

| What | Where |
|---|---|
| Drawings, decks, conformers | `~/ChemDraw-Output/` (fixed; subfolders in [Getting started](getting-started.md#where-the-files-go)) |
| Server log | `~/ChemDraw-Output/server.log`, rotated at 1 MB, two older files kept |
| Extension installation | `~/.local/share/chemdraw-mcp-bundle/` (or under `$XDG_DATA_HOME`), one `env-<version>` folder per version; a version not started for 30 days is removed |
| Claude Desktop config (routes 2 and 3) | macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`; Linux: `~/.config/Claude/claude_desktop_config.json`; a `.bak` copy is written before the first change |

## A config entry by hand

Claude Desktop starts MCP servers with a minimal PATH, so `command` must be an
absolute path (`which uvx` prints it):

```json
"chemdraw": {
  "command": "/opt/homebrew/bin/uvx",
  "args": ["chemdraw-mcp"],
  "env": {"CHEMDRAW_PROFILE": "mvp"}
}
```

More in [installation.md](installation.md#4-editing-the-config-by-hand).

## Limits

- There is no setting for the output folder.
- The profile is fixed per server process; the two connectors are two
  processes.
- The vault tools exist only in the `full` profile and only with
  `CHEMDRAW_VAULT_PATH` set.
