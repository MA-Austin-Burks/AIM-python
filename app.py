import os

import streamlit as st

st.set_page_config(
    page_title="Aspen Investing Menu",
    layout="wide",
    initial_sidebar_state=250,
    menu_items={
        "Report a Bug": "mailto:aburks@merceradvisors.com",
    },
)

# Add Mercer Advisors logo
st.logo("styles/Mercer_Advisors_Logo_blk.png", size="large")

# Set up navigation with pages
pages = {
    "Aspen Investing Menu": [
        st.Page("pages/search.py", title="Search", icon=":material/dashboard:", url_path="search", default=True),
        st.Page("pages/about.py", title="About", icon=":material/info:", url_path="about"),
    ],
}

# Create navigation and run the current page
pg = st.navigation(pages, position="top", expanded=True)

pg.run()
