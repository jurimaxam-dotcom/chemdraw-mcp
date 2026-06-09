import base64

import pytest

from chemdraw_tool.png_writer import (
    PNG_MAGIC,
    decode_png,
    save_png_bytes,
)


def _png_b64(extra: bytes = b"payload") -> str:
    """A minimal valid-looking PNG: magic bytes + arbitrary tail."""
    return base64.b64encode(PNG_MAGIC + extra).decode()


def test_decode_plain_base64():
    raw = decode_png(_png_b64())
    assert raw.startswith(PNG_MAGIC)


def test_decode_strips_data_url_prefix():
    raw = decode_png("data:image/png;base64," + _png_b64())
    assert raw.startswith(PNG_MAGIC)


def test_decode_rejects_non_png():
    bad = base64.b64encode(b"this is not a png").decode()
    with pytest.raises(ValueError, match="kein PNG"):
        decode_png(bad)


def test_decode_rejects_broken_base64():
    with pytest.raises(ValueError, match="base64"):
        decode_png("@@@ not base64 @@@")


def test_decode_rejects_oversized(monkeypatch):
    monkeypatch.setattr("chemdraw_tool.png_writer.MAX_PNG_BYTES", 4)
    big = base64.b64encode(PNG_MAGIC + b"xxxxx").decode()  # 13 bytes > 4
    with pytest.raises(ValueError, match="zu groß"):
        decode_png(big)


def test_save_writes_named_file(tmp_path):
    p = save_png_bytes(_png_b64(), "Aspirin", tmp_path)
    assert p.exists()
    assert p.name == "Aspirin.png"
    assert p.read_bytes().startswith(PNG_MAGIC)


def test_save_sanitizes_filename_and_blocks_traversal(tmp_path):
    p = save_png_bytes(_png_b64(), "../../etc/pa sswd", tmp_path)
    assert p.parent == tmp_path
    assert "/" not in p.name and "\\" not in p.name
    assert p.name.endswith(".png")


def test_save_avoids_collision(tmp_path):
    p1 = save_png_bytes(_png_b64(), "x", tmp_path)
    p2 = save_png_bytes(_png_b64(), "x", tmp_path)
    assert p1 != p2
    assert p1.exists() and p2.exists()


def test_save_empty_name_falls_back(tmp_path):
    p = save_png_bytes(_png_b64(), "   ", tmp_path)
    assert p.name == "molekuel.png"


def test_decode_tolerates_whitespace():
    raw = decode_png("data:image/png;base64,\n" + _png_b64() + "\n")
    assert raw.startswith(PNG_MAGIC)


def test_decode_rejects_oversized_before_decode(monkeypatch):
    monkeypatch.setattr("chemdraw_tool.png_writer.MAX_PNG_BYTES", 9)
    # Encoded string longer than the recomputed encoded cap → rejected pre-decode.
    huge = "A" * 1000
    with pytest.raises(ValueError, match="zu groß"):
        decode_png(huge)


def test_decode_data_url_prefix_only_is_not_png():
    with pytest.raises(ValueError, match="kein PNG"):
        decode_png("data:image/png;base64,")


def test_save_truncates_long_filename(tmp_path):
    p = save_png_bytes(_png_b64(), "a" * 300, tmp_path)
    assert p.exists()
    assert len(p.stem) <= 200
    assert p.name.endswith(".png")
