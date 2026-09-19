"""Fusion Engine for InspectAI.

Merges per-image ``InspectionReport`` objects into a single unified
inspection result — eliminating duplicate findings, combining evidence,
and producing a property-level summary.

Design goals:
  • Deduplicate findings by damage type across all images
  • Preserve the worst severity and highest confidence per finding
  • Combine causes, repair steps, and tips into merged lists
  • Produce a single ``FusedInspection`` with:
      - overall damage %, confidence, severity, health score
      - merged findings (one per distinct damage type)
      - image priority ranking
      - AI executive summary
      - repair timeline
      - overall maintenance tips

The fused output is compatible with the report module — see
``to_inspection_reports()``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from streamlit_app.ai.inspection_engine import InspectionReport
from streamlit_app.ai.health_engine import assess_health, PropertyHealthReport
from streamlit_app.ai.comparison_engine import compare_inspections, ComparisonReport
from streamlit_app.report.risk_engine import assess_risk, RiskAssessment


# ── Data Types ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ImageRank:
    """Priority ranking for a single image within the inspection.

    Attributes:
        rank:          1-based rank (1 = most damaged).
        file_name:     Source image file name.
        damage_pct:    Damage percentage detected in this image.
        severity:      Worst severity found in this image.
        damage_type:   Primary damage type found.
        confidence:    AI confidence for this image.
    """
    rank: int = 0
    file_name: str = ""
    damage_pct: float = 0.0
    severity: str = "N/A"
    damage_type: str = "N/A"
    confidence: int = 0


@dataclass(frozen=True)
class FusedFinding:
    """A deduplicated finding merged from multiple images of the same damage type.

    Attributes:
        damage_type:        Category (e.g. "Crack", "Water Damage").
        severity:           Worst severity across all source images.
        confidence:         Highest confidence across all source images.
        damage_pct:         Maximum damage % from any single image.
        affected_images:    File names of images that showed this damage.
        image_count:        How many images showed this damage.
        possible_causes:    Deduplicated list of possible causes.
        repair_steps:       Deduplicated ordered repair steps.
        recommended_professional: Professional to consult.
        estimated_cost_range: Combined cost range.
        urgency:            Urgency classification.
        prevention_tips:    Deduplicated maintenance tips.
    """
    damage_type: str = "N/A"
    severity: str = "Medium"
    confidence: int = 0
    damage_pct: float = 0.0
    affected_images: list[str] = field(default_factory=list)
    image_count: int = 0
    possible_causes: list[str] = field(default_factory=list)
    repair_steps: list[str] = field(default_factory=list)
    recommended_professional: str = "N/A"
    estimated_cost_range: str = "N/A"
    urgency: str = "N/A"
    prevention_tips: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FusedInspection:
    """Unified property-level inspection result from multiple images.

    This is the output of ``fuse_reports()``.  It replaces the list of
    per-image reports with a single merged view.

    Attributes:
        overall_damage_pct:    Highest damage % across all images.
        overall_confidence:    Mean confidence across all images.
        overall_severity:      Worst severity across all images.
        overall_health_score:  0-100 health score (inverse of risk).
        overall_estimated_cost_min: Lower cost bound.
        overall_estimated_cost_max: Upper cost bound.
        total_repair_area_px:  Sum of estimated repair areas across all images.
        avg_crack_width_px:    Average crack width across all linear regions.
        findings:              Deduplicated FusedFinding list (sorted by severity).
        image_rankings:        Images sorted by damage (most damaged first).
        executive_summary:     8-sentence professional summary (generated).
        property_summary:      Short property-level overview.
        inspection_conclusion: Final verdict paragraph.
        timeline:              Repair timeline entries.
        maintenance_tips:      Deduplicated tips from all findings.
        total_images:          Number of images analysed.
        total_findings:        Number of distinct damage types found.
        processing_time_sec:   Total AI processing time.
        risk_assessment:       Full RiskAssessment from risk_engine.
        source_reports:        Original InspectionReport list (preserved).
        health_report:         PropertyHealthReport from health_engine.
    """
    overall_damage_pct: float = 0.0
    overall_confidence: float = 0.0
    overall_severity: str = "N/A"
    overall_health_score: int = 100
    overall_estimated_cost_min: int = 0
    overall_estimated_cost_max: int = 0
    total_repair_area_px: int = 0
    avg_crack_width_px: float = 0.0
    findings: list[FusedFinding] = field(default_factory=list)
    image_rankings: list[ImageRank] = field(default_factory=list)
    executive_summary: str = ""
    property_summary: str = ""
    inspection_conclusion: str = ""
    timeline: list = field(default_factory=list)
    maintenance_tips: list[str] = field(default_factory=list)
    total_images: int = 0
    total_findings: int = 0
    processing_time_sec: float = 0.0
    risk_assessment: Optional[RiskAssessment] = None
    source_reports: list[InspectionReport] = field(default_factory=list)
    health_report: Optional[PropertyHealthReport] = None
    comparison_report: Optional[ComparisonReport] = None


# ── Helper utilities ───────────────────────────────────────────────────────────

_SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "N/A": 4, "": 5}
_SEVERITY_WEIGHTS = {"Critical": 1.0, "High": 0.75, "Medium": 0.5, "Low": 0.25, "N/A": 0.0, "": 0.0}

_COST_MAP = {
    "Critical": (15000, 50000),
    "High": (8000, 25000),
    "Medium": (3000, 10000),
    "Low": (500, 3000),
}


def _parse_cost(cost_str: str) -> tuple[int, int]:
    """Parse cost range string → (min, max)."""
    if not cost_str or cost_str == "N/A":
        return 0, 0
    parts = cost_str.replace(",", "").replace("—", "-").split("-")
    try:
        if len(parts) == 2:
            return int(parts[0].strip()), int(parts[1].strip())
    except (ValueError, IndexError):
        pass
    return 0, 0


def _normalize_damage_type(damage_type: str) -> str:
    """Normalize damage type string for deduplication.

    Maps variants to canonical names.
    """
    dt = (damage_type or "").strip().lower()
    mapping = {
        "crack": "Crack",
        "water damage": "Water Damage",
        "water_stain": "Water Damage",
        "water stain": "Water Damage",
        "mold": "Mold",
        "paint peeling": "Paint Peeling",
        "peeling paint": "Paint Peeling",
        "roof damage": "Roof Damage",
        "foundation": "Foundation Issue",
        "structural damage": "Structural Damage",
        "structural": "Structural Damage",
        "electrical": "Electrical",
        "plumbing": "Plumbing",
        "termite": "Termite Damage",
        "pest": "Termite Damage",
    }
    for key, canonical in mapping.items():
        if key in dt:
            return canonical
    # Capitalize first letter of each word
    return damage_type.title() if damage_type else "General Damage"


def _deduplicate(items: list[str]) -> list[str]:
    """Remove duplicates while preserving order and trimming whitespace."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = item.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


# ── Core fusion function ───────────────────────────────────────────────────────

def fuse_reports(reports: list[InspectionReport]) -> FusedInspection:
    """Merge multiple per-image InspectionReports into a single FusedInspection.

    Strategy:
      1. Filter to valid reports with detected damage.
      2. Group findings by normalized damage type.
      3. Merge each group into a FusedFinding (worst severity, max confidence,
         max damage %, deduplicated lists).
      4. Compute overall metrics.
      5. Rank images by damage percentage.
      6. Generate executive summary text.
      7. Build timeline.
      8. Collect maintenance tips.

    Args:
        reports: List of InspectionReport from the AI pipeline.

    Returns:
        FusedInspection dataclass.
    """
    if not reports:
        return FusedInspection()

      # Filter valid reports with actual damage
    valid = [r for r in reports if r.validation_passed]

    # Reports that actually contain image data
    processable = [
        r for r in reports
        if r.image_width > 0 or r.image_height > 0
    ]

    # Use validated reports for damage analysis.
    damaged = [
        r for r in valid
        if r.damage_percentage > 0.1 or r.contour_count > 0
    ]

    # Count all reports that actually reached the inspection pipeline.
    total_images = len(processable) if processable else len(reports)

    total_time = sum(
        r.total_processing_time_sec
        for r in reports
    )

    if not damaged:
        # No damage detected — return clean inspection
        health = assess_health([], fused=None)
        return FusedInspection(
            total_images=total_images,
            total_findings=0,
            total_repair_area_px=0,
            overall_estimated_cost_min=0,
            overall_estimated_cost_max=0,
            executive_summary=(
                f"Inspection of {total_images} images completed. "
                "No significant damage detected."
            ),
            health_report=health,
            total_processing_time_sec=total_time,
        )

    # ── Step 1: Group by damage type ────────────────────────────────────
    groups: dict[str, list[InspectionReport]] = {}
    for r in damaged:
        canonical = _normalize_damage_type(r.damage_type)
        if canonical not in groups:
            groups[canonical] = []
        groups[canonical].append(r)

    # ── Step 2: Merge each group into a FusedFinding ────────────────────
    fused_findings: list[FusedFinding] = []

    for damage_type, group_reports in groups.items():
        # Severity: take the worst
        worst_sev = min(
            (r.severity for r in group_reports if r.severity in _SEVERITY_ORDER),
            key=lambda s: _SEVERITY_ORDER.get(s, 99),
            default="Medium",
        )

        # Confidence: take the maximum
        max_conf = max(r.confidence for r in group_reports)

        # Damage %: take the maximum from any single image
        max_dmg_pct = max(r.damage_percentage for r in group_reports)

        # Affected images
        affected = _deduplicate([r.file_name for r in group_reports if r.file_name])

        # Merge causes, steps, tips
        all_causes = []
        all_steps = []
        all_tips = []
        professionals: set[str] = set()
        for r in group_reports:
            all_causes.extend(r.possible_causes or [])
            all_steps.extend(r.repair_steps or [])
            all_tips.extend(r.prevention_tips or [])
            if r.recommended_professional and r.recommended_professional != "N/A":
                professionals.add(r.recommended_professional)

        # Parse cost ranges
        cost_mins, cost_maxs = [], []
        for r in group_reports:
            lo, hi = _parse_cost(r.estimated_cost_range)
            if lo > 0 or hi > 0:
                cost_mins.append(lo)
                cost_maxs.append(hi)

        if not cost_mins:
            # Fall back to severity-based estimate
            lo, hi = _COST_MAP.get(worst_sev, (2000, 5000))
            cost_mins = [lo]
            cost_maxs = [hi]

        est_min = sum(cost_mins)
        est_max = sum(cost_maxs)

        # Urgency: derive from worst severity
        urgency_map = {
            "Critical": "Immediate attention required",
            "High": "Schedule within 7 days",
            "Medium": "Schedule within 30 days",
            "Low": "No urgency — cosmetic",
        }
        urgency = urgency_map.get(worst_sev, "Schedule within 30 days")

        fused_findings.append(FusedFinding(
            damage_type=damage_type,
            severity=worst_sev,
            confidence=max_conf,
            damage_pct=round(max_dmg_pct, 2),
            affected_images=affected,
            image_count=len(affected),
            possible_causes=_deduplicate(all_causes) or ["Unknown — expert review recommended"],
            repair_steps=_deduplicate(all_steps) or ["Contact a certified inspector for assessment"],
            recommended_professional=", ".join(sorted(professionals)) if professionals else "Structural Engineer",
            estimated_cost_range=f"{est_min:,} - {est_max:,}",
            urgency=urgency,
            prevention_tips=_deduplicate(all_tips) or ["Regular inspection recommended"],
        ))

    # ── Step 3: Sort findings by severity (worst first) ────────────────
    fused_findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))

    # ── Step 4: Compute overall metrics ────────────────────────────────
    # Damage %: take the maximum across all images
    overall_dmg_pct = max(r.damage_percentage for r in damaged)

    # Confidence: average across all damaged images
    overall_conf = sum(r.confidence for r in damaged) / len(damaged)

    # Severity: take the worst across all findings
    overall_severity = min(
        (f.severity for f in fused_findings),
        key=lambda s: _SEVERITY_ORDER.get(s, 99),
        default="Low",
    )

    # Cost: sum all fused findings
    all_cost_mins, all_cost_maxs = [], []
    for f in fused_findings:
        lo, hi = _parse_cost(f.estimated_cost_range)
        if lo > 0 or hi > 0:
            all_cost_mins.append(lo)
            all_cost_maxs.append(hi)
    total_cost_min = sum(all_cost_mins) if all_cost_mins else 0
    total_cost_max = sum(all_cost_maxs) if all_cost_maxs else 0

    # ── Step 5: Authoritative health score from risk engine ─────────────
    worst_report = max(damaged, key=lambda r: _SEVERITY_ORDER.get(r.severity, 99))
    risk = assess_risk([worst_report])

    # Override with fused findings for accuracy
    n_findings = len(fused_findings)
    sev_weight = _SEVERITY_WEIGHTS.get(overall_severity, 0.0)
    health_score = risk.health_score

    # Update risk with fused aggregate values (keep authoritative health_score)
    risk = RiskAssessment(
        overall_risk_score=round(100 - health_score, 1),
        risk_level=risk.risk_level,
        risk_color=risk.risk_color,
        risk_bg=risk.risk_bg,
        health_score=health_score,
        total_findings=n_findings,
        avg_damage_pct=round(overall_dmg_pct, 2),
        max_damage_pct=round(overall_dmg_pct, 2),
        avg_confidence=round(overall_conf, 1),
        avg_severity=sev_weight,
        estimated_cost_min=total_cost_min,
        estimated_cost_max=total_cost_max,
        critical_count=sum(1 for f in fused_findings if f.severity == "Critical"),
        high_count=sum(1 for f in fused_findings if f.severity == "High"),
        medium_count=sum(1 for f in fused_findings if f.severity == "Medium"),
        low_count=sum(1 for f in fused_findings if f.severity == "Low"),
    )

    # ── Step 6: Image ranking ──────────────────────────────────────────
    ranked = sorted(damaged, key=lambda r: r.damage_percentage, reverse=True)
    image_rankings = [
        ImageRank(
            rank=i + 1,
            file_name=r.file_name,
            damage_pct=round(r.damage_percentage, 2),
            severity=r.severity if r.severity != "N/A" else "Low",
            damage_type=r.damage_type if r.damage_type != "N/A" else "General",
            confidence=r.confidence,
        )
        for i, r in enumerate(ranked)
    ]

    # ── Step 7: Timeline ────────────────────────────────────────────────
    severity_to_bucket = {
        "Critical": "immediate",
        "High": "within_7_days",
        "Medium": "within_30_days",
        "Low": "future_monitoring",
        "N/A": "future_monitoring",
        "": "future_monitoring",
    }
    bucket_meta = {
        "immediate": ("Immediate", "#EF4444"),
        "within_7_days": ("Within 7 Days", "#F97316"),
        "within_30_days": ("Within 30 Days", "#F59E0B"),
        "future_monitoring": ("Future Monitoring", "#10B981"),
    }

    from streamlit_app.report.summary_engine import TimelineEntry
    buckets: dict[str, list[FusedFinding]] = {
        "immediate": [],
        "within_7_days": [],
        "within_30_days": [],
        "future_monitoring": [],
    }
    for f in fused_findings:
        bkey = severity_to_bucket.get(f.severity, "future_monitoring")
        buckets[bkey].append(f)

    timeline = [
        TimelineEntry(bucket=display, findings=items, icon="", color=color)
        for bkey, (display, color) in bucket_meta.items()
        for items in [buckets[bkey]]
    ]

    # ── Step 8: Maintenance tips ────────────────────────────────────────
    all_tips_merged: list[str] = []
    for r in damaged:
        all_tips_merged.extend(r.prevention_tips or [])
    maintenance_tips = _deduplicate(all_tips_merged) or [
        "Schedule professional inspections every 6 months",
        "Address water leaks immediately to prevent secondary damage",
        "Monitor crack widths monthly — growing cracks need urgent attention",
        "Ensure proper ventilation to reduce moisture buildup",
    ]

    # ── Step 9: Generate AI text summaries ──────────────────────────────
    executive_summary = _generate_executive_summary(
        total_images=total_images,
        damaged_count=len(damaged),
        findings=fused_findings,
        risk=risk,
        total_cost_min=total_cost_min,
        total_cost_max=total_cost_max,
    )

    property_summary = _generate_property_summary(
        total_images=total_images,
        findings=fused_findings,
        overall_severity=overall_severity,
    )

    inspection_conclusion = _generate_conclusion(
        findings=fused_findings,
        risk=risk,
        overall_severity=overall_severity,
    )

    # ── Step 10: Aggregate measurement data ─────────────────────────────
    total_repair_area = 0
    crack_widths: list[float] = []
    largest_region = None
    largest_area = 0

    for r in valid:
        mr = r.measurement_report
        if mr:
            total_repair_area += mr.total_repair_area_px
            if mr.avg_crack_width > 0:
                crack_widths.append(mr.avg_crack_width)
            if mr.largest_region and mr.largest_region.area_px > largest_area:
                largest_area = mr.largest_region.area_px
                largest_region = mr.largest_region

    avg_crack_width = (
        round(sum(crack_widths) / len(crack_widths), 1) if crack_widths else 0.0
    )

    # ── Step 11: Property Health Intelligence ────────────────────────────
    health_report = assess_health(damaged)

    return FusedInspection(
        overall_damage_pct=round(overall_dmg_pct, 2),
        overall_confidence=round(overall_conf, 1),
        overall_severity=overall_severity,
        overall_health_score=health_score,
        overall_estimated_cost_min=total_cost_min,
        overall_estimated_cost_max=total_cost_max,
        total_repair_area_px=total_repair_area,
        avg_crack_width_px=avg_crack_width,
        findings=fused_findings,
        image_rankings=image_rankings,
        executive_summary=executive_summary,
        property_summary=property_summary,
        inspection_conclusion=inspection_conclusion,
        timeline=timeline,
        maintenance_tips=maintenance_tips,
        total_images=total_images,
        total_findings=n_findings,
        processing_time_sec=round(total_time, 3),
        risk_assessment=risk,
        source_reports=list(reports),
        health_report=health_report,
        comparison_report=None,
    )


def attach_comparison_report(fused: FusedInspection, comparison: ComparisonReport) -> FusedInspection:
    """Attach a ComparisonReport to an existing FusedInspection.

    This is the non-mutating way to add comparison data to a fused inspection
    result.  Used by the results page after running comparison logic.

    Args:
        fused:      Existing FusedInspection result.
        comparison: ComparisonReport from compare_inspections().

    Returns:
        A new FusedInspection with the comparison_report field populated.
    """
    return FusedInspection(
        overall_damage_pct=fused.overall_damage_pct,
        overall_confidence=fused.overall_confidence,
        overall_severity=fused.overall_severity,
        overall_health_score=fused.overall_health_score,
        overall_estimated_cost_min=fused.overall_estimated_cost_min,
        overall_estimated_cost_max=fused.overall_estimated_cost_max,
        total_repair_area_px=fused.total_repair_area_px,
        avg_crack_width_px=fused.avg_crack_width_px,
        findings=fused.findings,
        image_rankings=fused.image_rankings,
        executive_summary=fused.executive_summary,
        property_summary=fused.property_summary,
        inspection_conclusion=fused.inspection_conclusion,
        timeline=fused.timeline,
        maintenance_tips=fused.maintenance_tips,
        total_images=fused.total_images,
        total_findings=fused.total_findings,
        processing_time_sec=fused.processing_time_sec,
        risk_assessment=fused.risk_assessment,
        source_reports=fused.source_reports,
        health_report=fused.health_report,
        comparison_report=comparison,
    )


# ── Text generation (rule-based, no API required) ─────────────────────────────

def _generate_executive_summary(
    total_images: int,
    damaged_count: int,
    findings: list[FusedFinding],
    risk: RiskAssessment,
    total_cost_min: int,
    total_cost_max: int,
) -> str:
    """Generate a professional executive summary (max 8 sentences)."""
    lines: list[str] = []

    lines.append(
        f"This inspection analyzed {total_images} image{'s' if total_images != 1 else ''} "
        f"and identified {len(findings)} distinct type{'s' if len(findings) != 1 else ''} "
        f"of property damage across the inspected areas."
    )

    if damaged_count < total_images:
        lines.append(
            f"{total_images - damaged_count} image{'s' if total_images - damaged_count != 1 else ''} "
            f"showed no significant damage."
        )

    # Severity breakdown
    crit = sum(1 for f in findings if f.severity == "Critical")
    high = sum(1 for f in findings if f.severity == "High")
    med = sum(1 for f in findings if f.severity == "Medium")
    low = sum(1 for f in findings if f.severity == "Low")

    if crit > 0:
        lines.append(
            f"{crit} critical issue{'s' if crit != 1 else ''} require{'s' if crit == 1 else ''} "
            f"immediate attention to prevent further structural deterioration."
        )
    if high > 0:
        lines.append(
            f"{high} high-priority issue{'s' if high != 1 else ''} should be addressed within 7 days."
        )
    if med > 0:
        lines.append(
            f"{med} medium-severity issue{'s' if med != 1 else ''} is recommended for repair within 30 days."
        )
    if low > 0:
        lines.append(
            f"{low} minor issue{'s' if low != 1 else ''} was detected and can be addressed during routine maintenance."
        )

    lines.append(
        f"The overall property health score is {risk.health_score}/100, "
        f"indicating a '{risk.risk_level}' risk level."
    )

    if total_cost_min > 0:
        lines.append(
            f"Estimated repair costs range from {total_cost_min:,} to {total_cost_max:,}, "
            f"depending on the extent of work required."
        )

    lines.append(
        "Professional inspection and timely repairs are recommended to maintain "
        "structural integrity and prevent escalating damage costs."
    )

    # Truncate to 8 sentences
    return " ".join(lines[:8])


def _generate_property_summary(
    total_images: int,
    findings: list[FusedFinding],
    overall_severity: str,
) -> str:
    """Generate a short property-level overview."""
    parts = []
    parts.append(
        f"Inspection covered {total_images} area{'s' if total_images != 1 else ''} "
        f"with {len(findings)} distinct damage type{'s' if len(findings) != 1 else ''} identified."
    )

    damage_types = [f.damage_type for f in findings[:3]]
    if damage_types:
        parts.append(
            f"Primary concerns include: {', '.join(damage_types)}."
        )

    worst = next((f for f in findings if f.severity == "Critical"), None)
    if worst:
        parts.append(
            f"The most urgent issue is {worst.damage_type.lower()} affecting "
            f"{', '.join(worst.affected_images[:2])}."
        )

    return " ".join(parts)


def _generate_conclusion(
    findings: list[FusedFinding],
    risk: RiskAssessment,
    overall_severity: str,
) -> str:
    """Generate a final verdict paragraph."""
    if overall_severity == "Critical":
        return (
            "URGENT: Critical structural damage was detected that poses an immediate risk "
            "to safety and property integrity. All critical findings must be addressed "
            "before the property is considered safe for occupancy. Do not delay repairs."
        )
    elif overall_severity in ("High", "Critical"):
        return (
            "Significant damage was detected that requires prompt professional attention. "
            "While the property remains usable, delays in repair could lead to escalating "
            "costs and further structural issues. A qualified contractor should assess "
            "the property within 7 days."
        )
    elif overall_severity == "Medium":
        return (
            "Moderate damage was detected. The property is structurally sound but "
            "requires attention within 30 days. Recommended repairs should be scheduled "
            "with a qualified professional to prevent deterioration."
        )
    else:
        return (
            "Minor issues were detected. The property is in acceptable condition with "
            "routine maintenance. No urgent repairs are required, but addressing the "
            "identified issues will help maintain long-term property value."
        )


# ── Compatibility: convert FusedInspection → list of InspectionReport ──────────

def to_inspection_reports(fused: FusedInspection) -> list[InspectionReport]:
    """Convert a FusedInspection back to a list of InspectionReport.

    Creates one synthetic InspectionReport per FusedFinding so the
    existing report_builder and risk_engine can consume the merged data
    without modification.

    The original source reports' numpy arrays are attached to the first
    synthetic report so images still display in the results page.
    """
    synthetic_reports: list[InspectionReport] = []

    for i, f in enumerate(fused.findings):
        # Parse cost range back to individual min/max
        lo, hi = _parse_cost(f.estimated_cost_range)

        source = fused.source_reports[i] if i < len(fused.source_reports) else None
        synthetic_reports.append(InspectionReport(
            file_name=f"merged_finding_{i+1}.jpg",
            damage_type=f.damage_type,
            severity=f.severity,
            confidence=f.confidence,
            damage_percentage=f.damage_pct,
            contour_count=f.image_count,
            possible_causes=list(f.possible_causes),
            repair_steps=list(f.repair_steps),
            recommended_professional=f.recommended_professional,
            estimated_cost_range=f.estimated_cost_range,
            urgency=f.urgency,
            prevention_tips=list(f.prevention_tips),
            # Attach overlay from the most damaged image for this finding
            processed_image=getattr(source, "processed_image", None),
            damage_mask=getattr(source, "damage_mask", None),
            heatmap=getattr(source, "heatmap", None),
            overlay_image=getattr(source, "overlay_image", None),
            image_width=getattr(source, "image_width", 0),
            image_height=getattr(source, "image_height", 0),
            file_size_mb=getattr(source, "file_size_mb", 0.0),
            validation_passed=True,
            damage_area_px=0,
            image_area_px=0,
            largest_damage_area_px=0,
            cv_processing_time_sec=0.0,
            gemini_processing_time_sec=0.0,
            total_processing_time_sec=fused.processing_time_sec / max(len(fused.findings), 1),
            gemini_skipped=True,
            measurement_report=getattr(source, "measurement_report", None),
        ))

    return synthetic_reports
