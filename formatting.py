"""Formatting utilities for display."""

import polars as pl
import streamlit as st

# Display columns configuration
DISPLAY_COLUMNS = [
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

# Column configuration for dataframe display
COLUMN_CONFIG = {
    "Recommended": st.column_config.TextColumn(
        "⭐", width=50
    ),  # Narrow width for star column (50px)
    "strategy": "Strategy",
    "Yield": "Yield",
    "Expense Ratio": "Expense Ratio",
    "minimum": "Minimum",
    "Equity %": "Equity %",
    "Subtype": "Subtype",
    "Tax-Managed": "Tax-Managed",
    "Status": "Status",
}


@st.cache_data
def format_display_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    """
    Format dataframe columns for display.

    Caches the formatted result to avoid re-formatting on every rerun.
    The cache key is based on the dataframe's content hash.

    Args:
        df: Filtered strategies dataframe

    Returns:
        Formatted dataframe with string-formatted columns (percentages and currency)
    """
    return df.select(DISPLAY_COLUMNS).with_columns(
        _format_percentage("Yield"),
        _format_percentage("Expense Ratio"),
        _format_currency("minimum"),
        _format_percentage("Equity %"),
    )


def _format_percentage(col_name: str) -> pl.Expr:
    """Format a percentage column."""
    return (
        pl.when(pl.col(col_name).is_not_null())
        .then((pl.col(col_name) * 100).round(2).cast(pl.String) + "%")
        .otherwise(pl.lit(""))
        .alias(col_name)
    )


def _format_currency(col_name: str) -> pl.Expr:
    """Format a currency column."""
    return (
        pl.when(pl.col(col_name).is_not_null())
        .then("$" + pl.col(col_name).cast(pl.Int64).cast(pl.String))
        .otherwise(pl.lit(""))
        .alias(col_name)
    )
