"""Centralized constants for the application."""

from typing import Final

# =============================================================================
# UPDATE DATES
# =============================================================================
ABBREVIATIONS_UPDATE_DATE: Final[str] = "2026-01-17"
EQUIVALENTS_UPDATE_DATE: Final[str] = "2026-01-17"
TLH_UPDATE_DATE: Final[str] = "2026-01-17"
UNDER_DEVELOPMENT_UPDATE_DATE: Final[str] = "2026-01-17"
EXPLANATION_CARD_UPDATE_DATE: Final[str] = "2026-01-17"

# =============================================================================
# SESSION STATE KEYS
# =============================================================================
SELECTED_STRATEGY_MODAL_KEY: Final[str] = "selected_strategy_for_modal"
CARD_ORDER_KEY: Final[str] = "card_order_by"
CARDS_DISPLAYED_KEY: Final[str] = "cards_displayed"
ALLOCATION_COLLAPSE_SMA_KEY: Final[str] = "allocation_collapse_sma"

# =============================================================================
# CARD VIEW CONSTANTS
# =============================================================================
DEFAULT_CARD_ORDER: Final[str] = "Recommended (Default)"
CARDS_PER_LOAD: Final[int] = 20
CARD_GRID_COLUMNS: Final[int] = 4  # Deprecated: kept for backwards compatibility
CARD_FIXED_WIDTH: Final[str] = "350px"  # Fixed width for each card
CARD_GAP: Final[str] = "1rem"  # Gap between cards

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

# =============================================================================
# FILTER CONSTANTS
# =============================================================================
STRATEGY_TYPES: Final[list[str]] = ["Risk-Based", "Asset-Class", "Special Situation"]

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

# =============================================================================
# ALLOCATION TAB CONSTANTS
# =============================================================================
DEFAULT_COLLAPSE_SMA: Final[bool] = True
SMA_COLLAPSE_THRESHOLD: Final[int] = 10

# =============================================================================
# DESCRIPTION TAB CONSTANTS
# =============================================================================
GROUPING_OPTIONS: Final[list[str]] = ["Asset Category", "Asset Type", "Asset Class", "Product"]
PIE_CHART_MAX_ITEMS: Final[int] = 20

# =============================================================================
# DEFAULT VALUES
# =============================================================================
DEFAULT_MIN_STRATEGY: Final[int] = 50000
DEFAULT_EQUITY_RANGE: Final[tuple[int, int]] = (0, 100)
DEFAULT_TOTAL_ASSETS: Final[float] = 100000.0
