import subprocess
import time
from pathlib import Path

CHEMDRAW_APP_PATHS = [
    Path("/Applications/ChemDraw Professional.app"),
    Path("/Applications/ChemDraw.app"),
    Path("/Applications/ChemDraw Prime.app"),
]


def find_chemdraw() -> Path | None:
    for path in CHEMDRAW_APP_PATHS:
        if path.exists():
            return path
    return None


def _escape_applescript(s: str) -> str:
    """Escape backslashes and double-quotes for an AppleScript string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_open_script(app_name: str, filepath: str) -> str:
    app_name = _escape_applescript(app_name)
    filepath = _escape_applescript(filepath)
    return f'tell application "{app_name}" to open POSIX file "{filepath}"'


def build_cleanup_script(app_name: str) -> str:
    app_name = _escape_applescript(app_name)
    return (
        f'tell application "{app_name}"\n'
        f"  activate\n"
        f"end tell\n"
        f'tell application "System Events"\n'
        f'  tell process "{app_name}"\n'
        f"    delay 0.5\n"
        f'    keystroke "a" using command down\n'
        f"    delay 0.3\n"
        f'    keystroke "k" using {{shift down, control down, command down}}\n'
        f"  end tell\n"
        f"end tell"
    )


def build_export_svg_script(app_name: str, output_filepath: str) -> str:
    app_name = _escape_applescript(app_name)
    output_path = str(Path(output_filepath).resolve())
    if output_path.endswith(".svg"):
        output_path = output_path[:-4]

    return (
        f'tell application "{app_name}"\n'
        f"  activate\n"
        f"end tell\n"
        f'tell application "System Events"\n'
        f'  tell process "{app_name}"\n'
        f"    delay 0.5\n"
        f'    keystroke "s" using command down\n'
        f"    delay 1.0\n"
        f'    keystroke "{output_path}"\n'
        f"    delay 0.5\n"
        f"    keystroke tab\n"
        f"    delay 0.3\n"
        f'    keystroke "svg"\n'
        f"    delay 0.3\n"
        f"    keystroke return\n"
        f"    delay 1.0\n"
        f"  end tell\n"
        f"end tell"
    )


def open_in_chemdraw(filepath: str, cleanup: bool = False) -> bool:
    app = find_chemdraw()
    if app is None:
        raise FileNotFoundError("ChemDraw not found in /Applications/")
    app_name = app.stem
    script = build_open_script(app_name, filepath)
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return False

    if cleanup:
        time.sleep(0.5)
        cleanup_script = build_cleanup_script(app_name)
        result = subprocess.run(
            ["osascript", "-e", cleanup_script], capture_output=True, text=True
        )
        return result.returncode == 0

    return True


def export_to_svg(cdxml_filepath: str, svg_output_path: str) -> str:
    app = find_chemdraw()
    if app is None:
        raise FileNotFoundError("ChemDraw not found in /Applications/")

    app_name = app.stem
    cdxml_path = str(Path(cdxml_filepath).resolve())

    open_script = build_open_script(app_name, cdxml_path)
    result = subprocess.run(
        ["osascript", "-e", open_script], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to open CDXML: {result.stderr}")

    time.sleep(1.0)

    cleanup_script = build_cleanup_script(app_name)
    result = subprocess.run(
        ["osascript", "-e", cleanup_script], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to run Clean Up: {result.stderr}")

    time.sleep(1.0)

    export_script = build_export_svg_script(app_name, svg_output_path)
    result = subprocess.run(
        ["osascript", "-e", export_script], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to export SVG: {result.stderr}")

    time.sleep(1.0)

    svg_path = Path(svg_output_path)
    if not svg_path.suffix == ".svg":
        svg_path = svg_path.with_suffix(".svg")

    if not svg_path.exists():
        raise RuntimeError(f"SVG file not created at {svg_path}")

    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    return svg_content
