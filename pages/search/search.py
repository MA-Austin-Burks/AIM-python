import hashlib
from datetime import datetime

import polars as pl
import streamlit as st

from utils.data import load_strategy_list, load_cleaned_data
from utils.models import StrategySummary
from utils.branding import get_subtype_color
from utils.session_state import get_or_init, initialize_session_state, reset_if_changed
from utils.column_names import RECOMMENDED, EQUITY_PCT, STRATEGY
from components import (
    render_card_view,
    build_filter_expression,
    render_filters,
    render_footer,
    render_strategy_modal,
)
from components.cards import (
    CARD_ORDER_KEY,
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    DEFAULT_CARD_ORDER,
    SELECTED_STRATEGY_MODAL_KEY,
)

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


@st.cache_data
def filter_and_sort_strategies(strats: pl.DataFrame, _filter_expr: pl.Expr, filter_hash: str) -> pl.DataFrame:
    """Filter and sort the strategy table DataFrame.
    
    Cached using filter_hash as part of the cache key to avoid re-filtering
    when filters haven't changed.
    
    Args:
        strats: Strategy-level DataFrame (already collected, not LazyFrame)
        _filter_expr: Polars filter expression from sidebar (prefixed with _ to exclude from cache key)
        filter_hash: Hash of the filter expression for cache key (computed in app.py)
    """
    # Default sort prioritizes Investment Committee recommendations
    return (
        strats.filter(_filter_expr)
        .sort(
            by=[RECOMMENDED, EQUITY_PCT, STRATEGY],
            descending=[True, True, True],
            nulls_last=True,
        )
    )


# Initialize session state explicitly at app start
initialize_session_state()

st.markdown("# Aspen Investing Menu (Development Version)")

strats: pl.DataFrame = load_strategy_list()
cleaned_data: pl.LazyFrame = load_cleaned_data()

st.caption(f"last updated: {datetime.now().strftime('%Y-%m-%d')}")

render_filters()
st.space(1)

card_order: str = get_or_init(CARD_ORDER_KEY, DEFAULT_CARD_ORDER)
selected_order: str = st.selectbox(
    "Order By:",
    options=CARD_ORDER_OPTIONS,
    index=CARD_ORDER_OPTIONS.index(card_order) if card_order in CARD_ORDER_OPTIONS else 0,
    key="card_order_by_select",
    on_change=lambda: st.session_state.update({CARDS_DISPLAYED_KEY: CARDS_PER_LOAD}),
)
st.session_state[CARD_ORDER_KEY] = selected_order

filter_expr: pl.Expr = build_filter_expression()
filter_hash: str = _hash_filter_expression(filter_expr)
filtered_strategies: pl.DataFrame = filter_and_sort_strategies(strats, filter_expr, filter_hash)

reset_if_changed("last_filter_hash", filter_hash, CARDS_DISPLAYED_KEY, CARDS_PER_LOAD)
render_card_view(filtered_strategies)

strategy_name: str | None = st.session_state.get(SELECTED_STRATEGY_MODAL_KEY)
if strategy_name:
    strategy_row: pl.DataFrame = filtered_strategies.filter(pl.col(STRATEGY) == strategy_name)
    if strategy_row.height > 0:
        strategy_data = StrategySummary.from_row(strategy_row.row(0, named=True))
        strategy_color: str = get_subtype_color(strategy_data.type)
        render_strategy_modal(strategy_name, strategy_data, strategy_color, cleaned_data)
    del st.session_state[SELECTED_STRATEGY_MODAL_KEY]

render_footer()
