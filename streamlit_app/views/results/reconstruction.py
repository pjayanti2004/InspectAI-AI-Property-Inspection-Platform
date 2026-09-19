"""Reconstruct dataclass instances from session-state dicts.

Session state can't store numpy arrays or complex dataclasses, so the
results page stores data as plain dicts. These helpers rebuild the
typed objects when displaying.
"""
from __future__ import annotations

from typing import Optional

from streamlit_app.ai.health_engine import Grade, HealthCategory, HealthMetric, PropertyHealthReport
from streamlit_app.ai.comparison_engine import ComparisonReport
from streamlit_app.ai.fusion_engine import FusedInspection, FusedFinding, ImageRank
from streamlit_app.report.risk_engine import RiskAssessment
from streamlit_app.report.summary_engine import TimelineEntry


def rebuild_health_report(data: Optional[dict]) -> Optional[PropertyHealthReport]:
    """Rebuild PropertyHealthReport from serialised dict."""
    if not data:
        return None
    categories = []
    for c in data.get("categories", []):
        grade_val = c.get("grade", "D")
        grade = Grade(grade_val) if grade_val in [g.value for g in Grade] else Grade.D
        metrics = [HealthMetric(**m) for m in c.get("metrics", [])]
        categories.append(HealthCategory(
            category=c.get("category", ""),
            score=c.get("score", 0.0),
            grade=grade,
            findings_count=c.get("findings_count", 0),
            issues=c.get("issues", []),
            metrics=metrics,
        ))
    grade_val = data.get("overall_grade", "D")
    grade = Grade(grade_val) if grade_val in [g.value for g in Grade] else Grade.D
    return PropertyHealthReport(
        overall_score=data.get("overall_score", 0.0),
        overall_grade=grade,
        categories=categories,
        remaining_life_years=data.get("remaining_life_years", 0.0),
        immediate_risk=data.get("immediate_risk", "Low"),
        immediate_risk_desc=data.get("immediate_risk_desc", ""),
        future_predictions=data.get("future_predictions", {}),
        inspection_confidence=data.get("inspection_confidence", 0.0),
        repair_priority_index=data.get("repair_priority_index", 0.0),
        health_summary=data.get("health_summary", ""),
        strengths=data.get("strengths", []),
        weaknesses=data.get("weaknesses", []),
        priority_actions=data.get("priority_actions", []),
        preventive_maintenance=data.get("preventive_maintenance", []),
    )


def rebuild_fused_inspection(fused_dict: dict) -> FusedInspection:
    """Rebuild FusedInspection from serialised dict."""
    # Rebuild risk assessment
    ra_dict = fused_dict.get("risk_assessment", {})
    risk = RiskAssessment(
        overall_risk_score=ra_dict.get("overall_risk_score", 0.0),
        risk_level=ra_dict.get("risk_level", "Low"),
        risk_color=ra_dict.get("risk_color", "#10B981"),
        risk_bg=ra_dict.get("risk_bg", "rgba(16,185,129,0.15)"),
        health_score=ra_dict.get("health_score", 100),
        total_findings=ra_dict.get("total_findings", 0),
        critical_count=ra_dict.get("critical_count", 0),
        high_count=ra_dict.get("high_count", 0),
        medium_count=ra_dict.get("medium_count", 0),
        low_count=ra_dict.get("low_count", 0),
        avg_damage_pct=ra_dict.get("avg_damage_pct", 0.0),
        max_damage_pct=ra_dict.get("max_damage_pct", 0.0),
        estimated_cost_min=ra_dict.get("estimated_cost_min", 0),
        estimated_cost_max=ra_dict.get("estimated_cost_max", 0),
    )

    # Rebuild findings
    findings = [
        FusedFinding(
            damage_type=f.get("damage_type", "N/A"),
            severity=f.get("severity", "Medium"),
            confidence=f.get("confidence", 0),
            damage_pct=f.get("damage_pct", 0.0),
            affected_images=f.get("affected_images", []),
            image_count=f.get("image_count", 0),
            possible_causes=f.get("possible_causes", []),
            repair_steps=f.get("repair_steps", []),
            recommended_professional=f.get("recommended_professional", "N/A"),
            estimated_cost_range=f.get("estimated_cost_range", "N/A"),
            urgency=f.get("urgency", "N/A"),
            prevention_tips=f.get("prevention_tips", []),
        )
        for f in fused_dict.get("findings", [])
    ]

    # Rebuild image rankings
    image_rankings = [
        ImageRank(
            rank=r.get("rank", 0),
            file_name=r.get("file_name", ""),
            damage_pct=r.get("damage_pct", 0.0),
            severity=r.get("severity", "N/A"),
            damage_type=r.get("damage_type", "N/A"),
            confidence=r.get("confidence", 0),
        )
        for r in fused_dict.get("image_rankings", [])
    ]

    # Rebuild timeline entries (deserialize findings from serialized dicts)
    timeline = []
    for t in fused_dict.get("timeline", []):
        entry_findings = [
            FusedFinding(
                damage_type=f.get("damage_type", "N/A"),
                severity=f.get("severity", "Medium"),
                confidence=f.get("confidence", 0),
                damage_pct=f.get("damage_pct", 0.0),
                affected_images=f.get("affected_images", []),
                image_count=f.get("image_count", 0),
                possible_causes=f.get("possible_causes", []),
                repair_steps=f.get("repair_steps", []),
                recommended_professional=f.get("recommended_professional", "N/A"),
                estimated_cost_range=f.get("estimated_cost_range", "N/A"),
                urgency=f.get("urgency", "N/A"),
                prevention_tips=f.get("prevention_tips", []),
            )
            for f in t.get("findings", [])
        ]
        timeline.append(TimelineEntry(
            bucket=t.get("bucket", ""),
            findings=entry_findings,
            icon=t.get("icon", ""),
            color=t.get("color", "#64748B"),
        ))

    # Reconstruct FusedInspection
    return FusedInspection(
        overall_damage_pct=fused_dict.get("overall_damage_pct", 0.0),
        overall_confidence=fused_dict.get("overall_confidence", 0.0),
        overall_severity=fused_dict.get("overall_severity", "N/A"),
        overall_health_score=fused_dict.get("overall_health_score", 100),
        overall_estimated_cost_min=fused_dict.get("overall_estimated_cost_min", 0),
        overall_estimated_cost_max=fused_dict.get("overall_estimated_cost_max", 0),
        total_repair_area_px=fused_dict.get("total_repair_area_px", 0),
        avg_crack_width_px=fused_dict.get("avg_crack_width_px", 0.0),
        findings=findings,
        image_rankings=image_rankings,
        executive_summary=fused_dict.get("executive_summary", ""),
        property_summary=fused_dict.get("property_summary", ""),
        inspection_conclusion=fused_dict.get("inspection_conclusion", ""),
        timeline=timeline,
        maintenance_tips=fused_dict.get("maintenance_tips", []),
        total_images=fused_dict.get("total_images", 0),
        total_findings=fused_dict.get("total_findings", 0),
        processing_time_sec=fused_dict.get("processing_time_sec", 0.0),
        risk_assessment=risk,
        source_reports=[],
        health_report=rebuild_health_report(fused_dict.get("health_report")),
    )
