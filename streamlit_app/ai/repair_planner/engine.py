"""Repair planning engine — public entry point for InspectAI.

Public API: generate_repair_plan(reports, fused=None) → RepairPlan
Compatibility: repair_plan_to_dict(plan) → dict
"""
from __future__ import annotations

from typing import Optional

from streamlit_app.ai.repair_planner.helpers import (
    _build_checklists,
    _build_phases,
    _build_tasks,
    _build_timeline,
    _estimate_costs,
    _get_severity_rank,
)
from streamlit_app.ai.repair_planner.models import RepairPlan
from streamlit_app.ai.repair_planner.helpers import repair_plan_to_dict


def generate_repair_plan(reports: list, fused: Optional[object] = None) -> RepairPlan:
    """Generate a complete repair plan from inspection findings.

    Args:
        reports:  List of InspectionReport objects or serialised dicts.
        fused:    Optional FusedInspection for aggregated data (unused, kept for API compat).

    Returns:
        RepairPlan dataclass with tasks, phases, costs, checklists, and schedule.
    """
    # ── Step 1: Collect findings ──────────────────────────────────────────
    findings: list[dict] = []

    for r in reports:
        if hasattr(r, "to_dict"):
            d = r.to_dict()
        elif isinstance(r, dict):
            d = r
        else:
            continue

        if d.get("damage_type", "N/A") == "N/A":
            continue
        if d.get("damage_percentage", 0.0) < 0.1:
            continue

        findings.append({
            "damage_type": d.get("damage_type", "General Damage"),
            "severity": d.get("severity", "Medium"),
            "confidence": d.get("confidence", 0),
            "damage_pct": d.get("damage_percentage", 0.0),
            "urgency": d.get("urgency", "Schedule within 30 days"),
            "repair_steps": d.get("repair_steps", []),
            "file_name": d.get("file_name", "Unknown"),
        })

    if not findings:
        findings.append({
            "damage_type": "General Maintenance",
            "severity": "Low",
            "confidence": 100,
            "damage_pct": 0.0,
            "urgency": "No urgency",
            "repair_steps": ["Routine inspection"],
            "file_name": "N/A",
        })

    # ── Step 2-5: Build tasks, phases, estimate costs, timeline ───────────
    tasks        = _build_tasks(findings)
    phases       = _build_phases(tasks)
    mat_cost, lab_cost, equip_cost, total_cost = _estimate_costs(tasks, phases)
    timeline     = _build_timeline(phases)
    before_cl, during_cl, after_cl = _build_checklists()

    # ── Step 6: Build maintenance schedule ─────────────────────────────────
    from streamlit_app.ai.repair_planner.helpers import _build_maintenance_schedule
    worst = max(findings, key=lambda f: _get_severity_rank(f.get("severity", "Low")))
    maintenance = _build_maintenance_schedule(
        worst.get("severity", "Low"),
        worst.get("damage_type", "General Damage"),
    )

    return RepairPlan(
        tasks=tasks,
        phases=phases,
        total_material_cost=mat_cost,
        total_labour_cost=lab_cost,
        total_equipment_cost=equip_cost,
        total_repair_cost=total_cost,
        professional_timeline=timeline,
        before_checklist=before_cl,
        during_checklist=during_cl,
        after_checklist=after_cl,
        maintenance_schedule=maintenance,
    )


__all__ = ["generate_repair_plan", "repair_plan_to_dict"]
