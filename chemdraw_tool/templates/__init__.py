"""Mechanism template registry with lazy loading."""

from __future__ import annotations

from chemdraw_tool.mechanism import MechanismTemplate

_REGISTRY: dict[str, MechanismTemplate] = {}


def register(template: MechanismTemplate) -> None:
    _REGISTRY[template.id] = template


def get_template(template_id: str) -> MechanismTemplate | None:
    _ensure_loaded()
    return _REGISTRY.get(template_id)


def list_templates() -> list[str]:
    _ensure_loaded()
    return sorted(_REGISTRY.keys())


_loaded = False


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    from chemdraw_tool.templates import (
        ester,  # noqa: F401
        substitution,  # noqa: F401
    )
