import React from "react";
import FoundAs from "./FoundAs";

// Kopf der Views ohne eigenen panel-header. `actions` (Reiter, Expand) stehen rechts
// oben, an derselben Stelle wie im Molekül-Panel (Etappe 3); ohne actions bleibt es
// die bloße Überschrift wie bisher.
export default function SectionHeader({ title, subtitle, foundAs, actions, className = "" }) {
  const heading = <div className="panel-heading"><h2 className="panel-title">{title}</h2>{subtitle && <p className="panel-subtitle">{subtitle}</p>}<FoundAs value={foundAs} /></div>;
  if (!actions) return heading;
  return <div className={["section-header", className].filter(Boolean).join(" ")}>{heading}<div className="panel-actions">{actions}</div></div>;
}
