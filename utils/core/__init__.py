"""Core utility functions for formatting, data processing, and date handling."""

from utils.core.data import (
    get_model_agg_sort_order,
    get_strategy_by_name,
    get_strategy_table,
    hash_lazyframe,
    load_cleaned_data,
    load_strategy_list,
)
from utils.core.dates import PERIOD_OPTIONS, get_period_dates
from utils.core.formatting import (
    format_currency_compact,
    generate_badges,
    get_series_color_from_row,
    get_strategy_color,
)
from utils.core.session_state import get_or_init, reset_if_changed

__all__ = [
    # Formatting utilities
    "format_currency_compact",
    "generate_badges",
    "get_strategy_color",
    "get_series_color_from_row",
    # Date utilities
    "PERIOD_OPTIONS",
    "get_period_dates",
    # Data utilities
    "hash_lazyframe",
    "load_cleaned_data",
    "load_strategy_list",
    "get_strategy_table",
    "get_strategy_by_name",
    "get_model_agg_sort_order",
    # Session state utilities
    "get_or_init",
    "reset_if_changed",
]
