import React from "react";
import { groupInfo } from "../utils/groupInfo";

// Chips statt Liste: Hover/Fokus leuchtet die Gruppe in der Struktur an,
// GroupNote darunter nennt Name und Kurzformel. Die Zahl ist die Zahl der Gruppen.
export default function FunctionalGroupList({ groups, hoveredGroup, onHoverGroup }) {
  if (!groups?.length) return null;
  return <div className="functional-groups">
    {groups.map((g, i) => <button key={i} type="button" className="functional-group"
      style={{ "--group-color": g.color }}
      aria-pressed={hoveredGroup === g.name}
      onMouseEnter={() => onHoverGroup(g.name)} onMouseLeave={() => onHoverGroup(null)}
      onFocus={() => onHoverGroup(g.name)} onBlur={() => onHoverGroup(null)}
      onClick={() => onHoverGroup(g.name)}>
      <span className="group-dot" aria-hidden="true" />
      <span>{groupInfo(g.name).label}</span><span className="group-count">{g.count}</span>
    </button>)}
  </div>;
}

/** Name und Kurzformel der gerade markierten Gruppe — oder ein Hinweis im Ruhezustand. */
export function GroupNote({ groups, hoveredGroup }) {
  const group = groups?.find((g) => g.name === hoveredGroup);
  if (!group) {
    return <div className="group-note" role="status">
      <span className="group-note-hint">Hover a group to see where it sits in the structure.</span>
    </div>;
  }
  const info = groupInfo(group.name);
  return <div className="group-note is-active" role="status" style={{ "--group-color": group.color }}>
    <div className="group-note-head">
      <span className="group-dot" aria-hidden="true" />
      <strong>{info.label}</strong>
      {info.formula && <span className="group-formula">{info.formula}</span>}
    </div>
  </div>;
}
