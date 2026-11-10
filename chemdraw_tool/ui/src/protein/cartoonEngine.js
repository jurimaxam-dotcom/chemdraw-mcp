// Cartoon-Engine des Protein-Panels (E13): Mol* (MIT, molstar.org) als
// schlanker Eigenbau — nur Canvas3D, mmCIF-Leser, Cartoon-, Putty- und
// Ball-and-Stick-Darstellung, kein Plugin, keine Oberfläche.
//
// Wird NICHT in das Panel-Bundle importiert, sondern von vite.config.js mit
// esbuild zu einem IIFE gebaut und als Zeichenkette eingebettet; ProteinView
// führt es erst aus, wenn ein Protein gezeigt wird (protein/loadEngine.js).
// Grund (gemessen 10.11.2026): als normaler Import wertet der Browser die
// 2,4 MB bei jedem Panel-Start aus (+180 ms auch für Molekül-Panels).
//
// Koordinaten kommen schon im Ansichtsrahmen des Servers (x rechts, y oben,
// z zum Betrachter) — die Ruhekamera blickt entlang −z, so zeigen Panel und
// PNG/SVG dieselbe Ausgangsansicht.
import { Canvas3D, Canvas3DContext } from "molstar/lib/mol-canvas3d/canvas3d.js";
import { CIF } from "molstar/lib/mol-io/reader/cif.js";
import { trajectoryFromMmCIF } from "molstar/lib/mol-model-formats/structure/mmcif.js";
import { Structure, StructureElement, StructureProperties, Bond } from "molstar/lib/mol-model/structure.js";
import { CartoonRepresentationProvider } from "molstar/lib/mol-repr/structure/representation/cartoon.js";
import { PuttyRepresentationProvider } from "molstar/lib/mol-repr/structure/representation/putty.js";
import { BallAndStickRepresentationProvider } from "molstar/lib/mol-repr/structure/representation/ball-and-stick.js";
import { ColorTheme } from "molstar/lib/mol-theme/color.js";
import { SizeTheme } from "molstar/lib/mol-theme/size.js";
import { Task } from "molstar/lib/mol-task/index.js";
import { SyncRuntimeContext } from "molstar/lib/mol-task/execution/synchronous.js";
import { AssetManager } from "molstar/lib/mol-util/assets.js";
import { Color } from "molstar/lib/mol-util/color/index.js";
import { SecondaryStructureProvider } from "molstar/lib/mol-model-props/computed/secondary-structure.js";
import { Vec3 } from "molstar/lib/mol-math/linear-algebra.js";
import { resizeCanvas } from "molstar/lib/mol-canvas3d/util.js";
import { Binding } from "molstar/lib/mol-util/binding.js";
import { ButtonsType, ModifiersKeys } from "molstar/lib/mol-util/input/input-observer.js";
import { ELEMENT_COLOR } from "./colors.js";

const hex = (s) => Color(parseInt(String(s).replace("#", ""), 16));

async function parse(text) {
  const parsed = await CIF.parse(text).run();
  if (parsed.isError) throw new Error(String(parsed.message || parsed));
  const models = await trajectoryFromMmCIF(parsed.result.blocks[0]).run();
  const model = await Task.resolveInContext(models.getFrameAtIndex(0));
  const structure = Structure.ofModel(model);
  await SecondaryStructureProvider.attach({ runtime: SyncRuntimeContext, assetManager: new AssetManager() }, structure);
  return structure;
}

// Ein Farbthema, das je Rest eine vorgegebene Farbe nimmt: Schlüssel
// "Kette:label_seq_id" → Color. So stimmen Panel und Datei Farbe für Farbe.
function lookupTheme(colors, fallback) {
  const fb = hex(fallback);
  const table = new Map([...colors].map(([k, v]) => [k, hex(v)]));
  const pick = (loc) => table.get(`${StructureProperties.chain.label_asym_id(loc)}:${StructureProperties.residue.label_seq_id(loc)}`) ?? fb;
  const factory = (ctx, props) => ({
    factory,
    granularity: "group",
    preferSmoothing: false,
    color: (location) => {
      if (StructureElement.Location.is(location)) return pick(location);
      if (Bond.isLocation(location)) {
        const l = StructureElement.Location.create(location.aStructure, location.aUnit, location.aUnit.elements[location.aIndex]);
        return pick(l);
      }
      return fb;
    },
    props,
    description: "per-residue colours from the panel",
  });
  return factory;
}

// Elementfarben aus colors.js (= protein_render.ELEMENT_COLOR); Mol* nennt
// Elemente in Großbuchstaben (FE, ZN)
const ELEMENT = Object.fromEntries(Object.entries(ELEMENT_COLOR).map(([k, v]) => [k.toUpperCase(), v]));

function elementTheme() {
  const fb = hex(ELEMENT.C);
  const of = (loc) => hex(ELEMENT[StructureProperties.atom.type_symbol(loc)] || ELEMENT.C);
  const factory = (ctx, props) => ({
    factory,
    granularity: "group",
    color: (location) => {
      if (StructureElement.Location.is(location)) return of(location);
      if (Bond.isLocation(location)) {
        return of(StructureElement.Location.create(location.aStructure, location.aUnit, location.aUnit.elements[location.aIndex]));
      }
      return fb;
    },
    props,
    description: "element colours",
  });
  return factory;
}

/**
 * Cartoon in `container` zeichnen. `scene` = {protein: mmCIF-Text, ligands:
 * mmCIF-Text | "", colors: Map("A:12" → "#hex"), fallback: "#hex"}.
 * Rückgabe: Steuerung {setColors, setStyle, resetView, snapshot, dispose}.
 * Wirft, wenn kein WebGL-Kontext entsteht — der Aufrufer fällt dann auf die
 * SVG-Spur zurück.
 */
export async function create(container, scene, options = {}) {
  const canvas = document.createElement("canvas");
  canvas.style.cssText = "position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none";
  canvas.setAttribute("data-cartoon", "");
  container.appendChild(canvas);
  let canvas3d;
  try {
    const ctx = Canvas3DContext.fromCanvas(canvas, new AssetManager(),
      { preserveDrawingBuffer: true, antialias: true, failIfMajorPerformanceCaveat: false },
      { pixelScale: Math.min(2, window.devicePixelRatio || 1) });
    canvas3d = Canvas3D.create(ctx);
    canvas3d.setProps((p) => {
      p.camera.mode = "orthographic";
      p.camera.helper.axes = { name: "off", params: {} };
      p.cameraFog = { name: "on", params: { intensity: 25 } };
      p.renderer.backgroundColor = hex(options.background || "#ffffff");
      p.renderer.ambientIntensity = 0.45;
      p.postprocessing.occlusion = { name: "on", params: { ...p.postprocessing.occlusion.params, samples: 32, radius: 5, bias: 0.8, blurKernelSize: 15 } };
      p.postprocessing.outline = { name: "on", params: { scale: 1, threshold: 0.33, color: Color(0x222222), includeTransparent: true } };
      p.multiSample.mode = "on";
      p.transparentBackground = false;
      // Kein Nachlauf: Drehen/Zoomen folgen direkt der Hand, und „Reset“ landet
      // genau in der Ruhelage statt von gedämpftem Restschwung überlagert zu werden
      p.trackball.staticMoving = true;
    }, true);
  } catch (err) {
    canvas.remove();
    throw err;
  }
  // Mol* bemisst die Zeichenfläche nicht selbst (das macht sonst das Plugin)
  const pixelScale = Math.min(2, window.devicePixelRatio || 1);
  // Ändert sich die Fläche (das Panel blendet nach dem Start Leisten ein, der
  // Host verbreitert das iframe), passt die Ruhelage neu ein — solange niemand
  // gedreht oder gezoomt hat. Gemessen 10.11.: sonst Startradius 16,4 statt
  // 19,9 Å, das Lysozym ragte oben/unten aus der Fläche.
  let pristine = true;
  let fitted = null; // rest() — erst gesetzt, wenn die Struktur geladen ist
  const resize = () => {
    resizeCanvas(canvas, container, pixelScale);
    canvas3d.handleResize();
    if (pristine && fitted) canvas3d.camera.setState(fitted(), 0);
  };
  resize();
  // Das Panel steht im Chatverlauf: ein bloßes Mausrad soll den Chat scrollen,
  // nicht zoomen. Ein Capture-Listener am Container hält es von Mol* fern (und
  // verhindert nichts → der Host scrollt). Strg/⌘+Rad und Trackpad-Pinch
  // (Chromium/WebKit: Rad mit ctrlKey) gehen durch und zoomen; preventDefault,
  // damit der Host nicht die ganze Seite vergrößert. Mol* führt Modifier aus
  // Tastaturereignissen — ein Pinch hat keine —, also passt die Zoom-Bindung
  // auf „ohne“ und „mit Strg/⌘“. Bindungen sind in Mol* 5.13 Attribute, keine Props.
  canvas3d.input.noScroll = false;
  const onWheel = (ev) => {
    if (ev.ctrlKey || ev.metaKey) {
      ev.preventDefault();
      pristine = false;
    } else ev.stopPropagation();
  };
  const touched = () => { pristine = false; };
  container.addEventListener("pointerdown", touched, true);
  container.addEventListener("wheel", onWheel, { capture: true, passive: false });
  const wheel = (mods) => Binding.Trigger(ButtonsType.Flag.Auxilary, ModifiersKeys.create(mods));
  canvas3d.setAttribs({
    trackball: {
      bindings: {
        ...canvas3d.attribs.trackball.bindings,
        scrollZoom: Binding([wheel({}), wheel({ control: true }), wheel({ meta: true })], "Zoom", "Ctrl/Cmd+scroll or pinch"),
        scrollFocus: Binding.Empty,
        scrollFocusZoom: Binding.Empty,
      },
    },
  });
  const observer = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
  observer?.observe(container);
  canvas3d.animate();

  const reprCtx = { webgl: canvas3d.webgl, colorThemeRegistry: ColorTheme.createRegistry(), sizeThemeRegistry: SizeTheme.createRegistry() };
  const protein = await parse(scene.protein);
  const ligands = scene.ligands ? await parse(scene.ligands) : null;
  let style = options.style || "cartoon";
  let colors = scene.colors;
  let fallback = scene.fallback || "#8a8f98";

  const cartoonParams = {
    ...CartoonRepresentationProvider.defaultValues,
    quality: "custom",
    linearSegments: 10,
    radialSegments: 20,
    sizeFactor: 0.25,
    aspectRatio: 5,
    arrowFactor: 1.5,
    tubularHelices: false,
    helixProfile: "elliptical",
    visuals: ["polymer-trace", "polymer-gap"],
    material: { metalness: 0, roughness: 0.4, bumpiness: 0 },
  };
  const puttyParams = { ...PuttyRepresentationProvider.defaultValues, quality: "custom", linearSegments: 8, radialSegments: 16, sizeFactor: 0.25, material: { metalness: 0, roughness: 0.4, bumpiness: 0 } };

  const cartoon = CartoonRepresentationProvider.factory(reprCtx, CartoonRepresentationProvider.getParams);
  const putty = PuttyRepresentationProvider.factory(reprCtx, PuttyRepresentationProvider.getParams);
  const sticks = ligands ? BallAndStickRepresentationProvider.factory(reprCtx, BallAndStickRepresentationProvider.getParams) : null;

  const theme = () => ({
    color: lookupTheme(colors, fallback)({ structure: protein }, {}),
    size: reprCtx.sizeThemeRegistry.create("uniform", { structure: protein }, { value: 1 }),
  });

  async function draw() {
    const active = style === "trace" ? putty : cartoon;
    const idle = style === "trace" ? cartoon : putty;
    active.setTheme(theme());
    await active.createOrUpdate(style === "trace" ? puttyParams : cartoonParams, protein).run();
    if (!canvas3d.hasRepr?.(active)) canvas3d.add(active);
    canvas3d.remove(idle);
    canvas3d.requestDraw();
  }
  await draw();
  if (sticks) {
    sticks.setTheme({
      color: elementTheme()({ structure: ligands }, {}),
      size: reprCtx.sizeThemeRegistry.create("physical", { structure: ligands }),
    });
    await sticks.createOrUpdate({ ...BallAndStickRepresentationProvider.defaultValues, sizeFactor: 0.28, sizeAspectRatio: 0.55, quality: "high" }, ligands).run();
    canvas3d.add(sticks);
  }

  // Ruhekamera: Blick entlang −z, y oben, auf die Box der Struktur gepasst
  // (`options.frame` aus dem Panel). getFocus passt einen Radius in die
  // kürzere Bildseite und behielte sonst die aktuelle Blickrichtung — Abstand
  // und Radius nehmen wir von dort, Richtung und Oben setzen wir selbst.
  const box = options.frame;
  const center = box
    ? Vec3.create(box.cx, box.cy, protein.boundary.sphere.center[2])
    : Vec3.clone(protein.boundary.sphere.center);
  const fitRadius = () => {
    if (!box) return protein.boundary.sphere.radius * 0.95;
    const aspect = Math.max(0.1, canvas.clientWidth / Math.max(1, canvas.clientHeight));
    return aspect >= 1 ? Math.max(box.halfH, box.halfW / aspect) : Math.max(box.halfW, box.halfH * aspect);
  };
  const rest = () => {
    const s = canvas3d.camera.getFocus(center, fitRadius());
    const dist = Vec3.distance(s.position, s.target);
    return { ...s, target: Vec3.clone(center), position: Vec3.create(center[0], center[1], center[2] + dist), up: Vec3.create(0, 1, 0) };
  };
  canvas3d.requestCameraReset({ snapshot: rest(), durationMs: 0 });
  canvas3d.commit(true);
  // requestCameraReset passt den Radius selbst an die Szene an; die Ruhelage ist
  // genau rest() — dieselbe, in der die Einblend-Drehung endet und Reset landet
  canvas3d.camera.setState(rest(), 0);
  fitted = rest;

  return {
    canvas,
    canvas3d,
    async setColors(next, fb) {
      colors = next;
      fallback = fb || fallback;
      await draw();
    },
    async setStyle(next) {
      style = next;
      await draw();
    },
    // Farbschema des Hosts wechselt (hell ↔ dunkel) ohne Neuaufbau
    setBackground(color) {
      canvas3d.setProps((p) => { p.renderer.backgroundColor = hex(color); });
    },
    resetView(durationMs = 300) {
      pristine = true;
      canvas3d.camera.setState(rest(), durationMs);
    },
    /** Kamera um `angle` (rad) um y gedreht starten und in `ms` zur Ruhe drehen. */
    intro(angle, ms) {
      const r = rest();
      const dist = Vec3.distance(r.position, r.target);
      const start = { ...r, position: Vec3.create(center[0] + Math.sin(angle) * dist, center[1], center[2] + Math.cos(angle) * dist) };
      canvas3d.camera.setState(start, 0);
      canvas3d.camera.setState(r, ms);
    },
    /** PNG des aktuellen Bildes in `scale`-facher Auflösung (data:-URL). */
    async snapshot(scale = 3) {
      const w = Math.max(1, Math.round(canvas.clientWidth * scale));
      const h = Math.max(1, Math.round(canvas.clientHeight * scale));
      const pass = canvas3d.getImagePass({ cameraHelper: { axes: { name: "off", params: {} } } });
      const data = await pass.getImageData(SyncRuntimeContext, w, h);
      const out = document.createElement("canvas");
      out.width = w;
      out.height = h;
      out.getContext("2d").putImageData(data, 0, 0);
      return { url: out.toDataURL("image/png"), width: w, height: h };
    },
    dispose() {
      observer?.disconnect();
      container.removeEventListener("wheel", onWheel, { capture: true });
      container.removeEventListener("pointerdown", touched, true);
      try { canvas3d.dispose(); } finally { canvas.remove(); }
    },
  };
}

// Für den Panel-Lader: das IIFE legt die Engine hier ab.
if (typeof window !== "undefined") window.__chemCartoon = { create };
