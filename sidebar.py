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


def _get_available_subtypes(
    strats: pl.DataFrame, selected_types: list[str]
) -> list[str]:
    """
    Get available subtypes based on selected strategy types.

    Args:
        strats: The strategies dataframe
        selected_types: List of selected strategy types

    Returns:
        List of available subtype names
    """
    all_subtypes = strats["strategy_subtype"].drop_nulls().unique().to_list()

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

    Args:
        selected_types: List of selected strategy types
        selected_subtypes: List of selected strategy subtypes

    Returns:
        True if slider should be shown, False otherwise
    """
    if not selected_types:
        return True

    if "Risk-Based" in selected_types:
        return True

    if selected_subtypes:
        return any(st in RISK_BASED_SUBTYPES for st in selected_subtypes)

    return False


def render_sidebar_filters(strats: pl.DataFrame) -> dict[str, Any]:
    """
    Render sidebar filters and return filter values.

    Args:
        strats: The strategies dataframe

    Returns:
        Dictionary containing filter values:
        - strategy_search: Strategy search text
        - selected_managers: List of selected managers
        - min_strategy: Minimum strategy value
        - tax_managed_filter: Tax-Managed filter ("All", "Yes", "No")
        - show_recommended: Boolean for Recommended status
        - show_approved: Boolean for Approved status
        - selected_types: List of selected strategy types
        - selected_subtypes: List of selected strategy subtypes
        - equity_range: Tuple of (min, max) equity allocation range
    """
    with st.sidebar:
        # Performance monitoring toggle
        if "enable_performance_monitoring" not in st.session_state:
            st.session_state.enable_performance_monitoring = False

        st.session_state.enable_performance_monitoring = st.checkbox(
            "⚡ Enable Performance Monitoring",
            value=st.session_state.enable_performance_monitoring,
            key="perf_monitor_toggle",
        )

        st.header("Search")
        st.header("")

        # Strategy Name search text input - filters already-filtered results
        selected_strategy_search = st.text_input(
            "Search by Strategy Name",
            value="",
            placeholder="Type to filter strategies...",
            key="strategy_search_input",
        )

        st.divider()

        min_strategy = st.number_input(
            "Strategy Minimum ($)",
            min_value=0,
            value=20000,
            step=10000,
            key="strategy_minimum",
        )

        tax_managed_options = ["All", "Yes", "No"]
        tax_managed_filter = st.segmented_control(
            "Tax-Managed (TM)",
            options=tax_managed_options,
            selection_mode="single",
            default="All",
            key="tax_managed_control",
        )

        # Has SMA Manager filter (conditional on column existence)
        has_sma_manager_options = ["All", "Yes", "No"]
        if "Has SMA Manager" in strats.columns:
            has_sma_manager_filter = st.segmented_control(
                "Has SMA Manager",
                options=has_sma_manager_options,
                selection_mode="single",
                default="All",
                key="has_sma_manager_control",
            )
        else:
            # Dummy filter for when column doesn't exist yet
            has_sma_manager_filter = st.segmented_control(
                "Has SMA Manager",
                options=has_sma_manager_options,
                selection_mode="single",
                default="All",
                key="has_sma_manager_control",
                disabled=True,
            )

        st.subheader("Investment Committee Status")
        status_options = ["Recommended", "Approved"]
        selected_status = st.segmented_control(
            "Select Status",
            options=status_options,
            selection_mode="multi",
            default=["Recommended", "Approved"],
            label_visibility="collapsed",
            key="status_control",
        )
        show_recommended = "Recommended" in selected_status
        show_approved = "Approved" in selected_status

        # Strategy Type as Pills
        st.subheader("Strategy Type")
        strategy_types = strats["strategy_type"].drop_nulls().unique().sort().to_list()
        # Default to Risk-Based selected
        default_types = ["Risk-Based"] if "Risk-Based" in strategy_types else []
        selected_types = st.pills(
            "Select Strategy Types",
            options=strategy_types,
            selection_mode="multi",
            default=default_types,
            label_visibility="collapsed",
            key="strategy_type_pills",
        )

        # Strategy Subtype as Pills (filtered based on Strategy Type selection)
        st.subheader("Strategy Subtype")
        available_subtypes = _get_available_subtypes(strats, selected_types)
        # Default to Multifactor selected if available
        default_subtypes = (
            ["Multifactor"] if "Multifactor" in available_subtypes else []
        )
        selected_subtypes = st.pills(
            "Select Strategy Subtypes",
            options=available_subtypes,
            selection_mode="multi",
            default=default_subtypes,
            label_visibility="collapsed",
            key="strategy_subtype_pills",
        )

        # Conditional Equity Allocation Range - only show for Risk-Based strategies
        if _should_show_equity_slider(selected_types, selected_subtypes):
            st.subheader("Equity Allocation Range")
            equity_range = st.slider(
                "Equity Allocation Range",
                min_value=0,
                max_value=100,
                value=(0, 100),
                step=10,
                label_visibility="collapsed",
                key="equity_slider",
            )
        else:
            equity_range = (0, 100)  # Default, no filtering

        # Manager as Pills
        st.subheader("Manager")
        selected_managers = st.pills(
            "Select Managers",
            options=MANAGER_OPTIONS,
            selection_mode="multi",
            default=[],
            label_visibility="collapsed",
            key="manager_pills",
        )

        # Performance monitoring panel (if enabled)
        if st.session_state.get("enable_performance_monitoring", False):
            from utils.performance import PerformanceMonitor, render_performance_panel

            monitor = PerformanceMonitor()
            render_performance_panel(monitor)

    return {
        "strategy_search": selected_strategy_search
        if selected_strategy_search
        else None,
        "selected_managers": selected_managers,
        "min_strategy": min_strategy,
        "tax_managed_filter": tax_managed_filter,
        "has_sma_manager_filter": has_sma_manager_filter,
        "show_recommended": show_recommended,
        "show_approved": show_approved,
        "selected_types": selected_types,
        "selected_subtypes": selected_subtypes,
        "equity_range": equity_range,
    }
