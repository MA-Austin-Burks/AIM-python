from typing import Optional
import hashlib

import polars as pl
import streamlit as st

from utils.styles.branding import SUBTYPE_COLORS
from utils.core.models import StrategySummary
from utils.core.performance import track_performance


def _hash_filter_expression(filter_expr: pl.Expr) -> str:
    """Create a stable hash for filter expression."""
    # Convert expression to string representation for hashing
    filter_str = str(filter_expr)
    return hashlib.md5(filter_str.encode()).hexdigest()


@track_performance
@st.cache_data
def filter_and_sort_strategies(strats: pl.DataFrame, _filter_expr: pl.Expr, filter_hash: str) -> pl.DataFrame:
    """Filter and sort the strategy table DataFrame.
    
    Cached using filter_hash as part of the cache key to avoid re-filtering
    when filters haven't changed.
    
    Args:
        strats: Strategy-level DataFrame (already collected, not LazyFrame)
        _filter_expr: Polars filter expression from sidebar (prefixed with _ to exclude from cache key)
        filter_hash: Hash of the filter expression for cache key (computed in app.py)
    """
    # Default sort prioritizes Investment Committee recommendations
    return (
        strats.filter(_filter_expr)
        .sort(
            by=["Recommended", "Equity %", "Strategy"],
            descending=[True, True, True],
            nulls_last=True,
        )
    )


def render_dataframe_section(filtered_strategies: pl.DataFrame) -> tuple[Optional[str], Optional[StrategySummary]]:
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
                "Subtype",
                options=list(SUBTYPE_COLORS.keys()),
                color=list(SUBTYPE_COLORS.values()),
                width="content",
            ),
            "Tax-Managed": st.column_config.CheckboxColumn(
                "Tax-Managed", width="content"
            ),
        },
    )

    if selected_rows.selection.rows:
        row_idx = selected_rows.selection.rows[0]
        strategy_row = filtered_strategies.row(row_idx, named=True)
        strategy_summary = StrategySummary.from_row(strategy_row)
        return strategy_summary.strategy, strategy_summary
    return None, None
