"""Release Notes page - displays version history and release information."""

import streamlit as st

from components import render_footer

RELEASE_NOTES_UPDATE_DATE = "2026-01-24"


def render_release(
    version: str,
    date: str,
    features: list[str],
    improvements: list[str] | None = None,
    fixes: list[str] | None = None,
) -> None:
    """Render a release section with version, date, and changes."""
    st.markdown(f"### Version {version}")
    st.caption(f"Released: {date}")

    if features:
        st.markdown("#### :material/auto_awesome: New Features")
        for feature in features:
            st.markdown(f"- {feature}")

    if improvements:
        st.markdown("#### :material/trending_up: Improvements")
        for improvement in improvements:
            st.markdown(f"- {improvement}")

    if fixes:
        st.markdown("#### :material/bug_report: Bug Fixes")
        for fix in fixes:
            st.markdown(f"- {fix}")


st.markdown("# :material/new_releases: Release Notes")
st.caption(f"last updated: {RELEASE_NOTES_UPDATE_DATE}")

st.markdown(
    "Welcome to the Aspen Investment Menu (AIM)! This is our initial release, providing a comprehensive platform for exploring and discovering investment strategies."
)

# AIM 2.0.0 Release
render_release(
    version="2.0.0",
    date="January 24, 2026",
    features=[
        "Initial release of the Aspen Investment Menu (AIM 2.0) with goal of 1-to-1 conversion from existing Excel spreadsheet",
        "Combined search, filter, and card-based navigation for existing Orion strategies",
        "View allocation table and strategy information including account minimums, expense ratios, yields, and equity percentages",
    ],
)

# Footer
render_footer()
