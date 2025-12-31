"""Dataframe display component."""

import polars as pl
import streamlit as st

SERIES_COLORS = {
    "Multifactor": "pink",
    "Market": "violet",
    "Income": "green",
    "Equity": "blue",
    "Fixed Income": "blue",
    "Cash": "gray",
    "Alternative": "orange",
    "Special Situation": "yellow",
    "Blended": "gray",
}


def filter_and_sort_strategies(strats: pl.LazyFrame, filters: dict) -> pl.DataFrame:
    """Filter and sort strategies based on filter criteria."""
    from components.filters import build_filter_expression

    filter_expr = build_filter_expression(filters=filters)
    return (
        strats.filter(filter_expr)
        .sort(
            by=["Recommended", "Strategy"],
            descending=[True, True],
            nulls_last=True,
        )
        .with_columns(
            # Convert Type to Series list format for MultiselectColumn with colors
            pl.when(pl.col("Type").is_not_null())
            .then(pl.concat_list([pl.col("Type")]))
            .otherwise(pl.lit([]).cast(pl.List(pl.Utf8)))
            .alias("Series"),
        )
        .collect()
    )


def render_dataframe(filtered_strategies: pl.DataFrame) -> str | None:
    """Render the strategies dataframe and return selected strategy name."""
    selected_rows = st.dataframe(
        filtered_strategies.select(
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
                options=list(SERIES_COLORS.keys()),
                color=list(SERIES_COLORS.values()),
            ),
            "Tax-Managed": st.column_config.CheckboxColumn("Tax-Managed"),
        },
    )

    if selected_rows.selection.rows:
        return filtered_strategies["Strategy"][selected_rows.selection.rows[0]]
    return None


def render_dataframe_section(strats: pl.LazyFrame, filters: dict) -> str | None:
    """Render the complete dataframe section including filtering, formatting, and display."""
    filtered_strategies = filter_and_sort_strategies(strats=strats, filters=filters)
    st.markdown(f"**{filtered_strategies.height} strategies returned**")
    return render_dataframe(filtered_strategies)
