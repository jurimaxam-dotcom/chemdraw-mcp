import React, { forwardRef, useEffect, useId, useRef, useState } from "react";
import CopyButton from "./CopyButton";
import FoundAs from "./FoundAs";
import { FooterStatus } from "./PanelFooter";
import { displayPath } from "../utils/displayPath";

// Gemeinsame Bausteine des Panels (docs/design/panel-ueberarbeitung-2026-11-17.md, §4) — der Vertrag
// für die Pakete A, B und C: Kopf-, Bühnen-, Kernwert-, Knopf- und Fußformen gibt es nur hier.
// Aussehen in styles/frame.css, ausschließlich unter eigenen Klassen (.panel, .panel-head, .stage …);
// die alten Haken (.panel-header, .panel-title, .key-facts, .panel-footer …) stehen zusätzlich am
// Element, weil Tests, test:host und die Desktop-Probe auf sie zielen.
//
// Zonen-Reihenfolge (§2): PanelHead → (PanelBody je Reiter) → StageBar → Stage → Facts → Extras → ContinueRow → PanelFoot.
// Jeder Baustein ohne Inhalt rendert nichts; der Abstand kommt aus dem gap von .panel und fällt mit.
//
// A0 (17.11.2026): bereitgestellt, noch von keiner View benutzt.

const cx = (...parts) => parts.filter(Boolean).join(" ");
const isEmpty = (node) => node == null || node === false || node === "";

// --- Symbole: ein Strich-Satz, 16er-Raster, 1,5 px, immer aria-hidden ---------------------------

const ICONS = {
  // zwei Diagonalpfeile nach außen
  expand: <path d="M9.5 2.5h4v4M13.5 2.5 9 7M6.5 13.5h-4v-4M2.5 13.5 7 9" />,
  "chevron-down": <path d="m4 6 4 4 4-4" />,
  "chevron-left": <path d="m10 4-4 4 4 4" />,
  "chevron-right": <path d="m6 4 4 4-4 4" />,
  check: <path d="m3 8.5 3 3 7-7" />,
  download: <path d="M8 2.5v8M4.5 7 8 10.5 11.5 7M3 13.5h10" />,
  copy: <><rect x="5.5" y="5.5" width="8" height="8" rx="1.5" /><path d="M10.5 3.5V3A1.5 1.5 0 0 0 9 1.5H3A1.5 1.5 0 0 0 1.5 3v6A1.5 1.5 0 0 0 3 10.5h.5" /></>,
};

/** Strich-Symbol `name` (expand, chevron-down/-left/-right, check, download, copy); unbekannt → nichts. */
export function Icon({ name, size = 14, className }) {
  const shape = ICONS[name];
  if (!shape) return null;
  return (
    <svg className={cx("icon", `icon-${name}`, className)} width={size} height={size} viewBox="0 0 16 16" fill="none"
      stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {shape}
    </svg>
  );
}

// --- Rahmen ------------------------------------------------------------------------------------

/** article.panel[data-panel=kind] — Spalte mit gap 16; `fill` lässt die Bühne in Fill den Rest nehmen. */
export const Panel = forwardRef(function Panel({ kind, fill = false, className, children, ...rest }, ref) {
  return (
    <article ref={ref} className={cx("panel", className)} data-panel={kind} data-fill={fill ? "" : undefined} {...rest}>
      {children}
    </article>
  );
});

/**
 * div.panel-body — Zonen-Spalte innerhalb eines Reiters (role="tabpanel", data-view …): dieselbe Spalte
 * mit gap 16 und dieselbe Fill-Kette wie .panel, damit Bühne, StageBar und Facts im Reiter wirken wie
 * direkte Kinder des Panels. hidden blendet den Reiter aus.
 */
export const PanelBody = forwardRef(function PanelBody({ className, children, ...rest }, ref) {
  return <div ref={ref} className={cx("panel-body", className)} {...rest}>{children}</div>;
});

/**
 * header.panel-head: links Titel (h2.panel-title), Untertitel (p.panel-subtitle, voller Text im title)
 * und „Found as“; rechts `tabs` und `expand` als fertige Knoten in .panel-actions. `heading` ersetzt
 * Titel und Untertitel ganz (Study: verdeckter Name, Zähler) — dann steht vom Titel nichts im DOM.
 */
export function PanelHead({ title, subtitle, subtitleTitle, foundAs, tabs, expand, heading, className, children, ...rest }) {
  const hasHeading = !isEmpty(heading) || !isEmpty(title) || !isEmpty(subtitle) || !isEmpty(foundAs) || !isEmpty(children);
  const hasActions = !isEmpty(tabs) || !isEmpty(expand);
  if (!hasHeading && !hasActions) return null;
  const subTitle = subtitleTitle ?? (typeof subtitle === "string" ? subtitle : undefined);
  return (
    <header className={cx("panel-head", "panel-header", !isEmpty(tabs) && "has-tabs", !isEmpty(expand) && "has-expand", className)} {...rest}>
      <div className="panel-heading">
        {!isEmpty(heading) ? heading : (
          <>
            {!isEmpty(title) && <h2 className="panel-title">{title}</h2>}
            {!isEmpty(subtitle) && <p className="panel-subtitle" title={subTitle}>{subtitle}</p>}
            {typeof foundAs === "string" ? <FoundAs value={foundAs} /> : foundAs}
          </>
        )}
        {children}
      </div>
      {hasActions && (
        <div className="panel-actions">
          {!isEmpty(tabs) && <div className="panel-head-tabs">{tabs}</div>}
          {!isEmpty(expand) && <div className="panel-head-expand">{expand}</div>}
        </div>
      )}
    </header>
  );
}

/** div.stage-bar über der Bühne: links Achse/Unterreiter, rechts Hinweis (auch als title) und ruhige Knöpfe. */
export function StageBar({ left, right, hint, className, ...rest }) {
  if (isEmpty(left) && isEmpty(right) && isEmpty(hint)) return null;
  const hintText = typeof hint === "string" ? hint : undefined;
  return (
    <div className={cx("stage-bar", className)} {...rest}>
      <div className="stage-bar-start">{left}</div>
      {(!isEmpty(right) || !isEmpty(hint)) && (
        <div className="stage-bar-end" title={hintText}>
          {!isEmpty(hint) && <span className="stage-bar-hint">{hint}</span>}
          {right}
        </div>
      )}
    </div>
  );
}

/** div.stage — variant "plain" (Standard), "paper" (Scope) oder "3d"; reicht alle Attribute und ref durch. */
export const Stage = forwardRef(function Stage({ variant = "plain", className, children, ...rest }, ref) {
  return (
    <div ref={ref} className={cx("stage", `stage-${variant}`, className)} data-stage={variant} {...rest}>
      {children}
    </div>
  );
});

/**
 * dl.panel-facts.key-facts: items = [{ label, value, copy, title, key }] — copy ist der zu kopierende
 * Text (true = der Wert selbst), title steht am Wert. Einträge ohne Wert entfallen; children folgen.
 */
export function Facts({ items = [], children, className, ...rest }) {
  const shown = items.filter((it) => it && !isEmpty(it.value));
  const extra = React.Children.toArray(children).filter(Boolean);
  if (shown.length === 0 && extra.length === 0) return null;
  return (
    <dl className={cx("panel-facts", "key-facts", className)} {...rest}>
      {shown.map((it, i) => {
        const copyText = it.copy === true ? String(it.value) : it.copy;
        return (
          <div className="fact" key={it.key ?? (typeof it.label === "string" ? it.label : i)}>
            <dt>{it.label}</dt>
            <dd title={it.title}>
              <span className="fact-value">{it.value}</span>
              {!isEmpty(copyText) && <CopyButton text={String(copyText)} size="xs" label={it.copyLabel} quiet />}
            </dd>
          </div>
        );
      })}
      {extra}
    </dl>
  );
}

/** button.chip — die einzige Pille: Punkt in `color` (--group-color), Text, Zahl; `pressed` → aria-pressed. */
export const Chip = forwardRef(function Chip({ pressed, color, count, className, style, children, type = "button", ...rest }, ref) {
  return (
    <button ref={ref} type={type} className={cx("chip", className)}
      aria-pressed={pressed === undefined ? undefined : Boolean(pressed)}
      style={color ? { "--group-color": color, ...style } : style} {...rest}>
      <span className="chip-dot group-dot" aria-hidden="true" />
      {children}
      {count != null && <span className="chip-count group-count">{count}</span>}
    </button>
  );
});

/** button.btn — variant "quiet" (Standard) oder "primary"; `icon` = Name aus dem Symbolsatz oder ein Knoten. */
export const Button = forwardRef(function Button({ variant = "quiet", icon, className, children, type = "button", ...rest }, ref) {
  const iconNode = typeof icon === "string" ? <Icon name={icon} /> : icon;
  const iconOnly = !isEmpty(iconNode) && React.Children.count(children) === 0;
  return (
    <button ref={ref} type={type} className={cx("btn", `btn-${variant}`, iconOnly && "is-icon", className)} {...rest}>
      {iconNode}
      {children}
    </button>
  );
});

/** p.hint — höchstens zwei Zeilen; tone "warn" mit Punkt in --danger. Ohne Inhalt nichts. */
export function Hint({ tone = "quiet", className, children, ...rest }) {
  if (React.Children.toArray(children).length === 0) return null;
  return (
    <p className={cx("hint", tone === "warn" && "hint-warn", className)} {...rest}>
      {tone === "warn" && <span className="hint-dot" aria-hidden="true" />}
      {children}
    </p>
  );
}

/** div.panel-state in Bühnenhöhe — kind "loading" (Spinner, role=status), "empty" oder "error". */
export function PanelState({ kind = "loading", title, message, className, children, ...rest }) {
  return (
    <div className={cx("panel-state", className)} data-state={kind} role={kind === "loading" ? "status" : undefined}
      aria-busy={kind === "loading" ? true : undefined} {...rest}>
      {kind === "loading" && <span className="seg-spinner" aria-hidden="true" />}
      {!isEmpty(title) && <p className="panel-state-title">{title}</p>}
      {!isEmpty(message) && <p className="panel-state-message">{message}</p>}
      {children}
    </div>
  );
}

// --- Fuß -----------------------------------------------------------------------------------------

/** Gemeinsamer Ordner der Dateien (Elternverzeichnis), für „Copy folder“. */
export function commonFolder(paths) {
  const dirs = paths.map((p) => p.replace(/[\\/][^\\/]*$/, ""));
  if (dirs.length === 0) return "";
  let common = dirs[0];
  for (const d of dirs.slice(1)) {
    while (common && d !== common && !d.startsWith(`${common}/`) && !d.startsWith(`${common}\\`)) {
      common = common.replace(/[\\/][^\\/]*$/, "");
    }
  }
  return common;
}

// Kopieren wie CopyButton (Zwischenablage, Rückfall über ein Textfeld); Erfolg nur, wenn bestätigt.
function copyText(text) {
  const fallback = () => {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try {
      ok = document.execCommand("copy") !== false;
    } catch {
      ok = false;
    }
    document.body.removeChild(ta);
    return ok;
  };
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text).then(() => true, fallback);
  return Promise.resolve(fallback());
}

function CopyFolderButton({ folder }) {
  const [copied, setCopied] = useState(false);
  const timer = useRef(null);
  useEffect(() => () => clearTimeout(timer.current), []);
  const onClick = () => copyText(folder).then((ok) => {
    if (!ok) return;
    setCopied(true);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setCopied(false), 1500);
  });
  return (
    <Button className={cx("panel-foot-folder", copied && "is-copied")} icon={copied ? "check" : "copy"}
      aria-label="Copy folder" title={folder} onClick={onClick}>
      Copy folder
    </Button>
  );
}

/**
 * footer.panel-foot.panel-footer: links der Files-Schalter (Name „Files, N“, aria-expanded/-controls),
 * rechts die Aktionen (children: Export PNG, Add to Anki) unter FooterStatus — ihre Rückmeldung
 * („Saved: …“, role=status) ersetzt für die Flash-Dauer den Schalter. Die Liste steht immer im DOM
 * (zugeklappt mit hidden), damit .panel-footer-path samt title für test:host erreichbar bleibt.
 * Escape in der Liste schließt sie und setzt den Fokus zurück auf den Schalter.
 * hideFiles (Study): kein Schalter und kein Pfad im DOM — nichts darf den Namen verraten.
 * files = [{ label, path }] (fileEntries aus PanelFooter); folder überschreibt den Ordner für „Copy folder“.
 */
export function PanelFoot({ files = [], folder, hideFiles = false, className, children, ...rest }) {
  const [status, setStatus] = useState(null);
  const [open, setOpen] = useState(false);
  const listId = useId();
  const toggleRef = useRef(null);
  const rows = hideFiles ? [] : files.filter((f) => f && f.path);
  const actions = React.Children.toArray(children).filter(Boolean);
  if (rows.length === 0 && actions.length === 0) return null;
  const dir = folder ?? commonFolder(rows.map((f) => f.path));

  const onKeyDown = (e) => {
    if (e.key !== "Escape" || !open) return;
    e.preventDefault();
    e.stopPropagation();
    setOpen(false);
    toggleRef.current?.focus();
  };

  return (
    <footer className={cx("panel-foot", "panel-footer", className)} data-testid="panel-footer" onKeyDown={onKeyDown} {...rest}>
      <div className="panel-foot-files">
        {status ? (
          <span className={`export-feedback${status.kind === "error" ? " is-error" : ""}`} role="status">{status.text}</span>
        ) : rows.length > 0 && (
          <button ref={toggleRef} type="button" className="panel-foot-toggle" aria-expanded={open} aria-controls={listId}
            aria-label={`Files, ${rows.length}`} onClick={() => setOpen((o) => !o)}>
            Files <span className="panel-foot-count">{rows.length}</span>
            <Icon name="chevron-down" />
          </button>
        )}
      </div>
      {actions.length > 0 && (
        <FooterStatus.Provider value={setStatus}>
          <div className="panel-foot-actions panel-footer-actions">{actions}</div>
        </FooterStatus.Provider>
      )}
      {rows.length > 0 && (
        <div id={listId} className="panel-foot-list" hidden={!open}>
          {rows.map((f) => (
            <div className="panel-footer-file" key={`${f.label}:${f.path}`}>
              <span className="panel-footer-label">{f.label}</span>
              <span className="panel-footer-path" title={f.path}><span dir="ltr">{displayPath(f.path)}</span></span>
              <CopyButton text={f.path} size="xs" label="Copy path" quiet />
            </div>
          ))}
          {dir && <CopyFolderButton folder={dir} />}
        </div>
      )}
    </footer>
  );
}
