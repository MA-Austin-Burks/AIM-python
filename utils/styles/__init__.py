"""Styling utilities and branding configuration."""

from .branding import (
    CHART_COLORS_ALLOCATION,
    CHART_COLORS_EXTENDED,
    CHART_COLORS_PRIMARY,
    CHART_COLORS_SEQUENTIAL_AZURE,
    CHART_COLORS_SEQUENTIAL_IRIS,
    CHART_COLORS_SEQUENTIAL_RASPBERRY,
    FONTS,
    GOOGLE_FONTS_IMPORT,
    PRIMARY,
    SECONDARY,
    SUBTYPE_COLORS,
    SPECIAL,
    STREAMLIT_CUSTOM_CSS,
    TERTIARY,
    format_currency_compact,
    generate_badges,
    get_allocation_table_main_css,
    get_allocation_table_summary_css,
    get_series_color_from_row,
    get_strategy_color,
    hex_to_rgba,
)

__all__ = [
    # Branding exports
    "CHART_COLORS_ALLOCATION",
    "CHART_COLORS_EXTENDED",
    "CHART_COLORS_PRIMARY",
    "CHART_COLORS_SEQUENTIAL_AZURE",
    "CHART_COLORS_SEQUENTIAL_IRIS",
    "CHART_COLORS_SEQUENTIAL_RASPBERRY",
    "FONTS",
    "GOOGLE_FONTS_IMPORT",
    "PRIMARY",
    "SECONDARY",
    "SUBTYPE_COLORS",
    "SPECIAL",
    "STREAMLIT_CUSTOM_CSS",
    "TERTIARY",
    "hex_to_rgba",
    # Formatting utilities
    "format_currency_compact",
    "generate_badges",
    "get_strategy_color",
    "get_series_color_from_row",
    # Table styling exports
    "get_allocation_table_main_css",
    "get_allocation_table_summary_css",
]
