import React from "react";
import MoleculeView from "./MoleculeView";
import ReactionView from "./ReactionView";
import DatabaseView from "./DatabaseView";
import MechanismView from "./MechanismView";
import ValidationView from "./ValidationView";

export default function App({ data }) {
  switch (data.type) {
    case "molecule":
      return <MoleculeView data={data} />;
    case "reaction":
      return <ReactionView data={data} />;
    case "database":
      return <DatabaseView data={data} />;
    case "batch":
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {(data.molecules || []).map((mol, i) => (
            // Prefer a stable identity (SMILES/name) so per-molecule state
            // survives list changes; fall back to index when neither exists.
            <MoleculeView key={mol.properties?.smiles || mol.name || i} data={mol} />
          ))}
        </div>
      );
    case "mechanism":
      return <MechanismView data={data} />;
    case "validation":
      return <ValidationView data={data} />;
    default:
      return <div style={{ color: "#8b949e", padding: 16 }}>Unbekannter Typ: {data.type}</div>;
  }
}
