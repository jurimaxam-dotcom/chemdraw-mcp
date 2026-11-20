import React, { useLayoutEffect, useMemo, useRef, useState } from "react";
import Tabs from "./components/Tabs";
import ExportPngButton from "./components/ExportPngButton";
import ExpandButton, { useCanExpand } from "./components/ExpandButton";
import ContinueRow from "./components/ContinueRow";
import { Button, Hint, Icon, Panel, PanelFoot, PanelHead, PanelState, Stage, StageBar } from "./components/Panel";
import { useModelContextReport } from "./ModelContext";
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
  const count = data.reaction_type === "sn2"
    ? `One concerted step · ${total} view${total === 1 ? "" : "s"}`
    : `${total} step${total === 1 ? "" : "s"}`;
  return [label && !named ? label : null, count,
    data.reversible ? "each step an equilibrium" : null].filter(Boolean).join(" · ");
}

// Punkte je Schritt: Name „Step n“ (Tests, Probe), der gezeigte trägt aria-current. Aussehen in b-graphics.css.
function StepIndicator({ current, total, onStepClick, itemLabel }) {
  return (
    <span className="mech-dots">
      {Array.from({ length: total }, (_, i) => (
        <button
          key={i}
          type="button"
          className="mech-dot"
          aria-label={`${itemLabel} ${i + 1}`}
          aria-current={current === i ? "step" : undefined}
          onClick={() => onStepClick(i)}
        />
      ))}
    </span>
  );
}

// Pfeil zwischen zwei Schritten: in einer Zeile waagrecht, zwischen zwei Zeilen senkrecht.
// reversible (Fischer): jeder Schritt ist ein Gleichgewicht — zwei Halbpfeile ⇌ statt eines
// einfachen Pfeils (Etappe E2). Maße wie ARROW_W/ARROW_H in utils/mechanismLayout.js.
function StepArrow({ reversible, down = false }) {
  const stroke = { stroke: "currentColor", strokeWidth: 1.5, fill: "none" };
  return (
    <div
      className="mech-arrow"
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
            <polygon points="6,16 10,24 14,16" fill="currentColor" />
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
          <polygon points="16,6 24,10 16,14" fill="currentColor" />
        </svg>
      )}
    </div>
  );
}

function StepTile({ step, index, scale, onStepClick, itemLabel }) {
  const w = naturalWidth(step.svg) || 300;
  const h = naturalHeight(step.svg) || 200;
  const caption = step.is_transition_state ? `[${step.label}]‡` : step.label;
  return (
    <div
      role="button"
      tabIndex={0}
      className="mech-tile"
      aria-label={`Open ${itemLabel.toLowerCase()} ${index + 1}: ${step.label}`}
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
function OverviewMode({ steps, reversible, layout, onStepClick, itemLabel }) {
  return (
    <div className="mech-overview" data-rows={layout.rows.length}>
      {layout.rows.map((row, r) => (
        <React.Fragment key={r}>
          {r > 0 && <StepArrow reversible={reversible} down />}
          <div className="mech-overview-row">
            {row.map((i, k) => (
              <React.Fragment key={i}>
                {k > 0 && <StepArrow reversible={reversible} />}
                <StepTile step={steps[i]} index={i} scale={layout.scale} onStepClick={onStepClick} itemLabel={itemLabel} />
              </React.Fragment>
            ))}
          </div>
        </React.Fragment>
      ))}
    </div>
  );
}

// Schrittmodus (Spezifikation §5.7): Back/Next als ruhige Knöpfe mit Chevron in der StageBar,
// dazwischen Zähler „Step n / N“ (eigenes Element — test:host sucht den Text exakt), Bezeichnung
// und Punkte; darunter die Bühne ohne Karte.
function StepBar({ steps, current, setCurrentStep, itemLabel }) {
  const step = steps[current];
  const total = steps.length;
  const label = step.is_transition_state ? `[${step.label}]‡` : step.label;
  return (
    <StageBar
      className="mech-nav"
      left={(
        <>
          <Button icon="chevron-left" onClick={() => setCurrentStep(Math.max(0, current - 1))} disabled={current === 0}>
            Back
          </Button>
          <div className="mech-nav-center">
            <span className="mech-counter">{itemLabel} {current + 1} / {total}</span>
            <span className={step.is_transition_state ? "mech-step-label is-ts" : "mech-step-label"} title={label}>{label}</span>
            <StepIndicator current={current} total={total} onStepClick={setCurrentStep} itemLabel={itemLabel} />
          </div>
        </>
      )}
      right={(
        <Button className="mech-next" onClick={() => setCurrentStep(Math.min(total - 1, current + 1))} disabled={current === total - 1}>
          Next<Icon name="chevron-right" />
        </Button>
      )}
    />
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

// Höhenbudget der Übersicht im Chat (Panel-Umbau 17.11.2026): eine feste Zahl, nicht aus der
// eigenen Panelhöhe abgeleitet — das Panel ist inhaltsgroß, sonst entstünde eine Mess-Schleife.
// 440 px Bühne + Kopf, Hinweis, Continue-Zeile und Fuß bleiben unter 700 px.
export const OVERVIEW_CHAT_H = 440;

export default function MechanismView({ data }) {
  const steps = data.steps || [];
  const concerted = data.reaction_type === "sn2";
  const itemLabel = concerted ? "View" : "Step";
  const [mode, setMode] = useState(data.current_step === 0 ? "overview" : "step");
  const [currentStep, setCurrentStep] = useState(
    data.current_step > 0 ? data.current_step - 1 : 0
  );
  const { flush } = useModelContextReport(mechanismContext(data, { mode, step: currentStep }), data.name || "mechanism");
  const canExpand = useCanExpand();

  // Übersicht (Etappe 5): Platz der Bühne messen — Breite direkt; Höhe im Chat ein festes Budget,
  // in Fill (Seitenpanel, Vollbild) die Fensterhöhe minus alles außer der Bühne. Beides hängt nicht
  // vom Inhalt der Übersicht ab, deshalb kann die Aufteilung das Maß nicht zurückverändern.
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
      let height = OVERVIEW_CHAT_H;
      if (document.documentElement.hasAttribute("data-host-height")) {
        const cs = getComputedStyle(document.body);
        const total = window.innerHeight - (parseFloat(cs.paddingTop) || 0) - (parseFloat(cs.paddingBottom) || 0);
        const rest = panel.getBoundingClientRect().height - stage.getBoundingClientRect().height;
        height = Math.floor(total - rest);
      }
      const width = Math.floor(stage.clientWidth);
      setBox((b) => (b.width === width && b.height === height ? b : { width, height }));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(panel);
    ro.observe(stage);
    return () => ro.disconnect();
  }, [mode]);
  const layout = useMemo(() => overviewLayout(sizes, box.width, box.height), [sizes, box]);

  if (steps.length === 0) {
    return (
      <Panel kind="mechanism" className="mechanism-panel">
        <PanelHead title={data.name || "Mechanismus"} />
        <PanelState kind="empty" message="No steps available." />
      </Panel>
    );
  }
  // Begrenzen: ein Index jenseits der Liste ließ das ganze Panel weiß werden.
  const shown = Math.min(Math.max(0, currentStep), steps.length - 1);

  return (
    <Panel ref={panelRef} kind="mechanism" fill className="mechanism-panel" data-mode={mode}>
      <PanelHead
        title={data.name || "Mechanismus"}
        subtitle={mechanismSubtitle(data, steps.length)}
        tabs={<Tabs label="Mechanism view" value={mode} onChange={setMode}
          tabs={[{ key: "overview", label: "Overview" }, { key: "step", label: concerted ? "Views" : "Step by step" }]} />}
        expand={canExpand ? <ExpandButton /> : null}
      />
      {mode === "step" && <StepBar steps={steps} current={shown} setCurrentStep={setCurrentStep} itemLabel={itemLabel} />}
      <Stage ref={stageRef} className="mech-stage" data-mode={mode}>
        {mode === "overview" ? (
          <OverviewMode steps={steps} reversible={!!data.reversible} layout={layout} itemLabel={itemLabel}
            onStepClick={(i) => { setCurrentStep(i); setMode("step"); }} />
        ) : (
          <div className="mech-step-svg" dangerouslySetInnerHTML={{ __html: steps[shown].svg }} />
        )}
      </Stage>
      {(data.notes || []).map((note, i) => <Hint key={i} className="mech-note">{note}</Hint>)}
      <ContinueRow actions={mechanismFollowUps(data, { mode, step: currentStep })} flush={flush} />
      {/* Fuß (E3): der Server schreibt für Mechanismen keine Datei — nur die Aktion. */}
      <PanelFoot>
        <ExportPngButton size="sm" filename={data.name || "mechanism"}
          getSvg={() => (mode === "step" ? steps[shown]?.svg : overviewSvg(steps, !!data.reversible))} />
      </PanelFoot>
    </Panel>
  );
}
