// Text für Claude (U4b): Claude sieht das Panel nicht, nur diesen Text, den der
// Host mit der nächsten Nachricht mitschickt (app.updateModelContext). Er nennt,
// was gezeigt und ausgewählt ist — gebaut nur aus Payload und Nutzerzustand,
// nie aus Größe oder Anzeigemodus: ein abgelöstes Panel (Seitenpanel → Chat)
// ändert damit seinen Text nicht und bleibt still (abgleich.md Nr. 17).
//
// Der Host behält nur das letzte Update, also trägt jeder Text den vollen Zustand.
import { groupInfo } from "./groupInfo.js";

export const MAX_CONTEXT = 3800;

const HEAD = "Chem-MCP panel next to the chat (the user sees it; you do not):";

function clip(text) {
  return text.length <= MAX_CONTEXT ? text : `${text.slice(0, MAX_CONTEXT - 1)}…`;
}

const ELEMENTS = {
  C: "carbon", H: "hydrogen", N: "nitrogen", O: "oxygen", S: "sulfur", P: "phosphorus",
  F: "fluorine", Cl: "chlorine", Br: "bromine", I: "iodine", B: "boron", Si: "silicon",
};

export function elementName(el) {
  return ELEMENTS[el] || el || "unknown";
}

const DRAWINGS = {
  skeletal: "2D skeletal formula",
  all_h: "2D formula with all hydrogens drawn",
  fischer: "Fischer projection",
  haworth: "Haworth projection",
  chair: "chair conformation",
};

const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

function compoundLine(name, formula, smiles) {
  const bits = [formula && `formula ${formula}`, smiles && `SMILES ${smiles}`].filter(Boolean);
  return `Compound: ${name || smiles || "unnamed"}${bits.length ? ` (${bits.join(", ")})` : ""}`;
}

function groupsLine(groups) {
  if (!groups?.length) return "";
  return `Functional groups: ${groups.map((g) => `${groupInfo(g.name).label} ×${g.count ?? 1}`).join(", ")}`;
}

function stereoLine(warnings) {
  const list = warnings || [];
  const atoms = list.filter((w) => w.kind === "atom").length;
  const bonds = list.filter((w) => w.kind === "double_bond").length;
  const parts = [atoms && plural(atoms, "undefined stereocentre"), bonds && plural(bonds, "undefined double bond")].filter(Boolean);
  return parts.length ? `Stereochemistry: ${parts.join(", ")} (the input leaves the configuration open)` : "";
}

function pinnedLine(pinned, groups) {
  if (!pinned) return "";
  if (pinned.kind === "group") {
    const group = (groups || []).find((g) => g.name === pinned.name);
    const info = groupInfo(pinned.name);
    const where = group?.atomIndices?.length ? `, atom indices ${group.atomIndices.join(", ")}` : "";
    return `Pinned selection: the ${info.label} group${info.formula ? ` (${info.formula})` : ""}${where}. `
      + "When the user says \"this\" or \"this group\", they mean this selection.";
  }
  if (pinned.kind === "atom") {
    return `Pinned selection: a single ${elementName(pinned.el)} atom (${pinned.el}, atom index ${pinned.idx}), `
      + "not part of a detected functional group. When the user says \"this atom\", they mean it.";
  }
  return "";
}

// --- Lernmodus ------------------------------------------------------------------

/** Was der Lernmodus verdecken kann, in fester Reihenfolge (Kopf, Kernwerte, Gruppen). */
export function studyItems(data) {
  const props = data.properties || {};
  const formula = data.formula ?? props.formula;
  const items = [];
  if (data.name) items.push({ key: "name", label: "name" });
  if (formula) items.push({ key: "formula", label: "formula" });
  if (props.mw) items.push({ key: "mass", label: "molar mass" });
  if (props.cas) items.push({ key: "cas", label: "CAS" });
  (data.functionalGroups || []).forEach((g, i) => {
    items.push({ key: `group:${g.name}`, label: `functional group ${i + 1} (${groupInfo(g.name).label})`, group: g, index: i });
  });
  return items;
}

function studyLines(data, revealed) {
  const open = new Set(revealed || []);
  const items = studyItems(data);
  const covered = items.filter((i) => !open.has(i.key));
  const shown = items.filter((i) => open.has(i.key));
  const lines = ["View: Study mode — the user is testing themselves on this structure; the drawing stays visible."];
  if (covered.length === 0) {
    lines.push("Everything is revealed.");
    return lines;
  }
  lines.push(`Still covered: ${covered.map((i) => i.label).join(", ")} (${covered.length} of ${items.length} still covered).`);
  if (shown.length) lines.push(`Revealed: ${shown.map((i) => i.label).join(", ")}.`);
  lines.push("Do not reveal covered information (above all the name) unless the user explicitly asks for it; give hints instead.");
  return lines;
}

// --- Views ----------------------------------------------------------------------

/**
 * MoleculeView. `state`: { view: "structure"|"data"|"study", drawing, is3d,
 * pinned: {kind:"group",name} | {kind:"atom",idx,el} | null, revealed: [keys] }.
 */
export function moleculeContext(data, state = {}) {
  const props = data.properties || {};
  const formula = data.formula ?? props.formula;
  const smiles = data.smiles ?? props.smiles;
  const lines = [HEAD, compoundLine(data.name, formula, smiles)];
  if (props.pubchemTitle) lines.push(`PubChem record: ${props.pubchemTitle}${props.cid ? ` (CID ${props.cid})` : ""}`);
  const facts = [props.mw && `molar mass ${/g\/mol/.test(props.mw) ? props.mw : `${props.mw} g/mol`}`, props.cas && `CAS ${props.cas}`].filter(Boolean);
  if (facts.length) lines.push(`Key facts: ${facts.join(", ")}`);
  if (state.view === "study") {
    lines.push(...studyLines(data, state.revealed));
  } else if (state.view === "data") {
    lines.push("View: Data sheet (database entries for the compound)");
  } else {
    const drawing = state.is3d ? "rotatable 3D ball-and-stick model" : DRAWINGS[state.drawing || "skeletal"] || state.drawing;
    lines.push(`View: Structure — ${drawing}`);
  }
  const groups = data.functionalGroups || [];
  for (const line of [groupsLine(groups), stereoLine(data.stereoWarnings)]) if (line) lines.push(line);
  if (state.view !== "study") {
    const pin = pinnedLine(state.pinned, groups);
    if (pin) lines.push(pin);
  }
  return clip(lines.join("\n"));
}

export function moleculeSummary(data) {
  const props = data.properties || {};
  const formula = data.formula ?? props.formula;
  const who = data.name || data.smiles || props.smiles || "unnamed";
  return formula ? `${who} (${formula})` : who;
}

/** DatabaseView: Datenblatt mit lokalem Weg zur Struktur. */
export function databaseContext(data, state = {}) {
  const lines = [HEAD, compoundLine(data.name, data.formula, data.smiles)];
  const sources = (data.sources || []).map((s) => s.source || s.type).filter(Boolean);
  lines.push(state.view === "structure"
    ? "View: Structure (from the data sheet)"
    : `View: Data sheet${sources.length ? ` — sources ${sources.join(", ")}` : ""}`);
  const groups = data.functionalGroups || [];
  for (const line of [groupsLine(groups), stereoLine(data.stereoWarnings), pinnedLine(state.pinned, groups)]) {
    if (line) lines.push(line);
  }
  return clip(lines.join("\n"));
}

function sideNames(list, fallback) {
  return (list || []).map((m, i) => (m?.name || "").trim() || fallback?.[i] || "?");
}

export function reactionContext(data) {
  const left = sideNames(data.reactants, data.request?.reactants);
  const right = sideNames(data.products, data.request?.products);
  const lines = [HEAD, `Reaction: ${data.name || "unnamed"}`, `Equation: ${left.join(" + ")} → ${right.join(" + ")}`];
  if (data.conditions || data.conditions_below) lines.push(`Conditions: ${[data.conditions, data.conditions_below].filter(Boolean).join("; ")}`);
  if (data.balance) lines.push(`Balance: ${data.balance.balanced ? "balanced" : "not balanced"}`);
  return clip(lines.join("\n"));
}

export function mechanismContext(data, { mode, step } = {}) {
  const steps = data.steps || [];
  const lines = [HEAD, `Mechanism: ${data.name || "unnamed"} (${data.reaction_type || "?"})`];
  if (data.substrates_drawn === false) lines.push("Drawn with the textbook example, not the user's substrates.");
  lines.push(mode === "step" && steps[step]
    ? `Showing: step ${step + 1} of ${steps.length} — ${steps[step].label}`
    : `Showing: overview of all ${steps.length} steps`);
  return clip(lines.join("\n"));
}

/** Knappe Fassung für Views ohne eigenen Zustand. */
export function genericContext(type, data) {
  const name = data.name ? `: ${data.name}` : "";
  let body;
  switch (type) {
    case "spectrum":
      body = `Schematic ${data.spectrum_type || ""} spectrum${name}`.replace("  ", " ");
      break;
    case "tlc": {
      const lanes = (data.lanes || []).map((l) => `${l.name} (Rf ${(l.spots || []).map((s) => s.rf).join(", ") || "–"})`);
      body = `TLC plate${name}${data.solvent ? `, solvent ${data.solvent}` : ""}${lanes.length ? `\nLanes: ${lanes.join("; ")}` : ""}`;
      break;
    }
    case "plot":
      body = `Diagram${name}${data.subtitle ? ` — ${data.subtitle}` : ""}`;
      break;
    case "protein":
      body = `Protein structure${name}${data.subtitle ? ` — ${data.subtitle}` : ""}`;
      break;
    case "molecule3d":
      body = `Rotatable 3D ball-and-stick model${name}`;
      break;
    case "anki_deck":
      body = `Anki deck${name} with ${plural(data.cards ?? 0, "card")}`;
      break;
    case "scope":
      body = `Substrate scope figure${name} with ${plural((data.entries || []).length, "entry").replace("entrys", "entries")}`;
      break;
    case "ambiguous":
      body = `The name${name} fits several isomers; the user is asked to pick one: ${(data.candidates || []).map((c) => c.label || c.name).filter(Boolean).join(", ")}`;
      break;
    default:
      body = `${type}${name}`;
  }
  return clip(`${HEAD}\n${body}`);
}

/**
 * Ein Text aus allen Meldungen des Panels. Eine Meldung → ihr Text. Mehrere
 * (batch_generate): ein gemeinsamer Überblick plus die Karte, die zuletzt
 * bedient wurde — so überschreiben sich die Karten nicht gegenseitig.
 * `entries`: [{ text, summary, focus }] in Anzeigereihenfolge; focus > 0 = bedient.
 */
export function buildModelContext(entries) {
  const list = (entries || []).filter((e) => e && e.text);
  if (list.length === 0) return "";
  if (list.length === 1) return clip(list[0].text);
  const lines = [`${HEAD} ${list.length} cards side by side.`];
  list.forEach((e, i) => lines.push(`${i + 1}. ${e.summary || "item"}`));
  let focus = -1;
  list.forEach((e, i) => {
    if ((e.focus || 0) > 0 && (focus < 0 || e.focus > list[focus].focus)) focus = i;
  });
  if (focus >= 0) {
    const detail = list[focus].text.startsWith(HEAD) ? list[focus].text.slice(HEAD.length).trimStart() : list[focus].text;
    lines.push("", `In focus — card ${focus + 1} of ${list.length}:`, detail);
  }
  return clip(lines.join("\n"));
}
