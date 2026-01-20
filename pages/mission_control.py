"""Mission Control page wrapper - tries to load from mission_control folder, falls back if not available."""

import streamlit as st
from components import render_footer

st.set_page_config(page_title="Mission Control", layout="wide")

# Try to import and run the mission control module
try:
    # Import the mission control module
    from mission_control.mission_control_views import (
        render_aum_by_classification,
        render_aum_by_manager,
        render_aum_by_product,
        render_aum_by_sleeve,
        render_aum_by_strategy,
        render_firmwide_overview,
    )
    
    # Header section
    with st.container(horizontal=True, vertical_alignment="bottom"):
        st.header("Mission Control", width="stretch")
        st.markdown(":small[Firmwide AUM Dashboard]", width="stretch")

    # View selection
    view = st.segmented_control(
        "View",
        [
            "Firmwide Overview",
            "AUM by Product",
            "AUM by Manager",
            "AUM by Classification",
            "AUM by Strategy",
            "AUM by Sleeve",
        ],
        default="Firmwide Overview",
        label_visibility="collapsed"
    )

    # Render selected view
    if view == "Firmwide Overview":
        render_firmwide_overview()
    elif view == "AUM by Product":
        render_aum_by_product()
    elif view == "AUM by Manager":
        render_aum_by_manager()
    elif view == "AUM by Classification":
        render_aum_by_classification()
    elif view == "AUM by Strategy":
        render_aum_by_strategy()
    elif view == "AUM by Sleeve":
        render_aum_by_sleeve()

except (ImportError, ModuleNotFoundError, FileNotFoundError) as e:
    # Fallback: show "in progress" message
    st.markdown("# Mission Control")
    st.markdown("This page is under development.")
    st.info("Mission Control module not available. The dashboard is currently being developed.")

# Footer
render_footer()
