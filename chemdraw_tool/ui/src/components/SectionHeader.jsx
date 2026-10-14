import React from "react";
export default function SectionHeader({ title, subtitle }) {
  return <div className="panel-heading"><h2 className="panel-title">{title}</h2>{subtitle && <p className="panel-subtitle">{subtitle}</p>}</div>;
}
