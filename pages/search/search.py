import os

import polars as pl
import streamlit as st

from components import (
    render_card_view,
    build_filter_expression,
    render_filters,
    render_footer,
    render_strategy_modal,
)
from components.cards import (
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    SELECTED_STRATEGY_MODAL_KEY,
)
from components.dataframe import filter_and_sort_strategies, _hash_filter_expression
from utils.core.constants import (
    CARD_ORDER_KEY,
    CARD_ORDER_OPTIONS,
    DEFAULT_CARD_ORDER,
    EXPLANATION_CARD_UPDATE_DATE,
)
from utils.core.data import load_strategy_list, load_cleaned_data
from utils.core.models import StrategySummary
from utils.styles.branding import get_subtype_color
from utils.core.session_state import get_or_init, initialize_session_state, reset_if_changed
from utils.core.performance import track_step, track_process, get_performance_tracker

# Initialize session state explicitly at app start
initialize_session_state()

# Initialize performance tracker
get_performance_tracker()

# Load pre-generated strategy summary for cards/filtering (fast)
with track_step("Load Strategy List"):
    strats: pl.DataFrame = load_strategy_list()

# Load full dataset for modal tabs (only when needed)
with track_step("Load Cleaned Data"):
    cleaned_data: pl.LazyFrame = load_cleaned_data()

st.markdown("# Aspen Investing Menu (Development Version)")

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

# Render filters inline (search bar is now inside the filters expander)
with track_step("Render Filters"):
    render_filters()

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
with track_step("Build Filter Expression"):
    filter_expr: pl.Expr = build_filter_expression()
    filter_hash: str = _hash_filter_expression(filter_expr)

with track_step("Filter and Sort Strategies"):
    filtered_strategies: pl.DataFrame = filter_and_sort_strategies(strats, filter_expr, filter_hash)

reset_if_changed("last_filter_hash", filter_hash, CARDS_DISPLAYED_KEY, CARDS_PER_LOAD)

with track_step("Render Card View"):
    selected_strategy, strategy_data = render_card_view(filtered_strategies)

strategy_name = st.session_state.get(SELECTED_STRATEGY_MODAL_KEY)
if strategy_name:
    with track_step("Render Strategy Modal"):
        strategy_row: pl.DataFrame = filtered_strategies.filter(pl.col("Strategy") == strategy_name)
        if strategy_row.height > 0:
            strategy_data = StrategySummary.from_row(strategy_row.row(0, named=True))
            strategy_color: str = get_subtype_color(strategy_data.type)
            render_strategy_modal(strategy_name, strategy_data, strategy_color, cleaned_data)
    del st.session_state[SELECTED_STRATEGY_MODAL_KEY]

# Footer
render_footer()
