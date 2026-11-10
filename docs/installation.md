# Installation

Pick **one** route — the extension and `chemdraw-install` register the same
connectors, and installing both makes the model see every tool twice.
Afterwards restart Claude Desktop and ask *"draw caffeine"*. The short version
is in the [README](../README.md#installation).

Every route registers two connectors from one installation: `chemdraw`
(profile `mvp`, the default) and `chemdraw-pharma` (profile `full`). Enable one
per chat; switching needs no restart. See [tools.md#profiles](tools.md#profiles).

## 1. Claude Desktop extension (macOS, Linux)

Download `chemdraw-mcp-<version>.mcpb` from the
[latest release](https://github.com/jurimaxam-dotcom/chemdraw-mcp/releases/latest),
double-click it and confirm in Claude Desktop, then restart Claude Desktop once.
`chemdraw-mcp-pharma-<version>.mcpb` from the same release is the second
connector (full profile); install it the same way — both bundles share one
installation on disk, so the second costs no download.
The first start fetches the package from PyPI via [uv](https://docs.astral.sh/uv/),
every file checked against hashes pinned at release time (a missing uv is
downloaded at a fixed version and its SHA-256 verified). That is about 40 MB
and takes a minute; later starts are offline.

If your organization manages Claude Desktop, it may block extensions or allow
only listed ones — then use route 2.

## 2. From PyPI

Needs [uv](https://docs.astral.sh/uv/):

```bash
uv tool install chemdraw-mcp
chemdraw-install
```

`chemdraw-install` adds both Claude Desktop entries (`chemdraw` and
`chemdraw-pharma`) with the absolute path of the installed launcher, backs up
the config first, replaces the single `chemdraw-tool` entry of versions before
0.9.0, leaves other MCP servers untouched and prints what it registered.

## 3. From a clone (to read or change the code)

```bash
git clone https://github.com/jurimaxam-dotcom/chemdraw-mcp.git
cd chemdraw-mcp && ./install.sh
```

`install.sh` installs uv if missing, syncs the dependencies and registers the
server the same way `chemdraw-install` does. For tests and the build see
[development.md](development.md).

## 4. Editing the config by hand

Add this to `claude_desktop_config.json` under `mcpServers` (macOS:
`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
"chemdraw": {
  "command": "/opt/homebrew/bin/uvx",
  "args": ["chemdraw-mcp"],
  "env": {"CHEMDRAW_PROFILE": "mvp"}
},
"chemdraw-pharma": {
  "command": "/opt/homebrew/bin/uvx",
  "args": ["chemdraw-mcp"],
  "env": {"CHEMDRAW_PROFILE": "full"}
}
```

One entry is enough if you only want one profile; `CHEMDRAW_PROFILE` defaults
to `mvp`.

Claude Desktop starts MCP servers with a minimal PATH, not your login shell.
A bare `"uvx"` cannot be found there and the server fails without a message.
Put the absolute path that `which uvx` prints on your machine into `command`.

## Optional extras

- **A Java runtime** (e.g. `brew install openjdk`) lets
  [OPSIN](https://github.com/dan2097/opsin) parse systematic IUPAC names
  offline, including names no database indexes (a trivial name without
  locants is still cross-checked against PubChem when online). Without Java,
  names are resolved online through PubChem and NCI.
- **The AnkiConnect add-on** lets `export_anki_deck` add cards to a running
  Anki. Without it you import the `.apkg` file yourself.
- **ChemDraw** is never required. Request `formats=["cdxml"]` to continue
  editing a structure there.

## Something not working? Run the doctor

```bash
chemdraw-doctor                            # after "uv tool install chemdraw-mcp"
uv run chemdraw-doctor                     # in a clone
uvx --from chemdraw-mcp chemdraw-doctor    # without installing anything
```

It checks the seven things that make the server look dead in the chat or
explain what it sends — RDKit rendering, the Java/OPSIN runtime, the `uv` path,
the Claude Desktop entry, the name databases, the SMILES lookup setting and the
output directory — and prints the command that fixes
each problem. Results are `[OK]`, `[LIMITED]` (works, but restricted), `[FAIL]`
or `[NOTE]` (does not apply). The exit code stays 0 while the server is usable.
With the extension installed, the Claude Desktop check reports `[NOTE]`:
extensions are managed by Claude Desktop and are not listed in its config file.

If the server code or a dependency changed, restart Claude Desktop: it keeps
the server process running, and an old process mixed with new files fails in
confusing ways.
