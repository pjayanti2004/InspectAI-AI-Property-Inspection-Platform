"""PDF Report Generator for InspectAI.

Generates professional, print-ready PDF inspection reports using ReportLab.

Usage::

    from streamlit_app.report.pdf_generator import generate_pdf
    pdf_bytes = generate_pdf(fused_inspection_dict)
    st.download_button("Download PDF", pdf_bytes, file_name="report.pdf")

The generator is pure Python — no Streamlit, no I/O side effects.
It accepts the dict returned by ``get_report()`` (or any dict with the
same keys) so it stays independent from the rendering layer.
"""
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Any

# ReportLab imports — standard layout primitives
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.platypus.flowables import KeepTogether
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart


# ── Constants ─────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# Brand colours
CLR_PRIMARY   = colors.HexColor("#4F46E5")   # Indigo-600
CLR_SECONDARY = colors.HexColor("#06B6D4")   # Cyan-500
CLR_DARK      = colors.HexColor("#0F172A")   # Slate-900
CLR_TEXT      = colors.HexColor("#334155")   # Slate-700
CLR_MUTED     = colors.HexColor("#64748B")   # Slate-500
CLR_LIGHT_BG  = colors.HexColor("#F8FAFC")   # Slate-50
CLR_BORDER    = colors.HexColor("#E2E8F0")   # Slate-200

# Severity colours (matching UI constants)
SEVERITY_CLR = {
    "Critical": colors.HexColor("#EF4444"),
    "High":     colors.HexColor("#F97316"),
    "Medium":   colors.HexColor("#F59E0B"),
    "Low":      colors.HexColor("#10B981"),
}
GRADE_CLR = {
    "A+": colors.HexColor("#10B981"), "A": colors.HexColor("#10B981"),
    "B+": colors.HexColor("#22C55E"), "B": colors.HexColor("#84CC16"),
    "C":  colors.HexColor("#F59E0B"), "D": colors.HexColor("#EF4444"),
}
RISK_CLR = {
    "Critical": colors.HexColor("#EF4444"),
    "High":     colors.HexColor("#F97316"),
    "Medium":   colors.HexColor("#F59E0B"),
    "Low":      colors.HexColor("#10B981"),
}


# ── Styles ─────────────────────────────────────────────────────────────────────
def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    styles: dict[str, ParagraphStyle] = {}

    styles["report_title"] = ParagraphStyle(
        "ReportTitle",
        parent=base["Heading1"],
        fontSize=22,
        leading=28,
        textColor=CLR_DARK,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    styles["report_subtitle"] = ParagraphStyle(
        "ReportSubtitle",
        parent=base["Normal"],
        fontSize=10,
        leading=14,
        textColor=CLR_MUTED,
        spaceAfter=2,
    )
    styles["section_heading"] = ParagraphStyle(
        "SectionHeading",
        parent=base["Heading2"],
        fontSize=13,
        leading=18,
        textColor=CLR_PRIMARY,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=6,
    )
    styles["subsection"] = ParagraphStyle(
        "Subsection",
        parent=base["Heading3"],
        fontSize=11,
        leading=16,
        textColor=CLR_TEXT,
        fontName="Helvetica-Bold",
        spaceBefore=8,
        spaceAfter=4,
    )
    styles["body"] = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=9,
        leading=13,
        textColor=CLR_TEXT,
        spaceAfter=4,
    )
    styles["body_small"] = ParagraphStyle(
        "BodySmall",
        parent=base["Normal"],
        fontSize=8,
        leading=12,
        textColor=CLR_MUTED,
        spaceAfter=3,
    )
    styles["bullet"] = ParagraphStyle(
        "Bullet",
        parent=base["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=CLR_TEXT,
        leftIndent=12,
        firstLineIndent=0,
        spaceAfter=3,
        bulletIndent=2,
        bulletFontName="Helvetica-Bold",
    )
    styles["footer"] = ParagraphStyle(
        "Footer",
        parent=base["Normal"],
        fontSize=7,
        leading=10,
        textColor=CLR_MUTED,
        alignment=1,  # center
    )
    styles["badge"] = ParagraphStyle(
        "Badge",
        parent=base["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        alignment=1,
    )
    styles["metric_value"] = ParagraphStyle(
        "MetricValue",
        parent=base["Normal"],
        fontSize=18,
        leading=22,
        textColor=CLR_DARK,
        fontName="Helvetica-Bold",
        alignment=1,
    )
    styles["metric_label"] = ParagraphStyle(
        "MetricLabel",
        parent=base["Normal"],
        fontSize=7.5,
        leading=10,
        textColor=CLR_MUTED,
        alignment=1,
    )
    styles["cell"] = ParagraphStyle(
        "TableCell",
        parent=base["Normal"],
        fontSize=8,
        leading=11,
        textColor=CLR_TEXT,
    )
    styles["cell_header"] = ParagraphStyle(
        "TableHeader",
        parent=base["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )
    styles["finding_severity"] = ParagraphStyle(
        "FindingSeverity",
        parent=base["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        alignment=1,
    )

    return styles


# Module-level styles — built once, reused across all section renderers.
_STYLES = _build_styles()


# ── Page templates ─────────────────────────────────────────────────────────────
def _header_footer(canvas, doc):
    """Draw running header and footer on every page."""
    canvas.saveState()

    # Header bar
    canvas.setFillColor(CLR_PRIMARY)
    canvas.rect(MARGIN, PAGE_H - MARGIN - 8, CONTENT_W, 4, fill=1, stroke=0)

    # Header text
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(CLR_DARK)
    canvas.drawString(MARGIN, PAGE_H - MARGIN - 22, "InspectAI")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CLR_MUTED)
    canvas.drawRightString(MARGIN + CONTENT_W, PAGE_H - MARGIN - 22,
                           f"Report — {doc.report_id}")

    # Footer bar
    canvas.setFillColor(CLR_BORDER)
    canvas.rect(MARGIN, MARGIN - 6, CONTENT_W, 1, fill=1, stroke=0)

    # Footer text
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CLR_MUTED)
    canvas.drawString(MARGIN, MARGIN - 18,
                      f"Generated: {doc.generated_at}  |  InspectAI — Automated Property Inspection")
    canvas.drawRightString(MARGIN + CONTENT_W, MARGIN - 18, f"Page {doc.page}")

    canvas.restoreState()


def _first_page_header(canvas, doc):
    """Cover-style header on the first page."""
    canvas.saveState()

    # Dark top banner
    banner_h = 60
    canvas.setFillColor(CLR_DARK)
    canvas.rect(0, PAGE_H - banner_h, PAGE_W, banner_h, fill=1, stroke=0)
    canvas.setFillColor(CLR_PRIMARY)
    canvas.rect(0, PAGE_H - banner_h - 4, PAGE_W, 4, fill=1, stroke=0)

    # Logo placeholder
    canvas.setFillColor(CLR_SECONDARY)
    canvas.rect(MARGIN, PAGE_H - 52, 8, 32, fill=1, stroke=0)

    # Brand name
    canvas.setFont("Helvetica-Bold", 20)
    canvas.setFillColor(colors.white)
    canvas.drawString(MARGIN + 16, PAGE_H - 36, "InspectAI")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(CLR_SECONDARY)
    canvas.drawString(MARGIN + 16, PAGE_H - 52, "Inspect Smarter. Repair Faster.")

    # Report title on banner
    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColor(colors.white)
    canvas.drawString(MARGIN, PAGE_H - banner_h - 28, "PROPERTY INSPECTION REPORT")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(CLR_MUTED)
    canvas.drawString(MARGIN, PAGE_H - banner_h - 42, doc.property_address)

    canvas.restoreState()


def _build_doc_template(styles: dict) -> BaseDocTemplate:
    """Create the ReportLab document template with frames."""
    doc = BaseDocTemplate(
        _get_pdf_buffer().name,  # temp path
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 28,
        bottomMargin=MARGIN + 10,
        title="InspectAI Property Inspection Report",
        author="InspectAI",
    )
    doc.report_id = "—"
    doc.generated_at = "—"
    doc.property_address = "—"

    # Content frame
    content_frame = Frame(
        MARGIN, MARGIN + 10,
        CONTENT_W, PAGE_H - 2 * MARGIN - 38,
        id="content",
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
    )

    doc.addPageTemplates([
        PageTemplate(id="first",  frames=[content_frame], onPage=_first_page_header),
        PageTemplate(id="later",  frames=[content_frame], onPage=_header_footer),
    ])
    return doc


# ── Helper builders ────────────────────────────────────────────────────────────
def _sp(h: float = 6) -> Spacer:
    return Spacer(1, h)


def _hr(color=CLR_BORDER, thickness=0.5):
    return HRFlowable(width=CONTENT_W, thickness=thickness, color=color,
                      spaceAfter=4, spaceBefore=4)


def _p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, _STYLES[style])


def _section(title: str) -> list:
    return [
        _sp(10),
        _p(title, "section_heading"),
        _hr(CLR_PRIMARY, 1),
    ]


def _seal_box(label: str, value: str, sub: str = "", color=CLR_PRIMARY,
              width=CONTENT_W / 3 - 4) -> Table:
    """Colored metric box used in the cover health dashboard."""
    cell_style = [
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TEXTCOLOR",  (0, 0), (-1, -1), colors.white),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [4]),
    ]
    data = [[Paragraph(f"<b>{value}</b>", _STYLES["metric_value"])],
            [Paragraph(label, _STYLES["metric_label"])]]
    if sub:
        data.append([Paragraph(sub, _STYLES["body_small"])])
    t = Table(data, colWidths=[width], rowHeights=None)
    t.setStyle(TableStyle(cell_style))
    return t


def _badge(text: str, bg_color=CLR_PRIMARY) -> Table:
    """Small rounded badge for severity / status."""
    data = [[Paragraph(text, _STYLES["badge"])]]
    t = Table(data, colWidths=[len(text) * 5.5 + 6])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("ROUNDEDCORNERS", [3]),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]))
    return t


def _info_row(label: str, value: str) -> Table:
    """Two-column label : value row."""
    data = [[Paragraph(label, _STYLES["body_small"]),
             Paragraph(f"<b>{value}</b>", _STYLES["body"])]]
    t = Table(data, colWidths=[CONTENT_W * 0.32, CONTENT_W * 0.68])
    t.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    return t


def _severity_badge(severity: str) -> Table:
    color = SEVERITY_CLR.get(severity, CLR_MUTED)
    return _badge(severity.upper(), color)


# ── Section renderers ──────────────────────────────────────────────────────────
def _render_cover(data: dict[str, Any], styles: dict) -> list:
    """Page 1: Cover with property details and health score overview."""
    story: list = []
    S = styles

    # ── Health score visual ─────────────────────────────────────────────────
    health_score = data.get("overall_health_score", 0) or 0
    risk_level   = data.get("risk_level", "Low")
    grade        = data.get("grade", _score_to_grade(health_score))
    severity     = data.get("overall_severity", "Medium")

    score_color = colors.HexColor("#10B981") if health_score >= 70 else (
                  colors.HexColor("#F59E0B") if health_score >= 50 else
                  colors.HexColor("#EF4444"))
    risk_color  = RISK_CLR.get(risk_level, CLR_MUTED)
    grade_color = GRADE_CLR.get(grade, CLR_MUTED)
    sev_color   = SEVERITY_CLR.get(severity, CLR_MUTED)

    # ── Property details table ──────────────────────────────────────────────
    property_details = [
        ("Property Address", data.get("property_address", "—")),
        ("Property Type",   data.get("property_type", "—").title()),
        ("City",            data.get("property_city", "—")),
        ("State",           data.get("property_state", "—")),
        ("Inspection ID",   data.get("inspection_id", "—")),
        ("Inspection Date", data.get("inspection_date", "—")),
        ("Inspector",       data.get("inspector_name", "—")),
        ("Weather",         data.get("weather_condition", "—")),
    ]

    detail_rows = []
    for label, value in property_details:
        detail_rows.append([
            Paragraph(label, S["body_small"]),
            Paragraph(f"<b>{value}</b>", S["body"]),
        ])
    detail_table = Table(detail_rows, colWidths=[CONTENT_W * 0.28, CONTENT_W * 0.72])
    detail_table.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LINEBELOW",    (0, 0), (-1, -2), 0.3, CLR_BORDER),
    ]))

    # ── Assemble ────────────────────────────────────────────────────────────
    story += [
        _sp(14),
        _p("PROPERTY DETAILS", "section_heading"),
        _hr(CLR_PRIMARY, 1),
        detail_table,
        _sp(16),
    ]

    # Health score metric row
    est_min = data.get("overall_estimated_cost_min", 0)
    est_max = data.get("overall_estimated_cost_max", 0)

    metric_boxes = [
        _seal_box("Health Score", str(health_score), color=score_color,
                  width=CONTENT_W / 4 - 4),
        _seal_box("Grade", grade, color=grade_color,
                  width=CONTENT_W / 4 - 4),
        _seal_box("Risk Level", risk_level, color=risk_color,
                  width=CONTENT_W / 4 - 4),
        _seal_box("Severity", severity.title(), color=sev_color,
                  width=CONTENT_W / 4 - 4),
    ]

    metric_row = Table(
        [[mb] for mb in metric_boxes],
        colWidths=[CONTENT_W / 4] * 4,
        hAlign="LEFT",
    )
    metric_row.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))

    story += [
        _p("INSPECTION OVERVIEW", "section_heading"),
        _hr(CLR_PRIMARY, 1),
        metric_row,
        _sp(12),
    ]

    # Executive summary text
    exec_summary = data.get("executive_summary", "")
    if exec_summary:
        story += [
            _p("EXECUTIVE SUMMARY", "section_heading"),
            _hr(CLR_PRIMARY, 1),
            _p(exec_summary, "body"),
            _sp(10),
        ]

    return story


def _render_findings(data: dict[str, Any], styles: dict) -> list:
    """Damage findings table with severity breakdown."""
    story: list = []
    S = styles

    findings = data.get("findings", [])
    if not findings:
        return story + [_p("No damage findings recorded.", "body")]

    story += _section("DAMAGE FINDINGS")

    # Severity counts summary
    sev_counts: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "Medium")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    summary_badges = []
    for sev in ["Critical", "High", "Medium", "Low"]:
        count = sev_counts.get(sev, 0)
        if count > 0:
            summary_badges.append(_badge(f"{sev}: {count}", SEVERITY_CLR.get(sev, CLR_MUTED)))

    if summary_badges:
        badge_row = Table(
            [[b] for b in summary_badges],
            colWidths=[max(len(str(sev_counts.get(s, 0))) * 8 + 30, 40) for s in
                       ["Critical", "High", "Medium", "Low"] if sev_counts.get(s, 0) > 0],
            hAlign="LEFT",
        )
        badge_row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(badge_row)
        story.append(_sp(8))

    # Findings table
    col_w = [CONTENT_W * 0.13, CONTENT_W * 0.15, CONTENT_W * 0.10,
             CONTENT_W * 0.16, CONTENT_W * 0.46]

    header = [
        Paragraph("TYPE", S["cell_header"]),
        Paragraph("SOURCE", S["cell_header"]),
        Paragraph("SEVERITY", S["cell_header"]),
        Paragraph("CONFIDENCE", S["cell_header"]),
        Paragraph("REPAIR STEPS", S["cell_header"]),
    ]
    rows = [header]
    for f in findings:
        severity     = f.get("severity", "Medium")
        sev_color    = SEVERITY_CLR.get(severity, CLR_MUTED)
        damage_type  = f.get("damage_type", "N/A").replace("_", " ").title()
        source       = f.get("file_name", "—")
        confidence   = f"{f.get('confidence', 0)}%"
        repair_steps = "; ".join(f.get("repair_steps", [])[:3]) or "—"

        rows.append([
            Paragraph(damage_type, S["cell"]),
            Paragraph(source[:22], S["cell"]),
            Paragraph(severity.upper(), S["finding_severity"]),
            Paragraph(confidence, S["cell"]),
            Paragraph(repair_steps[:60], S["cell"]),
        ])

    table_style = TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0), CLR_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        # Body
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("LEADING",       (0, 1), (-1, -1), 11),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, CLR_LIGHT_BG]),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        # Grid
        ("GRID",          (0, 0), (-1, -1), 0.3, CLR_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        # Severity cell colour
        ("BACKGROUND",    (2, 1), (2, -1), sev_color),
    ])

    findings_table = Table(rows, colWidths=col_w, repeatRows=1)
    findings_table.setStyle(table_style)
    story.append(findings_table)

    return story


def _render_repair_plan(data: dict[str, Any], styles: dict) -> list:
    """Repair plan section — cost estimates + recommendations."""
    story: list = []
    S = styles

    story += _section("REPAIR PLAN & RECOMMENDATIONS")

    # Cost estimate summary
    est_min = data.get("overall_estimated_cost_min", 0)
    est_max = data.get("overall_estimated_cost_max", 0)
    avg_cost = data.get("avg_repair_cost") or ((est_min + est_max) // 2 if (est_min or est_max) else 0)

    cost_data = [
        [Paragraph("ESTIMATED COST RANGE", S["cell_header"]),
         Paragraph("AVERAGE ESTIMATE", S["cell_header"])],
        [Paragraph(f"₹{est_min:,} – ₹{est_max:,}", S["body"]),
         Paragraph(f"₹{avg_cost:,}", S["body"])],
    ]
    cost_table = Table(cost_data, colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
    cost_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), CLR_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("BACKGROUND",    (0, 1), (-1, -1), CLR_LIGHT_BG),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.3, CLR_BORDER),
    ]))
    story += [cost_table, _sp(10)]

    # Repair steps per finding
    findings = data.get("findings", [])
    for i, f in enumerate(findings, 1):
        severity    = f.get("severity", "Medium")
        damage_type = f.get("damage_type", "N/A").replace("_", " ").title()
        sev_color   = SEVERITY_CLR.get(severity, CLR_MUTED)
        steps       = f.get("repair_steps", [])
        causes      = f.get("possible_causes", [])
        prevention  = f.get("prevention_tips", [])
        professional = f.get("recommended_professional", "N/A")

        block = [
            KeepTogether([
                Table(
                    [[Paragraph(f"  {i}.  {damage_type}", S["subsection"]),
                      _severity_badge(severity)]],
                    colWidths=[CONTENT_W * 0.8, CONTENT_W * 0.2],
                    hAlign="LEFT",
                ),
                _hr(CLR_BORDER, 0.5),
            ]),
        ]

        if causes:
            block.append(_p(f"<b>Possible Causes:</b> {', '.join(causes)}", "body_small"))
        if steps:
            step_bullets = [_p(f"• {s}", "bullet") for s in steps[:4]]
            block.append(Paragraph("<b>Repair Steps:</b>", S["body_small"]))
            block.extend(step_bullets)
        if professional and professional != "N/A":
            block.append(_p(f"<b>Recommended Professional:</b> {professional}", "body_small"))
        if prevention:
            block.append(_p(f"<b>Prevention:</b> {'; '.join(prevention[:2])}", "body_small"))

        story.extend(block)
        story.append(_sp(6))

    return story


def _render_timeline(data: dict[str, Any], styles: dict) -> list:
    """Repair timeline section."""
    story: list = []
    S = styles

    timeline = data.get("timeline", [])
    if not timeline:
        return story

    story += _section("REPAIR TIMELINE")

    timeline_data = []
    for entry in timeline:
        if isinstance(entry, dict):
            bucket   = entry.get("bucket", entry.get("phase", ""))
            desc     = entry.get("description", "")
            actions  = entry.get("actions", [])
        else:
            bucket   = getattr(entry, "bucket", getattr(entry, "phase", ""))
            desc     = getattr(entry, "description", "")
            actions  = getattr(entry, "actions", [])

        action_str = "; ".join(actions[:2]) if actions else desc or "—"
        timeline_data.append([
            Paragraph(bucket, S["body"]),
            Paragraph(action_str[:80], S["body_small"]),
        ])

    if timeline_data:
        timeline_table = Table(timeline_data, colWidths=[CONTENT_W * 0.25, CONTENT_W * 0.75])
        timeline_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), CLR_LIGHT_BG),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.white, CLR_LIGHT_BG]),
            ("GRID",          (0, 0), (-1, -1), 0.3, CLR_BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ]))
        story.append(timeline_table)

    return story


def _render_recommendations(data: dict[str, Any], styles: dict) -> list:
    """Recommendations section — maintenance tips + preventive advice."""
    story: list = []
    S = styles

    story += _section("RECOMMENDATIONS")

    maintenance_tips = data.get("maintenance_tips", [])
    if maintenance_tips:
        story.append(_p("PREVENTIVE MAINTENANCE", "subsection"))
        for tip in maintenance_tips[:6]:
            story.append(_p(f"• {tip}", "bullet"))

    # Property summary
    property_summary = data.get("property_summary", "")
    if property_summary:
        story += [_sp(6), _p("PROPERTY SUMMARY", "subsection"), _p(property_summary, "body")]

    # Inspection conclusion
    conclusion = data.get("inspection_conclusion", "")
    if conclusion:
        story += [_sp(6), _p("CONCLUSION", "subsection"), _p(conclusion, "body")]

    return story


# ── Grade helper ───────────────────────────────────────────────────────────────
def _score_to_grade(score: float) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    if score >= 50: return "C"
    return "D"


# ── Public entry point ─────────────────────────────────────────────────────────
_BUFFER = None  # keep-alive for the temp path


def _get_pdf_buffer() -> io.BufferedIOBase:
    """Return a reusable temp file handle for the PDF output."""
    global _BUFFER
    if _BUFFER is None:
        _BUFFER = io.BytesIO()
    return _BUFFER


def generate_pdf(report_data: dict[str, Any]) -> bytes:
    """Generate a professional PDF inspection report.

    Args:
        report_data: Dict as returned by ``get_report()`` or
                     ``get_inspection_history()``.  Expected keys:
                     - inspection_id, inspection_date
                     - property_address, property_type, property_city, property_state
                     - inspector_name, weather_condition
                     - overall_health_score, overall_severity, grade, risk_level
                     - overall_estimated_cost_min, overall_estimated_cost_max
                     - avg_repair_cost
                     - executive_summary, property_summary, inspection_conclusion
                     - findings (list of dicts)
                     - timeline (list of dicts)
                     - maintenance_tips (list of str)

    Returns:
        Raw PDF bytes ready for ``st.download_button`` or file I/O.
    """
    buf = io.BytesIO()
    styles = _build_styles()

    # Build doc template
    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 28,
        bottomMargin=MARGIN + 10,
        title="InspectAI Property Inspection Report",
        author="InspectAI",
    )
    doc.report_id    = report_data.get("inspection_id", "—")
    doc.generated_at = datetime.now().strftime("%d %B %Y, %I:%M %p")
    doc.property_address = report_data.get("property_address", "—")

    content_frame = Frame(
        MARGIN, MARGIN + 10,
        CONTENT_W, PAGE_H - 2 * MARGIN - 38,
        id="content",
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([
        PageTemplate(id="first", frames=[content_frame], onPage=_first_page_header),
        PageTemplate(id="later", frames=[content_frame], onPage=_header_footer),
    ])

    # ── Build story ────────────────────────────────────────────────────────
    story: list = []

    # Page 1: Cover (details + health overview + exec summary)
    story += _render_cover(report_data, styles)

    # Page break → findings
    story.append(PageBreak())
    story += _render_findings(report_data, styles)

    # Page break → repair plan
    story.append(PageBreak())
    story += _render_repair_plan(report_data, styles)

    # Page break → timeline
    story.append(PageBreak())
    story += _render_timeline(report_data, styles)

    # Page break → recommendations
    story.append(PageBreak())
    story += _render_recommendations(report_data, styles)

    # Build PDF
    doc.build(story)

    buf.seek(0)
    return buf.read()
