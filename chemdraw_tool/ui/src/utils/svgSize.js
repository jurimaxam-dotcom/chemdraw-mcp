// Natürliche Breite eines SVG-Strings aus seiner viewBox. Die Mechanismus-Overview skaliert damit
// jede Kachel nach Inhalt statt nach Kachelbreite — sonst werden breite Bilder (Produkt + weit
// entferntes Br⁻) winzig und schmale riesig.
export function naturalWidth(svg) {
  const m = /viewBox=['"]\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+[\d.]+\s*['"]/.exec(svg || "");
  return m ? Number(m[1]) : null;
}

// Natürliche Höhe aus der viewBox — das Reaktions-Panel erkennt daran Stoffe, die der Server
// größer als 250×200 gezeichnet hat (fester Bindungsmaßstab, E16).
export function naturalHeight(svg) {
  const m = /viewBox=['"]\s*[-\d.]+[\s,]+[-\d.]+[\s,]+[\d.]+[\s,]+([\d.]+)\s*['"]/.exec(svg || "");
  return m ? Number(m[1]) : null;
}
