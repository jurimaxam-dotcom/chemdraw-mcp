import React, { useLayoutEffect, useMemo, useRef, useState } from "react";
import SectionHeader from "./components/SectionHeader";
import Tabs from "./components/Tabs";
import ExportPngButton from "./components/ExportPngButton";
import PanelFooter from "./components/PanelFooter";
import ContinueRow from "./components/ContinueRow";
import { hostCan, useModelContextReport } from "./ModelContext";
import { useAppBridge } from "./AppContext";
import { mechanismFollowUps } from "./utils/followUps.js";
import { mechanismContext } from "./utils/modelContext.js";
import { composeSvg } from "./utils/composeSvg";
import { naturalHeight, naturalWidth } from "./utils/svgSize";
import { overviewLayout, ARROW_H, ARROW_W, TILE_PAD } from "./utils/mechanismLayout.js";

// Lesbare Angabe der Familie für den Untertitel (Etappe 5: vorher stand dort der Rohwert „sn2“).
const FAMILY_LABEL = { sn2: "SN2", sn1: "SN1", fischer_ester: "Fischer esterification" };

/** „SN1 · 3 steps“ — die Familie nur, wenn der Titel sie nicht schon nennt. */
export function mechanismSubtitle(data, total) {
  const label = FAMILY_LABEL[data.reaction_type];
  const named = label && String(data.name || "").toLowerCase().includes(label.toLowerCase());
  return [label && !named ? label : null, `${total} step${total === 1 ? "" : "s"}`,
    data.reversible ? "each step an equilibrium" : null].filter(Boolean).join(" · ");
}

function StepIndicator({ current, total, onStepClick }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        marginTop: 8,
      }}
    >
      {Array.from({ length: total }, (_, i) => (
        <button
          key={i}
          type="button"
          aria-label={`Step ${i + 1}`}
          aria-current={current === i ? "step" : undefined}
          onClick={() => onStepClick(i)}
          style={{
            width: current === i ? 10 : 6,
            height: current === i ? 10 : 6,
            borderRadius: "50%",
            border: "none",
            background: current === i ? "var(--accent)" : "var(--border)",
            cursor: "pointer",
            padding: 0,
            transition: "all 0.15s",
          }}
        />
      ))}
    </div>
  );
}

// Pfeil zwischen zwei Schritten: in einer Zeile waagrecht, zwischen zwei Zeilen senkrecht.
// reversible (Fischer): jeder Schritt ist ein Gleichgewicht — zwei Halbpfeile ⇌ statt eines
// einfachen Pfeils (Etappe E2). Maße wie ARROW_W/ARROW_H in utils/mechanismLayout.js.
function StepArrow({ reversible, down = false }) {
  const stroke = { stroke: "var(--fg-muted)", strokeWidth: 1.5, fill: "none" };
  return (
    <div
      data-arrow={reversible ? "equilibrium" : "forward"}
      data-arrow-dir={down ? "down" : "right"}
      title={reversible ? "equilibrium" : undefined}
      style={{ display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
        width: down ? "100%" : ARROW_W, height: down ? ARROW_H : undefined }}
    >
      {down ? (
        reversible ? (
          <svg width="20" height="26" viewBox="0 0 20 26">
            <line x1="7" y1="2" x2="7" y2="23" {...stroke} />
            <polyline points="3,17 7,23" {...stroke} />
            <line x1="13" y1="3" x2="13" y2="24" {...stroke} />
            <polyline points="17,9 13,3" {...stroke} />
          </svg>
        ) : (
          <svg width="20" height="26" viewBox="0 0 20 26">
            <line x1="10" y1="2" x2="10" y2="16" {...stroke} />
            <polygon points="6,16 10,24 14,16" fill="var(--fg-muted)" />
          </svg>
        )
      ) : reversible ? (
        <svg width="26" height="20" viewBox="0 0 26 20">
          <line x1="2" y1="7" x2="23" y2="7" {...stroke} />
          <polyline points="17,3 23,7" {...stroke} />
          <line x1="3" y1="13" x2="24" y2="13" {...stroke} />
          <polyline points="9,17 3,13" {...stroke} />
        </svg>
      ) : (
        <svg width="26" height="20" viewBox="0 0 26 20">
          <line x1="2" y1="10" x2="16" y2="10" {...stroke} />
          <polygon points="16,6 24,10 16,14" fill="var(--fg-muted)" />
        </svg>
      )}
    </div>
  );
}

function StepTile({ step, index, scale, onStepClick }) {
  const w = naturalWidth(step.svg) || 300;
  const h = naturalHeight(step.svg) || 200;
  const caption = step.is_transition_state ? `[${step.label}]‡` : step.label;
  return (
    <div
      role="button"
      tabIndex={0}
      className="mech-tile"
      aria-label={`Open step ${index + 1}: ${step.label}`}
      onClick={() => onStepClick(index)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onStepClick(index);
        }
      }}
      style={{ padding: TILE_PAD, width: Math.round(w * scale) + 2 * TILE_PAD }}
    >
      <div
        className="mech-tile-svg"
        dangerouslySetInnerHTML={{ __html: step.svg }}
        style={{ width: Math.round(w * scale), height: Math.round(h * scale) }}
      />
      <div className={step.is_transition_state ? "mech-tile-caption is-ts" : "mech-tile-caption"} title={caption}>
        {caption}
      </div>
    </div>
  );
}

// Übersicht (Etappe 5): Zeilen aus Schritten mit Pfeilen dazwischen, so wenige Zeilen wie die
// Breite in lesbarer Größe erlaubt (utils/mechanismLayout.js). Kein eigener Rollbereich:
// passt es nicht in die Höhe, wächst das Panel.
function OverviewMode({ steps, reversible, layout, onStepClick }) {
  return (
    <div className="mech-overview" data-rows={layout.rows.length}>
      {layout.rows.map((row, r) => (
        <React.Fragment key={r}>
          {r > 0 && <StepArrow reversible={reversible} down />}
          <div className="mech-overview-row">
            {row.map((i, k) => (
              <React.Fragment key={i}>
                {k > 0 && <StepArrow reversible={reversible} />}
                <StepTile step={steps[i]} index={i} scale={layout.scale} onStepClick={onStepClick} />
              </React.Fragment>
            ))}
          </div>
        </React.Fragment>
      ))}
    </div>
  );
}

function StepMode({ steps, currentStep: wantedStep, setCurrentStep }) {
  // Begrenzen: ein Index jenseits der Liste ließ das ganze Panel weiß werden.
  const currentStep = Math.min(Math.max(0, wantedStep), steps.length - 1);
  const step = steps[currentStep];
  const total = steps.length;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 8,
        flex: 1,
        minHeight: 0,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexShrink: 0,
        }}
      >
        <button
          onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
          disabled={currentStep === 0}
          style={{
            background: "none",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm, 6px)",
            color: currentStep === 0 ? "var(--border)" : "var(--fg-muted)",
            cursor: currentStep === 0 ? "default" : "pointer",
            padding: "4px 10px",
            fontSize: 11,
            fontFamily: "var(--font)",
          }}
        >
          ← Back
        </button>
        <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>
          Step {currentStep + 1} / {total}
        </div>
        <button
          onClick={() => setCurrentStep(Math.min(total - 1, currentStep + 1))}
          disabled={currentStep === total - 1}
          style={{
            background: "none",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm, 6px)",
            color: currentStep === total - 1 ? "var(--border)" : "var(--fg-muted)",
            cursor: currentStep === total - 1 ? "default" : "pointer",
            padding: "4px 10px",
            fontSize: 11,
            fontFamily: "var(--font)",
          }}
        >
          Next →
        </button>
      </div>

      <div
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: step.is_transition_state ? "var(--accent)" : "var(--fg)",
          textAlign: "center",
        }}
      >
        {step.is_transition_state ? `[${step.label}]‡` : step.label}
      </div>

      <div
        className="mech-step-svg"
        dangerouslySetInnerHTML={{ __html: step.svg }}
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          flex: 1,
          minHeight: 0,
        }}
      />
      <style>{`.mech-step-svg svg { width: 100%; height: 100%; max-width: 100%; max-height: 100%; }`}</style>

      <StepIndicator
        current={currentStep}
        total={total}
        onStepClick={setCurrentStep}
      />
    </div>
  );
}

// Export folgt der Ansicht: im Schrittmodus der gezeigte Schritt, in der Übersicht alle
// Schritte untereinander mit Pfeilen (eine Spalte — das Panel ordnet sie seit Etappe 5 in
// Zeilen nach der Breite, die Datei bleibt davon unabhängig).
function overviewSvg(steps, reversible) {
  const parts = [];
  steps.forEach((step, i) => {
    if (i > 0) parts.push({ kind: "arrow", reversible });
    parts.push({ kind: "svg", svg: step.svg, caption: step.is_transition_state ? `[${step.label}]‡` : step.label });
  });
  return composeSvg(parts, { direction: "column", gap: 6 });
}

const STAGE_PAD = 12;

export default function MechanismView({ data }) {
  const steps = data.steps || [];
  const [mode, setMode] = useState(data.current_step === 0 ? "overview" : "step");
  const [currentStep, setCurrentStep] = useState(
    data.current_step > 0 ? data.current_step - 1 : 0
  );
  const { flush } = useModelContextReport(mechanismContext(data, { mode, step: currentStep }), data.name || "mechanism");
  // Die Weiter-Zeile (U3) sitzt in der festen Höhe: um sie wächst das Panel,
  // damit die Schrittkarte nicht schrumpft.
  const withRow = hostCan(useAppBridge(), "message");
  const chatHeight = withRow ? 680 : 540;  // intrinsisch — der Host bemisst das iframe am Inhalt

  // Übersicht (Etappe 5): Platz der Bühne messen — Breite direkt, Höhe als Panelhöhe minus
  // alles außer der Bühne. Beides hängt nicht vom Inhalt der Übersicht ab, deshalb kann die
  // Aufteilung das Maß nicht zurückverändern (keine Mess-Schleife).
  const panelRef = useRef(null);
  const stageRef = useRef(null);
  const [box, setBox] = useState({ width: 0, height: 0 });
  const sizes = useMemo(
    () => steps.map((s) => ({ w: naturalWidth(s.svg) || 300, h: naturalHeight(s.svg) || 200 })),
    [steps]
  );
  useLayoutEffect(() => {
    const panel = panelRef.current;
    const stage = stageRef.current;
    if (mode !== "overview" || !panel || !stage || typeof ResizeObserver === "undefined") return undefined;
    const measure = () => {
      let total = chatHeight;
      if (document.documentElement.hasAttribute("data-host-height")) {
        const cs = getComputedStyle(document.body);
        total = window.innerHeight - (parseFloat(cs.paddingTop) || 0) - (parseFloat(cs.paddingBottom) || 0);
      }
      const rest = panel.getBoundingClientRect().height - stage.getBoundingClientRect().height;
      const width = Math.floor(stage.clientWidth - 2 * STAGE_PAD);
      const height = Math.floor(total - rest - 2 * STAGE_PAD);
      setBox((b) => (b.width === width && b.height === height ? b : { width, height }));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(panel);
    ro.observe(stage);
    return () => ro.disconnect();
  }, [mode, chatHeight]);
  const layout = useMemo(() => overviewLayout(sizes, box.width, box.height), [sizes, box]);
  const grows = mode === "overview" && layout.overflow;

  if (steps.length === 0) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No steps available.
      </div>
    );
  }

  return (
    <div
      ref={panelRef}
      className="mechanism-panel"
      style={{
        // Feste Höhe im Chat; nur eine Übersicht, die lesbar nicht hineinpasst, macht das Panel höher.
        height: grows ? "auto" : chatHeight,
        "--mech-min-h": `${chatHeight}px`,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        padding: "8px 12px",
      }}
    >
      <SectionHeader
        title={data.name || "Mechanismus"}
        subtitle={mechanismSubtitle(data, steps.length)}
        className="mech-header"
        expand
        actions={<Tabs label="Mechanism view" value={mode} onChange={setMode}
          tabs={[{ key: "overview", label: "Overview" }, { key: "step", label: "Step by step" }]} />}
      />

      {(data.notes || []).map((note, i) => (
        <div
          key={i}
          className="mech-note"
          style={{
            fontSize: 11,
            color: "var(--fg-muted)",
            borderLeft: "2px solid var(--accent)",
            padding: "2px 8px",
            marginBottom: 6,
            flexShrink: 0,
          }}
        >
          {note}
        </div>
      ))}

      <div
        ref={stageRef}
        className="mech-stage"
        data-mode={mode}
        style={{
          background: "var(--bg-alt)",
          borderRadius: "var(--radius, 10px)",
          boxShadow: "var(--shadow)",
          padding: STAGE_PAD,
          // Step-Modus füllt die feste Fläche; die Übersicht ist nie kleiner als ihr Inhalt
          // und rollt nie selbst (Etappe 5: vorher eigener Rollbalken in der Karte).
          flex: mode === "step" ? "1 1 0" : "1 0 auto",
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: mode === "step" ? undefined : "center",
          overflow: "hidden",
        }}
      >
        {mode === "overview" ? (
          <OverviewMode steps={steps} reversible={!!data.reversible} layout={layout}
            onStepClick={(i) => { setCurrentStep(i); setMode("step"); }} />
        ) : (
          <StepMode
            steps={steps}
            currentStep={currentStep}
            setCurrentStep={setCurrentStep}
          />
        )}
      </div>
      <ContinueRow actions={mechanismFollowUps(data, { mode, step: currentStep })} flush={flush} />
      {/* Fußzeile (E3): der Server schreibt für Mechanismen keine Datei — nur die Aktion. */}
      <PanelFooter>
        <ExportPngButton size="sm" filename={data.name || "mechanism"}
          getSvg={() => (mode === "step" ? steps[currentStep]?.svg : overviewSvg(steps, !!data.reversible))} />
      </PanelFooter>
    </div>
  );
}
