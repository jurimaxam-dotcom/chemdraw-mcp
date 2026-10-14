import React from "react";

export default function FunctionalGroupList({ groups, hoveredGroup, onHoverGroup }) {
  if (!groups?.length) return null;
  return <div className="functional-groups">
    {groups.map((g, i) => <button key={i} type="button" className="functional-group"
      aria-pressed={hoveredGroup === g.name}
      onMouseEnter={() => onHoverGroup(g.name)} onMouseLeave={() => onHoverGroup(null)}
      onFocus={() => onHoverGroup(g.name)} onBlur={() => onHoverGroup(null)}
      onClick={() => onHoverGroup(g.name)}>
      <span className="group-dot" style={{ background: g.color }} aria-hidden="true" />
      <span>{g.name}</span><span className="group-count">{g.count}</span>
    </button>)}
  </div>;
}
