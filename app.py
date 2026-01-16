from typing import Any, Optional

import polars as pl
import streamlit as st

from components import (
    render_card_view,
    render_dataframe_section,
    render_page_header,
    render_sidebar,
    render_strategy_modal,
    render_tabs,
)
from components.constants import (
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    DEFAULT_VIEW_MODE,
    SELECTED_STRATEGY_MODAL_KEY,
    VIEW_MODE_KEY,
)
from components.dataframe import filter_and_sort_strategies
from utils.core.data import get_strategy_table, load_cleaned_data

render_page_header()

# Full dataset only needed when viewing allocation details (product-level data)
# Strategy table is pre-aggregated for performance in card/table views
cleaned_data: pl.LazyFrame = load_cleaned_data()
strategy_table: pl.DataFrame = get_strategy_table(cleaned_data)

filters: dict[str, Any] = render_sidebar(strategy_table)
filtered_strategies: pl.DataFrame = filter_and_sort_strategies(strategy_table, filters)

# Reset pagination when filters change to avoid showing stale results
# Hash comparison prevents unnecessary resets on unrelated state changes
filter_hash = hash(tuple(sorted((k, str(v)) for k, v in filters.items())))
if "last_filter_hash" not in st.session_state:
    st.session_state["last_filter_hash"] = filter_hash
elif st.session_state["last_filter_hash"] != filter_hash:
    st.session_state["last_filter_hash"] = filter_hash
    st.session_state[CARDS_DISPLAYED_KEY] = CARDS_PER_LOAD

if VIEW_MODE_KEY not in st.session_state:
    st.session_state[VIEW_MODE_KEY] = DEFAULT_VIEW_MODE

view_mode: str = st.session_state[VIEW_MODE_KEY]
if view_mode == "table":
    selected_strategy: Optional[str]
    strategy_data: Optional[dict[str, Any]]
    selected_strategy, strategy_data = render_dataframe_section(filtered_strategies)
    st.divider()
    render_tabs(selected_strategy, strategy_data, filters, cleaned_data)
else:
    selected_strategy, strategy_data = render_card_view(filtered_strategies)

# Modal state persists across reruns via @st.dialog decorator
# Clearing trigger prevents reopening when other interactions cause reruns
if view_mode == "card" and SELECTED_STRATEGY_MODAL_KEY in st.session_state:
    strategy_name: str = st.session_state[SELECTED_STRATEGY_MODAL_KEY]
    strategy_row: pl.DataFrame = filtered_strategies.filter(pl.col("Strategy") == strategy_name)
    if strategy_row.height > 0:
        strategy_data_dict: dict[str, Any] = strategy_row.row(0, named=True)
        render_strategy_modal(strategy_name, strategy_data_dict, filters, cleaned_data)
    del st.session_state[SELECTED_STRATEGY_MODAL_KEY]
