import React from "react";
import { Stage } from "./Panel";
import { naturalHeight, naturalWidth } from "../utils/svgSize";

// Diagrammfläche für Spektrum, DC-Platte, die Kurven-Plots und den Strukturvergleich
// (Etappe 1, 16.11.2026). Seit dem Panel-Umbau (17.11.2026, Spezifikation §5.8) ist die
// Fläche selbst die Bühne: Stage „plain“ ohne Rahmen, Polster und eigene Fläche — der Plotgrund
// färbt sich über --plot-paper mit dem Panel. Größe und Thema regelt styles/b-graphics.css über
// .plot-svg. Das SVG selbst bleibt unverändert — „Export PNG“ und die Datei bekommen weiter
// das helle Original.

/** matplotlib (Kurven, Spektrum, DC) oder RDKit (Strukturvergleich)? */
export function svgSource(svg) {
  return /xmlns:rdkit=/.test(svg || "") ? "rdkit" : "matplotlib";
}

export default function PlotFigure({ svg, kind = "" }) {
  // Seitenverhältnis der Figur (Höhe/Breite): in Fill passt sich die Bühne einer hochformatigen
  // DC-Platte an, statt unter ihr leer zu bleiben (Etappe 5, b-graphics.css).
  const w = naturalWidth(svg), h = naturalHeight(svg);
  return (
    <Stage
      variant="plain"
      className={kind ? `plot-svg ${kind}-svg` : "plot-svg"}
      data-svg-source={svgSource(svg)}
      data-plot-kind={kind || "plot"}
      style={w && h ? { "--plot-aspect": (h / w).toFixed(4) } : undefined}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
