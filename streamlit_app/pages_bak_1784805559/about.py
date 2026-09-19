"""About page — Information about InspectAI and the project.

Static informational page.
"""
import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_header,
    render_info_box,
    render_section_title,
)


# ── Static Content ───────────────────────────────────────────────────────────
ABOUT_SECTIONS = [
    {
        "title": "What is InspectAI?",
        "icon": "🤖",
        "content": """
            InspectAI is an AI-powered property inspection platform that helps homeowners,
            property inspectors, civil engineers, builders, and real-estate companies inspect
            buildings using images and AI. Upload property photos and get instant damage
            detection, severity assessment, repair recommendations, and cost estimates.
        """,
    },
    {
        "title": "How It Works",
        "icon": "⚙️",
        "steps": [
            ("📸", "Upload", "Upload property images to the platform"),
            ("🤖", "Analyze", "AI detects and classifies property damage"),
            ("📊", "Report", "Get a professional inspection report instantly"),
            ("🔧", "Act", "Use repair recommendations and cost estimates"),
        ],
    },
    {
        "title": "Key Features",
        "icon": "✨",
        "features": [
            ("Damage Detection", "AI-powered identification of wall cracks, water stains, mold, paint peeling, and more"),
            ("Severity Assessment", "Critical, High, Medium, Low severity ratings for prioritization"),
            ("Cost Estimation", "Repair cost ranges based on damage type and severity"),
            ("Professional Reports", "Generate shareable inspection reports in seconds"),
            ("Inspection History", "Track and compare inspections over time"),
        ],
    },
    {
        "title": "Technology Stack",
        "icon": "🛠️",
        "stack": [
            ("Python", "Core programming language"),
            ("Streamlit", "Web application framework"),
            ("OpenCV", "Computer vision and image processing"),
            ("NumPy", "Numerical computing"),
            ("Pillow", "Image manipulation"),
            ("SQLite", "Local database (planned)"),
        ],
    },
]


def render_about():
    """Render the about page."""
    inject_custom_css()
    init_page_config()

    render_header(
        title="About InspectAI",
        subtitle="Inspect Smarter. Repair Faster.",
        icon="ℹ️",
    )

    # Hero
    st.markdown(
        """
        <div class="card" style="
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.15), rgba(6, 182, 212, 0.05));
            border: 1px solid rgba(79, 70, 229, 0.3);
            text-align: center;
            padding: 3rem 2rem;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
            <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">InspectAI</h1>
            <p style="font-size: 1.25rem; color: #94A3B8; margin: 0;">
                Inspect Smarter. Repair Faster.
            </p>
            <p style="font-size: 0.9rem; color: #64748B; margin-top: 1rem;">
                v0.1.0 • UI Foundation Phase
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='mt-4'></div>", unsafe_allow_html=True)

    # What is InspectAI?
    _render_what_is()

    # How It Works
    _render_how_it_works()

    # Key Features
    _render_features()

    # Technology Stack
    _render_tech_stack()

    # Project Info
    _render_project_info()


def _render_what_is():
    """Render the 'What is InspectAI' section."""
    section = ABOUT_SECTIONS[0]
    render_section_title(section["title"], icon=section["icon"])
    st.markdown(
        f"""
        <div class="card">
            <p style="color: #94A3B8; line-height: 1.7; font-size: 0.95rem;">
                {section["content"]}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_how_it_works():
    """Render the 'How It Works' section."""
    section = ABOUT_SECTIONS[1]
    render_section_title(section["title"], icon=section["icon"])

    cols = st.columns(len(section["steps"]), gap="medium")
    for col, (icon, label, description) in zip(cols, section["steps"]):
        with col:
            st.markdown(
                f"""
                <div class="card" style="text-align: center; height: 100%;">
                    <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">{icon}</div>
                    <h4 style="margin: 0 0 0.5rem; color: #F1F5F9;">{label}</h4>
                    <p style="font-size: 0.85rem; color: #94A3B8; margin: 0;">{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_features():
    """Render the 'Key Features' section."""
    section = ABOUT_SECTIONS[2]
    render_section_title(section["title"], icon=section["icon"])

    for i, (label, description) in enumerate(section["features"]):
        icon = ["🔍", "⚠️", "💰", "📊", "📜"][i] if i < 5 else "✨"
        st.markdown(
            f"""
            <div class="card" style="
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 1rem 1.25rem;
                margin-bottom: 0.75rem;
            ">
                <div style="
                    width: 48px;
                    height: 48px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(79, 70, 229, 0.15);
                    border-radius: 8px;
                    font-size: 1.5rem;
                    flex-shrink: 0;
                ">{icon}</div>
                <div style="flex: 1;">
                    <p style="color: #F1F5F9; font-weight: 600; margin: 0 0 0.25rem;">{label}</p>
                    <p style="color: #94A3B8; font-size: 0.85rem; margin: 0;">{description}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_tech_stack():
    """Render the 'Technology Stack' section."""
    section = ABOUT_SECTIONS[3]
    render_section_title(section["title"], icon=section["icon"])

    cols = st.columns(3, gap="medium")
    for i, (tech, description) in enumerate(section["stack"]):
        with cols[i % 3]:
            icons = {
                "Python": "🐍",
                "Streamlit": "🎈",
                "OpenCV": "👁️",
                "NumPy": "🔢",
                "Pillow": "🖼️",
                "SQLite": "💾",
            }
            st.markdown(
                f"""
                <div class="card" style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icons.get(tech, "🛠️")}</div>
                    <p style="color: #F1F5F9; font-weight: 600; margin: 0 0 0.25rem;">{tech}</p>
                    <p style="color: #64748B; font-size: 0.75rem; margin: 0;">{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_project_info():
    """Render project info section."""
    st.markdown("<div class='mt-4'></div>", unsafe_allow_html=True)
    render_section_title("Project Information", icon="📌")

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown(
            """
            <div class="card">
                <h4 style="margin-top: 0;">🎯 Project Status</h4>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.6;">
                    <strong style="color: #10B981;">Current:</strong> UI Foundation Phase<br>
                    <strong style="color: #94A3B8;">Next:</strong> AI Pipeline Integration<br>
                    <strong style="color: #94A3B8;">Future:</strong> Database & Auth
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="card">
                <h4 style="margin-top: 0;">📅 Roadmap</h4>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.6;">
                    <strong style="color: #10B981;">✓ Phase 1:</strong> UI Foundation<br>
                    <strong style="color: #F59E0B;">→ Phase 2:</strong> AI Pipeline<br>
                    <strong style="color: #64748B;">○ Phase 3:</strong> Database<br>
                    <strong style="color: #64748B;">○ Phase 4:</strong> Reports & Deploy
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Disclaimer
    st.markdown("<div class='mt-3'></div>", unsafe_allow_html=True)
    render_info_box(
        "InspectAI is currently in the UI Foundation phase. AI analysis, database integration, and user authentication will be added in upcoming phases.",
        box_type="info",
    )