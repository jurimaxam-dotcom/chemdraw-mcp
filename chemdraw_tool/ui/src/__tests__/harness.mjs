// Minimaler Render-Helfer fuer die Panel-Tests. Kein Framework — React 18
// bringt `act` selbst mit, jsdom das DOM; mehr braucht es nicht.
//
// Keine `.test.mjs`-Endung: der Runner-Glob laesst diese Datei damit in Ruhe.
import { act } from "react";
import { createRoot } from "react-dom/client";

/** Rendert ein Element in einen frischen Container am document.body. */
export function render(element) {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => {
    root.render(element);
  });
  return {
    container,
    rerender(next) {
      act(() => {
        root.render(next);
      });
    },
    unmount() {
      act(() => {
        root.unmount();
      });
      container.remove();
    },
  };
}

/** Klick, dessen Folge-Renders vollstaendig abgearbeitet sind. */
export async function click(element) {
  await act(async () => {
    element.dispatchEvent(
      new window.MouseEvent("click", { bubbles: true, cancelable: true })
    );
  });
}

/** Alle Knoepfe eines Containers nach ihrem sichtbaren Text. */
export function buttonByText(container, text) {
  return [...container.querySelectorAll("button")].find(
    (b) => b.textContent.trim() === text
  );
}

/** Sichtbarer Text ohne Zeilenumbrueche/Mehrfach-Leerzeichen. */
export function textOf(node) {
  return (node?.textContent ?? "").replace(/\s+/g, " ").trim();
}
