import hashlib
from datetime import datetime

import polars as pl
import streamlit as st

from components import (
    build_filter_expression,
    render_card_view,
    render_filters,
    render_footer,
)
from components.cards import (
    CARD_ORDER_KEY,
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    DEFAULT_CARD_ORDER,
    SELECTED_MODAL_TYPE_KEY,
    SELECTED_STRATEGY_MODAL_KEY,
)
from components.modals import render_modal_by_type
from utils.branding import SUBTYPE_COLORS, get_subtype_color
from utils.data import load_cleaned_data, load_strategy_list
from utils.session_state import get_or_init, initialize_session_state, reset_if_changed

CARD_ORDER_OPTIONS = [
    "Recommended (Default)",
    "Acct Min - Highest to Lowest",
    "Acct Min - Lowest to Highest",
    "Expense Ratio - Highest to Lowest",
    "Expense Ratio - Lowest to Highest",
    "Yield - High to Low",
    "Yield - Low to High",
    "Equity % - High to Low",
    "Equity % - Low to High",
    "Strategy Name - A to Z",
    "Strategy Name - Z to A",
]


def _hash_filter_expression(filter_expr: pl.Expr) -> str:
    """Create a stable hash for filter expression."""
    # Convert expression to string representation for hashing
    filter_str = str(filter_expr)
    return hashlib.md5(filter_str.encode()).hexdigest()


@st.cache_data(max_entries=50)
def filter_and_sort_strategies(
    strats: pl.DataFrame, _filter_expr: pl.Expr, filter_hash: str
) -> pl.DataFrame:
    """Filter and sort the strategy table DataFrame.

    Cached using filter_hash as part of the cache key to avoid re-filtering
    when filters haven't changed.

    Args:
        strats: Strategy-level DataFrame (already collected, not LazyFrame)
        _filter_expr: Polars filter expression from sidebar (prefixed with _ to exclude from cache key)
        filter_hash: Hash of the filter expression for cache key (computed in app.py)
    """
    # Default sort prioritizes Investment Committee recommendations
    return strats.filter(_filter_expr).sort(
        by=["ic_recommend", "equity_allo", "strategy"],
        descending=[True, True, False],
        nulls_last=True,
    )


# Initialize session state explicitly at app start
initialize_session_state()

st.markdown("# Aspen Investing Menu")

strats: pl.DataFrame = load_strategy_list()
cleaned_data: pl.LazyFrame = load_cleaned_data()

st.caption(f"last updated: {datetime.now().strftime('%Y-%m-%d')}")

render_filters()
st.space(1)

card_order: str = get_or_init(CARD_ORDER_KEY, DEFAULT_CARD_ORDER)
selected_order: str = st.selectbox(
    "Order By:",
    options=CARD_ORDER_OPTIONS,
    index=CARD_ORDER_OPTIONS.index(card_order)
    if card_order in CARD_ORDER_OPTIONS
    else 0,
    key="card_order_by_select",
    on_change=lambda: st.session_state.update({CARDS_DISPLAYED_KEY: CARDS_PER_LOAD}),
)
st.session_state[CARD_ORDER_KEY] = selected_order

filter_expr: pl.Expr = build_filter_expression()
filter_hash: str = _hash_filter_expression(filter_expr)
filtered_strategies: pl.DataFrame = filter_and_sort_strategies(
    strats, filter_expr, filter_hash
)

reset_if_changed("last_filter_hash", filter_hash, CARDS_DISPLAYED_KEY, CARDS_PER_LOAD)
render_card_view(filtered_strategies)

strategy_name: str | None = st.session_state.get(SELECTED_STRATEGY_MODAL_KEY)
modal_type: str | None = st.session_state.get(SELECTED_MODAL_TYPE_KEY)
if strategy_name and modal_type:
    strategy_row: pl.DataFrame = filtered_strategies.filter(
        pl.col("strategy") == strategy_name
    )
    if strategy_row.height > 0:
        # Pass row dict directly - no intermediate objects needed
        row_dict = strategy_row.row(0, named=True)

        # Determine color based on modal type
        if modal_type == "cais":
            strategy_color: str = SUBTYPE_COLORS.get(
                "Alternative Strategies", "#F9A602"
            )
        else:
            strategy_color = get_subtype_color(row_dict.get("ss_subtype", ""))

        render_modal_by_type(
            modal_type, strategy_name, row_dict, strategy_color, cleaned_data
        )
    del st.session_state[SELECTED_STRATEGY_MODAL_KEY]
    del st.session_state[SELECTED_MODAL_TYPE_KEY]

render_footer()
