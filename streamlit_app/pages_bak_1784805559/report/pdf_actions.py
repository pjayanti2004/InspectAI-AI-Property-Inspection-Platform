"""PDF export actions for the report page.

Provides the download button and PDF generation logic.
"""
from __future__ import annotations

import streamlit as st

from streamlit_app.report.pdf_generator import generate_pdf


def download_pdf(report_data: dict, inspection_id: str) -> None:
    """Generate PDF bytes and offer download button."""
    try:
        pdf_bytes = generate_pdf(report_data)
        st.download_button(
            label="📥 Download PDF",
            data=pdf_bytes,
            file_name=f"InspectAI_Report_{inspection_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"PDF generation failed: {e}")
