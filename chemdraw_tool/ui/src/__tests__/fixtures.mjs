// Gemeinsame Testdaten fuer die Panel-Tests. Gekuerzte, aber echte Formen:
// so kommen Molekuel- und Datenblatt-Payload wirklich am Panel an.

export const ATOMS = [
  { idx: 0, el: "C", x: 10, y: 10, hCount: 3, charge: 0 },
  { idx: 1, el: "C", x: 20, y: 10, hCount: 0, charge: 0 },
  { idx: 2, el: "O", x: 30, y: 10, hCount: 0, charge: 0 },
];

export const GROUPS = [
  { name: "Ester", atomIndices: [0, 1, 2], color: "#d35400" },
];

export const SVG = "<svg viewBox='0 0 40 20'><path d='M0 0'/></svg>";

export const MOLECULE = {
  type: "molecule",
  name: "Aspirin",
  subtitle: "2-(Acetyloxy)benzoesäure",
  svg: SVG,
  formula: "C9H8O4",
  properties: { smiles: "CC(=O)Oc1ccccc1C(=O)O", mw: "180.16", cas: "50-78-2" },
  atoms: ATOMS,
  functionalGroups: GROUPS,
};

export const DATABASE = {
  type: "database",
  name: "Aspirin",
  smiles: "CC(=O)Oc1ccccc1C(=O)O",
  molecule_svg: SVG,
  atoms: ATOMS,
  functionalGroups: GROUPS,
  sources: [
    {
      type: "PubChem",
      source: "PubChem",
      url: "https://pubchem.ncbi.nlm.nih.gov/compound/2244",
      rows: [
        { key: "CAS", val: "50-78-2" },
        { key: "InChIKey", val: "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" },
      ],
    },
  ],
};

/** Erfolgsantwort von callServerTool — wie Claude Desktop sie liefert:
 *  structuredContent gestrippt, Payload nur noch als JSON-Textblock. */
export function lookupSuccess(payload = DATABASE) {
  return {
    isError: false,
    content: [{ type: "text", text: JSON.stringify(payload) }],
  };
}

/** Fehlerantwort — die harte SDK-Flagge, wie ExportPngButton sie prueft. */
export function lookupFailure() {
  return {
    isError: true,
    content: [{ type: "text", text: "Fehler: Stoff nicht gefunden" }],
  };
}
