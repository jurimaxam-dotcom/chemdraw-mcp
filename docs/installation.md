# Installation

Pick **one** route — installing twice registers the server twice and the model
sees every tool doubled. Afterwards restart Claude Desktop and ask
*"draw caffeine"*. The short version is in the
[README](../README.md#installation).

## 1. Claude Desktop extension (macOS, Linux)

Download `chemdraw-mcp-<version>.mcpb` from the
[latest release](https://github.com/jurimaxam-dotcom/chemdraw-mcp/releases/latest),
double-click it and confirm in Claude Desktop, then restart Claude Desktop once.
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

`chemdraw-install` adds the Claude Desktop entry with the absolute path of the
installed launcher, backs up the config first, leaves other MCP servers
untouched and prints what it registered.

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
"chemdraw-tool": {
  "command": "/opt/homebrew/bin/uvx",
  "args": ["chemdraw-mcp"]
}
```

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

It checks the six things that make the server look dead in the chat — RDKit
rendering, the Java/OPSIN runtime, the `uv` path, the Claude Desktop entry, the
name databases and the output directory — and prints the command that fixes
each problem. Results are `[OK]`, `[LIMITED]` (works, but restricted), `[FAIL]`
or `[NOTE]` (does not apply). The exit code stays 0 while the server is usable.
From a PyPI install the `uv` and Claude Desktop checks report `[NOTE]`, because
they belong to the repository installer.

If the server code or a dependency changed, restart Claude Desktop: it keeps
the server process running, and an old process mixed with new files fails in
confusing ways.
