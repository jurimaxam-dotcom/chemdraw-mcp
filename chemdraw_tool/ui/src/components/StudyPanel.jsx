import React, { useState } from "react";
import StructureCanvas from "./StructureCanvas";
import { groupInfo } from "../utils/groupInfo";

// Lernmodus (U4b): die Zeichnung bleibt, Kernwerte und Gruppen sind verdeckt.
// Ein Klick deckt ein Stück auf; eine aufgedeckte Gruppe leuchtet in der
// Struktur. Verdeckte Gruppen heißen „Group 1…n“ und tragen nirgends ihren
// Namen — auch nicht in aria-label oder title. Der Zustand (was aufgedeckt
// ist) gehört MoleculeView, weil Kopf und Text für Claude ihn mitlesen.

export default function StudyPanel({ uid, svg, atoms, groups, facts, revealed, focusGroup, onReveal, onFocusGroup, onRevealAll, onCover }) {
  const [hover, setHover] = useState(null);
  const open = (key) => revealed.includes(key);
  // Nur Aufgedecktes ist für die Struktur „sichtbar“: sonst verriete der Hover-Glow,
  // wo eine verdeckte Gruppe sitzt.
  const shownGroups = groups.filter((g) => open(`group:${g.name}`));
  return (
    <div id={`${uid}-study`} role="tabpanel" aria-labelledby={`${uid}-tab-study`} data-view="study">
      <div className="structure-layout">
        <div className="structure-main">
          <StructureCanvas svg={svg} atoms={atoms} groups={shownGroups}
            hoveredGroup={hover || focusGroup} onHoverGroup={setHover} />
        </div>
        {facts.length > 0 && <dl className="key-facts" aria-label="Key facts">
          {facts.map((f) => <div className="fact" key={f.key}>
            <dt>{f.label}</dt>
            <dd>{open(f.key)
              ? <span>{f.value}</span>
              : <button type="button" className="study-cover" aria-label={`Show ${f.label.toLowerCase()}`}
                  onClick={() => onReveal(f.key)}>Think first, then show</button>}</dd>
          </div>)}
        </dl>}
      </div>
      {groups.length > 0 && <section className="group-section" aria-label="Functional groups">
        <h3 className="section-label">Functional groups: {groups.length} to find</h3>
        <div className="functional-groups">
          {groups.map((g, i) => {
            const key = `group:${g.name}`;
            if (!open(key)) {
              return <button key={key} type="button" className="functional-group is-covered"
                aria-label={`Show group ${i + 1}`} onClick={() => onReveal(key)}>
                <span className="group-dot" aria-hidden="true" />
                <span>Group {i + 1}</span>
              </button>;
            }
            return <button key={key} type="button" className="functional-group"
              style={{ "--group-color": g.color }} aria-pressed={focusGroup === g.name}
              onClick={() => onFocusGroup(g.name)}>
              <span className="group-dot" aria-hidden="true" />
              <span>{groupInfo(g.name).label}</span><span className="group-count">{g.count}</span>
            </button>;
          })}
        </div>
      </section>}
      <div className="study-actions">
        <button type="button" className="study-button is-primary" onClick={onRevealAll}>Reveal all</button>
        <button type="button" className="study-button" onClick={onCover}>Cover again</button>
      </div>
    </div>
  );
}
