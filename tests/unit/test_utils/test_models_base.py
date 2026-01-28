"""Tests for utils.models.base module."""

import pytest

from utils.models.base import _normalize_bool, _normalize_subtype


def test_normalize_bool_string_true():
    """Test _normalize_bool with string 'TRUE'."""
    assert _normalize_bool("TRUE") is True
    assert _normalize_bool("true") is True  # Case insensitive
    assert _normalize_bool("True") is True


def test_normalize_bool_string_yes():
    """Test _normalize_bool with string 'YES'."""
    assert _normalize_bool("YES") is True
    assert _normalize_bool("yes") is True
    assert _normalize_bool("Yes") is True


def test_normalize_bool_string_one():
    """Test _normalize_bool with string '1'."""
    assert _normalize_bool("1") is True


def test_normalize_bool_string_false():
    """Test _normalize_bool with string 'FALSE'."""
    assert _normalize_bool("FALSE") is False
    assert _normalize_bool("false") is False
    assert _normalize_bool("NO") is False
    assert _normalize_bool("0") is False


def test_normalize_bool_boolean_values():
    """Test _normalize_bool with actual boolean values."""
    assert _normalize_bool(True) is True
    assert _normalize_bool(False) is False


def test_normalize_bool_numeric():
    """Test _normalize_bool with numeric values."""
    assert _normalize_bool(1) is True
    assert _normalize_bool(0) is False
    assert _normalize_bool(42) is True  # Any non-zero is truthy


def test_normalize_bool_edge_cases():
    """Test _normalize_bool with edge cases."""
    assert _normalize_bool("") is False  # Empty string is falsy
    assert _normalize_bool(None) is False  # None is falsy
    assert _normalize_bool([]) is False  # Empty list is falsy
    assert _normalize_bool([1]) is True  # Non-empty list is truthy


def test_normalize_subtype_none():
    """Test _normalize_subtype with None."""
    result = _normalize_subtype(None)
    assert result == []


def test_normalize_subtype_list():
    """Test _normalize_subtype with list."""
    result = _normalize_subtype(["Type A", "Type B"])
    assert result == ["Type A", "Type B"]


def test_normalize_subtype_list_with_non_strings():
    """Test _normalize_subtype converts list items to strings."""
    result = _normalize_subtype([1, 2, 3])
    assert result == ["1", "2", "3"]


def test_normalize_subtype_string():
    """Test _normalize_subtype with string."""
    result = _normalize_subtype("Single Type")
    assert result == ["Single Type"]


def test_normalize_subtype_other_types():
    """Test _normalize_subtype with other types converts to string."""
    result = _normalize_subtype(123)
    assert result == ["123"]

    result = _normalize_subtype(True)
    assert result == ["True"]
