from datetime import datetime

import streamlit as st

from components.constants import DEFAULT_VIEW_MODE, VIEW_MODE_KEY


def _apply_custom_styles() -> None:
    """Apply custom CSS for sidebar, brand fonts, and layout tweaks."""
    from styles.branding import STREAMLIT_CUSTOM_CSS
    
    # Combine all custom styles
    custom_css = f"""
    <style>
        /* Fixed sidebar width and hide collapse button */
        [data-testid="stSidebar"] {{
            min-width: 500px;
            max-width: 500px;
        }}
        [data-testid="stSidebar"] button[kind="headerNoPadding"] {{
            display: none;
        }}
        [data-testid="collapsedControl"] {{
            display: none;
        }}
        
        /* Brand styles */
        {STREAMLIT_CUSTOM_CSS}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_page_header() -> None:
    st.set_page_config(
        page_title="Aspen Investing Menu",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Apply all custom styles (sidebar, brand, layout)
    _apply_custom_styles()

    col_title, col_toggle = st.columns([3, 1])
    with col_title:
        st.title("Aspen Investing Menu")
        st.caption(f"Last updated: {datetime.today().strftime(format='%Y-%m-%d')}")
    with col_toggle:
        st.space("small")  # Vertical alignment
        if VIEW_MODE_KEY not in st.session_state:
            st.session_state[VIEW_MODE_KEY] = DEFAULT_VIEW_MODE
        
        # Use toggle: True = Card view, False = Table view
        is_card_view = st.session_state[VIEW_MODE_KEY] == "card"
        card_view_toggle = st.toggle(
            "Card View",
            value=is_card_view,
            label_visibility="collapsed",
        )
        st.session_state[VIEW_MODE_KEY] = "card" if card_view_toggle else "table"
    st.divider()
