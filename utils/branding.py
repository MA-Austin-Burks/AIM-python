"""
Mercer Advisors Brand Guidelines Configuration
===============================================
Centralized styling and color palettes for charts, UI elements, and typography.
Based on official Mercer Advisors brand guidelines.

Note: Theme colors, fonts, and UI styling are now configured in .streamlit/config.toml.
This module provides programmatic access to brand colors and chart color sequences.
"""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.models import StrategySummary

# =============================================================================
# PRIMARY PALETTE
# =============================================================================
PRIMARY = {
    "raspberry": "#C00686",
    "dark_raspberry": "#820361",
    "white": "#FFFFFF",
    "pale_gray": "#F3F4F6",
    "charcoal": "#454759",
    "light_gray": "#D1D1D6",
    "black": "#000000",
}

# =============================================================================
# SECONDARY PALETTE (Iris)
# =============================================================================
SECONDARY = {
    "pale_iris": "#E9E9FF",
    "light_iris": "#CFCCFF",
    "medium_iris": "#A5A0EF",
    "iris": "#7673DC",
    "dark_iris": "#50439B",
}

# =============================================================================
# TERTIARY PALETTE
# =============================================================================
TERTIARY = {
    # Azure shades
    "pale_azure": "#D5EEFF",
    "light_azure": "#A4D4FF",
    "medium_azure": "#6DB7FF",
    "azure": "#1E90FF",
    "dark_azure": "#225CBD",
    # Spring shades
    "pale_spring": "#BDFFDF",
    "light_spring": "#89F2C3",
    "medium_spring": "#47DEA2",
    "spring": "#00C48C",
    "dark_spring": "#00826B",
    # Gold shades
    "cream": "#FFF5E5",
    "light_gold": "#FDDB9A",
    "gold": "#F9A602",
    "dark_gold": "#CC8700",
    # Red shades
    "light_red": "#FA696E",
    "red": "#DA0028",
}

# =============================================================================
# SPECIAL USE PALETTE
# =============================================================================
SPECIAL = {
    "pale_raspberry": "#FFD8EF",
    "light_raspberry": "#FF96D7",
    "medium_raspberry": "#FC3DB0",
    "deep_raspberry": "#630349",
    "medium_gray": "#ABACB4",
    "gray": "#747583",
}

# =============================================================================
# CHART COLOR SEQUENCES
# Use these for Plotly charts, bar charts, pie/donut charts, etc.
# =============================================================================

# Primary chart sequence - use for most charts
CHART_COLORS_PRIMARY = [
    PRIMARY["raspberry"],  # #C00686
    SECONDARY["iris"],  # #7673DC
    TERTIARY["azure"],  # #1E90FF
    TERTIARY["spring"],  # #00C48C
    TERTIARY["gold"],  # #F9A602
    PRIMARY["charcoal"],  # #454759
]

# Extended chart sequence - for charts with more categories
CHART_COLORS_EXTENDED = [
    PRIMARY["raspberry"],  # #C00686
    SECONDARY["iris"],  # #7673DC
    TERTIARY["azure"],  # #1E90FF
    TERTIARY["spring"],  # #00C48C
    TERTIARY["gold"],  # #F9A602
    PRIMARY["charcoal"],  # #454759
    SECONDARY["dark_iris"],  # #50439B
    TERTIARY["dark_azure"],  # #225CBD
    TERTIARY["dark_spring"],  # #00826B
    TERTIARY["dark_gold"],  # #CC8700
]

# Allocation chart colors - for asset allocation pie/donut charts
CHART_COLORS_ALLOCATION = [
    TERTIARY["azure"],  # #1E90FF - U.S. stocks
    TERTIARY["spring"],  # #00C48C - Non-U.S. stocks
    TERTIARY["gold"],  # #F9A602 - Bonds
    SECONDARY["iris"],  # #7673DC - Short-term reserves
    PRIMARY["charcoal"],  # #454759 - Other
]

# Sequential palette for gradients (light to dark)
CHART_COLORS_SEQUENTIAL_RASPBERRY = [
    SPECIAL["pale_raspberry"],  # #FFD8EF
    SPECIAL["light_raspberry"],  # #FF96D7
    SPECIAL["medium_raspberry"],  # #FC3DB0
    PRIMARY["raspberry"],  # #C00686
    PRIMARY["dark_raspberry"],  # #820361
    SPECIAL["deep_raspberry"],  # #630349
]

CHART_COLORS_SEQUENTIAL_IRIS = [
    SECONDARY["pale_iris"],  # #E9E9FF
    SECONDARY["light_iris"],  # #CFCCFF
    SECONDARY["medium_iris"],  # #A5A0EF
    SECONDARY["iris"],  # #7673DC
    SECONDARY["dark_iris"],  # #50439B
]

CHART_COLORS_SEQUENTIAL_AZURE = [
    TERTIARY["pale_azure"],  # #D5EEFF
    TERTIARY["light_azure"],  # #A4D4FF
    TERTIARY["medium_azure"],  # #6DB7FF
    TERTIARY["azure"],  # #1E90FF
    TERTIARY["dark_azure"],  # #225CBD
]

# =============================================================================
# STRATEGY COLORS (Primary and Secondary)
# =============================================================================
STRATEGY_COLORS = {
    "Fixed Income Strategies": {
        "primary": "#00C48C",  # spring
        "secondary": "#BDFFDF",  # pale spring
    },
    "Cash Strategies": {
        "primary": "#FF0000",
        "secondary": "#FFD5D5",
    },
    "Special Situation Strategies": {
        "primary": "#274472",
        "secondary": "#5885af",
    },
}

# =============================================================================
# SERIES/CATEGORY COLORS (for dataframe tags and filters)
# =============================================================================
SUBTYPE_COLORS = {
    "Multifactor Series": PRIMARY["raspberry"],
    "Market Series": SECONDARY["iris"],
    "Income Series": PRIMARY["charcoal"],
    "Equity Strategies": TERTIARY["azure"],
    "Fixed Income Strategies": STRATEGY_COLORS["Fixed Income Strategies"]["primary"],
    "Cash Strategies": STRATEGY_COLORS["Cash Strategies"]["primary"],
    "Alternative Strategies": TERTIARY["gold"],
    "Special Situation Strategies": STRATEGY_COLORS["Special Situation Strategies"]["primary"],
    "Blended Strategy": SPECIAL["gray"],
}

# =============================================================================
# TYPOGRAPHY
# Note: Fonts are configured in .streamlit/config.toml for Streamlit UI.
# This dictionary is kept for programmatic use in Plotly charts.
# =============================================================================
FONTS = {
    "headline": "'Merriweather', Georgia, serif",
    "body": "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
}

# Google Fonts import for Streamlit custom CSS
GOOGLE_FONTS_IMPORT = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=Merriweather:wght@300;400;700&display=swap');
"""


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert hex color to RGBA string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# =============================================================================
# FORMATTING UTILITIES
# =============================================================================
def format_currency_compact(value: float) -> str:
    """Format currency value with K (thousands) and M (millions) suffixes."""
    if value is None or value == 0:
        return "$0.0"
    
    abs_value = abs(value)
    
    if abs_value >= 1_000_000:
        # Format as millions with 1 decimal place
        millions = value / 1_000_000
        return f"${millions:.1f}M"
    elif abs_value >= 1_000:
        # Format as thousands with 1 decimal place
        thousands = value / 1_000
        return f"${thousands:.1f}K"
    else:
        # Format as regular number with 1 decimal place
        return f"${value:.1f}"


def generate_badges(strategy_data: "StrategySummary | dict[str, Any]") -> list[str]:
    """Generate badge strings for a strategy based on its data."""
    if hasattr(strategy_data, "type"):
        recommended = getattr(strategy_data, "recommended", False)
        category = getattr(strategy_data, "category", None)
        type_val = getattr(strategy_data, "type", None)
        tax_managed = getattr(strategy_data, "tax_managed", False)
        private_markets = getattr(strategy_data, "private_markets", False)
    else:
        recommended = strategy_data.get("Recommended")
        category = strategy_data.get("Strategy Type")  # Database column name still "Strategy Type"
        type_val = strategy_data.get("Type")
        tax_managed = strategy_data.get("Tax-Managed")
        private_markets = strategy_data.get("Private Markets")

    badges = []

    if recommended:
        badges.append(":primary-badge[Recommend]")

    if category:
        badges.append(f":orange-badge[{category}]")

    if type_val:
        badges.append(f":blue-badge[{type_val}]")

    if tax_managed:
        badges.append(":green-badge[Tax-Managed]")

    if private_markets:
        badges.append(":gray-badge[Private Markets]")

    return badges


def get_subtype_color(subtype: str) -> str:
    """Get the color for a strategy based on its subtype."""
    return SUBTYPE_COLORS.get(subtype, PRIMARY["raspberry"])


def get_subtype_color_from_row(strategy_row: "StrategySummary | dict[str, Any]") -> str:
    """Get the color for a strategy based on its Subtype/Type from a row dict."""
    if hasattr(strategy_row, "subtype"):
        subtype_name = getattr(strategy_row, "subtype_primary", None)
        if subtype_name:
            return SUBTYPE_COLORS.get(subtype_name, PRIMARY["light_gray"])
        type_val = getattr(strategy_row, "type", None)
        if type_val:
            return SUBTYPE_COLORS.get(type_val, PRIMARY["light_gray"])
        return PRIMARY["light_gray"]

    subtype_list = strategy_row.get("Series", [])  # Database column name still "Series"
    if subtype_list and len(subtype_list) > 0:
        subtype_name = subtype_list[0] if isinstance(subtype_list, list) else subtype_list
        return SUBTYPE_COLORS.get(subtype_name, PRIMARY["light_gray"])

    # Fallback to Type field if Series is empty
    type_val = strategy_row.get("Type")
    if type_val:
        return SUBTYPE_COLORS.get(type_val, PRIMARY["light_gray"])

    return PRIMARY["light_gray"]


def get_strategy_primary_color(strategy_type: str) -> str:
    """Get the primary color for a strategy type."""
    if strategy_type in STRATEGY_COLORS:
        return STRATEGY_COLORS[strategy_type]["primary"]
    return SUBTYPE_COLORS.get(strategy_type, PRIMARY["raspberry"])


def get_strategy_secondary_color(strategy_type: str) -> str:
    """Get the secondary color for a strategy type."""
    if strategy_type in STRATEGY_COLORS:
        return STRATEGY_COLORS[strategy_type]["secondary"]
    # Fallback to a light version of the primary color if not defined
    return PRIMARY["light_gray"]


# =============================================================================
# TABLE STYLING
# =============================================================================
def get_allocation_table_main_css() -> str:
    """Generate CSS for the main allocation table.
    
    Note: Column widths are now handled via Great Tables cols_width() API.
    """
    return f"""
        #allocation-table-main {{ margin: 0 !important; padding: 0 !important; border: none !important; }}
        #allocation-table-main .gt_table {{ width: 100% !important; table-layout: fixed !important; margin: 0 !important; padding: 0 !important; border: none !important; }}
        #allocation-table-main .gt_table table {{ width: 100% !important; table-layout: fixed !important; margin: 0 !important; border-collapse: collapse !important; border: none !important; border-spacing: 0 !important; }}
        #allocation-table-main .gt_table thead {{ border: none !important; }}
        #allocation-table-main .gt_table thead th {{ padding-top: 12px !important; padding-bottom: 12px !important; padding-left: 12px !important; padding-right: 12px !important; border: none !important; border-bottom: none !important; border-top: none !important; border-left: none !important; border-right: none !important; }}
        #allocation-table-main .gt_table tbody {{ border: none !important; }}
        #allocation-table-main .gt_table tbody tr td {{ padding-top: 5px !important; padding-bottom: 5px !important; border: none !important; border-bottom: none !important; border-top: none !important; border-left: none !important; border-right: none !important; }}
        #allocation-table-main .gt_table thead th:first-child {{ padding-top: 8px !important; }}
        #allocation-table-main .gt_table tbody tr:last-child td {{ padding-bottom: 8px !important; }}
        #allocation-table-main .gt_table tbody tr {{ height: auto !important; border: none !important; }}
        #allocation-table-main .gt_table table td, #allocation-table-main .gt_table table th {{ border: none !important; border-width: 0 !important; outline: none !important; }}
        #allocation-table-main .gt_table * {{ border: none !important; border-width: 0 !important; outline: none !important; }}
        #allocation-table-main .gt_table table, #allocation-table-main .gt_table table * {{ border: none !important; border-width: 0 !important; }}
        /* Column widths now handled via Great Tables cols_width() API */
        /* Text alignment handled via Great Tables cols_align() API */
        /* Note: Indentation and spacing handled via Great Tables style.css() API */
    """


def get_allocation_table_summary_css(summary_metric_col_width: str, equity_col_width: str) -> str:
    """Generate CSS for the summary allocation table."""
    return f"""
        #allocation-table-summary .gt_table {{ width: 100% !important; table-layout: fixed !important; }}
        #allocation-table-summary .gt_table table {{ width: 100% !important; table-layout: fixed !important; border-collapse: collapse !important; }}
        #allocation-table-summary .gt_table thead th {{ padding-top: 12px !important; padding-bottom: 12px !important; border: none !important; border-bottom: none !important; border-top: none !important; }}
        #allocation-table-summary .gt_table tbody tr td {{ padding-top: 7px !important; padding-bottom: 7px !important; border: none !important; border-bottom: none !important; border-top: none !important; }}
        #allocation-table-summary .gt_table tbody tr {{ border: none !important; }}
        #allocation-table-summary .gt_table table td, #allocation-table-summary .gt_table table th {{ border: none !important; }}
        #allocation-table-summary .gt_table thead th:first-child {{ width: {summary_metric_col_width} !important; }}
        #allocation-table-summary .gt_table tbody td:first-child {{ width: {summary_metric_col_width} !important; }}
        #allocation-table-summary .gt_table thead th:not(:first-child) {{ width: {equity_col_width} !important; text-align: center !important; }}
        #allocation-table-summary .gt_table tbody td:not(:first-child) {{ width: {equity_col_width} !important; text-align: center !important; }}
    """


# =============================================================================
# STREAMLIT CUSTOM CSS
# Note: Most styling is now handled by .streamlit/config.toml, but this is
# kept for backward compatibility or additional customizations if needed.
# =============================================================================
STREAMLIT_CUSTOM_CSS = f"""
{GOOGLE_FONTS_IMPORT}

/* Apply brand fonts */
html, body, [class*="st-"] {{
    font-family: {FONTS["body"]};
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: {FONTS["headline"]};
    color: {PRIMARY["charcoal"]};
}}

/* Primary accent color */
.stButton > button {{
    background-color: {PRIMARY["raspberry"]};
    color: {PRIMARY["white"]};
    border: none;
}}

.stButton > button:hover {{
    background-color: {PRIMARY["dark_raspberry"]};
}}

/* Links */
a {{
    color: {PRIMARY["raspberry"]};
}}

a:hover {{
    color: {PRIMARY["dark_raspberry"]};
}}
"""
