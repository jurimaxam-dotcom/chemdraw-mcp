# chempane as a connector in Claude

The hosted chempane connector draws chemical structures inside a Claude conversation. It needs no
installation, no account and no API key. For the local server with all tools, see the
[README](../README.md).

## Add it

In Claude, open **Settings → Connectors**, choose **Add custom connector** and enter

```text
https://mcp.chempane.com/mcp
```

No sign-in is required. Once chempane is listed in the Claude directory you can add it from there
instead.

## Use it

Ask for a structure in your own words:

- `Draw caffeine.`
- `Draw aspirin and show me its ester group.`
- `Draw lactic acid from this SMILES string: C[C@@H](O)C(=O)O`
- `Show glucose as a Haworth projection.`

Claude calls the tool **Draw a structure** and shows a panel with the 2D structure, molecular formula
and molar mass. Select a functional-group chip to highlight the group in the drawing. The **Study** tab
hides the name so you can quiz yourself, and the buttons under the structure continue the conversation.

## What it does and does not do

- One tool, read-only: it draws one compound per call and writes no files.
- Compound names should be English or IUPAC; Claude translates other languages before calling.
- Structures above 200 heavy atoms are refused.
- The hosted connector has no 3D viewer, reactions, lab graphics, calculations or Anki export yet.
  Those are in the local server.

## Limits

The server is a free community service. It limits requests per minute and per day; when a limit is
reached it answers with an error and Claude tells you to try again later.

## Privacy

What the server receives, sends on and stores is described at
<https://mcp.chempane.com/privacy>. In short: a structure you type is sent to no other service, a
compound name may be looked up at PubChem and the NCI Chemical Identifier Resolver, and nothing you
draw is stored.

## Unofficial

chempane is an open-source project (Apache-2.0). It is not affiliated with Revvity, the maker of
ChemDraw, or with Anthropic.
