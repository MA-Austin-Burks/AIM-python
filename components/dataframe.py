import polars as pl
import streamlit as st

from components.branding import SERIES_COLORS
from components.filters import build_filter_expression


def filter_and_sort_strategies(strats: pl.LazyFrame, filters: dict) -> pl.DataFrame:
    filter_expr = build_filter_expression(filters)
    return (
        strats.filter(filter_expr)
        .sort(
            by=["Recommended", "Equity %", "Strategy"],
            descending=[True, True, True],
            nulls_last=True,
        )
        .with_columns(
            pl.when(pl.col("Type").is_not_null())
            .then(pl.concat_list([pl.col("Type")]))
            .otherwise(pl.lit([]).cast(pl.List(pl.Utf8)))
            .alias("Series"),
        )
        .collect()
    )


def render_dataframe_section(strats: pl.LazyFrame, filters: dict) -> tuple[str | None, dict | None]:
    filtered_strategies: pl.DataFrame = filter_and_sort_strategies(strats, filters)
    st.markdown(f"**{filtered_strategies.height} strategies returned**")
    
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
        width="content",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Recommended": st.column_config.CheckboxColumn("Recommended", width=125),
            "Strategy": st.column_config.TextColumn("Strategy", width=400),
            "Yield": st.column_config.NumberColumn(
                "Yield", format="%.2f%%", width="small"
            ),
            "Expense Ratio": st.column_config.NumberColumn(
                "Expense Ratio", format="accounting", width="content"
            ),
            "Minimum": st.column_config.NumberColumn(
                "Minimum", format="dollar", width="small"
            ),
            "Equity %": st.column_config.ProgressColumn(
                "Equity %", format="%d/100", width="medium"
            ),
            "Series": st.column_config.MultiselectColumn(
                "Series",
                options=list(SERIES_COLORS.keys()),
                color=list(SERIES_COLORS.values()),
                width="content",
            ),
            "Tax-Managed": st.column_config.CheckboxColumn(
                "Tax-Managed", width="content"
            ),
        },
    )

    if selected_rows.selection.rows:
        row_idx = selected_rows.selection.rows[0]
        strategy_name = filtered_strategies["Strategy"][row_idx]
        strategy_row = filtered_strategies.row(row_idx, named=True)
        return strategy_name, strategy_row
    return None, None
