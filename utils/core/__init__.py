"""Core utility functions for formatting, data processing, and date handling."""

from utils.core.constants import (
    ABBREVIATIONS_UPDATE_DATE,
    ALLOCATION_COLLAPSE_SMA_KEY,
    CARD_GRID_COLUMNS,
    CARD_ORDER_KEY,
    CARD_ORDER_OPTIONS,
    CARDS_DISPLAYED_KEY,
    CARDS_PER_LOAD,
    DEFAULT_CARD_ORDER,
    DEFAULT_COLLAPSE_SMA,
    DEFAULT_EQUITY_RANGE,
    DEFAULT_MIN_STRATEGY,
    DEFAULT_TOTAL_ASSETS,
    EQUIVALENTS_UPDATE_DATE,
    EXPLANATION_CARD_UPDATE_DATE,
    GROUPING_OPTIONS,
    PIE_CHART_MAX_ITEMS,
    SELECTED_STRATEGY_MODAL_KEY,
    SMA_COLLAPSE_THRESHOLD,
    STRATEGY_TYPES,
    STRATEGY_TYPE_TO_SERIES,
    TLH_UPDATE_DATE,
    UNDER_DEVELOPMENT_UPDATE_DATE,
)
from utils.core.data import (
    get_model_agg_sort_order,
    get_strategy_by_name,
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
    # Constants
    "ABBREVIATIONS_UPDATE_DATE",
    "ALLOCATION_COLLAPSE_SMA_KEY",
    "CARD_GRID_COLUMNS",
    "CARD_ORDER_KEY",
    "CARD_ORDER_OPTIONS",
    "CARDS_DISPLAYED_KEY",
    "CARDS_PER_LOAD",
    "DEFAULT_CARD_ORDER",
    "DEFAULT_COLLAPSE_SMA",
    "DEFAULT_EQUITY_RANGE",
    "DEFAULT_MIN_STRATEGY",
    "DEFAULT_TOTAL_ASSETS",
    "EQUIVALENTS_UPDATE_DATE",
    "EXPLANATION_CARD_UPDATE_DATE",
    "GROUPING_OPTIONS",
    "PIE_CHART_MAX_ITEMS",
    "SELECTED_STRATEGY_MODAL_KEY",
    "SMA_COLLAPSE_THRESHOLD",
    "STRATEGY_TYPES",
    "STRATEGY_TYPE_TO_SERIES",
    "TLH_UPDATE_DATE",
    "UNDER_DEVELOPMENT_UPDATE_DATE",
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
    "get_strategy_by_name",
    "get_model_agg_sort_order",
    # Session state utilities
    "get_or_init",
    "reset_if_changed",
]
