# =============================================================================
# PRIMARY PALETTE
# =============================================================================
PRIMARY: dict[str, str] = {
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
SECONDARY: dict[str, str] = {
    "pale_iris": "#E9E9FF",
    "light_iris": "#CFCCFF",
    "medium_iris": "#A5A0EF",
    "iris": "#7673DC",
    "dark_iris": "#50439B",
}

# =============================================================================
# TERTIARY PALETTE
# =============================================================================
TERTIARY: dict[str, str] = {
    "pale_azure": "#D5EEFF",
    "light_azure": "#A4D4FF",
    "medium_azure": "#6DB7FF",
    "azure": "#1E90FF",
    "dark_azure": "#225CBD",
    "pale_spring": "#BDFFDF",
    "light_spring": "#89F2C3",
    "medium_spring": "#47DEA2",
    "spring": "#00C48C",
    "dark_spring": "#00826B",
    "cream": "#FFF5E5",
    "light_gold": "#FDDB9A",
    "gold": "#F9A602",
    "dark_gold": "#CC8700",
    "light_red": "#FA696E",
    "red": "#DA0028",
}

# =============================================================================
# SPECIAL USE PALETTE
# =============================================================================
SPECIAL: dict[str, str] = {
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
CHART_COLORS_PRIMARY: list[str] = [
    PRIMARY["raspberry"],  # #C00686
    SECONDARY["iris"],  # #7673DC
    TERTIARY["azure"],  # #1E90FF
    TERTIARY["spring"],  # #00C48C
    TERTIARY["gold"],  # #F9A602
    PRIMARY["charcoal"],  # #454759
]

# Extended chart sequence - for charts with more categories
CHART_COLORS_EXTENDED: list[str] = [
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
CHART_COLORS_ALLOCATION: list[str] = [
    TERTIARY["azure"],  # #1E90FF - U.S. stocks
    TERTIARY["spring"],  # #00C48C - Non-U.S. stocks
    TERTIARY["gold"],  # #F9A602 - Bonds
    SECONDARY["iris"],  # #7673DC - Short-term reserves
    PRIMARY["charcoal"],  # #454759 - Other
]

# Sequential palette for gradients (light to dark)
CHART_COLORS_SEQUENTIAL_RASPBERRY: list[str] = [
    SPECIAL["pale_raspberry"],  # #FFD8EF
    SPECIAL["light_raspberry"],  # #FF96D7
    SPECIAL["medium_raspberry"],  # #FC3DB0
    PRIMARY["raspberry"],  # #C00686
    PRIMARY["dark_raspberry"],  # #820361
    SPECIAL["deep_raspberry"],  # #630349
]

CHART_COLORS_SEQUENTIAL_IRIS: list[str] = [
    SECONDARY["pale_iris"],  # #E9E9FF
    SECONDARY["light_iris"],  # #CFCCFF
    SECONDARY["medium_iris"],  # #A5A0EF
    SECONDARY["iris"],  # #7673DC
    SECONDARY["dark_iris"],  # #50439B
]

CHART_COLORS_SEQUENTIAL_AZURE: list[str] = [
    TERTIARY["pale_azure"],  # #D5EEFF
    TERTIARY["light_azure"],  # #A4D4FF
    TERTIARY["medium_azure"],  # #6DB7FF
    TERTIARY["azure"],  # #1E90FF
    TERTIARY["dark_azure"],  # #225CBD
]

# =============================================================================
# STRATEGY COLORS (Primary and Secondary)
# =============================================================================
STRATEGY_COLORS: dict[str, dict[str, str]] = {
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
SUBTYPE_COLORS: dict[str, str] = {
    "Multifactor Series": PRIMARY["raspberry"],
    "Market Series": SECONDARY["iris"],
    "Income Series": PRIMARY["charcoal"],
    "Equity Strategies": TERTIARY["azure"],
    "Fixed Income Strategies": STRATEGY_COLORS["Fixed Income Strategies"]["primary"],
    "Cash Strategies": STRATEGY_COLORS["Cash Strategies"]["primary"],
    "Alternative Strategies": TERTIARY["gold"],
    "Special Situation Strategies": STRATEGY_COLORS["Special Situation Strategies"][
        "primary"
    ],
    "Blended Strategy": SPECIAL["gray"],
}

# =============================================================================
# TYPOGRAPHY
# Note: Fonts are configured in .streamlit/config.toml for Streamlit UI.
# This dictionary is kept for programmatic use in Plotly charts.
# =============================================================================
FONTS: dict[str, str] = {
    "headline": "'Merriweather', Georgia, serif",
    "body": "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
}


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert hex color to RGBA string."""
    h: str = hex_color.lstrip("#")
    r: int = int(h[0:2], 16)
    g: int = int(h[2:4], 16)
    b: int = int(h[4:6], 16)
    return f"rgba({r:d}, {g:d}, {b:d}, {alpha:.2f})"


def get_subtype_color(subtype: str) -> str:
    """Get the color for a strategy based on its subtype."""
    return SUBTYPE_COLORS.get(subtype, PRIMARY["raspberry"])
