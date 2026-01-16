"""Formatting utilities for the application."""

from typing import Any

from styles.branding import PRIMARY, SERIES_COLORS


def format_currency_compact(value: float) -> str:
    """Format currency value with K (thousands) and M (millions) suffixes."""
    if value is None or value == 0:
        return "$0"
    
    abs_value = abs(value)
    
    if abs_value >= 1_000_000:
        # Format as millions with 1-2 decimal places
        millions = value / 1_000_000
        if millions % 1 == 0:
            return f"${int(millions)}M"
        elif millions * 10 % 1 == 0:
            return f"${millions:.1f}M"
        else:
            return f"${millions:.2f}M"
    elif abs_value >= 1_000:
        # Format as thousands with 0-1 decimal places
        thousands = value / 1_000
        if thousands % 1 == 0:
            return f"${int(thousands)}K"
        else:
            return f"${thousands:.1f}K"
    else:
        # Format as regular number
        return f"${int(value):,}"


def generate_badges(strategy_data: dict[str, Any]) -> list[str]:
    """Generate badge strings for a strategy based on its data."""
    badges = []

    if strategy_data.get("Recommended"):
        badges.append(":primary[Recommend]")

    strategy_type = strategy_data.get("Strategy Type")
    if strategy_type:
        badges.append(f":orange-badge[{strategy_type}]")

    strategy_type_field = strategy_data.get("Type")
    if strategy_type_field:
        badges.append(f":blue-badge[{strategy_type_field}]")

    if strategy_data.get("Tax-Managed"):
        badges.append(":green[Tax-Managed]")

    if strategy_data.get("Private Markets"):
        badges.append(":gray[Private Markets]")

    return badges


def get_strategy_color(strategy_type: str) -> str:
    """Get the color for a strategy based on its type/series."""
    return SERIES_COLORS.get(strategy_type, PRIMARY["raspberry"])


def get_series_color_from_row(strategy_row: dict[str, Any]) -> str:
    """Get the color for a strategy based on its Series/Type from a row dict."""
    series_list = strategy_row.get("Series", [])
    if series_list and len(series_list) > 0:
        series_name = series_list[0] if isinstance(series_list, list) else series_list
        return SERIES_COLORS.get(series_name, PRIMARY["light_gray"])
    
    # Fallback to Type field if Series is empty
    strategy_type = strategy_row.get("Type")
    if strategy_type:
        return SERIES_COLORS.get(strategy_type, PRIMARY["light_gray"])
    
    return PRIMARY["light_gray"]


def clean_product_name(product_name: str) -> str:
    """Remove 'ETF' suffix from product names if present.
    
    Args:
        product_name: Original product name
    
    Returns:
        Product name with 'ETF' removed from the end (if present)
    """
    if not product_name:
        return product_name
    
    # Remove trailing "ETF" (case-insensitive, with optional whitespace)
    cleaned = product_name.rstrip()
    if cleaned.upper().endswith("ETF"):
        cleaned = cleaned[:-3].rstrip()
    
    return cleaned
