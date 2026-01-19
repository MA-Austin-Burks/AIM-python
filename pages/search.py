import os
from typing import Any

import polars as pl
import streamlit as st

from components import (
    render_card_view,
    render_filters,
    render_filters_inline,
    render_strategy_modal,
)
from components.constants import (
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    EXPLANATION_CARD_UPDATE_DATE,
    SELECTED_STRATEGY_MODAL_KEY,
)
from components.dataframe import filter_and_sort_strategies, _hash_filter_expression
from utils.core.data import load_strategy_list, load_cleaned_data
from utils.core.formatting import get_strategy_color
from utils.core.session_state import reset_if_changed
from styles.branding import PRIMARY

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
if st.session_state.get("_clear_search_flag", False):
    st.session_state["strategy_search_input"] = ""
    st.session_state["_clear_search_flag"] = False

strategy_search_text = st.session_state.get("strategy_search_input", "")
search_active = bool(strategy_search_text and strategy_search_text.strip())

# Render filters inline in two rows
render_filters_inline(search_active)

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
        strategy_type: str | None = strategy_data_dict.get("Type") or strategy_data_dict.get("type")
        strategy_color: str = get_strategy_color(strategy_type) if strategy_type else PRIMARY["raspberry"]
        render_strategy_modal(strategy_name, strategy_data_dict, strategy_color, cleaned_data)
    del st.session_state[SELECTED_STRATEGY_MODAL_KEY]
