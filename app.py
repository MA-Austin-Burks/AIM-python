from typing import Any

import polars as pl
import streamlit as st

from components import (
    render_card_view,
    render_explanation_card,
    render_sidebar,
    render_strategy_modal,
)
from components.constants import (
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    EXPLANATION_CARD_UPDATE_DATE,
    SELECTED_STRATEGY_MODAL_KEY,
)
from components.dataframe import filter_and_sort_strategies, _hash_filter_expression
from utils.core.data import get_strategy_table, load_cleaned_data
from utils.core.formatting import get_strategy_color
from utils.core.session_state import reset_if_changed
from styles.branding import PRIMARY


st.set_page_config(
    page_title="Aspen Investing Menu",
    layout="wide",
    initial_sidebar_state=475,
    menu_items={
        "Report a Bug": "mailto:aburks@merceradvisors.com",
    },
)

cleaned_data: pl.LazyFrame = load_cleaned_data()
strats: pl.DataFrame = get_strategy_table(cleaned_data)

filter_expr: pl.Expr = render_sidebar()

st.markdown("## Aspen Investing Menu (AIM 2.0)")
st.caption(f"last updated: {EXPLANATION_CARD_UPDATE_DATE}")

render_explanation_card()

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
