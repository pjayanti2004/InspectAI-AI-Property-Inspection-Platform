"""Smart Inspection Comparison & Change Detection Engine for InspectAI.

Compares current inspection against a previous inspection to detect changes
in property health over time.

Design:
  • Pure logic — no Streamlit imports
  • Rule-based — no ML required
  • Consumes two FusedInspection objects (or serialized dicts)
  • Produces ComparisonReport consumed by results page + report builder

Change Detection:
  • New damage — present now but not in previous inspection
  • Resolved damage — was present before but not now
  • Increased damage — same type, higher severity/area now
  • Reduced damage — same type, lower severity/area now

Metrics compared:
  • Overall health score
  • Overall grade
  • Total damage %
  • Damage types
  • Severity levels
  • Repair area (px)
  • Crack length/width
  • Moisture levels
  • Repair cost
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Data Types ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class InspectionSnapshot:
    """A serializable snapshot of an inspection for comparison.

    Attributes:
        inspection_id:       Unique inspection identifier.
        inspection_date:     Date string (YYYY-MM-DD).
        health_score:        Overall health score (0-100).
        grade:               Letter grade (A+ → D).
        total_damage_pct:    Total damage percentage.
        total_findings:      Number of distinct findings.
        total_repair_cost:   Total estimated repair cost (INR).
        total_repair_area_px: Total repair area in pixels.
        avg_crack_width_px:  Average crack width.
        moisture_level:      Moisture assessment ("Low"/"Medium"/"High"/"Critical").
        critical_count:      Number of critical findings.
        high_count:          Number of high-severity findings.
        medium_count:        Number of medium-severity findings.
        low_count:           Number of low-severity findings.
        damage_types:        List of damage types found.
        summary:             Short summary text.
    """
    inspection_id: str = ""
    inspection_date: str = ""
    health_score: float = 0.0
    grade: str = "D"
    total_damage_pct: float = 0.0
    total_findings: int = 0
    total_repair_cost: int = 0
    total_repair_area_px: int = 0
    avg_crack_width_px: float = 0.0
    moisture_level: str = "Low"
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    damage_types: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass(frozen=True)
class ComparisonFinding:
    """A change detected between two inspections for a specific damage type.

    Attributes:
        damage_type:    Type of damage.
        change_type:    "new" / "resolved" / "increased" / "reduced" / "unchanged".
        previous_severity: Severity in previous inspection.
        current_severity:  Severity in current inspection.
        previous_damage_pct: Damage % in previous inspection.
        current_damage_pct:  Damage % in current inspection.
        previous_area_px:    Repair area in previous inspection.
        current_area_px:     Repair area in current inspection.
        delta_pct:         Change in damage % (positive = worse).
        delta_area_px:     Change in repair area (positive = worse).
        severity_delta:    "up" / "down" / "same".
        recommendation:    Action recommended based on change.
    """
    damage_type: str = ""
    change_type: str = "unchanged"
    previous_severity: str = "N/A"
    current_severity: str = "N/A"
    previous_damage_pct: float = 0.0
    current_damage_pct: float = 0.0
    previous_area_px: int = 0
    current_area_px: int = 0
    delta_pct: float = 0.0
    delta_area_px: int = 0
    severity_delta: str = "same"
    recommendation: str = ""


@dataclass(frozen=True)
class ComparisonReport:
    """Complete comparison report between two inspections.

    Attributes:
        previous:              Previous inspection snapshot.
        current:               Current inspection snapshot.
        findings:              List of ComparisonFinding objects.
        health_score_delta:    Change in health score (negative = worse).
        grade_changed:         Whether grade changed.
        previous_grade:        Previous letter grade.
        current_grade:         Current letter grade.
        damage_delta_pct:      Change in total damage %.
        new_damage_count:      Number of new damage types.
        resolved_damage_count: Number of resolved damage types.
        increased_count:       Number of increased damage types.
        reduced_count:         Number of reduced damage types.
        unchanged_count:       Number of unchanged damage types.
        improvement_score:     0-100 score (100 = perfect improvement).
        damage_growth_pct:     Overall damage growth percentage.
        repair_effectiveness_pct: How effective repairs were (0-100).
        risk_trend:            "Improving" / "Stable" / "Deteriorating".
        comparison_summary:    AI-generated summary (max 8 sentences).
        days_between:          Days between the two inspections.
    """
    previous: InspectionSnapshot = None
    current: InspectionSnapshot = None
    findings: list[ComparisonFinding] = field(default_factory=list)
    health_score_delta: float = 0.0
    grade_changed: bool = False
    previous_grade: str = "D"
    current_grade: str = "D"
    damage_delta_pct: float = 0.0
    new_damage_count: int = 0
    resolved_damage_count: int = 0
    increased_count: int = 0
    reduced_count: int = 0
    unchanged_count: int = 0
    improvement_score: float = 0.0
    damage_growth_pct: float = 0.0
    repair_effectiveness_pct: float = 0.0
    risk_trend: str = "Stable"
    comparison_summary: str = ""
    days_between: int = 0


# ── Grade helpers ──────────────────────────────────────────────────────────────

_GRADE_SCORES = {
    "A+": 95, "A": 85, "B+": 75, "B": 65, "C": 55, "D": 45,
}
_GRADE_ORDER = ["A+", "A", "B+", "B", "C", "D"]


def _grade_to_score(grade: str) -> int:
    return _GRADE_SCORES.get(grade, 45)


def _score_to_grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B+"
    if score >= 60:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def _severity_rank(severity: str) -> int:
    return {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "N/A": 4, "": 5}.get(severity, 5)


# ── Snapshot builders ──────────────────────────────────────────────────────────

def _snapshot_from_fused(fused, inspection_id: str = "", inspection_date: str = "") -> InspectionSnapshot:
    """Build an InspectionSnapshot from a FusedInspection or dict."""
    if hasattr(fused, "to_dict"):
        f = fused
    elif isinstance(fused, dict):
        # Reconstruct minimal fields from dict
        class _DictWrapper:
            pass
        f = _DictWrapper()
        for k, v in fused.items():
            setattr(f, k, v)
    else:
        f = fused

    # Determine moisture level from findings
    moisture_level = "Low"
    if hasattr(f, "findings") and f.findings:
        moisture_findings = [
            finding for finding in f.findings
            if hasattr(finding, 'damage_type') and 'moisture' in finding.damage_type.lower()
            or hasattr(finding, 'damage_type') and 'water' in finding.damage_type.lower()
        ]
        if moisture_findings:
            worst = min(moisture_findings, key=lambda x: _severity_rank(getattr(x, 'severity', 'Low')))
            moisture_level = getattr(worst, 'severity', 'Low')

    health_score = getattr(f, 'overall_health_score', getattr(f, 'health_score', 50))
    grade = getattr(f, 'overall_grade', getattr(f, 'grade', _score_to_grade(health_score)))
    if hasattr(grade, 'value'):
        grade = grade.value

    damage_types = []
    if hasattr(f, 'findings') and f.findings:
        damage_types = [finding.damage_type for finding in f.findings if hasattr(finding, 'damage_type')]
    elif hasattr(f, 'findings') and isinstance(f.findings, list):
        for finding in f.findings:
            if isinstance(finding, dict):
                damage_types.append(finding.get('damage_type', ''))

    return InspectionSnapshot(
        inspection_id=inspection_id,
        inspection_date=inspection_date,
        health_score=health_score,
        grade=grade,
        total_damage_pct=getattr(f, 'overall_damage_pct', 0.0),
        total_findings=getattr(f, 'total_findings', 0),
        total_repair_cost=getattr(f, 'overall_estimated_cost_max', 0),
        total_repair_area_px=getattr(f, 'total_repair_area_px', 0),
        avg_crack_width_px=getattr(f, 'avg_crack_width_px', 0.0),
        moisture_level=moisture_level,
        critical_count=getattr(getattr(f, 'risk_assessment', None), 'critical_count', 0) if hasattr(f, 'risk_assessment') else 0,
        high_count=getattr(getattr(f, 'risk_assessment', None), 'high_count', 0) if hasattr(f, 'risk_assessment') else 0,
        medium_count=getattr(getattr(f, 'risk_assessment', None), 'medium_count', 0) if hasattr(f, 'risk_assessment') else 0,
        low_count=getattr(getattr(f, 'risk_assessment', None), 'low_count', 0) if hasattr(f, 'risk_assessment') else 0,
        damage_types=damage_types,
        summary=getattr(f, 'inspection_conclusion', ''),
    )


# ── Core comparison logic ──────────────────────────────────────────────────────

def _compare_findings(
    previous_types: list[str],
    current_types: list[str],
    previous_findings: list,
    current_findings: list,
) -> list[ComparisonFinding]:
    """Compare findings between two inspections."""
    results: list[ComparisonFinding] = []

    # Normalize findings into dict by damage_type
    def findings_to_map(findings) -> dict[str, dict]:
        m = {}
        for finding in findings:
            if hasattr(finding, 'damage_type'):
                dtype = finding.damage_type
                m[dtype] = {
                    'severity': getattr(finding, 'severity', 'Low'),
                    'damage_pct': getattr(finding, 'damage_pct', 0.0),
                    'area_px': getattr(finding, 'damage_pct', 0.0) * 1000,  # rough px estimate
                    'confidence': getattr(finding, 'confidence', 0),
                }
            elif isinstance(finding, dict):
                dtype = finding.get('damage_type', '')
                m[dtype] = {
                    'severity': finding.get('severity', 'Low'),
                    'damage_pct': finding.get('damage_pct', 0.0),
                    'area_px': finding.get('damage_pct', 0.0) * 1000,
                    'confidence': finding.get('confidence', 0),
                }
        return m

    prev_map = findings_to_map(previous_findings)
    curr_map = findings_to_map(current_findings)

    # Normalize damage type names for matching
    def normalize(dtype: str) -> str:
        return dtype.lower().strip().replace("_", " ").replace("-", " ")

    norm_prev = {normalize(k): (k, v) for k, v in prev_map.items()}
    norm_curr = {normalize(k): (k, v) for k, v in curr_map.items()}

    all_types = set(norm_prev.keys()) | set(norm_curr.keys())

    for norm_type in all_types:
        # Find matching entries
        prev_entry = norm_prev.get(norm_type)
        curr_entry = norm_curr.get(norm_type)

        if prev_entry and curr_entry:
            # Exists in both — compare
            _, prev_data = prev_entry
            _, curr_data = curr_entry

            prev_sev = prev_data['severity']
            curr_sev = curr_data['severity']
            prev_pct = prev_data['damage_pct']
            curr_pct = curr_data['damage_pct']
            prev_area = prev_data['area_px']
            curr_area = curr_data['area_px']

            delta_pct = curr_pct - prev_pct
            delta_area = int(curr_area - prev_area)
            sev_delta = "same"
            if _severity_rank(curr_sev) < _severity_rank(prev_sev):
                sev_delta = "up"  # worse
            elif _severity_rank(curr_sev) > _severity_rank(prev_sev):
                sev_delta = "down"  # improved

            if abs(delta_pct) < 0.5 and sev_delta == "same":
                change_type = "unchanged"
            elif delta_pct > 0.5 or sev_delta == "up":
                change_type = "increased"
            else:
                change_type = "reduced"

            # Recommendation
            if change_type == "increased":
                recommendation = f"Urgent: {curr_sev} priority — schedule repair immediately"
            elif change_type == "reduced":
                recommendation = f"Positive trend — {curr_sev} priority — continue monitoring"
            else:
                recommendation = f"No significant change — {curr_sev} priority — routine monitoring"

            results.append(ComparisonFinding(
                damage_type=curr_entry[0] if curr_entry else prev_entry[0],
                change_type=change_type,
                previous_severity=prev_sev,
                current_severity=curr_sev,
                previous_damage_pct=prev_pct,
                current_damage_pct=curr_pct,
                previous_area_px=int(prev_area),
                current_area_px=int(curr_area),
                delta_pct=round(delta_pct, 2),
                delta_area_px=delta_area,
                severity_delta=sev_delta,
                recommendation=recommendation,
            ))

        elif curr_entry and not prev_entry:
            # New damage
            dtype, data = curr_entry
            results.append(ComparisonFinding(
                damage_type=dtype,
                change_type="new",
                previous_severity="N/A",
                current_severity=data['severity'],
                previous_damage_pct=0.0,
                current_damage_pct=data['damage_pct'],
                previous_area_px=0,
                current_area_px=int(data['area_px']),
                delta_pct=round(data['damage_pct'], 2),
                delta_area_px=int(data['area_px']),
                severity_delta="up",
                recommendation=f"New {data['severity']} finding — address {data['severity'].lower()} priority",
            ))

        elif prev_entry and not curr_entry:
            # Resolved damage
            dtype, data = prev_entry
            results.append(ComparisonFinding(
                damage_type=dtype,
                change_type="resolved",
                previous_severity=data['severity'],
                current_severity="N/A",
                previous_damage_pct=data['damage_pct'],
                current_damage_pct=0.0,
                previous_area_px=int(data['area_px']),
                current_area_px=0,
                delta_pct=round(-data['damage_pct'], 2),
                delta_area_px=int(-data['area_px']),
                severity_delta="down",
                recommendation=f"Resolved — no action required, continue routine monitoring",
            ))

    return results


def _compute_scores(findings: list[ComparisonFinding], prev_snap: InspectionSnapshot, curr_snap: InspectionSnapshot) -> tuple[float, float, float, str]:
    """Compute improvement score, damage growth %, repair effectiveness, and risk trend."""
    if not findings:
        return 100.0, 0.0, 100.0, "Stable"

    new_count = sum(1 for f in findings if f.change_type == "new")
    resolved_count = sum(1 for f in findings if f.change_type == "resolved")
    increased_count = sum(1 for f in findings if f.change_type == "increased")
    reduced_count = sum(1 for f in findings if f.change_type == "reduced")
    unchanged_count = sum(1 for f in findings if f.change_type == "unchanged")

    # Damage growth % — how much total damage grew
    if prev_snap.total_damage_pct > 0:
        damage_growth = ((curr_snap.total_damage_pct - prev_snap.total_damage_pct) / prev_snap.total_damage_pct) * 100
    elif curr_snap.total_damage_pct > 0:
        damage_growth = 100.0  # New damage from zero
    else:
        damage_growth = 0.0
    damage_growth = round(damage_growth, 1)

    # Repair effectiveness — how well did repairs work
    if resolved_count > 0 or reduced_count > 0:
        total_resolved = resolved_count + reduced_count
        repair_eff = min(100.0, (total_resolved / max(len(findings), 1)) * 100 + 50)
    elif increased_count > 0 or new_count > 0:
        repair_eff = max(0.0, 50 - (new_count + increased_count) * 10)
    else:
        repair_eff = 50.0
    repair_eff = round(repair_eff, 1)

    # Improvement score — composite
    health_delta = curr_snap.health_score - prev_snap.health_score
    score = 50.0  # Base
    score += health_delta * 0.5  # Health score improvement
    score += resolved_count * 8  # Bonus for resolved
    score += reduced_count * 5   # Bonus for reduced
    score -= new_count * 10      # Penalty for new
    score -= increased_count * 8 # Penalty for increased
    score -= damage_growth * 0.3 # Penalty for growth
    score = max(0.0, min(100.0, score))
    improvement_score = round(score, 1)

    # Risk trend
    if health_delta > 5 and damage_growth < -10:
        risk_trend = "Improving"
    elif health_delta < -5 or damage_growth > 20:
        risk_trend = "Deteriorating"
    elif abs(health_delta) <= 5 and abs(damage_growth) <= 10:
        risk_trend = "Stable"
    elif health_delta > 0:
        risk_trend = "Improving"
    else:
        risk_trend = "Deteriorating"

    return improvement_score, damage_growth, repair_eff, risk_trend


def _generate_comparison_summary(
    prev: InspectionSnapshot,
    curr: InspectionSnapshot,
    findings: list[ComparisonFinding],
    improvement_score: float,
    risk_trend: str,
) -> str:
    """Generate AI comparison summary (max 8 sentences)."""
    lines = []

    health_delta = curr.health_score - prev.health_score
    grade_changed = prev.grade != curr.grade

    lines.append(
        f"Comparing inspection {prev.inspection_id or 'previous'} ({prev.inspection_date or 'unknown date'}) "
        f"with current inspection ({curr.inspection_date or 'current'})."
    )

    if health_delta > 0:
        lines.append(
            f"Health score improved by {health_delta:.0f} points from {prev.health_score:.0f} to {curr.health_score:.0f}."
        )
    elif health_delta < 0:
        lines.append(
            f"Health score declined by {abs(health_delta):.0f} points from {prev.health_score:.0f} to {curr.health_score:.0f}."
        )
    else:
        lines.append("Health score remained stable.")

    if grade_changed:
        lines.append(f"Grade changed from {prev.grade} to {curr.grade}.")
    else:
        lines.append(f"Grade remains {curr.grade}.")

    new_dmg = [f for f in findings if f.change_type == "new"]
    resolved_dmg = [f for f in findings if f.change_type == "resolved"]
    if new_dmg:
        names = ", ".join(f.damage_type for f in new_dmg[:3])
        lines.append(f"New damage detected: {names}.")
    if resolved_dmg:
        names = ", ".join(f.damage_type for f in resolved_dmg[:3])
        lines.append(f"Resolved damage: {names}.")

    increased = [f for f in findings if f.change_type == "increased"]
    if increased:
        lines.append(f"{len(increased)} existing issue(s) worsened in severity or extent.")

    lines.append(f"Risk trend: {risk_trend}. Improvement score: {improvement_score:.0f}/100.")

    return " ".join(lines[:8])


# ── Main Entry Point ───────────────────────────────────────────────────────────

def compare_inspections(
    previous,
    current,
    previous_id: str = "",
    current_id: str = "",
    previous_date: str = "",
    current_date: str = "",
) -> ComparisonReport:
    """Compare two inspections and generate a change detection report.

    Args:
        previous:         Previous FusedInspection or serialized dict.
        current:          Current FusedInspection or serialized dict.
        previous_id:      Previous inspection ID string.
        current_id:       Current inspection ID string.
        previous_date:    Previous inspection date string.
        current_date:     Current inspection date string.

    Returns:
        ComparisonReport with all change detection data.
    """
    # ── Step 1: Build snapshots ───────────────────────────────────────────
    prev_snap = _snapshot_from_fused(previous, previous_id, previous_date)
    curr_snap = _snapshot_from_fused(current, current_id, current_date)

    # ── Step 2: Compare findings ──────────────────────────────────────────
    findings = _compare_findings(
        prev_snap.damage_types,
        curr_snap.damage_types,
        getattr(previous, 'findings', []) if hasattr(previous, 'findings') else [],
        getattr(current, 'findings', []) if hasattr(current, 'findings') else [],
    )

    # ── Step 3: Counts ────────────────────────────────────────────────────
    new_count = sum(1 for f in findings if f.change_type == "new")
    resolved_count = sum(1 for f in findings if f.change_type == "resolved")
    increased_count = sum(1 for f in findings if f.change_type == "increased")
    reduced_count = sum(1 for f in findings if f.change_type == "reduced")
    unchanged_count = sum(1 for f in findings if f.change_type == "unchanged")

    # ── Step 4: Deltas ───────────────────────────────────────────────────
    health_delta = round(curr_snap.health_score - prev_snap.health_score, 1)
    grade_changed = prev_snap.grade != curr_snap.grade
    damage_delta = round(curr_snap.total_damage_pct - prev_snap.total_damage_pct, 2)

    # ── Step 5: Scores ───────────────────────────────────────────────────
    improvement_score, damage_growth, repair_eff, risk_trend = _compute_scores(
        findings, prev_snap, curr_snap
    )

    # ── Step 6: Days between ─────────────────────────────────────────────
    days_between = 0
    if previous_date and current_date:
        try:
            from datetime import datetime
            fmt = "%Y-%m-%d"
            d1 = datetime.strptime(previous_date[:10], fmt)
            d2 = datetime.strptime(current_date[:10], fmt)
            days_between = (d2 - d1).days
        except Exception:
            days_between = 0

    # ── Step 7: Summary ──────────────────────────────────────────────────
    comparison_summary = _generate_comparison_summary(
        prev_snap, curr_snap, findings, improvement_score, risk_trend,
    )

    return ComparisonReport(
        previous=prev_snap,
        current=curr_snap,
        findings=findings,
        health_score_delta=health_delta,
        grade_changed=grade_changed,
        previous_grade=prev_snap.grade,
        current_grade=curr_snap.grade,
        damage_delta_pct=damage_delta,
        new_damage_count=new_count,
        resolved_damage_count=resolved_count,
        increased_count=increased_count,
        reduced_count=reduced_count,
        unchanged_count=unchanged_count,
        improvement_score=improvement_score,
        damage_growth_pct=damage_growth,
        repair_effectiveness_pct=repair_eff,
        risk_trend=risk_trend,
        comparison_summary=comparison_summary,
        days_between=days_between,
    )


# ── Compatibility helpers ──────────────────────────────────────────────────────

def comparison_report_to_dict(report: ComparisonReport) -> dict:
    """Convert ComparisonReport to a plain dict for session state storage."""
    return {
        "previous": {
            "inspection_id": report.previous.inspection_id,
            "inspection_date": report.previous.inspection_date,
            "health_score": report.previous.health_score,
            "grade": report.previous.grade,
            "total_damage_pct": report.previous.total_damage_pct,
            "total_findings": report.previous.total_findings,
            "total_repair_cost": report.previous.total_repair_cost,
            "total_repair_area_px": report.previous.total_repair_area_px,
            "avg_crack_width_px": report.previous.avg_crack_width_px,
            "moisture_level": report.previous.moisture_level,
            "critical_count": report.previous.critical_count,
            "high_count": report.previous.high_count,
            "medium_count": report.previous.medium_count,
            "low_count": report.previous.low_count,
            "damage_types": report.previous.damage_types,
            "summary": report.previous.summary,
        },
        "current": {
            "inspection_id": report.current.inspection_id,
            "inspection_date": report.current.inspection_date,
            "health_score": report.current.health_score,
            "grade": report.current.grade,
            "total_damage_pct": report.current.total_damage_pct,
            "total_findings": report.current.total_findings,
            "total_repair_cost": report.current.total_repair_cost,
            "total_repair_area_px": report.current.total_repair_area_px,
            "avg_crack_width_px": report.current.avg_crack_width_px,
            "moisture_level": report.current.moisture_level,
            "critical_count": report.current.critical_count,
            "high_count": report.current.high_count,
            "medium_count": report.current.medium_count,
            "low_count": report.current.low_count,
            "damage_types": report.current.damage_types,
            "summary": report.current.summary,
        },
        "findings": [
            {
                "damage_type": f.damage_type,
                "change_type": f.change_type,
                "previous_severity": f.previous_severity,
                "current_severity": f.current_severity,
                "previous_damage_pct": f.previous_damage_pct,
                "current_damage_pct": f.current_damage_pct,
                "previous_area_px": f.previous_area_px,
                "current_area_px": f.current_area_px,
                "delta_pct": f.delta_pct,
                "delta_area_px": f.delta_area_px,
                "severity_delta": f.severity_delta,
                "recommendation": f.recommendation,
            }
            for f in report.findings
        ],
        "health_score_delta": report.health_score_delta,
        "grade_changed": report.grade_changed,
        "previous_grade": report.previous_grade,
        "current_grade": report.current_grade,
        "damage_delta_pct": report.damage_delta_pct,
        "new_damage_count": report.new_damage_count,
        "resolved_damage_count": report.resolved_damage_count,
        "increased_count": report.increased_count,
        "reduced_count": report.reduced_count,
        "unchanged_count": report.unchanged_count,
        "improvement_score": report.improvement_score,
        "damage_growth_pct": report.damage_growth_pct,
        "repair_effectiveness_pct": report.repair_effectiveness_pct,
        "risk_trend": report.risk_trend,
        "comparison_summary": report.comparison_summary,
        "days_between": report.days_between,
    }


def rebuild_comparison_report(data: dict) -> Optional[ComparisonReport]:
    """Rebuild ComparisonReport from serialized dict."""
    if not data:
        return None

    def rebuild_snapshot(snap_data: dict) -> InspectionSnapshot:
        return InspectionSnapshot(
            inspection_id=snap_data.get("inspection_id", ""),
            inspection_date=snap_data.get("inspection_date", ""),
            health_score=snap_data.get("health_score", 0.0),
            grade=snap_data.get("grade", "D"),
            total_damage_pct=snap_data.get("total_damage_pct", 0.0),
            total_findings=snap_data.get("total_findings", 0),
            total_repair_cost=snap_data.get("total_repair_cost", 0),
            total_repair_area_px=snap_data.get("total_repair_area_px", 0),
            avg_crack_width_px=snap_data.get("avg_crack_width_px", 0.0),
            moisture_level=snap_data.get("moisture_level", "Low"),
            critical_count=snap_data.get("critical_count", 0),
            high_count=snap_data.get("high_count", 0),
            medium_count=snap_data.get("medium_count", 0),
            low_count=snap_data.get("low_count", 0),
            damage_types=snap_data.get("damage_types", []),
            summary=snap_data.get("summary", ""),
        )

    findings = [
        ComparisonFinding(
            damage_type=f.get("damage_type", ""),
            change_type=f.get("change_type", "unchanged"),
            previous_severity=f.get("previous_severity", "N/A"),
            current_severity=f.get("current_severity", "N/A"),
            previous_damage_pct=f.get("previous_damage_pct", 0.0),
            current_damage_pct=f.get("current_damage_pct", 0.0),
            previous_area_px=f.get("previous_area_px", 0),
            current_area_px=f.get("current_area_px", 0),
            delta_pct=f.get("delta_pct", 0.0),
            delta_area_px=f.get("delta_area_px", 0),
            severity_delta=f.get("severity_delta", "same"),
            recommendation=f.get("recommendation", ""),
        )
        for f in data.get("findings", [])
    ]

    return ComparisonReport(
        previous=rebuild_snapshot(data.get("previous", {})),
        current=rebuild_snapshot(data.get("current", {})),
        findings=findings,
        health_score_delta=data.get("health_score_delta", 0.0),
        grade_changed=data.get("grade_changed", False),
        previous_grade=data.get("previous_grade", "D"),
        current_grade=data.get("current_grade", "D"),
        damage_delta_pct=data.get("damage_delta_pct", 0.0),
        new_damage_count=data.get("new_damage_count", 0),
        resolved_damage_count=data.get("resolved_damage_count", 0),
        increased_count=data.get("increased_count", 0),
        reduced_count=data.get("reduced_count", 0),
        unchanged_count=data.get("unchanged_count", 0),
        improvement_score=data.get("improvement_score", 0.0),
        damage_growth_pct=data.get("damage_growth_pct", 0.0),
        repair_effectiveness_pct=data.get("repair_effectiveness_pct", 0.0),
        risk_trend=data.get("risk_trend", "Stable"),
        comparison_summary=data.get("comparison_summary", ""),
        days_between=data.get("days_between", 0),
    )
