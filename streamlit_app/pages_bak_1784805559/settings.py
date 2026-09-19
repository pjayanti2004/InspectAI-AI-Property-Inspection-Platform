"""Settings page — Manage user preferences and account settings.

(Database integration and authentication will be added in Phase 3.)
"""
import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_header,
    render_info_box,
)


def render_settings():
    """Render the settings page."""
    inject_custom_css()
    init_page_config()

    render_header(
        title="Settings",
        subtitle="Manage your preferences and account settings",
        icon="⚙️",
    )

    # Settings tabs
    tab1, tab2, tab3 = st.tabs(["👤 Account", "⚙️ Preferences", "🔔 Notifications"])

    with tab1:
        _render_account_settings()

    with tab2:
        _render_preferences()

    with tab3:
        _render_notifications()


def _render_account_settings():
    """Render account settings form."""
    st.markdown(
        """
        <div class="card">
            <h3 style="margin-top: 0;">Profile Information</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 1.5rem;">
                Update your personal information.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("account_settings_form"):
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input("Full Name", value="User", placeholder="Your name")
            email = st.text_input("Email", value="user@example.com", placeholder="your@email.com")
            phone = st.text_input("Phone", value="+91 98765 43210", placeholder="+91 XXXXXXXXXX")

        with col2:
            company = st.text_input("Company", value="", placeholder="Company name (optional)")
            role = st.selectbox(
                "Role",
                ["Homeowner", "Property Inspector", "Civil Engineer", "Builder", "Real Estate"],
                index=0,
            )
            location = st.text_input("Location", value="Mumbai, India", placeholder="City, Country")

        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
            render_info_box("Profile updated! (Database coming in Phase 3)", box_type="success")

    st.markdown("<div class='mt-3'></div>", unsafe_allow_html=True)

    # Danger zone
    st.markdown(
        """
        <div class="card" style="border-color: rgba(239, 68, 68, 0.3);">
            <h3 style="margin-top: 0; color: #EF4444;">⚠️ Danger Zone</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 1rem;">
                These actions are irreversible. Please proceed with caution.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Delete All Data", type="secondary", use_container_width=True):
            render_info_box("Data deletion will be available when database is integrated.", box_type="error")
    with col2:
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            render_info_box("Authentication will be implemented in Phase 3.", box_type="warning")


def _render_preferences():
    """Render application preferences."""
    st.markdown(
        """
        <div class="card">
            <h3 style="margin-top: 0;">Display Preferences</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("preferences_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.selectbox("Language", ["English", "Hindi", "Spanish", "French"], index=0)
            st.selectbox("Currency", ["INR (₹)", "USD ($)", "EUR (€)"], index=0)
            st.selectbox("Date Format", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"], index=0)

        with col2:
            st.selectbox("Severity Scale", ["4-Level (Low/Med/High/Critical)", "5-Level"], index=0)
            st.selectbox("Report Template", ["Standard", "Detailed", "Executive Summary"], index=0)
            st.checkbox("Show Confidence Scores", value=True)
            st.checkbox("Include Cost Estimates", value=True)

        if st.form_submit_button("Save Preferences", type="primary", use_container_width=True):
            render_info_box("Preferences saved! (Persistence coming in Phase 3)", box_type="success")


def _render_notifications():
    """Render notification settings."""
    st.markdown(
        """
        <div class="card">
            <h3 style="margin-top: 0;">Notification Settings</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 1.5rem;">
                Configure how you receive notifications.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.checkbox("Email notifications for new inspections", value=True)
    st.checkbox("Email notifications for critical findings", value=True)
    st.checkbox("Weekly summary report", value=False)
    st.checkbox("In-app notifications", value=True)

    if st.button("Save Notification Settings", type="primary", use_container_width=True):
        render_info_box("Notification settings saved! (Coming in Phase 3)", box_type="success")
