"""Analytics Dashboard — main page for InspectAI analytics.

Shows:
- KPI cards (6 summary metrics)
- Charts (matplotlib-based: trend, risk distribution, health grades, damage types, property types, repair costs)
- Recent activity table
- Top risk properties
- Quick insights

Reuses UI components from ui_components.py for styling consistency.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for Streamlit

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    render_section_title,
)
from streamlit_app.utils.constants import (
    BG_CARD, BORDER_COLOR, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    PRIMARY, ACCENT, SUCCESS, WARNING, DANGER,
    SEVERITY_COLORS,
)


# ── Color palette for charts ────────────────────────────────────────────────────
CHART_COLORS = [
    "#4F46E5", "#06B6D4", "#10B981", "#F59E0B",
    "#EF4444", "#F97316", "#8B5CF6", "#EC4899",
    "#14B8A6", "#6366F1",
]

def _score_color(score: float) -> str:
    if score >= 80: return SUCCESS
    if score >= 60: return WARNING
    return DANGER


# ── KPI Card renderer ─────────────────────────────────────────────────────────

def _render_kpis(kpis: list[dict]) -> None:
    """Render 6 KPI cards in a responsive grid."""
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    cols = st.columns(3, gap="medium")
    for i, kpi in enumerate(kpis):
        with cols[i % 3]:
            value = kpi["value"]
            if kpi.get("is_currency"):
                value_str = f"INR {value:,}"
            elif kpi.get("is_score"):
                score_val = float(value) if value else 0
                bar_color = _score_color(score_val)
                value_str = f"""
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 1.5rem; font-weight: 800;">{value}</span>
                    <span style="font-size: 0.7rem; color: {bar_color}; background: {bar_color}22;
                                 padding: 0.15rem 0.4rem; border-radius: 4px; font-weight: 600;">/100</span>
                </div>"""
            else:
                value_str = str(value)

            st.markdown(f"""
                <div class="kpi-card" style="--kpi-color: {kpi['color']};">
                    <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px;
                                background: {kpi['color']}; border-radius: 12px 12px 0 0;"></div>
                    <div class="kpi-icon">{kpi['icon']}</div>
                    <div class="kpi-value">{value_str}</div>
                    <div class="kpi-label">{kpi['label']}</div>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ── Bar chart helper ──────────────────────────────────────────────────────────

def _render_bar_chart(
    labels: list[str],
    values: list[int],
    colors: list[str] | None = None,
    title: str = "",
    horizontal: bool = False,
    show_values: bool = True,
    figsize: tuple[int, int] = (5, 3.2),
) -> None:
    """Render a clean bar chart using matplotlib."""
    if not labels or not values:
        st.caption("_No data available._")
        return

    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    fig.patch.set_facecolor("#1E293B")
    ax.set_facecolor("#1E293B")

    bar_colors = colors or CHART_COLORS[: len(labels)]

    if horizontal:
        bars = ax.barh(labels, values, color=bar_colors, height=0.6,
                       edgecolor="none", linewidth=0)
        ax.set_xlim(0, max(values) * 1.15 if values else 1)
        if show_values:
            for bar, val in zip(bars, values):
                ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                        str(val), va="center", ha="left", fontsize=9,
                        color="#F1F5F9", fontweight="600")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#334155")
        ax.spines["bottom"].set_color("#334155")
        ax.tick_params(colors="#94A3B8", labelsize=9)
        ax.set_xlabel("")
        ax.set_ylabel("")
    else:
        x = np.arange(len(labels))
        bars = ax.bar(x, values, color=bar_colors, width=0.55,
                      edgecolor="none", linewidth=0)
        ax.set_ylim(0, max(values) * 1.2 if values else 1)
        if show_values:
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(values) * 0.02,
                        str(val), ha="center", va="bottom", fontsize=9,
                        color="#F1F5F9", fontweight="600")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=0)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#334155")
        ax.spines["bottom"].set_color("#334155")
        ax.tick_params(colors="#94A3B8", labelsize=9)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    ax.set_title(title, color="#F1F5F9", fontsize=11, fontweight="600", pad=12)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# ── Line chart for trends ─────────────────────────────────────────────────────

def _render_trend_chart(labels: list[str], values: list[int], title: str = "") -> None:
    """Render a line chart with area fill for inspection trends."""
    if not labels or not values:
        st.caption("_No data available._")
        return

    fig, ax = plt.subplots(figsize=(7, 3.2), dpi=100)
    fig.patch.set_facecolor("#1E293B")
    ax.set_facecolor("#1E293B")

    x = np.arange(len(labels))
    ax.plot(x, values, color=PRIMARY, linewidth=2.5, marker="o",
            markersize=7, markerfacecolor=PRIMARY, markeredgecolor="#1E293B",
            markeredgewidth=2, zorder=3)
    ax.fill_between(x, values, alpha=0.15, color=PRIMARY)

    # Annotate points
    for xi, yi in zip(x, values):
        ax.annotate(str(yi), (xi, yi), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=9,
                    color="#F1F5F9", fontweight="600")

    ax.set_ylim(0, max(values) * 1.3 if values else 1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#334155")
    ax.spines["bottom"].set_color("#334155")
    ax.tick_params(colors="#94A3B8", labelsize=9)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.set_title(title, color="#F1F5F9", fontsize=11, fontweight="600", pad=12)
    ax.grid(axis="y", color="#334155", linewidth=0.5, alpha=0.5)

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# ── Donut chart ───────────────────────────────────────────────────────────────

def _render_donut(
    labels: list[str], values: list[int], colors: list[str] | None = None, title: str = ""
) -> None:
    """Render a donut chart."""
    if not labels or not values:
        st.caption("_No data available._")
        return

    colors = colors or CHART_COLORS[: len(labels)]
    fig, ax = plt.subplots(figsize=(4.5, 4), dpi=100)
    fig.patch.set_facecolor("#1E293B")
    ax.set_facecolor("#1E293B")

    wedge_props = {"edgecolor": "#1E293B", "linewidth": 2}
    wedges, texts, autotexts = ax.pie(
        values, labels=None, colors=colors,
        autopct=lambda p: f"{p:.0f}%" if p >= 5 else "",
        startangle=90, wedgeprops=wedge_props,
        pctdistance=0.78,
    )
    for t in autotexts:
        t.set_color("#F1F5F9")
        t.set_fontsize(9)
        t.set_fontweight("600")

    # Legend
    legend_patches = [mpatches.Patch(color=c, label=f"{l} ({v})")
                      for l, v, c in zip(labels, values, colors)]
    ax.legend(handles=legend_patches, loc="upper center", bbox_to_anchor=(0.5, -0.08),
              ncol=2, frameon=False, fontsize=9,
              labelcolor="#94A3B8")

    # Donut hole
    centre_circle = plt.Circle((0, 0), 0.55, fc="#1E293B")
    ax.add_artist(centre_circle)

    ax.set_title(title, color="#F1F5F9", fontsize=11, fontweight="600", pad=16)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# ── Chart orchestration ────────────────────────────────────────────────────────

def render_charts() -> None:
    """Render all chart sections: trend, risk, grades, damage, property types, costs."""
    from streamlit_app.analytics.stats_engine import (
        get_monthly_trend,
        get_risk_distribution,
        get_grade_distribution,
        get_damage_type_distribution,
        get_property_type_distribution,
        get_repair_cost_distribution,
    )

    # Row 1: Trend (full width) + Risk Distribution
    col_trend, col_risk = st.columns([3, 2], gap="medium")

    with col_trend:
        trend = get_monthly_trend(12)
        _render_trend_chart(trend["labels"], trend["counts"],
                            title="📈 Monthly Inspection Trend")

    with col_risk:
        risk = get_risk_distribution()
        if risk["labels"]:
            _render_donut(risk["labels"], risk["counts"], colors=risk["colors"],
                          title="⚠️ Risk Distribution")
        else:
            st.caption("_No severity data yet._")

    # Row 2: Health Grade + Damage Type + Property Type
    st.markdown("---")
    col_g, col_d, col_p = st.columns(3, gap="medium")

    with col_g:
        render_section_title("Health Grade Distribution", icon="📊")
        grades = get_grade_distribution()
        _render_bar_chart(
            grades["labels"], grades["counts"], colors=grades.get("colors"),
            title="", figsize=(4.5, 3),
        )

    with col_d:
        render_section_title("Damage Type Distribution", icon="🔨")
        dmg = get_damage_type_distribution()
        _render_bar_chart(
            dmg["labels"], dmg["counts"],
            horizontal=True, title="", figsize=(4.5, 3),
        )

    with col_p:
        render_section_title("Property Type Distribution", icon="🏘️")
        ptypes = get_property_type_distribution()
        _render_bar_chart(
            ptypes["labels"], ptypes["counts"],
            title="", figsize=(4.5, 3),
        )

    # Row 3: Repair Cost Distribution (full width)
    st.markdown("---")
    col_cost_left, col_cost_right = st.columns([1, 2])
    with col_cost_left:
        render_section_title("Repair Cost Distribution", icon="💰")
    with col_cost_right:
        pass  # placeholder to keep layout balanced

    costs = get_repair_cost_distribution(buckets=6)
    _render_bar_chart(
        costs["labels"], costs["counts"],
        title="Average Repair Cost (INR)", figsize=(7, 3.2),
    )


# ── Recent Activity table ──────────────────────────────────────────────────────

def render_recent_activity() -> None:
    """Render the recent activity table with status badges."""
    from streamlit_app.analytics.stats_engine import get_recent_activity

    activities = get_recent_activity(limit=8)
    render_section_title("📋 Recent Activity", icon="")

    if not activities:
        st.info("No inspections yet. Complete an inspection to see activity here.")
        return

    # Build a simple HTML table
    rows_html = []
    for act in activities:
        score = act.get("overall_health_score") or 0
        score_color = _score_color(score)
        severity = (act.get("overall_severity") or "N/A").title()
        sev_color = SEVERITY_COLORS.get(severity, "#64748B")

        rows_html.append(f"""
            <tr>
                <td style="color: {TEXT_SECONDARY}; font-size: 0.8rem; font-weight: 600;">
                    {act['inspection_id']}
                </td>
                <td style="color: {TEXT_PRIMARY}; font-size: 0.8rem;">
                    {act['address'][:35]}{'…' if len(act.get('address', '')) > 35 else ''}
                </td>
                <td style="color: {TEXT_MUTED}; font-size: 0.8rem;">{act['city']}</td>
                <td style="color: {TEXT_MUTED}; font-size: 0.8rem;">{act['inspection_date']}</td>
                <td style="text-align: center;">
                    <span style="background: {sev_color}22; color: {sev_color};
                                 padding: 0.2rem 0.5rem; border-radius: 4px;
                                 font-size: 0.75rem; font-weight: 600;">{severity}</span>
                </td>
                <td style="text-align: center; color: {score_color}; font-weight: 700; font-size: 0.85rem;">
                    {score}/100
                </td>
                <td style="text-align: center; color: {TEXT_MUTED}; font-size: 0.8rem;">
                    {act['damages_found']}
                </td>
                <td>
                    <span style="background: {BG_CARD}; color: {TEXT_SECONDARY};
                                 padding: 0.2rem 0.5rem; border-radius: 4px;
                                 font-size: 0.75rem;">{act['status'].title()}</span>
                </td>
            </tr>
        """)

    table_html = f"""
        <div style="overflow-x: auto; border-radius: 8px; border: 1px solid {BORDER_COLOR};">
            <table style="width: 100%; border-collapse: collapse; background: {BG_CARD};">
                <thead>
                    <tr style="background: rgba(79, 70, 229, 0.08); border-bottom: 1px solid {BORDER_COLOR};">
                        <th style="padding: 0.75rem; text-align: left; color: {TEXT_MUTED};
                                   font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">ID</th>
                        <th style="padding: 0.75rem; text-align: left; color: {TEXT_MUTED};
                                   font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Address</th>
                        <th style="padding: 0.75rem; text-align: left; color: {TEXT_MUTED};
                                   font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">City</th>
                        <th style="padding: 0.75rem; text-align: left; color: {TEXT_MUTED};
                                   font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Date</th>
                        <th style="padding: 0.75rem; text-align: center; color: {TEXT_MUTED};
                                   font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Severity</th>
                        <th style="padding: 0.75rem; text-align: center; color: {TEXT_MUTED};
                                   font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Health</th>
                        <th style="padding: 0.75rem; text-align: center; color: {TEXT_MUTED};
                                   font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Issues</th>
                        <th style="padding: 0.75rem; text-align: center; color: {TEXT_MUTED};
                                   font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Status</th>
                    </tr>
                </thead>
                <tbody>{"".join(rows_html)}</tbody>
            </table>
        </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


# ── Top Risk Properties ───────────────────────────────────────────────────────

def render_top_risk() -> None:
    """Render the top risk properties list."""
    from streamlit_app.analytics.stats_engine import get_top_risk_properties

    risks = get_top_risk_properties(limit=5)
    render_section_title("🚨 Top Risk Properties", icon="")

    if not risks:
        st.info("No inspections with risk data yet.")
        return

    cols = st.columns(len(risks) if len(risks) <= 5 else 5, gap="small")
    for i, r in enumerate(risks):
        with cols[i % 5] if len(risks) > 1 else cols[0]:
            score = r.get("overall_health_score") or 0
            score_color = _score_color(score)
            risk_level = r.get("risk_level", "Unknown")
            sev_color = SEVERITY_COLORS.get(risk_level, "#64748B")
            cost = r.get("avg_repair_cost", 0)

            st.markdown(f"""
                <div style="
                    background: {BG_CARD}; border: 1px solid {BORDER_COLOR};
                    border-radius: 10px; padding: 1rem; text-align: center;
                    border-top: 3px solid {sev_color};
                ">
                    <div style="font-size: 0.65rem; color: {TEXT_MUTED}; text-transform: uppercase;
                                letter-spacing: 0.08em; margin-bottom: 0.3rem;">{r['inspection_id']}</div>
                    <div style="font-size: 0.85rem; color: {TEXT_PRIMARY}; font-weight: 600;
                                margin-bottom: 0.2rem;">
                        {r['address'][:25]}{'…' if len(r.get('address', '')) > 25 else ''}
                    </div>
                    <div style="font-size: 0.7rem; color: {TEXT_MUTED}; margin-bottom: 0.75rem;">{r['city']}</div>
                    <div style="font-size: 1.75rem; font-weight: 800; color: {score_color};">
                        {score}<span style="font-size: 0.65rem; color: {TEXT_MUTED};">/100</span>
                    </div>
                    <div style="margin: 0.4rem 0;">
                        <span style="background: {sev_color}22; color: {sev_color};
                                     padding: 0.15rem 0.4rem; border-radius: 4px;
                                     font-size: 0.7rem; font-weight: 600;">{risk_level}</span>
                    </div>
                    <div style="font-size: 0.7rem; color: {TEXT_MUTED}; margin-top: 0.25rem;">
                        Est. cost: INR {cost:,}
                    </div>
                </div>
            """, unsafe_allow_html=True)


# ── Quick Insights ────────────────────────────────────────────────────────────

def render_insights() -> None:
    """Render the quick insights section."""
    from streamlit_app.analytics.stats_engine import get_insights

    insights = get_insights()
    render_section_title("💡 Quick Insights", icon="")

    if not insights:
        st.info("Complete more inspections to generate insights.")
        return

    for ins in insights:
        border_left = SUCCESS if ins["type"] == "success" else (
            WARNING if ins["type"] == "warning" else ACCENT
        )
        bg = f"{border_left}12"

        st.markdown(f"""
            <div style="
                display: flex; align-items: flex-start; gap: 0.75rem;
                padding: 0.85rem 1rem; margin-bottom: 0.5rem;
                background: {BG_CARD}; border: 1px solid {BORDER_COLOR};
                border-left: 3px solid {border_left}; border-radius: 8px;
            ">
                <span style="font-size: 1.1rem; flex-shrink: 0;">{ins['icon']}</span>
                <span style="font-size: 0.85rem; color: {TEXT_SECONDARY}; line-height: 1.5;">
                    {ins['text']}
                </span>
            </div>
        """, unsafe_allow_html=True)


# ── Main dashboard renderer ───────────────────────────────────────────────────

def render_analytics_dashboard() -> None:
    """Main entry point — render the complete analytics dashboard."""
    inject_custom_css()

    # Header
    st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: {TEXT_PRIMARY};">
                📊 Analytics Dashboard
            </h2>
            <p style="margin: 0.25rem 0 0; color: {TEXT_MUTED}; font-size: 0.9rem;">
                Property inspection insights and trends
            </p>
        </div>
    """, unsafe_allow_html=True)

    # KPI Cards
    from streamlit_app.analytics.stats_engine import get_kpi_cards
    kpis = get_kpi_cards()
    _render_kpis(kpis)

    st.markdown(f"<div style='border-top: 1px solid {BORDER_COLOR}; margin: 2rem 0;'></div>",
                unsafe_allow_html=True)

    # Charts
    render_charts()

    st.markdown(f"<div style='border-top: 1px solid {BORDER_COLOR}; margin: 2rem 0;'></div>",
                unsafe_allow_html=True)

    # Recent Activity
    render_recent_activity()

    st.markdown(f"<div style='border-top: 1px solid {BORDER_COLOR}; margin: 2rem 0;'></div>",
                unsafe_allow_html=True)

    # Top Risk Properties
    render_top_risk()

    st.markdown(f"<div style='border-top: 1px solid {BORDER_COLOR}; margin: 2rem 0;'></div>",
                unsafe_allow_html=True)

    # Quick Insights
    render_insights()
