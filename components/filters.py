import polars as pl
import streamlit as st

from utils.core.constants import (
    STRATEGY_TYPE_TO_SERIES,
    STRATEGY_TYPES,
)
from utils.security import MAX_SEARCH_INPUT_LENGTH, validate_search_input

# Series options derived from strategy type mapping
SERIES_OPTIONS: list[str] = [
    series for series_list in STRATEGY_TYPE_TO_SERIES.values() for series in series_list
]



def _render_yes_no_filter(label: str, key: str, disabled: bool, default: str | None = None) -> str | None:
    """Render a boolean filter segmented control with Yes/No options.
    
    Args:
        label: Label for the filter control
        key: Session state key for the filter
        disabled: Whether the filter is disabled
        default: Default selection ("Yes", "No", or None)
    """
    return st.segmented_control(
        label,
        options=["Yes", "No"],
        selection_mode="single",
        default=default,
        disabled=disabled,
        key=key,
    )


def render_search_bar() -> tuple[bool, str | None]:
    """Render search bar UI and return (search_active, strategy_search).
    
    Note: This function is now called from within render_filters_inline, but kept for backward compatibility.
    """
    # Check if we need to clear search (must be done before any widgets are created)
    if st.session_state["_clear_search_flag"]:
        st.session_state["strategy_search_input"] = ""
        st.session_state["_clear_search_flag"] = False
    
    # Validate and sanitize search input
    strategy_search_text = st.session_state.get("strategy_search_input", "")
    try:
        strategy_search = validate_search_input(strategy_search_text)
        search_active = bool(strategy_search)
    except ValueError as e:
        # If validation fails, show error and reset search
        st.error(str(e))
        st.session_state["strategy_search_input"] = ""
        strategy_search = None
        search_active = False
    
    return search_active, strategy_search


def render_filters_inline(search_active: bool) -> None:
    """Render filter controls inline in two rows above Order By.
    
    Args:
        search_active: Whether search is currently active (for display purposes only, filters are not disabled)
    """
    # Check if we need to clear search (must be done before any widgets are created)
    if st.session_state["_clear_search_flag"]:
        st.session_state["strategy_search_input"] = ""
        st.session_state["_clear_search_flag"] = False
    
    with st.expander("Filters", expanded=True, icon=":material/feature_search:"):
        # Render search bar at the top of the filters container
        col_search, col_clear = st.columns([10, 2])
        with col_search:
            strategy_search_text = st.text_input(
                "Strategy Name:",
                value="",
                placeholder="Type to filter by strategy name...",
                key="strategy_search_input",
                max_chars=MAX_SEARCH_INPUT_LENGTH,
                label_visibility="collapsed",
            )
            # Validate search input
            if strategy_search_text:
                try:
                    validate_search_input(strategy_search_text)
                except ValueError as e:
                    st.error(str(e))
                    st.session_state["strategy_search_input"] = ""
        with col_clear:
            if st.button(":material/close: Clear", key="clear_search_btn", use_container_width=True):
                st.session_state["_clear_search_flag"] = True
                st.rerun()
        
        st.space(1)
        # Row 1: IC Status, Yes/No filters, Account Value
        col_ic, col_tax, col_sma, col_private, col_min = st.columns([2, 1, 1, 1, 2])
        
        with col_ic:
            # IC Status: Recommended / Approved
            st.segmented_control(
                "IC Status",
                options=["Recommended", "Recommended & Approved"],
                selection_mode="single",
                key="filter_recommended_only",
            )
        
        with col_tax:
            _render_yes_no_filter(
                label="Tax-Managed (TM)", key="filter_tax_managed", disabled=False
            )
        
        with col_sma:
            _render_yes_no_filter(
                label="Has SMA Manager", key="filter_sma_manager", disabled=False
            )
        
        with col_private:
            _render_yes_no_filter(
                label="Private Markets", key="filter_private_markets", disabled=False
            )
        
        with col_min:
            st.number_input(
                "Account Value ($)",
                min_value=0,
                value=None,
                step=10000,
                key="min_strategy",
            )
        
        # Row 2: Strategy Type (multi-select), Series, Equity Allocation (only visible when Risk-Based selected)
        selected_type = st.session_state.get("filter_strategy_type", [])
        if not isinstance(selected_type, list):
            selected_type = [selected_type] if selected_type else []
        
        is_risk_based = "Risk-Based" in selected_type if selected_type else False
        
        # Always use 3 columns for consistent alignment
        col_type, col_series, col_equity = st.columns([2, 4, 2])
        
        with col_type:
            # Strategy Type: multi-select
            # Note: Don't use default= when key is set - Streamlit automatically syncs with session state
            # The session state is initialized in utils.core.session_state, so the key will handle the value
            st.segmented_control(
                "Strategy Type",
                options=STRATEGY_TYPES,
                selection_mode="multi",
                key="filter_strategy_type",
            )
        
        with col_series:
            # Session state is initialized, so we can access directly
            selected_type = st.session_state.get("filter_strategy_type", [])
            if not isinstance(selected_type, list):
                selected_type = [selected_type] if selected_type else []
            
            previous_type_key = "_previous_strategy_type"
            previous_type = st.session_state.get(previous_type_key, [])
            if not isinstance(previous_type, list):
                previous_type = [previous_type] if previous_type else []
            
            # Get all series options for selected strategy types
            # If no strategy types selected, show all series options
            type_options: list[str] = []
            if selected_type:
                for st_type in selected_type:
                    if st_type in STRATEGY_TYPE_TO_SERIES:
                        type_options.extend(STRATEGY_TYPE_TO_SERIES[st_type])
                # Remove duplicates while preserving order
                type_options = list(dict.fromkeys(type_options))
            else:
                # No strategy types selected - show all series options
                type_options = SERIES_OPTIONS

            # Handle strategy type changes by clearing series selections
            if set(selected_type) != set(previous_type):
                # When strategy types change, reset series to empty (show all)
                st.session_state["filter_series"] = []
                st.session_state[previous_type_key] = selected_type
            
            # Use segmented control for multi-select Series
            # Note: Don't use default= when key is set - Streamlit automatically syncs with session state
            # Empty list in session state means show all (none selected)
            st.segmented_control(
                "Series",
                options=type_options,
                selection_mode="multi",
                key="filter_series",
            )
        
        # Equity Allocation range slider (only visible when Risk-Based is selected)
        with col_equity:
            if is_risk_based:
                # Get current range values from session state
                equity_range = st.session_state.get("equity_allocation_range", (0, 100))
                if not isinstance(equity_range, tuple) or len(equity_range) != 2:
                    equity_range = (0, 100)
                
                st.slider(
                    "Equity Allocation (%)",
                    min_value=0,
                    max_value=100,
                    value=equity_range,
                    step=10,
                    key="equity_allocation_range",
                )
            else:
                # Empty spacer to maintain column alignment
                st.empty()


def _build_search_filter(strategy_search: str | None) -> pl.Expr:
    """Build search filter expression.
    
    Args:
        strategy_search: Sanitized search text
        
    Returns:
        Polars expression for search filter
    """
    if not strategy_search:
        return pl.lit(True)
    
    return (
        pl.col("Strategy")
        .str.to_lowercase()
        .str.contains(strategy_search.lower(), literal=True)
    )


def _build_recommended_filter(recommended_selection: str) -> pl.Expr | None:
    """Build recommended filter expression.
    
    Args:
        recommended_selection: "Recommended" or "Recommended & Approved"
        
    Returns:
        Polars expression for recommended filter, or None if no filter should be applied
    """
    if recommended_selection == "Recommended":
        return pl.col("Recommended")
    elif recommended_selection == "Recommended & Approved":
        # Show all strategies (no filter applied) - return None to skip adding to expressions
        return None
    # Fallback to Recommended if somehow invalid value
    return pl.col("Recommended")


def _build_account_value_filter(min_strategy: int | float | None) -> pl.Expr | None:
    """Build account value filter expression.
    
    Args:
        min_strategy: Minimum account value or None to disable filtering
        
    Returns:
        Polars expression for account value filter or None if no filter needed
    """
    if min_strategy is None:
        return None
    return pl.col("Minimum") <= min_strategy


def _build_equity_allocation_filter(equity_range: tuple[int, int] | None) -> pl.Expr | None:
    """Build equity allocation filter expression.
    
    Args:
        equity_range: Tuple of (min, max) equity percentage values or None
        
    Returns:
        Polars expression for equity allocation filter or None if not filtering
    """
    if equity_range is None:
        return None
    min_equity, max_equity = equity_range
    # Filter within the selected range
    return (
        (pl.col("Equity %").is_not_null())
        & (pl.col("Equity %") >= min_equity)
        & (pl.col("Equity %") <= max_equity)
    )


def _build_boolean_filter(column_name: str, selection: str | None) -> pl.Expr | None:
    """Build boolean filter expression for Yes/No filters.
    
    Args:
        column_name: Column name to filter on
        selection: "Yes", "No", or None
        
    Returns:
        Polars expression or None if no filter needed
    """
    if not selection:
        return None
    return pl.col(column_name) == (selection == "Yes")


def _build_private_markets_filter(selection: str | None) -> pl.Expr | None:
    """Build private markets filter expression.
    
    Args:
        selection: "Yes", "No", or None
        
    Returns:
        Polars expression or None if no filter needed
    """
    if not selection:
        return None
    if selection == "Yes":
        return pl.col("Private Markets")
    elif selection == "No":
        return ~pl.col("Private Markets")
    return None


def _build_strategy_type_filter(selected_types: list[str] | str | None) -> pl.Expr | None:
    """Build strategy type filter expression.
    
    Args:
        selected_types: List of strategy types, single strategy type, or None
        
    Returns:
        Polars expression or None if no filter needed
    """
    if not selected_types:
        return None
    if isinstance(selected_types, str):
        selected_types = [selected_types]
    if not selected_types:
        return None
    return pl.col("Strategy Type").is_in(selected_types)


def _build_series_filter(selected_subtypes: list[str] | str | None) -> pl.Expr | None:
    """Build series filter expression.
    
    Args:
        selected_subtypes: List of series, single series, or None
        
    Returns:
        Polars expression or None if no filter needed
    """
    if selected_subtypes is None:
        return None
    if not isinstance(selected_subtypes, list):
        selected_subtypes = [selected_subtypes]
    if not selected_subtypes:
        return None
    return pl.col("Type").is_in(selected_subtypes)


def _combine_filter_expressions(expressions: list[pl.Expr]) -> pl.Expr:
    """Combine filter expressions with AND logic.
    
    Args:
        expressions: List of Polars expressions
        
    Returns:
        Combined expression
    """
    if not expressions:
        return pl.lit(True)
    
    combined_expr = expressions[0]
    for expr in expressions[1:]:
        combined_expr = combined_expr & expr
    return combined_expr


def render_filters(search_active: bool) -> pl.Expr:
    """Build filter expression from session state (filters are rendered inline via render_filters_inline).
    
    Args:
        search_active: Whether search is currently active (for combining with filters)
    """
    # Build filter expressions from session state
    expressions: list[pl.Expr] = []
    
    # Add search filter if active
    if search_active:
        strategy_search_text = st.session_state["strategy_search_input"]
        try:
            strategy_search = validate_search_input(strategy_search_text)
            search_expr = _build_search_filter(strategy_search)
            if search_expr is not None:
                expressions.append(search_expr)
        except ValueError:
            pass
    
    # Investment Committee Recommended
    # "Recommended" filters to only recommended strategies
    # "Recommended & Approved" shows all strategies (no filter)
    recommended_expr = _build_recommended_filter(st.session_state["filter_recommended_only"])
    if recommended_expr is not None:
        expressions.append(recommended_expr)
    
    # Account Value
    account_value_expr = _build_account_value_filter(st.session_state["min_strategy"])
    if account_value_expr is not None:
        expressions.append(account_value_expr)
    
    # Equity Allocation (only if Risk-Based is selected and equity_range is set)
    selected_type = st.session_state.get("filter_strategy_type", [])
    if not isinstance(selected_type, list):
        selected_type = [selected_type] if selected_type else []
    is_risk_based = "Risk-Based" in selected_type if selected_type else False
    
    if is_risk_based:
        equity_range = st.session_state.get("equity_allocation_range")
        # Only apply filter if range is not the default (0, 100) or if it's explicitly set
        if equity_range and isinstance(equity_range, tuple) and len(equity_range) == 2:
            min_eq, max_eq = equity_range
            # Only filter if range is not the full range (0-100)
            if min_eq != 0 or max_eq != 100:
                equity_expr = _build_equity_allocation_filter(equity_range)
                if equity_expr is not None:
                    expressions.append(equity_expr)
    
    # Tax-Managed
    tax_managed_expr = _build_boolean_filter("Tax-Managed", st.session_state["filter_tax_managed"])
    if tax_managed_expr is not None:
        expressions.append(tax_managed_expr)
    
    # Has SMA Manager
    sma_expr = _build_boolean_filter("Has SMA Manager", st.session_state["filter_sma_manager"])
    if sma_expr is not None:
        expressions.append(sma_expr)
    
    # Private Markets
    private_markets_expr = _build_private_markets_filter(st.session_state["filter_private_markets"])
    if private_markets_expr is not None:
        expressions.append(private_markets_expr)
    
    # Strategy Type (multi-select)
    # Empty list means show all (none selected)
    strategy_type_value = st.session_state.get("filter_strategy_type", [])
    if not isinstance(strategy_type_value, list):
        strategy_type_value = [strategy_type_value] if strategy_type_value else []
    # Only apply filter if list is not empty
    if strategy_type_value:
        strategy_type_expr = _build_strategy_type_filter(strategy_type_value)
        if strategy_type_expr is not None:
            expressions.append(strategy_type_expr)
    
    # Series
    # Empty list means show all (none selected)
    series_value = st.session_state.get("filter_series", [])
    # Only apply filter if list is not empty
    if series_value:
        series_expr = _build_series_filter(series_value)
        if series_expr is not None:
            expressions.append(series_expr)
    
    # Combine all filter expressions with AND logic
    return _combine_filter_expressions(expressions)


