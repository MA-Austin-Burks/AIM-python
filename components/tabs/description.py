from datetime import datetime
from typing import Any, Optional

import plotly.graph_objects as go
import polars as pl
import streamlit as st

from styles.branding import (
    CHART_CONFIG,
    FONTS,
    PRIMARY,
    SECONDARY,
    TERTIARY,
)
from components.constants import GROUPING_OPTIONS
from utils.core.data import hash_lazyframe


CATEGORY_COLORS: dict[str, str] = {
    "Equity": PRIMARY["raspberry"],
    "Bonds": TERTIARY["azure"],
    "Alternative": SECONDARY["iris"],
    "Cash": TERTIARY["spring"],
    "Other": PRIMARY["charcoal"],
    "Fixed Income": TERTIARY["azure"],
}


def _get_color_for_group(group_name: str, grouping_option: str) -> str:
    """Get color for a group based on grouping option."""
    if grouping_option == "Asset Category":
        return CATEGORY_COLORS.get(group_name, PRIMARY["charcoal"])
    
    # Hash-based assignment ensures same group name always gets same color
    # Important for consistency when switching between grouping options
    import hashlib
    hash_val = int(hashlib.md5(group_name.encode()).hexdigest()[:6], 16)
    colors = [
        PRIMARY["raspberry"],
        TERTIARY["azure"],
        SECONDARY["iris"],
        TERTIARY["spring"],
        PRIMARY["charcoal"],
        TERTIARY["gold"],
    ]
    return colors[hash_val % len(colors)]


@st.cache_data(hash_funcs={pl.LazyFrame: hash_lazyframe})
def get_grouped_allocations_for_chart(
    cleaned_data: pl.LazyFrame,
    strategy_name: str,
    grouping_option: str,
    total_assets: float,
) -> list[dict[str, Any]]:
    """Get grouped allocation data for pie chart only."""
    strategy_data = cleaned_data.filter(pl.col("strategy") == strategy_name)
    
    # Ensure grouping_option is valid, default to "Asset Type" if None
    if grouping_option is None:
        grouping_option = "Asset Type"
    
    group_column_map = {
        "Asset Category": "asset_category",
        "Asset Type": "asset_type",
        "Asset Class": "asset_class",
        "Product": "product",
    }
    
    if grouping_option not in group_column_map:
        grouping_option = "Asset Type"
    
    group_column = group_column_map[grouping_option]
    
    # Apply vectorized product name cleaning if grouping by Product
    strategy_data_processed = strategy_data
    if grouping_option == "Product":
        strategy_data_processed = strategy_data.with_columns([
            pl.col(group_column)
            .str.strip_chars()
            .str.replace(r"(?i)ETF\s*$", "", literal=False)
            .str.strip_chars()
            .alias(group_column)
        ])
    
    grouped = (
        strategy_data_processed
        .group_by(group_column)
        .agg([
            pl.sum("weight").alias("total_weight"),
        ])
        .filter(
            pl.col(group_column).is_not_null() &
            (pl.col(group_column) != "")
        )
        .sort("total_weight", descending=True)
        .collect()
    )
    
    data = []
    for row in grouped.to_dicts():
        group_name = str(row[group_column])
        # weight is stored as decimal (0-1), convert to percentage
        allocation_pct = float(row["total_weight"]) * 100
        color = _get_color_for_group(group_name, grouping_option)
        
        data.append({
            "name": group_name,
            "allocation": allocation_pct,
            "market_value": total_assets * allocation_pct / 100,
            "color": color,
        })
    
    # If more than 15 items, combine the rest into "Others"
    if len(data) > 15:
        top_15 = data[:15]
        others_allocation = sum(item["allocation"] for item in data[15:])
        others_market_value = sum(item["market_value"] for item in data[15:])
        
        # Use a neutral color for "Others"
        others_color = PRIMARY["charcoal"]
        
        top_15.append({
            "name": "Others",
            "allocation": others_allocation,
            "market_value": others_market_value,
            "color": others_color,
        })
        
        return top_15
    
    return data


def _metric_with_date(label: str, value: str, as_of: Optional[str] = None, help: Optional[str] = None) -> None:
    if as_of is None:
        as_of = datetime.now().strftime("%m-%d-%Y")
    st.metric(label, value, help=help)
    st.caption(f"as of {as_of}")


def render_description_tab(strategy_name: str, strategy_data: dict[str, Any], cleaned_data: Optional[pl.LazyFrame] = None) -> None:
    st.markdown(
        "Strategic, globally diversified multi-asset portfolios designed to seek long-term capital appreciation. Efficiently covers market exposures through a minimum number of holdings to reduce cost and trading."
    )

    st.divider()

    # Summary Statistics
    st.markdown("#### Summary Statistics")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        _metric_with_date(
            "WEIGHTED AVG EXP RATIO", f"{strategy_data['Expense Ratio']:.2}"
        )
    with c2:
        y: Optional[float] = strategy_data.get("Yield")
        _metric_with_date("12-MONTH YIELD", f"{y:.2f}%" if y else "X.XX")
    with c3:
        _metric_with_date("3 YEAR RETURN", "XX.XX%")
    with c4:
        inception_date: str = strategy_data.get("Inception Date", "01/01/2010")
        _metric_with_date(
            "SINCE INCEPTION",
            "XX.XX%",
            help=inception_date,
        )
    with c5:
        _metric_with_date("3 YR STD DEV", "XX.XX%")
    st.divider()

    # Allocation chart provides visual breakdown by grouping option
    if cleaned_data is not None:
        grouping_option: Optional[str] = st.segmented_control(
            "Group By",
            options=GROUPING_OPTIONS,
            default="Asset Class",
            key="description_allocation_grouping",
        )
        
        # Ensure grouping_option is never None (fallback to default)
        if grouping_option is None:
            grouping_option = "Asset Class"
        
        # Total assets used for market value calculation (display only)
        total_assets: float = 100000.0
        chart_data: list[dict[str, Any]] = get_grouped_allocations_for_chart(
            cleaned_data, strategy_name, grouping_option, total_assets
        )
        
        if chart_data:
            labels: list[str] = [item["name"] for item in chart_data]
            values: list[float] = [item["allocation"] for item in chart_data]
            colors: list[str] = [item["color"] for item in chart_data]

            fig: go.Figure = go.Figure(
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.5,
                    marker_colors=colors,
                    textinfo="none",
                    showlegend=False,
                    hovertemplate="<b>%{label}</b><br>%{percent:.1%}<extra></extra>",
                ),
                layout={
                    "font": {"family": FONTS["body"], "color": PRIMARY["charcoal"]},
                    "height": 500,
                    "margin": {"l": 40, "r": 20, "t": 0, "b": 40},
                },
            )
            
            # Layout chart and legend side by side
            col_chart, col_legend = st.columns([2, 1])
            with col_chart:
                st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)
                st.caption(f"as of {datetime.now().strftime('%m-%d-%Y')}")
            
            with col_legend:
                st.markdown("**Legend**")
                for item in chart_data:
                    st.markdown(
                        f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem;"><span style="width: 12px; height: 12px; background: {item["color"]}; border-radius: 50%; margin-right: 8px; display: inline-block;"></span><span><strong>{item["name"]}:</strong> {item["allocation"]:.2f}%</span></div>',
                        unsafe_allow_html=True,
                    )
    
    st.divider()

    # Factsheet
    st.download_button(
        label="📄 Download Fact Sheet",
        data="Fact sheet content goes here.",
        file_name=f"{strategy_name}_factsheet.pdf",
        mime="application/pdf",
        disabled=True,
    )
