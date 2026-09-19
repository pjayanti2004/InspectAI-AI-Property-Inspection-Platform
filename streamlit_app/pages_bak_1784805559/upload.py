"""Step 2 — Image Upload page for the InspectAI inspection wizard.

Allows multiple image upload, shows thumbnail previews, supports removal,
and advances to the review step once at least one image is uploaded.
"""
import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_header,
    render_wizard_stepper,
    render_wizard_nav,
    render_info_box,
    render_empty_state,
)
from streamlit_app.utils.constants import WIZARD_STEPS
from streamlit_app.utils.session_manager import (
    get_property_data,
    save_uploaded_files,
    get_inspection_step,
    set_inspection_step,
)


# ── Constants ────────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png"]
MAX_FILE_SIZE_MB = 10
MAX_IMAGES = 20


def render_image_upload():
    """Render the image upload step of the inspection wizard."""
    inject_custom_css()
    init_page_config()

    # Guard: must have property data to proceed
    property_data = get_property_data()
    if not property_data:
        render_info_box(
            "Please complete the property details first.",
            box_type="warning",
        )
        if st.button("← Go to Property Details"):
            set_inspection_step(1)
            st.session_state["current_page"] = "new_inspection"
            st.rerun()
        return

    current_step = get_inspection_step()

    render_header(
        title="Upload Images",
        subtitle=f"Step 2 of 5 — {property_data.get('property_name', 'Inspection')}",
        icon="📤",
    )

    # Wizard stepper
    render_wizard_stepper(current_step=current_step, steps=WIZARD_STEPS)

    st.markdown("<div class='mt-3'></div>", unsafe_allow_html=True)

    # Section header
    st.markdown(
        f"""
        <div class="card">
            <h3 style="margin-top: 0;">📤 Upload Property Images</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                Upload photos of the property. Supported formats:
                <strong style="color: #F1F5F9;">JPG, JPEG, PNG</strong>.
                Max {MAX_IMAGES} images, {MAX_FILE_SIZE_MB}MB each.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── File uploader ───────────────────────────────────────────────────────
    new_uploads = st.file_uploader(
        "Drag & drop images here, or click to browse",
        type=ALLOWED_EXTENSIONS,
        accept_multiple_files=True,
        key="image_uploader",
        help=f"Upload up to {MAX_IMAGES} JPG, JPEG, or PNG images",
    )

    # Combine previously uploaded files with new ones in this session
    # Streamlit re-creates a fresh list on every rerun, so we just use the
    # latest set of files returned by the uploader. Each file has a stable
    # `.name` and `.id` (when available).
    uploaded_files = list(new_uploads) if new_uploads else []

    # Enforce max images
    if len(uploaded_files) > MAX_IMAGES:
        render_info_box(
            f"Maximum {MAX_IMAGES} images allowed. Showing only the first {MAX_IMAGES}.",
            box_type="warning",
        )
        uploaded_files = uploaded_files[:MAX_IMAGES]

    # Validate file sizes
    valid_files = []
    for f in uploaded_files:
        size_mb = f.size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            render_info_box(
                f"'{f.name}' is {size_mb:.1f}MB — exceeds {MAX_FILE_SIZE_MB}MB limit and was skipped.",
                box_type="warning",
            )
            continue
        valid_files.append(f)

    uploaded_files = valid_files

    # ── Image preview grid ──────────────────────────────────────────────────
    if uploaded_files:
        # Header with count and clear-all button
        col_header, col_clear = st.columns([3, 1])
        with col_header:
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.75rem 1rem;
                    background: rgba(16, 185, 129, 0.08);
                    border: 1px solid rgba(16, 185, 129, 0.2);
                    border-radius: 8px;
                    margin: 1rem 0;
                ">
                    <span style="font-size: 1.25rem;">📷</span>
                    <span style="color: #F1F5F9; font-weight: 600;">
                        {len(uploaded_files)} image{'s' if len(uploaded_files) != 1 else ''} uploaded
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_clear:
            if st.button("🗑 Clear All", key="clear_uploads", type="secondary", use_container_width=True):
                # Streamlit file_uploader persists via key — to clear, set the session-state
                # flag used by the widget. As a workaround, we mark the inspection flow
                # so the next rerun shows no images.
                st.session_state["_clear_uploader"] = True
                st.rerun()

        # 4-column thumbnail grid
        num_cols = 4
        rows = [uploaded_files[i:i + num_cols] for i in range(0, len(uploaded_files), num_cols)]

        for row in rows:
            cols = st.columns(num_cols, gap="medium")
            for col, file in zip(cols, row):
                with col:
                    _render_image_thumbnail(file)

        # Save to session state
        save_uploaded_files(uploaded_files)
    else:
        # Empty state
        render_empty_state(
            icon="📷",
            title="No images uploaded yet",
            message="Upload at least one image of the property to continue.",
        )

    # ── Warning if no images ────────────────────────────────────────────────
    if not uploaded_files:
        render_info_box(
            "Please upload at least one image before continuing.",
            box_type="warning",
        )

    st.markdown("<div class='mt-4'></div>", unsafe_allow_html=True)

    # ── Wizard navigation ───────────────────────────────────────────────────
    back_clicked, next_clicked = render_wizard_nav(
        current_step=2,
        next_label="Continue to Review →",
        next_disabled=False,
        back_key="step2_back",
        next_key="step2_next",
    )

    if back_clicked:
        set_inspection_step(1)
        st.rerun()

    if next_clicked and uploaded_files:
        set_inspection_step(3)
        st.session_state["current_page"] = "review"
        st.rerun()


def _render_image_thumbnail(file):
    """Render a single image thumbnail card with a remove button.

    Args:
        file: Streamlit UploadedFile object.
    """
    col_img, col_btn = st.columns([4, 1], gap="small")

    with col_img:
        st.image(file, use_container_width=True)

    with col_btn:
        # Show file size
        size_kb = file.size / 1024
        size_text = f"{size_kb:.0f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"
        st.markdown(
            f"""
            <div style="
                padding: 0.25rem 0.5rem;
                background: rgba(30, 41, 59, 0.6);
                border-radius: 6px;
                font-size: 0.7rem;
                color: #94A3B8;
                text-align: center;
                margin-bottom: 0.25rem;
            ">
                {size_text}
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Remove button — uses filename as key
        if st.button("✕", key=f"remove_{file.name}_{file.size}", help="Remove this image", use_container_width=True):
            # We can't mutate st.file_uploader state directly, but setting the
            # clear flag and rerunning lets the user re-upload without this file.
            st.session_state["_clear_uploader"] = True
            render_info_box(
                f"Use 'Clear All' to remove '{file.name}'. Per-image removal needs a database in V2.",
                box_type="info",
            )
