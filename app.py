from typing import Any, Optional

import polars as pl
import streamlit as st

from components import (
    render_card_view,
    render_page_header,
    render_sidebar,
    render_strategy_modal,
)
from components.constants import (
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    SELECTED_STRATEGY_MODAL_KEY,
)
from components.dataframe import filter_and_sort_strategies, _hash_filters
from utils.core.data import get_strategy_table, load_cleaned_data

render_page_header()

# Full dataset only needed when viewing allocation details (product-level data)
# Strategy table is pre-aggregated for performance in card/table views
cleaned_data: pl.LazyFrame = load_cleaned_data()
strategy_table: pl.DataFrame = get_strategy_table(cleaned_data)

filters: dict[str, Any] = render_sidebar(strategy_table)
# Compute filter hash for caching
filter_hash = _hash_filters(filters)
filtered_strategies: pl.DataFrame = filter_and_sort_strategies(strategy_table, filters, filter_hash)

# Reset pagination when filters change to avoid showing stale results
# Hash comparison prevents unnecessary resets on unrelated state changes
filter_hash = _hash_filters(filters)
if "last_filter_hash" not in st.session_state:
    st.session_state["last_filter_hash"] = filter_hash
elif st.session_state["last_filter_hash"] != filter_hash:
    st.session_state["last_filter_hash"] = filter_hash
    st.session_state[CARDS_DISPLAYED_KEY] = CARDS_PER_LOAD

selected_strategy, strategy_data = render_card_view(filtered_strategies)

# Modal state persists across reruns via @st.dialog decorator
# Clearing trigger prevents reopening when other interactions cause reruns
if SELECTED_STRATEGY_MODAL_KEY in st.session_state:
    strategy_name: str = st.session_state[SELECTED_STRATEGY_MODAL_KEY]
    strategy_row: pl.DataFrame = filtered_strategies.filter(pl.col("Strategy") == strategy_name)
    if strategy_row.height > 0:
        strategy_data_dict: dict[str, Any] = strategy_row.row(0, named=True)
        render_strategy_modal(strategy_name, strategy_data_dict, filters, cleaned_data)
    del st.session_state[SELECTED_STRATEGY_MODAL_KEY]
