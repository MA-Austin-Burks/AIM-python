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
st.logo("utils/styles/Mercer_Advisors_Logo_blk.png", size="large")

# Set up navigation with pages
pages = {
    "Aspen Investing Menu": [
        st.Page("pages/search/search.py", title="Search", icon=":material/dashboard:", url_path="search", default=True),
    ],
    "About": [
        st.Page("pages/about/about_platform.py", title="About the Platform", icon=":material/description:", url_path="about"),
        st.Page("pages/about/abbreviations.py", title="Abbreviations", icon=":material/menu_book:", url_path="abbreviations"),
        st.Page("pages/about/tax_loss_harvesting.py", title="Tax-Loss Harvesting", icon=":material/money_off:", url_path="tax-loss-harvesting"),
        st.Page("pages/about/equivalents.py", title="Equivalents", icon=":material/equal:", url_path="equivalents"),
        st.Page("pages/about/under_development.py", title="Under Development", icon=":material/construction:", url_path="under-development"),
    ],
}

# Create navigation and run the current page
pg = st.navigation(pages, position="top", expanded=True)

pg.run()
