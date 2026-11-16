"""Jede Farbe, die RDKit ins Panel-SVG schreibt, braucht eine Dunkel-Umfärbung.

Befund 10.11.2026 (dunkles Schema): Abkürzungs-Labels („Boc“, „Ph“,
„CO2H“) standen fast schwarz auf dunklem Grund. RDKit zeichnet Dummy-Atome
(die Träger der Kürzel) in #191919 — die Umfärbung in styles.css kannte nur
#000000 und die Heteroatomfarben. Gemessen wird am echten Panel-SVG gegen die
echten Selektoren beider Dunkel-Blöcke (Media-Query und data-theme="dark").
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from rdkit import Chem

from chemdraw_tool.generator import generate_2d
from chemdraw_tool.render_style import condense_groups
from chemdraw_tool.svg_renderer import render_svg

CSS = (Path(__file__).parent.parent / "chemdraw_tool" / "ui" / "src" / "styles.css").read_text()

# Zwei Dunkel-Varianten: Systemschema (Media-Query) und Host-Schalter data-theme.
# Seit Etappe 1 (16.11.2026) ist nur noch Scope ausgenommen: der Strukturvergleich
# (.plot-svg) liegt im Dunkeln nicht mehr auf weißer Karte und wird mit umgefärbt.
_PREFIXES = {
    "media": ':root:not([data-theme="light"]) svg:not(.scope-svg svg)',
    "data-theme": ':root[data-theme="dark"] svg:not(.scope-svg svg)',
}

PROBES = {
    # Boc und Ph als Kürzel.
    "boc_ph": "O=C(c1ccccc1)CC1CCN(C(=O)OC(C)(C)C)CC1",
    # Aspirin: CO2H und OAc.
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
}


def _colours(svg: str) -> tuple[set[str], set[str]]:
    strokes = set(re.findall(r"stroke:(#[0-9A-Fa-f]{6})", svg))
    fills = set(re.findall(r"fill='(#[0-9A-Fa-f]{6})'", svg))
    return strokes, fills


def _has_rule(prefix: str, selector: str) -> bool:
    return f"{prefix} {selector}" in CSS


def test_prefixes_exist_at_all():
    # Gegenprobe: ohne die Präfixe prüfte der Test nichts.
    for prefix in _PREFIXES.values():
        assert _has_rule(prefix, 'path[style*="stroke:#000000"]'), prefix


@pytest.mark.parametrize("probe", sorted(PROBES))
@pytest.mark.parametrize("variant", sorted(_PREFIXES))
def test_every_panel_colour_is_recoloured_in_dark(probe, variant):
    mol = generate_2d(Chem.MolFromSmiles(PROBES[probe]))
    for drawn in (mol, condense_groups(mol)):
        svg = render_svg(drawn, fill_container=True)
        strokes, fills = _colours(svg)
        prefix = _PREFIXES[variant]
        missing = [f"stroke {c}" for c in sorted(strokes)
                   if not _has_rule(prefix, f'path[style*="stroke:{c}"]')]
        missing += [f"fill {c}" for c in sorted(fills)
                    if not _has_rule(prefix, f'path[fill="{c}"]')]
        assert not missing, f"{probe} ({variant}): keine Dunkel-Umfärbung für {missing}"


# Etappe 6 (16.11.2026, Handlauf in Desktop, dunkles Thema): im Mechanismus standen die
# Klammern des Übergangszustands schwarz auf dunklem Grund, „Br“ dunkelbraun. Ursache: das
# Mechanismus-SVG nutzt RDKits Standardpalette (Br #7F4C19, I #A01EEF statt #A52A2A/#A020F0
# aus svg_renderer) und schreibt die Klammern als stroke-Attribut statt als style — beides
# trafen die Dunkel-Regeln nicht. Geprüft wird jede Farbe der echten Schritt-SVGs gegen eine
# Regel beider Dunkel-Blöcke und deren Kontrast gegen den dunklen Grund.

MECHANISMS = {
    "sn2": ("sn2", ["C[C@@H](Br)CC", "[C-]#N"]),
    "sn1_cl": ("sn1", ["CC(C)(C)Cl", "O"]),
    "sn1_br": ("sn1", ["CC(C)(C)Br", "O"]),
    "sn1_i": ("sn1", ["CC(C)(C)I", "[OH-]"]),
    "fischer": ("fischer_ester", ["CC(=O)O", "CCO"]),
}
# Bewusst in beiden Schemata gleich: Elektronenpfeile (Rot) und gestrichelte Teilbindungen (Grau).
_SAME_IN_BOTH = {"#e74c3c", "#999"}
_DARK_BG = "#202724"  # --bg (dunkel, ohne Host-Variable)


def _mechanism_svgs(reaction_type: str, smiles: list[str]) -> list[str]:
    from chemdraw_tool import mechanism_coords
    from chemdraw_tool.mechanism_renderer import render_step_svg
    from chemdraw_tool.mechanism_substrate import build_steps

    steps = build_steps(reaction_type, smiles)
    return [render_step_svg(s, m) for s, m in zip(steps, mechanism_coords.layout_anchored(steps))]


def _drawn_colours(svg: str) -> set[tuple[str, str, str, str]]:
    """(Tag, Eigenschaft, Form, Farbe) für jede Farbe, die ein Element setzt."""
    found = set()
    for tag, attrs in re.findall(r"<(path|text|line|polygon)\b([^>]*)>", svg):
        style = re.search(r"style=['\"]([^'\"]*)", attrs)
        for prop, colour in re.findall(r"(stroke|fill):(#[0-9A-Fa-f]{3,6})", style.group(1) if style else ""):
            found.add((tag, prop, "style", colour))
        for prop, colour in re.findall(r"\s(stroke|fill)=['\"](#[0-9A-Fa-f]{3,6})['\"]", attrs):
            found.add((tag, prop, "attr", colour))
    return found


def _dark_value(prefix_root: str, prefix: str, selector: str) -> str | None:
    """Farbe, auf die die Dunkel-Regel umfärbt (Variable aufgelöst), oder None ohne Regel."""
    m = re.search(re.escape(f"{prefix} {selector}") + r"\s*\{\s*(?:stroke|fill):\s*var\((--[\w-]+)\)", CSS)
    if not m:
        return None
    var = m.group(1)
    if var == "--atom-c":
        return "#e2eae5"  # var(--fg), dunkel
    block = CSS[CSS.index(prefix_root):]
    v = re.search(re.escape(var) + r":\s*(#[0-9A-Fa-f]{6})", block)
    return v.group(1) if v else None


def _luminance(hex_colour: str) -> float:
    def ch(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _contrast(a: str, b: str) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


_ROOTS = {"media": ':root:not([data-theme="light"]) {', "data-theme": ':root[data-theme="dark"] {'}


@pytest.mark.parametrize("case", sorted(MECHANISMS))
@pytest.mark.parametrize("variant", sorted(_PREFIXES))
def test_mechanism_colours_are_readable_in_dark(case, variant):
    prefix = _PREFIXES[variant]
    colours = set()
    for svg in _mechanism_svgs(*MECHANISMS[case]):
        colours |= _drawn_colours(svg)
    assert colours, "keine Farben gefunden — der Test prüfte nichts"
    problems = []
    for tag, prop, form, colour in sorted(colours):
        if colour.lower() in _SAME_IN_BOTH:
            continue
        selector = f'{tag}[style*="{prop}:{colour}"]' if form == "style" else f'{tag}[{prop}="{colour}"]'
        dark = _dark_value(_ROOTS[variant], prefix, selector)
        if dark is None:
            problems.append(f"{selector}: keine Dunkel-Regel")
        elif _contrast(dark, _DARK_BG) < 4.5:
            problems.append(f"{selector} → {dark}: Kontrast {_contrast(dark, _DARK_BG):.1f} < 4,5")
    assert not problems, f"{case} ({variant}): {problems}"
