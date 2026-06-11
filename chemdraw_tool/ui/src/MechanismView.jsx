import React, { useState } from "react";
import SectionHeader from "./components/SectionHeader";

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

function StepArrow() {
  return (
    <div style={{ display: "flex", alignItems: "center", flexShrink: 0, padding: "0 2px" }}>
      <svg width="30" height="20" viewBox="0 0 30 20">
        <line x1="2" y1="10" x2="22" y2="10" stroke="var(--fg-muted)" strokeWidth="1.5" />
        <polygon points="22,6 30,10 22,14" fill="var(--fg-muted)" />
      </svg>
    </div>
  );
}

function OverviewMode({ steps, onStepClick }) {
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        padding: 8,
      }}
    >
      {steps.map((step, i) => (
        <React.Fragment key={i}>
          {i > 0 && <StepArrow />}
          <div
            onClick={() => onStepClick(i)}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 6,
              flexShrink: 0,
              minWidth: 180,
              maxWidth: 240,
              cursor: "pointer",
              padding: 6,
              borderRadius: 8,
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
            onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
          >
            <div
              dangerouslySetInnerHTML={{ __html: step.svg }}
              style={{
                display: "flex",
                justifyContent: "center",
                width: "100%",
              }}
            />
            <div
              style={{
                fontSize: 11,
                color: step.is_transition_state ? "var(--accent)" : "var(--fg-muted)",
                textAlign: "center",
                fontWeight: step.is_transition_state ? 600 : 400,
              }}
            >
              {step.is_transition_state ? `[${step.label}]‡` : step.label}
            </div>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
}

function StepMode({ steps, currentStep, setCurrentStep }) {
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

export default function MechanismView({ data }) {
  const steps = data.steps || [];
  const [mode, setMode] = useState(data.current_step === 0 ? "overview" : "step");
  const [currentStep, setCurrentStep] = useState(
    data.current_step > 0 ? data.current_step - 1 : 0
  );

  if (steps.length === 0) {
    return (
      <div style={{ color: "var(--fg-muted)", padding: 16 }}>
        No steps available.
      </div>
    );
  }

  return (
    <div
      style={{
        height: "calc(100vh - 16px)",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        padding: "8px 12px",
      }}
    >
      <SectionHeader
        title={data.name || "Mechanismus"}
        subtitle={data.reaction_type}
      />

      <div
        style={{
          display: "flex",
          gap: 2,
          marginBottom: 8,
          background: "var(--bg-alt)",
          borderRadius: 6,
          padding: 2,
        }}
      >
        {["overview", "step"].map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            style={{
              flex: 1,
              padding: "4px 8px",
              fontSize: 11,
              fontFamily: "var(--font)",
              borderRadius: 4,
              border: "none",
              cursor: "pointer",
              background: mode === m ? "var(--bg)" : "transparent",
              boxShadow: mode === m ? "0 1px 2px rgba(0,0,0,0.1)" : "none",
              color: mode === m ? "var(--fg)" : "var(--fg-muted)",
              transition: "all 0.15s",
            }}
          >
            {m === "overview" ? "Overview" : "Step by step"}
          </button>
        ))}
      </div>

      <div
        style={{
          background: "var(--bg-alt)",
          borderRadius: "var(--radius, 10px)",
          boxShadow: "var(--shadow)",
          padding: 12,
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          // Step-Modus füllt die Fläche ohne Scroll; die Overview-Liste
          // scrollt INNERHALB der Karte, nie das ganze Panel.
          overflow: mode === "step" ? "hidden" : "auto",
        }}
      >
        {mode === "overview" ? (
          <OverviewMode steps={steps} onStepClick={(i) => { setCurrentStep(i); setMode("step"); }} />
        ) : (
          <StepMode
            steps={steps}
            currentStep={currentStep}
            setCurrentStep={setCurrentStep}
          />
        )}
      </div>
    </div>
  );
}
