"""scripts/release_check.py — der Vorab-Job in publish.yml, der einen Release rot macht.

Im Gate nicht prüfbar, weil es dort keinen Tag gibt: passt der Tag zur Version,
ist der CHANGELOG-Abschnitt der Version datiert und gefüllt, und ist
[Unreleased] beim Release leer (sonst fehlen die Änderungen in den Release-Notes).
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("release_check", ROOT / "scripts" / "release_check.py")
release_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(release_check)

GUT = """# Changelog

## [Unreleased]

## [1.2.0] — 2026-11-06

### Added

- Something new.

## [1.1.0] — 2026-10-01

- Older.
"""


def test_sauberer_release_hat_keine_befunde():
    assert release_check.befunde("1.2.0", GUT, tag="v1.2.0") == []


def test_tag_muss_zur_version_passen():
    assert any("Tag" in b for b in release_check.befunde("1.2.0", GUT, tag="v1.2.1"))


def test_ohne_tag_wird_der_tag_nicht_geprueft():
    assert release_check.befunde("1.2.0", GUT, tag=None) == []


def test_abschnitt_der_version_fehlt():
    assert any("1.3.0" in b for b in release_check.befunde("1.3.0", GUT, tag="v1.3.0"))


def test_abschnitt_ohne_datum():
    text = GUT.replace("## [1.2.0] — 2026-11-06", "## [1.2.0]")
    assert any("Datum" in b for b in release_check.befunde("1.2.0", text, tag="v1.2.0"))


def test_leerer_abschnitt():
    text = GUT.replace("### Added\n\n- Something new.\n", "")
    assert any("leer" in b for b in release_check.befunde("1.2.0", text, tag="v1.2.0"))


def test_unreleased_mit_eintraegen_ist_rot():
    text = GUT.replace("## [Unreleased]\n", "## [Unreleased]\n\n- Forgotten change.\n")
    assert any("Unreleased" in b for b in release_check.befunde("1.2.0", text, tag="v1.2.0"))


def test_publish_workflow_haengt_am_vorab_job():
    """Ohne needs: check liefe der Upload auch bei roter Prüfung."""
    wf = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    check = wf[wf.index("\n  check:") : wf.index("\n  build:")]
    assert "scripts/release_check.py" in check
    for test in ("tests/test_readme.py", "tests/test_docs_consistency.py", "tests/test_release_versions.py"):
        assert test in check, test
    build = wf[wf.index("\n  build:") : wf.index("\n  publish:")]
    assert "needs: check" in build


def test_release_checkliste_steht_im_release_ablauf():
    """Das nicht mechanisch Prüfbare: Doku-Sichtung gegen den Diff seit dem letzten Tag."""
    ablauf = (ROOT / "docs" / "registry-publish.md").read_text(encoding="utf-8")
    teil = ablauf[ablauf.index("## Release-Reihenfolge im Ganzen") :]
    assert "git diff" in teil and "docs/tools.md" in teil and "README.md" in teil
    assert "release_check.py" in teil
