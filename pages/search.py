import os
from typing import Any

import polars as pl
import streamlit as st

from components import (
    render_card_view,
    render_filters,
    render_filters_inline,
    render_footer,
    render_strategy_modal,
)
from components.cards import (
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    SELECTED_STRATEGY_MODAL_KEY,
)
from components.dataframe import filter_and_sort_strategies, _hash_filter_expression
from components.filters import render_search_bar
from utils.core.constants import (
    CARD_ORDER_KEY,
    CARD_ORDER_OPTIONS,
    DEFAULT_CARD_ORDER,
    EXPLANATION_CARD_UPDATE_DATE,
)
from utils.core.data import load_strategy_list, load_cleaned_data
from utils.styles.branding import get_strategy_color
from utils.core.session_state import get_or_init, initialize_session_state, reset_if_changed

# Initialize session state explicitly at app start
initialize_session_state()

# Load pre-generated strategy summary for cards/filtering (fast)
strats: pl.DataFrame = load_strategy_list()

# Load full dataset for modal tabs (only when needed)
cleaned_data: pl.LazyFrame = load_cleaned_data()

st.markdown("# Aspen Investing Menu")

# Build caption with local mode indicator if applicable
is_local_mode = os.getenv("USE_LOCAL_DATA", "").lower() in ("true", "1", "yes")
caption_text = f"last updated: {EXPLANATION_CARD_UPDATE_DATE}"
if is_local_mode:
    caption_text += " • local mode"
st.caption(caption_text)

# Check if we need to clear search (must be done before any widgets are created)
if st.session_state["_clear_search_flag"]:
    st.session_state["strategy_search_input"] = ""
    st.session_state["_clear_search_flag"] = False

# Render Strategy Name search bar (full row, first)
search_active, strategy_search = render_search_bar()

# Render filters inline in two rows
render_filters_inline(search_active)

# Small space between filters and order by
st.space(1)

# Render Order By (two columns, Order By in first, second empty)
card_order = get_or_init(CARD_ORDER_KEY, DEFAULT_CARD_ORDER)
col_order, col_empty = st.columns([1, 1])
with col_order:
    selected_order = st.selectbox(
        "Order By:",
        options=CARD_ORDER_OPTIONS,
        index=CARD_ORDER_OPTIONS.index(card_order) if card_order in CARD_ORDER_OPTIONS else 0,
        key="card_order_by_select",
        on_change=lambda: st.session_state.update({CARDS_DISPLAYED_KEY: CARDS_PER_LOAD}),
    )
    st.session_state[CARD_ORDER_KEY] = selected_order
with col_empty:
    # Empty column
    pass

# Get filter expression from session state
filter_expr: pl.Expr = render_filters(search_active)

filter_hash: str = _hash_filter_expression(filter_expr)
filtered_strategies: pl.DataFrame = filter_and_sort_strategies(strats, filter_expr, filter_hash)

reset_if_changed("last_filter_hash", filter_hash, CARDS_DISPLAYED_KEY, CARDS_PER_LOAD)

selected_strategy, strategy_data = render_card_view(filtered_strategies)

strategy_name = st.session_state.get(SELECTED_STRATEGY_MODAL_KEY)
if strategy_name:
    strategy_row: pl.DataFrame = filtered_strategies.filter(pl.col("Strategy") == strategy_name)
    if strategy_row.height > 0:
        strategy_data_dict: dict[str, Any] = strategy_row.row(0, named=True)
        # ETL should ensure "Type" field exists and is consistent
        strategy_type: str = strategy_data_dict["Type"]
        strategy_color: str = get_strategy_color(strategy_type)
        render_strategy_modal(strategy_name, strategy_data_dict, strategy_color, cleaned_data)
    del st.session_state[SELECTED_STRATEGY_MODAL_KEY]

# Footer
render_footer()
