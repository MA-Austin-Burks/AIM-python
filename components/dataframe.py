"""Dataframe display component."""

from typing import Any

import polars as pl
import streamlit as st


def filter_and_sort_strategies(
    strats: pl.LazyFrame, filters: dict[str, Any]
) -> pl.DataFrame:
    """Filter and sort strategies based on filter criteria."""
    from components.filters import build_filter_expression

    filter_expr: pl.Expr = build_filter_expression(filters=filters)
    return (
        strats.filter(filter_expr)
        .sort(
            by=["Recommended", "Strategy"],
            descending=[True, True],
            nulls_last=True,
        )
        .with_columns(
            # Convert Strategy Subtype to Series list format for MultiselectColumn with colors
            pl.when(pl.col("Strategy Subtype").is_not_null())
            .then(pl.concat_list([pl.col("Strategy Subtype")]))
            .otherwise(pl.lit([]).cast(pl.List(pl.Utf8)))
            .alias("Series"),
        )
        .collect()
    )


def render_dataframe(df: pl.DataFrame, filtered_strategies: pl.DataFrame) -> str | None:
    """
    Render the strategies dataframe and return selected strategy name.
    """
    selected_rows = st.dataframe(
        df.select(
            [
                "Recommended",
                "Strategy",
                "Yield",
                "Expense Ratio",
                "Minimum",
                "Equity %",
                "Series",
                "Tax-Managed",
            ]
        ),
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Recommended": st.column_config.TextColumn("Recommended"),
            "Strategy": st.column_config.TextColumn("Strategy"),
            "Yield": st.column_config.NumberColumn("Yield", format="%.2f%%"),
            "Expense Ratio": st.column_config.NumberColumn("Expense Ratio"),
            "Minimum": st.column_config.NumberColumn("Minimum", format="dollar"),
            "Equity %": st.column_config.ProgressColumn("Equity %", format="%d/100"),
            "Series": st.column_config.MultiselectColumn(
                "Series",
                options=[
                    "Multifactor",
                    "Market",
                    "Income",
                    "Equity",
                    "Fixed Income",
                    "Cash",
                    "Alternative",
                    "Special Situation",
                    "Blended",
                ],
                color=[
                    "pink",  # Multifactor
                    "violet",  # Market
                    "green",  # Income
                    "blue",  # Equity
                    "blue",  # Fixed Income
                    "gray",  # Cash
                    "orange",  # Alternative
                    "yellow",  # Special Situation
                    "gray",  # Blended
                ],
            ),
            "Tax-Managed": st.column_config.CheckboxColumn("Tax-Managed"),
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
    strats: pl.LazyFrame, filters: dict[str, Any]
) -> str | None:
    """
    Render the complete dataframe section including filtering, formatting, and display.
    Returns the selected strategy name.
    """
    filtered_strategies: pl.DataFrame = filter_and_sort_strategies(
        strats=strats, filters=filters
    )

    st.markdown(f"**{filtered_strategies.height} strategies returned**")
    return render_dataframe(
        df=filtered_strategies, filtered_strategies=filtered_strategies
    )
