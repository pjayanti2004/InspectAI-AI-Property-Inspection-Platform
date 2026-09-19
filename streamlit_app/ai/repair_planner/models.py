"""Repair planning data models for InspectAI.

Public types: RepairMaterial, RepairTask, RepairPhase, RepairPlan
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RepairMaterial:
    """A single material needed for a repair task."""
    name: str = ""
    quantity: str = ""
    unit: str = ""
    estimated_cost: int = 0


@dataclass(frozen=True)
class RepairTask:
    """A single repair task for one finding."""
    finding_id: str = ""
    damage_type: str = ""
    title: str = ""
    priority: str = "Medium"
    workers_required: int = 1
    labour_hours: float = 0.0
    repair_duration: str = "1 day"
    materials: list[RepairMaterial] = field(default_factory=list)
    repair_sequence: list[str] = field(default_factory=list)
    safety_gear: list[str] = field(default_factory=list)
    tools_required: list[str] = field(default_factory=list)
    professional: str = "General Contractor"
    diy_possible: bool = False
    warranty_months: int = 6
    inspection_after: bool = True


@dataclass(frozen=True)
class RepairPhase:
    """A phase of the overall repair plan."""
    phase: str = ""
    tasks: list[RepairTask] = field(default_factory=list)
    duration_days: int = 0
    icon: str = "🔧"
    color: str = "#64748B"


@dataclass(frozen=True)
class RepairPlan:
    """Complete repair plan for a property inspection."""
    tasks: list[RepairTask] = field(default_factory=list)
    phases: list[RepairPhase] = field(default_factory=list)
    total_material_cost: int = 0
    total_labour_cost: int = 0
    total_equipment_cost: int = 0
    total_repair_cost: int = 0
    professional_timeline: str = ""
    before_checklist: list[str] = field(default_factory=list)
    during_checklist: list[str] = field(default_factory=list)
    after_checklist: list[str] = field(default_factory=list)
    maintenance_schedule: dict[str, list[str]] = field(default_factory=dict)


__all__ = [
    "RepairMaterial",
    "RepairTask",
    "RepairPhase",
    "RepairPlan",
]
