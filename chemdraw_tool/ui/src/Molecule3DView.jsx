import React, { useMemo, useRef, useState } from "react";
import SectionHeader from "./components/SectionHeader";

// Leichtgewichtiger Ball-and-Stick-Viewer: Rotationsmatrix + Painter's
// Algorithm in purem SVG. Bewusst kein WebGL/3Dmol — die Single-File-App
// bliebe sonst nicht klein, und WebGL ist im Panel-iframe nicht garantiert.

const ELEMENT_COLORS = {
  H: "#b8b8b8",
  C: "#3a3a3a",
  N: "#4a9eff",
  O: "#ff6b6b",
  S: "#c8c800",
  Cl: "#2e9e2e",
  F: "#2e9e2e",
  Br: "#8B4513",
  I: "#7728a8",
  P: "#FFA500",
};

const ATOM_RADIUS = { H: 0.36, default: 0.6 };

function rotate(atom, sin, cos) {
  // erst um y (horizontaler Drag), dann um x (vertikaler Drag)
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

  // Painter's Algorithm: Bindungen und Atome gemeinsam nach Tiefe sortieren.
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
    <div style={{ padding: 16 }}>
      <SectionHeader
        title={data.name}
        subtitle="3D conformer (ETKDG + force field) · drag to rotate"
      />
      <svg
        viewBox={`0 0 ${size} ${size}`}
        style={{
          width: "100%",
          maxWidth: size,
          display: "block",
          margin: "0 auto",
          background: "#ffffff",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
          cursor: "grab",
          touchAction: "none",
        }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
      >
        {items.map((item, i) => {
          if (item.kind === "bond") {
            const width = item.order >= 2 ? 5 : 3;
            return (
              <line
                key={i}
                x1={item.p.sx}
                y1={item.p.sy}
                x2={item.q.sx}
                y2={item.q.sy}
                stroke="#777777"
                strokeWidth={width}
                strokeLinecap="round"
              />
            );
          }
          const r =
            (ATOM_RADIUS[item.p.symbol] ?? ATOM_RADIUS.default) * scale * 0.55;
          // Tiefenhinweis: hintere Atome etwas kleiner und blasser
          const depth = (item.p.z / maxExtent + 1) / 2; // 0 hinten … 1 vorn
          return (
            <circle
              key={i}
              cx={item.p.sx}
              cy={item.p.sy}
              r={r * (0.75 + 0.25 * depth)}
              fill={ELEMENT_COLORS[item.p.symbol] || "#888888"}
              opacity={0.65 + 0.35 * depth}
              stroke="#ffffff"
              strokeWidth="1"
            />
          );
        })}
      </svg>
      {data.files?.sdf && (
        <div
          style={{
            fontSize: 10,
            color: "var(--fg-muted)",
            marginTop: 8,
            fontFamily: "ui-monospace, monospace",
            wordBreak: "break-all",
          }}
        >
          SDF: {data.files.sdf}
        </div>
      )}
    </div>
  );
}
