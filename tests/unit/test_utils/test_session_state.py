"""Tests for utils.session_state module."""

from utils.session_state import (
    get_or_init,
    initialize_session_state,
    reset_if_changed,
)


# Test `initialize_session_state()`
def test_initialize_session_state_sets_all_defaults(mock_streamlit):
    """Test that initialize_session_state sets all default values."""
    # Call the function
    initialize_session_state()

    # Verify all defaults are set
    assert mock_streamlit["filter_ic"] == "Recommended"
    assert mock_streamlit["filter_tm"] is None
    assert mock_streamlit["filter_sma"] is None
    assert mock_streamlit["filter_pm"] is None
    assert mock_streamlit["min_strategy"] is None
    assert mock_streamlit["filter_type"] == []
    assert mock_streamlit["filter_subtype"] == []
    assert mock_streamlit["_previous_type"] == []
    assert mock_streamlit["_previous_subtype"] == []
    assert mock_streamlit["strategy_search_input"] == ""
    assert mock_streamlit["_clear_search_flag"] is False


# Test `get_or_init`
def test_get_or_init_returns_existing_value(mock_streamlit):
    """Test that get_or_init returns existing value if key exists."""
    # Set up: key already exists
    mock_streamlit["existing_key"] = "existing_value"

    # Call function
    result = get_or_init("existing_key", "default_value")

    # Verify: returns existing value, not default
    assert result == "existing_value"
    assert mock_streamlit["existing_key"] == "existing_value"


def test_get_or_init_sets_default_when_missing(mock_streamlit):
    """Test that get_or_init sets and returns default when key is missing."""
    # Set up: key doesn't exist

    # Call function
    result = get_or_init("new_key", "default_value")

    # Verify: default was set and returned
    assert result == "default_value"
    assert mock_streamlit["new_key"] == "default_value"


def test_get_or_init_uses_init_function(mock_streamlit):
    """Test that get_or_init uses init function when provided."""

    # Set up: create an init function
    def init_fn():
        return ["initialized", "list"]

    # Call function
    result = get_or_init("new_key", None, init_fn=init_fn)

    # Verify: init function was called and result stored
    assert result == ["initialized", "list"]
    assert mock_streamlit["new_key"] == ["initialized", "list"]


def test_get_or_init_does_not_call_init_if_key_exists(mock_streamlit):
    """Test that init function is not called if key already exists."""
    # Set up: key exists
    mock_streamlit["existing_key"] = "existing_value"
    init_func_called = False

    def init_fn():
        nonlocal init_func_called
        init_func_called = True
        return "should_not_be_called"

    # Call function
    result = get_or_init("existing_key", "default", init_fn=init_fn)

    # Verify: init function was NOT called
    assert result == "existing_value"
    assert init_func_called is False


# Test `reset_if_changed()`
def test_reset_if_changed_sets_value_when_key_missing(mock_streamlit):
    """Test that reset_if_changed sets value when key is missing."""
    # Set up: key doesn't exist, reset_key has a value
    mock_streamlit["reset_key"] = "old_value"

    # Call function
    reset_if_changed("watch_key", "new_value", "reset_key", "reset_value")

    # Verify: watch_key was set, reset_key was reset
    assert mock_streamlit["watch_key"] == "new_value"
    assert mock_streamlit["reset_key"] == "reset_value"


def test_reset_if_changed_resets_when_value_changes(mock_streamlit):
    """Test that reset_if_changed resets when watched value changes."""
    # Set up: watch_key exists with old value
    mock_streamlit["watch_key"] = "old_value"
    mock_streamlit["reset_key"] = "old_reset_value"

    # Call function with new value
    reset_if_changed("watch_key", "new_value", "reset_key", "reset_value")

    # Verify: watch_key updated, reset_key reset
    assert mock_streamlit["watch_key"] == "new_value"
    assert mock_streamlit["reset_key"] == "reset_value"


def test_reset_if_changed_does_nothing_when_value_unchanged(mock_streamlit):
    """Test that reset_if_changed does nothing when value hasn't changed."""
    # Set up: watch_key exists with same value
    mock_streamlit["watch_key"] = "same_value"
    mock_streamlit["reset_key"] = "should_stay"

    # Call function with same value
    reset_if_changed("watch_key", "same_value", "reset_key", "reset_value")

    # Verify: reset_key was NOT changed
    assert mock_streamlit["reset_key"] == "should_stay"
