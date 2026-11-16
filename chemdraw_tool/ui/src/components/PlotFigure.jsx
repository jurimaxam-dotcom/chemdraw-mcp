import React from "react";

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
  return (
    <div
      className={kind ? `plot-svg ${kind}-svg` : "plot-svg"}
      data-svg-source={svgSource(svg)}
      data-plot-kind={kind || "plot"}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
