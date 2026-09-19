"""InspectAI report package.

Exports the main entry point for rendering a full inspection report.
"""
from __future__ import annotations

from streamlit_app.report.report_builder import render_report

__version__ = "1.0.0"

__all__ = ["render_report"]
