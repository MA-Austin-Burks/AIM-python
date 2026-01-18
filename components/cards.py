from typing import Any, Optional
import base64

import polars as pl
import streamlit as st
from datetime import datetime
from streamlit_product_card import product_card

from styles.branding import hex_to_rgba
from utils.core.formatting import get_series_color_from_row
from components.constants import (
    CARD_GRID_COLUMNS,
    CARD_ORDER_KEY,
    CARD_ORDER_OPTIONS,
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    DEFAULT_CARD_ORDER,
    SELECTED_STRATEGY_MODAL_KEY,
)


def render_explanation_card() -> None:
    """Render an explanation card describing the site's intent and how to use it."""
    with st.container(border=False):
        st.markdown("### Aspen Investing Menu 2.0")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d')}")
        with st.expander("About this app", expanded=True):
            st.markdown(
                """
                This application replaces [**AIM 1.0**](https://merceradvisors.sharepoint.com/:x:/r/sites/InvestmentStrategy/_layouts/15/Doc.aspx?sourcedoc=%7BE603B512-F595-4006-B33C-C6DB7CEA1487%7D&file=Aspen%20Investing%20Menu.xlsx&action=default&mobileredirect=true) 
                and helps you explore and filter investment strategies available on the Aspen Investment platform. 
                Use the sidebar filters to narrow down strategies based on your investment criteria, or search 
                for specific strategy names.
                
                **How to use:**
                - **Search**: Type a strategy name in the search box to quickly find specific strategies
                - **Filters**: Use the sidebar filters to refine results
                - **View Details**: Click on any strategy card to see detailed allocation information
                - **Sort**: Use the "Order By" dropdown to sort strategies by various criteria
                
                Click on any strategy card below to explore its detailed allocation breakdown.
                """
            )

# Card styles defined at module level to avoid recreating dict on every render
# This improves performance when rendering many cards
_CARD_STYLES = {
    "card": {
        "border-radius": "12px",
        "box-shadow": "0 4px 12px rgba(0,0,0,0.08)",
        "border": "1px solid rgba(0,0,0,0.06)",
        "cursor": "pointer",
        "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        "background": "linear-gradient(135deg, #ffffff 0%, #fafafa 100%)",
        "overflow": "hidden",
    },
    "card:hover": {
        "box-shadow": "0 12px 24px rgba(0,0,0,0.15)",
        "transform": "translateY(-4px)",
        "border-color": "rgba(192, 6, 134, 0.2)",
    },
    "image": {
        "min-width": "40px",
        "border-radius": "12px 0 0 12px",
        "position": "relative",
    },
    "title": {
        "font-size": "1.15rem",
        "font-weight": "600",
        "color": "#2c3e50",
        "margin-bottom": "0.875rem",
        "line-height": "1.4",
        "letter-spacing": "-0.01em",
    },
    "description": {
        "line-height": "1.8",
        "color": "#546e7a",
        "font-size": "0.925rem",
        "font-weight": "400",
    },
}




@st.cache_data(ttl=3600)
def _generate_card_svg(series_color: str, recommended: bool) -> str:
    """Generate and cache the SVG image for a card. Returns base64 data URL."""
    star_html = ""
    if recommended:
        star_html = '''
        <defs>
            <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="0" dy="1" stdDeviation="1" flood-opacity="0.3"/>
            </filter>
        </defs>
        <text x="20" y="30" fill="#FFD700" font-size="24" font-weight="bold" 
              text-anchor="middle" filter="url(#shadow)">★</text>
        '''
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="40" height="200">
        <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:{series_color};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{series_color};stop-opacity:0.85" />
            </linearGradient>
        </defs>
        <rect width="40" height="200" fill="url(#grad)"/>
        {star_html}
    </svg>'''
    
    svg_encoded = base64.b64encode(svg_content.encode()).decode()
    return f"data:image/svg+xml;base64,{svg_encoded}"


def _render_strategy_card(strategy_row: dict[str, Any], index: int) -> tuple[bool, str]:
    """Render a single strategy card, return (clicked, strategy_name)."""
    strategy_name = strategy_row["Strategy"]
    series_color = get_series_color_from_row(strategy_row)
    
    recommended = strategy_row.get("Recommended", False)
    equity_pct = strategy_row.get("Equity %", 0)
    yield_val = strategy_row.get("Yield")
    expense_ratio = strategy_row.get("Expense Ratio", 0)
    minimum = strategy_row.get("Minimum", 0)
    
    colored_image_url = _generate_card_svg(series_color, recommended)
    
    if yield_val is not None:
        yield_str = f"{yield_val * 100:.2f}%"
    else:
        yield_str = "N/A"
    
    description_lines = [
        f"Equity: {equity_pct:.0f}%",
        f"Yield: {yield_str}",
        f"Expense Ratio: {expense_ratio * 100:.2f}%",
        f"Minimum: ${minimum:,.0f}",
    ]
    
    # Background color uses series color at low opacity for visual grouping
    # Helps users quickly identify strategy series without overwhelming the card
    card_bg_color = hex_to_rgba(series_color, alpha=0.1)
    card_styles = {
        **_CARD_STYLES,
        "card": {
            **_CARD_STYLES["card"],
            "background": card_bg_color,
        },
    }
    
    card_key = f"strategy_card_{index}"
    clicked = product_card(
        product_name=strategy_name,
        description=description_lines,
        product_image=colored_image_url,
        picture_position="left",
        image_width_percent=10,
        image_aspect_ratio="native",
        image_object_fit="cover",
        enable_animation=True,
        on_button_click=None,
        button_text=None,
        styles=card_styles,
        key=card_key,
    )
    return clicked, strategy_name


def _apply_sort_order(strategies: pl.DataFrame, sort_order: str) -> pl.DataFrame:
    """Apply sorting based on the selected order."""
    if sort_order == "Recommended (Default)":
        # Investment Committee recommendations prioritized, then by equity allocation
        return strategies.sort(
            by=["Recommended", "Equity %", "Strategy"],
            descending=[True, True, True],
            nulls_last=True,
        )
    elif sort_order == "Investment Committee Status":
        return strategies.sort("Recommended", descending=True, nulls_last=True)
    elif sort_order == "Acct Min - Highest to Lowest":
        return strategies.sort("Minimum", descending=True, nulls_last=True)
    elif sort_order == "Acct Min - Lowest to Highest":
        return strategies.sort("Minimum", descending=False, nulls_last=True)
    elif sort_order == "Expense Ratio - Highest to Lowest":
        return strategies.sort("Expense Ratio", descending=True, nulls_last=True)
    elif sort_order == "Expense Ratio - Lowest to Highest":
        return strategies.sort("Expense Ratio", descending=False, nulls_last=True)
    elif sort_order == "Yield - High to Low":
        return strategies.sort("Yield", descending=True, nulls_last=True)
    elif sort_order == "Yield - Low to High":
        return strategies.sort("Yield", descending=False, nulls_last=True)
    elif sort_order == "Equity % - High to Low":
        return strategies.sort("Equity %", descending=True, nulls_last=True)
    elif sort_order == "Equity % - Low to High":
        return strategies.sort("Equity %", descending=False, nulls_last=True)
    elif sort_order == "Strategy Name - A to Z":
        return strategies.sort("Strategy", descending=False, nulls_last=True)
    elif sort_order == "Strategy Name - Z to A":
        return strategies.sort("Strategy", descending=True, nulls_last=True)
    else:
        return strategies.sort(
            by=["Recommended", "Equity %", "Strategy"],
            descending=[True, True, True],
            nulls_last=True,
        )


def _reset_cards_displayed() -> None:
    """Reset the number of cards displayed when filters change."""
    st.session_state[CARDS_DISPLAYED_KEY] = CARDS_PER_LOAD


def render_card_view(filtered_strategies: pl.DataFrame) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    """Render the card view with filtered strategies.
    
    Steps:
    1. Initialize session state for card ordering and pagination
    2. Render sort order selector
    3. Apply sorting and check for empty results
    4. Render cards in grid layout
    5. Render "Load More" button if more cards available
    """
    # ============================================================================
    # STEP 1: Initialize session state for card ordering and pagination
    # ============================================================================
    total_count = filtered_strategies.height
    
    if CARD_ORDER_KEY not in st.session_state:
        st.session_state[CARD_ORDER_KEY] = DEFAULT_CARD_ORDER
    
    if CARDS_DISPLAYED_KEY not in st.session_state:
        st.session_state[CARDS_DISPLAYED_KEY] = CARDS_PER_LOAD
    
    # ============================================================================
    # STEP 2: Render sort order selector
    # ============================================================================
    selected_order = st.selectbox(
        "Order By:",
        options=CARD_ORDER_OPTIONS,
        index=CARD_ORDER_OPTIONS.index(st.session_state[CARD_ORDER_KEY]) if st.session_state[CARD_ORDER_KEY] in CARD_ORDER_OPTIONS else 0,
        key="card_order_by_select",
        on_change=_reset_cards_displayed,
    )
    st.session_state[CARD_ORDER_KEY] = selected_order
    
    # ============================================================================
    # STEP 3: Apply sorting and check for empty results
    # ============================================================================
    filtered_strategies = _apply_sort_order(filtered_strategies, selected_order)
    
    if filtered_strategies.height == 0:
        st.info("No strategies match the current filters.")
        return None, None
    
    # Pagination: load cards incrementally to improve initial render performance
    cards_to_show = min(st.session_state[CARDS_DISPLAYED_KEY], total_count)
    display_strategies = filtered_strategies.head(cards_to_show)
    
    st.markdown(f"**Showing {cards_to_show} of {total_count} strategies**")
    
    # ============================================================================
    # STEP 4: Render cards in grid layout
    # ============================================================================
    cols = st.columns(CARD_GRID_COLUMNS)
    
    for idx, row in enumerate(display_strategies.iter_rows(named=True)):
        col_idx = idx % CARD_GRID_COLUMNS
        with cols[col_idx]:
            clicked, strategy_name = _render_strategy_card(row, idx)
            if clicked:
                st.session_state[SELECTED_STRATEGY_MODAL_KEY] = strategy_name
                st.rerun()
    
    # ============================================================================
    # STEP 5: Render "Load More" button if more cards available
    # ============================================================================
    remaining = total_count - cards_to_show
    if remaining > 0:
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            next_load = min(CARDS_PER_LOAD, remaining)
            if st.button(
                f"Load {next_load} More ({remaining} remaining)",
                width="stretch",
                type="secondary",
            ):
                st.session_state[CARDS_DISPLAYED_KEY] += CARDS_PER_LOAD
                st.rerun()
    
    return None, None
