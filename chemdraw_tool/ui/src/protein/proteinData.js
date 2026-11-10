// Panel-Daten eines Proteins (E13) → Koordinaten und ein minimales mmCIF.
// Format (Server: chemdraw_tool/protein_view.py): je Segment `ca` = Base64 aus
// int16 LE in 0,1 Å, `o` = Base64 aus int8 (O − Cα) in 0,1 Å, `ss` H/E/C je Rest,
// `q` pLDDT-Klasse 1–4; Liganden `e` (Elemente) + `xyz` wie `ca`.
// Das mmCIF füttert die Cartoon-Engine: _atom_site (CA + O je Rest, HETATM der
// Liganden) plus _struct_conf/_struct_sheet_range aus `ss` — die Engine rechnet
// so keine eigene Sekundärstruktur und zeigt dieselbe wie die Datei.

function bytes(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

/** Base64 int16 LE (0,1 Å) → [[x, y, z], …] in Å. */
export function decodeXyz(b64) {
  if (!b64) return [];
  const u = bytes(b64);
  const v = new DataView(u.buffer);
  const out = [];
  for (let i = 0; i + 5 < u.length; i += 6) {
    out.push([v.getInt16(i, true) / 10, v.getInt16(i + 2, true) / 10, v.getInt16(i + 4, true) / 10]);
  }
  return out;
}

/** Base64 int8 Abstände (0,1 Å) → [[dx, dy, dz] | null, …]; 0,0,0 = fehlt. */
export function decodeOffsets(b64) {
  if (!b64) return [];
  const u = bytes(b64);
  const out = [];
  for (let i = 0; i + 2 < u.length; i += 3) {
    const d = [0, 1, 2].map((k) => ((u[i + k] << 24) >> 24) / 10);
    out.push(d[0] === 0 && d[1] === 0 && d[2] === 0 ? null : d);
  }
  return out;
}

/** Segmente mit decodierten Punkten: {chain, ci, ca, o, ss, q}. */
export function decodeChains(chains = []) {
  const out = [];
  chains.forEach((chain, ci) => {
    for (const seg of chain.segments || []) {
      const ca = seg.ca ? decodeXyz(seg.ca) : legacy(seg.c);
      const off = decodeOffsets(seg.o);
      const o = ca.map((p, i) => (off[i] ? [p[0] + off[i][0], p[1] + off[i][1], p[2] + off[i][2]] : null));
      out.push({ chain, ci, ca, o, ss: seg.ss || "", q: seg.q || "" });
    }
  });
  return out;
}

// Altes Textformat (E8: "x y z …" in 0,1 Å) — nur noch für alte Antworten im Verlauf.
function legacy(c) {
  if (!c) return [];
  const v = c.trim().split(/\s+/).map(Number);
  const out = [];
  for (let i = 0; i + 2 < v.length; i += 3) out.push([v[i] / 10, v[i + 1] / 10, v[i + 2] / 10]);
  return out;
}

export function decodeLigands(ligands = []) {
  return ligands.map((l) => ({ ...l, elements: (l.e || "").split(/\s+/).filter(Boolean), xyz: decodeXyz(l.xyz) }));
}

const f3 = (v) => v.toFixed(2);
const PLDDT_B = { 4: 95, 3: 80, 2: 60, 1: 40 };

/**
 * Reste in Engine-Nummerierung: je Kette fortlaufende label_seq_id, zwischen
 * zwei Segmenten derselben Kette ein Sprung um 10 — so läuft kein Band über
 * die Lücke. Liefert die Segmente mit `seq0` (erste Nummer).
 */
export function layout(protein) {
  const segs = decodeChains(protein.chains);
  const lastSeq = new Map();
  for (const seg of segs) {
    const asym = seg.chain.id;
    seg.seq0 = lastSeq.has(asym) ? lastSeq.get(asym) + 10 : 1;
    lastSeq.set(asym, seg.seq0 + seg.ca.length - 1);
  }
  return segs;
}

function atomSite(rows) {
  return [
    "loop_",
    "_atom_site.group_PDB",
    "_atom_site.id",
    "_atom_site.type_symbol",
    "_atom_site.label_atom_id",
    "_atom_site.label_comp_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_entity_id",
    "_atom_site.label_seq_id",
    "_atom_site.Cartn_x",
    "_atom_site.Cartn_y",
    "_atom_site.Cartn_z",
    "_atom_site.B_iso_or_equiv",
    "_atom_site.auth_seq_id",
    "_atom_site.auth_asym_id",
    "_atom_site.pdbx_PDB_model_num",
    ...rows,
    "#",
  ];
}

/**
 * Minimales mmCIF des Proteins für die Engine: CA + O je Rest (Rest-Typ ALA —
 * der Cartoon braucht nur das Rückgrat), B-Faktor = pLDDT-Klasse, dazu
 * _struct_conf/_struct_sheet_range aus `ss`. Die Engine rechnet so keine
 * eigene Sekundärstruktur und zeigt dieselbe wie die Datei.
 */
export function proteinMmcif(segs) {
  const atoms = [];
  const conf = [];
  const sheet = [];
  let id = 1;
  for (const seg of segs) {
    const asym = seg.chain.id;
    const first = seg.seq0;
    seg.ca.forEach((p, i) => {
      const b = PLDDT_B[seg.q[i]] ?? 0;
      atoms.push(`ATOM ${id++} C CA ALA ${asym} 1 ${first + i} ${f3(p[0])} ${f3(p[1])} ${f3(p[2])} ${b} ${first + i} ${asym} 1`);
      const o = seg.o[i];
      if (o) atoms.push(`ATOM ${id++} O O ALA ${asym} 1 ${first + i} ${f3(o[0])} ${f3(o[1])} ${f3(o[2])} ${b} ${first + i} ${asym} 1`);
    });
    let k = 0;
    while (k < seg.ss.length) {
      let j = k;
      while (j < seg.ss.length && seg.ss[j] === seg.ss[k]) j++;
      const code = seg.ss[k];
      if (code === "H" && j - k >= 3) conf.push([asym, first + k, first + j - 1]);
      if (code === "E" && j - k >= 2) sheet.push([asym, first + k, first + j - 1]);
      k = j;
    }
  }
  const lines = ["data_protein", "#", ...atomSite(atoms)];
  const range = (a, b, e) => `ALA ${a} ${b} ALA ${a} ${e} ${a} ${b} ${a} ${e}`;
  const ends = ["beg_label_comp_id", "beg_label_asym_id", "beg_label_seq_id", "end_label_comp_id",
    "end_label_asym_id", "end_label_seq_id", "beg_auth_asym_id", "beg_auth_seq_id", "end_auth_asym_id", "end_auth_seq_id"];
  if (conf.length) {
    lines.push("loop_", "_struct_conf.conf_type_id", "_struct_conf.id", "_struct_conf.pdbx_PDB_helix_class",
      ...ends.map((f) => `_struct_conf.${f}`),
      ...conf.map(([a, b, e], i) => `HELX_P HELX_P${i + 1} 1 ${range(a, b, e)}`), "#");
  }
  if (sheet.length) {
    lines.push("loop_", "_struct_sheet_range.sheet_id", "_struct_sheet_range.id",
      ...ends.map((f) => `_struct_sheet_range.${f}`),
      ...sheet.map(([a, b, e], i) => `S${i + 1} 1 ${range(a, b, e)}`), "#");
  }
  return lines.join("\n") + "\n";
}

/** HETATM der Liganden als eigenes mmCIF ("" ohne Liganden). */
export function ligandMmcif(ligands = []) {
  const ligs = decodeLigands(ligands);
  if (!ligs.length) return "";
  const atoms = [];
  let id = 1;
  ligs.forEach((l, li) => {
    const asym = `L${li + 1}`;
    const comp = (l.code || "LIG").replace(/\s/g, "");
    l.xyz.forEach((p, i) => {
      const el = (l.elements[i] || "C").toUpperCase();
      atoms.push(`HETATM ${id++} ${el} ${el}${i + 1} ${comp} ${asym} ${li + 1} . ${f3(p[0])} ${f3(p[1])} ${f3(p[2])} 0 ${li + 1} ${asym} 1`);
    });
  });
  return ["data_ligands", "#", ...atomSite(atoms)].join("\n") + "\n";
}
