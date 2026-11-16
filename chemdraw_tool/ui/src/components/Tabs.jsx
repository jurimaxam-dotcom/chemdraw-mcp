import React from "react";

// Das eine Reiter-Bauteil des Panels (Etappe 3, 16.11.2026): Struktur/Daten/Study,
// Mechanismus (Overview/Step by step), Datenblatt-Quellen (PubChem/GHS) und die
// Protein-Achsen sehen gleich aus und bedienen sich gleich. Vorher drei Macharten:
// Segment oben rechts, Vollbreite-Leiste mit inline-Styles, aria-pressed-Knöpfe.
//
// Tastatur nach WAI-ARIA „Tabs with manual activation“: nur der gewählte Reiter
// steht in der Tab-Reihenfolge; Pfeile (mit Umlauf), Home und End bewegen den Fokus,
// gewählt wird per Klick, Enter oder Leertaste (native Knöpfe). Manuell, weil der
// Data-Reiter beim Wählen das Datenblatt übers Netz holt — ein Pfeildruck soll nichts laden.
//
// size "sm" = Unter-Reiter (Datenblatt-Quellen): kleiner, sonst dieselbe Machart.
// tabs: [{ key, label, id?, controls?, busy?, title? }]
export default function Tabs({ label, tabs, value, onChange, size = "md", className = "" }) {
  function onKeyDown(e) {
    const list = [...e.currentTarget.querySelectorAll('[role="tab"]')];
    const at = list.indexOf(document.activeElement);
    if (at < 0) return;
    const next = { ArrowRight: at + 1, ArrowDown: at + 1, ArrowLeft: at - 1, ArrowUp: at - 1, Home: 0, End: list.length - 1 }[e.key];
    if (next === undefined) return;
    e.preventDefault();
    list[(next + list.length) % list.length].focus();
  }

  const cls = ["seg", size === "sm" ? "seg-sm" : "", className].filter(Boolean).join(" ");
  return (
    <div className={cls} role="tablist" aria-label={label} onKeyDown={onKeyDown}>
      {tabs.map((t) => (
        <button
          key={t.key}
          type="button"
          role="tab"
          id={t.id}
          aria-controls={t.controls}
          aria-selected={t.key === value}
          aria-busy={t.busy || undefined}
          tabIndex={t.key === value ? 0 : -1}
          title={t.title}
          onClick={() => onChange(t.key)}
        >
          {t.busy && <span className="seg-spinner" aria-hidden="true" />}
          {t.label}
        </button>
      ))}
    </div>
  );
}
