from typing import Any, Optional

import polars as pl
import streamlit as st
from components.model_card import model_card

from utils.core.formatting import get_series_color_from_row
from utils.core.session_state import get_or_init
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
    with st.expander("About the Aspen Investment Menu", icon=":material/book:"):
        with open("data/explanation_card.txt", "r", encoding="utf-8") as f:
            st.markdown(f.read())


def _render_strategy_card(strategy_row: dict[str, Any], index: int) -> tuple[bool, str]:
    """Render a single strategy card using the custom investment card component, return (clicked, strategy_name)."""
    strategy_name = strategy_row["Strategy"]
    series_color = get_series_color_from_row(strategy_row)
    
    recommended = strategy_row.get("Recommended", False)
    equity_pct = strategy_row.get("Equity %", 0)
    yield_val = strategy_row.get("Yield")
    expense_ratio = strategy_row.get("Expense Ratio", 0)
    minimum = strategy_row.get("Minimum", 0)
    
    # Convert decimal values to percentages for display
    # yield_val is stored as decimal (e.g., 0.085 for 8.5%)
    yield_pct_display = (yield_val * 100) if yield_val is not None else 0.0
    
    # expense_ratio is stored as decimal (e.g., 0.0045 for 0.45%)
    expense_ratio_display = expense_ratio * 100
    
    card_key = f"strategy_card_{index}"
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
    
    card_order = get_or_init(CARD_ORDER_KEY, DEFAULT_CARD_ORDER)
    cards_displayed = get_or_init(CARDS_DISPLAYED_KEY, CARDS_PER_LOAD)
    
    # ============================================================================
    # STEP 2: Render sort order selector
    # ============================================================================
    selected_order = st.selectbox(
        "Order By:",
        options=CARD_ORDER_OPTIONS,
        index=CARD_ORDER_OPTIONS.index(card_order) if card_order in CARD_ORDER_OPTIONS else 0,
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
    cards_to_show = min(cards_displayed, total_count)
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
                use_container_width=True,
                type="primary",
            ):
                st.session_state[CARDS_DISPLAYED_KEY] += CARDS_PER_LOAD
                st.rerun()
    
    return None, None
