"""Formatting utilities for the application."""

from typing import Any

from styles.branding import PRIMARY, SERIES_COLORS


def format_currency_compact(value: float) -> str:
    """Format currency value with K (thousands) and M (millions) suffixes."""
    if value is None or value == 0:
        return "$0.0"
    
    abs_value = abs(value)
    
    if abs_value >= 1_000_000:
        # Format as millions with 1 decimal place
        millions = value / 1_000_000
        return f"${millions:.1f}M"
    elif abs_value >= 1_000:
        # Format as thousands with 1 decimal place
        thousands = value / 1_000
        return f"${thousands:.1f}K"
    else:
        # Format as regular number with 1 decimal place
        return f"${value:.1f}"


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


