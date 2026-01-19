import streamlit as st

from components import render_reference_data
from components.constants import EXPLANATION_CARD_UPDATE_DATE

st.markdown("# About the Platform")
st.caption(f"last updated: {EXPLANATION_CARD_UPDATE_DATE}")

# Display the About text directly (not in an expander)
with open("data/explanation_card.txt", "r", encoding="utf-8") as f:
    st.markdown(f.read())

# Render reference data sections (Abbreviations, TLH, Equivalents, Under Development)
st.markdown("### Additional Information")
render_reference_data()
