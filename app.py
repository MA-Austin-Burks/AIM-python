from datetime import datetime

import polars as pl
import streamlit as st
from streamlit_extras.bottom_container import bottom

from filters import build_filter_expression
from formatting import COLUMN_CONFIG, format_display_dataframe
from sidebar import render_sidebar_filters
from tabs import render_tabs

# Constants
STRATEGIES_CSV_FILE = "data/strategies.csv"
CACHE_TTL_SECONDS = 3600

# Page configuration
st.set_page_config(
    page_title="Aspen Investing Menu",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
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
    except Exception as e:
        error_msg: str = (
            f"{STRATEGIES_CSV_FILE} not found. Please run the data preparation script first."
            if isinstance(e, FileNotFoundError)
            else f"Error loading {STRATEGIES_CSV_FILE}: {str(e)}"
        )
        st.error(error_msg)
        st.stop()
        raise SystemExit()  # Explicitly raise to satisfy type checker


# Initialize session state for selected strategy
if "selected_strategy" not in st.session_state:
    st.session_state.selected_strategy = None

# Load pre-processed data
strategies_df = load_prepared_strategies_data()

# Sidebar filters
filters = render_sidebar_filters(strategies_df)

# Build and apply filter expression
filter_expr = build_filter_expression(filters, strategies_df)
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

render_tabs(st.session_state.selected_strategy)

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
