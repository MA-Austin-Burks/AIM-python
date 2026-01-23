"""Column name constants for data files.

This module centralizes all column name references to make the codebase
more maintainable. If column names change in the data files, update them here.

All data sources are normalized to lowercase at load time. Display names
are handled separately at the presentation layer.
"""

# ============================================================================
# INTERNAL COLUMN NAMES (lowercase - used throughout codebase)
# ============================================================================
# All column names are normalized to lowercase at data load time.
# Use these constants throughout the codebase for consistency.

# Core identifiers
STRATEGY = "strategy"
MODEL = "ss_suite"  # Updated: was "model"
PORTFOLIO = "portfolio"
MODEL_AGG = "model_agg"
PRODUCT = "product"
TICKER = "ticker"

# Allocation/weighting
TARGET = "target"  # Derived column: agg_target / 100 (created in _map_ss_all_to_cleaned_data)
AGG_TARGET = "agg_target"
WEIGHT = "weight"
WEIGHT_FLOAT = "weight_float"  # Derived column

# Financial metrics
FEE = "fee"
YIELD = "yield"
MINIMUM = "minimum"
EXPENSE_RATIO = "expense_ratio"

# Type/category
TYPE = "ss_subtype"  # Updated: was "type"
CATEGORY = "ss_type"  # Updated: was "strategy_type"

# Strategy list specific columns (normalized to lowercase)
EQUITY_PCT = "equity_allo"  # Updated: was "equity_pct"
ALT_PCT = "private_allo"  # Alternative allocation percentage
RECOMMENDED = "ic_recommend"  # Updated: was "recommended"
TAX_MANAGED = "has_tm"  # Updated: was "tax_managed"
PRIVATE_MARKETS = "has_private_market"  # Updated: was "private_markets"
HAS_SMA_MANAGER = "has_sma"  # Updated: was "has_sma_manager"
SERIES = "series"  # Updated: was "series" - list of ss_subtype values (aggregated)

# Derived/cleaned columns
PRODUCT_CLEANED = "product_cleaned"  # Derived column

# Display/internal columns
ASSET_FORMATTED = "asset_formatted"
IS_CATEGORY = "is_category"
ROW_COLOR = "row_color"
ASSET = "asset"

# ============================================================================
# DISPLAY COLUMN NAMES (title case - only for user-facing display)
# ============================================================================
# These are used only at the presentation layer (tables, UI labels, etc.)
# Internal code should always use the lowercase constants above.

DISPLAY_STRATEGY = "Strategy"
DISPLAY_EQUITY_PCT = "Equity %"
DISPLAY_EXPENSE_RATIO = "Expense Ratio"
DISPLAY_YIELD = "Yield"
DISPLAY_MINIMUM = "Minimum"
DISPLAY_RECOMMENDED = "Recommended"
DISPLAY_TYPE = "Type"
DISPLAY_CATEGORY = "Strategy Type"
DISPLAY_TAX_MANAGED = "Tax-Managed"
DISPLAY_PRIVATE_MARKETS = "Private Markets"
DISPLAY_HAS_SMA_MANAGER = "Has SMA Manager"
DISPLAY_SERIES = "Series"
DISPLAY_WEIGHT = "Weight"

# Mapping from internal (lowercase) to display (title case) names
INTERNAL_TO_DISPLAY = {
    STRATEGY: DISPLAY_STRATEGY,
    EQUITY_PCT: DISPLAY_EQUITY_PCT,
    EXPENSE_RATIO: DISPLAY_EXPENSE_RATIO,
    YIELD: DISPLAY_YIELD,
    MINIMUM: DISPLAY_MINIMUM,
    RECOMMENDED: DISPLAY_RECOMMENDED,
    TYPE: DISPLAY_TYPE,
    CATEGORY: DISPLAY_CATEGORY,
    TAX_MANAGED: DISPLAY_TAX_MANAGED,
    PRIVATE_MARKETS: DISPLAY_PRIVATE_MARKETS,
    HAS_SMA_MANAGER: DISPLAY_HAS_SMA_MANAGER,
    SERIES: DISPLAY_SERIES,
    WEIGHT: DISPLAY_WEIGHT,
}

# ============================================================================
# COLUMN GROUPS
# ============================================================================
# Common column groups used together

# Core model data columns
MODEL_DATA_COLUMNS = [
    STRATEGY,
    PORTFOLIO,
    MODEL_AGG,
    PRODUCT,
    TICKER,
    TARGET,
    AGG_TARGET,
    WEIGHT,
    FEE,
    YIELD,
    MINIMUM,
]

# Summary metrics columns
SUMMARY_METRICS_COLUMNS = [
    STRATEGY,
    TARGET,
    FEE,
    YIELD,
    MINIMUM,
]

# Product columns
PRODUCT_COLUMNS = [
    PRODUCT_CLEANED,
    TICKER,
    WEIGHT_FLOAT,
]

# Strategy list columns (for filtering/sorting)
STRATEGY_LIST_COLUMNS = [
    STRATEGY,
    RECOMMENDED,
    EQUITY_PCT,
    YIELD,
    EXPENSE_RATIO,
    MINIMUM,
    TYPE,
    CATEGORY,
    TAX_MANAGED,
    PRIVATE_MARKETS,
    HAS_SMA_MANAGER,
    SERIES,
]
