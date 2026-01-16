import random
from datetime import datetime
from typing import Any, Optional

import plotly.graph_objects as go
import polars as pl
import streamlit as st

from styles.branding import (
    CHART_CONFIG,
    FONTS,
    PRIMARY,
)
from components.constants import GROUPING_OPTIONS




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
        _metric_with_date("3 YEAR RETURN", f"{random.uniform(10, 15):.2f}%")
    with c4:
        inception_date: str = strategy_data.get("Inception Date", "01/01/2010")
        _metric_with_date(
            "SINCE INCEPTION",
            f"{random.uniform(15, 19):.2f}%",
            help=inception_date,
        )
    with c5:
        _metric_with_date("3 YR STD DEV", f"{random.uniform(10, 15):.2f}%")
    st.divider()

    # Allocation chart provides visual breakdown by grouping option
    if cleaned_data is not None:
        from components.tabs.allocation import (
            get_grouped_allocations_for_chart,
        )
        
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
                st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
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
