"""Centralized session state management utilities."""

from typing import TypeVar, Callable, Any

import streamlit as st

T = TypeVar("T")


def get_or_init(key: str, default: T, init_fn: Callable[[], T] | None = None) -> T:
    """Get session state value or initialize with default or init function."""
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
