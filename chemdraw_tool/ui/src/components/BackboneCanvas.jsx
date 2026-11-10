import React, { useMemo, useRef, useState } from "react";

// Drehbare Rückgratspur eines Proteins (E8) — seit E13 der Rückfall, wenn die
// Cartoon-Engine (WebGL) nicht startet, und Grundlage der Panel-Tests ohne
// WebGL. Gleiches Prinzip wie Ball3DCanvas — Drehmatrix + Maleralgorithmus in
// reinem SVG — und dieselbe Bedienung (Ziehen dreht, y dann x). Die
// Koordinaten kommen schon im Ansichtsrahmen des Servers an: Ruhelage =
// Identität, also zeigt das Panel zu Beginn dieselbe Ansicht wie die Datei.
// Glättung: Helices auf ihre Achse, Stränge ohne Zickzack (wie das frühere
// protein_render.smooth_trace), dann Catmull-Rom durch jeden Punkt (Muster aus
// biasmv/pv src/geom.js, MIT). Breite nach Sekundärstruktur in Å, hinten heller.
import { decodeChains } from "../protein/proteinData";
import { PLDDT_COLOR, PLDDT_NAME, SS_COLOR, SS_NAME, residueColorer } from "../protein/colors";

export { PLDDT_COLOR, PLDDT_NAME, SS_COLOR, SS_NAME };
const WIDTH_A = { H: 3.6, E: 1.9, C: 0.8 };
// Deckel wie MAX_PTS_PER_A im PNG: kleine Proteine (Insulin) nicht als Würste.
// Tiefe nur über die Breite — halbtransparente runde Kappen zeichneten Perlen.
const MAX_PX_PER_A = 7;

/** Helices auf ihre Achse (Mittel über 4 Cα), Stränge (¼, ½, ¼) geglättet. */
export function smoothTrace(points, ss) {
  const out = points.map((p) => p.slice());
  const n = points.length;
  const mean = (lo, hi) => [0, 1, 2].map((d) => {
    let sum = 0;
    for (let k = lo; k < hi; k++) sum += points[k][d];
    return sum / (hi - lo);
  });
  let i = 0;
  while (i < n) {
    let j = i;
    while (j < n && ss[j] === ss[i]) j++;
    if (ss[i] === "H" && j - i >= 5) {
      for (let k = i + 1; k < j - 1; k++) {
        const lo = Math.max(i, k - 1), hi = Math.min(j, k + 3);
        out[k] = hi - lo === 4 ? mean(lo, hi) : mean(Math.max(i, k - 2), Math.min(j, k + 2));
      }
    } else if (ss[i] === "E" && j - i >= 3) {
      for (let k = i + 1; k < j - 1; k++) {
        out[k] = [0, 1, 2].map((d) => 0.25 * points[k - 1][d] + 0.5 * points[k][d] + 0.25 * points[k + 1][d]);
      }
    }
    i = j;
  }
  return out;
}

// Uniformes Catmull-Rom; Index k der Ausgabe gehört zu Rest floor(k / sub).
function smooth(points, sub) {
  const n = points.length;
  if (n < 2 || sub <= 1) return points;
  const p = (i) => {
    if (i < 0) return points[0].map((v, d) => 2 * v - points[1][d]);
    if (i >= n) return points[n - 1].map((v, d) => 2 * v - points[n - 2][d]);
    return points[i];
  };
  const out = [];
  for (let i = 0; i < n - 1; i++) {
    const [p0, p1, p2, p3] = [p(i - 1), p(i), p(i + 1), p(i + 2)];
    for (let s = 0; s < sub; s++) {
      const t = s / sub, t2 = t * t, t3 = t2 * t;
      out.push([0, 1, 2].map((d) => 0.5 * (2 * p1[d] + (-p0[d] + p2[d]) * t
        + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3)));
    }
  }
  out.push(points[n - 1]);
  return out;
}

function rotate([x, y, z], sin, cos) {
  const x1 = x * cos.y + z * sin.y;
  const z1 = -x * sin.y + z * cos.y;
  return [x1, y * cos.x - z1 * sin.x, y * sin.x + z1 * cos.x];
}

export default function BackboneCanvas({ chains = [], colorBy = "ss", width = 480, height = 330 }) {
  const [rot, setRot] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const drag = useRef(null);

  // Glatte Kurven einmal je Datensatz; große Proteine mit weniger Zwischenpunkten.
  const curves = useMemo(() => {
    const segs = decodeChains(chains);
    const total = segs.reduce((n, s) => n + s.ss.length, 0);
    const sub = total <= 600 ? 4 : total <= 1500 ? 2 : 1;
    return segs.map((seg) => ({ ...seg, sub, pts: smooth(smoothTrace(seg.ca, seg.ss), sub) }));
  }, [chains]);

  // Maßstab für die Ruhelage (Hauptachsen: längste Ausdehnung waagrecht).
  const { scale, maxR } = useMemo(() => {
    let mx = 1, my = 1, r = 1;
    for (const cv of curves) for (const [x, y, z] of cv.pts) {
      mx = Math.max(mx, Math.abs(x)); my = Math.max(my, Math.abs(y)); r = Math.max(r, Math.hypot(x, y, z));
    }
    const margin = 2.5; // Å — gut eine halbe Helixbreite
    return { scale: Math.min((width / 2 - 6) / (mx + margin), (height / 2 - 6) / (my + margin)), maxR: r };
  }, [curves, width, height]);

  if (!curves.length) {
    return <div style={{ color: "var(--fg-muted)", padding: 16 }}>No backbone data available.</div>;
  }

  const sin = { x: Math.sin(rot.x), y: Math.sin(rot.y) };
  const cos = { x: Math.cos(rot.x), y: Math.cos(rot.y) };
  const colorOf = residueColorer(curves, colorBy);
  const color = (cv, res) => colorOf(cv, res);

  // Ein Stück je Rest (sub Teilstrecken), nach Tiefe sortiert.
  const items = [];
  const termini = [];
  for (const cv of curves) {
    const proj = cv.pts.map((p) => rotate(p, sin, cos));
    for (let k = 0; k + 1 < proj.length; k += cv.sub) {
      const res = Math.min(cv.ss.length - 1, Math.floor(k / cv.sub));
      const end = Math.min(proj.length - 1, k + cv.sub);
      const seg = proj.slice(k, end + 1);
      const z = seg.reduce((s, p) => s + p[2], 0) / seg.length;
      items.push({ cv, res, seg, z });
    }
  }
  for (const [ci, chain] of chains.entries()) {
    const own = curves.filter((cv) => cv.ci === ci);
    if (!own.length) continue;
    const first = rotate(own[0].pts[0], sin, cos);
    const lastCv = own[own.length - 1];
    const last = rotate(lastCv.pts[lastCv.pts.length - 1], sin, cos);
    const tag = chains.length > 1 ? ` (${chain.id})` : "";
    termini.push({ key: `${ci}N`, p: first, text: `N${tag}` }, { key: `${ci}C`, p: last, text: `C${tag}` });
  }
  items.sort((a, b) => a.z - b.z);

  const cx = width / 2, cy = height / 2;
  const sx = (p) => cx + p[0] * scale;
  const sy = (p) => cy - p[1] * scale;
  const depth = (z) => Math.max(0, Math.min(1, (z / maxR + 1) / 2));

  const onPointerDown = (e) => {
    drag.current = { x: e.clientX, y: e.clientY, rot };
    setDragging(true);
    if (e.pointerId != null) e.currentTarget.setPointerCapture?.(e.pointerId);
  };
  const onPointerMove = (e) => {
    if (!drag.current) return;
    setRot({
      x: drag.current.rot.x + (e.clientY - drag.current.y) * 0.01,
      y: drag.current.rot.y + (e.clientX - drag.current.x) * 0.01,
    });
  };
  const endDrag = () => {
    drag.current = null;
    setDragging(false);
  };

  return (
    <svg
      data-backbone=""
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Protein backbone trace, drag to rotate"
      style={{ flex: 1, width: "100%", height: "100%", minHeight: 0,
        cursor: dragging ? "grabbing" : "grab", touchAction: "none" }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onLostPointerCapture={endDrag}
    >
      {items.map(({ cv, res, seg, z }, i) => {
        const d = depth(z);
        const code = cv.ss[res] || "C";
        const pale = colorBy !== "plddt" && cv.q && cv.q[res] <= "2";
        return (
          <path
            key={i}
            data-residue-ss={code}
            d={seg.map((p, j) => `${j ? "L" : "M"}${sx(p).toFixed(1)} ${sy(p).toFixed(1)}`).join("")}
            fill="none"
            stroke={color(cv, res)}
            strokeOpacity={pale ? 0.35 : undefined}
            strokeWidth={(WIDTH_A[code] * Math.min(scale, MAX_PX_PER_A) * (0.7 + 0.5 * d)).toFixed(2)}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      })}
      {termini.map(({ key, p, text }) => (
        <text key={key} x={sx(p) + 6} y={sy(p) - 6} fontSize="12" fontWeight="600"
          style={{ fill: "var(--fg)", paintOrder: "stroke", stroke: "var(--bg, #fff)", strokeWidth: 3 }}>
          {text}
        </text>
      ))}
    </svg>
  );
}
