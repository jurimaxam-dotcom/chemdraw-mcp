import React from "react";
import MoleculeView from "./MoleculeView";
import ReactionView from "./ReactionView";
import DatabaseView from "./DatabaseView";
import MechanismView from "./MechanismView";
import SpectrumView from "./SpectrumView";
import TlcView from "./TlcView";
import ScopeView from "./ScopeView";
import AnkiDeckView from "./AnkiDeckView";
import PlotView from "./PlotView";
import Molecule3DView from "./Molecule3DView";
import ProteinView from "./ProteinView";
import AmbiguousView from "./AmbiguousView";
import BatchView from "./BatchView";

export default function App({ data }) {
  switch (data.type) {
    case "molecule":
      // Schlüssel = Stoff + angeforderte Ansicht: ein zweites Ergebnis im selben
      // Panel darf nicht auf den Zustand des vorigen treffen (Cache, Ansicht).
      return (
        <MoleculeView
          key={`${data.smiles || data.properties?.smiles || data.name}|${data.initialView || ""}|${JSON.stringify(data.viewRequest || {})}`}
          data={data}
        />
      );
    case "ambiguous":
      return <AmbiguousView key={data.name} data={data} />;
    case "reaction":
      // Ohne Schlüssel blieb nach „Apply coefficients“ die alte Gleichung stehen.
      return <ReactionView key={`${data.name}|${JSON.stringify(data.request || {})}`} data={data} />;
    case "database":
      return <DatabaseView key={data.smiles || data.name} data={data} />;
    case "batch":
      // Raster kompakter Karten, Klick öffnet die volle Molekül-Ansicht (Etappe 2).
      // Schlüssel = die Stoffe: ein neues Ergebnis beginnt in der Übersicht, nie in einem alten Detail.
      return <BatchView key={(data.molecules || []).map((m) => m.properties?.smiles || m.name).join("|")} data={data} />;
    case "mechanism":
      return <MechanismView key={`${data.name}|${data.reaction_type}|${(data.steps || []).length}`} data={data} />;
    case "spectrum":
      return <SpectrumView data={data} />;
    case "tlc":
      return <TlcView data={data} />;
    case "scope":
      return <ScopeView data={data} />;
    case "anki_deck":
      return <AnkiDeckView data={data} />;
    case "plot":
      return <PlotView data={data} />;
    case "molecule3d":
      return <Molecule3DView data={data} />;
    case "protein":
      return <ProteinView data={data} />;
    default:
      return <div style={{ color: "#8b949e", padding: 16 }}>Unknown type: {data.type}</div>;
  }
}
