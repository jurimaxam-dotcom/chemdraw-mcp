import React from "react";
import FoundAs from "./FoundAs";

export default function SectionHeader({ title, subtitle, foundAs }) {
  return <div className="panel-heading"><h2 className="panel-title">{title}</h2>{subtitle && <p className="panel-subtitle">{subtitle}</p>}<FoundAs value={foundAs} /></div>;
}
