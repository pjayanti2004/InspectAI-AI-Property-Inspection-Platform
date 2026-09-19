"""Property Health Intelligence Engine for InspectAI.

Converts inspection findings into a property-level health assessment with
category scores, grades, predictions, and actionable intelligence.

Design:
  • Pure logic — no Streamlit imports
  • Rule-based scoring (no ML required)
  • Consumes FusedInspection or list[InspectionReport]
  • Produces PropertyHealthReport consumed by results page + report builder

Scoring:
  • 10 property categories scored 0-100
  • Weighted overall score
  • Letter grade (A+ → D)
  • 3-month / 6-month / 12-month damage progression predictions
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Enums ─────────────────────────────────────────────────────────────────────

class Grade(Enum):
    """Letter grade for property health."""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"
    D = "D"

    @classmethod
    def from_score(cls, score: float) -> "Grade":
        if score >= 90:
            return cls.A_PLUS
        if score >= 80:
            return cls.A
        if score >= 70:
            return cls.B_PLUS
        if score >= 60:
            return cls.B
        if score >= 50:
            return cls.C
        return cls.D

    @property
    def color(self) -> str:
        mapping = {
            "A+": "#10B981",  # Green
            "A": "#34D399",
            "B+": "#6EE7B7",
            "B": "#FBBF24",   # Yellow
            "C": "#F97316",   # Orange
            "D": "#EF4444",   # Red
        }
        return mapping[self.value]

    @property
    def bg(self) -> str:
        mapping = {
            "A+": "rgba(16, 185, 129, 0.15)",
            "A": "rgba(52, 211, 153, 0.15)",
            "B+": "rgba(110, 231, 183, 0.15)",
            "B": "rgba(251, 191, 36, 0.15)",
            "C": "rgba(249, 115, 22, 0.15)",
            "D": "rgba(239, 68, 68, 0.15)",
        }
        return mapping[self.value]


# ── Data Types ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HealthMetric:
    """A single measurable health indicator.

    Attributes:
        name:        Metric name (e.g. "Damage %", "Confidence").
        value:       Current value.
        unit:        Unit string (e.g. "%", "px", "months").
        status:      Human-readable status (e.g. "Good", "Warning").
        color:       Hex color for UI rendering.
    """
    name: str = ""
    value: float = 0.0
    unit: str = ""
    status: str = "N/A"
    color: str = "#64748B"


@dataclass(frozen=True)
class HealthCategory:
    """Health assessment for a single property category.

    Attributes:
        category:        Category name (e.g. "Structure", "Walls").
        score:           0-100 health score.
        grade:           Letter grade.
        findings_count:  Number of findings in this category.
        issues:          List of issue descriptions.
        metrics:         Supporting HealthMetric objects.
    """
    category: str = ""
    score: float = 0.0
    grade: Grade = Grade.D
    findings_count: int = 0
    issues: list[str] = field(default_factory=list)
    metrics: list[HealthMetric] = field(default_factory=list)


@dataclass(frozen=True)
class PropertyHealthReport:
    """Complete property health assessment.

    Attributes:
        overall_score:        Weighted overall health score (0-100).
        overall_grade:        Letter grade (A+ → D).
        categories:           Per-category HealthCategory objects.
        remaining_life_years: Estimated remaining healthy life (years).
        immediate_risk:       Risk level string + description.
        future_predictions:   Dict with 3mo, 6mo, 12mo predictions.
        inspection_confidence:How confident the AI is (0-100%).
        repair_priority_index:Composite priority score (0-100).
        health_summary:       AI-generated summary (max 10 sentences).
        strengths:            List of property strengths.
        weaknesses:           List of property weaknesses.
        priority_actions:     Ordered list of actions to take.
        preventive_maintenance: List of preventive maintenance tips.
    """
    overall_score: float = 0.0
    overall_grade: Grade = Grade.D
    categories: list[HealthCategory] = field(default_factory=list)
    remaining_life_years: float = 0.0
    immediate_risk: str = "Low"
    immediate_risk_desc: str = ""
    future_predictions: dict[str, str] = field(default_factory=dict)
    inspection_confidence: float = 0.0
    repair_priority_index: float = 0.0
    health_summary: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    priority_actions: list[str] = field(default_factory=list)
    preventive_maintenance: list[str] = field(default_factory=list)


# ── Constants ─────────────────────────────────────────────────────────────────

# Category weights for overall score calculation
_CATEGORY_WEIGHTS = {
    "Structure": 0.25,
    "Walls": 0.20,
    "Ceiling": 0.10,
    "Floor": 0.10,
    "Paint": 0.08,
    "Moisture": 0.12,
    "Cracks": 0.10,
    "Electrical": 0.05,
    "Plumbing": 0.05,
    "Exterior": 0.05,
}

_CATEGORY_ORDER = [
    "Structure", "Walls", "Ceiling", "Floor", "Paint",
    "Moisture", "Cracks", "Electrical", "Plumbing", "Exterior",
]

# Category → damage-type keywords used for dynamic scoring assignment
_CATEGORY_KEYWORDS = {
    "Structure": ["structural", "foundation", "settlement", "beam", "column", "load-bearing"],
    "Walls": ["wall", "plaster", "spalling"],
    "Ceiling": ["ceiling", "roof leak"],
    "Floor": ["floor", "tile", "concrete", "slab"],
    "Paint": ["paint", "peeling", "discolour", "fade"],
    "Moisture": ["water damage", "moisture", "leak", "damp", "humidity", "mold", "mould"],
    "Cracks": ["crack", "fracture", "split", "surface crack"],
    "Electrical": ["electrical", "wiring", "outlet", "switch"],
    "Plumbing": ["plumbing", "pipe", "drain", "faucet"],
    "Exterior": ["exterior", "siding", "facade", "gutter", "window", "door frame", "rust"],
}


# ── Private helpers ────────────────────────────────────────────────────────────

def _score_to_grade(score: float) -> Grade:
    return Grade.from_score(score)


def _severity_weight(severity: str) -> float:
    mapping = {"Critical": 1.0, "High": 0.75, "Medium": 0.5, "Low": 0.25}
    return mapping.get(severity, 0.1)


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _score_from_findings(findings: list[dict], base: float = 85.0) -> float:
    """Calculate a category score from findings.

    Starts at `base` (assumes healthy) and degrades based on findings.
    """
    score = base
    for f in findings:
        sev = _severity_weight(f.get("severity", "Low"))
        conf = (f.get("confidence", 50) / 100.0)
        dmg = f.get("damage_pct", 0.0)
        penalty = (sev * 30) + (dmg * 1.5) + (1.0 - conf) * 5
        score -= penalty
    return _clamp(round(score, 1))


def _collect_issues(findings: list[dict], max_issues: int = 3) -> list[str]:
    issues = []
    for f in findings:
        sev = f.get("severity", "Low")
        dtype = f.get("damage_type", "Damage")
        pct = f.get("damage_pct", 0.0)
        issues.append(f"{sev} {dtype} ({pct:.1f}% area)")
    return issues[:max_issues]


def _predict_progression(
    score: float,
    severity_weights: list[float],
    findings_count: int,
    coverage_pct: float = 0.0,
) -> dict[str, str]:
    """Rule-based damage progression prediction over 3/6/12 months.

    Higher current damage + critical findings + high coverage → faster degradation.
    """
    avg_sev = sum(severity_weights) / len(severity_weights) if severity_weights else 0.1
    coverage_factor = min(coverage_pct / 100.0, 1.0)
    degradation_rate = (avg_sev * 0.5) + (coverage_factor * 0.3) + ((100 - score) * 0.02)

    def project(months: int) -> str:
        projected_score = _clamp(score - degradation_rate * months)
        projected_grade = _score_to_grade(projected_score)
        if projected_score >= 80:
            return f"Score: {projected_score:.0f}/100 ({projected_grade.value}) — Stable"
        elif projected_score >= 60:
            return f"Score: {projected_score:.0f}/100 ({projected_grade.value}) — Moderate decline expected"
        elif projected_score >= 40:
            return f"Score: {projected_score:.0f}/100 ({projected_grade.value}) — Significant deterioration likely"
        else:
            return f"Score: {projected_score:.0f}/100 ({projected_grade.value}) — Critical risk — Immediate action required"

    return {
        "3mo": project(3),
        "6mo": project(6),
        "12mo": project(12),
    }


def _compute_remaining_life(overall_score: float, findings_count: int, max_severity: str) -> float:
    """Estimate remaining healthy life in years.

    Higher severity → shorter remaining life.
    Higher health score → longer remaining life.
    """
    # Base remaining life (years) anchored on worst severity
    sev_to_life = {"Critical": 3, "High": 7, "Medium": 15, "Low": 25, "Minimal": 30}
    base_life = sev_to_life.get(max_severity, 15)
    # Scale by health score: at score=100 → full base_life; at score=0 → half base_life
    score_factor = 0.5 + (overall_score / 100.0) * 0.5
    findings_penalty = min(findings_count * 0.3, base_life * 0.4)
    return max(1.0, round(base_life * score_factor - findings_penalty, 1))


# ── Category mapping ───────────────────────────────────────────────────────────

def _map_findings_to_categories(findings: list[dict]) -> dict[str, list[dict]]:
    """Group findings by property category using keyword matching."""
    categories: dict[str, list[dict]] = {cat: [] for cat in _CATEGORY_ORDER}

    keyword_map = {
        "Structure": ["structural", "foundation", "load", "beam", "column"],
        "Walls": ["wall", "crack", "plaster"],
        "Ceiling": ["ceiling", "roof leak", "stain ceiling"],
        "Floor": ["floor", "tile", "concrete", "slab"],
        "Paint": ["paint", "peel", "discolour", "fade"],
        "Moisture": ["water damage", "moisture", "leak", "damp", "humidity", "mold", "mould"],
        "Cracks": ["crack", "fracture", "split"],
        "Electrical": ["electrical", "wiring", "outlet", "switch"],
        "Plumbing": ["plumbing", "pipe", "drain", "faucet", "leak"],
        "Exterior": ["exterior", "siding", "facade", "gutter", "window", "door frame"],
    }

    for f in findings:
        dtype = f.get("damage_type", "").lower()
        assigned = False
        for category, keywords in keyword_map.items():
            if any(kw in dtype for kw in keywords):
                categories[category].append(f)
                assigned = True
                break
        if not assigned:
            # Default: assign to Walls for cracks/damage, Structure for others
            if any(kw in dtype for kw in ["crack", "fracture", "split"]):
                categories["Cracks"].append(f)
            elif any(kw in dtype for kw in ["water", "moisture", "damp", "mold", "mould", "stain"]):
                categories["Moisture"].append(f)
            else:
                categories["Walls"].append(f)

    return categories


# ── Main entry point ───────────────────────────────────────────────────────────

def assess_health(reports: list, fused: Optional[object] = None) -> PropertyHealthReport:
    """Generate a complete property health assessment.

    Args:
        reports:  List of InspectionReport objects or serialised dicts.
        fused:    Optional FusedInspection for aggregated data.

    Returns:
        PropertyHealthReport with all health intelligence.
    """
    # ── Step 1: Normalize input ───────────────────────────────────────────
    findings: list[dict] = []
    total_confidence = 0.0
    conf_count = 0
    all_severities: list[str] = []

    for r in reports:
        if hasattr(r, "to_dict"):
            d = r.to_dict()
        elif isinstance(r, dict):
            d = r
        else:
            continue

        if d.get("damage_type", "N/A") == "N/A":
            continue

        findings.append({
            "damage_type": d.get("damage_type", "Unknown"),
            "severity": d.get("severity", "Low"),
            "confidence": d.get("confidence", 0),
            "damage_pct": d.get("damage_percentage", 0.0),
            "contour_count": d.get("contour_count", 0),
            "repair_steps": d.get("repair_steps", []),
            "urgency": d.get("urgency", "N/A"),
            "file_name": d.get("file_name", "Unknown"),
        })

        conf = d.get("confidence", 0)
        if conf > 0:
            total_confidence += conf
            conf_count += 1
        sev = d.get("severity", "Low")
        if sev != "N/A":
            all_severities.append(sev)

    avg_confidence = round(total_confidence / conf_count, 1) if conf_count > 0 else 0.0

    # Determine worst severity
    severity_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "N/A": 0}
    worst_severity = max(all_severities, key=lambda s: severity_rank.get(s, 0)) if all_severities else "Low"

    # ── Step 2: Map findings to categories ────────────────────────────────
    grouped = _map_findings_to_categories(findings)

    # ── Step 3: Score each category ───────────────────────────────────────
    categories: list[HealthCategory] = []
    weighted_sum = 0.0
    total_weight = 0.0

    for cat_name in _CATEGORY_ORDER:
        cat_findings = grouped.get(cat_name, [])
        if not cat_findings:
            base = 90.0
        else:
            # Dynamic base: higher for categories with only low-severity issues
            worst_sev_in_cat = max(
                (f["severity"] for f in cat_findings),
                key=lambda s: severity_rank.get(s, 0),
                default="Low",
            )
            base = {"Critical": 50, "High": 60, "Medium": 75, "Low": 85}.get(worst_sev_in_cat, 85)
        score = _score_from_findings(cat_findings, base=base)
        grade = _score_to_grade(score)
        weight = _CATEGORY_WEIGHTS.get(cat_name, 0.05)

        # Build metrics
        if cat_findings:
            max_dmg = max(f["damage_pct"] for f in cat_findings)
            avg_sev = sum(_severity_weight(f["severity"]) for f in cat_findings) / len(cat_findings)
            sev_label = {1.0: "Critical", 0.75: "High", 0.5: "Medium", 0.25: "Low"}.get(
                round(avg_sev, 2), "Low"
            )
            metrics = [
                HealthMetric(name="Findings", value=len(cat_findings), unit="issues", status=f"{len(cat_findings)} detected", color="#EF4444"),
                HealthMetric(name="Max Damage", value=max_dmg, unit="%", status=sev_label, color="#F97316"),
                HealthMetric(name="Avg Severity", value=avg_sev * 100, unit="%", status=sev_label, color="#F59E0B"),
            ]
        else:
            metrics = [
                HealthMetric(name="Status", value=100, unit="%", status="No issues", color="#10B981"),
            ]

        categories.append(HealthCategory(
            category=cat_name,
            score=score,
            grade=grade,
            findings_count=len(cat_findings),
            issues=_collect_issues(cat_findings),
            metrics=metrics,
        ))

        weighted_sum += score * weight
        total_weight += weight

    overall_score = round(weighted_sum / total_weight, 1) if total_weight > 0 else 100.0
    overall_grade = _score_to_grade(overall_score)

    # ── Step 4: Remaining healthy life ────────────────────────────────────
    remaining_life = _compute_remaining_life(
        overall_score, len(findings), worst_severity,
    )

    # ── Step 5: Immediate risk ────────────────────────────────────────────
    if worst_severity == "Critical":
        immediate_risk = "High"
        risk_desc = "Critical structural issues detected requiring immediate professional intervention before property use."
    elif worst_severity == "High":
        immediate_risk = "Elevated"
        risk_desc = "High-priority issues identified that could escalate if not addressed within 7 days."
    elif worst_severity == "Medium":
        immediate_risk = "Moderate"
        risk_desc = "Moderate issues detected. Property remains usable but requires scheduled repairs."
    else:
        immediate_risk = "Low"
        risk_desc = "Minor issues only. Property is structurally sound with routine maintenance recommended."

    # ── Step 6: Future predictions ────────────────────────────────────────
    sev_weights = [_severity_weight(f["severity"]) for f in findings]
    total_coverage = sum(f.get("damage_pct", 0.0) for f in findings)
    future_predictions = _predict_progression(
        overall_score, sev_weights, len(findings), coverage_pct=total_coverage,
    )

    # ── Step 7: Inspection confidence ────────────────────────────────────
    if avg_confidence >= 85:
        inspection_confidence = 95.0
    elif avg_confidence >= 70:
        inspection_confidence = 85.0
    elif avg_confidence >= 50:
        inspection_confidence = 70.0
    else:
        inspection_confidence = 55.0 if findings else 90.0
    inspection_confidence = _clamp(inspection_confidence, 0, 100)

    # ── Step 8: Repair priority index ────────────────────────────────────
    # Composite: severity-weighted findings + damage coverage + urgency
    sev_sum = sum(_severity_weight(f["severity"]) for f in findings)
    total_dmg = sum(f["damage_pct"] for f in findings)
    raw_rpi = (sev_sum * 15) + (total_dmg * 2) + (len(findings) * 3) + (100 - overall_score) * 0.5
    repair_priority_index = _clamp(round(raw_rpi, 1), 0, 100)

    # ── Step 9: AI health summary (max 10 sentences) ─────────────────────
    health_summary = _generate_health_summary(
        overall_score=overall_score,
        overall_grade=overall_grade,
        categories=categories,
        findings=findings,
        remaining_life=remaining_life,
        immediate_risk=immediate_risk,
        avg_confidence=avg_confidence,
        repair_priority_index=repair_priority_index,
    )

    # ── Step 10: Strengths & weaknesses ──────────────────────────────────
    strengths: list[str] = []
    weaknesses: list[str] = []

    for cat in categories:
        if cat.score >= 80:
            strengths.append(f"{cat.category} in good condition ({cat.grade.value})")
        elif cat.score < 60:
            weaknesses.append(f"{cat.category} requires attention ({cat.score:.0f}/100, {cat.grade.value})")

    if not strengths:
        strengths.append("Inspection completed — baseline established for future comparisons")
    if not weaknesses and findings:
        weaknesses.append("Minor issues detected across multiple categories")

    # ── Step 11: Priority actions ────────────────────────────────────────
    priority_actions: list[str] = []
    critical_findings = [f for f in findings if f["severity"] == "Critical"]
    high_findings = [f for f in findings if f["severity"] == "High"]

    for f in critical_findings[:3]:
        priority_actions.append(f"URGENT: Address {f['damage_type']} — {f['urgency']}")
    for f in high_findings[:3]:
        priority_actions.append(f"HIGH: Repair {f['damage_type']} — {f['urgency']}")

    if not critical_findings and not high_findings and findings:
        for f in findings[:3]:
            priority_actions.append(f"Schedule: {f['damage_type']} repair — {f['urgency']}")

    if not priority_actions:
        priority_actions.append("No immediate actions required — maintain current maintenance schedule")

    # ── Step 12: Preventive maintenance ──────────────────────────────────
    preventive_maintenance: list[str] = []
    seen_tips: set[str] = set()

    for f in findings:
        repair = f.get("repair_steps", [])
        for step in repair:
            if step not in seen_tips and len(preventive_maintenance) < 6:
                preventive_maintenance.append(step)
                seen_tips.add(step)

    # Add category-specific tips
    moisture_cats = [c for c in categories if c.category in ("Moisture", "Cracks")]
    if any(c.score < 70 for c in moisture_cats):
        preventive_maintenance.append("Schedule bi-monthly moisture and crack inspections")

    if overall_score < 70:
        preventive_maintenance.append("Consider professional structural assessment annually")

    if not preventive_maintenance:
        preventive_maintenance.append("Continue routine annual inspections to maintain property health")

    return PropertyHealthReport(
        overall_score=overall_score,
        overall_grade=overall_grade,
        categories=categories,
        remaining_life_years=remaining_life,
        immediate_risk=immediate_risk,
        immediate_risk_desc=risk_desc,
        future_predictions=future_predictions,
        inspection_confidence=inspection_confidence,
        repair_priority_index=repair_priority_index,
        health_summary=health_summary,
        strengths=strengths[:5],
        weaknesses=weaknesses[:5],
        priority_actions=priority_actions[:5],
        preventive_maintenance=preventive_maintenance[:6],
    )


# ── AI Health Summary Generator ───────────────────────────────────────────────

def _generate_health_summary(
    overall_score: float,
    overall_grade: Grade,
    categories: list[HealthCategory],
    findings: list[dict],
    remaining_life: float,
    immediate_risk: str,
    avg_confidence: float,
    repair_priority_index: float,
) -> str:
    """Generate a professional health summary (max 10 sentences)."""
    lines: list[str] = []

    lines.append(
        f"The property received an overall health score of {overall_score:.0f}/100 "
        f"(Grade {overall_grade.value}), indicating "
        f"{'excellent' if overall_score >= 80 else 'good' if overall_score >= 60 else 'concerning'} "
        f"condition across all assessed categories."
    )

    weak = [c for c in categories if c.score < 70]
    if weak:
        names = ", ".join(c.category for c in weak)
        lines.append(
            f"{len(weak)} categor{'y' if len(weak) == 1 else 'ies'} "
            f"require attention: {names}."
        )

    if immediate_risk in ("High", "Elevated"):
        lines.append(
            f"Immediate risk level is {immediate_risk}. "
            f"Professional intervention is recommended before property use."
        )

    lines.append(
        f"AI inspection confidence is {avg_confidence:.0f}% based on "
        f"{len(findings)} finding{'s' if len(findings) != 1 else ''} across "
        f"{sum(1 for c in categories if c.findings_count > 0)} categories."
    )

    lines.append(
        f"Estimated remaining healthy lifespan is {remaining_life:.1f} years "
        f"with current maintenance levels."
    )

    lines.append(
        f"Repair Priority Index is {repair_priority_index:.0f}/100, "
        f"{'indicating urgent repair needs' if repair_priority_index > 70 else 'suggesting scheduled maintenance is sufficient'}."
    )

    strong = [c for c in categories if c.score >= 85]
    if strong:
        lines.append(
            f"Strength areas: {', '.join(c.category for c in strong[:3])} — "
            f"these components show no significant wear."
        )

    lines.append(
        "Regular monitoring of identified weak areas is essential to prevent "
        "progression to more severe damage. Addressing issues early reduces repair costs by 40-60%."
    )

    lines.append(
        "A follow-up inspection is recommended within 3-6 months to verify "
        "the effectiveness of any repairs and detect new issues early."
    )

    if overall_score < 60:
        lines.append(
            "Given the current condition, a comprehensive structural assessment "
            "by a licensed engineer is strongly recommended."
        )

    return " ".join(lines[:10])


# ── Compatibility helpers ──────────────────────────────────────────────────────

def health_report_to_dict(report: PropertyHealthReport) -> dict:
    """Convert PropertyHealthReport to a plain dict for session state storage."""
    return {
        "overall_score": report.overall_score,
        "overall_grade": report.overall_grade.value,
        "grade_color": report.overall_grade.color,
        "grade_bg": report.overall_grade.bg,
        "remaining_life_years": report.remaining_life_years,
        "immediate_risk": report.immediate_risk,
        "immediate_risk_desc": report.immediate_risk_desc,
        "inspection_confidence": report.inspection_confidence,
        "repair_priority_index": report.repair_priority_index,
        "health_summary": report.health_summary,
        "future_predictions": report.future_predictions,
        "strengths": report.strengths,
        "weaknesses": report.weaknesses,
        "priority_actions": report.priority_actions,
        "preventive_maintenance": report.preventive_maintenance,
        "categories": [
            {
                "category": c.category,
                "score": c.score,
                "grade": c.grade.value,
                "grade_color": c.grade.color,
                "grade_bg": c.grade.bg,
                "findings_count": c.findings_count,
                "issues": c.issues,
                "metrics": [
                    {"name": m.name, "value": m.value, "unit": m.unit, "status": m.status, "color": m.color}
                    for m in c.metrics
                ],
            }
            for c in report.categories
        ],
    }
