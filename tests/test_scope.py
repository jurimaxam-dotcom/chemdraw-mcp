"""Tests für chemdraw_tool/scope.py — Substrate-Scope-Figuren (Raster).

Die häufigste Abbildung der Methodenliteratur: EINE Reaktion, viele
Substrate, das Ergebnis ist ein Raster aus Produktstrukturen mit
Bezeichner ("1a") und Ausbeute ("78%"), darüber die allgemeine Gleichung
mit den Bedingungen.

Kern ist das LAYOUT, nicht die Chemie. Festgenagelt wird deshalb vor allem
die pure Geometrie:

* Spaltenzahl: Default aus der Eintragszahl, nie mehr als 4 (breiter wird
  im Zweispaltensatz unleserlich) und nie mehr Spalten als Einträge.
* Zellen sind alle gleich groß; RDKit zeichnet mit EINER gemeinsamen Skala
  (drawMolsSameScale) — ein kleines Molekül wird also nicht auf Zellgröße
  aufgeblasen, wie es ein Raster aus Einzelbildern täte.
* Beschriftungen stehen auf einer gemeinsamen Grundlinie. RDKits eigene
  Legende kann das nicht: sie zentriert den Textblock in der Zelle und wirft
  Leerzeilen weg, eine einzeilige Beschriftung sitzt daneben also tiefer als
  die erste Zeile der zweizeiligen Nachbarzelle (gemessen 2026-08-15). Die
  Captions werden deshalb selbst gesetzt — RDKit reserviert nur den Platz.
* Eine unvollständige letzte Zeile wird so mittig gesetzt, wie es ganze
  Zellen erlauben (Platzhalter links und rechts).
"""

from xml.etree import ElementTree

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.scope import (
    MAX_CAPTION_LINES,
    MAX_COLUMNS,
    ReactionHeader,
    ScopeItem,
    auto_label,
    build_grid,
    caption_baselines,
    caption_lines,
    cell_box,
    default_columns,
    format_yield,
    header_aspect,
    plan_figure,
    render_scope_png,
    render_scope_svg,
    struct_aspect,
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


def _items(n: int) -> list[ScopeItem]:
    smis = ["CCO", "c1ccccc1C(=O)O", "CC(=O)Oc1ccccc1C(=O)O", "CCCCBr", "c1ccncc1"]
    return [
        ScopeItem(
            mol=_mol(smis[i % len(smis)]),
            label=auto_label(i),
            yield_text=f"{50 + i}%",
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Spaltenzahl
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "count,expected",
    [(1, 1), (2, 2), (3, 3), (4, 4), (5, 3), (6, 3), (7, 4), (8, 4), (9, 3), (12, 4)],
)
def test_default_columns_minimizes_empty_cells(count, expected):
    """3 oder 4 Spalten wie in der Fachliteratur — die Variante mit der
    volleren letzten Zeile gewinnt, bei Gleichstand die breitere."""
    assert default_columns(count) == expected


def test_default_columns_never_exceeds_max():
    assert all(default_columns(n) <= MAX_COLUMNS for n in range(1, 40))


def test_more_columns_than_entries_is_capped():
    """4 Spalten für 2 Einträge hieße: halbe Figur leer."""
    assert build_grid(2, columns=4).columns == 2


def test_absurd_column_count_raises():
    with pytest.raises(ValueError, match="[Ss]palten"):
        build_grid(12, columns=9)


def test_zero_columns_means_default():
    assert build_grid(6, columns=0).columns == default_columns(6)


def test_no_entries_raises():
    with pytest.raises(ValueError, match="[Ee]intrag"):
        build_grid(0)


# ---------------------------------------------------------------------------
# Rasterbelegung
# ---------------------------------------------------------------------------


def test_grid_fills_row_wise():
    grid = build_grid(6, columns=3)
    assert grid.rows == 2
    assert grid.slots == [0, 1, 2, 3, 4, 5]


def test_incomplete_last_row_is_centred_when_it_can_be():
    """6 Einträge in 4 Spalten: die letzten 2 bekommen links UND rechts eine
    leere Zelle — sonst klebt die Restzeile am linken Rand."""
    grid = build_grid(6, columns=4)
    assert grid.rows == 2
    assert grid.slots == [0, 1, 2, 3, None, 4, 5, None]


def test_odd_deficit_puts_the_extra_cell_on_the_right():
    """Bei ungerader Lücke geht mittig nicht auf — dann bleibt die Restzeile
    linksbündig statt um eine halbe Zelle zu wackeln."""
    grid = build_grid(5, columns=3)
    assert grid.slots == [0, 1, 2, 3, 4, None]


# ---------------------------------------------------------------------------
# Beschriftung
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [("78", "78%"), ("78%", "78%"), ("78.5", "78.5%"), ("quant.", "quant."), ("", "")],
)
def test_format_yield(raw, expected):
    """Bloße Zahl bekommt ihr Prozentzeichen, Freitext bleibt Freitext."""
    assert format_yield(raw) == expected


def test_caption_joins_label_and_yield_on_one_line():
    assert caption_lines("1a", "78", "") == ["1a, 78%"]


def test_caption_without_yield_is_just_the_label():
    assert caption_lines("1a", "", "") == ["1a"]


def test_caption_of_an_empty_entry_is_empty():
    assert caption_lines("", "", "") == []


def test_notes_go_below_and_wrap():
    lines = caption_lines("1a", "78%", "ee 94%, dr 10:1, 12 h bei 60 °C")
    assert lines[0] == "1a, 78%"
    assert len(lines) > 1
    assert all(len(line) <= 30 for line in lines)
    assert "ee 94%" in " ".join(lines[1:])


def test_caption_is_capped_and_ellipsized():
    """Umbrechen statt kürzen — aber gedeckelt: jede zusätzliche Zeile
    stiehlt ALLEN Zellen Höhe, weil die Legendenzone global gilt."""
    lines = caption_lines("1a", "78%", "x" * 20 + " " + "y" * 20 + " " + "z" * 40)
    assert len(lines) == MAX_CAPTION_LINES
    assert lines[-1].endswith("…")


def test_caption_baselines_are_identical_across_a_row():
    """Gemeinsame Grundlinie — unabhängig davon, wie viele Zeilen eine
    Nachbarzelle hat. Genau das kann RDKits eigene Legende nicht."""
    layout = plan_figure(6, columns=3, caption_lines_count=2)
    one_line = caption_baselines(layout, 0, 1)
    two_lines = caption_baselines(layout, 1, 2)
    assert one_line[0][1] == two_lines[0][1]
    # zweite Zeile darunter, nicht darüber
    assert two_lines[1][1] > two_lines[0][1]
    # zentriert in der jeweiligen Zelle
    assert one_line[0][0] == cell_box(layout, 0)[0] + layout.cell[0] / 2


def test_caption_band_sits_below_the_structure_and_holds_every_line():
    """Die Beschriftungszone ist der von RDKit freigehaltene Streifen — alle
    erlaubten Zeilen müssen hineinpassen, sonst schreibt Text aus der Zelle."""
    layout = plan_figure(4, caption_lines_count=MAX_CAPTION_LINES)
    x, y, w, h = cell_box(layout, 0)
    band_top = y + h - layout.legend_fraction * h
    baselines = caption_baselines(layout, 0, MAX_CAPTION_LINES)
    assert baselines[0][1] > band_top
    assert baselines[-1][1] <= y + h


def test_auto_label_counts_like_a_paper():
    assert [auto_label(i) for i in range(3)] == ["1a", "1b", "1c"]
    # Jenseits von z wie Tabellenspalten weiterzählen (1aa) — Serien mit über
    # 26 Einträgen kommen in Papern praktisch nicht vor, brauchen aber einen
    # eindeutigen Bezeichner statt einer Wiederholung von "1a".
    assert auto_label(26) == "1aa"


# ---------------------------------------------------------------------------
# Figurgeometrie
# ---------------------------------------------------------------------------


def test_figure_is_as_wide_as_the_grid():
    layout = plan_figure(6, columns=3)
    assert layout.width == 3 * layout.cell[0]
    assert layout.height == layout.grid_y + 2 * layout.cell[1]


def test_header_and_title_add_height_on_top():
    plain = plan_figure(4)
    with_header = plan_figure(4, title="Substrate scope", has_header=True)
    assert with_header.width == plain.width
    assert with_header.height > plain.height
    assert with_header.header_box is not None
    x, y, w, h = with_header.header_box
    # Kopfreaktion sitzt über dem Raster, seitlich eingerückt: über die volle
    # Breite gezeichnet geriete sie deutlich größer als die Rasterstrukturen.
    assert x > 0 and x + w == with_header.width - x
    assert y + h <= with_header.grid_y
    assert plain.header_box is None


def test_header_height_follows_the_shape_of_the_reaction():
    """Die Kopfzeile bekommt so viel Höhe, wie die Gleichung breit ist —
    sonst steht zwischen Gleichung und Bedingungen ein Loch (RDKit zentriert
    die Zeichnung in der Box, die überschüssige Höhe bleibt leer)."""
    wide = ReactionHeader(
        reactants=[_mol("Brc1ccccc1"), _mol("OB(O)c1ccccc1")],
        products=[_mol("c1ccc(-c2ccccc2)cc1")],
    )
    narrow = ReactionHeader(reactants=[_mol("CCO")], products=[_mol("CC=O")])
    assert header_aspect(wide) > header_aspect(narrow)

    flat = plan_figure(4, has_header=True, header_aspect=header_aspect(wide))
    tall = plan_figure(4, has_header=True, header_aspect=header_aspect(narrow))
    assert flat.header_box[3] < tall.header_box[3]


def test_header_aspect_accounts_for_arrow_and_plus():
    """Auch die kleinste Gleichung ist breiter als hoch: Pfeil und '+'
    stehen zwischen den Strukturen."""
    assert header_aspect(ReactionHeader([_mol("C")], [_mol("CO")])) > 2


def test_conditions_get_their_own_line_under_the_equation():
    """Über dem Pfeil kollidiert der Bedingungstext mit den Strukturen, sobald
    er realistisch lang wird (Katalysator, Base, Solvens, Temperatur) — er
    bekommt deshalb eine eigene Zeile unter der Gleichung."""
    without = plan_figure(4, has_header=True)
    with_conditions = plan_figure(4, has_header=True, conditions_lines=1)
    assert with_conditions.height > without.height
    assert without.conditions_y == 0
    x, y, w, h = with_conditions.header_box
    assert with_conditions.conditions_y > y + h
    assert with_conditions.conditions_y < with_conditions.grid_y


def test_svg_scale_halves_every_length():
    """Wie MOL_PNG_SIZE/MOL_SVG_SIZE im Projekt: das SVG ist die halb so
    große, sonst identische Figur — gleiche Proportionen, gleiche Optik."""
    png = plan_figure(6, columns=3, title="T", has_header=True, conditions_lines=1)
    svg = plan_figure(
        6, columns=3, title="T", has_header=True, conditions_lines=1, scale=0.5
    )
    assert svg.width == png.width // 2
    # Geprüft wird das Verhältnis, nicht die absolute Höhe: jede Länge wird
    # einzeln gerundet, ein halbes Pixel je Block summiert sich — die
    # Proportionen bleiben davon unberührt, und genau die sind die Zusage.
    assert abs(svg.height / svg.width - png.height / png.width) < 0.02


def test_cells_follow_the_shape_of_the_structures():
    """Flache Strukturen (Biphenyle) bekommen flache Zellen. Mit fester
    Zellhöhe zentriert RDKit die Zeichnung und zwischen Struktur und
    Beschriftung steht ein leeres Band — die Figur wirkt zerrissen."""
    flat = [ScopeItem(_mol("c1ccc(-c2ccccc2)cc1"))]
    tall = [ScopeItem(_mol("CN1C=NC2=C1C(=O)N(C)C(=O)N2C"))]
    assert struct_aspect(flat) < struct_aspect(tall)

    flat_cell = plan_figure(4, struct_aspect=struct_aspect(flat)).cell
    tall_cell = plan_figure(4, struct_aspect=struct_aspect(tall)).cell
    assert flat_cell[0] == tall_cell[0]  # Breite bleibt die Rasterbreite
    assert flat_cell[1] < tall_cell[1]


def test_caption_never_takes_more_room_than_the_structure():
    """Auch bei flacher Struktur und dreizeiliger Beschriftung bleibt die
    Struktur die Hauptsache."""
    layout = plan_figure(
        4, struct_aspect=0.2, caption_lines_count=MAX_CAPTION_LINES
    )
    assert layout.legend_fraction < 0.4


def test_more_caption_lines_reserve_more_legend_space():
    """Drei Zeilen Beschriftung brauchen mehr Legendenzone als eine — sonst
    schreibt der Text in die Struktur."""
    assert plan_figure(4, caption_lines_count=3).legend_fraction > plan_figure(
        4, caption_lines_count=1
    ).legend_fraction


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def test_render_png_is_a_png_of_the_planned_size():
    import io

    from PIL import Image

    items = _items(5)
    png = render_scope_png(items)
    assert png[: len(PNG_MAGIC)] == PNG_MAGIC
    layout = plan_figure(5, struct_aspect=struct_aspect(items))
    assert Image.open(io.BytesIO(png)).size == (layout.width, layout.height)


def test_render_svg_is_wellformed_and_carries_the_grid():
    items = _items(5)
    svg = render_scope_svg(items)
    root = ElementTree.fromstring(svg)
    assert root.tag.endswith("svg")
    layout = plan_figure(5, scale=0.5, struct_aspect=struct_aspect(items))
    assert root.get("viewBox") == f"0 0 {layout.width} {layout.height}"


def test_header_reaction_is_composed_above_the_grid():
    header = ReactionHeader(
        reactants=[_mol("CCBr"), _mol("[OH-]")],
        products=[_mol("CCO")],
        conditions="NaOH, H2O, 60 °C",
    )
    plain = render_scope_png(_items(4))
    with_header = render_scope_png(_items(4), header=header, title="Substrate scope")
    assert len(with_header) > 0
    import io

    from PIL import Image

    assert Image.open(io.BytesIO(with_header)).size[1] > Image.open(
        io.BytesIO(plain)
    ).size[1]

    svg = render_scope_svg(_items(4), header=header, title="Substrate scope")
    root = ElementTree.fromstring(svg)
    # Kopfreaktion und Raster sind je ein verschachteltes <svg> im Rahmen
    nested = root.findall("{http://www.w3.org/2000/svg}svg")
    assert len(nested) == 2
    assert "Substrate scope" in svg


def test_render_without_items_raises():
    with pytest.raises(ValueError, match="[Ee]intrag"):
        render_scope_png([])


def test_unknown_style_raises_before_rendering():
    with pytest.raises(ValueError, match="render_style"):
        render_scope_png(_items(3), style="neon")


def test_style_is_applied_to_the_grid():
    """compact zeichnet dünner — die Datei muss sich messbar unterscheiden."""
    items = _items(3)
    assert render_scope_svg(items, style="compact") != render_scope_svg(items)
