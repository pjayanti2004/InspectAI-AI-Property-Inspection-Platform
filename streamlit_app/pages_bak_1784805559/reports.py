"""Reports page — View, search, filter, and manage all inspection reports.

Features:
  - Database-backed report listing with pagination
  - Search by property address / inspection ID
  - Filter by severity, grade, date range
  - Sort by date, health score, damage severity
  - Report cards with quick stats
  - Click-through to detailed report view
  - PDF download (via pdf_generator)
  - Delete reports
"""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_header,
    render_section_title,
)
from streamlit_app.database import (
    delete_report,
    get_inspection_history,
    init_db,
    list_reports,
)
from streamlit_app.utils.constants import (
    TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR, PRIMARY,
    SEVERITY_COLORS, SUCCESS, DANGER, WARNING,
)
from streamlit_app.utils.session_manager import navigate_to


# ── Per-page count ─────────────────────────────────────────────────────────────
PAGE_SIZE = 9


def render_reports():
    """Render the reports listing page with search, filters, and sorting."""
    inject_custom_css()
    init_page_config()
    init_db()

    viewing_id = st.session_state.get("view_report_id")
    if viewing_id:
        # Navigate to the report detail page (delegates to pages/report.py)
        from streamlit_app.pages.report import render_report_page
        render_report_page()
        return

    # ── Page header ────────────────────────────────────────────────────────
    render_header(
        title="Reports",
        subtitle="View, search, and download inspection reports",
        icon="📑",
    )

    # ── Quick stats ────────────────────────────────────────────────────────
    _render_quick_stats()

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ── Filters & Search ──────────────────────────────────────────────────
    search, severity_filter, grade_filter, sort_option = _render_filters()

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ── Fetch reports from database ───────────────────────────────────────
    reports, total = _fetch_reports(search, severity_filter, grade_filter, sort_option)

    st.markdown(
        f"""
        <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 1rem;">
            Showing <b style="color: #F1F5F9;">{len(reports)}</b> of <b style="color: #F1F5F9;">{total}</b> reports
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not reports:
        st.markdown(
            """
            <div style="text-align: center; padding: 3rem 2rem;">
                <div style="font-size: 3rem; margin-bottom: 0.75rem;">📭</div>
                <p style="color: #64748B; font-size: 1rem;">
                    No reports found. Complete an inspection to generate your first report.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Card grid (3 columns) ──────────────────────────────────────────────
    _render_report_cards(reports)

    # ── Pagination ────────────────────────────────────────────────────────
    if total > PAGE_SIZE:
        _render_pagination(total)


# ──────────────────────────────────────────────────────────────────────────────
# Quick stats
# ──────────────────────────────────────────────────────────────────────────────

def _render_quick_stats():
    """Compute and display four quick-stat cards."""
    try:
        all_reports, total = list_reports(limit=100)
    except Exception:
        all_reports, total = [], 0

    total_reports  = total
    critical_count = sum(1 for r in all_reports if r.get("overall_severity") == "Critical")
    avg_score      = (sum(r.get("overall_health_score", 0) for r in all_reports) // max(len(all_reports), 1)) if all_reports else 0

    stats = [
        ("Total Reports", str(total_reports), PRIMARY),
        ("Critical Issues", str(critical_count), "#EF4444"),
        ("Avg Health Score", f"{avg_score}/100", "#10B981" if avg_score >= 70 else "#F59E0B"),
        ("Exports", "—", "#06B6D4"),
    ]

    cols = st.columns(4, gap="medium")
    for col, (label, value, color) in zip(cols, stats):
        with col:
            st.markdown(
                f"""
                <div class="stat-card" style="
                    background: {color}12; border: 1px solid {color}35;
                ">
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.05em; margin-bottom: 0.3rem;">{label}</div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: {color};">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ──────────────────────────────────────────────────────────────────────────────
# Filters
# ──────────────────────────────────────────────────────────────────────────────

def _render_filters():
    """Render search + filter controls. Returns (search, severity, grade, sort)."""
    col_search, col_sev, col_grade, col_sort = st.columns([2, 1, 1, 1])

    with col_search:
        search = st.text_input(
            "Search",
            placeholder="🔍  Search by address or inspection ID...",
            label_visibility="collapsed",
        )

    with col_sev:
        severity_filter = st.selectbox(
            "Severity",
            ["All", "Critical", "High", "Medium", "Low"],
            label_visibility="collapsed",
        )

    with col_grade:
        grade_filter = st.selectbox(
            "Grade",
            ["All", "A+", "A", "B+", "B", "C", "D"],
            label_visibility="collapsed",
        )

    with col_sort:
        sort_option = st.selectbox(
            "Sort",
            ["Newest First", "Oldest First", "Highest Score", "Lowest Score"],
            label_visibility="collapsed",
        )

    return search, severity_filter, grade_filter, sort_option


# ──────────────────────────────────────────────────────────────────────────────
# Data fetching
# ──────────────────────────────────────────────────────────────────────────────

def _fetch_reports(search: str, severity: str, grade: str, sort: str):
    """Fetch reports from SQLite with filters applied.

    Returns:
        (reports_list, total_count)
    """
    try:
        # Severity filter maps to the database's overall_severity column
        sev = "" if severity == "All" else severity

        # Grade filter: we fetch all and filter client-side
        # (SQLite doesn't have a grade column in reports table)

        reports = list_reports(severity=sev, limit=100)

        # Client-side grade filtering
        if grade != "All":
            reports = [r for r in reports if r.get("grade", "") == grade]

        # Client-side search filter
        if search:
            q = search.lower()
            reports = [
                r for r in reports
                if q in r.get("property_address", "").lower()
                or q in r.get("inspection_id", "").lower()
                or q in r.get("inspector_name", "").lower()
            ]

        # Sorting
        if sort == "Newest First":
            reports.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        elif sort == "Oldest First":
            reports.sort(key=lambda r: r.get("created_at", ""))
        elif sort == "Highest Score":
            reports.sort(key=lambda r: r.get("overall_health_score", 0), reverse=True)
        elif sort == "Lowest Score":
            reports.sort(key=lambda r: r.get("overall_health_score", 0))

        total = len(reports)
        return reports[:PAGE_SIZE], total

    except Exception as e:
        st.error(f"Failed to load reports: {e}")
        return [], 0


# ──────────────────────────────────────────────────────────────────────────────
# Card rendering
# ──────────────────────────────────────────────────────────────────────────────

def _render_report_cards(reports: list):
    """Render report cards in a 3-column grid."""
    cols = st.columns(3, gap="medium")
    for i, report in enumerate(reports):
        col = cols[i % 3]
        with col:
            _render_report_card(report, i)


def _render_report_card(report: dict, index: int):
    """Render a single report card."""
    health_score = report.get("overall_health_score", 0)
    risk_level   = report.get("overall_severity", "Medium")
    report_id    = report.get("report_id", report.get("inspection_id", "—"))
    address     = report.get("property_address", "—")
    prop_type   = report.get("property_type", "").title()
    date_str    = report.get("created_at", report.get("inspection_date", "—"))[:10]
    findings    = report.get("findings", [])
    finding_count = len(findings) if isinstance(findings, list) else 0

    # Health score color
    if health_score >= 80:
        health_color = "#10B981"
    elif health_score >= 60:
        health_color = "#F59E0B"
    else:
        health_color = "#EF4444"

    # Severity badge
    sev_color = SEVERITY_COLORS.get(risk_level, "#64748B")

    # Grade
    grade = report.get("grade", "—")
    grade_color = {"A+": "#10B981", "A": "#34D399", "B+": "#6EE7B7",
                   "B": "#FBBF24", "C": "#F97316", "D": "#EF4444"}.get(grade, "#64748B")

    st.markdown(
        f"""
        <div style="
            background: #1E293B; border: 1px solid {BORDER_COLOR}; border-radius: 10px;
            padding: 1.25rem; margin-bottom: 1rem; transition: border-color 0.2s;
        " onmouseover="this.style.borderColor='#4F46E5'" onmouseout="this.style.borderColor='#334155'">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                <div style="flex: 1;">
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.05em; margin-bottom: 0.2rem;">{report_id}</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: {TEXT_PRIMARY};
                                line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2;
                                -webkit-box-orient: vertical; overflow: hidden;">
                        {address}
                    </div>
                </div>
                <div style="
                    background: {health_color}18; border: 1px solid {health_color}40;
                    border-radius: 8px; padding: 0.4rem 0.6rem; text-align: center; margin-left: 0.75rem;
                ">
                    <div style="font-size: 1.1rem; font-weight: 800; color: {health_color};">{health_score}</div>
                    <div style="font-size: 0.6rem; color: #64748B; text-transform: uppercase;">Score</div>
                </div>
            </div>

            <!-- Meta row -->
            <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap;">
                <span style="font-size: 0.75rem; color: #94A3B8; background: #0F172A; padding: 0.15rem 0.5rem; border-radius: 4px;">
                    {prop_type or "—"}
                </span>
                <span style="font-size: 0.75rem; color: #64748B;">{date_str}</span>
                <span style="
                    background: {sev_color}18; color: {sev_color}; padding: 0.15rem 0.5rem;
                    border-radius: 4px; font-size: 0.7rem; font-weight: 600;
                ">{risk_level}</span>
            </div>

            <!-- Grade -->
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <span style="font-size: 0.75rem; color: #64748B;">Grade:</span>
                <span style="
                    background: {grade_color}18; color: {grade_color}; padding: 0.1rem 0.5rem;
                    border-radius: 4px; font-size: 0.85rem; font-weight: 700;
                ">{grade}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Action buttons
    col_view, col_pdf, col_del = st.columns([2, 1, 1])
    with col_view:
        if st.button("👁️ View Report", key=f"view_{report_id}_{index}", type="primary", use_container_width=True):
            st.session_state["view_report_id"] = report_id
            st.rerun()
    with col_pdf:
        if st.button("📥 PDF", key=f"pdf_{report_id}_{index}", use_container_width=True):
            _download_report_pdf(report, report_id)
    with col_del:
        if st.button("🗑️", key=f"del_{report_id}_{index}", use_container_width=True):
            _confirm_delete(report_id)


def _download_report_pdf(report: dict, report_id: str):
    """Generate and download a PDF for this report."""
    try:
        from streamlit_app.report.pdf_generator import generate_pdf
        pdf_bytes = generate_pdf(report)
        st.download_button(
            label="📥 Downloading…",
            data=pdf_bytes,
            file_name=f"InspectAI_Report_{report_id}.pdf",
            mime="application/pdf",
            key=f"dl_btn_{report_id}",
        )
    except Exception as e:
        st.error(f"PDF generation failed: {e}")


def _confirm_delete(report_id: str):
    """Show a delete confirmation inline."""
    st.session_state[f"_delete_confirm_{report_id}"] = True


def _render_pagination(total: int):
    """Render pagination controls (simple prev/next)."""
    current = st.session_state.get("_reports_page", 0)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    if total_pages <= 1:
        return

    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_info:
        st.markdown(
            f"<div style='text-align: center; font-size: 0.85rem; color: #64748B;'>"
            f"Page {current + 1} of {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with col_prev:
        if st.button("← Previous", disabled=(current == 0), use_container_width=True):
            st.session_state["_reports_page"] = max(0, current - 1)
            st.rerun()
    with col_next:
        if st.button("Next →", disabled=(current >= total_pages - 1), use_container_width=True):
            st.session_state["_reports_page"] = min(total_pages - 1, current + 1)
            st.rerun()
