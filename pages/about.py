import streamlit as st

from components import render_footer, render_reference_data
from components.cards import _load_explanation_card
from pages.search import EXPLANATION_CARD_UPDATE_DATE

st.markdown("# About the Platform")
st.caption(f"last updated: {EXPLANATION_CARD_UPDATE_DATE}")

# Display the About text directly (not in an expander)
explanation_text: str = _load_explanation_card()
st.markdown(explanation_text)

# Render reference data sections (Abbreviations, TLH, Equivalents, Under Development)
st.markdown("### Additional Information")
render_reference_data()

# Footer
render_footer()
