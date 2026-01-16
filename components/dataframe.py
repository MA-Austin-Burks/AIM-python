from typing import Any, Optional
import hashlib

import polars as pl
import streamlit as st

from styles.branding import SERIES_COLORS
from components.filters import build_filter_expression


def _hash_filters(filters: dict[str, Any]) -> str:
    """Create a stable hash for filter dictionary."""
    # Sort filters for consistent hashing
    sorted_filters = tuple(sorted((k, str(v)) for k, v in filters.items()))
    filter_str = str(sorted_filters)
    return hashlib.md5(filter_str.encode()).hexdigest()


@st.cache_data
def filter_and_sort_strategies(strats: pl.DataFrame, filters: dict[str, Any], filter_hash: str) -> pl.DataFrame:
    """Filter and sort the strategy table DataFrame.
    
    Cached using filter_hash as part of the cache key to avoid re-filtering
    when filters haven't changed.
    
    Args:
        strats: Strategy-level DataFrame (already collected, not LazyFrame)
        filters: Filter dictionary from sidebar
        filter_hash: Hash of the filters for cache key (computed in app.py)
    """
    filter_expr: pl.Expr = build_filter_expression(filters)
    # Default sort prioritizes Investment Committee recommendations
    return (
        strats.filter(filter_expr)
        .sort(
            by=["Recommended", "Equity %", "Strategy"],
            descending=[True, True, True],
            nulls_last=True,
        )
    )


def render_dataframe_section(filtered_strategies: pl.DataFrame) -> tuple[Optional[str], Optional[dict[str, Any]]]:
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
