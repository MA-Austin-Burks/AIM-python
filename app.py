from datetime import datetime

import streamlit as st

from expressions import fmt_cur, fmt_dec, fmt_pct
from filters import build_filter_expression
from footer import render_footer
from sidebar import render_sidebar_filters
from tabs import render_tabs
from utils import load_strats

# Page configuration
st.set_page_config(page_title="Aspen Investing Menu", layout="wide")
st.title("Aspen Investing Menu")
st.caption(f"Last updated: {datetime.today().strftime('%Y-%m-%d')}")
st.divider()

# Load pre-processed data
strategies_df = load_strats()

# Sidebar filters
filters = render_sidebar_filters(strategies_df)

# Build and apply filter expression
filter_expr = build_filter_expression(filters, strategies_df)
filtered_strategies = strategies_df.filter(filter_expr)

# Sort by Recommended descending, then by Equity % descending
filtered_strategies = filtered_strategies.sort(
    ["Recommended", "Equity %"], descending=[True, True], nulls_last=True
)

st.markdown(f"**{len(filtered_strategies)} strategies returned**")

display_df = filtered_strategies.with_columns(
    fmt_pct("yield").alias("Yield"),
    fmt_dec("Expense Ratio").alias("Expense Ratio"),
    fmt_cur("minimum").alias("minimum"),
    fmt_pct("Equity %").alias("Equity %"),
).select(
    [
        "Recommended",
        "strategy",
        "Yield",
        "Expense Ratio",
        "minimum",
        "Equity %",
        "Subtype",
        "Tax-Managed",
        "Status",
    ]
)

selected_rows = st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Recommended": "⭐",
        "strategy": "Strategy",
        "Yield": "Yield",
        "Expense Ratio": "Expense Ratio",
        "minimum": "Minimum",
        "Equity %": "Equity %",
        "Subtype": "Subtype",
        "Tax-Managed": "Tax-Managed",
        "Status": "Status",
    },
)


# Get selected strategy from current selection
selected_strategy = (
    filtered_strategies.select("strategy").row(
        selected_rows.selection.rows[0], named=True
    )["strategy"]
    if selected_rows.selection.rows
    else None
)

st.divider()
render_tabs(selected_strategy)
render_footer()
