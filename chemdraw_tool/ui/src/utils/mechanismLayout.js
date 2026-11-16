// Mechanismus-Übersicht (Etappe 5, 16.11.2026): alle Schritte auf einen Blick, ohne inneren
// Rollbereich. Vorher stand jeder Schritt in einer Spalte untereinander (Maßstab 0,62) in einer
// Karte mit eigenem Rollbalken — bei 1000 px waren zwei von drei SN2-Schritten zu sehen.
//
// Regel: so wenige Zeilen wie möglich (nebeneinander, wo die Breite reicht), aber nie kleiner
// als MIN_SCALE — darunter werden Atombeschriftung und Elektronenpfeile unlesbar. Passt keine
// Aufteilung in die verfügbare Höhe, bleibt es bei MIN_SCALE und das Panel wird höher
// (`overflow`): dann rollt die Seite, nie ein Bereich im Bereich.

// Pixel je viewBox-Einheit: 0,62 war der Maßstab der alten Spalte (lesbar), 1 die volle Größe.
export const MIN_SCALE = 0.62;
export const MAX_SCALE = 1;
// Feste Anteile je Kachel und Pfeil (MechanismView rendert genau diese Maße).
export const TILE_PAD = 6;          // Innenabstand der Kachel je Seite
export const CAPTION_H = 24;        // Beschriftung (eine Zeile) + Abstand zur Zeichnung
export const ARROW_W = 30;          // waagrechter Pfeil zwischen zwei Kacheln einer Zeile
export const ARROW_H = 30;          // senkrechter Pfeil zwischen zwei Zeilen

function chunk(n, perRow) {
  const rows = [];
  for (let i = 0; i < n; i += perRow) rows.push(Array.from({ length: Math.min(perRow, n - i) }, (_, k) => i + k));
  return rows;
}

function measure(sizes, rows, width, height) {
  const tile = 2 * TILE_PAD;
  let sw = Infinity;
  for (const row of rows) {
    const fixed = row.length * tile + (row.length - 1) * ARROW_W;
    const sum = row.reduce((s, i) => s + sizes[i].w, 0);
    sw = Math.min(sw, (width - fixed) / sum);
  }
  const fixedH = rows.length * (tile + CAPTION_H) + (rows.length - 1) * ARROW_H;
  const sumH = rows.reduce((s, row) => s + Math.max(...row.map((i) => sizes[i].h)), 0);
  const sh = height > 0 ? (height - fixedH) / sumH : Infinity;
  const need = (s) => fixedH + s * sumH;
  return { sw, sh, need };
}

/**
 * Aufteilung der Übersicht.
 * @param sizes  [{w, h}] je Schritt (viewBox-Maße)
 * @param width  verfügbare Breite in px (Inhalt der Bühne)
 * @param height verfügbare Höhe in px (0 = unbekannt)
 * @returns {{rows: number[][], scale: number, height: number, overflow: boolean}}
 */
export function overviewLayout(sizes, width, height) {
  const n = sizes.length;
  if (n === 0) return { rows: [], scale: MIN_SCALE, height: 0, overflow: false };
  if (!(width > 0)) {
    // Noch nicht gemessen (jsdom, erster Wurf): eine Spalte im alten Maßstab.
    const rows = chunk(n, 1);
    return { rows, scale: MIN_SCALE, height: measure(sizes, rows, 1, 0).need(MIN_SCALE), overflow: false };
  }
  // Fewest rows first: r Zeilen mit je ceil(n / r) Schritten.
  let fallback = null;
  for (let r = 1; r <= n; r++) {
    const perRow = Math.ceil(n / r);
    if (r > 1 && Math.ceil(n / (r - 1)) === perRow) continue; // gleiche Aufteilung wie eben
    const rows = chunk(n, perRow);
    const m = measure(sizes, rows, width, height);
    if (m.sw < MIN_SCALE) continue;
    // Gerundet: misst die Bühne genau die Höhe dieser Aufteilung, gilt sie als passend.
    const scale = Math.min(MAX_SCALE, m.sw, m.sh);
    if (scale >= MIN_SCALE - 1e-3) return { rows, scale, height: m.need(scale), overflow: false };
    if (!fallback) fallback = { rows, scale: MIN_SCALE, height: m.need(MIN_SCALE), overflow: true };
  }
  if (fallback) return fallback;
  // Selbst ein Schritt je Zeile ist breiter als die Bühne: in die Breite einpassen.
  const rows = chunk(n, 1);
  const m = measure(sizes, rows, width, height);
  const scale = Math.max(0.1, Math.min(MAX_SCALE, m.sw));
  return { rows, scale, height: m.need(scale), overflow: m.need(scale) > height + 1 };
}
