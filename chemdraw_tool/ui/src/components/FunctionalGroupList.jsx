import React from "react";
import { groupInfo } from "../utils/groupInfo";
import { elementName } from "../utils/modelContext.js";

// Chips statt Liste. Zwei getrennte Zustände (U4): Hover/Fokus ist nur Vorschau
// (onHoverGroup), ein Klick hält die Gruppe fest (onPin) — zweiter Klick löst.
// aria-pressed meint die festgehaltene Auswahl, nicht den Hover.
export default function FunctionalGroupList({ groups, pinnedGroup, onHoverGroup, onPin }) {
  if (!groups?.length) return null;
  const pick = onPin || onHoverGroup;
  return <div className="functional-groups">
    {groups.map((g, i) => <button key={i} type="button" className="functional-group"
      style={{ "--group-color": g.color }}
      aria-pressed={pinnedGroup === g.name}
      onMouseEnter={() => onHoverGroup?.(g.name)} onMouseLeave={() => onHoverGroup?.(null)}
      onFocus={() => onHoverGroup?.(g.name)} onBlur={() => onHoverGroup?.(null)}
      onClick={() => pick?.(g.name)}>
      <span className="group-dot" aria-hidden="true" />
      <span>{groupInfo(g.name).label}</span><span className="group-count">{g.count}</span>
    </button>)}
  </div>;
}

const HINT_PIN = "Click a group to pin it. The buttons below then ask Claude about it.";
const HINT_HOVER = "Hover a group to see where it sits in the structure.";
const PINNED_ASK = "Pinned. The buttons below now ask about this group.";

/**
 * Hinweis-Karte unter den Chips: angezeigt wird die Hover-Vorschau, sonst die
 * festgehaltene Auswahl (Gruppe oder Einzelatom). Die Sätze versprechen nur, was die
 * Chat-Knöpfe leisten (die Gruppe steht im gesendeten Satz) — ohne Knöpfe (canAsk) kein
 * Satz über Claude, für ein Einzelatom auch nicht (dafür gibt es keinen Knopf).
 */
export function GroupNote({ groups, hoveredGroup, pinned, canAsk = false, onClear }) {
  const pinnedName = pinned?.kind === "group" ? pinned.name : null;
  const group = groups?.find((g) => g.name === (hoveredGroup || pinnedName));
  const pinLine = (
    <div className="group-note-pin">
      <span className="group-note-hint">{canAsk && pinnedName ? PINNED_ASK : "Pinned."}</span>
      {onClear && <button type="button" className="group-note-clear" onClick={onClear}>Clear</button>}
    </div>
  );
  if (!group && pinned?.kind === "atom") {
    return <div className="group-note is-active is-pinned" role="status" style={{ "--group-color": "var(--accent)" }}>
      <div className="group-note-head">
        <span className="group-dot" aria-hidden="true" />
        <strong>{elementName(pinned.el).replace(/^./, (c) => c.toUpperCase())} atom</strong>
        <span className="group-formula">{pinned.el}</span>
      </div>
      {pinLine}
    </div>;
  }
  if (!group) {
    return <div className="group-note" role="status">
      <span className="group-note-hint">{canAsk ? HINT_PIN : HINT_HOVER}</span>
    </div>;
  }
  const info = groupInfo(group.name);
  const isPinned = group.name === pinnedName;
  return <div className={`group-note is-active${isPinned ? " is-pinned" : ""}`} role="status" style={{ "--group-color": group.color }}>
    <div className="group-note-head">
      <span className="group-dot" aria-hidden="true" />
      <strong>{info.label}</strong>
      {info.formula && <span className="group-formula">{info.formula}</span>}
    </div>
    {isPinned && pinLine}
  </div>;
}
