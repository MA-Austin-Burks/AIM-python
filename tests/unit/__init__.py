"""Tests for utils.branding module."""

import pytest

from utils.branding import hex_to_rgba, get_subtype_color, SUBTYPE_COLORS


def test_hex_to_rgba_valid_color():
    """Test hex_to_rgba with valid hex color."""
    # Test a known color: #C00686 (raspberry)
    result = hex_to_rgba("#C00686", 0.5)

    # Expected: rgba(192, 6, 134, 0.50)
    assert result == "rgba(192, 6, 134, 0.50)"


def test_hex_to_rgba_without_hash_prefix():
    """Test hex_to_rgba handles hex without # prefix."""
    result = hex_to_rgba("C00686", 1.0)

    assert result == "rgba(192, 6, 134, 1.00)"


def test_hex_to_rgba_black():
    """Test hex_to_rgba with black color."""
    result = hex_to_rgba("#000000", 0.0)

    assert result == "rgba(0, 0, 0, 0.00)"


def test_hex_to_rgba_white():
    """Test hex_to_rgba with white color."""
    result = hex_to_rgba("#FFFFFF", 0.75)

    assert result == "rgba(255, 255, 255, 0.75)"


def test_hex_to_rgba_alpha_rounding():
    """Test that alpha values are rounded to 2 decimal places."""
    result = hex_to_rgba("#C00686", 0.123456)

    # Should round to 2 decimal places
    assert result == "rgba(192, 6, 134, 0.12)"


def test_get_subtype_color_known_subtype():
    """Test get_subtype_color with known subtype."""
    # Test with a known subtype from SUBTYPE_COLORS
    result = get_subtype_color("Multifactor Series")

    # Should return the color from SUBTYPE_COLORS
    expected = SUBTYPE_COLORS["Multifactor Series"]
    assert result == expected


def test_get_subtype_color_unknown_subtype():
    """Test get_subtype_color with unknown subtype returns default."""
    result = get_subtype_color("Unknown Subtype")

    # Should return default (raspberry)
    from utils.branding import PRIMARY

    assert result == PRIMARY["raspberry"]


def test_get_subtype_color_empty_string():
    """Test get_subtype_color with empty string returns default."""
    result = get_subtype_color("")

    from utils.branding import PRIMARY

    assert result == PRIMARY["raspberry"]


def test_get_subtype_color_all_known_subtypes():
    """Test get_subtype_color for all known subtypes."""
    # Test that all subtypes in SUBTYPE_COLORS work
    for subtype, expected_color in SUBTYPE_COLORS.items():
        result = get_subtype_color(subtype)
        assert result == expected_color, f"Failed for subtype: {subtype}"
