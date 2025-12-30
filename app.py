from datetime import datetime

import polars as pl
import streamlit as st

from dataframe import render_dataframe
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

# Load and filter data
strategies_df = load_strats()
filters = render_sidebar_filters(strategies_df)
filter_expr = build_filter_expression(filters, strategies_df)
filtered_strategies = strategies_df.filter(filter_expr).sort(
    ["Recommended", "Equity %"], descending=[True, True], nulls_last=True
)

st.markdown(f"**{len(filtered_strategies)} strategies returned**")

# Format and display dataframe
display_df = filtered_strategies.with_columns(
    fmt_pct("Yield").alias("Yield"),
    fmt_dec("Expense Ratio").alias("Expense Ratio"),
    fmt_cur("Minimum").alias("Minimum"),
    pl.when(pl.col("Equity %").is_not_null())
    .then(pl.col("Equity %").round(2).cast(pl.String) + "%")
    .otherwise(pl.lit(""))
    .alias("Equity %"),
    pl.col("Strategy Subtype").alias("Subtype"),
    pl.when(pl.col("Tax Managed").is_not_null())
    .then(pl.col("Tax Managed").cast(pl.String).replace({"true": "Yes", "false": "No"}))
    .otherwise(pl.lit(""))
    .alias("Tax-Managed"),
    pl.col("IC Status").alias("Status"),
)
selected_strategy = render_dataframe(display_df, filtered_strategies)

# Display strategy details
st.divider()
render_tabs(selected_strategy)
render_footer()
