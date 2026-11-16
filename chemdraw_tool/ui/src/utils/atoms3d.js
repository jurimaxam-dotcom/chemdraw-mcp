// Summenformel und Molmasse aus den Atomen eines 3D-Konformers (Etappe 5, 16.11.2026).
// generate_3d liefert keine Formel, aber jedes Atom einzeln — mit expliziten H, also
// vollständig. Ladungen trägt die Atomliste nicht: die Formel ist die des Gerüsts.

// Standard-Atomgewichte (IUPAC, konventionelle Werte). Ein Element, das hier fehlt, ergibt
// keine Masse statt einer falschen.
const WEIGHT = {
  H: 1.008, Li: 6.94, B: 10.81, C: 12.011, N: 14.007, O: 15.999, F: 18.998, Na: 22.99, Mg: 24.305,
  Al: 26.982, Si: 28.085, P: 30.974, S: 32.06, Cl: 35.45, K: 39.098, Ca: 40.078, Mn: 54.938,
  Fe: 55.845, Co: 58.933, Ni: 58.693, Cu: 63.546, Zn: 65.38, As: 74.922, Se: 78.971, Br: 79.904,
  Ag: 107.868, Sn: 118.71, I: 126.904, Ba: 137.327, Pt: 195.084, Au: 196.967, Hg: 200.592,
  Pb: 207.2, Bi: 208.98,
};

function counts(atoms) {
  const n = {};
  for (const a of atoms || []) if (a?.symbol) n[a.symbol] = (n[a.symbol] || 0) + 1;
  return n;
}

/** Hill-Reihenfolge: C, dann H, dann alphabetisch; ohne C alles alphabetisch. */
export function formulaOfAtoms(atoms) {
  const n = counts(atoms);
  const symbols = Object.keys(n).sort();
  const order = n.C ? ["C", ...(n.H ? ["H"] : []), ...symbols.filter((s) => s !== "C" && s !== "H")] : symbols;
  return order.map((s) => s + (n[s] > 1 ? n[s] : "")).join("");
}

/** Molmasse in g/mol, oder null bei einem Element ohne Eintrag. */
export function massOfAtoms(atoms) {
  const n = counts(atoms);
  let m = 0;
  for (const [s, k] of Object.entries(n)) {
    if (!(s in WEIGHT)) return null;
    m += WEIGHT[s] * k;
  }
  return Object.keys(n).length ? m : null;
}
