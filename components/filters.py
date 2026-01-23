import polars as pl
import streamlit as st

from utils.column_names import (
    STRATEGY,
    RECOMMENDED,
    TAX_MANAGED,
    HAS_SMA_MANAGER,
    PRIVATE_MARKETS,
    MINIMUM,
    EQUITY_PCT,
    CATEGORY,
    TYPE,
)

# Type to subtype mapping
# Note: Keys must match ss_type values in the data ("Asset Class" not "Asset-Class")
TYPE_TO_SUBTYPE: dict[str, list[str]] = {
    "Risk-Based": [
        "Multifactor Series",
        "Market Series",
        "Income Series",
    ],
    "Asset Class": [
        "Equity Strategies",
        "Fixed Income Strategies",
        "Cash Strategies",
        "Alternative Strategies",
        "Special Situation Strategies",
    ],
}

def _clear_search_state() -> None:
    """Clear search state."""
    st.session_state["_clear_search_flag"] = True

def _clear_search_flag_if_needed() -> None:
    """Clear search flag if needed."""
    if st.session_state.get("_clear_search_flag", False):
        st.session_state["strategy_search_input"] = ""
        st.session_state["_clear_search_flag"] = False

def _reset_filter_state() -> None:
    """Reset filter state."""
    st.session_state["filter_ic"] = "Recommended"
    st.session_state["filter_tm"] = None
    st.session_state["filter_sma"] = None
    st.session_state["filter_pm"] = None
    st.session_state["filter_esg"] = None
    st.session_state["min_strategy"] = None
    st.session_state["equity_allocation_range"] = (0, 100)
    st.session_state["filter_type"] = []
    st.session_state["filter_subtype"] = []
    st.session_state["_previous_type"] = []

def _reset_all_state() -> None:
    """Reset all filter state."""
    _reset_filter_state()
    st.session_state["_clear_search_flag"] = True

def render_filters() -> None:
    """Render the filters UI."""
    _clear_search_flag_if_needed()
    
    with st.expander("Filters", expanded=True, icon=":material/feature_search:"):

        # Row 1
        search, clear_search, clear_filters, reset_all = st.columns([10, 3, 3, 3]) 

        with search:
            st.text_input(
                "Strategy Name:",
                value="",
                placeholder="Type to filter by strategy name...",
                key="strategy_search_input",
                max_chars=250,
                label_visibility="collapsed",
            )
        
        with clear_search:
            st.button(
                ":material/close: Clear search",
                key="clear_search_btn",
                width="stretch",
                on_click=_clear_search_state,
            )

        with clear_filters:
            st.button(
                ":material/filter_alt_off: Clear filters",
                key="clear_filters_btn",
                width="stretch",
                on_click=_reset_filter_state,
            )

        with reset_all:
            st.button(
                ":material/restart_alt: Reset all",
                key="reset_all_btn",
                width="stretch",
                on_click=_reset_all_state,
            )
        
        # Row 2
        st.space(1)
        ic, tm, sma, pm, esg = st.columns([6, 3, 3, 3, 3])
        
        with ic:
            st.segmented_control(
                label=":material/star: IC Status",
                options=["Recommended", "Recommended & Approved"],
                selection_mode="single",
                key="filter_ic",
            )
        
        with tm:
            st.segmented_control(
                label=":material/savings: Tax-Managed (TM)",
                options=["Yes", "No"],
                selection_mode="single",
                key="filter_tm",
            )
        
        with sma:
            st.segmented_control(
                label=":material/tune: SMA Manager",
                options=["Yes", "No"],
                selection_mode="single",
                key="filter_sma",
            )
        
        with pm:
            st.segmented_control(
                label=":material/key: Private Markets",
                options=["Yes", "No"],
                selection_mode="single",
                key="filter_pm",
            )
        
        with esg:
            st.segmented_control(
                label=":material/eco: ESG Filtered",
                options=["Yes", "No"],
                selection_mode="single",
                key="filter_esg",
                disabled=True,
            )
        
        # Row 3
        type, min, empty, equity = st.columns([3, 2, 1, 3])
        
        with type:
            st.segmented_control(
                ":material/stat_minus_1: Type",
                options=["Risk-Based", "Asset Class"],
                selection_mode="multi",
                key="filter_type",
            )
        
        with empty:
            st.empty()
        
        with min:
            st.number_input(
                ":material/attach_money: Current Account Value",
                min_value=0,
                value=None,
                step=10000,
                key="min_strategy",
            )
        
        # Equity Allocation range slider (only visible when Risk-Based is selected)
        with equity:
            if "Risk-Based" in st.session_state.get("filter_type", []):
                st.slider(
                    "Equity Allocation (%)",
                    min_value=0,
                    max_value=100,
                    value=(0, 100),
                    step=10,
                    key="equity_allocation_range",
                )
            else:
                st.empty()
        
        # Row 4
        selected_type: list[str] = st.session_state.get("filter_type", [])
        previous_type: list[str] = st.session_state.get("_previous_type", [])
        

        if not selected_type:
            # Show all subtypes when no types are selected
            all_subtypes: list[str] = [
                subtype for subtype_list in TYPE_TO_SUBTYPE.values() for subtype in subtype_list
            ]
            type_options: list[str] = all_subtypes
        else:
            type_options: list[str] = []
            for st_type in selected_type:
                if st_type in TYPE_TO_SUBTYPE:
                    type_options.extend(TYPE_TO_SUBTYPE[st_type])
        
        # Always sort with Multifactor Series, Market Series, Income Series first
        priority_subtypes = ["Multifactor Series", "Market Series", "Income Series"]
        type_options = (
            [subtype for subtype in priority_subtypes if subtype in type_options] +
            [subtype for subtype in type_options if subtype not in priority_subtypes]
        )
        
        if set(selected_type) != set(previous_type):
            st.session_state["filter_subtype"] = []
            st.session_state["_previous_type"] = selected_type.copy()
        
        st.segmented_control(
            ":material/stat_minus_2: Subtype",
            options=type_options,
            selection_mode="multi",
            key="filter_subtype",
        )

def build_filter_expression() -> pl.Expr:
    """Build filter expression from session state."""

    expressions: list[pl.Expr] = []
    
    # Search filter
    strategy_search_text: str = st.session_state.get("strategy_search_input", "")
    if strategy_search_text:
        sanitized: str = strategy_search_text.strip()
        if sanitized:
            expressions.append(
                pl.col(STRATEGY)
                .str.to_lowercase()
                .str.contains(pattern=sanitized.lower(), literal=True)
            )
    
    # IC Status filter
    recommended_selection: str = st.session_state["filter_ic"]
    if recommended_selection == "Recommended":
        expressions.append(pl.col(RECOMMENDED))

    # TODO: update to use boolean filter once database is updated
    # Tax-Managed filter
    tax_managed_selection: str | None = st.session_state["filter_tm"]
    if tax_managed_selection:
        expressions.append(pl.col(TAX_MANAGED) == (tax_managed_selection == "Yes"))

    # TODO: update to use boolean filter once database is updated
    # Has SMA Manager filter
    sma_selection: str | None = st.session_state["filter_sma"]
    if sma_selection:
        expressions.append(pl.col(HAS_SMA_MANAGER) == (sma_selection == "Yes"))
    
    # TODO: update to use boolean filter once database is updated
    # Private Markets filter
    private_markets_selection: str | None = st.session_state["filter_pm"]
    if private_markets_selection:
        if private_markets_selection == "Yes":
            expressions.append(pl.col(PRIVATE_MARKETS))
        elif private_markets_selection == "No":
            expressions.append(~pl.col(PRIVATE_MARKETS))

    # Account Value filter
    min_strategy: int | float | None = st.session_state["min_strategy"]
    if min_strategy is not None:
        expressions.append(pl.col(MINIMUM).le(min_strategy))

    # Equity Allocation filter (only if Risk-Based is selected)
    if "Risk-Based" in st.session_state.get("filter_type", []):
        min_eq, max_eq = st.session_state.get("equity_allocation_range", (0, 100))
        expressions.append(
            (pl.col(EQUITY_PCT).is_not_null()) # TODO: check database if this is needed
            & (pl.col(EQUITY_PCT).ge(min_eq))
            & (pl.col(EQUITY_PCT).le(max_eq))
        )
    
    # Type (multi-select) - Empty list means show all (none selected)
    type_value: list[str] = st.session_state.get("filter_type", [])
    if type_value:
        expressions.append(pl.col(CATEGORY).is_in(type_value)) # TODO: check when database is updated
    
    # Subtype - Empty list means show all (none selected)
    subtype_value: list[str] = st.session_state.get("filter_subtype", [])
    if subtype_value:
        expressions.append(pl.col(TYPE).is_in(subtype_value)) # TODO: check when database is updated
    
    # Combine all filter expressions with AND logic
    if not expressions:
        return pl.lit(True)
    
    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr
