"""Dataframe display component."""

from typing import Any

import polars as pl
import streamlit as st

from components.expressions import (
    fmt_cur,
    fmt_dec,
    fmt_equity_pct,
    fmt_pct,
    fmt_tax_managed,
)

DISPLAY_COLUMNS: list[str] = [
    "Recommended",
    "Strategy",
    "Yield",
    "Expense Ratio",
    "Minimum",
    "Equity %",
    "Series",
    "Tax-Managed",
    "IC Status",
]


def format_display_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    """Format dataframe columns for display."""
    return df.with_columns(
        fmt_pct(col="Yield"),
        fmt_dec(col="Expense Ratio"),
        fmt_cur(col="Minimum"),
        fmt_equity_pct(col="Equity %"),
        pl.col(name="Strategy Subtype").alias(name="Series"),
        fmt_tax_managed(col="Tax Managed"),
        pl.col(name="IC Status"),
    )


def render_dataframe(df: pl.DataFrame, filtered_strategies: pl.DataFrame) -> str | None:
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
            "Recommended": "",
            "Strategy": st.column_config.TextColumn("Strategy", width=325),
            "Yield": st.column_config.TextColumn("Yield", width=125),
            "Expense Ratio": st.column_config.TextColumn("Expense Ratio", width=125),
            "Minimum": st.column_config.TextColumn("Minimum", width=125),
            "Equity %": st.column_config.TextColumn("Equity %", width=125),
            "Series": st.column_config.TextColumn("Series", width=125),
            "Tax-Managed": st.column_config.TextColumn("Tax-Managed", width=125),
            "IC Status": st.column_config.TextColumn("IC Status", width=150),
        },
    )

    return (
        filtered_strategies.select("Strategy").row(
            index=selected_rows.selection.rows[0], named=True
        )["Strategy"]
        if selected_rows.selection.rows
        else None
    )


def render_dataframe_section(
    strats: pl.DataFrame, filters: dict[str, Any]
) -> str | None:
    """
    Render the complete dataframe section including filtering, formatting, and display.
    Returns the selected strategy name.
    """
    from components.utils import filter_and_sort_strategies

    filtered_strategies: pl.DataFrame = filter_and_sort_strategies(
        strats=strats, filters=filters
    )

    st.markdown(f"**{filtered_strategies.height} strategies returned**")
    display_df: pl.DataFrame = format_display_dataframe(filtered_strategies)
    return render_dataframe(df=display_df, filtered_strategies=filtered_strategies)
