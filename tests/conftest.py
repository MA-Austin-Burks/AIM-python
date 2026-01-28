"""Shared pytest fixtures for all tests."""

from unittest.mock import patch

import pytest


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit's session_state as a dictionary."""
    # Create a mock session_state dict
    mock_session_state = {}

    # Patch st.session_state where it's used
    with patch("streamlit.session_state", mock_session_state):
        # Also patch it in utils modules that import it
        with patch("utils.session_state.st.session_state", mock_session_state):
            yield mock_session_state
