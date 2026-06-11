import React, { useMemo, useRef, useState } from "react";
import SectionHeader from "./components/SectionHeader";

// Leichtgewichtiger Ball-and-Stick-Viewer: Rotationsmatrix + Painter's
// Algorithm in purem SVG. Bewusst kein WebGL/3Dmol — die Single-File-App
// bliebe sonst nicht klein, und WebGL ist im Panel-iframe nicht garantiert.
// Layout-Vertrag: füllt IMMER den Panel-Viewport (100vh, kein Scrollen);
// das Modell skaliert proportional in die verfügbare Fläche.

const ELEMENT_COLORS = {
  H: "#d8d8d8",
  C: "#4a4a4a",
  N: "#3b7fff",
  O: "#ff4d4d",
  S: "#e6c200",
  Cl: "#33cc33",
  F: "#66d9a8",
  Br: "#a0522d",
  I: "#8a2be2",
  P: "#ff8c1a",
};

const ATOM_RADIUS = { H: 0.34, default: 0.58 };

function shade(hex, factor) {
  const n = parseInt(hex.slice(1), 16);
  const ch = (shiftedColor) =>
    Math.max(0, Math.min(255, Math.round(shiftedColor)));
  const r = ch(((n >> 16) & 255) * factor);
  const g = ch(((n >> 8) & 255) * factor);
  const b = ch((n & 255) * factor);
  return `rgb(${r},${g},${b})`;
}

function rotate(atom, sin, cos) {
  const x1 = atom.x * cos.y + atom.z * sin.y;
  const z1 = -atom.x * sin.y + atom.z * cos.y;
  const y2 = atom.y * cos.x - z1 * sin.x;
  const z2 = atom.y * sin.x + z1 * cos.x;
  return { x: x1, y: y2, z: z2 };
}

export default function Molecule3DView({ data }) {
  const [rot, setRot] = useState({ x: -0.4, y: 0.6 });
  const drag = useRef(null);

  const atoms = data.atoms || [];
  const bonds = data.bonds || [];

  const maxExtent = useMemo(() => {
    let m = 1;
    for (const a of atoms) {
      m = Math.max(m, Math.abs(a.x), Math.abs(a.y), Math.abs(a.z));
    }
    return m;
  }, [atoms]);

  const elements = useMemo(
    () => [...new Set(atoms.map((a) => a.symbol))],
    [atoms]
  );

  if (!atoms.length) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No 3D data available.
      </div>
    );
  }

  const size = 480;
  const scale = (size / 2 - 30) / maxExtent;
  const sin = { x: Math.sin(rot.x), y: Math.sin(rot.y) };
  const cos = { x: Math.cos(rot.x), y: Math.cos(rot.y) };

  const projected = atoms.map((a) => {
    const p = rotate(a, sin, cos);
    return {
      symbol: a.symbol,
      sx: size / 2 + p.x * scale,
      sy: size / 2 - p.y * scale,
      z: p.z,
    };
  });

  const items = [];
  for (const b of bonds) {
    const p = projected[b.a];
    const q = projected[b.b];
    items.push({ kind: "bond", z: (p.z + q.z) / 2, p, q, order: b.order });
  }
  for (const p of projected) {
    items.push({ kind: "atom", z: p.z, p });
  }
  items.sort((a, b) => a.z - b.z);

  const onPointerDown = (e) => {
    drag.current = { x: e.clientX, y: e.clientY, rot };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onPointerMove = (e) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.x;
    const dy = e.clientY - drag.current.y;
    setRot({
      x: drag.current.rot.x + dy * 0.01,
      y: drag.current.rot.y + dx * 0.01,
    });
  };
  const onPointerUp = () => {
    drag.current = null;
  };

  return (
    <div
      style={{
        height: "calc(100vh - 16px)",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        padding: "12px 16px",
      }}
    >
      <SectionHeader
        title={data.name}
        subtitle="3D conformer (ETKDG + force field) · drag to rotate"
      />
      <div style={{ flex: 1, minHeight: 0, display: "flex" }}>
        <svg
          viewBox={`0 0 ${size} ${size}`}
          preserveAspectRatio="xMidYMid meet"
          style={{
            flex: 1,
            width: "100%",
            height: "100%",
            background:
              "radial-gradient(circle at 50% 40%, #ffffff 60%, #f0f2f6 100%)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            cursor: "grab",
            touchAction: "none",
          }}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
        >
          <defs>
            {elements.map((el) => {
              const base = ELEMENT_COLORS[el] || "#888888";
              return (
                <radialGradient key={el} id={`atom-${el}`} cx="32%" cy="30%" r="75%">
                  <stop offset="0%" stopColor={shade(base, 1.65)} />
                  <stop offset="45%" stopColor={base} />
                  <stop offset="100%" stopColor={shade(base, 0.55)} />
                </radialGradient>
              );
            })}
          </defs>
          {items.map((item, i) => {
            if (item.kind === "bond") {
              const width = item.order >= 2 ? 6 : 4;
              return (
                <line
                  key={i}
                  x1={item.p.sx}
                  y1={item.p.sy}
                  x2={item.q.sx}
                  y2={item.q.sy}
                  stroke="#5a5a5a"
                  strokeWidth={width}
                  strokeLinecap="round"
                />
              );
            }
            const r =
              (ATOM_RADIUS[item.p.symbol] ?? ATOM_RADIUS.default) *
              scale *
              0.55;
            const depth = (item.p.z / maxExtent + 1) / 2; // 0 hinten … 1 vorn
            return (
              <circle
                key={i}
                cx={item.p.sx}
                cy={item.p.sy}
                r={r * (0.78 + 0.22 * depth)}
                fill={`url(#atom-${item.p.symbol})`}
                opacity={0.78 + 0.22 * depth}
              />
            );
          })}
        </svg>
      </div>
      {data.files?.sdf && (
        <div
          style={{
            fontSize: 10,
            color: "var(--fg-muted)",
            marginTop: 8,
            fontFamily: "ui-monospace, monospace",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            flexShrink: 0,
          }}
        >
          SDF: {data.files.sdf}
        </div>
      )}
    </div>
  );
}
