"""
Mercer Advisors Brand Guidelines Configuration
===============================================
Centralized styling and color palettes for charts, UI elements, and typography.
Based on official Mercer Advisors brand guidelines.
"""

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
# SERIES/CATEGORY COLORS (for dataframe tags and filters)
# =============================================================================
SERIES_COLORS = {
    "Multifactor": PRIMARY["raspberry"],
    "Market": SECONDARY["iris"],
    "Income": TERTIARY["spring"],
    "Equity": TERTIARY["azure"],
    "Fixed Income": TERTIARY["dark_azure"],
    "Cash": PRIMARY["charcoal"],
    "Alternative": TERTIARY["gold"],
    "Special Situation": TERTIARY["dark_gold"],
    "Blended": SPECIAL["gray"],
}

# =============================================================================
# TYPOGRAPHY
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
# PLOTLY CHART LAYOUT DEFAULTS
# =============================================================================
def get_chart_layout(title: str = "", height: int = 400) -> dict:
    """Get default Plotly chart layout with brand styling."""
    return {
        "title": {
            "text": title,
            "font": {"family": FONTS["headline"], "color": PRIMARY["charcoal"]},
        },
        "font": {"family": FONTS["body"], "color": PRIMARY["charcoal"]},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "height": height,
        "margin": {"l": 40, "r": 40, "t": 40 if title else 0, "b": 40},
    }


# =============================================================================
# STREAMLIT CUSTOM CSS
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
