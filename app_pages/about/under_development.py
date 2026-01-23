"""Under Development page - displays features currently under development."""

import streamlit as st

from components import render_footer


@st.cache_data(ttl=3600)
def _load_under_development() -> dict[str, list[str]]:
    """Load under development text file and parse into sections (cached for 1 hour)."""
    with open("app_pages/about/data/under_development.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    sections = {}
    current_section = None
    current_items = []
    
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("###"):
            # Save previous section if exists
            if current_section:
                sections[current_section] = current_items
            # Start new section
            current_section = line.replace("###", "").strip()
            current_items = []
        elif line.startswith("-") and current_section:
            current_items.append(line.replace("-", "").strip())
    
    # Save last section
    if current_section:
        sections[current_section] = current_items
    
    return sections


st.markdown("# :material/construction: Under Development")
st.caption("last updated: 2026-01-17")

sections: dict[str, list[str]] = _load_under_development()

# Create three columns
col1, col2, col3 = st.columns(3)

# Display each section in its own column
with col1:
    if "Risk-Based Strategies" in sections:
        st.markdown("### Risk-Based Strategies")
        for item in sections["Risk-Based Strategies"]:
            st.markdown(f"- {item}")

with col2:
    if "Asset Class Strategies" in sections:
        st.markdown("### Asset Class Strategies")
        for item in sections["Asset Class Strategies"]:
            st.markdown(f"- {item}")

with col3:
    if "Special Situation Strategies" in sections:
        st.markdown("### Special Situation Strategies")
        for item in sections["Special Situation Strategies"]:
            st.markdown(f"- {item}")

# Footer
render_footer()
