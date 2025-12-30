"""Utility functions for data loading."""

import polars as pl
import streamlit as st


@st.cache_data(ttl=3600)
def load_strats(path: str = "data/strategies.csv") -> pl.DataFrame:
    """
    Load strategies data from CSV file.
    """
    return pl.read_csv(path, null_values=["NA"], truncate_ragged_lines=True)
