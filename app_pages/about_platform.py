"""About the Platform page - main platform information and series comparison."""

import streamlit as st

from components import render_footer

EXPLANATION_CARD_UPDATE_DATE = "2026-01-17"


@st.cache_data(ttl=3600)
def _load_explanation_card() -> str:
    """Load explanation card text file (cached for 1 hour)."""
    with open("app_pages/data/explanation_card.txt", "r", encoding="utf-8") as f:
        return f.read()


st.markdown("# :material/description: About the Platform")
st.caption(f"last updated: {EXPLANATION_CARD_UPDATE_DATE}")

# Display the About text directly (not in an expander)
explanation_text: str = _load_explanation_card()
st.markdown(explanation_text)

# Series Comparison Table
st.markdown("### Series Comparison")

# Create three columns for the series comparison
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Market Series")
    st.markdown("**What Does it Do?**")
    st.markdown(
        "Portfolios are designed to provide low-cost, highly diversified global market exposure."
    )
    st.markdown("**Who is it For?**")
    st.markdown(
        "Investors looking for performance and investment exposure that closely resembles the broad market, or those that do not like to see performance diverging from the market."
    )
    st.markdown(
        "**Client Examples:** ERISA plans (Defined Contribution), clients adverse to tracking error."
    )

with col2:
    st.markdown("#### Multifactor Series")
    st.markdown("**What Does it Do?**")
    st.markdown(
        "Portfolios are designed to utilize the latest academic investment research to systematically capture higher expected returns through a factor tilted globally diversified portfolio."
    )
    st.markdown("**Who is it For?**")
    st.markdown(
        "Long-term investors willing to tolerate performance deviations from the market (tracking error) in pursuit of greater long-term returns."
    )
    st.markdown(
        '**Client Examples:** "Engineering" types, those seeking long-term outperformance.'
    )

with col3:
    st.markdown("#### Income Series")
    st.markdown("**What Does it Do?**")
    st.markdown(
        "Portfolios are designed to provide enhanced and consistent income through exposure to high dividend global equities and high yielding global fixed income."
    )
    st.markdown("**Who is it For?**")
    st.markdown("Investors requiring income for current or specified cash flow needs.")
    st.markdown(
        '**Client Examples:** Retirees, "Red Zone" clients, and certain Trusts/Institutions'
    )

# Footer
render_footer()
