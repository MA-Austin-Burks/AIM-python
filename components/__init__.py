"""Component modules for the Aspen Investing Menu app."""

from components.branding import (
    CHART_COLORS_ALLOCATION,
    CHART_COLORS_EXTENDED,
    CHART_COLORS_PRIMARY,
    CHART_COLORS_SEQUENTIAL_AZURE,
    CHART_COLORS_SEQUENTIAL_IRIS,
    CHART_COLORS_SEQUENTIAL_RASPBERRY,
    FONTS,
    PRIMARY,
    SECONDARY,
    SERIES_COLORS,
    SPECIAL,
    STREAMLIT_CUSTOM_CSS,
    TERTIARY,
    get_chart_layout,
)
from components.dataframe import (
    render_dataframe,
    render_dataframe_section,
)
from components.filters import build_filter_expression
from components.footer import render_footer
from components.header import render_page_header
from components.sidebar import render_sidebar
from components.tabs import render_tabs

__all__ = [
    # Branding
    "PRIMARY",
    "SECONDARY",
    "TERTIARY",
    "SPECIAL",
    "CHART_COLORS_PRIMARY",
    "CHART_COLORS_EXTENDED",
    "CHART_COLORS_ALLOCATION",
    "CHART_COLORS_SEQUENTIAL_RASPBERRY",
    "CHART_COLORS_SEQUENTIAL_IRIS",
    "CHART_COLORS_SEQUENTIAL_AZURE",
    "SERIES_COLORS",
    "FONTS",
    "get_chart_layout",
    "STREAMLIT_CUSTOM_CSS",
    # Components
    "render_dataframe",
    "render_dataframe_section",
    "build_filter_expression",
    "render_footer",
    "render_page_header",
    "render_sidebar",
    "render_tabs",
]
