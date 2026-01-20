"""Styling utilities and branding configuration."""

from styles.branding import (
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
    SERIES_COLORS,
    SPECIAL,
    STREAMLIT_CUSTOM_CSS,
    TERTIARY,
    hex_to_rgba,
)
from styles.table import (
    get_allocation_table_main_css,
    get_allocation_table_summary_css,
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
    "SERIES_COLORS",
    "SPECIAL",
    "STREAMLIT_CUSTOM_CSS",
    "TERTIARY",
    "hex_to_rgba",
    # Table styling exports
    "get_allocation_table_main_css",
    "get_allocation_table_summary_css",
]
