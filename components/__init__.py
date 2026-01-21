"""Component modules for the Aspen Investing Menu app."""

from utils.styles.branding import (
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
)
from components.cards import render_card_view, render_explanation_card, _load_explanation_card
from components.footer import render_footer
from components.modal import render_strategy_modal
from components.filters import render_filters, render_filters_inline, render_search_bar
from components.tab_overview import render_allocation_tab

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
    "STREAMLIT_CUSTOM_CSS",
    # Components
    "render_card_view",
    "render_explanation_card",
    "_load_explanation_card",
    "render_filters",
    "render_filters_inline",
    "render_footer",
    "render_search_bar",
    "render_strategy_modal",
    # Individual tab components
    "render_allocation_tab",
]
