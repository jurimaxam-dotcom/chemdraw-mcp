// Funktionelle Gruppen fuers Panel: was der Glow verbindet und wie die
// Gruppe unter den Chips heisst (Name + Kurzformel). Ein Erklaersatz ist
// bewusst weggelassen (Jay, 15.10.2026): er waere fuer jeden Stoff derselbe.
//
// Der Server liefert Gruppennamen auf Deutsch ("Carbonsäure") und keine
// Bindungen, nur Atomkoordinaten. Beides wird hier im Panel aufgeloest, damit
// das Payload-Format unveraendert bleibt.

// RDKit zeichnet alle Bindungen gleich lang. Zwei Atome im 120°-Winkel liegen
// ~1.73 Bindungslaengen auseinander — 1.25 trennt Bindung von Nachbarschaft.
const BOND_FACTOR = 1.25;

/** Paare von Gruppenatomen, die im Bild durch eine Bindung verbunden sind. */
export function groupBonds(atoms, atomIndices) {
  if (!atoms?.length || !atomIndices?.length) return [];
  let shortest = Infinity;
  for (let i = 0; i < atoms.length; i++) {
    for (let j = i + 1; j < atoms.length; j++) {
      const d = Math.hypot(atoms[i].x - atoms[j].x, atoms[i].y - atoms[j].y);
      if (d > 0 && d < shortest) shortest = d;
    }
  }
  if (!Number.isFinite(shortest)) return [];
  const wanted = new Set(atomIndices);
  const members = atoms.filter((a) => wanted.has(a.idx));
  const bonds = [];
  for (let i = 0; i < members.length; i++) {
    for (let j = i + 1; j < members.length; j++) {
      const a = members[i];
      const b = members[j];
      if (Math.hypot(a.x - b.x, a.y - b.y) <= shortest * BOND_FACTOR) bonds.push([a, b]);
    }
  }
  return bonds;
}

// Schluessel = Name aus svg_renderer._FUNCTIONAL_GROUPS (plus "Aromat").
const GROUPS = {
  "Carbonsäure": ["Carboxylic acid", "–COOH"],
  "Ester": ["Ester", "–COO–"],
  "Keton": ["Ketone", "C–CO–C"],
  "Aldehyd": ["Aldehyde", "–CHO"],
  "Nitro": ["Nitro group", "–NO₂"],
  "Ether": ["Ether", "C–O–C"],
  "Amid": ["Amide", "–CO–N<"],
  "Sulfonamid": ["Sulfonamide", "–SO₂–N<"],
  "Prim. Amin": ["Primary amine", "–NH₂"],
  "Sek. Amin": ["Secondary amine", "–NH–"],
  "Tert. Amin": ["Tertiary amine", "–N<"],
  "Hydroxyl": ["Alcohol", "–OH"],
  "Phenol": ["Phenol", "Ar–OH"],
  "Thiol": ["Thiol", "–SH"],
  "Halogenid": ["Halide", "C–X"],
  "Phosphat": ["Phosphate", "–PO(OH)₂"],
  "Aromat": ["Aromatic ring", "C₆"],
};

/** Anzeigename und Kurzformel zu einem Gruppennamen des Servers. */
export function groupInfo(name) {
  const entry = GROUPS[name];
  if (!entry) return { label: name ?? "", formula: "" };
  const [label, formula] = entry;
  return { label, formula };
}
