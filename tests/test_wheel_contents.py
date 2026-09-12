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
