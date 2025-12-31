"""Sidebar filters component for the Aspen Investing Menu app."""

from typing import Any

import polars as pl
import streamlit as st

SUBTYPE_MAPPING: dict[str, list[str]] = {
    "Risk-Based": ["Market", "Multifactor", "Income"],
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
            st.selectbox(
                "Tracking Error",
                options=TRACKING_ERROR_OPTIONS,
                index=0,
                disabled=True,
            )
        with col_benchmark:
            st.selectbox(
                "Reference Benchmark",
                options=REFERENCE_BENCHMARK_OPTIONS,
                index=0,
                disabled=True,
            )

        st.divider()
        with st.container(border=True):
            st.markdown("**Abbreviations**")
            st.markdown(
                """
                - **5YTRYSMA** - MA 5 Year Treasury Ladder (SMA)
                - **B5YCRP** - BlackRock Corporate 1-5 Year
                - **MA** - Managed Account
                - **MUSLGMKTLM** - MA Market US Large (SMA Low Min)
                - **N7YMUN** - Nuveen Municipal 1-7 Year
                - **QP** - Quantitative Portfolio
                - **QUSALMKT** - QP Market US All Cap
                - **QUSLGVMQ** - QP Factor US Large Cap VMQ
                - **SMA** - Separately Managed Account
                - **VMQ** - Value, Momentum, Quality
                """
            )

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
        "selected_geography": selected_geography,
    }
