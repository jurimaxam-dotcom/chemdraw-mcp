import React, { useRef, useState, useLayoutEffect, useCallback } from "react";
import ExportPngButton from "./components/ExportPngButton";
import ExpandButton, { useCanExpand } from "./components/ExpandButton";
import { fileEntries } from "./components/PanelFooter";
import { Button, Hint, Icon, Panel, PanelFoot, PanelHead, Stage } from "./components/Panel";
import ContinueRow from "./components/ContinueRow";
import { useModelContextReport } from "./ModelContext";
import { reactionFollowUps } from "./utils/followUps.js";
import { reactionContext } from "./utils/modelContext.js";
import { composeSvg } from "./utils/composeSvg";
import { useAppBridge } from "./AppContext";
import { loadToolData } from "./utils/toolData";
import { naturalHeight, naturalWidth } from "./utils/svgSize";

export const APPLY_ERROR = "The coefficients could not be applied. Click again to retry.";

const MIN_SCALE = 0.4;
// Große Stoffe (E16, 10.11.2026, z. B. Porphyrine): der Server zeichnet sie im festen
// Bindungsmaßstab auf eine größere Fläche statt sie auf 250×200 zu quetschen. Eine
// Zeile aus zwei Porphyrinen ist dann ~1000 px breit; auf Panelbreite geschrumpft
// wären N/O-Labels wieder < 9 px. Solche Reaktionen stapeln Edukte | Pfeil | Produkte,
// statt unter READABLE_SCALE zu schrumpfen. Kleine Reaktionen nehmen diesen Weg nie.
const READABLE_SCALE = 0.85; // N-Glyphe 10,6 px × 0,85 ≈ 9 px
// Was auf RDKits 250×200-Fläche passt, ist nach dem Zuschnitt höchstens 250+2·22 breit
// bzw. 200+2·22 hoch (svg_renderer.SVG_PADDING) — alles darüber kam von der größeren Fläche.
// Kleine Reaktionen stapeln unter diesem Maßstab (Panel-Umbau 17.11.2026): ohne die alten 16-px-Polster
// lag die Veresterung im 320-px-Seitenpanel bei 0,44 knapp über MIN_SCALE — Namen um 6 px, unlesbar.
const STACK_SCALE = 0.5;

/** Stapeln statt nebeneinander? rowW = Zeilenbreite mit waagrechtem Pfeil. */
export function shouldStack(containerW, rowW, canStack = false) {
  return rowW > 0 && containerW / rowW < (canStack ? READABLE_SCALE : STACK_SCALE);
}

const LARGE_W = 294;
const LARGE_H = 244;

function isLarge(molecule) {
  return (naturalWidth(molecule.svg) ?? 0) > LARGE_W || (naturalHeight(molecule.svg) ?? 0) > LARGE_H;
}

// Pfeilformen im 110×18-Raster. Vorwaerts bleibt der bisherige Pfeil;
// Gleichgewicht = zwei Halbpfeile (⇌), Retro = Doppelschaft mit offener Spitze (⇒).
// Farbe über currentColor: das SVG trägt die Klasse rxn-arrow (b-graphics.css, --text-2).
function ArrowGlyph({ kind }) {
  const stroke = "currentColor";
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
    <div className="rxn-conditions" data-conditions={position}>
      {text}
    </div>
  );
}

// Gestapelt (große Stoffe): Pfeil nach unten, Bedingungen rechts daneben.
function VerticalArrow({ kind, above, below }) {
  return (
    <div data-arrow-layout="vertical"
      style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", flexShrink: 0 }}>
      <div style={{ position: "relative", width: 18, height: 64, flexShrink: 0 }}>
        {/* 64×18 um die Mitte gedreht: Mittelpunkt (32,9) → (9,32) */}
        <svg className="rxn-arrow" data-arrow={kind} width="64" height="18" viewBox="0 0 110 18" preserveAspectRatio="none"
          style={{ position: "absolute", left: -23, top: 23, transform: "rotate(90deg)", maxWidth: "none" }}>
          <ArrowGlyph kind={kind} />
        </svg>
      </div>
      {(above || below) && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
          <ArrowText text={above} position="above" />
          <ArrowText text={below} position="below" />
        </div>
      )}
    </div>
  );
}

// Pfeilspalte: Bedingungen oben ueber, unten unter dem Pfeil — wie im
// exportierten Bild und im CDXML.
function ReactionArrow({ kind, above, below, vertical = false }) {
  const known = ["forward", "equilibrium", "retro"].includes(kind) ? kind : "forward";
  if (vertical) return <VerticalArrow kind={known} above={above} below={below} />;
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
        className="rxn-arrow"
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
  return <div className="rxn-plus">+</div>;
}

// Stoechiometrischer Koeffizient vor dem Molekuel; 1 schreibt niemand hin.
function Coefficient({ value }) {
  if (!value || value === 1) return null;
  return (
    <div className="rxn-coefficient" data-coefficient>
      {value}
    </div>
  );
}

function MoleculeCard({ molecule }) {
  return (
    <>
    <Coefficient value={molecule.coefficient} />
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
        <div className="rxn-missing">
          {molecule.name || "?"}
        </div>
      )}
      {molecule.name && (
        <div className="rxn-name">
          {molecule.name}
        </div>
      )}
    </div>
    </>
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

// Zuschlag, um den der waagrechte Pfeil breiter wäre als der gerade gezeigte (0, wenn er
// schon waagrecht steht): max(110, Textbreite) + 2·12 Polster gegen die senkrechte Breite.
function horizontalArrowExtra(inner) {
  const arrow = inner.querySelector('[data-arrow-layout="vertical"]');
  if (!arrow) return 0;
  const text = Math.max(0, ...[...arrow.querySelectorAll("[data-conditions]")].map((el) => el.offsetWidth));
  return Math.max(110, text) + 24 - arrow.offsetWidth;
}

function ScaledRow({ children, canStack = false }) {
  const outerRef = useRef(null);
  const innerRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [naturalH, setNaturalH] = useState(0);
  const [stacked, setStacked] = useState(false);

  const measure = useCallback(() => {
    const outer = outerRef.current;
    const inner = innerRef.current;
    if (!outer || !inner) return;
    // Bühne ohne Polster (Panel-Umbau 17.11.2026, vorher 16 px je Seite in der gefüllten Karte).
    const containerW = outer.clientWidth;
    // Restore the actual value afterwards — setting "" here clears React's
    // inline style, and a state bailout (same scale) would never re-render
    // to put it back, leaving the row permanently unscaled.
    const prevTransform = inner.style.transform;
    // Auch die Breite neutral messen (Fund c, 09.11.): geschrumpft trägt die
    // Zeile width = 100/scale %, und scrollWidth ist nie kleiner als die
    // eigene Breite — das Verhältnis kam als alter Maßstab zurück, die Zeile
    // wuchs nach dem Verbreitern nie zurück (gemessen: 0.67 → 0.45 → 0.40).
    const prevWidth = inner.style.width;
    inner.style.transform = "none";
    inner.style.width = "max-content";
    let naturalW = inner.scrollWidth;
    let naturalHeight = inner.scrollHeight;
    // Gestapelt wird nur gemessen, wenn die Zeile nebeneinander unter die Lesegrenze fiele —
    // die Zeilenbreite muss dafür im Zeilenmodus gemessen werden, egal wie gerade gezeigt.
    let stack = false;
    // Kleine Reaktionen stapeln erst unter STACK_SCALE (U2: Seitenpanel bis ~320 px breit), große unter READABLE_SCALE.
    {
      const prevDir = inner.style.flexDirection;
      inner.style.flexDirection = "row";
      // Beide Zustände entscheiden über dieselbe Zahl: die Zeilenbreite mit WAAGRECHTEM Pfeil.
      // Gestapelt ist der Pfeil senkrecht und ~116 px schmaler — mit ihm gemessen stimmte
      // jeder Zustand für den anderen, die Ansicht pendelte (Host-Test, Breitenband).
      const rowW = inner.scrollWidth + horizontalArrowExtra(inner);
      if (shouldStack(containerW, rowW, canStack)) {
        inner.style.flexDirection = "column";
        stack = true;
        naturalW = inner.scrollWidth;
        naturalHeight = inner.scrollHeight;
      } else {
        naturalW = rowW;
        naturalHeight = inner.scrollHeight;
      }
      inner.style.flexDirection = prevDir;
    }
    inner.style.transform = prevTransform;
    inner.style.width = prevWidth;
    if (naturalW <= 0) return;
    // Cap at 1: never blow small reactions up beyond their chemical scale —
    // only shrink-to-fit. Below MIN_SCALE the row stacks (U2); only a stacked row
    // still wider than that scrolls.
    setScale(Math.min(1, Math.max(MIN_SCALE, containerW / naturalW)));
    setNaturalH(naturalHeight);
    setStacked(stack);
  }, [canStack]);

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
    <Stage
      ref={outerRef}
      className="rxn-stage"
      data-scroll={needsScroll || undefined}
      style={{ height: scaledH !== undefined ? Math.ceil(scaledH) : undefined }}
    >
      <div
        ref={innerRef}
        data-stacked={stacked || undefined}
        style={{
          display: "flex",
          flexDirection: stacked ? "column" : "row",
          alignItems: "center",
          gap: 4,
          transformOrigin: "top left",
          transform: needsScroll ? "none" : `scale(${scale})`,
          width: needsScroll ? undefined : `${100 / scale}%`,
        }}
      >
        {typeof children === "function" ? children(stacked) : children}
      </div>
    </Stage>
  );
}

// Stoffbilanz der gezeichneten Gleichung (Spezifikation §5.6). Ausgeglichen: Text mit Häkchen.
// Sonst ein Warnhinweis mit Befund und Vorschlag — der Vorschlag ist nicht gezeichnet, die
// Zeichnung bleibt —, daneben „Apply coefficients“ und nach dem Übernehmen „Undo“.
function BalanceRow({ balance, onApply, onUndo, applying, failed }) {
  if (!balance) return null;
  const ok = Boolean(balance.balanced);
  const state = ok ? "balanced" : "unbalanced";
  return (
    <div className="balance-row" role="note" title={balance.note || undefined}>
      {ok ? (
        <span className="balance-badge balance-ok" data-testid="balance-badge" data-state={state}>
          <Icon name="check" />balanced
        </span>
      ) : (
        <Hint tone="warn" className="balance-hint">
          <span className="balance-badge balance-off" data-testid="balance-badge" data-state={state}>
            {`not balanced: ${balance.summary || ""}`}
          </span>
          {balance.suggestedEquation && (
            <>
              {" · "}
              <span className="balance-badge balance-suggest" data-testid="balance-suggestion">
                {`suggested: ${balance.suggestedEquation}`}
              </span>
            </>
          )}
        </Hint>
      )}
      {!ok && onApply && balance.suggestedCoefficients && (
        <Button onClick={onApply} disabled={applying} aria-busy={applying || undefined}
          title="Redraw the equation with the suggested coefficients">
          Apply coefficients
        </Button>
      )}
      {onUndo && (
        <Button onClick={onUndo} title="Show the equation as it was drawn first">Undo</Button>
      )}
      {failed && <span className="balance-error" role="status">{APPLY_ERROR}</span>}
    </div>
  );
}

// Export PNG braucht ein SVG; das Panel zeichnet die Gleichung aber aus
// Einzel-SVGs und HTML. Dieselbe Zeile als ein Dokument: Strukturen mit Namen,
// „+“, Koeffizienten, Pfeil mit Bedingungen oben und unten.
export function reactionSvg(data) {
  const parts = [];
  const side = (molecules) => molecules.forEach((m, i) => {
    if (i > 0) parts.push({ kind: "text", text: "+" });
    if (m.coefficient && m.coefficient !== 1) parts.push({ kind: "text", text: String(m.coefficient) });
    parts.push(m.svg ? { kind: "svg", svg: m.svg, caption: m.name } : { kind: "text", text: m.name || "?", size: 14 });
  });
  side(data.reactants || []);
  parts.push({ kind: "arrow", arrow: data.arrow, above: data.conditions, below: data.conditions_below });
  side(data.products || []);
  return composeSvg(parts);
}

export default function ReactionView({ data: initial }) {
  const app = useAppBridge();
  // Nach „Apply coefficients“ zeigt das Panel die neu gezeichnete Gleichung.
  const [applied, setApplied] = useState(null);
  const [applying, setApplying] = useState(false);
  const [failed, setFailed] = useState(false);
  const data = applied || initial;
  const { flush } = useModelContextReport(reactionContext(data), data.name || "reaction");
  const canExpand = useCanExpand();
  const handleUndo = useCallback(() => {
    setApplied(null);
    setFailed(false);
  }, []);

  const handleApply = useCallback(async () => {
    const coefficients = data.balance?.suggestedCoefficients;
    if (applying || !coefficients || !data.request) return;
    setApplying(true);
    setFailed(false);
    try {
      if (!app?.callServerTool) throw new Error("keine App-Bruecke");
      const result = await app.callServerTool({
        name: "generate_reaction",
        arguments: { ...data.request, coefficients },
      });
      const payload = await loadToolData(app, result);
      if (!payload || payload.type !== "reaction") throw new Error("kein Reaktions-Payload");
      setApplied(payload);
    } catch {
      setFailed(true);
    } finally {
      setApplying(false);
    }
  }, [app, applying, data]);

  const reactants = data.reactants || [];
  const products = data.products || [];
  const conditions = data.conditions || null;
  const conditionsBelow = data.conditions_below || null;
  const name = data.name || null;

  return (
    <Panel kind="reaction" className="reaction-panel">
      <PanelHead title={name} expand={canExpand ? <ExpandButton /> : null} />
      <ScaledRow canStack={[...reactants, ...products].some(isLarge)}>
        {(stacked) => (
          <>
            {reactants.length > 0 && <MoleculeGroup molecules={reactants} />}
            <ReactionArrow kind={data.arrow} above={conditions} below={conditionsBelow} vertical={stacked} />
            {products.length > 0 && <MoleculeGroup molecules={products} />}
          </>
        )}
      </ScaledRow>
      <BalanceRow balance={data.balance} onApply={data.request ? handleApply : null}
        onUndo={applied ? handleUndo : null} applying={applying} failed={failed} />
      {/* Fuß (E3): Dateien und Export folgen der gezeigten Gleichung (nach Apply die neue). */}
      <ContinueRow actions={reactionFollowUps(data)} flush={flush} />
      <PanelFoot files={fileEntries(data.files)}>
        {(reactants.length > 0 || products.length > 0) &&
          <ExportPngButton size="sm" getSvg={() => reactionSvg(data)} filename={name || "reaction"} />}
      </PanelFoot>
    </Panel>
  );
}
