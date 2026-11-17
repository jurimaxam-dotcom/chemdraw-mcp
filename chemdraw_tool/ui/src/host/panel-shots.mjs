// Bildschau für Lesbarkeit: dieselben Panel-Fälle im hellen UND dunklen Schema,
// über denselben sandboxed Host wie host.e2e.mjs und den echten Server (Wegwerf-HOME,
// nichts landet in ~/ChemDraw-Output). Kein Test — Bilder zum Ansehen, vorher/nachher.
// usage: node src/host/panel-shots.mjs <ordner>   (Netz für PubChem-Namen; SHOTS_ONLY=a-*,e3-molekuel-chat1000 filtert)
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { build } from "esbuild";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdtempSync, mkdirSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..", "..");
const dest = process.argv[2] || join(tmpdir(), "chemdraw-panel-shots");
mkdirSync(dest, { recursive: true });
const out = join(mkdtempSync(join(tmpdir(), "panel-shots-")), "host.js");
await build({ entryPoints: [join(here, "host-entry.js")], bundle: true, format: "iife", outfile: out, logLevel: "error" });

const serverBin = join(repo, ".venv", "bin", "chemdraw-tool-server");
if (!existsSync(serverBin)) throw new Error("venv fehlt — erst `uv sync`");
const client = new Client({ name: "panel-shots", version: "0.0.0" });
const wegwerfHome = mkdtempSync(join(tmpdir(), "panel-shots-home-"));
// Volles Profil: Scope und Batch gehören mit in die Schau.
await client.connect(new StdioClientTransport({ command: serverBin, env: { ...process.env, HOME: wegwerfHome, CHEMDRAW_PROFILE: "full" }, cwd: repo }));

const BOC = "O=C(c1ccccc1)CC1CCN(C(=O)OC(C)(C)C)CC1";
const PORPHYRIN = {
  reactants: ["CC1=C(CCC(=O)O)C2=CC3=C(CCC(=O)O)C(C)=C(N3)C=C4C(C)=C(C=C)C(=N4)C=C5C(C=C)=C(C)C(=N5)C=C1N2", "[Fe+2]"], products: ["CC1=C(C2=CC3=NC(=CC4=C(C(=C([N-]4)C=C5C(=C(C(=N5)C=C1[N-]2)C)C=C)C)C=C)C(=C3CCC(=O)O)C)CCC(=O)O.[Fe+2]", "[H+]"], coefficients: [1, 1, 1, 2],
  conditions: "ferrochelatase", name: "Protoporphyrin IX → heme b",
};
// [Datei, Tool, Argumente, iframe-Breite]; 930 px ≈ Panelbreite in Claude Desktop (Stand 10.11.2026).
const CASES = [
  // Die zwei Panelbilder der Nutzerdoku (docs/images/panel-molecule.png, panel-peptide.png = helle Fassung).
  ["doku-molekuel", "generate_molecule", { name_or_smiles: "thalidomide" }, 700],
  ["doku-peptid", "generate_molecule", { name_or_smiles: "Ala-Trp-Lys-Ser-Gly" }, 700],
  ["boc-abgekuerzt", "generate_molecule", { name_or_smiles: BOC, abbreviate_groups: true }, 930],
  ["aspirin-abgekuerzt", "generate_molecule", { name_or_smiles: "aspirin", abbreviate_groups: true }, 930],
  ["porphyrin-abgekuerzt", "generate_reaction", { ...PORPHYRIN, abbreviate_groups: true }, 930],
  ["porphyrin", "generate_reaction", PORPHYRIN, 930],
  ["knallgas", "generate_reaction", { reactants: ["H2", "O2"], products: ["H2O"], coefficients: [2, 1, 2] }, 930],
  ["veresterung", "generate_reaction", { reactants: ["CC(=O)O", "CCO"], products: ["CC(=O)OCC", "O"], conditions: "H2SO4", name: "Fischer esterification" }, 930],
  ["veresterung-510", "generate_reaction", { reactants: ["CC(=O)O", "CCO"], products: ["CC(=O)OCC", "O"], conditions: "H2SO4", name: "Fischer esterification" }, 510],
  ["mechanismus-kette", "generate_mechanism", { reaction_type: "fischer_ester", substrates: ["CCCCCCCCCCCCCCCCCC(=O)O", "CCO"] }, 930],
  ["vergleich", "compare_molecules", { structures: [BOC, "O=C(c1ccccc1)CC1CCNCC1"] }, 930],
  ["batch-abgekuerzt", "batch_generate", { molecules: [BOC, "aspirin"], abbreviate_groups: true }, 930],
  ["scope-abgekuerzt", "generate_scope_table", { entries: [{ structure: BOC }, { structure: "O=C(c1ccccc1)CC1CCN(S(=O)(=O)c2ccc(C)cc2)CC1" }], abbreviate_groups: true }, 930],
];

// Diagramm-Panels (Etappe 1, 16.11.2026): je Fall Chat 1000 px (inhaltsgroß),
// Vollbild 1000×700 und Seitenpanel 320×700 (feste Höhe vom Host).
const IR_NAH = { spectrum_type: "ir", title: "Aspirin IR", peaks: [
  { position: 1750, intensity: 1, label: "Ester-C=O" }, { position: 1690, intensity: 1, label: "Säure-C=O" }] };
const DC = { title: "DC-Platte", lanes: [
  { name: "Edukt", spots: [{ rf: 0.3, label: "Edukt" }] }, { name: "Produkt", spots: [{ rf: 0.65, label: "Produkt" }] }] };
const TITRATION = { substance: "Acetic acid", pka_values: [4.76], c_acid: 0.1, v_acid_ml: 25, c_titrant: 0.1,
  indicator: { name: "Phenolphthalein", ph_range: [8.2, 10.0] } };
const SPEZIES = { substance: "Phosphoric acid", pka_values: [2.15, 7.2, 12.35] };
const VERGLEICH = { structures: ["CC(C)Cc1ccc(cc1)C(C)C(=O)O", "COc1ccc2cc(ccc2c1)[C@H](C)C(=O)O"], labels: ["Ibuprofen", "Naproxen"] };
for (const [file, name, input] of [
  ["plot-spektrum", "generate_spectrum", IR_NAH],
  ["plot-dc", "generate_tlc", DC],
  ["plot-titration", "generate_titration_curve", TITRATION],
  ["plot-spezies", "generate_species_distribution", SPEZIES],
  ["plot-vergleich", "compare_molecules", VERGLEICH],
]) {
  CASES.push([`${file}-chat1000`, name, input, 1000]);
  CASES.push([`${file}-1000x700`, name, input, 1000, 700]);
  CASES.push([`${file}-320x700`, name, input, 320, 700]);
}
// Vollprofil-Kurven über dieselbe PlotView: je einmal im Chat bei 1000 px.
for (const [file, name, input] of [
  ["plot-kalibrierung", "generate_calibration_curve", { concentrations: [0, 2, 4, 6, 8, 10], signals: [0.01, 0.21, 0.40, 0.62, 0.80, 1.01],
    unknown_signals: [0.47, 0.55], substance: "Paracetamol", x_label: "c [mg/L]", y_label: "A" }],
  ["plot-pk", "generate_pk_curve", { dose_mg: 500, vd_l: 40, half_life_h: 6, ka_per_h: 1.2, bioavailability: 0.8, tau_h: 8,
    mec_mg_per_l: 5, mtc_mg_per_l: 20, drug: "Beispiel" }],
  ["plot-dosis", "generate_dose_response", { ec50: 10, antagonist_concentration: 30, antagonist_kb: 10, drug: "Agonist" }],
]) CASES.push([`${file}-chat1000`, name, input, 1000]);
// Etappe 2 (16.11.2026): batch_generate als Raster. Sechs Stoffe in drei Breiten,
// drei Stoffe mit einem Fehlschlag, und die Detailansicht nach Klick auf eine Karte.
const SECHS = { molecules: ["benzene", "toluene", "phenol", "aspirin", "caffeine", "ibuprofen"] };
const MIT_FEHLER = { molecules: ["benzene", "xyzzyl", "phenol"] };
CASES.push(["batch6-chat1000", "batch_generate", SECHS, 1000]);
CASES.push(["batch6-1000x700", "batch_generate", SECHS, 1000, 700]);
CASES.push(["batch6-320x700", "batch_generate", SECHS, 320, 700]);
CASES.push(["batch-fehler-chat1000", "batch_generate", MIT_FEHLER, 1000]);
CASES.push(["batch6-detail-chat1000", "batch_generate", SECHS, 1000, undefined, ".batch-card >> nth=2"]);
CASES.push(["batch6-detail-320x700", "batch_generate", SECHS, 320, 700, ".batch-card >> nth=2"]);
// Etappe 3 (16.11.2026): einheitliche Bedienelemente — Molekül (2D/3D), Datenblatt aus
// lookup_molecule_data, Mechanismus, 3D-Einstieg, Protein und Reaktion in drei Breiten.
const KOFFEIN = { name_or_smiles: "caffeine" };
const SN2 = { reaction_type: "sn2", substrates: ["C[C@@H](Br)CC", "[C-]#N"] };
const VERESTERUNG = { reactants: ["CC(=O)O", "CCO"], products: ["CC(=O)OCC", "O"], conditions: "H2SO4", name: "Fischer esterification" };
const DRITTE = [
  ["e3-molekuel", "generate_molecule", KOFFEIN],
  ["e3-molekuel-3d", "generate_molecule", KOFFEIN, "[data-view-axis] button:has-text('3D')"],
  ["e3-datenblatt", "lookup_molecule_data", { name: "paracetamol" }],
  ["e3-datenblatt-struktur", "lookup_molecule_data", { name: "paracetamol" }, "[role=tab]:has-text('Structure')"],
  ["e3-mechanismus", "generate_mechanism", SN2],
  ["e3-3d", "generate_3d", { name_or_smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O", label: "Caffeine" }],
  ["e3-protein", "generate_protein_or_antibody", { name: "trastuzumab" }],
  ["e3-reaktion", "generate_reaction", VERESTERUNG],
  ["e3-scope", "generate_scope_table", { entries: [{ structure: "CC(=O)c1ccccc1" }, { structure: "CC(=O)c1ccc(Cl)cc1" }, { structure: "CC(=O)c1ccc(OC)cc1" }, { structure: "CC(=O)c1ccc(F)cc1" }] }],
];
for (const [file, name, input, klick] of DRITTE) {
  CASES.push([`${file}-chat1000`, name, input, 1000, undefined, klick]);
  CASES.push([`${file}-1000x700`, name, input, 1000, 700, klick]);
  CASES.push([`${file}-320x700`, name, input, 320, 700, klick]);
}
// Etappe 4 (16.11.2026): Datenblatt-Zeilen (PubChem, GHS), Gruppen-Sektion mit und ohne
// angeheftete Gruppe, die kompakte Zeile „Continue in chat“ — Koffein und Aspirin wegen der Höhe.
const VIERTE = [
  ["e4-molekuel", "generate_molecule", KOFFEIN],
  ["e4-aspirin", "generate_molecule", { name_or_smiles: "aspirin" }],
  ["e4-gruppe-angeheftet", "generate_molecule", KOFFEIN, "button.functional-group >> nth=0"],
  ["e4-datenblatt", "lookup_molecule_data", { name: "paracetamol" }],
  ["e4-datenblatt-ghs", "lookup_molecule_data", { name: "paracetamol" }, "[role=tab]:has-text('GHS')"],
  ["e4-reaktion", "generate_reaction", VERESTERUNG],
];
for (const [file, name, input, klick] of VIERTE) {
  CASES.push([`${file}-chat1000`, name, input, 1000, undefined, klick]);
  CASES.push([`${file}-1000x700`, name, input, 1000, 700, klick]);
  CASES.push([`${file}-320x700`, name, input, 320, 700, klick]);
}
// Etappe 5 (16.11.2026): Mechanismus-Übersicht (SN2, Fischer mit acht Schritten), Anki-Deck,
// 3D mit Formel und „Reset view“, Protein-Höhe, Kalibrier-Notizen, Datenblatt und DC-Platte.
const ANKI = { deck_name: "Koffein und Paracetamol", cards: [
  { front: { structure: "caffeine" }, back: { text: "<b>Koffein</b> (Caffeine)<br>Methylxanthin, Adenosin-Antagonist" } },
  { front: { structure: "paracetamol" }, back: { text: "<b>Paracetamol</b><br>Analgetikum, Antipyretikum" } },
  { front: { text: "Welche funktionelle Gruppe trägt Aspirin neben der Carbonsäure?" }, back: { text: "Einen Phenylester (Acetylester)", structure: "aspirin" } },
] };
const ANKI_VIELE = { deck_name: "Lösungsmittel", cards: ["methanol", "ethanol", "acetone", "toluene", "hexane", "benzene", "phenol", "pyridine", "acetonitrile", "chloroform"]
  .map((s) => ({ front: { text: `Formel von ${s}?` }, back: { text: s } })) };
const KALIBRIERUNG = { concentrations: [0, 2, 4, 6, 8, 10], signals: [0.01, 0.21, 0.40, 0.62, 0.80, 1.01],
  unknown_signals: [0.47, 0.55], substance: "Paracetamol", x_label: "c [mg/L]", y_label: "A" };
const FUENFTE = [
  ["e5-mechanismus", "generate_mechanism", SN2],
  ["e5-mechanismus-fischer", "generate_mechanism", { reaction_type: "fischer_ester", substrates: ["CCCCCCCCCCCCCCCCCC(=O)O", "CCO"] }],
  ["e5-mechanismus-schritt2", "generate_mechanism", SN2, "[aria-label^='Open step 2']"],
  ["e5-anki", "export_anki_deck", ANKI],
  ["e5-anki-viele", "export_anki_deck", ANKI_VIELE],
  ["e5-3d", "generate_3d", { name_or_smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O", label: "Caffeine" }],
  ["e5-molekuel-3d", "generate_molecule", KOFFEIN, "[data-view-axis] button:has-text('3D')"],
  ["e5-protein", "generate_protein_or_antibody", { name: "trastuzumab" }],
  ["e5-protein-lysozym", "generate_protein_or_antibody", { name: "lysozyme" }],
  ["e5-protein-schema", "generate_protein_or_antibody", { name: "trastuzumab" }, "[role='tab']:has-text('Scheme')"],
  ["e5-kalibrierung", "generate_calibration_curve", KALIBRIERUNG],
  ["e5-datenblatt", "lookup_molecule_data", { name: "paracetamol" }],
  ["e5-dc", "generate_tlc", DC],
];
for (const [file, name, input, klick] of FUENFTE) {
  CASES.push([`${file}-chat1000`, name, input, 1000, undefined, klick]);
  CASES.push([`${file}-1000x700`, name, input, 1000, 700, klick]);
  CASES.push([`${file}-320x700`, name, input, 320, 700, klick]);
}
// Etappe 6 (16.11.2026): Study in der vergrößerten Ansicht, Mechanismen im Dunkeln, 3D-Größe.
const SECHSTE = [
  ["e6-study", "generate_molecule", { name_or_smiles: "aspirin" }, "[role=tab]:has-text('Study')"],
  ["e6-datenblatt-study", "lookup_molecule_data", { name: "paracetamol" }, "[role=tab]:has-text('Study')"],
  ["e6-mechanismus-sn2", "generate_mechanism", SN2],
  ["e6-mechanismus-sn2-schritt2", "generate_mechanism", SN2, "[aria-label^='Open step 2']"],
  ["e6-mechanismus-sn1", "generate_mechanism", { reaction_type: "sn1", substrates: ["CC(C)(C)Cl", "O"] }],
  ["e6-mechanismus-sn1-iod", "generate_mechanism", { reaction_type: "sn1", substrates: ["CC(C)(C)I", "[OH-]"] }],
  ["e6-mechanismus-fischer", "generate_mechanism", { reaction_type: "fischer_ester", substrates: ["CC(=O)O", "CCO"] }],
  ["e6-molekuel-3d", "generate_molecule", KOFFEIN, "[data-view-axis] button:has-text('3D')"],
  ["e6-3d", "generate_3d", { name_or_smiles: "Cn1c(=O)c2c(ncn2C)n(C)c1=O", label: "Caffeine" }],
];
for (const [file, name, input, klick] of SECHSTE) {
  CASES.push([`${file}-chat1000`, name, input, 1000, undefined, klick]);
  CASES.push([`${file}-1000x700`, name, input, 1000, 700, klick]);
  CASES.push([`${file}-320x700`, name, input, 320, 700, klick]);
}
// Panel-Umbau Paket A (17.11.2026, docs/design/panel-ueberarbeitung-2026-11-17.md §7): Molekül (2D, 3D,
// Data, Study), Datenblatt, Batch (Raster, Detail), Auswahl, Platzhalter und Fehler in Chat 1000 und 860
// (inline-Kontext wie Desktop, damit Expand erscheint), Seitenpanel 320×700 und Vollbild 1000×700.
// Je Bild eine Messzeile (aMetrics): Panelhöhe, Bühne, Inhaltsbreite, waagrechtes Rollen.
// Optionen je Fall: klick (Selektor vor dem Bild), hold (nur toolinput, kein Ergebnis), fehler (isError zulassen).
const A_FAELLE = [
  ["a-molekuel", "generate_molecule", KOFFEIN],
  ["a-molekuel-stereo", "generate_molecule", { name_or_smiles: "methylphenidate" }],
  ["a-molekuel-3d", "generate_molecule", KOFFEIN, { klick: "[data-view-axis] button:has-text('3D')" }],
  ["a-molekuel-data", "generate_molecule", KOFFEIN, { klick: "[role=tab]:has-text('Data')" }],
  ["a-molekuel-study", "generate_molecule", KOFFEIN, { klick: "[role=tab]:has-text('Study')" }],
  ["a-datenblatt", "lookup_molecule_data", { name: "paracetamol" }],
  ["a-batch6", "batch_generate", SECHS],
  ["a-batch6-detail", "batch_generate", SECHS, { klick: ".batch-card >> nth=2" }],
  ["a-batch-fehler", "batch_generate", MIT_FEHLER],
  ["a-auswahl", "generate_molecule", { name_or_smiles: "glucose" }],
  ["a-platzhalter", "generate_molecule", KOFFEIN, { hold: true }],
  ["a-platzhalter-batch", "batch_generate", SECHS, { hold: true }],
  ["a-fehler", "generate_molecule", { name_or_smiles: "C1CC" }, { fehler: true }],
];
for (const [file, name, input, opt = {}] of A_FAELLE) {
  CASES.push([`${file}-chat1000`, name, input, 1000, undefined, opt.klick, { ...opt, inline: true }]);
  CASES.push([`${file}-chat860`, name, input, 860, undefined, opt.klick, { ...opt, inline: true }]);
  CASES.push([`${file}-1000x700`, name, input, 1000, 700, opt.klick, opt]);
  CASES.push([`${file}-320x700`, name, input, 320, 700, opt.klick, opt]);
}
// Panelbilder der Nutzerdoku (docs/images/, nur hell; nach dem Panel-Umbau 17.11.2026 neu):
// SHOTS_ONLY=doku-* node src/host/panel-shots.mjs <ordner>, dann <name>-light.png nach docs/images/<datei>.png.
// Breite und Skalierung wie die Bilder vom 10.11.: 700-px-Panel, als 1400 px (scale 2), 700 px (scale 1) oder
// 1000 px (scale 1000/700, die zwei Proteinbilder) gespeichert.
// klicks laufen nacheinander, warte ist der Selektor, der danach stehen muss (sonst rot statt Ladebild).
const DOKU = [
  // docs/images/panel-chair.png
  ["doku-sessel", "generate_molecule", { name_or_smiles: "beta-D-glucose" }, 700,
    { scale: 2, klicks: ["[data-view-axis] button:has-text('Chair')"], warte: "[data-view-axis] button[aria-pressed='true']:has-text('Chair')" }],
  // docs/images/panel-mechanism-step1.png
  ["doku-mechanismus-schritt1", "generate_mechanism", { reaction_type: "sn2", substrates: ["(R)-2-bromobutane", "cyanide"] }, 700,
    { scale: 2, klicks: ["[role=tab]:has-text('Step by step')"], warte: "[role=tab][aria-selected='true']:has-text('Step by step')" }],
  // docs/images/panel-reaction.png und panel-reaction-applied.png
  ["doku-reaktion", "generate_reaction", { reactants: ["hydrogen", "oxygen"], products: ["water"] }, 700,
    { scale: 2, warte: "[data-testid='balance-badge'][data-state='unbalanced']" }],
  ["doku-reaktion-angewandt", "generate_reaction", { reactants: ["hydrogen", "oxygen"], products: ["water"] }, 700,
    { scale: 1, klicks: ["button:has-text('Apply coefficients')"], warte: "[data-testid='balance-badge'][data-state='balanced']" }],
  // docs/images/protein-panel-lysozyme.png und panel-igg-scheme.png (Mol*: warten, bis die Engine steht)
  ["doku-protein-lysozym", "generate_protein_or_antibody", { name: "lysozyme" }, 700,
    { scale: 1000 / 700, warte: "[data-protein-viewer='ready']", nachlauf: 2500 }],
  ["doku-igg-schema", "generate_protein_or_antibody", { name: "trastuzumab" }, 700,
    { scale: 1000 / 700, klicks: ["[role=tab]:has-text('Scheme')"], warte: "svg[data-igg-scheme]" }],
];
for (const [file, name, input, width, opt] of DOKU) CASES.push([file, name, input, width, undefined, undefined, { ...opt, themes: ["light"] }]);
const fixedCtx = (width, height) => ({ displayMode: "fullscreen", availableDisplayModes: ["inline", "fullscreen"],
  platform: "desktop", containerDimensions: { width, height } });
const inlineCtx = (width) => ({ displayMode: "inline", availableDisplayModes: ["inline", "fullscreen"],
  platform: "desktop", containerDimensions: { width, maxHeight: 6000 } });

// Maße für Paket A: Panelhöhe (wie Desktop sie übernimmt: #root + body-Polster), die Bühne
// (.stage, sonst die alte Zeichenfläche bzw. Kuhle), Inhaltsbreite, Rollen, Haarlinien.
function aMetrics() {
  const de = document.documentElement;
  const q = (s) => document.querySelector(s);
  const stage = q("[data-view-3d]") || q(".stage") || q(".structure-canvas") || q(".panel-state") || q(".placeholder-canvas");
  const body = getComputedStyle(document.body);
  const inhalt = document.body.clientWidth - parseFloat(body.paddingLeft) - parseFloat(body.paddingRight);
  const b = stage?.getBoundingClientRect();
  // Sichtbare Kanten (border-top/-bottom ≥ 1 px, nicht transparent) — Ziel: genau eine (Fuß).
  const linien = [...document.querySelectorAll("body *")].filter((el) => {
    if (!el.getClientRects().length) return false;
    const cs = getComputedStyle(el);
    const sichtbar = (w, s, c) => parseFloat(w) >= 1 && s !== "none" && !/rgba\(\d+, \d+, \d+, 0\)|transparent/.test(c);
    return (sichtbar(cs.borderTopWidth, cs.borderTopStyle, cs.borderTopColor) && sichtbar(cs.borderBottomWidth, cs.borderBottomStyle, cs.borderBottomColor)) === false
      && (sichtbar(cs.borderTopWidth, cs.borderTopStyle, cs.borderTopColor) || sichtbar(cs.borderBottomWidth, cs.borderBottomStyle, cs.borderBottomColor))
      && (cs.borderLeftWidth === "0px" || cs.borderLeftStyle === "none");
  }).map((el) => el.className?.baseVal ?? el.className);
  return {
    panel: Math.ceil(q("#root").getBoundingClientRect().bottom) + 16,
    buehne: b ? `${Math.round(b.width)}×${Math.round(b.height)}` : null,
    inhalt: Math.round(inhalt),
    rollenX: de.scrollWidth > de.clientWidth + 1,
    rollenY: de.scrollHeight > innerHeight + 1,
    linien,
  };
}

// Maße der Diagrammfläche: Karte, gezeichnete Figur (viewBox, „meet“), Rollen ja/nein.
function plotMetrics() {
  const card = document.querySelector(".plot-svg, .spectrum-svg, .tlc-svg");
  const svg = card?.querySelector("svg");
  if (!svg) return { rollen: document.documentElement.scrollHeight > innerHeight + 1, hoehe: document.documentElement.scrollHeight };
  const c = card.getBoundingClientRect(), r = svg.getBoundingClientRect();
  const vb = svg.viewBox.baseVal;
  const k = vb && vb.width ? Math.min(r.width / vb.width, r.height / vb.height) : 1;
  return { karte: `${Math.round(c.width)}×${Math.round(c.height)}`, figur: `${Math.round(vb.width * k)}×${Math.round(vb.height * k)}`,
    massstab: +k.toFixed(2), rollen: document.documentElement.scrollHeight > innerHeight + 1,
    hintergrund: getComputedStyle(card).backgroundColor };
}

const only = process.env.SHOTS_ONLY?.split(",");
const tools = (await client.listTools()).tools;
const browser = await chromium.launch();
try {
  for (const [file, name, input, width, fixed, klick, opt = {}] of CASES) {
    if (only && !only.some((o) => file === o || (o.endsWith("*") && file.startsWith(o.slice(0, -1))))) continue;
    const isA = file.startsWith("a-");
    const tool = tools.find((t) => t.name === name);
    const result = await client.callTool({ name, arguments: input });
    if (result.isError && !opt.fehler) { console.log(`✘ ${file}: ${JSON.stringify(result.content).slice(0, 300)}`); continue; }
    const html = (await client.readResource({ uri: tool._meta.ui.resourceUri })).contents[0].text;
    for (const colorScheme of opt.themes || ["light", "dark"]) {
      const page = await browser.newPage({ viewport: { width: width + 20, height: 1400 }, colorScheme, deviceScaleFactor: opt.scale || 1 });
      await page.setContent('<body style="margin:0;background:#888"></body>');
      await page.addScriptTag({ path: out });
      await page.exposeFunction("__callTool", (req) => client.callTool(req));
      const hostContext = fixed ? fixedCtx(width, fixed) : opt.inline ? inlineCtx(width) : undefined;
      await page.evaluate((a) => window.__startHost(a), { html, toolInput: input, toolResult: result, hostContext, holdResult: Boolean(opt.hold) });
      const iframe = page.locator("iframe").last();
      if (!fixed) await iframe.evaluate((el, w) => { el.style.width = `${w}px`; el.style.height = "1380px"; }, width);
      const frame = page.frames().at(-1);
      const bereit = opt.hold ? "[data-testid='tool-placeholder']" : opt.fehler ? "[role=alert]" : "svg";
      await frame.locator(bereit).first().waitFor({ timeout: 30000 });
      await page.waitForTimeout(600);
      // Optionaler Klick vor dem Bild (Detailansicht); fehlt das Element, bleibt die Startansicht.
      if (klick && await frame.locator(klick).count()) {
        await frame.locator(klick).first().click();
        await page.waitForTimeout(2500);
      }
      // Doku-Bilder: Klickfolge, dann muss der Zielzustand stehen — fehlt ein Element, ist der Fall rot.
      for (const k of opt.klicks || []) {
        await frame.locator(k).first().click({ timeout: 30000 });
        await page.waitForTimeout(800);
      }
      if (opt.warte) await frame.locator(opt.warte).first().waitFor({ timeout: 60000 });
      if (opt.nachlauf) await page.waitForTimeout(opt.nachlauf);
      if (fixed) {
        const m = await frame.evaluate(isA ? aMetrics : plotMetrics);
        await page.setViewportSize({ width: width + 20, height: fixed + 20 });
        await iframe.screenshot({ path: join(dest, `${file}-${colorScheme}.png`) });
        console.log(`✔ ${file}-${colorScheme}.png (${width}×${fixed}) ${JSON.stringify(m)}`);
        await page.close();
        continue;
      }
      // Bild nur so hoch wie der Inhalt: Panelhöhe aus dem iframe-Dokument.
      const h = await frame.evaluate(() => Math.ceil(document.getElementById("root").getBoundingClientRect().bottom) + 16);
      await page.setViewportSize({ width: width + 20, height: Math.min(1400, h + 20) });
      await iframe.evaluate((el, hh) => { el.style.height = `${hh}px`; }, h);
      await iframe.screenshot({ path: join(dest, `${file}-${colorScheme}.png`) });
      const m = await frame.evaluate(isA ? aMetrics : plotMetrics);
      console.log(`✔ ${file}-${colorScheme}.png (${width}×${h})${m ? ` ${JSON.stringify(m)}` : ""}`);
      await page.close();
    }
  }
} finally {
  await browser.close();
  await client.close();
}
