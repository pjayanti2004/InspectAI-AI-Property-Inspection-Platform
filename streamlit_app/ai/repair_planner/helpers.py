"""Private helpers for the repair planning engine.

Public (cross-package): repair_plan_to_dict
Private (engine-only):  _clamp, _get_severity_rank, _get_repair_kb,
                        _scale_cost, _labour_cost, _equipment_cost,
                        _duration_to_days, _build_maintenance_schedule,
                        _build_checklists, _build_professional_timeline
"""
from __future__ import annotations

import re

from streamlit_app.ai.repair_planner.knowledge_base import (
    LABOUR_RATES,
    REPAIR_KB,
)
from streamlit_app.ai.repair_planner.models import (
    RepairMaterial,
    RepairPhase,
    RepairPlan,
    RepairTask,
)


# ── Utilities ──────────────────────────────────────────────────────────────────

def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *v* to the closed interval [lo, hi]."""
    return max(lo, min(hi, v))


def _get_severity_rank(severity: str) -> int:
    """Lower = more urgent."""
    return {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "N/A": 4, "": 5}.get(severity, 5)


def _get_repair_kb(damage_type: str) -> dict:
    """Return the knowledge-base entry for *damage_type*, falling back to general."""
    dt = damage_type.lower().strip()
    if dt in REPAIR_KB:
        return REPAIR_KB[dt]
    for key, kb in REPAIR_KB.items():
        if key.lower() in dt or dt in key.lower():
            return kb
    keyword_map = {
        "water": "Water Damage",
        "moisture": "Moisture Stain",
        "mold": "Mold", "mould": "Mold",
        "crack": "Crack",
        "structural": "Structural Damage",
        "foundation": "Foundation Issue",
        "roof": "Roof Damage",
        "electrical": "Electrical",
        "wiring": "Electrical",
        "plumbing": "Plumbing",
        "pipe": "Plumbing",
        "leak": "Water Damage",
        "paint": "Paint Peeling",
        "peel": "Paint Peeling",
        "stain": "Moisture Stain",
        "termite": "Termite Damage",
        "pest": "Termite Damage",
    }
    for kw, canonical in keyword_map.items():
        if kw in dt:
            return REPAIR_KB.get(canonical, REPAIR_KB["General Damage"])
    return REPAIR_KB["General Damage"]


def _scale_cost(base: int, damage_pct: float, severity: str) -> int:
    """Scale base cost by damage percentage and severity."""
    sev_multiplier = {"Critical": 2.0, "High": 1.5, "Medium": 1.2, "Low": 1.0}.get(severity, 1.0)
    dmg_factor = 1.0 + (damage_pct / 100.0) * 2.0
    return max(500, int(base * sev_multiplier * dmg_factor))


def _labour_cost(workers: int, hours: float, professional: str) -> int:
    """Calculate labour cost based on workers, hours, and professional type."""
    rate = LABOUR_RATES.get(professional, 500)
    return int(workers * hours * rate)


def _equipment_cost(tools: list[str]) -> int:
    """Estimate equipment rental cost from tool list."""
    rental_keywords = ["rental", "rent", "scaffolding", "crane", "excavator", "dehumidifier", "air scrubber", "shoring", "fumigation tent"]
    cost = 0
    for tool in tools:
        tool_lower = tool.lower()
        if "rental" in tool_lower or "rent" in tool_lower:
            cost += 2000
        elif "scaffolding" in tool_lower:
            cost += 3000
        elif "crane" in tool_lower:
            cost += 10000
        elif "excavator" in tool_lower:
            cost += 8000
        elif "dehumidifier" in tool_lower:
            cost += 2000
        elif "air scrubber" in tool_lower or "air" in tool_lower:
            cost += 2000
        elif "shoring" in tool_lower:
            cost += 5000
        elif "fumigation" in tool_lower:
            cost += 5000
        elif "mixer" in tool_lower or "pump" in tool_lower:
            cost += 3000
    return cost


def _duration_to_days(duration_str: str) -> int:
    """Parse duration string like '2-3 days' → 3."""
    numbers = re.findall(r'\d+', duration_str)
    if numbers:
        return max(int(n) for n in numbers)
    return 1


def _build_maintenance_schedule(severity: str, damage_type: str) -> dict[str, list[str]]:
    """Generate maintenance schedule for different timeframes."""
    schedule = {
        "1_month": [
            "Inspect repaired area daily for first week",
            "Check for new cracks or moisture signs",
            "Ensure repair materials have cured properly",
            "Verify drainage is functioning correctly",
            "Take photos for before/after documentation",
        ],
        "3_months": [
            "Full inspection of repaired area",
            "Check surrounding areas for new damage",
            "Verify waterproofing is still effective",
            "Inspect drainage systems",
            "Clean gutters and downspouts",
        ],
        "6_months": [
            "Complete property inspection",
            "Check paint condition on all walls",
            "Inspect all plumbing fixtures for leaks",
            "Test electrical outlets and switches",
            "Check exterior walls for new damage",
        ],
        "12_months": [
            "Full professional inspection recommended",
            "Deep clean gutters and drainage",
            "Re-apply waterproofing to exterior walls if needed",
            "Update maintenance log",
            "Review insurance coverage",
            "Budget for next year's maintenance",
        ],
    }

    if severity in ("Critical", "High"):
        schedule["3_months"].append(f"Re-inspect {damage_type.lower()} area with a professional")

    if "water" in damage_type.lower() or "moisture" in damage_type.lower() or "leak" in damage_type.lower():
        schedule["3_months"].append("Check moisture levels with moisture meter")

    if "crack" in damage_type.lower():
        schedule["3_months"].append("Measure crack width — growing cracks need urgent attention")

    if "foundation" in damage_type.lower() or "structural" in damage_type.lower():
        schedule["3_months"].append("Structural monitoring — check for new settlement cracks")
        schedule["6_months"].append("Structural assessment by engineer")
        schedule["12_months"].append("Foundation levelling check")

    if "roof" in damage_type.lower():
        schedule["6_months"].append("Roof inspection before monsoon season")

    if "paint" in damage_type.lower() or "peel" in damage_type.lower():
        schedule["6_months"].append("Touch up paint if fading/chipping observed")

    return schedule


def _build_checklists() -> tuple[list[str], list[str], list[str]]:
    """Generate before/during/after repair checklists."""
    before = [
        "Clear the work area of furniture and valuables",
        "Protect floors with drop cloths/plastic sheeting",
        "Ensure proper ventilation (open windows, use fans)",
        "Turn off water/electricity to affected area if needed",
        "Notify neighbours of upcoming work (noise/dust)",
        "Arrange alternative accommodation if area is uninhabitable",
        "Take detailed photos of damage before starting",
        "Gather all required permits if applicable",
        "Confirm professional booking and material delivery dates",
        "Set up temporary barriers for safety zones",
    ]

    during = [
        "Monitor workers for proper PPE usage",
        "Check progress against repair timeline daily",
        "Take photos at each major milestone",
        "Ensure all safety protocols are followed",
        "Verify material quality and quantities",
        "Address any unexpected damage discovered during repair",
        "Maintain communication with site supervisor",
        "Keep the work area clean and organised daily",
        "Document any changes to the original plan",
        "Test interim results (e.g., water tests for plumbing repairs)",
    ]

    after = [
        "Conduct thorough visual inspection of all repairs",
        "Run functional tests (water flow, electrical circuits, etc.)",
        "Clean the work area completely",
        "Dispose of all construction waste properly",
        "Compare before/after photos to verify completeness",
        "Obtain completion certificate from professional",
        "Register warranty documents for materials and workmanship",
        "Update property maintenance log",
        "Schedule follow-up inspection (1 month post-repair)",
        "Review total costs against estimates",
    ]

    return before, during, after


def _build_professional_timeline(phases: list[RepairPhase]) -> str:
    """Generate a human-readable professional repair timeline."""
    lines = []
    for phase in phases:
        task_count = len(phase.tasks)
        tasks_str = ", ".join(t.title for t in phase.tasks[:3])
        if len(phase.tasks) > 3:
            tasks_str += f" + {len(phase.tasks) - 3} more"
        lines.append(
            f"{phase.icon} **{phase.phase}** ({phase.duration_days} days): {tasks_str}"
        )
    return "\n".join(lines)


# ── Core builder functions ─────────────────────────────────────────────────────

def _build_tasks(findings: list[dict]) -> list[RepairTask]:
    """Build a RepairTask for each finding."""
    tasks: list[RepairTask] = []

    for i, f in enumerate(findings, 1):
        damage_type = f.get("damage_type", "General Damage")
        severity    = f.get("severity", "Medium")
        damage_pct  = f.get("damage_pct", 0.0)

        kb = _get_repair_kb(damage_type)

        # Scale costs based on damage extent
        mat_cost   = _scale_cost(kb["material_cost"], damage_pct, severity)
        lab_cost   = _labour_cost(kb["workers"], kb["labour_hours"], kb["professional"])
        equip_cost = _equipment_cost(kb.get("equipment_tools", []))

        # Build materials list
        materials = []
        for name, qty, unit, base_cost in kb["materials"]:
            scaled_cost = max(50, int(base_cost * (damage_pct / 5.0 + 0.5)))
            materials.append(RepairMaterial(
                name=name, quantity=qty, unit=unit, estimated_cost=scaled_cost,
            ))

        # Adjust priority based on severity
        priority = severity if severity in ("Critical", "High", "Medium", "Low") else kb["priority"]

        task = RepairTask(
            finding_id=f"T{i:03d}",
            damage_type=damage_type,
            title=kb["title"],
            priority=priority,
            workers_required=kb["workers"],
            labour_hours=kb["labour_hours"],
            repair_duration=kb["duration"],
            materials=materials,
            repair_sequence=kb["sequence"],
            safety_gear=kb["safety"],
            tools_required=kb["tools"],
            professional=kb["professional"],
            diy_possible=kb["diy"],
            warranty_months=kb["warranty"],
            inspection_after=kb["inspection"],
        )
        tasks.append(task)

    # Sort by severity
    tasks.sort(key=lambda t: _get_severity_rank(t.priority))
    return tasks


def _build_phases(tasks: list[RepairTask]) -> list[RepairPhase]:
    """Organize tasks into repair phases."""
    phases: list[RepairPhase] = []

    # Immediate phase: Critical priority tasks
    immediate_tasks = [t for t in tasks if t.priority == "Critical"]
    if immediate_tasks:
        phases.append(RepairPhase(
            phase="Immediate",
            tasks=immediate_tasks,
            duration_days=max(_duration_to_days(t.repair_duration) for t in immediate_tasks),
            icon="🚨",
            color="#EF4444",
        ))

    # Preparation phase
    prep_tasks = [
        RepairTask(
            finding_id="PREP", damage_type="Preparation", title="Site Preparation & Safety Setup",
            priority="High", workers_required=2, labour_hours=4.0, repair_duration="1 day",
            materials=[RepairMaterial(name="Safety barriers", quantity="1", unit="set", estimated_cost=500),
                        RepairMaterial(name="Drop cloths", quantity="5", unit="pieces", estimated_cost=300),
                        RepairMaterial(name="Ventilation fans", quantity="2", unit="units", estimated_cost=1000)],
            repair_sequence=[
                "Set up safety barriers and warning signs",
                "Cover floors and furniture with protective sheeting",
                "Set up ventilation (fans/open windows)",
                "Turn off utilities to affected area",
                "Set up temporary lighting if needed",
                "Arrange waste disposal containers",
            ],
            safety_gear=["Hard hat", "Safety vest", "Gloves"],
            tools_required=["Ladder", "Utility knife", "Measuring tape"],
            professional="General Contractor",
            diy_possible=True, warranty_months=0, inspection_after=False,
        )
    ]
    phases.append(RepairPhase(
        phase="Preparation",
        tasks=prep_tasks,
        duration_days=1,
        icon="🛠️",
        color="#F59E0B",
    ))

    # Repair phase: all remaining tasks
    repair_tasks = [t for t in tasks if t.priority != "Critical"]
    if repair_tasks:
        total_days = sum(_duration_to_days(t.repair_duration) for t in repair_tasks)
        phases.append(RepairPhase(
            phase="Repair",
            tasks=repair_tasks,
            duration_days=max(total_days, 1),
            icon="🔧",
            color="#F97316",
        ))

    # Finishing phase
    finishing_tasks = [
        RepairTask(
            finding_id="FINISH", damage_type="Finishing", title="Finishing & Cleanup",
            priority="Medium", workers_required=1, labour_hours=4.0, repair_duration="1 day",
            materials=[RepairMaterial(name="Cleaning supplies", quantity="1", unit="set", estimated_cost=500)],
            repair_sequence=[
                "Remove all protective coverings",
                "Clean all work areas thoroughly",
                "Touch up paint/finish for uniform appearance",
                "Polish and restore fixtures",
                "Dispose of all construction waste",
                "Restore utilities",
            ],
            safety_gear=["Gloves", "Dust mask"],
            tools_required=["Broom", "Mop", "Cleaning supplies"],
            professional="General Contractor",
            diy_possible=True, warranty_months=0, inspection_after=False,
        )
    ]
    phases.append(RepairPhase(
        phase="Finishing",
        tasks=finishing_tasks,
        duration_days=1,
        icon="✨",
        color="#3B82F6",
    ))

    # Inspection phase
    if any(t.inspection_after for t in tasks):
        inspect_task = RepairTask(
            finding_id="INSPECT", damage_type="Inspection", title="Post-Repair Inspection",
            priority="High", workers_required=1, labour_hours=2.0, repair_duration="1 day",
            materials=[],
            repair_sequence=[
                "Visual inspection of all repaired areas",
                "Functional testing (water, electricity, etc.)",
                "Document completion with photos",
                "Obtain sign-off from professional",
                "Register warranties",
            ],
            safety_gear=["Safety vest", "Hard hat"],
            tools_required=["Moisture meter", "Crack gauge", "Level", "Camera"],
            professional="Structural Engineer / Certified Inspector",
            diy_possible=False, warranty_months=0, inspection_after=True,
        )
        phases.append(RepairPhase(
            phase="Inspection",
            tasks=[inspect_task],
            duration_days=1,
            icon="✅",
            color="#10B981",
        ))

    return phases


def _estimate_costs(
    tasks: list[RepairTask],
    phases: list[RepairPhase],
) -> tuple[int, int, int, int]:
    """Calculate total material, labour, equipment, and total costs."""
    total_material = 0
    total_labour   = 0
    total_equipment = 0

    for task in tasks:
        for mat in task.materials:
            total_material += mat.estimated_cost
        rate = LABOUR_RATES.get(task.professional, 500)
        total_labour += int(task.workers_required * task.labour_hours * rate)
        total_equipment += _equipment_cost(task.tools_required)

    # Add phase-specific costs (avoid double-counting by skipping tasks already processed)
    seen = {t.finding_id for t in tasks}
    for phase in phases:
        for task in phase.tasks:
            if task.finding_id in seen:
                continue
            for mat in task.materials:
                total_material += mat.estimated_cost

    total = total_material + total_labour + total_equipment
    return total_material, total_labour, total_equipment, total


# ── Public compatibility helper ────────────────────────────────────────────────

def repair_plan_to_dict(plan: RepairPlan) -> dict:
    """Convert RepairPlan to a plain dict for session state storage."""

    def task_to_dict(t: RepairTask) -> dict:
        return {
            "finding_id": t.finding_id,
            "damage_type": t.damage_type,
            "title": t.title,
            "priority": t.priority,
            "workers_required": t.workers_required,
            "labour_hours": t.labour_hours,
            "repair_duration": t.repair_duration,
            "materials": [
                {"name": m.name, "quantity": m.quantity, "unit": m.unit, "estimated_cost": m.estimated_cost}
                for m in t.materials
            ],
            "repair_sequence": t.repair_sequence,
            "safety_gear": t.safety_gear,
            "tools_required": t.tools_required,
            "professional": t.professional,
            "diy_possible": t.diy_possible,
            "warranty_months": t.warranty_months,
            "inspection_after": t.inspection_after,
        }

    def phase_to_dict(p: RepairPhase) -> dict:
        return {
            "phase": p.phase,
            "tasks": [task_to_dict(t) for t in p.tasks],
            "duration_days": p.duration_days,
            "icon": p.icon,
            "color": p.color,
        }

    return {
        "tasks": [task_to_dict(t) for t in plan.tasks],
        "phases": [phase_to_dict(p) for p in plan.phases],
        "total_material_cost": plan.total_material_cost,
        "total_labour_cost": plan.total_labour_cost,
        "total_equipment_cost": plan.total_equipment_cost,
        "total_repair_cost": plan.total_repair_cost,
        "professional_timeline": plan.professional_timeline,
        "before_checklist": plan.before_checklist,
        "during_checklist": plan.during_checklist,
        "after_checklist": plan.after_checklist,
        "maintenance_schedule": plan.maintenance_schedule,
    }


__all__ = [
    # Public
    "repair_plan_to_dict",
    # Private helpers (exported for engine.py; prefix _ in engine import for clarity)
    "_clamp",
    "_get_severity_rank",
    "_get_repair_kb",
    "_scale_cost",
    "_labour_cost",
    "_equipment_cost",
    "_duration_to_days",
    "_build_maintenance_schedule",
    "_build_checklists",
    "_build_professional_timeline",
    "_build_timeline",
    "_build_tasks",
    "_build_phases",
    "_estimate_costs",
]

# Backward-compatible alias expected by engine.py
_build_timeline = _build_professional_timeline
