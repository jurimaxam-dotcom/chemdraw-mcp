"""Persist client-rendered PNG bytes to disk (PNG-export fallback path).

The MCP-App UI renders the PNG in-browser and, when the sandbox blocks the
image clipboard, sends the base64 PNG here to be written as a file. This module
only decodes, validates and stores — it never renders.
"""

from __future__ import annotations

import base64
import binascii
import re
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_PNG_BYTES = 8 * 1024 * 1024  # 8 MB

_DATA_URL_PREFIX = re.compile(r"^data:image/png;base64,", re.IGNORECASE)
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_stem(name: str) -> str:
    """Filesystem-safe stem: strip path parts, collapse unsafe chars."""
    name = (name or "").strip()
    # Drop any directory components to prevent path traversal.
    name = name.replace("\\", "/").split("/")[-1]
    stem = _UNSAFE_CHARS.sub("_", name).strip("._")
    # Cap length so long IUPAC names don't trigger OSError (filesystem limit ~255).
    return (stem or "molekuel")[:200]


def decode_png(png_base64: str) -> bytes:
    """Decode a base64 PNG (optionally a `data:` URL).

    Raises ValueError on invalid base64, oversize, or non-PNG content.
    Oversize is rejected on the *encoded* length first, so an enormous
    payload is not fully materialized in memory before being refused.
    """
    payload = _DATA_URL_PREFIX.sub("", png_base64.strip())
    payload = re.sub(r"\s+", "", payload)  # tolerate line-wrapped base64
    # ceil(MAX_PNG_BYTES / 3) * 4, plus slack for padding.
    max_encoded = (MAX_PNG_BYTES + 2) // 3 * 4 + 16
    if len(payload) > max_encoded:
        raise ValueError(f"PNG zu groß (encoded {len(payload)} > {max_encoded} Bytes)")
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"Ungültiges base64: {exc}") from exc
    if len(raw) > MAX_PNG_BYTES:
        raise ValueError(f"PNG zu groß ({len(raw)} > {MAX_PNG_BYTES} Bytes)")
    if not raw.startswith(PNG_MAGIC):
        raise ValueError("Daten sind kein PNG (Magic-Bytes fehlen)")
    return raw


def save_png_bytes(png_base64: str, filename: str, output_dir: Path) -> Path:
    """Decode + validate + write the PNG into output_dir. Returns the written path.

    Collisions get a numeric suffix (`name-2.png`, `name-3.png`, ...).
    """
    raw = decode_png(png_base64)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(filename)
    path = output_dir / f"{stem}.png"
    counter = 2
    while path.exists():
        path = output_dir / f"{stem}-{counter}.png"
        counter += 1
    path.write_bytes(raw)
    return path
