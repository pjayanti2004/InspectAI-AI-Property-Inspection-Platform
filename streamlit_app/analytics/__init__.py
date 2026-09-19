"""InspectAI Analytics — query and aggregate database stats."""
from streamlit_app.analytics.stats_engine import (
    get_kpi_cards,
    get_monthly_trend,
    get_risk_distribution,
    get_grade_distribution,
    get_damage_type_distribution,
    get_property_type_distribution,
    get_repair_cost_distribution,
    get_recent_activity,
    get_top_risk_properties,
    get_insights,
)

__all__ = [
    "get_kpi_cards",
    "get_monthly_trend",
    "get_risk_distribution",
    "get_grade_distribution",
    "get_damage_type_distribution",
    "get_property_type_distribution",
    "get_repair_cost_distribution",
    "get_recent_activity",
    "get_top_risk_properties",
    "get_insights",
]