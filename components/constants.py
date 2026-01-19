"""Constants for session state keys and configuration."""

from typing import Final

# Session state keys
SELECTED_STRATEGY_MODAL_KEY: Final[str] = "selected_strategy_for_modal"
CARD_ORDER_KEY: Final[str] = "card_order_by"
CARDS_DISPLAYED_KEY: Final[str] = "cards_displayed"
ALLOCATION_COLLAPSE_SMA_KEY: Final[str] = "allocation_collapse_sma"

# Default values
DEFAULT_CARD_ORDER: Final[str] = "Recommended (Default)"
CARDS_PER_LOAD: Final[int] = 20


# Card view options
CARD_ORDER_OPTIONS: Final[list[str]] = [
    "Recommended (Default)",
    "Acct Min - Highest to Lowest",
    "Acct Min - Lowest to Highest",
    "Expense Ratio - Highest to Lowest",
    "Expense Ratio - Lowest to Highest",
    "Yield - High to Low",
    "Yield - Low to High",
    "Equity % - High to Low",
    "Equity % - Low to High",
    "Strategy Name - A to Z",
    "Strategy Name - Z to A",
]
CARD_GRID_COLUMNS: Final[int] = 4

# Allocation/grouping options
GROUPING_OPTIONS: Final[list[str]] = ["Asset Category", "Asset Type", "Asset Class", "Product"]
DEFAULT_COLLAPSE_SMA: Final[bool] = True
SMA_COLLAPSE_THRESHOLD: Final[int] = 10
PIE_CHART_MAX_ITEMS: Final[int] = 20  # Maximum items to show in pie chart before combining into "Others"


EXPLANATION_CARD_UPDATE_DATE: Final[str] = "2026-01-17"