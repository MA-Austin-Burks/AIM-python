from typing import Any, Optional, Final

import polars as pl
import streamlit as st
from components.model_card import model_card

from utils.core.constants import (
    CARD_FIXED_WIDTH,
    CARD_GRID_COLUMNS,
    CARD_ORDER_KEY,
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    DEFAULT_CARD_ORDER,
    SELECTED_STRATEGY_MODAL_KEY,
)
from utils.styles.branding import get_series_color_from_row
from utils.core.session_state import get_or_init


@st.cache_data(ttl=3600)
def _load_explanation_card() -> str:
    """Load explanation card text file (cached for 1 hour)."""
    with open("pages/about/data/explanation_card.txt", "r", encoding="utf-8") as f:
        return f.read()


def render_explanation_card() -> None:
    """Render an explanation card describing the site's intent and how to use it."""
    with st.expander("About the Aspen Investment Menu", icon=":material/book:"):
        explanation_text: str = _load_explanation_card()
        st.markdown(explanation_text)


def _render_strategy_card(strategy_row: dict[str, Any], index: int) -> tuple[bool, str]:
    """Render a single strategy card using the custom investment card component, return (clicked, strategy_name)."""
    strategy_name = strategy_row["Strategy"]
    series_color = get_series_color_from_row(strategy_row)
    
    recommended_raw = strategy_row.get("Recommended", False)
    if isinstance(recommended_raw, str):
        recommended = recommended_raw.strip().upper() == "TRUE"
    else:
        recommended = bool(recommended_raw)
    equity_pct = strategy_row.get("Equity %", 0)
    yield_val = strategy_row.get("Yield")
    expense_ratio = strategy_row.get("Expense Ratio", 0)
    minimum = strategy_row.get("Minimum", 0)
    
    # Convert decimal values to percentages for display
    # yield_val is stored as decimal (e.g., 0.085 for 8.5%)
    yield_pct_display = (yield_val * 100) if yield_val is not None else 0.0
    
    # expense_ratio is stored as decimal (e.g., 0.0045 for 0.45%)
    expense_ratio_display = expense_ratio * 100
    
    card_key = f"strategy_card_{index}_{strategy_name}"
    clicked_id = model_card(
        id=strategy_name,
        name=strategy_name,
        yield_pct=yield_pct_display,
        expense_ratio=expense_ratio_display,
        minimum=minimum,
        color=series_color,
        featured=recommended,
        key=card_key,
    )
    
    # Return True if this card was clicked (clicked_id matches strategy_name)
    clicked = clicked_id == strategy_name
    return clicked, strategy_name


def _apply_sort_order(strategies: pl.DataFrame, sort_order: str) -> pl.DataFrame:
    """Apply sorting based on the selected order."""
    # Mapping of sort order options to (column, descending) tuples
    # Special case for "Recommended (Default)" uses multi-column sort
    sort_configs: dict[str, tuple[list[str], list[bool]] | tuple[str, bool]] = {
        "Acct Min - Highest to Lowest": ("Minimum", True),
        "Acct Min - Lowest to Highest": ("Minimum", False),
        "Expense Ratio - Highest to Lowest": ("Expense Ratio", True),
        "Expense Ratio - Lowest to Highest": ("Expense Ratio", False),
        "Yield - High to Low": ("Yield", True),
        "Yield - Low to High": ("Yield", False),
        "Equity % - High to Low": ("Equity %", True),
        "Equity % - Low to High": ("Equity %", False),
        "Strategy Name - A to Z": ("Strategy", False),
        "Strategy Name - Z to A": ("Strategy", True),
    }
    
    # Default sort: Investment Committee recommendations prioritized, then by equity allocation
    default_sort = (
        ["Recommended", "Equity %", "Strategy"],
        [True, True, True]
    )
    
    # Get sort configuration
    sort_config = sort_configs.get(sort_order)
    
    if sort_config is None or sort_order == "Recommended (Default)":
        # Use default multi-column sort
        return strategies.sort(
            by=default_sort[0],
            descending=default_sort[1],
            nulls_last=True,
        )
    
    # Single column sort
    column, descending = sort_config
    return strategies.sort(column, descending=descending, nulls_last=True)


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
    
    Args:
        filtered_strategies: Filtered strategy DataFrame
    """
    # ============================================================================
    # STEP 1: Initialize session state for card ordering and pagination
    # ============================================================================
    total_count = filtered_strategies.height
    
    card_order = get_or_init(CARD_ORDER_KEY, DEFAULT_CARD_ORDER)
    cards_displayed = get_or_init(CARDS_DISPLAYED_KEY, CARDS_PER_LOAD)
    
    # ============================================================================
    # STEP 2: Get sort order from session state (rendered above filters in search.py)
    # ============================================================================
    selected_order = st.session_state.get(CARD_ORDER_KEY, DEFAULT_CARD_ORDER)
    
    # ============================================================================
    # STEP 3: Apply sorting and check for empty results
    # ============================================================================
    filtered_strategies = _apply_sort_order(filtered_strategies, selected_order)
    
    if filtered_strategies.height == 0:
        st.info("No strategies match the current filters.")
        return None, None
    
    # Pagination: load cards incrementally to improve initial render performance
    cards_to_show = min(cards_displayed, total_count)
    display_strategies = filtered_strategies.head(cards_to_show)
    
    st.markdown(f"**Showing {cards_to_show} of {total_count} strategies**")
    
    # ============================================================================
    # STEP 4: Render cards in flex container (fixed width, dynamic wrapping)
    # ============================================================================
    clicked_strategy = None
    
    # Convert to list for easier rendering
    strategy_rows = list(display_strategies.iter_rows(named=True))
    
    # Add CSS to ensure cards spread evenly even in the last row
    # Streamlit adds 'st-key-' prefix to key-based classes
    st.markdown(
        """
        <style>
        /* Target the cards container to ensure even distribution */
        .st-key-cards-flex-container {
            justify-content: space-evenly !important;
        }
        /* Ensure card containers don't shrink */
        .st-key-cards-flex-container > div {
            flex: 0 0 auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Use st.container with horizontal=True for automatic flexbox wrapping
    # Each card is wrapped in a fixed-width container to ensure consistent sizing
    with st.container(horizontal=True, gap="small", key="cards-flex-container"):
        # Render all cards sequentially, each wrapped in a fixed-width container
        for card_idx, strategy_row in enumerate(strategy_rows):
            # Wrap each card in a fixed-width container
            # Convert "350px" to integer for width parameter
            card_width_px = int(CARD_FIXED_WIDTH.replace("px", ""))
            with st.container(width=card_width_px):
                clicked, strategy_name = _render_strategy_card(strategy_row, card_idx)
                if clicked:
                    clicked_strategy = strategy_name
        
        # Add empty placeholder cards to fill incomplete last row
        # Using CARD_GRID_COLUMNS (4) as expected cards per row
        num_cards = len(strategy_rows)
        cards_per_row = CARD_GRID_COLUMNS
        remainder = num_cards % cards_per_row
        
        if remainder > 0:
            # Calculate how many empty cards needed to complete the row
            empty_cards_needed = cards_per_row - remainder
            
            # Render empty placeholder cards (transparent, same dimensions as real cards)
            for empty_idx in range(empty_cards_needed):
                card_width_px = int(CARD_FIXED_WIDTH.replace("px", ""))
                with st.container(width=card_width_px):
                    # Render transparent placeholder with approximate card height
                    # Card height: ~60px header + ~120px body = ~180px total
                    st.markdown(
                        '<div style="width:100%;min-height:180px;opacity:0;pointer-events:none;"></div>',
                        unsafe_allow_html=True
                    )
    
    # Handle click after all cards are rendered to preserve layout
    if clicked_strategy:
        st.session_state[SELECTED_STRATEGY_MODAL_KEY] = clicked_strategy
        st.rerun()
    
    # ============================================================================
    # STEP 5: Render "Load More" button if more cards available
    # ============================================================================
    remaining = total_count - cards_to_show
    if remaining > 0:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            next_load = min(CARDS_PER_LOAD, remaining)

            if st.button(
                f"Load {next_load} More ({remaining} remaining)",
                use_container_width=True,
                type="primary",
            ):
                st.session_state[CARDS_DISPLAYED_KEY] += CARDS_PER_LOAD
                st.rerun()
    
    return None, None
