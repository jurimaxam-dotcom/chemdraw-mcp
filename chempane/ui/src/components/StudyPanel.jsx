import React, { useState } from "react";
import StructureCanvas from "./StructureCanvas";
import { Button, Facts, PanelBody, StageBar } from "./Panel";
import { groupInfo } from "../utils/groupInfo";

// Lernmodus (U4b): die Zeichnung bleibt, Kernwerte und Gruppen sind verdeckt.
// Ein Klick deckt ein Stück auf; eine aufgedeckte Gruppe leuchtet in der
// Struktur. Verdeckte Gruppen heißen „Group 1…n“ und tragen nirgends ihren
// Namen — auch nicht in aria-label oder title. Der Zustand (was aufgedeckt
// ist) gehört MoleculeView, weil Kopf und Text für Claude ihn mitlesen.
//
// Panel-Umbau A (17.11.2026, §5.1): dieselbe Geometrie wie Structure — StageBar (hier rechts
// „Reveal all“ und „Cover again“ an der Stelle der Achse), Bühne, Kernwerte als Zeile darunter,
// Gruppen. Verdecktes = --surface-1 mit gestrichelter --line-strong-Kante, die einzige gestrichelte
// Form im Panel. In Fill bekommt die Bühne dieselbe Flex-Kette wie Structure (B9, frame.css).

export default function StudyPanel({ uid, svg, atoms, groups, facts, revealed, focusGroup, onReveal, onFocusGroup, onRevealAll, onCover }) {
  const [hover, setHover] = useState(null);
  const open = (key) => revealed.includes(key);
  // Nur Aufgedecktes ist für die Struktur „sichtbar“: sonst verriete der Hover-Glow,
  // wo eine verdeckte Gruppe sitzt.
  const shownGroups = groups.filter((g) => open(`group:${g.name}`));
  return (
    <PanelBody id={`${uid}-study`} role="tabpanel" aria-labelledby={`${uid}-tab-study`} data-view="study">
      <StageBar className="study-actions" right={<>
        <Button variant="primary" className="study-button is-primary" onClick={onRevealAll}>Reveal all</Button>
        <Button className="study-button" onClick={onCover}>Cover again</Button>
      </>} />
      <StructureCanvas svg={svg} atoms={atoms} groups={shownGroups}
        hoveredGroup={hover || focusGroup} onHoverGroup={setHover} />
      <Facts aria-label="Key facts" items={facts.map((f) => ({
        key: f.key, label: f.label,
        value: open(f.key) ? f.value : <button type="button" className="study-cover" aria-label={`Show ${f.label.toLowerCase()}`}
          onClick={() => onReveal(f.key)}>Think first, then show</button>,
      }))} />
      {/* Kein eigenes Etikett „n of m groups to find“ mehr (Panel-Umbau A): der Zähler im Kopf zählt die
          Gruppen mit, und die Study-Bühne soll so hoch sein wie die von Structure (E6, B9). */}
      {groups.length > 0 && <section className="group-section" aria-label="Functional groups">
        <div className="functional-groups">
          {groups.map((g, i) => {
            const key = `group:${g.name}`;
            if (!open(key)) {
              return <button key={key} type="button" className="chip functional-group is-covered"
                aria-label={`Show group ${i + 1}`} onClick={() => onReveal(key)}>
                <span className="chip-dot group-dot" aria-hidden="true" />
                <span>Group {i + 1}</span>
              </button>;
            }
            return <button key={key} type="button" className="chip functional-group"
              style={{ "--group-color": g.color }} aria-pressed={focusGroup === g.name}
              onClick={() => onFocusGroup(g.name)}>
              <span className="chip-dot group-dot" aria-hidden="true" />
              <span>{groupInfo(g.name).label}</span><span className="chip-count group-count">{g.count}</span>
            </button>;
          })}
        </div>
      </section>}
    </PanelBody>
  );
}
