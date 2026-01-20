"""Roadmap page - displays upcoming features and enhancements for AIM."""

import streamlit as st
from components import render_footer

st.set_page_config(page_title="Roadmap", layout="wide")

st.markdown("# 🗺️ AIM Roadmap")
st.markdown("Upcoming features and enhancements planned for the Aspen Investing Menu platform.")

st.divider()

# Roadmap items organized by category
roadmap_items = [
    {
        "category": "Core Features",
        "items": [
            "Mission Control",
            "SMA Holdings Analysis Tool",
            "Blended Models",
            "Portfolio Review Scorecard",
        ]
    },
    {
        "category": "AIM Enhancements",
        "items": [
            "IPS Filters for AIM",
            "Private Markets for AIM",
            "Model Builder for AIM",
            "Tracking Error for AIM",
            "Reference Benchmark for AIM",
            "Factor Analysis for AIM",
            "MPT stats for AIM",
            "Performance for AIM",
        ]
    },
    {
        "category": "Platform Features",
        "items": [
            "Model Change History",
            "PDF Download Report",
        ]
    }
]

# Display roadmap items
for category in roadmap_items:
    st.markdown(f"### {category['category']}")
    
    # Create columns for better layout (2 columns)
    cols = st.columns(2)
    
    for idx, item in enumerate(category['items']):
        col = cols[idx % 2]
        with col:
            st.markdown(
                f"""
                <div style="
                    background-color: #f8f9fa;
                    border-left: 4px solid #0066cc;
                    padding: 16px;
                    margin-bottom: 12px;
                    border-radius: 4px;
                ">
                    <p style="margin: 0; font-size: 16px; font-weight: 500;">
                        ✓ {item}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    st.markdown("<br>", unsafe_allow_html=True)

st.divider()

# Status legend
st.markdown("### Status Legend")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div style="
            background-color: #e7f3ff;
            padding: 12px;
            border-radius: 4px;
            text-align: center;
        ">
            <strong>Planned</strong><br>
            <small>Features in planning phase</small>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div style="
            background-color: #fff4e6;
            padding: 12px;
            border-radius: 4px;
            text-align: center;
        ">
            <strong>In Development</strong><br>
            <small>Currently being built</small>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div style="
            background-color: #e6f7e6;
            padding: 12px;
            border-radius: 4px;
            text-align: center;
        ">
            <strong>Available</strong><br>
            <small>Ready to use</small>
        </div>
        """,
        unsafe_allow_html=True
    )

# Footer
render_footer()
