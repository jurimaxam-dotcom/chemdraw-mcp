import React from "react";
import { naturalHeight, naturalWidth } from "../utils/svgSize";

// Diagrammfläche für Spektrum, DC-Platte, die Kurven-Plots und den Strukturvergleich
// (Etappe 1, 16.11.2026). Größe und Thema regelt styles.css über .plot-svg: die Figur
// nimmt die Kartenbreite bis zu einer Höchsthöhe, im Dunkeln folgen Fläche, Achsen und
// Schrift den Theme-Variablen. Das SVG selbst bleibt unverändert — „Export PNG“ und
// die Datei bekommen weiter das helle Original.

/** matplotlib (Kurven, Spektrum, DC) oder RDKit (Strukturvergleich)? */
export function svgSource(svg) {
  return /xmlns:rdkit=/.test(svg || "") ? "rdkit" : "matplotlib";
}

export default function PlotFigure({ svg, kind = "" }) {
  // Seitenverhältnis der Figur (Höhe/Breite): bei fester Panelhöhe passt sich die Karte einer
  // hochformatigen DC-Platte an, statt unter ihr leer zu bleiben (Etappe 5, styles.css).
  const w = naturalWidth(svg), h = naturalHeight(svg);
  return (
    <div
      className={kind ? `plot-svg ${kind}-svg` : "plot-svg"}
      data-svg-source={svgSource(svg)}
      data-plot-kind={kind || "plot"}
      style={w && h ? { "--plot-aspect": (h / w).toFixed(4) } : undefined}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
