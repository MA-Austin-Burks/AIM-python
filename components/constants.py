"""Constants for session state keys and configuration."""

from typing import Final

# Session state keys
SELECTED_STRATEGY_MODAL_KEY: Final[str] = "selected_strategy_for_modal"
CARD_ORDER_KEY: Final[str] = "card_order_by"
CARDS_DISPLAYED_KEY: Final[str] = "cards_displayed"
ALLOCATION_COLLAPSE_SMA_KEY: Final[str] = "allocation_collapse_sma"

# Default values
DEFAULT_CARD_ORDER: Final[str] = "Recommended (Default)"
CARDS_PER_LOAD: Final[int] = 21

# Sidebar filter defaults
DEFAULT_RECOMMENDED_ONLY: Final[bool] = False
DEFAULT_STRATEGY_TYPE: Final[str] = "Risk-Based"
DEFAULT_MIN_ACCOUNT_VALUE: Final[int] = 50000
DEFAULT_EQUITY_RANGE: Final[tuple[int, int]] = (0, 100)
DEFAULT_SERIES_SUBTYPES: Final[list[str]] = ["Multifactor Series", "Market Series", "Income Series"]

# Filter options lists
STRATEGY_TYPES: Final[list[str]] = ["Risk-Based", "Asset-Class", "Special Situation"]

# Mapping of strategy types to their available series options
STRATEGY_TYPE_TO_SERIES: Final[dict[str, list[str]]] = {
    "Risk-Based": [
        "Multifactor Series",
        "Market Series",
        "Income Series",
    ],
    "Asset-Class": [
        "Equity Strategies",
        "Fixed Income Strategies",
        "Cash Strategies",
        "Alternative Strategies",
    ],
    "Special Situation": [
        "Special Situation Strategies",
    ],
}

SERIES_OPTIONS: Final[list[str]] = [
    series for series_list in STRATEGY_TYPE_TO_SERIES.values() for series in series_list
]

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
CARD_GRID_COLUMNS: Final[int] = 3

# Allocation/grouping options
GROUPING_OPTIONS: Final[list[str]] = ["Asset Category", "Asset Type", "Asset Class", "Product"]
DEFAULT_COLLAPSE_SMA: Final[bool] = True
SMA_COLLAPSE_THRESHOLD: Final[int] = 10
PIE_CHART_MAX_ITEMS: Final[int] = 20  # Maximum items to show in pie chart before combining into "Others"


# Input constraints
MIN_ACCOUNT_VALUE: Final[int] = 0
ACCOUNT_VALUE_STEP: Final[int] = 10000
EQUITY_MIN_VALUE: Final[int] = 0
EQUITY_MAX_VALUE: Final[int] = 100
EQUITY_STEP: Final[int] = 10

ABBREVIATIONS_UPDATE_DATE: Final[str] = "2026-01-17"
EQUIVALENTS_UPDATE_DATE: Final[str] = "2026-01-17"
TLH_UPDATE_DATE: Final[str] = "2026-01-17"
UNDER_DEVELOPMENT_UPDATE_DATE: Final[str] = "2026-01-17"
EXPLANATION_CARD_UPDATE_DATE: Final[str] = "2026-01-17"