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
    strats: pl.DataFrame, filters: dict[str, Any]
) -> pl.DataFrame:
    """Filter and sort strategies based on filter criteria."""
    from components.filters import build_filter_expression

    filter_expr: pl.Expr = build_filter_expression(filters=filters, strats=strats)
    return strats.filter(filter_expr).sort(
        by=["Recommended", "Equity %"], descending=[True, True], nulls_last=True
    )
