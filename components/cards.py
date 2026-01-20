from typing import Any, Optional, Final

import polars as pl
import streamlit as st
from components.model_card import model_card

from components.filters import render_search_bar
from utils.core.constants import (
    CARD_GRID_COLUMNS,
    CARD_ORDER_KEY,
    CARD_ORDER_OPTIONS,
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
    with open("data/explanation_card.txt", "r", encoding="utf-8") as f:
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
        equity=equity_pct,
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
    # STEP 2: Render sort order selector and search bar (filters are rendered above this)
    # ============================================================================
    col_order, col_search = st.columns([1, 2])
    with col_order:
        selected_order = st.selectbox(
            "Order By:",
            options=CARD_ORDER_OPTIONS,
            index=CARD_ORDER_OPTIONS.index(card_order) if card_order in CARD_ORDER_OPTIONS else 0,
            key="card_order_by_select",
            on_change=_reset_cards_displayed,
        )
        st.session_state[CARD_ORDER_KEY] = selected_order
    
    with col_search:
        search_active, strategy_search = render_search_bar()
    
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
    # STEP 4: Render cards in grid layout
    # ============================================================================
    # Render cards row by row for consistent spacing
    clicked_strategy = None
    
    # Convert to list for easier row-based rendering
    strategy_rows = list(display_strategies.iter_rows(named=True))
    
    # Render cards in rows of CARD_GRID_COLUMNS
    for row_start in range(0, len(strategy_rows), CARD_GRID_COLUMNS):
        # Get cards for this row
        row_cards = strategy_rows[row_start:row_start + CARD_GRID_COLUMNS]
        
        # Create columns for this row only
        cols = st.columns(CARD_GRID_COLUMNS)
        
        # Render each card in this row
        for col_idx in range(len(row_cards)):
            with cols[col_idx]:
                card_idx = row_start + col_idx
                clicked, strategy_name = _render_strategy_card(row_cards[col_idx], card_idx)
                if clicked:
                    clicked_strategy = strategy_name
    
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
