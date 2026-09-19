"""InspectAI Analytics Engine.

Queries the SQLite database and returns structured data for the
Analytics Dashboard.  Every function hits only existing tables:
  - properties
  - inspections
  - reports
  - inspection_images

No external APIs.  No fake data.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

import streamlit as st

from streamlit_app.database.database import init_db, get_connection
from streamlit_app.utils.logger import get_logger
from streamlit_app.utils.performance import PerformanceTracker

logger = get_logger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _conn():
    """Return a fresh connection (caller must close)."""
    init_db()
    return get_connection()


def _grade_label(score: float) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    if score >= 50: return "C"
    return "D"


_GRADE_COLORS = {
    "A+": "#10B981", "A": "#34D399", "B+": "#FBBF24",
    "B":  "#F59E0B", "C": "#F97316", "D": "#EF4444",
}

# ── KPI Cards ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_kpi_cards() -> list[dict[str, Any]]:
    """Return the 6 KPI cards for the dashboard."""
    logger.info("Computing KPI cards (cache miss).")
    with PerformanceTracker.get().stage("get_kpi_cards"):
        conn = _conn()
        try:
            # 1. Total properties
            total_props = conn.execute("SELECT COUNT(*) AS c FROM properties").fetchone()["c"]

            # 2. Total inspections
            total_insps = conn.execute("SELECT COUNT(*) AS c FROM inspections").fetchone()["c"]

            # 3. Average health score
            avg_health = conn.execute(
                "SELECT AVG(overall_health_score) AS avg FROM reports"
            ).fetchone()["avg"]
            avg_health = round(avg_health, 1) if avg_health else 0.0

            # 4. Average repair cost (midpoint of min/max)
            avg_cost_row = conn.execute(
                """SELECT AVG(
                       COALESCE(overall_estimated_cost_min, 0) +
                       COALESCE(overall_estimated_cost_max, 0)
                   ) / 2.0 AS avg FROM reports
                   WHERE overall_estimated_cost_min > 0 OR overall_estimated_cost_max > 0"""
            ).fetchone()
            avg_cost = int(avg_cost_row["avg"]) if avg_cost_row and avg_cost_row["avg"] else 0

            # 5. Critical properties (inspections with critical severity)
            critical_count = conn.execute(
                """SELECT COUNT(DISTINCT inspection_id) AS c
                   FROM reports WHERE overall_severity = 'critical'"""
            ).fetchone()["c"]

            # 6. Open repairs (inspections not yet completed)
            open_repairs = conn.execute(
                """SELECT COUNT(*) AS c FROM inspections
                   WHERE status NOT IN ('completed', 'failed')"""
            ).fetchone()["c"]

            return [
                {"label": "Total Properties",    "value": total_props,  "icon": "🏠", "color": "#4F46E5"},
                {"label": "Total Inspections",    "value": total_insps,  "icon": "📋", "color": "#06B6D4"},
                {"label": "Avg Health Score",     "value": avg_health,   "icon": "💚", "color": "#10B981",
                 "is_score": True},
                {"label": "Avg Repair Cost (INR)","value": avg_cost,     "icon": "💰", "color": "#F59E0B",
                 "is_currency": True},
                {"label": "Critical Properties",  "value": critical_count, "icon": "🚨", "color": "#EF4444"},
                {"label": "Open Repairs",         "value": open_repairs,  "icon": "🔧", "color": "#F97316"},
            ]
        finally:
            conn.close()


# ── Monthly Inspection Trend ───────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_monthly_trend(months: int = 12) -> dict[str, Any]:
    """Return inspection counts per month for the last N months.

    Returns:
        {"labels": ["Jan", "Feb", ...], "counts": [12, 8, ...]}
    """
    logger.info("Computing monthly trend for %d months (cache miss).", months)
    with PerformanceTracker.get().stage("get_monthly_trend"):
        conn = _conn()
        try:
            cutoff = (datetime.now() - timedelta(days=30 * months)).strftime("%Y-%m-01")

            rows = conn.execute(
                """SELECT strftime('%Y-%m', inspection_date) AS month,
                          COUNT(*) AS cnt
                   FROM inspections
                   WHERE inspection_date >= ?
                   GROUP BY month
                   ORDER BY month""",
                (cutoff,),
            ).fetchall()

            labels, counts = [], []
            # Fill missing months with 0
            if rows:
                current = datetime.strptime(rows[0]["month"], "%Y-%m")
                end = datetime.strptime(rows[-1]["month"], "%Y-%m")
                data_map = {r["month"]: r["cnt"] for r in rows}

                while current <= end:
                    key = current.strftime("%Y-%m")
                    labels.append(current.strftime("%b %y"))
                    counts.append(data_map.get(key, 0))
                    # advance one month
                    if current.month == 12:
                        current = current.replace(year=current.year + 1, month=1)
                    else:
                        current = current.replace(month=current.month + 1)

            return {"labels": labels, "counts": counts}
        finally:
            conn.close()


# ── Risk Distribution ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_risk_distribution() -> dict[str, Any]:
    """Return counts of reports by severity level.

    Returns:
        {"labels": ["Critical", "High", ...], "counts": [3, 7, ...],
         "colors": ["#EF4444", "#F97316", ...]}
    """
    logger.info("Computing risk distribution (cache miss).")
    with PerformanceTracker.get().stage("get_risk_distribution"):
        conn = _conn()
        try:
            rows = conn.execute(
                """SELECT overall_severity, COUNT(*) AS cnt
                   FROM reports
                   WHERE overall_severity IS NOT NULL AND overall_severity != ''
                   GROUP BY overall_severity"""
            ).fetchall()

            severity_order = ["Critical", "High", "Medium", "Low"]
            data = {r["overall_severity"]: r["cnt"] for r in rows}

            labels, counts, colors = [], [], []
            for sev in severity_order:
                if sev in data:
                    labels.append(sev)
                    counts.append(data[sev])
                    colors.append(_SEVERITY_COLORS.get(sev, "#64748B"))

            # Catch any unknown severities
            for sev, cnt in data.items():
                if sev not in severity_order:
                    labels.append(sev)
                    counts.append(cnt)
                    colors.append("#64748B")

            return {"labels": labels, "counts": counts, "colors": colors}
        finally:
            conn.close()


_SEVERITY_COLORS = {
    "Critical": "#EF4444",
    "High":     "#F97316",
    "Medium":   "#F59E0B",
    "Low":      "#10B981",
}


# ── Health Grade Distribution ─────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_grade_distribution() -> dict[str, Any]:
    """Return counts of reports bucketed into health grade bands.

    Returns:
        {"labels": ["A+", "A", ...], "counts": [...], "colors": [...]}
    """
    logger.info("Computing grade distribution (cache miss).")
    with PerformanceTracker.get().stage("get_grade_distribution"):
        conn = _conn()
        try:
            rows = conn.execute(
                """SELECT overall_health_score, COUNT(*) AS cnt
                   FROM reports
                   WHERE overall_health_score IS NOT NULL
                   GROUP BY overall_health_score"""
            ).fetchall()

            grade_counter: Counter = Counter()
            for r in rows:
                gl = _grade_label(r["overall_health_score"])
                grade_counter[gl] += r["cnt"]

            grade_order = ["A+", "A", "B+", "B", "C", "D"]
            labels, counts, colors = [], [], []
            for g in grade_order:
                if grade_counter.get(g, 0) > 0:
                    labels.append(g)
                    counts.append(grade_counter[g])
                    colors.append(_GRADE_COLORS.get(g, "#64748B"))

            return {"labels": labels, "counts": counts, "colors": colors}
        finally:
            conn.close()


# ── Damage Type Distribution ──────────────────────────────────────────────────

def get_damage_type_distribution() -> dict[str, Any]:
    """Parse findings_json across all reports and count damage types.

    Returns:
        {"labels": ["Crack", "Water Damage", ...], "counts": [...]}
    """
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT findings_json FROM reports"
        ).fetchall()

        counter: Counter = Counter()
        for r in rows:
            try:
                findings = json.loads(r["findings_json"] or "[]")
                for f in findings:
                    dtype = (f.get("damage_type") or "Unknown").strip().title()
                    if dtype and dtype != "N/A":
                        counter[dtype] += 1
            except (json.JSONDecodeError, TypeError):
                continue

        top = counter.most_common(15)
        if not top:
            return {"labels": [], "counts": []}

        labels, counts = zip(*top)
        return {"labels": list(labels), "counts": list(counts)}
    finally:
        conn.close()


# ── Property Type Distribution ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_property_type_distribution() -> dict[str, Any]:
    """Return counts of properties by type.

    Returns:
        {"labels": ["House", "Apartment", ...], "counts": [...]}
    """
    logger.info("Computing property type distribution (cache miss).")
    with PerformanceTracker.get().stage("get_property_type_distribution"):
        conn = _conn()
        try:
            rows = conn.execute(
                """SELECT property_type, COUNT(*) AS cnt
                   FROM properties
                   GROUP BY property_type
                   ORDER BY cnt DESC"""
            ).fetchall()

            labels = [r["property_type"].replace("_", " ").title() for r in rows]
            counts = [r["cnt"] for r in rows]
            return {"labels": labels, "counts": counts}
        finally:
            conn.close()


# ── Repair Cost Distribution ──────────────────────────────────────────────────

def get_repair_cost_distribution(buckets: int = 6) -> dict[str, Any]:
    """Return histogram-style distribution of average repair costs.

    Args:
        buckets: Number of cost buckets.

    Returns:
        {"labels": ["0–5k", "5k–10k", ...], "counts": [...]}
    """
    conn = _conn()
    try:
        rows = conn.execute(
            """SELECT
                   (COALESCE(overall_estimated_cost_min, 0) +
                    COALESCE(overall_estimated_cost_max, 0)) / 2.0 AS avg_cost
               FROM reports
               WHERE overall_estimated_cost_min > 0 OR overall_estimated_cost_max > 0"""
        ).fetchall()

        costs = [r["avg_cost"] for r in rows if r["avg_cost"]]
        if not costs:
            return {"labels": [], "counts": []}

        max_cost = max(costs)
        bucket_size = max(1, max_cost / buckets)
        bucket_counts: Counter = Counter()

        for c in costs:
            idx = min(int(c / bucket_size), buckets - 1)
            bucket_counts[idx] += 1

        labels, counts = [], []
        for i in range(buckets):
            lo = int(i * bucket_size)
            hi = int((i + 1) * bucket_size)
            labels.append(f"{lo:,}–{hi:,}")
            counts.append(bucket_counts.get(i, 0))

        return {"labels": labels, "counts": counts}
    finally:
        conn.close()


# ── Recent Activity ───────────────────────────────────────────────────────────

def get_recent_activity(limit: int = 8) -> list[dict[str, Any]]:
    """Return recent inspections with joined property and report data.

    Returns list of dicts with keys: inspection_id, date, status,
    address, city, property_type, health_score, severity, grade,
    damages_found.
    """
    conn = _conn()
    try:
        rows = conn.execute(
            """SELECT i.inspection_id, i.inspection_date, i.status,
                      p.address, p.city, p.property_type,
                      r.overall_health_score, r.overall_severity,
                      r.findings_json, r.overall_estimated_cost_min,
                      r.overall_estimated_cost_max
               FROM inspections i
               JOIN properties p ON i.property_id = p.property_id
               LEFT JOIN reports r ON r.inspection_id = i.inspection_id
               ORDER BY i.created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()

        results = []
        for row in rows:
            r = dict(row)
            # Derive grade
            score = r.get("overall_health_score") or 0
            r["grade"] = _grade_label(score)

            # Derive damages_found from findings JSON
            try:
                findings = json.loads(r.pop("findings_json", "[]"))
                r["damages_found"] = len(findings)
            except (json.JSONDecodeError, TypeError):
                r["damages_found"] = 0

            results.append(r)
        return results
    finally:
        conn.close()


# ── Top Risk Properties ───────────────────────────────────────────────────────

def get_top_risk_properties(limit: int = 5) -> list[dict[str, Any]]:
    """Return the highest-risk inspections/properties.

    Sorted by health score ascending (worst first).
    Only inspections with a report are included.

    Returns list of dicts with: inspection_id, address, city,
    property_type, health_score, grade, severity, risk_level,
    avg_repair_cost, inspection_date.
    """
    conn = _conn()
    try:
        rows = conn.execute(
            """SELECT i.inspection_id, i.inspection_date,
                      p.address, p.city, p.property_type,
                      r.overall_health_score, r.overall_severity,
                      r.overall_estimated_cost_min,
                      r.overall_estimated_cost_max
               FROM inspections i
               JOIN properties p ON i.property_id = p.property_id
               JOIN reports r ON r.inspection_id = i.inspection_id
               ORDER BY r.overall_health_score ASC, i.created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()

        results = []
        for row in rows:
            r = dict(row)
            score = r.get("overall_health_score") or 0
            r["grade"] = _grade_label(score)
            r["avg_repair_cost"] = (
                int((r.pop("overall_estimated_cost_min", 0) +
                     r.pop("overall_estimated_cost_max", 0)) / 2)
                if r.get("overall_estimated_cost_min") or r.get("overall_estimated_cost_max")
                else 0
            )
            # Risk level
            sev = (r.get("overall_severity") or "").lower()
            if sev == "critical" or score < 50:
                r["risk_level"] = "Critical"
            elif sev == "high" or score < 70:
                r["risk_level"] = "High"
            elif sev == "medium" or score < 85:
                r["risk_level"] = "Medium"
            else:
                r["risk_level"] = "Low"
            results.append(r)
        return results
    finally:
        conn.close()


# ── Quick Insights ────────────────────────────────────────────────────────────

def get_insights() -> list[dict[str, str]]:
    """Generate short rule-based insights from the database.

    Returns:
        List of dicts with keys: icon, text, type ("info"|"warning"|"success").
    """
    insights: list[dict[str, str]] = []
    conn = _conn()
    try:
        # ── Total counts ───────────────────────────────────────────────────────
        total_insps = conn.execute(
            "SELECT COUNT(*) AS c FROM inspections"
        ).fetchone()["c"]

        total_reports = conn.execute(
            "SELECT COUNT(*) AS c FROM reports"
        ).fetchone()["c"]

        critical = conn.execute(
            """SELECT COUNT(DISTINCT inspection_id) AS c
               FROM reports WHERE overall_severity = 'critical'"""
        ).fetchone()["c"]

        avg_health_row = conn.execute(
            "SELECT AVG(overall_health_score) AS avg FROM reports"
        ).fetchone()
        avg_health = round(avg_health_row["avg"], 1) if avg_health_row and avg_health_row["avg"] else None

        # ── This month's inspections ───────────────────────────────────────────
        this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = conn.execute(
            """SELECT COUNT(*) AS c FROM inspections
               WHERE inspection_date >= ?""",
            (this_month_start.strftime("%Y-%m-%d"),),
        ).fetchone()["c"]

        # ── Most common damage type ─────────────────────────────────────────────
        rows = conn.execute("SELECT findings_json FROM reports").fetchall()
        damage_counter: Counter = Counter()
        for r in rows:
            try:
                for f in json.loads(r["findings_json"] or "[]"):
                    dt = (f.get("damage_type") or "").strip()
                    if dt and dt != "N/A":
                        damage_counter[dt.title()] += 1
            except (json.JSONDecodeError, TypeError):
                continue
        top_damage = damage_counter.most_common(1)
        if top_damage:
            insights.append({
                "icon": "🏷️",
                "text": f"Most common damage type: <strong>{top_damage[0][0]}</strong> "
                        f"({top_damage[0][1]} occurrence{'s' if top_damage[0][1] != 1 else ''}).",
                "type": "info",
            })

        # ── Most common property type ───────────────────────────────────────────
        prop_type_rows = conn.execute(
            """SELECT property_type, COUNT(*) AS cnt
               FROM properties GROUP BY property_type
               ORDER BY cnt DESC LIMIT 1"""
        ).fetchall()
        if prop_type_rows:
            pt = prop_type_rows[0]["property_type"].replace("_", " ").title()
            insights.append({
                "icon": "🏘️",
                "text": f"Most inspected property type: <strong>{pt}</strong>.",
                "type": "info",
            })

        # ── Critical alert ──────────────────────────────────────────────────────
        if critical > 0:
            insights.append({
                "icon": "🚨",
                "text": f"<strong>{critical}</strong> property{'s' if critical != 1 else ''} "
                        f"with critical damage level {'require' if critical > 1 else 'requires'} "
                        f"immediate attention.",
                "type": "warning",
            })

        # ── Health score trend ──────────────────────────────────────────────────
        if avg_health is not None:
            if avg_health >= 80:
                insights.append({
                    "icon": "✅",
                    "text": f"Average health score is <strong>{avg_health}/100</strong> — "
                            f"overall condition is good.",
                    "type": "success",
                })
            elif avg_health >= 60:
                insights.append({
                    "icon": "⚠️",
                    "text": f"Average health score is <strong>{avg_health}/100</strong> — "
                            f"some properties need attention.",
                    "type": "warning",
                })
            else:
                insights.append({
                    "icon": "🔴",
                    "text": f"Average health score is <strong>{avg_health}/100</strong> — "
                            f"significant repairs may be needed.",
                    "type": "warning",
                })

        # ── Inspection volume ───────────────────────────────────────────────────
        if this_month == 0 and total_insps > 0:
            insights.append({
                "icon": "📅",
                "text": "No inspections this month yet. Schedule one to stay on top of property health.",
                "type": "info",
            })

        # ── Completion rate ─────────────────────────────────────────────────────
        if total_insps > 0:
            completed = conn.execute(
                "SELECT COUNT(*) AS c FROM inspections WHERE status = 'completed'"
            ).fetchone()["c"]
            rate = round(completed / total_insps * 100, 1)
            if rate >= 90:
                insights.append({
                    "icon": "📈",
                    "text": f"Inspection completion rate is <strong>{rate}%</strong> — excellent turnaround.",
                    "type": "success",
                })
            elif rate >= 70:
                insights.append({
                    "icon": "📊",
                    "text": f"Inspection completion rate is <strong>{rate}%</strong>.",
                    "type": "info",
                })
            else:
                insights.append({
                    "icon": "⏳",
                    "text": f"Only <strong>{rate}%</strong> of inspections are completed — "
                            f"check for pending work.",
                    "type": "warning",
                })

        # ── Repair cost alert ───────────────────────────────────────────────────
        high_cost = conn.execute(
            """SELECT COUNT(*) AS c FROM reports
               WHERE overall_estimated_cost_max > 100000"""
        ).fetchone()["c"]
        if high_cost > 0:
            insights.append({
                "icon": "💸",
                "text": f"<strong>{high_cost}</strong> inspection{'s' if high_cost != 1 else ''} "
                        f"has estimated repair costs above INR 1,00,000.",
                "type": "warning",
            })

    finally:
        conn.close()

    return insights
