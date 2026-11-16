import React from "react";

// Summenformel mit tiefgestellten Indizes: C9H8O4 → C₉H₈O₄. Ein Index folgt auf ein
// Element oder eine schließende Klammer; Ziffern am Anfang oder nach „·“ sind Koeffizienten
// (2H2O, CuSO4·5H2O) und bleiben auf der Grundlinie. Kopiert wird immer die Klarschrift —
// das macht der Aufrufer mit dem Originaltext, nicht mit diesem Satz.
export function formulaParts(text) {
  const parts = [];
  for (const m of String(text).matchAll(/\d+|\D+/g)) {
    const prev = m.index > 0 ? text[m.index - 1] : "";
    const sub = /^\d/.test(m[0]) && /[A-Za-z)\]]/.test(prev);
    parts.push({ text: m[0], sub });
  }
  return parts;
}

export default function Formula({ text }) {
  return formulaParts(text).map((p, i) => (p.sub ? <sub key={i}>{p.text}</sub> : <React.Fragment key={i}>{p.text}</React.Fragment>));
}

/** Sieht ein Datenblatt-Wert wie eine Summenformel aus? Nur dann wird gesetzt. */
export function looksLikeFormula(value) {
  return typeof value === "string" && /^(?:\d*(?:[A-Z][a-z]?\d*|[()[\]]\d*)+)(?:·\d*(?:[A-Z][a-z]?\d*|[()[\]]\d*)+)*[+-]?$/.test(value);
}
