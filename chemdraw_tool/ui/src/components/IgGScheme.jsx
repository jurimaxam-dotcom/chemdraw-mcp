import React from "react";

// IgG1-Domänenschema fürs Proteinpanel (Antikörper). Gleicher Inhalt wie die
// Datei aus igg_scheme.py (zwei schwere Ketten VH–CH1–Gelenk–CH2–CH3, zwei
// leichte VL–CL, Interketten-Disulfide, N297-Glykan), aber als Inline-SVG mit
// Theme-Variablen: Text und Linien in var(--fg)/var(--fg-muted), damit es im
// dunklen Schema lesbar bleibt. Domänenflächen tragen ihre eigene Textfarbe
// (Weiß auf Blau, Dunkel auf Orange) — beides hält in beiden Schemata.
// `highlight`: "fab" = ein Fab-Arm ist die gezeigte Struktur, "igg" = das
// ganze Molekül, "" = keine Markierung (allgemeine Architektur).

export const HEAVY = "#0072B2";
export const LIGHT = "#E69F00";
const SS = "#B8860B";
const CX = 200;
const DOM_L = 46; // Länge entlang der Kette
const DOM_W = 32; // Breite quer
const S = Math.SQRT1_2;

function Domain({ x, y, angle, face, label, ink }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${angle})`}>
      <ellipse rx={DOM_W / 2} ry={DOM_L / 2} fill={face} stroke="var(--fg)" strokeOpacity="0.55" strokeWidth="1" />
      <text transform={`rotate(${-angle})`} textAnchor="middle" dominantBaseline="central"
        fontSize="12" fontWeight="600" fill={ink}>{label}</text>
    </g>
  );
}

function arm(side) {
  // Richtung entlang des Arms (nach oben außen) und quer (nach außen unten)
  const d = [side * S, -S];
  const n = [side * S, S];
  const top = [CX + side * 18, 178];
  const at = (t, off = 0) => [top[0] + d[0] * t + n[0] * off, top[1] + d[1] * t + n[1] * off];
  return { side, d, n, top, at, angle: side * 45 };
}

function ArmShapes({ a }) {
  const off = DOM_W + 4;
  const ch1 = a.at(36), vh = a.at(36 + DOM_L + 2), cl = a.at(36, off), vl = a.at(36 + DOM_L + 2, off);
  const tail = a.at(8, off);
  return (
    <g>
      <line x1={a.top[0]} y1={a.top[1]} x2={ch1[0]} y2={ch1[1]} stroke="var(--fg)" strokeWidth="1.6" />
      <line x1={tail[0]} y1={tail[1]} x2={cl[0]} y2={cl[1]} stroke="var(--fg)" strokeWidth="1.6" />
      <line x1={tail[0]} y1={tail[1]} x2={a.at(4)[0]} y2={a.at(4)[1]} stroke={SS} strokeWidth="2.4" />
      <Domain x={ch1[0]} y={ch1[1]} angle={a.angle} face={HEAVY} ink="#ffffff" label="CH1" />
      <Domain x={vh[0]} y={vh[1]} angle={a.angle} face={HEAVY} ink="#ffffff" label="VH" />
      <Domain x={cl[0]} y={cl[1]} angle={a.angle} face={LIGHT} ink="#1a1a1a" label="CL" />
      <Domain x={vl[0]} y={vl[1]} angle={a.angle} face={LIGHT} ink="#1a1a1a" label="VL" />
    </g>
  );
}

function armBox(a) {
  const off = DOM_W + 4;
  const t0 = 36 - DOM_L / 2 - 6, t1 = 36 + 1.5 * DOM_L + 10;
  const o0 = -DOM_W / 2 - 6, o1 = off + DOM_W / 2 + 6;
  return [a.at(t0, o0), a.at(t1, o0), a.at(t1, o1), a.at(t0, o1)].map((p) => p.join(",")).join(" ");
}

export default function IgGScheme({ highlight = "", caption = "" }) {
  const arms = [arm(-1), arm(1)];
  const text = { fill: "var(--fg)", fontSize: 13 };
  const note = { fill: "var(--fg-muted)", fontSize: 12 };
  const tipL = arms[0].at(36 + 1.5 * DOM_L + 6, (DOM_W + 4) / 2);
  const tipR = arms[1].at(36 + 1.5 * DOM_L + 6, (DOM_W + 4) / 2);
  return (
    <svg data-igg-scheme={highlight || "none"} viewBox="40 6 360 346" role="img"
      aria-label={`IgG1 domain scheme${caption ? ` — ${caption}` : ""}`}
      style={{ width: "100%", height: "100%", display: "block" }}
      fontFamily="var(--font)">
      {/* Markierung: welcher Teil die gezeigte Struktur ist */}
      {highlight === "fab" && (
        <g data-highlight="fab">
          <polygon points={armBox(arms[0])} fill="var(--accent)" fillOpacity="0.12"
            stroke="var(--accent)" strokeWidth="2" strokeDasharray="6 4" strokeLinejoin="round" />
          <text x="48" y="24" {...text} fill="var(--accent)" fontWeight="600">Shown structure: this Fab arm</text>
        </g>
      )}
      {highlight === "igg" && (
        <g data-highlight="igg">
          <rect x="62" y="34" width="276" height="300" rx="10" fill="var(--accent)" fillOpacity="0.08"
            stroke="var(--accent)" strokeWidth="2" strokeDasharray="6 4" />
          <text x="48" y="24" {...text} fill="var(--accent)" fontWeight="600">Shown structure: the whole antibody</text>
        </g>
      )}
      {/* Fc-Stamm und Gelenk */}
      {[-1, 1].map((side) => (
        <g key={side}>
          <polyline points={`${CX + side * 18},178 ${CX + side * 18},206 ${CX + side * 30},236 ${CX + side * 30},250 ${CX + side * 21},300`}
            fill="none" stroke="var(--fg)" strokeWidth="1.6" />
          <Domain x={CX + side * 30} y={244} angle={0} face={HEAVY} ink="#ffffff" label="CH2" />
          <Domain x={CX + side * 21} y={298} angle={0} face={HEAVY} ink="#ffffff" label="CH3" />
          {/* N297-Glykan innen am CH2: GlcNAc (blaues Quadrat), Mannose (grüner Kreis) */}
          <rect x={CX + side * 9 - 3.5} y={236} width="7" height="7" fill={HEAVY} stroke="var(--fg)" strokeWidth="0.6" />
          <circle cx={CX + side * 6} cy={251} r="3.6" fill="#009E73" stroke="var(--fg)" strokeWidth="0.6" />
        </g>
      ))}
      {[190, 200].map((y) => (
        <line key={y} x1={CX - 18} y1={y} x2={CX + 18} y2={y} stroke={SS} strokeWidth="2.4" />
      ))}
      {arms.map((a) => <ArmShapes key={a.side} a={a} />)}
      {[tipL, tipR].map(([x, y]) => (
        <circle key={x} cx={x} cy={y} r="7" fill="none" stroke="#CC79A7" strokeWidth="2.2" />
      ))}
      {/* Beschriftung */}
      <text x="66" y="62" {...text} fontWeight="700" fontSize="15">Fab</text>
      <text x="312" y="62" {...text} fontWeight="700" fontSize="15">Fab</text>
      <line x1="256" y1="232" x2="262" y2="232" stroke="var(--fg-muted)" />
      <line x1="262" y1="232" x2="262" y2="322" stroke="var(--fg-muted)" />
      <line x1="256" y1="322" x2="262" y2="322" stroke="var(--fg-muted)" />
      <text x="268" y="282" {...text} fontWeight="700" fontSize="15">Fc</text>
      <line x1="220" y1="195" x2="300" y2="214" stroke="var(--fg-muted)" strokeWidth="0.8" />
      <text x="302" y="218" {...note}>hinge (H–H S–S)</text>
      <text x="146" y="262" {...note} textAnchor="end">N297 glycan</text>
      <text x={tipL[0] - 4} y={tipL[1] - 20} {...note} textAnchor="middle">antigen-binding site</text>
      <text x="396" y="346" {...note} textAnchor="end" fontSize="11">human IgG1 · EU numbering</text>
    </svg>
  );
}

export const SCHEME_LEGEND = [
  [HEAVY, "heavy chain"],
  [LIGHT, "light chain (κ)"],
  [SS, "inter-chain disulfide"],
  ["#CC79A7", "antigen-binding site"],
];
