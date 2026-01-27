import streamlit as st


def render_footer() -> None:
    """Render the footer with copyright and bug report link."""
    st.markdown("---")

    # Copyright footer
    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
    with footer_col2:
        st.markdown(
            """
            <div style="text-align: center; padding: 0.25rem 0; color: #454759; font-size: 0.875rem;">
                © 2026 Mercer Advisors. All rights reserved. | 
                <a href="mailto:aburks@merceradvisors.com" style="color: #C00686; text-decoration: none;">Report a Bug</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
