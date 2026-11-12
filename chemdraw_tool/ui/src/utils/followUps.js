// Knöpfe „Continue in chat“ (U3): jeder Knopf schreibt genau einen Satz an
// Claude (app.sendMessage). Nur Lieferbares: ein Knopf, dessen Wunsch der
// Server nicht erfüllen kann, wäre ein Versprechen ohne Deckung.
//
// Reine Funktionen: Payload (+ Panel-Zustand) → [{ id, label, text, color? }].
// Der Satz ist vollständiges Englisch und nennt den Stoff — so, wie ein Nutzer
// ihn tippen würde. Er steht danach sichtbar im Chat.
import { groupInfo } from "./groupInfo.js";

// Längere Namen passen nicht in einen Knopf (320 px), der Satz trägt sie trotzdem.
const MAX_LABEL_NAME = 24;

/** Wie der Satz den Stoff nennt: Name, sonst SMILES. */
function ref({ name, smiles }) {
  return (name || "").trim() || (smiles || "").trim() || "this compound";
}

// --- Mechanismus-Regel ---------------------------------------------------------
// generate_mechanism kann drei Familien (server.py): fischer_ester (eine
// Carbonsäure mit einem primären/sekundären Alkohol), sn2 (Methyl-, primäres oder
// sekundäres Alkylchlorid/-bromid/-iodid), sn1 (tertiäres oder benzylisches
// Alkylhalogenid). Die Gruppennamen kommen deutsch vom Server
// (svg_renderer._FUNCTIONAL_GROUPS): "Carbonsäure", "Hydroxyl" (nur [OX2H1][CX4],
// Phenol heißt eigens "Phenol"), "Halogenid" ([#6][F,Cl,Br,I] — auch Aryl und F,
// beides lehnt der Server ab, deshalb hier gefiltert).
const LEAVING = new Set(["Cl", "Br", "I"]);

function byIdx(atoms) {
  return new Map((atoms || []).map((a) => [a.idx, a]));
}

/** Kohlenstoff der Gruppe, der dem Atom `x` am nächsten liegt (= sein Bindungspartner). */
function partnerCarbon(atom, members) {
  let best = null;
  let bestD = Infinity;
  for (const m of members) {
    if (m.el !== "C" || m.idx === atom.idx) continue;
    const d = Math.hypot(m.x - atom.x, m.y - atom.y);
    if (d < bestD) {
      bestD = d;
      best = m;
    }
  }
  return best;
}

function halideMechanism(group, atoms, aromatic) {
  const map = byIdx(atoms);
  const members = group.atomIndices.map((i) => map.get(i)).filter(Boolean);
  for (const x of members) {
    if (!LEAVING.has(x.el)) continue;
    const c = partnerCarbon(x, members);
    if (!c || aromatic.has(c.idx)) continue;
    return (c.hCount ?? 0) >= 1 ? "sn2" : "sn1";
  }
  return null;
}

function isPrimaryOrSecondaryAlcohol(group, atoms) {
  if (!atoms?.length) return true; // ohne Atomliste nicht prüfbar — der Server nennt dann den Grund
  const map = byIdx(atoms);
  const members = group.atomIndices.map((i) => map.get(i)).filter(Boolean);
  const o = members.find((a) => a.el === "O");
  const c = o && partnerCarbon(o, members);
  return Boolean(c) && (c.hCount ?? 0) >= 1;
}

/** Welchen der drei Mechanismen der Stoff hergibt — oder null. */
export function mechanismFor(groups, atoms) {
  const list = groups || [];
  const find = (name) => list.find((g) => g.name === name);
  if (find("Carbonsäure")) return { type: "fischer_ester", role: "acid" };
  const alcohol = find("Hydroxyl");
  if (alcohol && isPrimaryOrSecondaryAlcohol(alcohol, atoms)) return { type: "fischer_ester", role: "alcohol" };
  const halide = find("Halogenid");
  if (halide && atoms?.length) {
    const aromatic = new Set(find("Aromat")?.atomIndices || []);
    const type = halideMechanism(halide, atoms, aromatic);
    if (type) return { type, role: "substrate" };
  }
  return null;
}

function mechanismAction(mech, who) {
  if (mech.type === "fischer_ester") {
    const text = mech.role === "acid"
      ? `Show me the Fischer esterification mechanism for ${who} with methanol, step by step.`
      : `Show me the Fischer esterification mechanism for acetic acid with ${who}, step by step.`;
    return { id: "mechanism", label: "Fischer esterification mechanism", text };
  }
  if (mech.type === "sn2") {
    return { id: "mechanism", label: "SN2 mechanism",
      text: `Show me the SN2 mechanism of ${who} with hydroxide as the nucleophile, step by step.` };
  }
  return { id: "mechanism", label: "SN1 mechanism",
    text: `Show me the SN1 mechanism of ${who} in water, step by step.` };
}

// --- Molekül --------------------------------------------------------------------

/**
 * Knöpfe unter einer Strukturformel. `pinned` = festgehaltene Auswahl (U4):
 * eine Gruppe bringt zwei Knöpfe vorn, die sich auf sie beziehen.
 */
export function moleculeFollowUps({ name, smiles, groups, atoms, pinned }) {
  const who = ref({ name, smiles });
  const short = (name || "").trim();
  const quizLabel = short && short.length <= MAX_LABEL_NAME && short !== smiles
    ? `Quiz me on ${short}` : "Quiz me on this compound";
  const mech = mechanismFor(groups, atoms);
  const general = [
    ...(mech ? [mechanismAction(mech, who)] : []),
    { id: "ir", label: "Predict the IR bands", text: `Predict the IR bands of ${who}.` },
    { id: "compare", label: "Compare with a related compound",
      text: `Compare ${who} with a closely related compound and draw both structures side by side.` },
    { id: "quiz", label: quizLabel, text: `Quiz me on ${who}: ask one question at a time and wait for my answer.` },
  ];
  const group = pinned?.kind === "group" ? (groups || []).find((g) => g.name === pinned.name) : null;
  if (group) {
    const label = groupInfo(group.name).label.toLowerCase();
    return [
      { id: "group-explain", label: `Explain this ${label}`, color: group.color,
        text: `Explain the ${label} group in ${who}: where it sits in the structure and how it shapes the compound's properties.` },
      { id: "group-reactions", label: "Reactions of this group", color: group.color,
        text: `What are the typical reactions of the ${label} group in ${who}?` },
      ...general.slice(0, 3),
    ];
  }
  return [
    { id: "explain", label: "Explain the structure", text: `Explain the structure of ${who} and its functional groups.` },
    ...general,
  ];
}

/**
 * Lernmodus: der Name ist verdeckt, der Satz landet aber sichtbar im Chat.
 * Deshalb nennt er den Stoff per SMILES (Claude erkennt ihn daran, der Nutzer
 * liest den Namen nicht mit), bis der Name aufgedeckt ist.
 */
export function studyFollowUps({ name, smiles, nameRevealed }) {
  const hidden = !nameRevealed && Boolean(smiles);
  const who = hidden ? `the compound in the panel (SMILES ${smiles})` : ref({ name, smiles });
  const keep = hidden ? "Don't tell me its name or anything I still have covered" : "Don't give away anything I still have covered";
  return [
    { id: "hint", label: "Give me a hint", text: `Give me a hint about ${who}. ${keep}.` },
    { id: "quiz", label: "Quiz me on this compound",
      text: `Quiz me on ${who}: ask one question at a time and wait for my answer. ${keep} before I answer.` },
    { id: "next", label: "Next: a similar compound",
      text: `Draw a compound similar to ${who} for me to study next. Don't tell me its name; I want to work it out.` },
  ];
}

// --- Reaktion und Mechanismus ------------------------------------------------------

function sides(data) {
  const names = (list, fallback) => (list || []).map((m, i) => (m?.name || "").trim() || fallback?.[i] || "").filter(Boolean);
  return {
    left: names(data.reactants, data.request?.reactants),
    right: names(data.products, data.request?.products),
  };
}

/** Mechanismus aus dem Reaktionsnamen — nur die drei, die generate_mechanism kann. */
export function mechanismFromReactionName(name) {
  const n = String(name || "");
  if (/fischer|esterif/i.test(n)) return { type: "fischer_ester", label: "Fischer esterification" };
  if (/\bS\s?N\s?2\b/i.test(n)) return { type: "sn2", label: "SN2" };
  if (/\bS\s?N\s?1\b/i.test(n)) return { type: "sn1", label: "SN1" };
  return null;
}

export function reactionFollowUps(data) {
  const { left, right } = sides(data);
  const equation = `${left.join(" + ")} → ${right.join(" + ")}`;
  const actions = [];
  const mech = mechanismFromReactionName(data.name);
  if (mech && left.length) {
    actions.push({ id: "mechanism", label: "Show the mechanism",
      text: `Show me the ${mech.label} mechanism for ${left.join(" and ")}, step by step.` });
  }
  if (left.length || right.length) {
    const cond = data.conditions ? ` (${data.conditions})` : "";
    const lead = data.name ? `Explain the ${data.name}` : "Explain this reaction";
    actions.push({ id: "explain", label: "Explain this reaction", text: `${lead}: ${equation}${cond}.` });
  }
  return actions;
}

export function mechanismFollowUps(data, { mode, step }) {
  const steps = data.steps || [];
  const name = data.name || "this reaction";
  const first = mode === "step" && steps[step]
    ? { id: "step", label: "Explain this step",
        text: `Explain step ${step + 1} of ${steps.length} in the mechanism "${name}": ${steps[step].label}.` }
    : { id: "overview", label: "Explain this mechanism", text: `Explain the mechanism "${name}" step by step.` };
  return [
    first,
    { id: "quiz", label: "Quiz me on this mechanism",
      text: `Quiz me on the mechanism "${name}": ask one question at a time and wait for my answer.` },
  ];
}

// --- Laborgrafiken und Protein -----------------------------------------------------

export function spectrumFollowUps(data) {
  const of = data.name ? ` of ${data.name}` : "";
  const kind = data.spectrum_type ? `${data.spectrum_type} ` : "";
  return [{ id: "explain", label: "Explain this spectrum",
    text: `Explain the ${kind}spectrum${of}: which signals belong to which structural features?` }];
}

export function tlcFollowUps(data) {
  const lanes = (data.lanes || []).map((l) => l.name).filter(Boolean);
  const which = lanes.length ? ` with the lanes ${lanes.join(", ")}` : "";
  return [{ id: "explain", label: "Explain this TLC plate",
    text: `Explain this TLC plate${which}: what do the Rf values say about the compounds?` }];
}

export function plotFollowUps(data) {
  if (!data.name) return [];
  return [{ id: "explain", label: "Explain this plot", text: `Explain the plot "${data.name}" and what it shows.` }];
}

export function proteinFollowUps(data) {
  if (!data.name) return [];
  return [{ id: "explain", label: "Explain this protein", text: `Explain the structure and function of ${data.name}.` }];
}
