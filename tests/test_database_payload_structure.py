"""Das Datenblatt-Panel traegt ab jetzt dieselben Strukturdaten wie das Molekuel.

Anlass (15.08.2026): Der Atom-Hover haengt an genau einem Panel. Faellt eine
Anfrage bei `lookup_molecule_data` statt bei `generate_molecule` heraus — was
bei einem knappen Prompt passiert — verliert der Nutzer den Hover, obwohl die
Struktur direkt vor ihm steht.

Statt das Routing dafuer perfekt machen zu wollen, entwertet der Umschalter im
Panel die Frage: beide Ansichten koennen beides zeigen. Dafuer braucht das
Datenblatt die Atomliste — sie kommt aus RDKit, kostet kein Netz und ist in
Millisekunden gerechnet.
"""

import pytest

from chemdraw_tool.payloads import DatabasePayload


def test_database_payload_carries_atoms():
    """Ohne Atomliste kann das Datenblatt-Panel keinen Tooltip zeigen."""
    payload = DatabasePayload()
    assert hasattr(payload, "atoms"), "DatabasePayload hat kein Feld `atoms`"
    assert payload.atoms == []


def test_database_payload_carries_functional_groups():
    """Die Gruppen-Highlights haengen an derselben Liste wie im Molekuel-Panel."""
    payload = DatabasePayload()
    assert hasattr(payload, "functionalGroups")
    assert payload.functionalGroups == []


def test_database_payload_knows_its_compound():
    """Der Umschalter zurueck zur Struktur braucht den Stoff, den er meint."""
    payload = DatabasePayload()
    assert hasattr(payload, "name")
    assert hasattr(payload, "smiles")


@pytest.mark.parametrize("field", ["atoms", "functionalGroups"])
def test_new_fields_are_typed_like_the_molecule_payload(field):
    """Gleiche Typen, damit UI-Komponenten fuer beide Panels dieselben sind."""
    from chemdraw_tool.payloads import MoleculePayload

    db_type = DatabasePayload.model_fields[field].annotation
    mol_type = MoleculePayload.model_fields[field].annotation
    assert db_type == mol_type, (
        f"{field}: DatabasePayload {db_type} != MoleculePayload {mol_type} — "
        "die geteilte Struktur-Komponente braucht identische Typen."
    )
