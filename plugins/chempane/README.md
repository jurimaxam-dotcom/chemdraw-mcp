# chempane

chempane (formerly chemdraw-mcp) is a local chemistry MCP server backed by RDKit and Matplotlib. It renders publication-style 2D skeletal structures, rotatable 3D conformers, reaction schemes, curved-arrow mechanisms, lab spectra, TLC plates, titration curves, protein cartoons and Anki study decks directly on your machine.

## Installation

```bash
claude plugin marketplace add chempane/chempane
claude plugin install chempane@chempane
```

Or inside a Claude Code session:

```text
/plugin marketplace add chempane/chempane
/plugin install chempane@chempane
```

## Requirements & what gets downloaded

- [uv](https://docs.astral.sh/uv/) must be installed on your machine (`uvx` available in `PATH`). Apps started from the Dock (Cowork, the desktop app's Code tab) see a shorter `PATH` than a terminal; if the chempane tools do not appear there, check that the app can find `uvx`.
- On first run, `uvx chempane==0.12.0` downloads the pinned `chempane==0.12.0` package and its Python dependencies (such as RDKit, Matplotlib, NumPy and the MCP Python SDK) from PyPI (`pypi.org`, `files.pythonhosted.org`) once into uv's cache (about 480 MB). That first start took 24 s on a fast connection and can take longer on a slow one; if Claude Code marks the server as failed meanwhile, run `/mcp` and choose **Reconnect**. Later starts reuse the cached environment (about 2 s).
- No API key and no commercial ChemDraw licence required.

## Example prompts

1. *"Draw caffeine as a skeletal formula and save PNG and SVG."*
2. *"Show the SN2 mechanism of (R)-2-bromobutane with cyanide, step by step."*
3. *"Draw a titration curve for 25 mL of 0.1 M acetic acid with 0.1 M NaOH and calculate the pH at the equivalence point."*
4. *"Compare aspirin and ibuprofen side by side and highlight the differences."*

## Local files, privacy & network access

- **Local rendering & output:** RDKit and Matplotlib compute and render all 2D/3D structures, spectra, TLC plates, titration curves and pH calculations locally. Exported files (PNG, SVG, optional CDXML, `.apkg`) are written to `~/chempane-output/` (or an existing `~/ChemDraw-Output/`).
- **Declared external hosts:**
  - `pypi.org`, `files.pythonhosted.org` — initial package download via `uvx chempane==0.12.0`.
  - `pubchem.ncbi.nlm.nih.gov`, `cactus.nci.nih.gov` — resolving compound names to structures and fetching properties/GHS safety data.
  - `www.ebi.ac.uk` (ChEBI OLS4, PDBe), `rest.kegg.jp`, `rest.uniprot.org` — biochemical/protein lookups and best-structure mappings.
  - `models.rcsb.org`, `alphafold.ebi.ac.uk` — fetching protein backbone mmCIF files for cartoon rendering.
- **Optional local loopback:** Anki deck push connects to local AnkiConnect (`http://127.0.0.1:8765`) only when you explicitly request Anki delivery.
- **SMILES privacy (server requests):** By default, a typed SMILES or InChI string is **not** sent to those chemistry databases by the server — only its locally computed 27-character InChIKey hash is queried (`CHEMPANE_SMILES_LOOKUP` is off by default). Compound names and lookup queries are sent as typed. Note that your Claude chat client still receives whatever you type in the conversation. See the full [privacy policy](https://github.com/chempane/chempane/blob/main/docs/privacy.md).

## License

Apache-2.0. Unofficial, not affiliated with Revvity.
