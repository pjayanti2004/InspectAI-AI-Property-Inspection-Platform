"""Step 1 — Property Details page for the InspectAI inspection wizard.

Collects all property information required before image upload.
Advances to the upload step only when required fields are filled.
"""
import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_header,
    render_html,
    render_wizard_stepper,
    render_wizard_nav,
    render_info_box,
)
from streamlit_app.utils.constants import PROPERTY_TYPES, WIZARD_STEPS
from streamlit_app.utils.session_manager import (
    get_property_data,
    save_property_data,
    get_inspection_step,
)


def render_property_details():
    """Render the property details step of the inspection wizard."""
    current_step = get_inspection_step()

    render_header(
        title="New Inspection",
        subtitle="Step 1 of 5 — Property Details",
        icon="🔍",
    )

    # Wizard stepper
    render_wizard_stepper(current_step=current_step, steps=WIZARD_STEPS)

    render_html("<div class='mt-3'></div>")

    # Pre-fill with saved data if returning from review
    saved_data = get_property_data()
    form_data = saved_data.copy() if saved_data else {}

    # Form card
    render_html("""
        <div class="card">
            <h3 style="margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">
                🏠 Property Information
            </h3>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 1.5rem;">
                Provide details about the property you want to inspect.
                Fields marked with * are required.
            </p>
        </div>
        """,
    )

    with st.form("property_details_form", clear_on_submit=False, border=True):
        col1, col2 = st.columns(2)

        with col1:
            property_name = st.text_input(
                "Property Name *",
                value=form_data.get("property_name", ""),
                placeholder="e.g., Sunset Apartments, Unit 4B",
                help="A descriptive name for this property",
            )
            property_type = st.selectbox(
                "Property Type *",
                options=PROPERTY_TYPES,
                index=PROPERTY_TYPES.index(form_data["property_type"]) if form_data.get("property_type") in PROPERTY_TYPES else 0,
            )
            address = st.text_input(
                "Address *",
                value=form_data.get("address", ""),
                placeholder="e.g., 42 Maple Street, Mumbai",
                help="Full address of the property",
            )

        with col2:
            inspector_name = st.text_input(
                "Inspector Name *",
                value=form_data.get("inspector_name", ""),
                placeholder="Your full name",
                help="Name of the person conducting the inspection",
            )
            inspection_date = st.date_input(
                "Inspection Date *",
                value=form_data.get("inspection_date") or st.session_state.get("_today"),
                help="Date of the inspection",
            )
            notes = st.text_area(
                "Notes",
                value=form_data.get("notes", ""),
                placeholder="Any additional observations, context, or specific areas to focus on...",
                height=120,
            )

        # Validation
        form_valid = (
            bool(property_name.strip())
            and bool(property_type)
            and bool(address.strip())
            and bool(inspector_name.strip())
        )

        render_html("<div class='mt-2'></div>")

        # Navigation buttons (form-aware: uses form_submit_button)
        _, next_clicked = render_wizard_nav(
            current_step=1,
            next_label="Continue to Upload Images →",
            back_label="← Cancel",
            next_disabled=False,
            show_back=True,
            next_key="step1_next",
            back_key="step1_cancel",
            submit=True,
        )

        if next_clicked and form_valid:
            data = {
                "property_name": property_name.strip(),
                "property_type": property_type,
                "address": address.strip(),
                "inspector_name": inspector_name.strip(),
                "inspection_date": str(inspection_date),
                "notes": notes.strip(),
            }
            save_property_data(data)
            st.session_state["current_page"] = "upload"
            st.rerun()

    if not form_valid:
        render_info_box(
            "Please fill in all required fields (*) to continue.",
            box_type="warning",
        )
