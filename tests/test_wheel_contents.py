"""Das Wheel muss das gebaute Panel enthalten — sonst zeichnet der Server, aber
das Panel meldet „kann nicht erreicht werden".

0.4.0 shippte ohne chemdraw_tool/ui/dist/index.html: ein `dist/` in .gitignore
(gemeint war das Release-dist/ im Repo-Root) traf auch ui/dist, und hatchling
haelt sich an .gitignore. Der Test baut das Wheel wirklich, statt Muster zu raten.
"""

import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_wheel_ships_the_ui_bundle(tmp_path):
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1, wheels
    names = zipfile.ZipFile(wheels[0]).namelist()
    assert "chemdraw_tool/ui/dist/index.html" in names, (
        "UI-Bundle fehlt im Wheel — .gitignore-Muster pruefen (hatchling filtert danach)"
    )
    assert not any(n.startswith("chemdraw_tool/ui/src/") for n in names)
    assert not any("node_modules" in n for n in names)


def test_sdist_ships_only_the_allowlist(tmp_path):
    """Das sdist geht öffentlich auf PyPI. hatchling packt sonst alles ein, was nicht
    gitignored ist — auch ungetrackte interne Dateien (.radar-inbox, .claude/, plans/;
    Codex-Audit 20.10.2026). Deshalb Erlaubnisliste statt Sperrliste."""
    import tarfile

    subprocess.run(
        ["uv", "build", "--sdist", "--out-dir", str(tmp_path)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    sdists = list(tmp_path.glob("*.tar.gz"))
    assert len(sdists) == 1, sdists
    with tarfile.open(sdists[0]) as tar:
        # erster Pfadteil ist chemdraw_mcp-<version>/
        tops = {n.split("/", 2)[1] for n in tar.getnames() if n.count("/") >= 1}
    erlaubt = {"chemdraw_tool", "README.md", "LICENSE", "CHANGELOG.md", "pyproject.toml", "PKG-INFO", ".gitignore"}
    assert tops <= erlaubt, f"unerwartet im sdist: {sorted(tops - erlaubt)}"
    assert "chemdraw_tool" in tops
