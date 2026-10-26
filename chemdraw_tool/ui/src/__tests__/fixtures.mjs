// Gemeinsame Testdaten fuer die Panel-Tests. Gekuerzte, aber echte Formen:
// so kommen Molekuel- und Datenblatt-Payload wirklich am Panel an.

export const ATOMS = [
  { idx: 0, el: "C", x: 10, y: 10, hCount: 3, charge: 0 },
  { idx: 1, el: "C", x: 20, y: 10, hCount: 0, charge: 0 },
  { idx: 2, el: "O", x: 30, y: 10, hCount: 0, charge: 0 },
];

export const GROUPS = [
  { name: "Ester", atomIndices: [0, 1, 2], count: 1, color: "#d35400" },
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

/** Mehrdeutiger Familienname — so, wie generate_molecule ihn beantwortet. */
export const AMBIGUOUS = {
  type: "ambiguous",
  name: "Xylol",
  message: "'Xylol' is ambiguous: it names 3 different compounds. Nothing was drawn.",
  candidates: [
    { label: "o-xylene", name: "1,2-dimethylbenzene", smiles: "Cc1ccccc1C", svg: SVG },
    { label: "m-xylene", name: "1,3-dimethylbenzene", smiles: "Cc1cccc(C)c1", svg: SVG },
    { label: "p-xylene", name: "1,4-dimethylbenzene", smiles: "Cc1ccc(C)cc1", svg: SVG },
  ],
};

/** Datenblatt mit GHS je Quelle (Etappe 5) — Form wie lookup_molecule_data
 *  sie für Koffein liefert, auf zwei Quellen gekürzt. */
export const DATABASE_GHS = {
  ...DATABASE,
  name: "Caffeine",
  sources: [
    DATABASE.sources[0],
    {
      type: "GHS",
      source: "PubChem CID 2519 — Safety",
      url: "https://pubchem.ncbi.nlm.nih.gov/compound/2519#section=Safety-and-Hazards",
      rows: [],
      status: "ok",
      note: "",
      groups: [
        {
          id: "ghs-272",
          source: "EU harmonised classification (CLP, Regulation (EC) No 1272/2008)",
          record_name: "caffeine",
          url: "https://eur-lex.europa.eu/eli/reg/2008/1272/oj",
          lead: true,
          note: "",
          signal: "Warning",
          hazards: [{ code: "H302", text: "Harmful if swallowed", percent: null }],
          pictograms: ["Irritant"],
          p_codes: ["P264", "P270"],
          not_classified: null,
          reports_total: null,
        },
        {
          id: "ghs-51",
          source: "ECHA C&L notifications (company self-classification)",
          record_name: "Caffeine (EC: 200-362-1)",
          url: "",
          lead: false,
          note: "",
          signal: "Warning",
          hazards: [{ code: "H302", text: "Harmful if swallowed", percent: 98.9 }],
          pictograms: ["Irritant"],
          p_codes: [],
          not_classified: { percent: 0.6, reports: 13, total: 2217 },
          reports_total: 2217,
        },
        {
          id: "ghs-262",
          source: "NITE-CMC (Japan)",
          record_name: "caffeine - FY2008",
          url: "",
          lead: false,
          note: "",
          signal: "Danger",
          hazards: [{ code: "H360", text: "May damage fertility or the unborn child", percent: null }],
          pictograms: ["Health Hazard"],
          p_codes: [],
          not_classified: null,
          reports_total: null,
        },
      ],
    },
  ],
};

/** GHS-Reiter, wenn der Abruf scheiterte. */
export const DATABASE_GHS_FAILED = {
  ...DATABASE,
  sources: [
    DATABASE.sources[0],
    {
      type: "GHS",
      source: "PubChem CID 2244 — Safety",
      url: "https://pubchem.ncbi.nlm.nih.gov/compound/2244#section=Safety-and-Hazards",
      rows: [],
      groups: [],
      status: "error",
      note: "GHS data could not be retrieved from PubChem (network or service error).",
    },
  ],
};
