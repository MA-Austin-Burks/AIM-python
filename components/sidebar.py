"""Sidebar filters component for the Aspen Investing Menu app."""

from typing import Any

import polars as pl
import streamlit as st

# Subtype mappings based on strategy type
SUBTYPE_MAPPING = {
    "Risk-Based": ["Market", "Multifactor", "Income"],
    "Asset Class": ["Equity", "Fixed Income", "Cash", "Alternative"],
    "Other": ["Special Situation", "Blended"],
}

RISK_BASED_SUBTYPES = ["Market", "Multifactor", "Income"]

# Manager options for filter
MANAGER_OPTIONS = [
    "Mercer Advisors",
    "Blackrock",
    "Nuveen",
    "PIMCO",
    "AQR",
    "Quantinno",
    "SpiderRock",
    "Shelton",
]

# Common filter options
YES_NO_ALL_OPTIONS = ["All", "Yes", "No"]
STATUS_OPTIONS = ["Recommended", "Approved"]

# Tracking Error options
TRACKING_ERROR_OPTIONS = ["<1%", "<1.5%", "<2%", "<2.5%", "<3%"]

# Reference Benchmark options
REFERENCE_BENCHMARK_OPTIONS = [
    "S&P 500",
    "Russell 2000",
    "Bloomberg Aggregate",
    "MSCI World",
    "Barclays Aggregate",
    "Custom",
]

# Geography options
GEOGRAPHY_OPTIONS = [
    "US",
    "International",
    "Global",
    "Emerging Markets",
    "Developed Markets",
]

# Abbreviations content
ABBREVIATIONS_CONTENT = """
**Abbreviations**

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


def _get_available_subtypes(
    strats: pl.DataFrame, selected_types: list[str]
) -> list[str]:
    """
    Get available subtypes based on selected strategy types.
    """
    all_subtypes = strats["Strategy Subtype"].drop_nulls().unique().to_list()

    if not selected_types:
        return sorted(all_subtypes)

    available_subtypes = []
    for stype in selected_types:
        if stype in SUBTYPE_MAPPING:
            available_subtypes.extend(SUBTYPE_MAPPING[stype])

    # Remove duplicates, sort, and filter to only existing subtypes
    return sorted(set(s for s in available_subtypes if s in all_subtypes))


def _should_show_equity_slider(
    selected_types: list[str], selected_subtypes: list[str]
) -> bool:
    """
    Determine if equity allocation slider should be shown.
    """
    if not selected_types:
        return True

    if "Risk-Based" in selected_types:
        return True

    if selected_subtypes:
        return any(st in RISK_BASED_SUBTYPES for st in selected_subtypes)

    return False


def render_sidebar(strats: pl.DataFrame) -> dict[str, Any]:
    """
    Render sidebar filters and return filter values.
    """
    with st.sidebar:
        # Full width search at top
        st.header("Search")
        selected_strategy_search = st.text_input(
            "Search by Strategy Name",
            value="",
            placeholder="Type to filter strategies...",
        )
        st.divider()

        # Get strategy types list (doesn't depend on user input)
        strategy_types = strats["Strategy Type"].drop_nulls().unique().sort().to_list()
        default_type = "Risk-Based" if "Risk-Based" in strategy_types else None

        # Initialize for equity range (will be updated after Strategy Type/Subtype selection)
        selected_types = [default_type] if default_type else []
        available_subtypes = _get_available_subtypes(strats, selected_types)
        # Don't default Strategy Series - let it be empty so all subtypes show
        default_subtypes = []
        selected_subtypes = default_subtypes

        # Minimum and Equity Allocation Range on same row
        col_min, col_equity = st.columns(2)
        with col_min:
            min_strategy = st.number_input(
                "Minimum ($)",
                min_value=0,
                value=20000,
                step=10000,
            )
        with col_equity:
            # Conditional Equity Allocation Range - only show for Risk-Based strategies
            # Note: Uses current selected_types/subtypes, updates on rerun when Strategy Type changes
            if _should_show_equity_slider(selected_types, selected_subtypes):
                equity_range = st.slider(
                    "Equity Allocation Range",
                    min_value=0,
                    max_value=100,
                    value=(0, 100),
                    step=10,
                )
            else:
                equity_range = (0, 100)  # Default, no filtering

        # Tax-Managed and Has SMA Manager on same row
        col_tax, col_sma = st.columns(2)
        with col_tax:
            tax_managed_filter = st.segmented_control(
                "Tax-Managed (TM)",
                options=YES_NO_ALL_OPTIONS,
                selection_mode="single",
                default="All",
            )
        with col_sma:
            # Has SMA Manager filter (conditional on column existence)
            has_sma_manager_filter = st.segmented_control(
                "Has SMA Manager",
                options=YES_NO_ALL_OPTIONS,
                selection_mode="single",
                default="All",
                disabled="Has SMA Manager" not in strats.columns,
            )

        # Private Markets and Investment Committee Status on same row
        col_private, col_status = st.columns(2)
        with col_private:
            # Private Markets filter (disabled)
            private_markets_filter = st.segmented_control(
                "Private Markets",
                options=YES_NO_ALL_OPTIONS,
                selection_mode="single",
                default="All",
                disabled=True,
            )
        with col_status:
            selected_status = st.segmented_control(
                "Investment Committee Status",
                options=STATUS_OPTIONS,
                selection_mode="multi",
                default=STATUS_OPTIONS,
            )
        show_recommended = "Recommended" in selected_status
        show_approved = "Approved" in selected_status

        # Strategy Type and Strategy Series on same row
        col_type, col_series = st.columns(2)
        with col_type:
            # Strategy Type as Pills (single selection only)
            selected_type = st.pills(
                "Strategy Type",
                options=strategy_types,
                selection_mode="single",
                default=default_type,
            )
            selected_types = [selected_type] if selected_type else []
        with col_series:
            # Strategy Series as Pills (filtered based on Strategy Type selection)
            available_subtypes = _get_available_subtypes(strats, selected_types)
            # Don't default Strategy Series - let it be empty so all subtypes show
            default_subtypes = []
            selected_subtypes = st.pills(
                "Strategy Series",
                options=available_subtypes,
                selection_mode="multi",
                default=default_subtypes,
            )

        # Manager and Geography on same row
        col_manager, col_geography = st.columns(2)
        with col_manager:
            selected_managers = st.pills(
                "Manager",
                options=MANAGER_OPTIONS,
                selection_mode="multi",
                default=[],
                disabled="Manager" not in strats.columns,
            )
        with col_geography:
            # Geography (disabled)
            selected_geography = st.pills(
                "Geography",
                options=GEOGRAPHY_OPTIONS,
                selection_mode="multi",
                default=[],
                disabled=True,
            )

        # Tracking Error and Reference Benchmark on same row
        col_tracking, col_benchmark = st.columns(2)
        with col_tracking:
            # Tracking Error (disabled)
            tracking_error = st.selectbox(
                "Tracking Error",
                options=TRACKING_ERROR_OPTIONS,
                index=0,
                disabled=True,
            )
        with col_benchmark:
            # Reference Benchmark (disabled)
            reference_benchmark = st.selectbox(
                "Reference Benchmark",
                options=REFERENCE_BENCHMARK_OPTIONS,
                index=0,
                disabled=True,
            )

        # Abbreviations info card at bottom
        st.divider()
        abbreviations_html = """
        <div style="background-color: #E8E8F0; color: #50439B; border: 2px solid #50439B; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
            <strong style="color: #50439B;">Abbreviations</strong>
            <ul style="margin-top: 0.5rem; margin-bottom: 0; padding-left: 1.5rem; color: #50439B;">
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
        "tracking_error": None,  # Disabled filter
        "reference_benchmark": None,  # Disabled filter
        "selected_geography": selected_geography,
    }
