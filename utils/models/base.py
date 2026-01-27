"""Base utility functions for model normalization."""

from typing import Any


def _normalize_bool(value: Any) -> bool:
    """Normalize mixed truthy values into a bool."""
    if isinstance(value, str):
        return value.strip().upper() in ("TRUE", "YES", "1")
    return bool(value)


def _normalize_subtype(value: Any) -> list[str]:
    """Normalize Subtype field into a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return [str(value)]
