"""Report page package.

Re-exports ``render_report_page`` for backward-compatible imports
(e.g. ``from streamlit_app.views.report import render_report_page``).
"""
from __future__ import annotations

from streamlit_app.views.report.page import render_report_page

__version__ = "1.0.0"

__all__ = ["render_report_page"]
