from typing import Any

import polars as pl
import streamlit as st

from components.model_card import CARD_FIXED_WIDTH, model_card
from utils.branding import PRIMARY, SUBTYPE_COLORS
from utils.models.base import _normalize_bool, _normalize_subtype
from utils.session_state import get_or_init

# Session state keys
SELECTED_STRATEGY_MODAL_KEY = "selected_strategy_for_modal"
SELECTED_MODAL_TYPE_KEY = "selected_modal_type"
CARD_ORDER_KEY = "card_order_by"
CARDS_DISPLAYED_KEY = "cards_displayed"

# Card view constants
DEFAULT_CARD_ORDER = "Recommended (Default)"
CARDS_PER_LOAD = 20


def _get_subtype_color(row: dict[str, Any]) -> str:
    """Get the color for a strategy based on its subtype from a row dict."""
    subtype_primary = row.get("ss_subtype", "")
    if subtype_primary:
        return SUBTYPE_COLORS.get(subtype_primary, PRIMARY["light_gray"])
    series = row.get("series")
    subtype = _normalize_subtype(series) if series else []
    if subtype:
        return SUBTYPE_COLORS.get(subtype[0], PRIMARY["light_gray"])
    return PRIMARY["light_gray"]


def _render_strategy_card(row: dict[str, Any], index: int) -> tuple[bool, str, str]:
    """Render a single strategy card from a row dict, return (clicked, strategy_name, modal_type)."""
    strategy_name: str = str(row.get("strategy", ""))
    subtype_color: str = _get_subtype_color(row)
    recommended: bool = _normalize_bool(row.get("ic_recommend", False))
    # Convert decimals to percentages for display (component expects 0-100 range)
    yield_pct_display: float = float(row.get("yield", 0) or 0) * 100
    expense_ratio_display: float = float(row.get("fee", 0) or 0) * 100
    minimum: float = float(row.get("minimum", 0) or 0)
    modal_type: str = "strategy"

    card_key: str = f"strategy_card_{index}_{strategy_name}"
    result = model_card(
        id=strategy_name,
        name=strategy_name,
        color=subtype_color,
        recommended=recommended,
        metric_label_1="Yield",
        metric_value_1=yield_pct_display,
        metric_format_1="PERCENT",
        metric_label_2="Expense Ratio",
        metric_value_2=expense_ratio_display,
        metric_format_2="PERCENT",
        metric_label_3="Minimum",
        metric_value_3=minimum,
        metric_format_3="DOLLAR",
        modal_type=modal_type,
        key=card_key,
    )

    # Return True if this card was clicked (result.clicked is one-time trigger)
    clicked = getattr(result, "clicked", None) == strategy_name
    return clicked, strategy_name, modal_type


def _render_cais_card(row: dict[str, Any], index: int) -> tuple[bool, str, str]:
    """Render a single CAIS card from a row dict, return (clicked, strategy_name, modal_type)."""
    strategy_name = str(row.get("strategy", ""))
    # Use "Alternative Strategies" color from branding
    color = SUBTYPE_COLORS.get("Alternative Strategies", "#F9A602")
    recommended = False  # CAIS strategies are not recommended
    modal_type = "cais"

    card_key = f"cais_card_{index}_{strategy_name}"
    result = model_card(
        id=strategy_name,
        name=strategy_name,
        color=color,
        recommended=recommended,
        metric_label_1="CAIS Type",
        metric_value_1=str(row.get("cais_type", "")),
        metric_format_1="STRING",
        metric_label_2="Client Type",
        metric_value_2=str(row.get("client_type", "")),
        metric_format_2="STRING",
        metric_label_3="Minimum",
        metric_value_3=float(row.get("minimum", 0) or 0),
        metric_format_3="DOLLAR",  # Use built-in DOLLAR formatting (handles K/M)
        modal_type=modal_type,
        key=card_key,
    )

    # Return True if this card was clicked (result.clicked is one-time trigger)
    clicked = getattr(result, "clicked", None) == strategy_name
    return clicked, strategy_name, modal_type


def _apply_sort_order(strategies: pl.DataFrame, sort_order: str) -> pl.DataFrame:
    """Apply sorting based on the selected order."""
    # Mapping of sort order options to (column, descending) tuples
    # Special case for "Recommended (Default)" uses multi-column sort
    sort_configs: dict[str, tuple[list[str], list[bool]] | tuple[str, bool]] = {
        "Acct Min - Highest to Lowest": ("minimum", True),
        "Acct Min - Lowest to Highest": ("minimum", False),
        "Expense Ratio - Highest to Lowest": ("fee", True),
        "Expense Ratio - Lowest to Highest": ("fee", False),
        "Yield - High to Low": ("yield", True),
        "Yield - Low to High": ("yield", False),
        "Equity % - High to Low": ("equity_allo", True),
        "Equity % - Low to High": ("equity_allo", False),
        "Strategy Name - A to Z": ("strategy", False),
        "Strategy Name - Z to A": ("strategy", True),
    }

    # Default sort: Investment Committee recommendations prioritized, then by equity allocation, then by strategy name (A to Z)
    default_sort = (["ic_recommend", "equity_allo", "strategy"], [True, True, False])

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


def render_card_view(
    filtered_strategies: pl.DataFrame,
) -> None:
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
    total_count: int = filtered_strategies.height

    cards_displayed: int = get_or_init(CARDS_DISPLAYED_KEY, CARDS_PER_LOAD)

    # ============================================================================
    # STEP 2: Get sort order from session state (rendered above filters in search.py)
    # ============================================================================
    selected_order: str = st.session_state.get(CARD_ORDER_KEY, DEFAULT_CARD_ORDER)

    # ============================================================================
    # STEP 3: Apply sorting and check for empty results
    # ============================================================================
    filtered_strategies: pl.DataFrame = _apply_sort_order(
        filtered_strategies, selected_order
    )

    if filtered_strategies.height == 0:
        st.warning(
            ":material/search_off: No strategies match the current filters. Please try different filters."
        )
        return

    # Pagination: load cards incrementally to improve initial render performance
    cards_to_show: int = min(cards_displayed, total_count)
    display_strategies: pl.DataFrame = filtered_strategies.head(cards_to_show)

    st.markdown(f"**Showing {cards_to_show} of {total_count} strategies**")

    # ============================================================================
    # STEP 4: Render cards in grid layout (fixed width, responsive columns)
    # ============================================================================
    clicked_strategy = None
    clicked_modal_type = None

    # Convert DataFrame to list of dicts - no intermediate objects needed
    card_rows: list[dict[str, Any]] = display_strategies.to_dicts()

    # Add CSS to use CSS Grid for automatic responsive card layout
    # Grid handles last-row alignment naturally without placeholder cards
    # Streamlit adds 'st-key-' prefix to key-based classes
    st.markdown(
        f"""
        <style>
        /* Convert flex container to CSS Grid for better last-row handling */
        .st-key-cards-flex-container {{
            display: grid !important;
            grid-template-columns: repeat(auto-fill, {CARD_FIXED_WIDTH}) !important;
            justify-content: space-evenly !important;
            gap: 10px !important;
        }}
        /* Ensure card containers don't override card border-radius */
        .st-key-cards-flex-container > div > div {{
            border-radius: inherit !important;
        }}
        /* Ensure the card component itself maintains border-radius */
        .st-key-cards-flex-container .mc-card {{
            border-radius: 12px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Use st.container with horizontal=True, then CSS overrides to Grid layout
    # Grid ensures last row stays left-aligned while other rows are evenly distributed
    with st.container(horizontal=True, gap="small", key="cards-flex-container"):
        # Render all cards sequentially, each wrapped in a fixed-width container
        for card_idx, row in enumerate(card_rows):
            # Wrap each card in a fixed-width container
            # Convert "350px" to integer for width parameter
            card_width_px = int(CARD_FIXED_WIDTH.replace("px", ""))
            with st.container(width=card_width_px):
                # Detect CAIS rows by checking for non-null cais_type
                is_cais = row.get("cais_type") is not None
                if is_cais:
                    clicked, strategy_name, modal_type = _render_cais_card(
                        row, card_idx
                    )
                else:
                    clicked, strategy_name, modal_type = _render_strategy_card(
                        row, card_idx
                    )
                if clicked:
                    clicked_strategy = strategy_name
                    clicked_modal_type = modal_type

    # Handle click after all cards are rendered to preserve layout
    if clicked_strategy:
        st.session_state[SELECTED_STRATEGY_MODAL_KEY] = clicked_strategy
        st.session_state[SELECTED_MODAL_TYPE_KEY] = clicked_modal_type
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
                width="stretch",
                type="primary",
                key="load_more_cards_btn",
            ):
                st.session_state[CARDS_DISPLAYED_KEY] += CARDS_PER_LOAD
                st.rerun()
