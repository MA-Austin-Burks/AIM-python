from typing import Any

import polars as pl
import streamlit as st
from datetime import datetime

from components.constants import (
    ACCOUNT_VALUE_STEP,
    DEFAULT_EQUITY_RANGE,
    DEFAULT_MIN_ACCOUNT_VALUE,
    DEFAULT_RECOMMENDED_ONLY,
    DEFAULT_SERIES_SUBTYPES,
    DEFAULT_STRATEGY_TYPE,
    EQUITY_MAX_VALUE,
    EQUITY_MIN_VALUE,
    EQUITY_STEP,
    MIN_ACCOUNT_VALUE,
    SERIES_OPTIONS,
    STRATEGY_TYPES,
    STRATEGY_TYPE_TO_SERIES,
)

# Session state key for pending clear action
_PENDING_CLEAR_KEY = "_pending_clear_search"


def _clear_search() -> None:
    """Callback to clear the search input."""
    st.session_state["strategy_search_input"] = ""


def _schedule_clear_search() -> None:
    """Schedule a clear for the next rerun (used by shortcut button)."""
    st.session_state[_PENDING_CLEAR_KEY] = True


def render_sidebar(strats: pl.DataFrame) -> dict[str, Any]:
    """Render sidebar filters using the strategy table DataFrame.
    
    Steps:
    1. Handle search input and clear functionality
    2. Render search input and filters toggle
    3. Render filter controls (recommended, account value, equity range)
    4. Render boolean filters (tax-managed, SMA manager, private markets)
    5. Render type and series filters
    6. Render abbreviations section
    7. Render under development popover
    8. Return filter dictionary
    """
    # ============================================================================
    # STEP 1: Handle search input and clear functionality
    # ============================================================================
    schema: pl.Schema = strats.schema
    
    # Check if we need to clear search from a previous shortcut button press
    if st.session_state.get(_PENDING_CLEAR_KEY, False):
        st.session_state["strategy_search_input"] = ""
        st.session_state[_PENDING_CLEAR_KEY] = False

    with st.sidebar:
        # ============================================================================
        # STEP 2: Render search input and filters toggle
        # ============================================================================
        st.header("Search")
        
        col_search, col_clear = st.columns([9, 1])
        with col_search:
            strategy_search_text = st.text_input(
                "Strategy Name",
                value="",
                placeholder="Type to filter by strategy name...",
                key="strategy_search_input",
                label_visibility="collapsed",
            )
        with col_clear:
            st.button("✕", help="Clear search and enable filters", key="clear_search_btn", on_click=_clear_search)
        
        # Search mode disables filters to prevent confusion (search is OR, filters are AND)
        search_active = bool(strategy_search_text and strategy_search_text.strip())
        
        # Visual separator clarifies that search and filters are mutually exclusive modes
        st.markdown(
            """
            <div style="display: flex; align-items: center; margin: 1rem 0;">
                <div style="flex: 1; height: 1px; background-color: rgba(128, 128, 128, 0.3);"></div>
                <span style="padding: 0 0.75rem; color: rgba(128, 128, 128, 0.7); font-size: 1.1rem; font-weight: 500;">OR</span>
                <div style="flex: 1; height: 1px; background-color: rgba(128, 128, 128, 0.3);"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.space("small")
        if search_active:
            if st.button("Enable Filters", key="enable_filters_btn", type="primary", width="stretch"):
                _schedule_clear_search()
        
        # ============================================================================
        # STEP 3: Render filter controls (recommended, account value, equity range)
        # ============================================================================
        recommended_only = st.toggle(
            "Investment Committee Recommended Only",
            value=DEFAULT_RECOMMENDED_ONLY,
            help="Show only recommended strategies when enabled",
            disabled=search_active,
        )
        show_recommended = recommended_only
        show_approved = False

        strategy_types: list[str] = STRATEGY_TYPES
        default_type: str = DEFAULT_STRATEGY_TYPE

        selected_types: list[str] = [default_type] if default_type else []
        
        col_min, col_equity = st.columns(2)
        with col_min:
            min_strategy = st.number_input(
                "Account Value ($)",
                min_value=MIN_ACCOUNT_VALUE,
                value=DEFAULT_MIN_ACCOUNT_VALUE,
                step=ACCOUNT_VALUE_STEP,
                key="min_strategy",
                disabled=search_active,
            )
        with col_equity:
            equity_range = st.slider(
                "Equity Allocation Range",
                min_value=EQUITY_MIN_VALUE,
                max_value=EQUITY_MAX_VALUE,
                value=DEFAULT_EQUITY_RANGE,
                step=EQUITY_STEP,
                key="equity_range",
                disabled=search_active,
            )

        # ============================================================================
        # STEP 4: Render boolean filters (tax-managed, SMA manager, private markets)
        # ============================================================================
        col_tax, col_sma, col_private = st.columns(3)
        with col_tax:
            tax_managed_selection = st.pills(
                "Tax-Managed (TM)",
                options=["Yes", "No"],
                selection_mode="single",
                default=None,
                disabled=search_active,
                key="sidebar_tax_managed",
            )
        with col_sma:
            has_sma_manager_selection = st.pills(
                "Has SMA Manager",
                options=["Yes", "No"],
                selection_mode="single",
                default=None,
                disabled=search_active or "Has SMA Manager" not in schema,
                key="sidebar_sma_manager",
            )
        with col_private:
            private_markets_selection = st.pills(
                "Private Markets",
                options=["Yes", "No"],
                selection_mode="single",
                default=None,
                disabled=search_active,
                key="sidebar_private_markets",
            )

        # ============================================================================
        # STEP 5: Render type and series filters
        # ============================================================================
        selected_type = st.pills(
            "Strategy Type",
            options=strategy_types,
            selection_mode="single",
            default=default_type,
            disabled=search_active,
            key="sidebar_strategy_type",
        )
        selected_types = [selected_type] if selected_type else []

        # Track previous strategy type to detect changes
        previous_type_key = "_previous_strategy_type"
        previous_type = st.session_state.get(previous_type_key, default_type)
        
        # Dynamically filter series options based on selected strategy type
        if selected_type and selected_type in STRATEGY_TYPE_TO_SERIES:
            type_options: list[str] = STRATEGY_TYPE_TO_SERIES[selected_type]
        else:
            type_options: list[str] = SERIES_OPTIONS

        # Determine default selections based on strategy type
        if selected_type == "Risk-Based":
            default_selections = DEFAULT_SERIES_SUBTYPES  # ["Multifactor Series"]
        elif selected_type == "Asset-Class":
            default_selections = []
        elif selected_type == "Special Situation":
            default_selections = ["Special Situation Strategies"]
        else:
            default_selections = []

        # Handle strategy type changes by clearing invalid selections
        if selected_type != previous_type:
            # Strategy type changed - clear the session state so widget can initialize with new defaults
            if "sidebar_series" in st.session_state:
                del st.session_state["sidebar_series"]
            st.session_state[previous_type_key] = selected_type
            # Use the new defaults
            valid_selections = default_selections
        else:
            # Strategy type hasn't changed - get current selections and filter invalid ones
            current_selections = st.session_state.get("sidebar_series", default_selections)
            if isinstance(current_selections, list):
                # Filter to only include valid options for the current strategy type
                valid_selections = [s for s in current_selections if s in type_options]
                # If no valid selections remain, use defaults
                if not valid_selections:
                    valid_selections = default_selections
            else:
                valid_selections = default_selections
            st.session_state[previous_type_key] = selected_type

        selected_subtypes = st.pills(
            "Series",
            options=type_options,
            selection_mode="multi",
            default=valid_selections,
            disabled=search_active,
            key="sidebar_series",
        )

        # ============================================================================
        # STEP 6: Render abbreviations section
        # ============================================================================
        st.divider()
        with st.expander("**Abbreviations**"):
            st.caption(f"last updated: {datetime.now().strftime('%Y-%m-%d')}")
            st.markdown(
                """
                - **MUSALMKT** - MA Market US All (SMA)
                - **MUSLGMKT** - MA Market US Large (SMA)
                - **QUSALVMQ** - QP Factor US All Cap VMQ
                - **QUSLGVMQ** - QP Factor US Large Cap VMQ
                - **QUSLGDIV** - QP Market US Large Div Income
                - **QIDMVMQ** - QP Factor Int'l Dev ADR VMQ
                - **MUSLGMKTLM** - MA Market US Large (SMA Low Min)
                - **MUSLGMFTLM** - MA Multifct US Large (SMA Low Min)
                - **5YTRYSMA** - MA 5 Year Treasury Ladder (SMA)
                - **5YCRPETF** - MA 5 Year US Corporate Ladder (ETF)
                - **5YTRYETF** - MA 5 Year US Treasury Ladder (ETF)
                - **9YTRYETF** - MA 9 Year US Treasury Ladder (ETF)
                - **5YMUNETF** - MA 5 Year Municipal Ladder (ETF)
                - **B5YCRP** - BlackRock Corporate 1-5 Year
                - **B10YCRP** - BlackRock Corporate 1-10 Year
                - **N7YMUN** - Nuveen Municipal 1-7 Year
                - **N15YMUN** - Nuveen Municipal 1-15 Year
                """
            )
        
        # ============================================================================
        # STEP 7: Render under development expander
        # ============================================================================
        with st.expander("**Under Development**"):
            st.caption(f"last updated: {datetime.now().strftime('%Y-%m-%d')}")
            st.markdown("### **Risk-Based Strategies**")
            st.markdown("""
            - Market (ETF, Hedged Equity)
            """)
            st.markdown("### **Asset Class Strategies**")
            st.markdown("""
            - MA Market Global (SMA)
            - MA Market Non-US Developed Markets (SMA)
            - MA Market Non-US Emerging Markets (SMA)
            - MA Market US All Cap (SMA)
            - MA Market US Large Cap (SMA)
            - MA Market US Small Cap (SMA)
            - MA Multifactor Global (SMA)
            - MA Multifactor Non-US Developed Markets (SMA)
            - MA Multifactor Non-US Emerging Markets (SMA)
            - MA Multifactor US All Cap (SMA)
            - MA Multifactor US Large Cap (SMA)
            - MA Multifactor US Small Cap (SMA)
            - MA Income US Large Cap (SMA)
            - MA Income US Large Cap (SMA Low Min)
            - MA Income Non-US Developed Markets (SMA)
            - MA Absolute Return
            - MA Commodities
            """)
            st.markdown("### **Special Situation Strategies**")
            st.markdown("""
            - Ares Real Estate Exchange Program
            - Goldman Sachs Tax Aware Fixed Income
            - DFA Liability Driven Investing
            """)

    # ============================================================================
    # STEP 8: Return filter dictionary
    # ============================================================================
    tax_managed_filter = tax_managed_selection if tax_managed_selection else "All"
    has_sma_manager_filter = has_sma_manager_selection if has_sma_manager_selection else "All"
    private_markets_filter = private_markets_selection if private_markets_selection else "All"

    return {
        "strategy_search": strategy_search_text.strip() if strategy_search_text else None,
        "search_only_mode": search_active,
        "min_strategy": min_strategy,
        "tax_managed_filter": tax_managed_filter,
        "has_sma_manager_filter": has_sma_manager_filter,
        "private_markets_filter": private_markets_filter,
        "show_recommended": show_recommended,
        "show_approved": show_approved,
        "selected_types": selected_types,
        "selected_subtypes": selected_subtypes,
        "equity_range": equity_range,
    }
