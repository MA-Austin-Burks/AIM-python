import warnings
from datetime import datetime

import polars as pl
import streamlit as st
from streamlit_extras.bottom_container import bottom

from filters import build_filter_expression
from formatting import COLUMN_CONFIG, format_display_dataframe
from sidebar import render_sidebar_filters
from tabs import render_tabs
from utils.performance import PerformanceMonitor, time_operation

# Constants
STRATEGIES_CSV_FILE = "data/strategies.csv"
CACHE_TTL_SECONDS = 3600

# Suppress Streamlit ScriptRunContext warnings (harmless threading warnings)
warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")

# Page configuration
st.set_page_config(
    page_title="Aspen Investing Menu",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS for Merriweather title only - let config.toml handle colors via primaryColor
st.markdown(
    """
    <style>
    /* Merriweather for Streamlit title (h1) only */
    h1, .stApp h1, .stMarkdown h1 {
        font-family: 'Merriweather', serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

now = datetime.today().strftime("%Y-%m-%d")

st.title("Aspen Investing Menu")
st.caption(f"Last updated: {now}")
st.divider()


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_prepared_strategies_data() -> pl.DataFrame:
    """
    Load pre-processed strategies data with recommended column already joined.

    Returns:
        pl.DataFrame: The strategies dataframe loaded from CSV

    Raises:
        SystemExit: If the CSV file is not found or cannot be read
    """
    try:
        return pl.read_csv(STRATEGIES_CSV_FILE, null_values=["NA"])
    except FileNotFoundError:
        st.error(
            f"{STRATEGIES_CSV_FILE} not found. Please run the data preparation script first."
        )
        st.stop()
        return pl.DataFrame()  # type: ignore[unreachable]  # Never reached, st.stop() raises SystemExit
    except Exception as e:
        st.error(f"Error loading {STRATEGIES_CSV_FILE}: {str(e)}")
        st.stop()
        return pl.DataFrame()  # type: ignore[unreachable]  # Never reached, st.stop() raises SystemExit


# Initialize session state for selected strategy
if "selected_strategy" not in st.session_state:
    st.session_state.selected_strategy = None

# Initialize performance monitoring
if "enable_performance_monitoring" not in st.session_state:
    st.session_state.enable_performance_monitoring = False

# Create performance monitor (always tracks, but only displays if enabled)
monitor = PerformanceMonitor()

# Load pre-processed data
with time_operation("load_data", monitor):
    strategies_df = load_prepared_strategies_data()

# Sidebar filters
with time_operation("render_sidebar", monitor):
    filters = render_sidebar_filters(strategies_df)

# Build and apply filter expression
with time_operation("build_filter", monitor):
    filter_expr = build_filter_expression(filters, strategies_df)

with time_operation("apply_filter", monitor):
    filtered_strategies = strategies_df.filter(filter_expr)

# Sort by Equity % descending (divide by 100), then by Recommended descending
filtered_strategies = (
    filtered_strategies.with_columns((pl.col("Equity %") / 100).alias("_equity_sort"))
    .sort(["Recommended", "_equity_sort"], descending=[True, True], nulls_last=True)
    .drop("_equity_sort")
)

# Display results with brand styling
st.markdown(
    f"<p style=\"color: #454759; font-family: 'IBM Plex Sans', sans-serif; font-weight: 500;\">"
    f"<strong>{len(filtered_strategies)} strategies returned</strong></p>",
    unsafe_allow_html=True,
)

# Format and display dataframe
with time_operation("format_dataframe", monitor):
    display_df = format_display_dataframe(filtered_strategies)

selected_rows = st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config=COLUMN_CONFIG,
)

st.divider()

# Update session state with selected strategy
with time_operation("update_selection", monitor):
    if selected_rows.selection.rows:
        selected_idx = selected_rows.selection.rows[0]
        st.session_state.selected_strategy = filtered_strategies.select("strategy").row(
            selected_idx, named=True
        )["strategy"]
    else:
        # Keep previous selection if available, otherwise None
        # Use Polars filter instead of converting to list (more efficient)
        if st.session_state.selected_strategy:
            exists = (
                filtered_strategies.filter(
                    pl.col("strategy") == st.session_state.selected_strategy
                ).height
                > 0
            )
            if not exists:
                st.session_state.selected_strategy = None

with time_operation("render_tabs", monitor):
    render_tabs(st.session_state.selected_strategy)

# Performance monitoring panel will be rendered in sidebar if enabled
# (handled by sidebar.py)

# Footer
with bottom():
    st.divider()
    st.markdown(
        """
            <div style="text-align: center; color: #747583; font-family: 'IBM Plex Sans', sans-serif;">
                <p><strong style="color: #454759;">Aspen Investing Menu</strong></p>
                <p>© 2025 Mercer Advisors.</p>
            </div>
            """,
        unsafe_allow_html=True,
    )
