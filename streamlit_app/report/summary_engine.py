"""Summary Engine for InspectAI.

Converts AI inspection reports into structured data for the report builder:
  - Executive summary records
  - Per-finding detail records
  - Timeline categorisation
  - Recommendation sets
  - Inspection checklist items

All functions are pure — they take data in and return dataclass/dict outputs.
No Streamlit or numpy imports here (the report_builder handles rendering).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from streamlit_app.ai.inspection_engine import InspectionReport
from streamlit_app.report.risk_engine import RiskAssessment, assess_risk


# ── Data Types ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FindingRecord:
    """A single damage finding ready for display.

    Attributes:
        file_name:          Source image file.
        damage_type:        Category (e.g. "Crack", "Water Damage").
        severity:           Critical / High / Medium / Low.
        confidence:         Gemini confidence (0-100).
        damage_pct:         Percentage of image affected.
        contour_count:      Number of distinct regions.
        possible_causes:    Likely root causes.
        repair_steps:       Ordered repair instructions.
        recommended_professional: Who to call.
        estimated_cost_range: Cost range string.
        urgency:            Urgency classification.
        prevention_tips:    Maintenance advice.
        image_thumbnail:    Small PIL Image or None.
        overlay_image:      Heatmap overlay (numpy array) or None.
    """
    file_name: str = ""
    damage_type: str = "N/A"
    severity: str = "Medium"
    confidence: int = 0
    damage_pct: float = 0.0
    contour_count: int = 0
    possible_causes: list[str] = field(default_factory=list)
    repair_steps: list[str] = field(default_factory=list)
    recommended_professional: str = "N/A"
    estimated_cost_range: str = "N/A"
    urgency: str = "N/A"
    prevention_tips: list[str] = field(default_factory=list)
    image_thumbnail: Any = None
    overlay_image: Any = None


@dataclass(frozen=True)
class TimelineEntry:
    """A finding placed into a time bucket.

    Attributes:
        bucket:    Immediate / Within 7 Days / Within 30 Days / Future Monitoring
        findings:  List of FindingRecord for this bucket.
        icon:      Emoji for the bucket.
        color:     Hex color.
    """
    bucket: str = ""
    findings: list[FindingRecord] = field(default_factory=list)
    icon: str = ""
    color: str = "#64748B"


@dataclass(frozen=True)
class ExecutiveSummary:
    """Complete executive summary for an inspection session.

    Attributes:
        inspection_id:        Unique ID string.
        inspection_date:      Date the inspection was performed.
        property_name:        Name from property form.
        property_type:        Type of property.
        inspector_name:       Inspector name (from user state or default).
        health_score:         0-100 score.
        risk_level:           Low / Medium / High / Critical.
        risk_color:           Matching hex color.
        total_findings:       Total damage regions detected.
        estimated_cost_min:   Lower repair cost bound.
        estimated_cost_max:   Upper repair cost bound.
        avg_confidence:       Mean AI confidence.
        image_count:          Number of images analysed.
        processing_time_sec:  Total AI processing time.
        property_data:        Raw property form dict.
    """
    inspection_id: str = ""
    inspection_date: str = ""
    property_name: str = ""
    property_type: str = ""
    inspector_name: str = "Inspector"
    health_score: int = 100
    risk_level: str = "Low"
    risk_color: str = "#10B981"
    total_findings: int = 0
    estimated_cost_min: int = 0
    estimated_cost_max: int = 0
    avg_confidence: float = 0.0
    image_count: int = 0
    processing_time_sec: float = 0.0
    property_data: dict = field(default_factory=dict)


# ── Severity → urgency mapping ────────────────────────────────────────────────

_SEVERITY_TO_BUCKET = {
    "Critical": "immediate",
    "High": "within_7_days",
    "Medium": "within_30_days",
    "Low": "future_monitoring",
    "N/A": "future_monitoring",
    "": "future_monitoring",
    None: "future_monitoring",
}

_BUCKET_META = {
    "immediate":       ("🔴 Immediate",     "Immediate",      "#EF4444"),
    "within_7_days":   ("🟠 Within 7 Days", "Within 7 Days",  "#F97316"),
    "within_30_days":  ("🟡 Within 30 Days","Within 30 Days", "#F59E0B"),
    "future_monitoring": ("🟢 Future Monitoring", "Future Monitoring", "#10B981"),
}


# ── Core Engine Functions ──────────────────────────────────────────────────────

def build_executive_summary(
    reports: list[InspectionReport],
    property_data: dict | None = None,
    inspection_id: str = "",
    inspector_name: str = "Inspector",
) -> ExecutiveSummary:
    """Build an executive summary from inspection reports.

    Args:
        reports:          List of InspectionReport from the AI pipeline.
        property_data:    Optional dict from the property form.
        inspection_id:    Unique inspection ID (generated if empty).
        inspector_name:   Name of the inspector.

    Returns:
        ExecutiveSummary dataclass.
    """
    property_data = property_data or {}
    risk = assess_risk(reports)

    # Generate an ID if none provided
    if not inspection_id:
        today = date.today()
        import random
        inspection_id = f"INS-{today.year}-{random.randint(1000, 9999)}"

    today_str = date.today().strftime("%B %d, %Y")

    return ExecutiveSummary(
        inspection_id=inspection_id,
        inspection_date=today_str,
        property_name=property_data.get("property_name", "Unknown Property"),
        property_type=property_data.get("property_type", "Not Specified"),
        inspector_name=inspector_name,
        health_score=risk.health_score,
        risk_level=risk.risk_level,
        risk_color=risk.risk_color,
        total_findings=risk.total_findings,
        estimated_cost_min=risk.estimated_cost_min,
        estimated_cost_max=risk.estimated_cost_max,
        avg_confidence=risk.avg_confidence,
        image_count=len(reports),
        processing_time_sec=sum(r.total_processing_time_sec for r in reports),
        property_data=property_data,
    )


def build_findings(reports: list[InspectionReport]) -> list[FindingRecord]:
    """Convert AI reports into display-ready finding records.

    One FindingRecord per image report (not per contour — keep it simple).

    Args:
        reports: List of InspectionReport.

    Returns:
        List of FindingRecord sorted by severity (Critical first).
    """
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "N/A": 4}
    findings: list[FindingRecord] = []

    for r in reports:
        if not r.validation_passed:
            continue
        if r.contour_count == 0 and r.damage_percentage < 0.1:
            continue  # No significant damage

        # Parse cost range
        lo, hi = 0, 0
        if r.estimated_cost_range and r.estimated_cost_range != "N/A":
            parts = (
                r.estimated_cost_range
                .replace("₹", "")
                .replace(",", "")
                .replace("—", "-")
                .split("-")
            )
            try:
                if len(parts) == 2:
                    lo, hi = int(parts[0].strip()), int(parts[1].strip())
            except (ValueError, IndexError):
                pass

        # Fall back to default cost if Gemini didn't provide one
        if lo == 0 and hi == 0:
            severity = r.severity if r.severity != "N/A" else "Medium"
            cost_map = {
                "Critical": (15000, 50000),
                "High": (8000, 25000),
                "Medium": (3000, 10000),
                "Low": (500, 3000),
            }
            lo, hi = cost_map.get(severity, (2000, 5000))

        findings.append(FindingRecord(
            file_name=r.file_name,
            damage_type=r.damage_type if r.damage_type != "N/A" else "Structural Damage",
            severity=r.severity if r.severity != "N/A" else "Medium",
            confidence=r.confidence if r.confidence > 0 else 75,
            damage_pct=r.damage_percentage,
            contour_count=r.contour_count,
            possible_causes=list(r.possible_causes) if r.possible_causes else ["Unknown — needs expert review"],
            repair_steps=list(r.repair_steps) if r.repair_steps else ["Contact a certified inspector for assessment"],
            recommended_professional=r.recommended_professional if r.recommended_professional != "N/A" else "Structural Engineer",
            estimated_cost_range=f"₹{lo:,} — ₹{hi:,}",
            urgency=r.urgency if r.urgency != "N/A" else "Schedule within 30 days",
            prevention_tips=list(r.prevention_tips) if r.prevention_tips else ["Regular inspection recommended"],
            overlay_image=r.overlay_image,
        ))

    # Sort: Critical → High → Medium → Low → N/A
    findings.sort(key=lambda f: severity_order.get(f.severity, 99))
    return findings


def build_timeline(findings: list[FindingRecord]) -> list[TimelineEntry]:
    """Group findings into a repair timeline.

    Args:
        findings: List of FindingRecord (sorted by severity).

    Returns:
        List of 4 TimelineEntry objects in priority order.
    """
    buckets: dict[str, list[FindingRecord]] = {
        "immediate": [],
        "within_7_days": [],
        "within_30_days": [],
        "future_monitoring": [],
    }

    for f in findings:
        bucket_key = _SEVERITY_TO_BUCKET.get(f.severity, "future_monitoring")
        buckets[bucket_key].append(f)

    entries: list[TimelineEntry] = []
    for bucket_key in ["immediate", "within_7_days", "within_30_days", "future_monitoring"]:
        label, display, color = _BUCKET_META[bucket_key]
        entries.append(TimelineEntry(
            bucket=display,
            findings=buckets[bucket_key],
            icon=label.split(" ")[0],
            color=color,
        ))

    return entries


def build_recommendations(reports: list[InspectionReport]) -> dict[str, list[str]]:
    """Aggregate recommendations from all reports.

    Returns:
        Dict with keys:
            "immediate_actions"    — urgent steps from Critical/High findings.
            "repair_priority"      — ordered repair list for all findings.
            "maintenance_tips"     — prevention advice.
            "professional_help"    — recommended professionals.
    """
    immediate_actions: list[str] = []
    repair_priority: list[str] = []
    maintenance_tips: list[str] = []
    professionals: set[str] = set()

    for r in reports:
        if not r.validation_passed:
            continue

        sev = r.severity if r.severity != "N/A" else "Medium"

        if sev in ("Critical", "High"):
            # First repair step as immediate action
            if r.repair_steps:
                immediate_actions.append(f"[{r.file_name}] {r.repair_steps[0]}")

        # All repair steps
        for step in r.repair_steps:
            repair_priority.append(f"[{r.file_name}] {step}")

        # Prevention tips
        for tip in r.prevention_tips:
            maintenance_tips.append(tip)

        # Professionals
        if r.recommended_professional and r.recommended_professional != "N/A":
            professionals.add(r.recommended_professional)

    # Deduplicate while preserving order
    def _dedup(items: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    return {
        "immediate_actions": _dedup(immediate_actions),
        "repair_priority": _dedup(repair_priority),
        "maintenance_tips": _dedup(maintenance_tips) or ["Schedule regular inspections every 6 months"],
        "professional_help": sorted(professionals) or ["Structural Engineer", "General Contractor"],
    }


def build_checklist(reports: list[InspectionReport]) -> list[dict[str, Any]]:
    """Generate a completed inspection checklist.

    The checklist covers all standard inspection categories, marking each
    as checked if damage was detected in that category, or as "noted"
    if the area was inspected and found clean.

    Args:
        reports: List of InspectionReport.

    Returns:
        List of checklist item dicts.
    """
    # Map damage types to inspection categories
    category_map = {
        "Crack":             "Structural Cracks",
        "Water Damage":      "Water Damage / Stains",
        "Paint Peeling":     "Paint Condition",
        "Mold":              "Mold / Fungus",
        "Roof Damage":       "Roof Condition",
        "Foundation Issue":  "Foundation / Structural",
        "Electrical":        "Electrical Systems",
        "Plumbing":          "Plumbing Systems",
        "Termite Damage":    "Pest / Termite Damage",
        "Structural Damage": "Structural Integrity",
    }

    # Collect all categories from reports
    detected_categories: set[str] = set()
    for r in reports:
        if not r.validation_passed:
            continue
        # Map damage_type to category
        dtype = r.damage_type if r.damage_type != "N/A" else ""
        for key, cat in category_map.items():
            if key.lower() in dtype.lower():
                detected_categories.add(cat)
        if not detected_categories and r.contour_count > 0:
            detected_categories.add("General Damage Assessment")

    # Build checklist
    all_categories = [
        "Structural Cracks",
        "Foundation / Structural",
        "Water Damage / Stains",
        "Paint Condition",
        "Mold / Fungus",
        "Electrical Systems",
        "Plumbing Systems",
        "Pest / Termite Damage",
        "Roof Condition",
        "Ventilation",
        "General Damage Assessment",
    ]

    checklist: list[dict[str, Any]] = []
    for cat in all_categories:
        if cat in detected_categories:
            status = "checked"
            note = "Issues detected — see findings"
        else:
            status = "noted"
            note = "Inspected — no issues found"
        checklist.append({
            "category": cat,
            "status": status,
            "note": note,
        })

    return checklist
