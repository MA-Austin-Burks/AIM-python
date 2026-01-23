"""Centralized session state management utilities."""

from typing import TypeVar, Callable, Any

import streamlit as st

T = TypeVar("T")


# =============================================================================
# FILTER VALIDATION FUNCTIONS
# =============================================================================

def _validate_filter_recommended(value: Any) -> bool:
    """Validate filter_ic value."""
    return value in ("Recommended", "Recommended & Approved")


def _validate_filter_yes_no(value: Any) -> bool:
    """Validate Yes/No filter values."""
    return value in ("Yes", "No", None)


def _validate_type(value: Any) -> bool:
    """Validate filter_type value."""
    return value in ("Risk-Based", "Asset Class", "Special Situation")


def _validate_filter_subtype(value: Any) -> bool:
    """Validate filter_subtype value."""
    if value is None:
        return True
    if isinstance(value, list):
        # Check all items are strings
        return all(isinstance(item, str) for item in value)
    if isinstance(value, str):
        return True
    return False


# =============================================================================
# INPUT/NUMERIC VALIDATION FUNCTIONS
# =============================================================================

def _validate_min_strategy(value: Any) -> bool:
    """Validate min_strategy value."""
    return isinstance(value, (int, float)) and value >= 0


def _validate_search_input(value: Any) -> bool:
    """Validate strategy_search_input value."""
    if value is None:
        return True
    return isinstance(value, str) and len(value) <= 500


def initialize_session_state() -> None:
    """Initialize all session state variables explicitly at app start.
    
    This ensures all filter and UI state variables are set, eliminating
    the need for fallback defaults in .get() calls throughout the codebase.
    Also validates existing values to prevent session state manipulation.
    """
    # =========================================================================
    # FILTER STATE - Initialize with defaults, validate existing values
    # =========================================================================
    
    # IC Status filter
    st.session_state.setdefault("filter_ic", "Recommended")
    if not isinstance(st.session_state["filter_ic"], str) or not _validate_filter_recommended(st.session_state["filter_ic"]):
        st.session_state["filter_ic"] = "Recommended"
    
    # Yes/No filters (Tax-Managed, SMA Manager, Private Markets)
    st.session_state.setdefault("filter_tm", None)
    if not isinstance(st.session_state["filter_tm"], (str, type(None))) or not _validate_filter_yes_no(st.session_state["filter_tm"]):
        st.session_state["filter_tm"] = None
    
    st.session_state.setdefault("filter_sma", None)
    if not isinstance(st.session_state["filter_sma"], (str, type(None))) or not _validate_filter_yes_no(st.session_state["filter_sma"]):
        st.session_state["filter_sma"] = None
    
    st.session_state.setdefault("filter_pm", None)
    if not isinstance(st.session_state["filter_pm"], (str, type(None))) or not _validate_filter_yes_no(st.session_state["filter_pm"]):
        st.session_state["filter_pm"] = None
    
    # Numeric filters
    st.session_state.setdefault("min_strategy", None)
    if not isinstance(st.session_state["min_strategy"], (int, float, type(None))) or (st.session_state["min_strategy"] is not None and not _validate_min_strategy(st.session_state["min_strategy"])):
        st.session_state["min_strategy"] = None
    
    st.session_state.setdefault("equity_allocation_range", (0, 100))
    if not isinstance(st.session_state["equity_allocation_range"], tuple) or not (isinstance(st.session_state["equity_allocation_range"], tuple) and len(st.session_state["equity_allocation_range"]) == 2 and all(isinstance(x, (int, float)) and 0 <= x <= 100 for x in st.session_state["equity_allocation_range"]) and st.session_state["equity_allocation_range"][0] <= st.session_state["equity_allocation_range"][1]):
        st.session_state["equity_allocation_range"] = (0, 100)
    
    # Multi-select filters (Type, Subtype)
    st.session_state.setdefault("filter_type", [])  # Empty list means show all (none selected)
    if not isinstance(st.session_state["filter_type"], (list, str)) or not ((isinstance(st.session_state["filter_type"], list) and all(_validate_type(t) for t in st.session_state["filter_type"])) or _validate_type(st.session_state["filter_type"])):
        st.session_state["filter_type"] = []
    
    st.session_state.setdefault("filter_subtype", [])  # Empty list means show all subtypes (none selected)
    if not isinstance(st.session_state["filter_subtype"], (list, str, type(None))) or not _validate_filter_subtype(st.session_state["filter_subtype"]):
        st.session_state["filter_subtype"] = []
    
    st.session_state.setdefault("_previous_type", [])  # Empty list for no selection
    if not isinstance(st.session_state["_previous_type"], (list, str)) or not ((isinstance(st.session_state["_previous_type"], list) and all(_validate_type(t) for t in st.session_state["_previous_type"])) or _validate_type(st.session_state["_previous_type"])):
        # Reset to default empty list if validation fails (consistent with initial default)
        st.session_state["_previous_type"] = []
    
    st.session_state.setdefault("_previous_subtype", [])  # Empty list for tracking previous subtype selections
    if not isinstance(st.session_state["_previous_subtype"], list) or not all(isinstance(item, str) for item in st.session_state["_previous_subtype"]):
        st.session_state["_previous_subtype"] = []
    
    # =========================================================================
    # SEARCH STATE
    # =========================================================================
    st.session_state.setdefault("strategy_search_input", "")
    if not isinstance(st.session_state["strategy_search_input"], (str, type(None))) or not _validate_search_input(st.session_state["strategy_search_input"]):
        st.session_state["strategy_search_input"] = ""
    
    st.session_state.setdefault("_clear_search_flag", False)
    if not isinstance(st.session_state["_clear_search_flag"], bool):
        st.session_state["_clear_search_flag"] = False


def get_or_init(key: str, default: T, init_fn: Callable[[], T] | None = None) -> T:
    """Get session state value or initialize with default or init function.
    
    Note: This should only be used for UI state (like card order, pagination).
    Filter state should be initialized via initialize_session_state().
    """
    if init_fn:
        if key not in st.session_state:
            st.session_state[key] = init_fn()
    else:
        st.session_state.setdefault(key, default)
    return st.session_state[key]


def reset_if_changed(key: str, new_value: Any, reset_key: str, reset_value: Any) -> None:
    """Reset a state key when another key's value changes."""
    if key not in st.session_state or st.session_state[key] != new_value:
        st.session_state[key] = new_value
        st.session_state[reset_key] = reset_value
