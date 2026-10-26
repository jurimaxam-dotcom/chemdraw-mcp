import React, { useRef, useState, useLayoutEffect, useCallback } from "react";
import SectionHeader from "./components/SectionHeader";

const MIN_SCALE = 0.4;

// Pfeilformen im 110×18-Raster. Vorwaerts bleibt der bisherige Pfeil;
// Gleichgewicht = zwei Halbpfeile (⇌), Retro = Doppelschaft mit offener Spitze (⇒).
function ArrowGlyph({ kind }) {
  const stroke = "var(--fg-muted)";
  if (kind === "equilibrium") {
    return (
      <>
        <line x1="2" y1="6" x2="108" y2="6" stroke={stroke} strokeWidth="1.6" />
        <polygon points="108,6 96,6 96,1" fill={stroke} />
        <line x1="2" y1="12" x2="108" y2="12" stroke={stroke} strokeWidth="1.6" />
        <polygon points="2,12 14,12 14,17" fill={stroke} />
      </>
    );
  }
  if (kind === "retro") {
    return (
      <>
        <line x1="2" y1="6" x2="103" y2="6" stroke={stroke} strokeWidth="1.6" />
        <line x1="2" y1="12" x2="103" y2="12" stroke={stroke} strokeWidth="1.6" />
        <polyline points="97,1 108,9 97,17" fill="none" stroke={stroke} strokeWidth="1.6" />
      </>
    );
  }
  return (
    <>
      <line x1="2" y1="9" x2="98" y2="9" stroke={stroke} strokeWidth="1.8" />
      <polygon points="98,4 110,9 98,14" fill={stroke} />
    </>
  );
}

function ArrowText({ text, position }) {
  if (!text) return null;
  return (
    <div
      data-conditions={position}
      style={{
        fontSize: 13,
        color: "var(--fg)",
        textAlign: "center",
        whiteSpace: "pre-wrap",
        lineHeight: 1.3,
        maxWidth: 200,
        padding: position === "above" ? "0 0 4px" : "4px 0 0",
      }}
    >
      {text}
    </div>
  );
}

// Pfeilspalte: Bedingungen oben ueber, unten unter dem Pfeil — wie im
// exportierten Bild und im CDXML.
function ReactionArrow({ kind, above, below }) {
  const known = ["forward", "equilibrium", "retro"].includes(kind) ? kind : "forward";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 12px",
        minWidth: 110,
        flexShrink: 0,
      }}
    >
      <ArrowText text={above} position="above" />
      <svg
        data-arrow={known}
        width="110"
        height="18"
        viewBox="0 0 110 18"
        style={{ display: "block" }}
      >
        <ArrowGlyph kind={known} />
      </svg>
      <ArrowText text={below} position="below" />
    </div>
  );
}

function Plus() {
  return (
    <div
      style={{
        fontSize: 22,
        fontWeight: 300,
        color: "var(--fg-muted)",
        padding: "0 14px",
        alignSelf: "center",
        flexShrink: 0,
      }}
    >
      +
    </div>
  );
}

function MoleculeCard({ molecule }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 6,
        flexShrink: 0,
      }}
    >
      {molecule.svg ? (
        <div
          dangerouslySetInnerHTML={{ __html: molecule.svg }}
          style={{
            display: "inline-block",
            lineHeight: 0,
          }}
        />
      ) : (
        <div
          style={{
            width: 80,
            height: 80,
            background: "var(--bg-alt)",
            borderRadius: "var(--radius-sm)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--fg-muted)",
            fontSize: 12,
          }}
        >
          {molecule.name || "?"}
        </div>
      )}
      {molecule.name && (
        <div
          style={{
            fontSize: 13,
            color: "var(--fg-muted)",
            textAlign: "center",
            maxWidth: 160,
            lineHeight: 1.3,
          }}
        >
          {molecule.name}
        </div>
      )}
    </div>
  );
}

function MoleculeGroup({ molecules }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      {molecules.map((mol, i) => (
        <React.Fragment key={i}>
          {i > 0 && <Plus />}
          <MoleculeCard molecule={mol} />
        </React.Fragment>
      ))}
    </div>
  );
}

function ScaledRow({ children }) {
  const outerRef = useRef(null);
  const innerRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [naturalH, setNaturalH] = useState(0);

  const measure = useCallback(() => {
    const outer = outerRef.current;
    const inner = innerRef.current;
    if (!outer || !inner) return;
    const containerW = outer.clientWidth - 32;
    // Restore the actual value afterwards — setting "" here clears React's
    // inline style, and a state bailout (same scale) would never re-render
    // to put it back, leaving the row permanently unscaled.
    const prevTransform = inner.style.transform;
    inner.style.transform = "none";
    const naturalW = inner.scrollWidth;
    const naturalHeight = inner.scrollHeight;
    inner.style.transform = prevTransform;
    if (naturalW <= 0) return;
    // Cap at 1: never blow small reactions up beyond their chemical scale —
    // only shrink-to-fit. Below MIN_SCALE we fall back to scrolling.
    setScale(Math.min(1, Math.max(MIN_SCALE, containerW / naturalW)));
    setNaturalH(naturalHeight);
  }, []);

  useLayoutEffect(() => {
    measure();
    const ro = new ResizeObserver(measure);
    // Observe BOTH: outer for panel resizes, inner for content swaps
    // (a new payload in the same view never resizes the outer container).
    if (outerRef.current) ro.observe(outerRef.current);
    if (innerRef.current) ro.observe(innerRef.current);
    return () => ro.disconnect();
  }, [measure]);

  const needsScroll = scale <= MIN_SCALE;
  // transform: scale() shrinks visually but keeps the un-scaled layout
  // height — compensate so the card hugs the drawing instead of leaving a
  // big empty band underneath.
  const scaledH = !needsScroll && naturalH > 0 ? naturalH * scale : undefined;

  return (
    <div
      ref={outerRef}
      style={{
        overflow: needsScroll ? "auto" : "hidden",
        padding: 16,
        height: scaledH !== undefined ? scaledH + 32 : undefined,
      }}
    >
      <div
        ref={innerRef}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 4,
          transformOrigin: "top left",
          transform: needsScroll ? "none" : `scale(${scale})`,
          width: needsScroll ? undefined : `${100 / scale}%`,
        }}
      >
        {children}
      </div>
    </div>
  );
}

export default function ReactionView({ data }) {
  const reactants = data.reactants || [];
  const products = data.products || [];
  const conditions = data.conditions || null;
  const conditionsBelow = data.conditions_below || null;
  const name = data.name || null;

  return (
    <div className="reaction-panel">
      {name && <SectionHeader title={name} />}
      <div
        style={{
          borderRadius: "var(--radius-md)",
          boxShadow: "var(--shadow-card)",
          background: "var(--bg-alt)",
          overflow: "hidden",
        }}
      >
        <ScaledRow>
          {reactants.length > 0 && <MoleculeGroup molecules={reactants} />}
          <ReactionArrow kind={data.arrow} above={conditions} below={conditionsBelow} />
          {products.length > 0 && <MoleculeGroup molecules={products} />}
        </ScaledRow>
      </div>
    </div>
  );
}
