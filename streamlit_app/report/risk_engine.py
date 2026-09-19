"""Risk Engine for InspectAI.

Computes overall health score, risk level, and finding severity weights
from a list of InspectionReport objects.

Uses a weighted scoring formula:
    risk_score = Σ (damage_pct_i × 0.35 + severity_weight_i × 0.35 + confidence_i × 0.15 + finding_count_factor × 0.15)

Risk levels:
    0-20   → Low
    21-40  → Medium
    41-60  → High
    61-100 → Critical
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from streamlit_app.ai.inspection_engine import InspectionReport

# ── Severity weight table ──────────────────────────────────────────────────────
SEVERITY_WEIGHTS = {
    "Critical": 1.0,
    "High": 0.75,
    "Medium": 0.5,
    "Low": 0.25,
    "N/A": 0.0,
    "": 0.0,
    None: 0.0,
}

# ── Risk level thresholds ──────────────────────────────────────────────────────
RISK_LEVELS = [
    (0, 20,  "Low",      "#10B981", "rgba(16, 185, 129, 0.15)"),
    (21, 40, "Medium",   "#F59E0B", "rgba(245, 158, 11, 0.15)"),
    (41, 60, "High",     "#F97316", "rgba(249, 115, 22, 0.15)"),
    (61, 100, "Critical","#EF4444", "rgba(239, 68, 68, 0.15)"),
]


@dataclass(frozen=True)
class RiskAssessment:
    """Aggregated risk data from one or more inspection reports.

    Attributes:
        overall_risk_score:  0-100 composite risk score.
        risk_level:          Low / Medium / High / Critical.
        risk_color:          Hex color matching the level.
        risk_bg:             RGBA background for badges/cards.
        health_score:        0-100 health score (inverse of risk).
        total_findings:      Total number of damage regions detected.
        avg_damage_pct:      Mean damage percentage across all images.
        max_damage_pct:      Worst-case damage percentage in any single image.
        avg_confidence:      Mean Gemini confidence (0-100).
        avg_severity:        Numeric average of severity weights (0.0-1.0).
        total_damage_area_px: Sum of damaged pixels across all images.
        critical_count:      Number of Critical findings.
        high_count:          Number of High findings.
        medium_count:        Number of Medium findings.
        low_count:           Number of Low findings.
        estimated_cost_min:  Lower bound of repair cost estimate (INR).
        estimated_cost_max:  Upper bound of repair cost estimate (INR).
    """
    overall_risk_score: float = 0.0
    risk_level: str = "Low"
    risk_color: str = "#10B981"
    risk_bg: str = "rgba(16, 185, 129, 0.15)"
    health_score: int = 100
    total_findings: int = 0
    avg_damage_pct: float = 0.0
    max_damage_pct: float = 0.0
    avg_confidence: float = 0.0
    avg_severity: float = 0.0
    total_damage_area_px: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    estimated_cost_min: int = 0
    estimated_cost_max: int = 0


def _parse_cost_range(cost_str: str) -> tuple[int, int]:
    """Parse a cost range string like '₹5,000 — ₹15,000' into (min, max).

    Falls back to (0, 0) if parsing fails.
    """
    if not cost_str or cost_str == "N/A":
        return 0, 0
    # Strip currency symbols and whitespace
    parts = cost_str.replace("₹", "").replace(",", "").replace("—", "-").split("-")
    try:
        if len(parts) == 2:
            return int(parts[0].strip()), int(parts[1].strip())
    except (ValueError, IndexError):
        pass
    return 0, 0


def _severity_category(severity: str) -> str:
    """Map a severity string to its category bucket."""
    s = (severity or "").strip()
    if s in ("Critical",):
        return "Critical"
    elif s in ("High",):
        return "High"
    elif s in ("Medium",):
        return "Medium"
    elif s in ("Low",):
        return "Low"
    return "Medium"  # Default to Medium for unknown


def assess_risk(reports: list[InspectionReport]) -> RiskAssessment:
    """Compute risk assessment from a list of inspection reports.

    The weighted formula:
        risk = damage% × 0.35
             + severity_weight × 0.35
             + confidence × 0.15
             + finding_count_factor × 0.15

    Finding count factor: linearly maps finding count to 0-100 scale
    (capped at 20 findings → 100).

    Args:
        reports: List of InspectionReport dataclass instances.

    Returns:
        RiskAssessment dataclass with all computed fields.
    """
    if not reports:
        return RiskAssessment()

    # Filter valid reports only
    valid = [r for r in reports if r.validation_passed and r.contour_count > 0]
    if not valid:
        return RiskAssessment()

    n = len(valid)

    # ── Aggregate raw metrics ─────────────────────────────────────────────
    avg_damage_pct = sum(r.damage_percentage for r in valid) / n
    max_damage_pct = max(r.damage_percentage for r in valid)
    total_findings = sum(r.contour_count for r in valid)
    total_damage_area = max(
        sum(r.damage_area_px for r in valid),
        sum(r.largest_damage_area_px for r in valid),
    )

    # Confidence: use reported confidence, fall back to 50
    avg_confidence = (
        sum(r.confidence for r in valid) / n if any(r.confidence > 0 for r in valid) else 50.0
    )

    # Severity weights
    sev_weights = [SEVERITY_WEIGHTS.get(_severity_category(r.severity), 0.0) for r in valid]
    avg_severity = sum(sev_weights) / n if sev_weights else 0.0

    # Finding count factor: 0 at 0 findings, 100 at 20+ findings
    finding_factor = min(total_findings / 20.0, 1.0) * 100.0

    # ── Weighted risk score ────────────────────────────────────────────────
    raw_score = (
        avg_damage_pct * 0.35
        + avg_severity * 100.0 * 0.35
        + avg_confidence * 0.15
        + finding_factor * 0.15
    )
    risk_score = max(0.0, min(100.0, raw_score))

    # ── Determine risk level ──────────────────────────────────────────────
    risk_level = "Low"
    risk_color = "#10B981"
    risk_bg = "rgba(16, 185, 129, 0.15)"
    for lo, hi, name, color, bg in RISK_LEVELS:
        if lo <= risk_score <= hi:
            risk_level, risk_color, risk_bg = name, color, bg
            break

    # ── Health score (inverse) ────────────────────────────────────────────
    health_score = max(0, min(100, round(100.0 - risk_score)))

    # ── Count severity buckets ────────────────────────────────────────────
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for r in valid:
        cat = _severity_category(r.severity)
        counts[cat] += 1
        # Also count each contour in the image as a finding of that severity
        for _ in range(max(r.contour_count, 1)):
            pass  # Already counted above via report level

    # ── Cost range ────────────────────────────────────────────────────────
    cost_mins, cost_maxs = [], []
    for r in valid:
        lo, hi = _parse_cost_range(r.estimated_cost_range)
        if lo > 0 or hi > 0:
            cost_mins.append(lo)
            cost_maxs.append(hi)

    est_min = sum(cost_mins) if cost_mins else 0
    est_max = sum(cost_maxs) if cost_maxs else 0

    return RiskAssessment(
        overall_risk_score=round(risk_score, 1),
        risk_level=risk_level,
        risk_color=risk_color,
        risk_bg=risk_bg,
        health_score=health_score,
        total_findings=total_findings,
        avg_damage_pct=round(avg_damage_pct, 2),
        max_damage_pct=round(max_damage_pct, 2),
        avg_confidence=round(avg_confidence, 1),
        avg_severity=round(avg_severity, 2),
        total_damage_area_px=total_damage_area,
        critical_count=counts["Critical"],
        high_count=counts["High"],
        medium_count=counts["Medium"],
        low_count=counts["Low"],
        estimated_cost_min=est_min,
        estimated_cost_max=est_max,
    )
