"""Tab components for displaying strategy details."""

import random
from datetime import datetime
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from components.branding import CHART_COLORS_PRIMARY, PRIMARY, get_chart_layout

BASE_TAB_NAMES: list[str] = [
    "Description",
    "Performance",
    "Allocations",
    "Minimum",
]


def _has_all_weather(strategy_name: str | None) -> bool:
    """Check if strategy name contains 'All Weather'."""
    if not strategy_name:
        return False
    return "All Weather" in strategy_name


def _has_blended(strategy_name: str | None) -> bool:
    """Check if strategy name contains 'Blended'."""
    if not strategy_name:
        return False
    return "Blended" in strategy_name


def render_tabs(
    selected_strategy: str | None = None,
    strategy_data: dict[str, Any] | None = None,
    filters: dict | None = None,
) -> None:
    """Render tabs for strategy details."""
    # Build tab names conditionally
    tab_names = BASE_TAB_NAMES.copy()

    # Add Private Markets tab only if strategy has "All Weather" in name
    if selected_strategy and _has_all_weather(selected_strategy):
        # Insert Private Markets before Minimum
        private_markets_index = tab_names.index("Minimum")
        tab_names.insert(private_markets_index, "Private Markets")

    # Add Blended tab only if strategy has "Blended" in name
    if selected_strategy and _has_blended(selected_strategy):
        # Insert Blended before Minimum
        blended_index = tab_names.index("Minimum")
        tab_names.insert(blended_index, "Blended")

    tabs = st.tabs(tab_names)

    if selected_strategy:
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                if tab_name == "Description":
                    _render_description_tab(selected_strategy, strategy_data, filters)
                else:
                    st.write(f"**{tab_name}** - {selected_strategy}")
    else:
        for tab, tab_name in zip(tabs, tab_names):
            with tab:
                st.info(
                    f"Please select a strategy from the table above to view its {tab_name.lower()}."
                )


def _render_description_tab(
    strategy_name: str,
    strategy_data: dict[str, Any] | None,
    filters: dict | None,
) -> None:
    """Render the Description tab with model details."""
    # Model name header
    st.markdown(
        f'<h1 style="color: {PRIMARY["raspberry"]}; margin-bottom: 0;">{strategy_name}</h1>',
        unsafe_allow_html=True,
    )

    # Calculate exposure breakdown
    equity_pct = strategy_data.get("Equity %", 0) if strategy_data else 0
    if equity_pct is None:
        equity_pct = 0
    equity_pct = float(equity_pct)

    fixed_income_pct = 100 - equity_pct
    alternative_pct = 0  # Default to 0, can be updated if data available

    # Check if Private Markets is True for alternative exposure
    if strategy_data and strategy_data.get("Private Markets"):
        # If private markets, allocate some percentage to alternatives
        alternative_pct = random.randint(5, 15)
        fixed_income_pct = max(0, fixed_income_pct - alternative_pct)

    # Exposure breakdown subtitle
    st.markdown(
        f'<h2 style="font-weight: bold; margin-top: 0.5rem; margin-bottom: 1rem;">'
        f"{int(equity_pct)}% Equity - {int(fixed_income_pct)}% Fixed Income"
        f"{f' - {int(alternative_pct)}% Alternative' if alternative_pct > 0 else ''}"
        f"</h2>",
        unsafe_allow_html=True,
    )

    # Description paragraph
    st.markdown(
        "Strategic, globally diversified multi-asset portfolios designed to seek long-term capital appreciation. "
        "Efficiently covers market exposures through a minimum number of holdings to reduce cost and trading."
    )

    st.markdown("---")

    # Model Characteristics
    characteristics = []
    if strategy_data:
        # Add characteristics based on strategy data
        if strategy_data.get("Strategy Type"):
            characteristics.append(strategy_data.get("Strategy Type", "").upper())
        if strategy_data.get("Type"):
            type_val = strategy_data.get("Type", "")
            if isinstance(type_val, list) and type_val:
                characteristics.extend([t.upper() for t in type_val])
            elif isinstance(type_val, str):
                characteristics.append(type_val.upper())
        if strategy_data.get("Tax-Managed"):
            characteristics.append("TAX-MANAGED")
        if strategy_data.get("Private Markets"):
            characteristics.append("PRIVATE MARKETS")

    # Add default characteristics if none found
    if not characteristics:
        characteristics = ["GROWTH", "ETF", "MUTUAL FUNDS", "STRATEGIC", "PASSIVE"]

    st.markdown("**Model Characteristics**")
    st.markdown(" | ".join(characteristics))

    st.markdown("---")

    # Summary Stats
    st.markdown("**Summary Statistics**")

    # Get current date for "as of" display
    as_of_date = datetime.now().strftime("%m/%d/%Y")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        expense_ratio = (
            strategy_data.get("Expense Ratio", 0.0004) if strategy_data else 0.0004
        )
        st.metric("WEIGHTED AVERAGE EXPENSE RATIO", f"{expense_ratio:.2%}")
        st.caption(f"as of {as_of_date}")

    with col2:
        st.metric("3 YEAR RETURN", "X.XX")
        st.caption(f"as of {as_of_date}")

    with col3:
        yield_val = strategy_data.get("Yield", 0) if strategy_data else 0
        if yield_val:
            st.metric("12-MONTH PORTFOLIO YIELD", f"{yield_val:.2f}%")
        else:
            st.metric("12-MONTH PORTFOLIO YIELD", "X.XX")
        st.caption(f"as of {as_of_date}")

    with col4:
        st.metric("INCEPTION", "X.XX")
        st.caption(f"as of {as_of_date}")

    with col5:
        st.metric("3 YEAR STANDARD DEVIATION", "X.XX")
        st.caption(f"as of {as_of_date}")

    st.markdown("---")

    # Allocation Chart
    st.markdown("**Asset Allocation**")

    # Generate random allocation data for the chart
    random.seed(hash(strategy_name) if strategy_name else 42)

    us_stocks = random.uniform(30, 40)
    non_us_stocks = random.uniform(20, 30)
    bonds = random.uniform(30, 45)
    short_term = random.uniform(2, 5)
    other = random.uniform(0, 1)

    # Normalize to 100%
    total = us_stocks + non_us_stocks + bonds + short_term + other
    us_stocks = (us_stocks / total) * 100
    non_us_stocks = (non_us_stocks / total) * 100
    bonds = (bonds / total) * 100
    short_term = (short_term / total) * 100
    other = (other / total) * 100

    # Create donut chart with brand colors
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[
                    "U.S. stocks",
                    "Non-U.S. stocks",
                    "Bonds",
                    "Short-term reserves",
                    "Other",
                ],
                values=[us_stocks, non_us_stocks, bonds, short_term, other],
                hole=0.5,
                marker_colors=CHART_COLORS_PRIMARY,
                textinfo="none",  # Hide text on chart, show in legend instead
                showlegend=False,  # We'll create custom legend
                hovertemplate="<b>%{label}</b><br>%{percent:.1%}<extra></extra>",
            )
        ]
    )

    fig.update_layout(**get_chart_layout(height=400))

    # Display chart and legend side by side
    chart_col, legend_col = st.columns([2, 1])

    with chart_col:
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with legend_col:
        # Create legend with brand colored dots
        legend_items = [
            ("U.S. stocks", us_stocks, CHART_COLORS_PRIMARY[0]),
            ("Non-U.S. stocks", non_us_stocks, CHART_COLORS_PRIMARY[1]),
            ("Bonds", bonds, CHART_COLORS_PRIMARY[2]),
            ("Short-term reserves", short_term, CHART_COLORS_PRIMARY[3]),
            ("Other", other, CHART_COLORS_PRIMARY[4]),
        ]

        for label, value, color in legend_items:
            st.markdown(
                f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem;">'
                f'<span style="display: inline-block; width: 12px; height: 12px; '
                f'background-color: {color}; border-radius: 50%; margin-right: 8px;"></span>'
                f"<span><strong>{label}:</strong> {value:.2f}%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.caption(f"as of {as_of_date}")

    st.markdown("---")

    # Factsheet download button
    _render_factsheet_button(strategy_name)


def _render_factsheet_button(strategy_name: str) -> None:
    """Render the Factsheet download button."""
    st.markdown(
        '<a href="#" download '
        'style="display: inline-flex; align-items: center; padding: 10px 20px; '
        "color: #333; text-decoration: none; border: 1px solid #ddd; border-radius: 5px; "
        "margin-top: 10px; font-family: 'IBM Plex Sans', sans-serif; font-weight: 500; "
        'transition: background-color 0.2s;">'
        "📄 Fact sheet</a>",
        unsafe_allow_html=True,
    )
