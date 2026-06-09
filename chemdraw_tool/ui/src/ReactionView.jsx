import React, { useRef, useState, useLayoutEffect, useCallback } from "react";
import SectionHeader from "./components/SectionHeader";

const MIN_SCALE = 0.4;

function ReactionArrow() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 12px",
        flexShrink: 0,
      }}
    >
      <svg width="110" height="14" viewBox="0 0 110 14" style={{ display: "block" }}>
        <line x1="2" y1="7" x2="98" y2="7" stroke="var(--fg-muted)" strokeWidth="1.8" />
        <polygon points="98,2 110,7 98,12" fill="var(--fg-muted)" />
      </svg>
    </div>
  );
}

function ConditionsCaption({ conditions }) {
  if (!conditions) return null;
  return (
    <div
      style={{
        fontSize: 11,
        color: "var(--fg-muted)",
        textAlign: "center",
        padding: "6px 12px",
        background: "var(--bg-alt)",
        borderTopLeftRadius: "var(--radius-md)",
        borderTopRightRadius: "var(--radius-md)",
        borderBottom: "1px solid var(--border)",
        whiteSpace: "pre-wrap",
        lineHeight: 1.4,
      }}
    >
      <span style={{ color: "var(--fg-muted)", marginRight: 6, fontSize: 9, letterSpacing: "0.04em", textTransform: "uppercase" }}>Bedingungen</span>
      <span style={{ color: "var(--fg)" }}>{conditions}</span>
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
            fontSize: 10,
          }}
        >
          {molecule.name || "?"}
        </div>
      )}
      {molecule.name && (
        <div
          style={{
            fontSize: 11,
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
  const name = data.name || null;

  return (
    <div style={{ padding: "8px 0" }}>
      {name && <SectionHeader title={name} />}
      <div
        style={{
          borderRadius: "var(--radius-md)",
          boxShadow: "var(--shadow-card)",
          background: "var(--bg-alt)",
          overflow: "hidden",
        }}
      >
        <ConditionsCaption conditions={conditions} />
        <ScaledRow>
          {reactants.length > 0 && <MoleculeGroup molecules={reactants} />}
          <ReactionArrow />
          {products.length > 0 && <MoleculeGroup molecules={products} />}
        </ScaledRow>
      </div>
    </div>
  );
}
