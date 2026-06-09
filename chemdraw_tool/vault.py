"""Optional local-vault integration.

Off by default. Set CHEMDRAW_VAULT_PATH to enable a single-user, on-disk
markdown knowledge base. For the default user-facing flow, materials live
in Claude Projects — the host handles storage and search there.
"""

import os
from pathlib import Path

_env_path = os.environ.get("CHEMDRAW_VAULT_PATH", "").strip()
VAULT_PATH: Path | None = Path(_env_path).expanduser() if _env_path else None


def is_enabled() -> bool:
    return VAULT_PATH is not None and VAULT_PATH.exists()


def list_entries() -> dict[str, list[str]]:
    if not is_enabled():
        return {}
    categories: dict[str, list[str]] = {}
    for md in sorted(VAULT_PATH.rglob("*.md")):
        rel = md.relative_to(VAULT_PATH)
        parts = rel.parts
        cat = parts[0] if len(parts) > 1 else "Allgemein"
        categories.setdefault(cat, []).append(md.stem)
    return categories


def search(query: str) -> list[dict[str, str]]:
    if not is_enabled():
        return []
    q = query.lower().strip()
    if not q:
        return []

    results = []
    for md in VAULT_PATH.rglob("*.md"):
        score = 0
        stem_lower = md.stem.lower()

        content_raw = None
        if q == stem_lower:
            score = 100
        elif q in stem_lower:
            score = 80
        else:
            content_raw = md.read_text(encoding="utf-8")
            if q in content_raw.lower():
                score = 50

        if score == 0:
            continue

        if content_raw is None:
            content_raw = md.read_text(encoding="utf-8")
        snippet = _extract_snippet(content_raw, q)
        rel = md.relative_to(VAULT_PATH)
        cat = rel.parts[0] if len(rel.parts) > 1 else "Allgemein"
        results.append(
            {
                "name": md.stem,
                "category": cat,
                "path": str(rel),
                "score": score,
                "snippet": snippet,
            }
        )

    results.sort(key=lambda r: -r["score"])
    return results[:10]


def read_entry(name: str) -> tuple[str | None, str | None]:
    if not is_enabled():
        return None, None
    n = name.lower().strip()

    for md in VAULT_PATH.rglob("*.md"):
        if md.stem.lower() == n:
            return md.stem, md.read_text(encoding="utf-8")

    for md in VAULT_PATH.rglob("*.md"):
        if n in md.stem.lower():
            return md.stem, md.read_text(encoding="utf-8")

    for md in VAULT_PATH.rglob("*.md"):
        content = md.read_text(encoding="utf-8")
        if n in content.lower():
            return md.stem, content

    return None, None


def _extract_snippet(content: str, query: str, context_chars: int = 150) -> str:
    lower = content.lower()
    idx = lower.find(query.lower())
    if idx == -1:
        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith("---")
                and not stripped.startswith("tags:")
            ):
                return stripped[:200]
        return ""

    start = max(0, idx - context_chars)
    end = min(len(content), idx + len(query) + context_chars)
    snippet = content[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    return snippet
