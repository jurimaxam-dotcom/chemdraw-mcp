// Datenblatt aus lookup_molecule_data als Molekül-Payload (Etappe 3, 16.11.2026):
// DatabaseView zeigt dieselbe Molekül-Ansicht mit offenem Data-Reiter. Formel,
// Molmasse, CAS und CID hat das DatabasePayload nicht als Felder (das Ausgabeschema
// ist per Tool-Schnappschuss eingefroren), sondern als Zeilen der PubChem-Quelle.
// Der Server schreibt „CAS No.“, ältere Payloads und Fixtures „CAS“.

const KEYS = {
  formula: /^molecular formula$/i,
  mw: /^(molar mass|molecular weight)$/i,
  cas: /^cas( no\.?)?$/i,
  cid: /^cid$/i,
};

function pubchemRows(sources) {
  const pubchem = (sources || []).find((s) => (s.type || "") === "PubChem");
  return pubchem?.rows || [];
}

export function databaseAsMolecule(data) {
  const rows = pubchemRows(data.sources);
  const pick = (re) => rows.find((r) => re.test(String(r.key || "").trim()))?.val ?? undefined;
  const properties = { smiles: data.smiles || undefined };
  for (const [field, re] of Object.entries(KEYS)) properties[field] = pick(re);
  return {
    type: "molecule",
    name: data.name || "",
    smiles: data.smiles || "",
    svg: data.molecule_svg || "",
    atoms: data.atoms || [],
    functionalGroups: data.functionalGroups || [],
    stereoWarnings: data.stereoWarnings || [],
    stereoNote: data.stereoNote || "",
    foundAs: data.foundAs || "",
    formula: properties.formula,
    properties,
    files: {},
  };
}
