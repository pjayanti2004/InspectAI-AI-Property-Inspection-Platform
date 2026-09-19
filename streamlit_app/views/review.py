"""Step 3 — Review page for the InspectAI inspection wizard.

Displays all entered property details and uploaded image previews.
User confirms to start inspection or goes back to edit.
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
from streamlit_app.utils.constants import WIZARD_STEPS
from streamlit_app.utils.session_manager import (
    get_property_data,
    get_uploaded_files,
    set_inspection_step,
    get_inspection_step,
)


def render_review():
    """Render the review step — shows all property details and uploaded files."""
    inject_custom_css()
    init_page_config()

    property_data = get_property_data()
    uploaded_files = get_uploaded_files()
    current_step = get_inspection_step()

    # If no data, send back to step 1
    if not property_data and not uploaded_files:
        st.warning("No inspection data found. Please start a new inspection.")
        if st.button("← Go to Property Details"):
            set_inspection_step(1)
            st.session_state["current_page"] = "new_inspection"
            st.rerun()
        return

    render_header(
        title="Review Inspection",
        subtitle="Step 3 of 5 — Verify your details before starting",
        icon="👁️",
    )

    # Wizard stepper
    render_wizard_stepper(current_step=current_step, steps=WIZARD_STEPS)

    render_html("<div class='mt-3'></div>")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        # Property details summary
        render_html("""
            <div class="card">
                <h3 style="margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">
                    📋 Property Details
                </h3>
            </div>
            """,
        )

        if property_data:
            _render_detail_rows(property_data)
        else:
            render_info_box("No property details entered.", box_type="info")

    with col_right:
        # Uploaded images summary
        render_html(
            """
            <div class="card">
                <h3 style="margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">
                    📷 Uploaded Images
                </h3>
            </div>
            """,
        )

        if uploaded_files:
            render_html(
                f"""
                <div style="
                    padding: 0.75rem 1rem;
                    margin: 1rem 0 0.75rem;
                    background: rgba(16, 185, 129, 0.08);
                    border: 1px solid rgba(16, 185, 129, 0.2);
                    border-radius: 8px;
                ">
                    <span style="color: #F1F5F9; font-weight: 600;">
                        {len(uploaded_files)} image{'s' if len(uploaded_files) != 1 else ''} ready for analysis
                    </span>
                </div>
                """,
            )

            # Show small thumbnails in a grid
            num_cols = 3
            rows = [uploaded_files[i:i + num_cols] for i in range(0, len(uploaded_files), num_cols)]
            for row in rows:
                cols = st.columns(num_cols, gap="small")
                for col, file in zip(cols, row):
                    with col:
                        size_kb = file.size / 1024
                        size_text = f"{size_kb:.0f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"
                        st.image(file, use_container_width=True)
                        st.caption(f"`{file.name}` · {size_text}")
        else:
            render_info_box("No images uploaded.", box_type="warning")

    render_html("<div class='mt-4'></div>")

    # ── Wizard navigation ───────────────────────────────────────────────────
    back_clicked, next_clicked = render_wizard_nav(
        current_step=3,
        next_label="Start Inspection →",
        back_label="← Back to Upload",
        back_key="step3_back",
        next_key="step3_start",
    )

    if back_clicked:
        set_inspection_step(2)
        st.session_state["current_page"] = "upload"
        st.rerun()

    if next_clicked:
        set_inspection_step(4)
        st.session_state["current_page"] = "processing"
        st.rerun()


def _render_detail_rows(data: dict):
    """Render labeled detail rows from a property data dict.

    Args:
        data: Property data dict from session state.
    """
    field_display = {
        "property_name": ("Property Name", "🏠"),
        "property_type": ("Property Type", "🏢"),
        "address": ("Address", "📍"),
        "inspector_name": ("Inspector Name", "👤"),
        "inspection_date": ("Inspection Date", "📅"),
        "notes": ("Notes", "📝"),
    }

    for key, (label, icon) in field_display.items():
        value = data.get(key, "")
        # Only show notes if non-empty
        if key == "notes" and not value:
            continue
        render_detail_row(label, value, icon=icon)


# Import render_detail_row from ui_components (circular-safe because the
# function doesn't import anything from this module).
from streamlit_app.components.ui_components import render_detail_row  # noqa: E402
