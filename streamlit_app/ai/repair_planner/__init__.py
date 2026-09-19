"""Repair planning package for InspectAI.

Re-exports for backward compatibility:
  - generate_repair_plan (from engine)
  - repair_plan_to_dict  (from helpers)
  - RepairPlan            (from models)
"""
from __future__ import annotations

from streamlit_app.ai.repair_planner.engine import generate_repair_plan
from streamlit_app.ai.repair_planner.helpers import repair_plan_to_dict
from streamlit_app.ai.repair_planner.models import RepairPlan

__all__ = [
    "generate_repair_plan",
    "repair_plan_to_dict",
    "RepairPlan",
]
