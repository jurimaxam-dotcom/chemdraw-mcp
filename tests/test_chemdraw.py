from pathlib import Path
from unittest.mock import Mock, patch

from chemdraw_tool.chemdraw import (
    build_cleanup_script,
    build_open_script,
    export_to_svg,
    find_chemdraw,
    open_in_chemdraw,
)


def test_build_open_script_contains_filepath():
    script = build_open_script("ChemDraw", "/tmp/test.cdxml")
    assert "/tmp/test.cdxml" in script


def test_build_open_script_contains_app_name():
    script = build_open_script("ChemDraw Professional", "/tmp/test.cdxml")
    assert "ChemDraw Professional" in script


def test_build_open_script_uses_posix_file():
    script = build_open_script("ChemDraw", "/tmp/test.cdxml")
    assert "POSIX file" in script


@patch("chemdraw_tool.chemdraw.CHEMDRAW_APP_PATHS", [Path("/tmp/nonexistent.app")])
def test_find_chemdraw_returns_none_when_missing():
    result = find_chemdraw()
    assert result is None


@patch("chemdraw_tool.chemdraw.subprocess.run")
@patch("chemdraw_tool.chemdraw.find_chemdraw")
def test_open_in_chemdraw_success(mock_find, mock_run):
    mock_find.return_value = Path("/Applications/ChemDraw Professional.app")
    mock_run.return_value = Mock(returncode=0)
    result = open_in_chemdraw("/tmp/test.cdxml")
    assert result is True
    mock_run.assert_called_once()


@patch("chemdraw_tool.chemdraw.find_chemdraw")
def test_open_in_chemdraw_raises_when_not_installed(mock_find):
    mock_find.return_value = None
    try:
        open_in_chemdraw("/tmp/test.cdxml")
        assert False, "Should have raised"
    except FileNotFoundError:
        pass


def test_build_cleanup_script_activates_app():
    script = build_cleanup_script("ChemDraw Professional")
    assert 'tell application "ChemDraw Professional"' in script
    assert "activate" in script


def test_build_cleanup_script_uses_system_events():
    script = build_cleanup_script("ChemDraw")
    assert 'tell application "System Events"' in script
    assert 'tell process "ChemDraw"' in script


def test_build_cleanup_script_sends_select_all_and_cleanup():
    script = build_cleanup_script("ChemDraw")
    assert 'keystroke "a" using command down' in script
    assert 'keystroke "k"' in script


@patch("chemdraw_tool.chemdraw.subprocess.run")
@patch("chemdraw_tool.chemdraw.find_chemdraw")
def test_open_with_cleanup_runs_both_scripts(mock_find, mock_run):
    mock_find.return_value = Path("/Applications/ChemDraw.app")
    mock_run.return_value = Mock(returncode=0)
    result = open_in_chemdraw("/tmp/test.cdxml", cleanup=True)
    assert result is True
    assert mock_run.call_count == 2


def test_build_export_svg_script_activates_app():
    from chemdraw_tool.chemdraw import build_export_svg_script

    script = build_export_svg_script("ChemDraw", "/tmp/test")
    assert 'tell application "ChemDraw"' in script
    assert "activate" in script


def test_build_export_svg_script_uses_cmd_s():
    from chemdraw_tool.chemdraw import build_export_svg_script

    script = build_export_svg_script("ChemDraw", "/tmp/test")
    assert 'keystroke "s" using command down' in script


def test_build_export_svg_script_selects_svg_format():
    from chemdraw_tool.chemdraw import build_export_svg_script

    script = build_export_svg_script("ChemDraw", "/tmp/test")
    assert 'keystroke "svg"' in script


def test_build_export_svg_script_removes_svg_extension():
    from chemdraw_tool.chemdraw import build_export_svg_script

    script = build_export_svg_script("ChemDraw", "/tmp/test.svg")
    assert "/tmp/test.svg" not in script
    assert "/tmp/test" in script


@patch("chemdraw_tool.chemdraw.subprocess.run")
@patch("chemdraw_tool.chemdraw.find_chemdraw")
def test_export_to_svg_runs_three_scripts(mock_find, mock_run):
    mock_find.return_value = Path("/Applications/ChemDraw.app")
    mock_run.return_value = Mock(returncode=0)
    # Create a temporary SVG file for the test
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
        f.write("<svg></svg>")
        temp_svg = f.name
    try:
        result = export_to_svg("/tmp/test.cdxml", temp_svg)
        # Should run 3 scripts: open, cleanup, export
        assert mock_run.call_count == 3
        assert result == "<svg></svg>"
    finally:
        Path(temp_svg).unlink()


@patch("chemdraw_tool.chemdraw.find_chemdraw")
def test_export_to_svg_raises_when_chemdraw_missing(mock_find):
    mock_find.return_value = None
    try:
        export_to_svg("/tmp/test.cdxml", "/tmp/output")
        assert False, "Should have raised"
    except FileNotFoundError:
        pass


def test_build_open_script_escapes_quotes_in_app_name():
    """A double-quote in the app name must be escaped so it can't break out
    of the AppleScript string literal (AppleScript injection)."""
    script = build_open_script('Evil" do shell script "x', "/tmp/a.cdxml")
    assert '"Evil" do shell script "x"' not in script
    assert '\\"' in script


def test_build_cleanup_script_escapes_quotes_in_app_name():
    script = build_cleanup_script('Evil" attack')
    assert '\\"' in script
    assert 'Evil" attack' not in script


def test_build_open_script_escapes_quotes_in_filepath():
    """A double-quote in the file path must be escaped so it can't break out
    of the AppleScript string literal (AppleScript injection via file_path)."""
    script = build_open_script("ChemDraw", '/tmp/evil".cdxml')
    assert '\\"' in script
    # the bare unescaped quote must not survive as a literal break
    assert 'file "/tmp/evil".cdxml"' not in script
