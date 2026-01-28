"""Centralized session state management utilities."""

from typing import Any, Callable, TypeVar

import streamlit as st

T = TypeVar("T")


def initialize_session_state() -> None:
    """Sets default values in Streamlit's session state."""
    defaults = {
        "filter_ic": "Recommended",
        "filter_tm": None,
        "filter_sma": None,
        "filter_pm": None,
        "min_strategy": None,
        "filter_type": [],
        "filter_subtype": [],
        "_previous_type": [],
        "_previous_subtype": [],
        "strategy_search_input": "",
        "_clear_search_flag": False,
    }
    for key, default in defaults.items():
        st.session_state.setdefault(key, default)


def get_or_init(key: str, default: T, init_fn: Callable[[], T] | None = None) -> T:
    """Gets a value or initializes it if missing."""
    if init_fn:
        if key not in st.session_state:
            st.session_state[key] = init_fn()
    else:
        st.session_state.setdefault(key, default)
    return st.session_state[key]


def reset_if_changed(
    key: str, new_value: Any, reset_key: str, reset_value: Any
) -> None:
    """Resets one value when another changes."""
    if key not in st.session_state or st.session_state[key] != new_value:
        st.session_state[key] = new_value
        st.session_state[reset_key] = reset_value
