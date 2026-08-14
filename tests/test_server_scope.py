"""Vertragstests für generate_scope_table (Substrate-Scope-Figur).

Wie generate_tlc: PNG+SVG sind Default und werden als Dateien geschrieben,
CDXML gibt es nicht (eine Figur ist keine Struktur). Zusätzlich gilt hier die
Batch-Regel aus batch_generate: ein Eintrag, der sich nicht auflösen lässt,
kippt nicht die ganze Figur — er wird gemeldet, der Rest wird gezeichnet.
"""

import io
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image
from rdkit import Chem
from rdkit.Chem import AllChem

from chemdraw_tool.image_export import PNG_MAGIC
from chemdraw_tool.payloads import ReactionSpec, ScopeEntry, ScopePayload
from chemdraw_tool.server import generate_scope_table

ENTRIES = [
    {"structure": "c1ccc(-c2ccccc2)cc1", "label": "2a", "yield_text": "92"},
    {"structure": "COc1ccc(-c2ccccc2)cc1", "label": "2b", "yield_text": "88%"},
    {
        "structure": "O=C(O)c1ccc(-c2ccccc2)cc1",
        "label": "2c",
        "yield_text": "64",
        "notes": "ee 94%",
    },
]


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr("chemdraw_tool.server.SCOPE_DIR", tmp_path / "scope")
    yield tmp_path


def _mol(smiles: str) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    return mol


def _resolver(*failing: str):
    """resolve()-Ersatz ohne Netz: SMILES werden geparst, Namen in `failing`
    scheitern wie ein nicht auffindbarer Stoff."""

    def fake(text: str):
        if text in failing:
            raise ValueError(f"Could not resolve '{text}'")
        mol = Chem.MolFromSmiles(text)
        if mol is None:
            raise ValueError(f"Could not resolve '{text}'")
        return Chem.MolToSmiles(mol), mol

    return fake


def test_default_writes_png_and_svg(tmp_path):
    with patch("chemdraw_tool.server.resolve", side_effect=_resolver()):
        payload = generate_scope_table(ENTRIES, title="Suzuki scope")
    assert isinstance(payload, ScopePayload)
    assert set(payload.files) == {"png", "svg"}
    png = Path(payload.files["png"])
    assert png.read_bytes()[: len(PNG_MAGIC)] == PNG_MAGIC
    assert "<svg" in Path(payload.files["svg"]).read_text()
    assert png.parent == tmp_path / "scope"


def test_payload_fields_for_the_panel():
    with patch("chemdraw_tool.server.resolve", side_effect=_resolver()):
        payload = generate_scope_table(ENTRIES, title="Suzuki scope")
    assert payload.type == "scope"
    assert payload.name == "Suzuki scope"
    assert payload.columns == 3
    assert [e.label for e in payload.entries] == ["2a", "2b", "2c"]
    # Ausbeuten kommen normalisiert zurück — im Panel steht dasselbe wie in
    # der Figur, egal ob das Modell "92" oder "92%" geliefert hat.
    assert [e.yield_text for e in payload.entries] == ["92%", "88%", "64%"]
    assert payload.entries[2].notes == "ee 94%"
    assert payload.failed == []
    assert "<svg" in payload.svg


def test_missing_labels_are_numbered_like_a_paper():
    entries = [{"structure": s} for s in ("CCO", "CCC", "CCN")]
    with patch("chemdraw_tool.server.resolve", side_effect=_resolver()):
        payload = generate_scope_table(entries)
    assert [e.label for e in payload.entries] == ["1a", "1b", "1c"]


def test_one_broken_entry_does_not_kill_the_figure():
    entries = [*ENTRIES, {"structure": "Unobtainium", "label": "2d", "yield_text": "0"}]
    with patch(
        "chemdraw_tool.server.resolve", side_effect=_resolver("Unobtainium")
    ):
        payload = generate_scope_table(entries, title="Suzuki scope")
    assert payload.failed == ["Unobtainium"]
    assert [e.label for e in payload.entries] == ["2a", "2b", "2c"]
    assert Path(payload.files["png"]).exists()


def test_all_entries_broken_raises():
    with patch("chemdraw_tool.server.resolve", side_effect=_resolver("Nope")):
        with pytest.raises(ValueError, match="[Ee]intrag"):
            generate_scope_table([{"structure": "Nope"}])


def test_header_reaction_is_drawn_above_the_grid():
    reaction = ReactionSpec(
        reactants=["Brc1ccccc1", "OB(O)c1ccccc1"],
        products=["c1ccc(-c2ccccc2)cc1"],
        conditions="Pd(PPh3)4 (2 mol%), K2CO3, 80 °C",
    )
    with patch("chemdraw_tool.server.resolve", side_effect=_resolver()):
        plain = generate_scope_table(ENTRIES, title="Ohne Kopf")
        with_header = generate_scope_table(
            ENTRIES, title="Mit Kopf", reaction=reaction
        )
    assert with_header.conditions == "Pd(PPh3)4 (2 mol%), K2CO3, 80 °C"
    tall = Image.open(io.BytesIO(Path(with_header.files["png"]).read_bytes())).size[1]
    flat = Image.open(io.BytesIO(Path(plain.files["png"]).read_bytes())).size[1]
    assert tall > flat


def test_broken_header_only_costs_the_header():
    """Auch der Kopf ist nur ein Bestandteil: scheitert er, entsteht die
    Figur trotzdem — mit Meldung statt Abbruch."""
    reaction = ReactionSpec(reactants=["Unobtainium"], products=["CCO"])
    with patch(
        "chemdraw_tool.server.resolve", side_effect=_resolver("Unobtainium")
    ):
        payload = generate_scope_table(ENTRIES, reaction=reaction)
    assert payload.failed == ["Unobtainium"]
    assert Path(payload.files["png"]).exists()


def test_columns_are_forwarded():
    with patch("chemdraw_tool.server.resolve", side_effect=_resolver()):
        payload = generate_scope_table(ENTRIES, columns=2)
    assert payload.columns == 2


def test_cdxml_is_rejected():
    with patch("chemdraw_tool.server.resolve", side_effect=_resolver()):
        with pytest.raises(ValueError, match="CDXML"):
            generate_scope_table(ENTRIES, formats=["cdxml"])


def test_unknown_style_fails_before_files_are_written(tmp_path):
    with patch("chemdraw_tool.server.resolve", side_effect=_resolver()):
        with pytest.raises(ValueError, match="render_style"):
            generate_scope_table(ENTRIES, render_style="neon")
    assert not (tmp_path / "scope").exists()


def test_entries_accept_the_pydantic_model_too():
    entries = [ScopeEntry(structure="CCO", label="3a", yield_text="55")]
    with patch("chemdraw_tool.server.resolve", side_effect=_resolver()):
        payload = generate_scope_table(entries)
    assert payload.entries[0].label == "3a"
