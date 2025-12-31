"""Sidebar filters component for the Aspen Investing Menu app."""

import polars as pl
import streamlit as st


@st.cache_data
def _get_strategy_types(_strats: pl.LazyFrame) -> list[str]:
    """Get unique strategy types."""
    return (
        _strats.select("Strategy Type")
        .drop_nulls()
        .unique()
        .collect()["Strategy Type"]
        .to_list()
    )


@st.cache_data
def _get_type_options(_strats: pl.LazyFrame) -> list[str]:
    """Get unique Type values."""
    return _strats.select("Type").drop_nulls().unique().collect()["Type"].to_list()


def render_sidebar(strats: pl.LazyFrame) -> dict:
    """Render sidebar filters and return filter values."""
    with st.sidebar:
        st.header("Search")
        selected_strategy_search: str = st.text_input(
            "Search by Strategy Name",
            value="",
            placeholder="Type to filter by strategy name...",
        )
        st.divider()

        recommended_only: bool = st.toggle(
            "Investment Committee Recommended Only",
            value=True,
            help="Show only recommended strategies when enabled",
        )
        show_recommended: bool = recommended_only
        show_approved: bool = (
            False  # Always False - toggle controls Recommended filter only
        )

        strategy_types: list[str] = _get_strategy_types(strats)
        default_type: str | None = (
            "Risk-Based" if "Risk-Based" in strategy_types else None
        )

        selected_types: list[str] = [default_type] if default_type else []
        type_options: list[str] = sorted(_get_type_options(strats))

        col_min, col_equity = st.columns(2)
        with col_min:
            min_strategy: int = st.number_input(
                "Account Value ($)",
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
                options=["All", "Yes", "No"],
                selection_mode="single",
                default="All",
            )
        with col_sma:
            has_sma_manager_filter: str = st.segmented_control(
                "Has SMA Manager",
                options=["All", "Yes", "No"],
                selection_mode="single",
                default="All",
                disabled="Has SMA Manager" not in strats.schema,
            )

        private_markets_filter: str = st.segmented_control(
            "Private Markets",
            options=["All", "Yes", "No"],
            selection_mode="single",
            default="All",
        )

        selected_type: str | None = st.pills(
            "Strategy Type",
            options=strategy_types,
            selection_mode="single",
            default=default_type,
        )
        selected_types: list[str] = [selected_type] if selected_type else []

        selected_subtypes: list[str] = st.pills(
            "Series",
            options=type_options,
            selection_mode="multi",
            default=["Multifactor Series"]
            if "Multifactor Series" in type_options
            else [],
        )

        selected_managers: list[str] = st.pills(
            "Manager",
            options=[
                "Mercer Advisors",
                "Blackrock",
                "Nuveen",
                "PIMCO",
                "AQR",
                "Quantinno",
                "SpiderRock",
                "Shelton",
            ],
            selection_mode="multi",
            default=[],
            disabled="Manager" not in strats.schema,
        )

        selected_geography: list[str] = st.pills(
            "Geography",
            options=[
                "US",
                "International",
                "Global",
                "Emerging Markets",
                "Developed Markets",
            ],
            selection_mode="multi",
            default=[],
            disabled=True,
        )

        col_tracking, col_benchmark = st.columns(2)
        with col_tracking:
            tracking_error: str | None = st.selectbox(
                "Tracking Error",
                options=["<1%", "<1.5%", "<2%", "<2.5%", "<3%"],
                index=0,
                disabled=True,
            )
        with col_benchmark:
            reference_benchmark: str | None = st.selectbox(
                "Reference Benchmark",
                options=[
                    "S&P 500",
                    "Russell 2000",
                    "Bloomberg Aggregate",
                    "MSCI World",
                    "Barclays Aggregate",
                    "Custom",
                ],
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
        "tracking_error": tracking_error,
        "reference_benchmark": reference_benchmark,
    }
