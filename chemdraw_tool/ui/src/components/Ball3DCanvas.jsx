import React, { useMemo, useRef, useState } from "react";

// Leichtgewichtiger Ball-and-Stick-Viewer: Rotationsmatrix + Painter's
// Algorithm in purem SVG. Bewusst kein WebGL/3Dmol — die Single-File-App
// bliebe sonst nicht klein, und WebGL ist im Panel-iframe nicht garantiert.
// Herausgelöst aus Molecule3DView, damit das Molekülpanel (3D-Knopf) denselben
// Viewer in seiner Zeichenfläche zeigt — eine Zeichnung, zwei Einstiege.
//
// Design-Kritik 07.11. (Rang 1 und 2): Die Kuhle ist die einzige Form — kein
// eigener Hintergrund, kein Rahmen; Verlauf, Schatten sowie C und H kommen aus
// Theme-Variablen (styles.css, `--bowl-*`, `--atom3d-*`). Bindungen zeigen die
// Chemie: Hälften in der Atomfarbe, Mehrfachbindungen als Parallel-Linien,
// aromatisch voll + gestrichelt, Strichstärke nach Tiefe.

// C und H hängen vom Theme ab (dunkler Kohlenstoff verschwindet auf dunkler
// Kuhle, heller Wasserstoff auf heller) — beide als CSS-Variable mit drei
// Tönen für den Kugelverlauf. Die Heteroatome sind in beiden Themes lesbar.
const THEMED = {
  C: { base: "var(--atom3d-c)", hi: "var(--atom3d-c-hi)", lo: "var(--atom3d-c-lo)" },
  H: { base: "var(--atom3d-h)", hi: "var(--atom3d-h-hi)", lo: "var(--atom3d-h-lo)" },
};

const ELEMENT_COLORS = {
  N: "#3b7fff",
  O: "#ff4d4d",
  S: "#e6c200",
  Cl: "#33cc33",
  F: "#66d9a8",
  Br: "#a0522d",
  I: "#8a2be2",
  P: "#ff8c1a",
};
const DEFAULT_COLOR = "#888888";

// Kovalenzradien in Å (Cordero et al. 2008, gerundet): Halogene und Schwefel
// sind sofort als größere Kugeln zu erkennen, statt zweier Klassen H/Rest.
const COVALENT_RADIUS = {
  H: 0.31, B: 0.84, C: 0.76, N: 0.71, O: 0.66, F: 0.57, Si: 1.11,
  P: 1.07, S: 1.05, Cl: 1.02, Se: 1.20, Br: 1.20, I: 1.39,
  default: 0.75,
};
const ATOM_DRAW_FACTOR = 0.55;  // gezeichneter Radius = Kovalenzradius × Faktor

const BOND_WIDTH = 4;        // Einfachbindung ganz vorn, in viewBox-Einheiten
const BOND_SPACING = 3.4;    // Abstand paralleler Linien (Doppel, Dreifach, aromatisch)

const radiusOf = (symbol) => COVALENT_RADIUS[symbol] ?? COVALENT_RADIUS.default;
const bondColor = (symbol) => THEMED[symbol]?.base ?? ELEMENT_COLORS[symbol] ?? DEFAULT_COLOR;

function shade(hex, factor) {
  const n = parseInt(hex.slice(1), 16);
  const ch = (shiftedColor) =>
    Math.max(0, Math.min(255, Math.round(shiftedColor)));
  const r = ch(((n >> 16) & 255) * factor);
  const g = ch(((n >> 8) & 255) * factor);
  const b = ch((n & 255) * factor);
  return `rgb(${r},${g},${b})`;
}

function gradientStops(el) {
  const themed = THEMED[el];
  if (themed) return [themed.hi, themed.base, themed.lo];
  const base = ELEMENT_COLORS[el] || DEFAULT_COLOR;
  return [shade(base, 1.65), base, shade(base, 0.55)];
}

function rotate(atom, sin, cos) {
  const x1 = atom.x * cos.y + atom.z * sin.y;
  const z1 = -atom.x * sin.y + atom.z * cos.y;
  const y2 = atom.y * cos.x - z1 * sin.x;
  const z2 = atom.y * sin.x + z1 * cos.x;
  return { x: x1, y: y2, z: z2 };
}

const isAromatic = (b) => b.aromatic === true || b.order === 1.5;

// Linien einer Bindung als Versätze senkrecht zur projizierten Achse:
// [Versatz, relative Breite, gestrichelt]. Aromatisch: volle Linie auf der
// Achse, gestrichelte zur Ringseite hin (side = ±1).
function bondStrands(bond, side) {
  if (isAromatic(bond)) return [[0, 0.7, false], [side * BOND_SPACING, 0.45, true]];
  const order = Math.round(bond.order || 1);
  if (order === 2) return [[-BOND_SPACING / 2, 0.55, false], [BOND_SPACING / 2, 0.55, false]];
  if (order >= 3) return [[-BOND_SPACING, 0.45, false], [0, 0.45, false], [BOND_SPACING, 0.45, false]];
  return [[0, 1, false]];
}

export default function Ball3DCanvas({ atoms = [], bonds = [], style }) {
  const [rot, setRot] = useState({ x: -0.4, y: 0.6 });
  const drag = useRef(null);

  // Bindungsradius (größter Abstand vom Ursprung): eine Drehung ändert den Betrag
  // nicht, also bleibt jedes Atom in jeder Lage innerhalb der Kuhle — und ein
  // flaches Molekül darf sie ganz ausfüllen, statt am größten Achsenwert zu hängen.
  const maxExtent = useMemo(() => {
    let m = 0.5;
    for (const a of atoms) {
      m = Math.max(m, Math.hypot(a.x, a.y, a.z));
    }
    return m;
  }, [atoms]);
  const atomReach = useMemo(
    () => Math.max(0, ...atoms.map((a) => radiusOf(a.symbol))) * ATOM_DRAW_FACTOR,
    [atoms]
  );

  const elements = useMemo(
    () => [...new Set(atoms.map((a) => a.symbol))],
    [atoms]
  );

  // Für die Ringseite aromatischer Bindungen: aromatische Nachbarn je Atom.
  const aromaticNeighbors = useMemo(() => {
    const nb = atoms.map(() => []);
    for (const b of bonds) {
      if (!isAromatic(b) || !nb[b.a] || !nb[b.b]) continue;
      nb[b.a].push(b.b);
      nb[b.b].push(b.a);
    }
    return nb;
  }, [atoms, bonds]);

  if (!atoms.length) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No 3D data available.
      </div>
    );
  }

  const size = 480;
  const center = size / 2;
  const bowlRadius = size / 2 - 12;
  // Atommittelpunkt + gezeichneter Radius bleiben innerhalb der Kuhle (4 px Luft)
  const scale = (bowlRadius - 4) / (maxExtent + atomReach);
  const sin = { x: Math.sin(rot.x), y: Math.sin(rot.y) };
  const cos = { x: Math.cos(rot.x), y: Math.cos(rot.y) };
  const depthOf = (z) => (z / maxExtent + 1) / 2; // 0 hinten … 1 vorn

  const projected = atoms.map((a) => {
    const p = rotate(a, sin, cos);
    const depth = depthOf(p.z);
    return {
      symbol: a.symbol,
      sx: center + p.x * scale,
      sy: center - p.y * scale,
      z: p.z,
      depth,
      r: radiusOf(a.symbol) * scale * ATOM_DRAW_FACTOR * (0.78 + 0.22 * depth),
    };
  });

  const items = [];
  for (const b of bonds) {
    const p = projected[b.a];
    const q = projected[b.b];
    if (!p || !q) continue;
    items.push({ kind: "bond", z: (p.z + q.z) / 2, bond: b, p, q });
  }
  for (const p of projected) {
    items.push({ kind: "atom", z: p.z, p });
  }
  items.sort((a, b) => a.z - b.z);

  // Kontaktschatten unter dem tiefsten projizierten Punkt, so breit wie das
  // Molekül — aber innerhalb der Kuhle (Sehne auf Schattenhöhe).
  const xs = projected.map((p) => p.sx);
  const bottom = Math.max(...projected.map((p) => p.sy + p.r));
  const shadowRy = size * 0.045;
  const shadowCy = Math.min(bottom + shadowRy * 0.4, center + bowlRadius - shadowRy - 2);
  const chord = Math.sqrt(Math.max(0, bowlRadius ** 2 - (shadowCy - center) ** 2));
  const shadowRx = Math.max(size * 0.08, Math.min((Math.max(...xs) - Math.min(...xs)) / 2 * 0.8, chord * 0.85));
  const shadowCx = Math.max(center - chord + shadowRx, Math.min(center + chord - shadowRx, (Math.max(...xs) + Math.min(...xs)) / 2));

  const renderBond = (item, i) => {
    const { bond, p, q } = item;
    const dx = q.sx - p.sx;
    const dy = q.sy - p.sy;
    const len = Math.hypot(dx, dy);
    const nx = len > 1e-6 ? -dy / len : 1;
    const ny = len > 1e-6 ? dx / len : 0;
    let side = 1;
    if (isAromatic(bond)) {
      const k = (aromaticNeighbors[bond.a] || []).find((n) => n !== bond.b)
        ?? (aromaticNeighbors[bond.b] || []).find((n) => n !== bond.a);
      if (k !== undefined && projected[k]) {
        const mx = (p.sx + q.sx) / 2;
        const my = (p.sy + q.sy) / 2;
        side = nx * (projected[k].sx - mx) + ny * (projected[k].sy - my) < 0 ? -1 : 1;
      }
    }
    const width = BOND_WIDTH * (0.5 + 0.5 * depthOf(item.z));
    const mid = { sx: (p.sx + q.sx) / 2, sy: (p.sy + q.sy) / 2 };
    const lines = [];
    bondStrands(bond, side).forEach(([off, rel, dashed], s) => {
      const ox = nx * off;
      const oy = ny * off;
      for (const [end, symbol] of [[p, p.symbol], [q, q.symbol]]) {
        const w = width * rel;
        lines.push(
          <line
            key={`${s}-${lines.length}`}
            data-element={symbol}
            x1={end.sx + ox}
            y1={end.sy + oy}
            x2={mid.sx + ox}
            y2={mid.sy + oy}
            style={{ stroke: bondColor(symbol) }}
            strokeWidth={w}
            strokeLinecap={dashed ? "butt" : "round"}
            strokeDasharray={dashed ? `${(w * 1.6).toFixed(2)} ${(w * 1.4).toFixed(2)}` : undefined}
          />
        );
      }
    });
    return (
      <g key={i} data-bond-order={isAromatic(bond) ? "aromatic" : String(Math.round(bond.order || 1))}>
        {lines}
      </g>
    );
  };

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
    <svg
      viewBox={`0 0 ${size} ${size}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="3D model, drag to rotate"
      style={{
        flex: 1,
        width: "100%",
        height: "100%",
        cursor: "grab",
        touchAction: "none",
        ...style,
      }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
    >
      <defs>
        {/* Konkave Mulde: Lichtpunkt unterhalb der Mitte, obere
            Innenwand dunkler — so liest das Auge "Kuhle" statt Kugel. */}
        <radialGradient id="bowl" cx="50%" cy="50%" r="50%" fx="50%" fy="63%">
          <stop offset="0%" style={{ stopColor: "var(--bowl-0)" }} />
          <stop offset="55%" style={{ stopColor: "var(--bowl-1)" }} />
          <stop offset="85%" style={{ stopColor: "var(--bowl-2)" }} />
          <stop offset="100%" style={{ stopColor: "var(--bowl-3)" }} />
        </radialGradient>
        <radialGradient id="contact-shadow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" style={{ stopColor: "var(--bowl-shadow)" }} />
          <stop offset="70%" style={{ stopColor: "var(--bowl-shadow-mid)" }} />
          <stop offset="100%" style={{ stopColor: "var(--bowl-shadow-end)" }} />
        </radialGradient>
        {elements.map((el) => {
          const [hi, base, lo] = gradientStops(el);
          return (
            <radialGradient key={el} id={`atom-${el}`} cx="32%" cy="30%" r="75%">
              <stop offset="0%" style={{ stopColor: hi }} />
              <stop offset="45%" style={{ stopColor: base }} />
              <stop offset="100%" style={{ stopColor: lo }} />
            </radialGradient>
          );
        })}
      </defs>
      <circle
        cx={center}
        cy={center}
        r={bowlRadius}
        fill="url(#bowl)"
        style={{ stroke: "var(--bowl-rim)" }}
        strokeWidth="1.5"
      />
      <ellipse
        cx={shadowCx}
        cy={shadowCy}
        rx={shadowRx}
        ry={shadowRy}
        fill="url(#contact-shadow)"
      />
      {items.map((item, i) => {
        if (item.kind === "bond") return renderBond(item, i);
        return (
          <circle
            key={i}
            cx={item.p.sx}
            cy={item.p.sy}
            r={item.p.r}
            fill={`url(#atom-${item.p.symbol})`}
            opacity={0.78 + 0.22 * item.p.depth}
          />
        );
      })}
    </svg>
  );
}
