"""Centralized session state management utilities."""

from typing import TypeVar, Callable, Any

import streamlit as st

from utils.core.constants import (
    DEFAULT_COLLAPSE_SMA,
    DEFAULT_EQUITY_RANGE,
    DEFAULT_MIN_STRATEGY,
    STRATEGY_TYPES,
    STRATEGY_TYPE_TO_SERIES,
)
from utils.security import validate_session_state_value

T = TypeVar("T")


def _validate_filter_recommended(value: Any) -> bool:
    """Validate filter_recommended_only value."""
    return value in ("Recommended", "All", None)


def _validate_filter_yes_no(value: Any) -> bool:
    """Validate Yes/No filter values."""
    return value in ("Yes", "No", None)


def _validate_min_strategy(value: Any) -> bool:
    """Validate min_strategy value."""
    return isinstance(value, (int, float)) and value >= 0


def _validate_equity_range(value: Any) -> bool:
    """Validate equity_range value."""
    return (
        isinstance(value, tuple) 
        and len(value) == 2 
        and all(isinstance(x, (int, float)) for x in value)
        and 0 <= value[0] <= value[1] <= 100
    )


def _validate_strategy_type(value: Any) -> bool:
    """Validate filter_strategy_type value."""
    return value in ("Risk-Based", "Asset-Class", "Special Situation")


def _validate_filter_series(value: Any) -> bool:
    """Validate filter_series value."""
    if value is None:
        return True
    if isinstance(value, list):
        # Check all items are strings
        return all(isinstance(item, str) for item in value)
    if isinstance(value, str):
        return True
    return False


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
    # Filter state - initialize with defaults, validate existing values
    if "filter_recommended_only" not in st.session_state:
        st.session_state["filter_recommended_only"] = "Recommended"
    elif not validate_session_state_value(
        "filter_recommended_only", 
        st.session_state["filter_recommended_only"],
        (str, type(None)),
        _validate_filter_recommended
    ):
        st.session_state["filter_recommended_only"] = "Recommended"
    
    if "filter_tax_managed" not in st.session_state:
        st.session_state["filter_tax_managed"] = None
    elif not validate_session_state_value(
        "filter_tax_managed",
        st.session_state["filter_tax_managed"],
        (str, type(None)),
        _validate_filter_yes_no
    ):
        st.session_state["filter_tax_managed"] = None
    
    if "filter_sma_manager" not in st.session_state:
        st.session_state["filter_sma_manager"] = None
    elif not validate_session_state_value(
        "filter_sma_manager",
        st.session_state["filter_sma_manager"],
        (str, type(None)),
        _validate_filter_yes_no
    ):
        st.session_state["filter_sma_manager"] = None
    
    if "filter_private_markets" not in st.session_state:
        st.session_state["filter_private_markets"] = None
    elif not validate_session_state_value(
        "filter_private_markets",
        st.session_state["filter_private_markets"],
        (str, type(None)),
        _validate_filter_yes_no
    ):
        st.session_state["filter_private_markets"] = None
    
    if "min_strategy" not in st.session_state:
        st.session_state["min_strategy"] = DEFAULT_MIN_STRATEGY
    elif not validate_session_state_value(
        "min_strategy",
        st.session_state["min_strategy"],
        (int, float),
        _validate_min_strategy
    ):
        st.session_state["min_strategy"] = 50000
    
    if "equity_allocation" not in st.session_state:
        st.session_state["equity_allocation"] = 60
    elif not validate_session_state_value(
        "equity_allocation",
        st.session_state["equity_allocation"],
        (int, float),
        lambda v: isinstance(v, (int, float)) and 0 <= v <= 100
    ):
        st.session_state["equity_allocation"] = 60
    
    if "filter_strategy_type" not in st.session_state:
        st.session_state["filter_strategy_type"] = [STRATEGY_TYPES[0]]  # ["Risk-Based"]
    elif not validate_session_state_value(
        "filter_strategy_type",
        st.session_state["filter_strategy_type"],
        (list, str),
        lambda v: (isinstance(v, list) and all(_validate_strategy_type(t) for t in v)) or _validate_strategy_type(v)
    ):
        st.session_state["filter_strategy_type"] = [STRATEGY_TYPES[0]]
    
    if "filter_series" not in st.session_state:
        # Default series for Risk-Based strategy type
        st.session_state["filter_series"] = STRATEGY_TYPE_TO_SERIES[STRATEGY_TYPES[0]]
    elif not validate_session_state_value(
        "filter_series",
        st.session_state["filter_series"],
        (list, str, type(None)),
        _validate_filter_series
    ):
        st.session_state["filter_series"] = ["Multifactor Series", "Market Series", "Income Series"]
    
    if "_previous_strategy_type" not in st.session_state:
        st.session_state["_previous_strategy_type"] = STRATEGY_TYPES[0]  # "Risk-Based"
    elif not validate_session_state_value(
        "_previous_strategy_type",
        st.session_state["_previous_strategy_type"],
        str,
        _validate_strategy_type
    ):
        st.session_state["_previous_strategy_type"] = "Risk-Based"
    
    # Search state
    if "strategy_search_input" not in st.session_state:
        st.session_state["strategy_search_input"] = ""
    elif not validate_session_state_value(
        "strategy_search_input",
        st.session_state["strategy_search_input"],
        (str, type(None)),
        _validate_search_input
    ):
        st.session_state["strategy_search_input"] = ""
    
    if "_clear_search_flag" not in st.session_state:
        st.session_state["_clear_search_flag"] = False
    elif not isinstance(st.session_state["_clear_search_flag"], bool):
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
