"""Health dashboard renderer for the report page."""
from __future__ import annotations

import streamlit as st

from streamlit_app.report.report_builder import (
    _render_health_dashboard as _rb_render_health_dashboard,
    _render_health_score_ring as _rb_render_health_score_ring,
)
from streamlit_app.views.report.helpers import (
    score_to_grade, risk_color, grade_color,
)
from streamlit_app.components.ui_components import render_html


def _render_health_dashboard(data: dict, health_report=None) -> None:
    """Property health score and grade display.

    If a full PropertyHealthReport is available, render the rich
    dashboard from report_builder.  Otherwise render a lightweight
    score ring + grade card fallback.
    """
    render_html(
        """
        <div class="section-title">🏥 Property Health Dashboard</div>
        """,
    )

    health_score = data.get("overall_health_score", 0)
    grade        = data.get("grade", _score_to_grade(health_score))
    risk_level   = data.get("risk_level", "Low")

    if health_report:
        # Full health dashboard from PropertyHealthReport
        _rb_render_health_dashboard(health_report)
    else:
        # Basic fallback: health ring + grade card
        col1, col2 = st.columns(2)
        with col1:
            _rb_render_health_score_ring(health_score, risk_level,
                                          _risk_color(risk_level))
        with col2:
            grade_color = _grade_color(grade)
            render_html(
                f"""
                <div style="padding: 1.5rem; text-align: center;
                            background: {grade_color}18; border: 2px solid {grade_color};
                            border-radius: 12px; margin-top: 1rem;">
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.1em; margin-bottom: 0.75rem;">Overall Grade</div>
                    <div style="font-size: 3.5rem; font-weight: 800; color: {grade_color}; line-height: 1;">
                        {grade}
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.5rem;">{health_score}/100</div>
                </div>
                """,
            )
