"""Centralized session state management utilities."""

from typing import TypeVar, Callable, Any

import streamlit as st

T = TypeVar("T")


def initialize_session_state() -> None:
    """Initialize all session state variables explicitly at app start.
    
    This ensures all filter and UI state variables are set, eliminating
    the need for fallback defaults in .get() calls throughout the codebase.
    """
    # Filter state - initialize with defaults
    if "filter_recommended_only" not in st.session_state:
        st.session_state["filter_recommended_only"] = "Yes"
    
    if "filter_tax_managed" not in st.session_state:
        st.session_state["filter_tax_managed"] = None
    
    if "filter_sma_manager" not in st.session_state:
        st.session_state["filter_sma_manager"] = None
    
    if "filter_private_markets" not in st.session_state:
        st.session_state["filter_private_markets"] = None
    
    if "min_strategy" not in st.session_state:
        st.session_state["min_strategy"] = 50000
    
    if "equity_range" not in st.session_state:
        st.session_state["equity_range"] = (0, 100)
    
    if "filter_strategy_type" not in st.session_state:
        st.session_state["filter_strategy_type"] = "Risk-Based"
    
    if "filter_series" not in st.session_state:
        st.session_state["filter_series"] = ["Multifactor Series", "Market Series", "Income Series"]
    
    if "_previous_strategy_type" not in st.session_state:
        st.session_state["_previous_strategy_type"] = "Risk-Based"
    
    # Search state
    if "strategy_search_input" not in st.session_state:
        st.session_state["strategy_search_input"] = ""
    
    if "_clear_search_flag" not in st.session_state:
        st.session_state["_clear_search_flag"] = False


def get_or_init(key: str, default: T, init_fn: Callable[[], T] | None = None) -> T:
    """Get session state value or initialize with default or init function.
    
    Note: This should only be used for UI state (like card order, pagination).
    Filter state should be initialized via initialize_session_state().
    """
    if key not in st.session_state:
        st.session_state[key] = init_fn() if init_fn else default
    return st.session_state[key]


def reset_if_changed(key: str, new_value: Any, reset_key: str, reset_value: Any) -> None:
    """Reset a state key when another key's value changes."""
    if key not in st.session_state:
        st.session_state[key] = new_value
        st.session_state[reset_key] = reset_value
    elif st.session_state[key] != new_value:
        st.session_state[key] = new_value
        st.session_state[reset_key] = reset_value
