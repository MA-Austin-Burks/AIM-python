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
DEFAULT_SERIES_SUBTYPES: Final[list[str]] = ["Multifactor Series", "Market Series"]

# Filter options lists
STRATEGY_TYPES: Final[list[str]] = ["Risk-Based", "Asset-Class", "Special Situation"]
SERIES_OPTIONS: Final[list[str]] = [
    "Multifactor Series",
    "Market Series",
    "Income Series",
    "Equity Strategies",
    "Fixed Income Strategies",
    "Cash Strategies",
    "Alternative Strategies",
    "Special Situation Strategies",
]

# Card view options
CARD_ORDER_OPTIONS: Final[list[str]] = [
    "Recommended (Default)",
    "Investment Committee Status",
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

# Model aggregate sort order
# TODO: add a column for the model aggregate sort order to the CSV to improve performance
MODEL_AGG_SORT_ORDER: Final[dict[str, int]] = {
    "GLOBAL EQUITY": 1,
    "ALL CAP": 2,
    "LARGE CAP": 3,
    "MID CAP": 4,
    "SMALL CAP": 5,
    "INT'L DEVELOPED": 6,
    "INTL DEVELOPED": 6,
    "INTL ADR": 7,
    "INT'L ADR": 7,
    "EMERGING MARKETS": 8,
    "NON TRADITIONAL": 9,
    "INTERVAL FUNDS": 10,
    "FIXED INCOME": 11,
}
# Note: Patterns are checked as substrings (case-insensitive)
# If multiple patterns match, the LOWEST sort_order is used
# Patterns should be ordered from most specific to least specific
MODEL_AGG_SORT_DEFAULT: Final[int] = 99  # Default sort order for unmatched patterns (high number = appears last)

# Input constraints
MIN_ACCOUNT_VALUE: Final[int] = 0
ACCOUNT_VALUE_STEP: Final[int] = 10000
EQUITY_MIN_VALUE: Final[int] = 0
EQUITY_MAX_VALUE: Final[int] = 100
EQUITY_STEP: Final[int] = 10
