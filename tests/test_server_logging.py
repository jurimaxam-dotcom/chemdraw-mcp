"""server.log: begrenzt und ohne DEBUG-Rauschen.

Befund 09.11.2026: der Server schrieb auf DEBUG in eine nie rotierte Datei —
8 MB nach wenigen Wochen, drei Viertel davon matplotlibs Font-Suche, dazu jede
PubChem-URL (also jeder eingegebene Stoffname) aus urllib3.
"""

import logging
from logging.handlers import RotatingFileHandler

import pytest

from chemdraw_tool import server


@pytest.fixture
def root_logger():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield root
    for h in root.handlers[:]:
        if h not in handlers:
            root.removeHandler(h)
            h.close()
    root.setLevel(level)


def _flush(handler):
    handler.flush()
    return open(handler.baseFilename, encoding="utf-8").read()


def test_log_rotates_instead_of_growing_forever(tmp_path, root_logger, monkeypatch):
    monkeypatch.delenv("CHEMDRAW_LOG_LEVEL", raising=False)
    handler = server._configure_logging(tmp_path)
    assert isinstance(handler, RotatingFileHandler)
    assert 0 < handler.maxBytes <= 2_000_000
    assert handler.backupCount >= 1
    assert handler.baseFilename == str(tmp_path / "server.log")


def test_default_level_keeps_debug_noise_out(tmp_path, root_logger, monkeypatch):
    monkeypatch.delenv("CHEMDRAW_LOG_LEVEL", raising=False)
    handler = server._configure_logging(tmp_path)
    logging.getLogger("matplotlib.font_manager").debug("findfont: score(...)")
    logging.getLogger("urllib3.connectionpool").debug("GET /rest/pug/compound/name/geheim")
    logging.getLogger("chemdraw_tool.server").info("MCP server starting")
    text = _flush(handler)
    assert "findfont" not in text
    assert "geheim" not in text
    assert "MCP server starting" in text


def test_debug_is_opt_in_via_environment(tmp_path, root_logger, monkeypatch):
    monkeypatch.setenv("CHEMDRAW_LOG_LEVEL", "debug")
    handler = server._configure_logging(tmp_path)
    logging.getLogger("chemdraw_tool.resolver").debug("cascade step 2")
    assert "cascade step 2" in _flush(handler)


def test_unknown_level_falls_back_to_info(tmp_path, root_logger, monkeypatch):
    monkeypatch.setenv("CHEMDRAW_LOG_LEVEL", "laut")
    handler = server._configure_logging(tmp_path)
    assert handler.level == logging.INFO
