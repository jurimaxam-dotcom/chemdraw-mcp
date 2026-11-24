# chempane

chempane (formerly chemdraw-mcp) is a local chemistry MCP server backed by RDKit and Matplotlib. It renders publication-style 2D skeletal structures, rotatable 3D conformers, reaction schemes, curved-arrow mechanisms, lab spectra, TLC plates, titration curves, protein cartoons and Anki study decks directly on your machine.

## Installation

```text
/plugin install chempane --marketplace chempane/chempane
```

## Requirements

- [uv](https://docs.astral.sh/uv/) (`uvx` downloads the pinned `chempane==0.12.0` package and its Python dependencies such as RDKit and Matplotlib from PyPI on first run).
- No API key and no commercial ChemDraw licence required.

## Example prompts

1. *"Draw caffeine as a skeletal formula and save PNG and SVG."*
2. *"Show the SN2 mechanism of (R)-2-bromobutane with cyanide, step by step."*
3. *"Draw a titration curve for 25 mL of 0.1 M acetic acid with 0.1 M NaOH and calculate the pH at the equivalence point."*
4. *"Compare aspirin and ibuprofen side by side and highlight the differences."*

## Privacy & network access

RDKit renders all structures locally. For database lookups, the server contacts public chemistry APIs (PubChem, ChEBI, KEGG, UniProt, NCI CIR, RCSB PDB / PDBe, AlphaFold DB). By default, a typed SMILES string is not sent to those databases — only its InChIKey hash is queried (your chat client still receives what you type in the conversation). See the full [privacy policy](https://github.com/chempane/chempane/blob/main/docs/privacy.md).

## License

Apache-2.0. Unofficial, not affiliated with Revvity.
