// Farben des Protein-Panels — dieselben Werte wie die Datei
// (chemdraw_tool/protein_render.py: SS_COLOR, Kettenfarben vom Server).
export const SS_COLOR = { H: "#c8423b", E: "#d99a00", C: "#9da3ab" };
export const SS_NAME = { H: "α-helix", E: "β-strand", C: "loop" };
// AlphaFold-Konfidenzfarben (AlphaFold DB): Klasse 4 >90 … 1 <50
export const PLDDT_COLOR = { 4: "#0053D6", 3: "#65CBF3", 2: "#FFDB13", 1: "#FF7D45" };
export const PLDDT_NAME = { 4: "pLDDT > 90", 3: "70–90", 2: "50–70", 1: "< 50" };
// Elementfarben der Liganden (CPK-artig, Kohlenstoff grau)
export const ELEMENT_COLOR = {
  C: "#8c8c8c", N: "#3050f8", O: "#e8212b", S: "#e6c619", P: "#ff8000", Fe: "#e06633", Zn: "#7d80b0",
  Cu: "#c88033", Mg: "#4fb83a", Ca: "#3dbf3d", Mn: "#9c7ac7", Co: "#f090a0", Ni: "#50d050",
  Na: "#ab5cf2", K: "#8f40d4", Cl: "#1fbf1f", Br: "#a62929", I: "#940094", F: "#7fc94a", Se: "#ffa100",
};

/** Regenbogen N→C (blau → rot) für t in [0, 1]. */
export function rainbow(t) {
  const h = 240 - 240 * Math.max(0, Math.min(1, t));
  const s = 0.72, l = 0.5;
  const f = (n) => {
    const k = (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    return Math.round(255 * (l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))));
  };
  return "#" + [f(0), f(8), f(4)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

/**
 * Farbe je Rest: f(segment, index) → "#hex". Regenbogen läuft je Kette von
 * N nach C (über alle Segmente der Kette).
 */
export function residueColorer(segs, mode) {
  const lengths = new Map();
  for (const s of segs) lengths.set(s.chain.id, (lengths.get(s.chain.id) || 0) + s.ss.length);
  const offset = new Map();
  const start = new WeakMap();
  for (const s of segs) {
    start.set(s, offset.get(s.chain.id) || 0);
    offset.set(s.chain.id, (offset.get(s.chain.id) || 0) + s.ss.length);
  }
  return (seg, i) => {
    if (mode === "chain") return seg.chain.color || SS_COLOR.C;
    if (mode === "plddt") return PLDDT_COLOR[seg.q[i]] || SS_COLOR.C;
    if (mode === "rainbow") return rainbow((start.get(seg) + i) / Math.max(1, lengths.get(seg.chain.id) - 1));
    return SS_COLOR[seg.ss[i]] || SS_COLOR.C;
  };
}
