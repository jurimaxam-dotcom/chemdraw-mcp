import React, { useState } from "react";
import SectionHeader from "./components/SectionHeader";

function CalcStep({ step }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      style={{
        padding: "8px 10px",
        background: step.is_outlier ? "rgba(220,38,38,0.08)" : "var(--bg-alt)",
        borderRadius: 6,
        borderLeft: step.is_outlier
          ? "3px solid #dc2626"
          : "3px solid transparent",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          cursor: "pointer",
        }}
        onClick={() => setOpen(!open)}
      >
        <span
          style={{
            fontWeight: 600,
            fontSize: 12,
            textDecoration: step.is_outlier ? "line-through" : "none",
            color: step.is_outlier ? "#dc2626" : "var(--fg)",
          }}
        >
          {step.label}
        </span>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            fontWeight: 600,
            color: step.is_outlier ? "#dc2626" : "var(--accent)",
          }}
        >
          {step.result}
        </span>
      </div>
      {open && (
        <div style={{ marginTop: 8, fontSize: 11 }}>
          <div style={{ color: "var(--fg-muted)", marginBottom: 2 }}>Formel:</div>
          <div style={{ fontFamily: "var(--font-mono)", marginBottom: 6 }}>
            {step.formula}
          </div>
          <div style={{ color: "var(--fg-muted)", marginBottom: 2 }}>
            Eingesetzt:
          </div>
          <div style={{ fontFamily: "var(--font-mono)", marginBottom: 6 }}>
            {step.substitution}
          </div>
          {step.explanation && (
            <div style={{ color: "var(--fg-muted)", fontStyle: "italic" }}>
              {step.explanation}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TestResult({ label, value, critical, passed, explanation }) {
  return (
    <div
      style={{
        padding: "8px 10px",
        borderRadius: 6,
        border: `1px solid ${passed ? "#16a34a" : "#dc2626"}`,
        background: passed ? "rgba(22,163,74,0.06)" : "rgba(220,38,38,0.06)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span style={{ fontSize: 12, fontWeight: 600 }}>{label}</span>
        <span style={{ fontSize: 13 }}>{passed ? "✅" : "❌"}</span>
      </div>
      <div
        style={{ fontFamily: "var(--font-mono)", fontSize: 11, marginTop: 4 }}
      >
        {typeof value === "number" ? value.toFixed(3) : value}
        {" < "}
        {typeof critical === "number" ? critical.toFixed(3) : critical}
      </div>
      {explanation && (
        <div style={{ fontSize: 10, color: "var(--fg-muted)", marginTop: 4 }}>
          {explanation}
        </div>
      )}
    </div>
  );
}

function StatBox({ label, value, unit }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: 10, color: "var(--fg-muted)" }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 600, fontFamily: "var(--font-mono)" }}>
        {typeof value === "number" ? value.toFixed(2) : value}
        {unit && (
          <span style={{ fontSize: 10, fontWeight: 400, color: "var(--fg-muted)" }}>
            {" "}{unit}
          </span>
        )}
      </div>
    </div>
  );
}

function MethodSection({ method }) {
  const [open, setOpen] = useState(true);
  return (
    <div style={{ marginBottom: 12 }}>
      <div
        onClick={() => setOpen(!open)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          cursor: "pointer",
          padding: "6px 0",
        }}
      >
        <span style={{ fontSize: 10, color: "var(--fg-muted)" }}>
          {open ? "▼" : "▶"}
        </span>
        <span style={{ fontSize: 13, fontWeight: 600 }}>{method.name}</span>
      </div>
      {open && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {method.gehalt_steps.map((step, i) => (
            <CalcStep key={i} step={step} />
          ))}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 8,
              padding: "10px 0",
              borderTop: "1px solid var(--border)",
              marginTop: 4,
            }}
          >
            <StatBox label="Mittelwert" value={method.mean} unit="%" />
            <StatBox label="s_rel" value={method.std_rel} unit="%" />
            <StatBox label="WFR" value={method.recovery} unit="%" />
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 8,
              paddingBottom: 8,
            }}
          >
            <StatBox label="s_abs" value={method.std_abs} unit="%" />
            <StatBox label="Varianz" value={method.variance} unit="%²" />
            <StatBox label="rel. Abw." value={method.rel_deviation} unit="%" />
          </div>
          <TestResult
            label="Einstichproben-t-Test"
            value={method.t_test_value}
            critical={method.t_test_critical}
            passed={method.t_test_passed}
            explanation={method.t_test_explanation}
          />
        </div>
      )}
    </div>
  );
}

export default function ValidationView({ data }) {
  return (
    <div>
      <SectionHeader
        title={`Validierung: ${data.substance}`}
        subtitle={`Variante ${data.variante} — Wahrer Wert: ${data.wahrer_wert} %`}
      />
      <MethodSection method={data.method_a} />
      <MethodSection method={data.method_b} />
      <div style={{ marginTop: 8 }}>
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
          Methodenvergleich
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <TestResult
            label="F-Test (Varianzen)"
            value={data.comparison.f_test_value}
            critical={data.comparison.f_test_critical}
            passed={data.comparison.f_test_passed}
            explanation={data.comparison.f_test_explanation}
          />
          <TestResult
            label="Welch-t-Test (Mittelwerte)"
            value={data.comparison.t_test_value}
            critical={data.comparison.t_test_critical}
            passed={data.comparison.t_test_passed}
            explanation={data.comparison.t_test_explanation}
          />
          <div
            style={{
              padding: "10px 12px",
              borderRadius: 6,
              background:
                data.comparison.f_test_passed && data.comparison.t_test_passed
                  ? "rgba(22,163,74,0.08)"
                  : "rgba(220,38,38,0.08)",
              fontWeight: 600,
              fontSize: 12,
              textAlign: "center",
            }}
          >
            {data.comparison.result_text}
          </div>
        </div>
      </div>
    </div>
  );
}
