"""Utility functions for data loading."""

from typing import Any

import polars as pl
import streamlit as st


@st.cache_data(ttl=3600)
def load_strats(path: str = "data/strategies.csv") -> pl.DataFrame:
    """
    Load strategies data from CSV file.
    """
    return pl.read_csv(path, null_values=["NA"], truncate_ragged_lines=True)


def filter_and_sort_strategies(
    strategies_df: pl.DataFrame, filters: dict[str, Any]
) -> pl.DataFrame:
    """Filter and sort strategies based on filter criteria."""
    from components.filters import build_filter_expression

    filter_expr = build_filter_expression(filters, strats=strategies_df)
    return strategies_df.filter(filter_expr).sort(
        ["Recommended", "Equity %"], descending=[True, True], nulls_last=True
    )
