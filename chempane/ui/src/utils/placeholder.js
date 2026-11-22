// Platzhalter aus `toolinput`: Claude hat das Tool aufgerufen, das Ergebnis ist
// noch unterwegs (Namensauflösung kostet Sekunden). Statt „Waiting for data…“
// zeigt das Panel, was die Argumente schon hergeben. Reine Funktion.

const str = (v) => (typeof v === "string" ? v.trim() : "");
const list = (v) => (Array.isArray(v) ? v.map(str).filter(Boolean) : []);

/** Argumente → { title, items } (items = beschriftete Platzhalter, z. B. batch_generate). */
export function placeholderFromInput(args) {
  const a = args && typeof args === "object" ? args : {};
  const molecules = list(a.molecules);
  if (molecules.length) return { title: `${molecules.length} structures`, items: molecules };
  const structures = list(a.structures);
  if (structures.length) return { title: str(a.title) || `${structures.length} structures`, items: structures };
  const reactants = list(a.reactants);
  const products = list(a.products);
  if (reactants.length || products.length) {
    return { title: str(a.name) || `${reactants.join(" + ")} → ${products.join(" + ")}`, items: [] };
  }
  if (str(a.reaction_type)) {
    const subs = list(a.substrates);
    const kind = str(a.reaction_type) === "fischer_ester" ? "Fischer esterification" : str(a.reaction_type).toUpperCase();
    return { title: `${kind} mechanism${subs.length ? `: ${subs.join(" + ")}` : ""}`, items: [] };
  }
  if (str(a.spectrum_type)) return { title: str(a.title) || `${str(a.spectrum_type)} spectrum`, items: [] };
  const title = str(a.label) || str(a.name_or_smiles) || str(a.name) || str(a.title);
  return { title, items: [] };
}
