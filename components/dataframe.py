"""Dataframe display component."""

from typing import Any

import polars as pl
import streamlit as st

from components.expressions import fmt_cur, fmt_dec, fmt_equity_pct, fmt_pct, fmt_tax_managed

DISPLAY_COLUMNS = [
    "Recommended",
    "Strategy",
    "Yield",
    "Expense Ratio",
    "Minimum",
    "Equity %",
    "Series",
    "Tax-Managed",
    "Status",
]


def format_display_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    """Format dataframe columns for display."""
    return df.with_columns(
        fmt_pct("Yield").alias("Yield"),
        fmt_dec("Expense Ratio").alias("Expense Ratio"),
        fmt_cur("Minimum").alias("Minimum"),
        fmt_equity_pct("Equity %"),
        pl.col("Strategy Subtype").alias("Series"),
        fmt_tax_managed("Tax Managed"),
        pl.col("IC Status").alias("Status"),
    )


def render_dataframe(df, filtered_strategies):
    """
    Render the strategies dataframe and return selected strategy name.
    """
    selected_rows = st.dataframe(
        df.select(DISPLAY_COLUMNS),
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Recommended": "⭐",
            "Strategy": "Strategy",
            "Yield": "Yield",
            "Expense Ratio": "Expense Ratio",
            "Minimum": "Minimum",
            "Equity %": "Equity %",
            "Series": "Series",
            "Tax-Managed": "Tax-Managed",
            "Status": "Status",
        },
    )

    return (
        filtered_strategies.select("Strategy").row(
            selected_rows.selection.rows[0], named=True
        )["Strategy"]
        if selected_rows.selection.rows
        else None
    )


def render_dataframe_section(
    strategies_df: pl.DataFrame, filters: dict[str, Any]
) -> str | None:
    """
    Render the complete dataframe section including filtering, formatting, and display.
    Returns the selected strategy name.
    """
    from components.utils import filter_and_sort_strategies

    # Filter and sort strategies
    filtered_strategies = filter_and_sort_strategies(strategies_df, filters)

    # Display count
    st.markdown(f"**{len(filtered_strategies)} strategies returned**")

    # Format and display dataframe
    display_df = format_display_dataframe(filtered_strategies)
    return render_dataframe(df=display_df, filtered_strategies=filtered_strategies)
