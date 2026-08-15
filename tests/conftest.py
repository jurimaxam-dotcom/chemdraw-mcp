"""Wächter gegen den teuersten Testfehler dieses Projekts: falsch-grün.

Die Tool-Tests leiten ihre Ausgabepfade per `monkeypatch.setattr` auf ein
tmp_path um — 26-mal, verteilt über die Suite. Das funktioniert nur, solange
das Patch-Ziel und der Ort, an dem der Code die Konstante nachschlägt, dasselbe
Modul sind. Verschiebt ein Umbau die Konstanten in ein anderes Modul, zeigt
`setattr` ins Leere: Die Tests laufen weiter grün und schreiben dabei in das
echte `~/ChemDraw-Output` des Nutzers.

Genau das fängt dieser Wächter ab. Er ist bewusst kein Mock, sondern eine
Nachkontrolle am echten Ordner: Was am Ende der Suite dort neu liegt, hat kein
Test dorthin gelegt — er wollte in tmp_path schreiben.
"""

from pathlib import Path

import pytest

REAL_OUTPUT = Path.home() / "ChemDraw-Output"

# Der Server schreibt hier im Normalbetrieb hin; ein laufender Desktop-Server
# darf die Suite nicht rot machen. Log-Dateien sind kein Testergebnis.
IGNORED = {"server.log"}


def _snapshot() -> set[Path]:
    if not REAL_OUTPUT.exists():
        return set()
    return {
        p
        for p in REAL_OUTPUT.rglob("*")
        if p.is_file() and p.name not in IGNORED
    }


@pytest.fixture(scope="session", autouse=True)
def _no_writes_to_the_real_output_dir():
    """Kein Test darf im echten Ausgabeordner Spuren hinterlassen."""
    before = _snapshot()
    yield
    new = _snapshot() - before
    if new:
        listing = "\n".join(f"  - {p}" for p in sorted(new)[:10])
        pytest.fail(
            "Tests haben in den ECHTEN Ausgabeordner geschrieben — eine "
            "Umleitung per monkeypatch zeigt ins Leere:\n"
            f"{listing}\n"
            "Patch-Ziel und Fundort der Konstante müssen dasselbe Modul sein."
        )
