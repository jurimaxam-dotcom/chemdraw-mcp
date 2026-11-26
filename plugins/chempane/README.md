# chempane

chempane draws publication-style 2D chemical structures directly inside Claude. The plugin connects to the hosted read-only MCP server at `https://mcp.chempane.com/mcp`, backed by RDKit, and renders interactive skeletal structures with highlighted functional groups, molecular formula, molar mass, projection views (all-H, Fischer, Haworth, chair) and a Study mode.

## Installation

Add the plugin in Claude via **Customize → Plugins**, or install it from the marketplace in Claude Code:

```bash
claude plugin marketplace add chempane/chempane
claude plugin install chempane@chempane
```

Or inside a Claude Code session:

```text
/plugin marketplace add chempane/chempane
/plugin install chempane@chempane
```

No local Python setup, no sign-in and no API key required.

## Example prompts

1. *"Draw caffeine as a skeletal formula."*
2. *"Draw aspirin and highlight its ester group."*
3. *"Draw lactic acid from this SMILES string: C[C@@H](O)C(=O)O"*
4. *"Show glucose as a Haworth projection."*

## Data flow & privacy

- **Remote endpoint:** The plugin connects to `https://mcp.chempane.com/mcp` (hosted on Fly.io in Frankfurt, Germany, and reached through Cloudflare as a reverse proxy). It is read-only and writes no files on your computer.
- **What is sent:** Only the tool call arguments (the compound name or SMILES string, an optional label and display options). It never receives your conversation, your files or your account details.
- **Typed structures stay on the server:** A SMILES or InChI string you provide is parsed, laid out and rendered in memory on the server and sent to no external database.
- **Compound names:** If a compound name cannot be resolved offline, the name is sent to `pubchem.ncbi.nlm.nih.gov` (PubChem, U.S. NIH) and `cactus.nci.nih.gov` (NCI Chemical Identifier Resolver) to look up its structure.
- **No storage, no tracking:** The server keeps no database, no user accounts, no cookies and no drawing history. Full details: [privacy policy](https://mcp.chempane.com/privacy).

## License

Apache-2.0. Unofficial open-source project, not affiliated with Revvity (ChemDraw) or Anthropic.

## Support and service terms

See the [connector guide](https://github.com/chempane/chempane/blob/main/docs/remote-connector.md) for setup and examples. Report issues through [project support](https://github.com/chempane/chempane/issues). The [terms of use](https://github.com/chempane/chempane/blob/main/docs/remote-terms.md) apply to the hosted service.
