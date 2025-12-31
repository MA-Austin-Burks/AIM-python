"""Sidebar filters component for the Aspen Investing Menu app."""

from typing import Any

import polars as pl
import streamlit as st

RISK_BASED_SUBTYPES: list[str] = ["Market", "Multifactor", "Income"]

SUBTYPE_MAPPING: dict[str, list[str]] = {
    "Risk-Based": RISK_BASED_SUBTYPES,
    "Asset Class": ["Equity", "Fixed Income", "Cash", "Alternative"],
    "Other": ["Special Situation", "Blended"],
}

MANAGER_OPTIONS: list[str] = [
    "Mercer Advisors",
    "Blackrock",
    "Nuveen",
    "PIMCO",
    "AQR",
    "Quantinno",
    "SpiderRock",
    "Shelton",
]

YES_NO_ALL_OPTIONS: list[str] = ["All", "Yes", "No"]
STATUS_OPTIONS: list[str] = ["Recommended", "Approved"]
TRACKING_ERROR_OPTIONS: list[str] = ["<1%", "<1.5%", "<2%", "<2.5%", "<3%"]
REFERENCE_BENCHMARK_OPTIONS: list[str] = [
    "S&P 500",
    "Russell 2000",
    "Bloomberg Aggregate",
    "MSCI World",
    "Barclays Aggregate",
    "Custom",
]

GEOGRAPHY_OPTIONS: list[str] = [
    "US",
    "International",
    "Global",
    "Emerging Markets",
    "Developed Markets",
]


def _get_available_subtypes(
    strats: pl.LazyFrame, selected_types: list[str]
) -> list[str]:
    """
    Get available subtypes based on selected strategy types.
    """
    all_subtypes: list[str] = (
        strats.select("Strategy Subtype")
        .drop_nulls()
        .unique()
        .collect()["Strategy Subtype"]
        .to_list()
    )

    if not selected_types:
        return sorted(all_subtypes)

    available_subtypes: list[str] = []
    for stype in selected_types:
        if stype in SUBTYPE_MAPPING:
            available_subtypes.extend(SUBTYPE_MAPPING[stype])

    return sorted(set[str](s for s in available_subtypes if s in all_subtypes))


def render_sidebar(strats: pl.LazyFrame) -> dict[str, Any]:
    """
    Render sidebar filters and return filter values.
    """
    with st.sidebar:
        st.header("Search")
        selected_strategy_search: str = st.text_input(
            "Search by Strategy Name",
            value="",
            placeholder="Type to filter by strategy name...",
        )
        st.divider()

        strategy_types: list[str] = (
            strats.select("Strategy Type")
            .drop_nulls()
            .unique()
            .collect()["Strategy Type"]
            .to_list()
        )
        default_type: str | None = (
            "Risk-Based" if "Risk-Based" in strategy_types else None
        )

        selected_types: list[str] = [default_type] if default_type else []
        available_subtypes: list[str] = _get_available_subtypes(strats, selected_types)
        default_subtypes: list[str] = []
        selected_subtypes: list[str] = default_subtypes

        col_min, col_equity = st.columns(2)
        with col_min:
            min_strategy: int = st.number_input(
                "Minimum ($)",
                min_value=0,
                value=20000,
                step=10000,
                key="min_strategy",
            )
        with col_equity:
            equity_range: tuple[int, int] = st.slider(
                "Equity Allocation Range",
                min_value=0,
                max_value=100,
                value=(0, 100),
                step=10,
                key="equity_range",
            )

        col_tax, col_sma = st.columns(2)
        with col_tax:
            tax_managed_filter: str = st.segmented_control(
                "Tax-Managed (TM)",
                options=YES_NO_ALL_OPTIONS,
                selection_mode="single",
                default="All",
            )
        with col_sma:
            has_sma_manager_filter: str = st.segmented_control(
                "Has SMA Manager",
                options=YES_NO_ALL_OPTIONS,
                selection_mode="single",
                default="All",
                disabled="Has SMA Manager" not in strats.schema,
            )

        col_private, col_status = st.columns(2)
        with col_private:
            private_markets_filter: str = st.segmented_control(
                "Private Markets",
                options=YES_NO_ALL_OPTIONS,
                selection_mode="single",
                default="All",
                disabled=True,
            )
        with col_status:
            selected_status: list[str] = st.segmented_control(
                "Investment Committee Status",
                options=STATUS_OPTIONS,
                selection_mode="multi",
                default=STATUS_OPTIONS,
            )
        show_recommended: bool = "Recommended" in selected_status
        show_approved: bool = "Approved" in selected_status

        col_type, col_series = st.columns(2)
        with col_type:
            selected_type: str | None = st.pills(
                "Strategy Type",
                options=strategy_types,
                selection_mode="single",
                default=default_type,
            )
            selected_types: list[str] = [selected_type] if selected_type else []
        with col_series:
            available_subtypes: list[str] = _get_available_subtypes(
                strats, selected_types
            )
            default_subtypes: list[str] = []
            selected_subtypes: list[str] = st.pills(
                "Strategy Series",
                options=available_subtypes,
                selection_mode="multi",
                default=default_subtypes,
            )

        col_manager, col_geography = st.columns(2)
        with col_manager:
            selected_managers: list[str] = st.pills(
                "Manager",
                options=MANAGER_OPTIONS,
                selection_mode="multi",
                default=[],
                disabled="Manager" not in strats.schema,
            )
        with col_geography:
            selected_geography: list[str] = st.pills(
                "Geography",
                options=GEOGRAPHY_OPTIONS,
                selection_mode="multi",
                default=[],
                disabled=True,
            )

        col_tracking, col_benchmark = st.columns(2)
        with col_tracking:
            tracking_error: str | None = st.selectbox(
                "Tracking Error",
                options=TRACKING_ERROR_OPTIONS,
                index=0,
                disabled=True,
            )
        with col_benchmark:
            reference_benchmark: str | None = st.selectbox(
                "Reference Benchmark",
                options=REFERENCE_BENCHMARK_OPTIONS,
                index=0,
                disabled=True,
            )

        st.divider()
        abbreviations_html: str = """
        <div style="background-color: #E8E8F0; color: #820361; border: 2px solid #bfbfbf; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
            <strong style="color: #820361;">Abbreviations</strong>
            <ul style="margin-top: 0.5rem; margin-bottom: 0; padding-left: 1.5rem; color: #820361;">
                <li><strong>5YTRYSMA</strong> - MA 5 Year Treasury Ladder (SMA)</li>
                <li><strong>B5YCRP</strong> - BlackRock Corporate 1-5 Year</li>
                <li><strong>MA</strong> - Managed Account</li>
                <li><strong>MUSLGMKTLM</strong> - MA Market US Large (SMA Low Min)</li>
                <li><strong>N7YMUN</strong> - Nuveen Municipal 1-7 Year</li>
                <li><strong>QP</strong> - Quantitative Portfolio</li>
                <li><strong>QUSALMKT</strong> - QP Market US All Cap</li>
                <li><strong>QUSLGVMQ</strong> - QP Factor US Large Cap VMQ</li>
                <li><strong>SMA</strong> - Separately Managed Account</li>
                <li><strong>VMQ</strong> - Value, Momentum, Quality</li>
            </ul>
        </div>
        """
        st.markdown(abbreviations_html, unsafe_allow_html=True)

    return {
        "strategy_search": selected_strategy_search or None,
        "selected_managers": selected_managers,
        "min_strategy": min_strategy,
        "tax_managed_filter": tax_managed_filter,
        "has_sma_manager_filter": has_sma_manager_filter,
        "private_markets_filter": private_markets_filter,
        "show_recommended": show_recommended,
        "show_approved": show_approved,
        "selected_types": selected_types,
        "selected_subtypes": selected_subtypes,
        "equity_range": equity_range,
        "tracking_error": None,
        "reference_benchmark": None,
        "selected_geography": selected_geography,
    }
