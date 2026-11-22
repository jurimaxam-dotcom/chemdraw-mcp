import React from "react";
import { groupInfo } from "../utils/groupInfo";
import { elementName } from "../utils/modelContext.js";
import { Button, Chip } from "./Panel";

// Chips statt Liste. Zwei getrennte Zustände (U4): Hover/Fokus ist nur Vorschau
// (onHoverGroup), ein Klick hält die Gruppe fest (onPin) — zweiter Klick löst.
// aria-pressed meint die festgehaltene Auswahl, nicht den Hover.
export default function FunctionalGroupList({ groups, pinnedGroup, onHoverGroup, onPin }) {
  if (!groups?.length) return null;
  const pick = onPin || onHoverGroup;
  // Panel-Umbau A (§4 Chip): die einzige Pille im Panel; aria-pressed = festgehalten.
  return <div className="functional-groups">
    {groups.map((g, i) => <Chip key={i} className="functional-group" color={g.color} count={g.count}
      pressed={pinnedGroup === g.name}
      onMouseEnter={() => onHoverGroup?.(g.name)} onMouseLeave={() => onHoverGroup?.(null)}
      onFocus={() => onHoverGroup?.(g.name)} onBlur={() => onHoverGroup?.(null)}
      onClick={() => pick?.(g.name)}>
      <span>{groupInfo(g.name).label}</span>
    </Chip>)}
  </div>;
}

// Etappe 4 (16.11.2026): der Hinweis steht in der Zeile der Überschrift statt als eigener
// Kasten darunter. Sichtbar ist nur der knappe Anfang; der volle Satz bleibt als Tooltip und
// für Bedienungshilfen (visually-hidden, nicht display:none) erhalten.
const HINT_PIN = ["Click a group to pin it", ". The buttons below then ask Claude about it."];
const HINT_HOVER = ["Hover a group to see where it sits", " in the structure."];
const PINNED_ASK = ["Pinned.", " The buttons below now ask about this group."];

function Hint({ parts }) {
  return <span className="group-note-hint" title={parts.join("")}>
    {parts[0]}<span className="visually-hidden">{parts[1]}</span>
  </span>;
}

/**
 * Hinweis neben den Chips: angezeigt wird die Hover-Vorschau, sonst die festgehaltene
 * Auswahl (Gruppe oder Einzelatom), sonst der knappe Hinweis — der verschwindet, sobald
 * etwas angeheftet ist. Die Sätze versprechen nur, was die Chat-Knöpfe leisten (die Gruppe
 * steht im gesendeten Satz) — ohne Knöpfe (canAsk) kein Satz über Claude, für ein
 * Einzelatom auch nicht (dafür gibt es keinen Knopf).
 */
export function GroupNote({ groups, hoveredGroup, pinned, canAsk = false, onClear }) {
  const pinnedName = pinned?.kind === "group" ? pinned.name : null;
  const group = groups?.find((g) => g.name === (hoveredGroup || pinnedName));
  const pinLine = <>
    {canAsk && pinnedName ? <Hint parts={PINNED_ASK} /> : <span className="group-note-hint">Pinned.</span>}
    {onClear && <Button className="group-note-clear" onClick={onClear}>Clear</Button>}
  </>;
  if (!group && pinned?.kind === "atom") {
    return <div className="group-note is-active is-pinned" role="status" style={{ "--group-color": "var(--accent)" }}>
      <span className="group-dot" aria-hidden="true" />
      <strong>{elementName(pinned.el).replace(/^./, (c) => c.toUpperCase())} atom</strong>
      <span className="group-formula">{pinned.el}</span>
      {pinLine}
    </div>;
  }
  if (!group) {
    return <div className="group-note" role="status"><Hint parts={canAsk ? HINT_PIN : HINT_HOVER} /></div>;
  }
  const info = groupInfo(group.name);
  const isPinned = group.name === pinnedName;
  return <div className={`group-note is-active${isPinned ? " is-pinned" : ""}`} role="status" style={{ "--group-color": group.color }}>
    <span className="group-dot" aria-hidden="true" />
    <strong>{info.label}</strong>
    {info.formula && <span className="group-formula">{info.formula}</span>}
    {isPinned && pinLine}
  </div>;
}
