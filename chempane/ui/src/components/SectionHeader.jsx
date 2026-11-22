import React from "react";
import FoundAs from "./FoundAs";
import ExpandButton, { useCanExpand } from "./ExpandButton";

// Kopf der Views ohne eigenen panel-header. `actions` (Reiter) und — mit `expand` — der
// Expand-Knopf stehen rechts oben, an derselben Stelle wie im Molekül-Panel (Etappe 3).
// Ohne beides bleibt es die bloße Überschrift wie bisher (keine zusätzliche Höhe).
export default function SectionHeader({ title, subtitle, foundAs, actions, expand = false, className = "" }) {
  const canExpand = useCanExpand() && expand;
  const heading = (title || subtitle) ? <div className="panel-heading">{title && <h2 className="panel-title">{title}</h2>}{subtitle && <p className="panel-subtitle">{subtitle}</p>}<FoundAs value={foundAs} /></div> : null;
  if (!actions && !canExpand) return heading;
  return <div className={["section-header", className].filter(Boolean).join(" ")}>
    {heading || <div className="panel-heading" />}
    <div className="panel-actions">{actions}{canExpand && <ExpandButton />}</div>
  </div>;
}
