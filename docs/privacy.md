# Privacy: what leaves your machine

What the server sends to which online service for each kind of input, what
stays local, what the log records and how to check the setting. The short
version is in the [README](../README.md#what-leaves-your-machine); the
reference wording is in [tools.md](tools.md#what-leaves-your-machine).

## The rule

Drawing is local: RDKit parses, lays out and renders every structure on your
computer. Online databases are asked for names and data. A structure you type
(SMILES, InChI) is **not sent** to any database by default; only its InChIKey
is.

## Input → where it goes

| What you give | Where it goes (default) |
|---|---|
| A SMILES or InChI, also with a label (`CCO batch 7`) or with group abbreviations (`Ph`, `Boc`) | Nowhere as written. Its InChIKey goes to PubChem for name, CAS number, properties and GHS. |
| A peptide sequence (`Ala-Trp-Lys-Ser-Gly`, `peptide:YGGFM`) | Built locally; its InChIKey goes to PubChem like any structure. |
| A compound name ("caffeine", "Koffein") | PubChem and NCI CIR, in several spellings; enzyme-like names and names no structure database knows also to UniProt. With Java, OPSIN reads systematic names offline; a name without locants is still cross-checked against PubChem. |
| A fixed name ("heme b", "hemin") | Resolved locally to a fixed structure; its InChIKey goes to PubChem. |
| A protein, enzyme or antibody name, a gene symbol (`RecA`) | UniProt. The UniProt accession then goes to PDBe (best structure) and the AlphaFold DB, the PDB ID to the RCSB ModelServer, which returns the structure file (backbone atoms and bound groups). Names in the curated table (lysozyme, trypsin, trastuzumab …) skip the search and fetch the structure by its PDB ID. |
| `lookup` with a name | PubChem, ChEBI, UniProt or KEGG, depending on the topic, as typed. A bare run of up to five letters (`PC`, `NOS`, `RecA`) counts as a name here. |
| `lookup` with a structure | Its InChIKey to PubChem; then PubChem's name for that record to the source of the topic (for `biochem` with the aspirin SMILES: "Aspirin" to UniProt and ChEBI). |
| The panel's **Data** button | The InChIKey of the drawn structure to PubChem. |
| Species of a reaction, substrates of a mechanism, the structure of `generate_3d`, `predict_spectrum` or an Anki card | A name is resolved as above (PubChem asked for the structure by name); a SMILES itself is not sent. For the substrates of a mechanism, the InChIKey goes to PubChem to fetch the compound's name. A protein name in `generate_3d` fetches the structure as above. |
| Spectra, TLC plates, titration curves, `calculate_ph` | Nothing. Computed and drawn locally. |
| Anki delivery | The `.apkg` file stays on your computer. With AnkiConnect the deck goes to the Anki running on your own computer (`http://127.0.0.1:8765`), and only when you ask for it. |

An input that looks like a SMILES but cannot be read is refused with what was
not read, and nothing is sent. **Anything else RDKit cannot read is treated as
a compound name and sent like one**, including `MeOH`, `Et3N` or `Boc2O`.

A systematic IUPAC name describes a structure as exactly as a SMILES does. For
an unpublished compound, pass the SMILES, not the name.

## What an InChIKey reveals

The InChIKey is a 27-character hash computed on your machine from the
structure (for aspirin `BSYNRYMUTXBXSQ-UHFFFAOYSA-N`). The structure cannot be
computed back from it. It only matches a record PubChem already holds; anyone
who already has the structure can compute the same key and recognise it. When
PubChem has no record for the key, the CAS number, logP, TPSA and H-bond counts
stay empty, formula and molar mass are computed locally, and the result says
why.

## Opt-in: look up by SMILES

When PubChem does not know the InChIKey, you can let the server send the SMILES
itself:

- **Claude Desktop extension:** Settings → Extensions → ChemDraw MCP → turn on
  **Look up typed structures by SMILES** (both bundles have it).
- **Everywhere else:** set `CHEMDRAW_SMILES_LOOKUP=1` in the server's
  environment (`true`, `yes` and `on` work too) and restart the server.

With it on, a structure whose InChIKey PubChem does not know is posted to
PubChem as SMILES, and `lookup` passes a typed SMILES as written to PubChem,
ChEBI, UniProt or KEGG. Leave it off for unpublished structures.

## Logs

The server keeps `~/ChemDraw-Output/server.log` on your computer, rotated at
1 MB with two older files. At the default level it records start-up, requests
and errors, and a name when its lookup needed a second attempt or failed. With
`CHEMDRAW_LOG_LEVEL=DEBUG` it records every lookup URL and therefore every name
you asked for. Nothing in the log is sent anywhere.

## How to check

1. Run `chemdraw-doctor`. Its "SMILES lookup" line says "SMILES lookup: off — a
   structure you type (SMILES, InChI) is not sent to any database by this
   server; only its InChIKey is." The doctor sees only its own environment.
2. For the server Claude Desktop runs, open `~/ChemDraw-Output/server.log`: at
   start-up it writes "SMILES lookup: off" or "on".

## Limits

- Most names go online. Offline are only systematic names OPSIN reads with
  locants (Java needed), peptide sequences and a few fixed names such as
  heme b, hemin and the elements ("oxygen" is O₂).
- Your prompt itself goes to Anthropic as part of the chat; this page covers
  only what the chemdraw-mcp server sends.
- The data services have their own logs and terms; the server sends no
  account or key.
