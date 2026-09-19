"""InspectAI database package.

Provides:
  - schema:      DDL statements for all tables.
  - database:    Connection management (init, reset, version tracking).
  - repository:  CRUD functions for properties, inspections, images, reports.
"""
from __future__ import annotations

from streamlit_app.database.database import (
    get_connection,
    init_db,
    reset_db,
    get_db_version,
    ConnectionManager,
    DB_PATH,
)

from streamlit_app.database.repository import (
    # Properties
    create_property,
    update_property,
    get_property,
    list_properties,
    delete_property,
    # Inspections
    create_inspection,
    update_inspection_status,
    get_inspection,
    get_inspections_by_property,
    delete_inspection,
    # Images
    save_inspection_image,
    get_images_by_inspection,
    # Reports
    save_report,
    get_report,
    list_reports,
    delete_report,
    # Dashboard
    get_dashboard_stats,
    # History
    get_inspection_history,
    get_history_stats,
)

__version__ = "1.0.0"

__all__ = [
    # Database management
    "get_connection",
    "init_db",
    "reset_db",
    "get_db_version",
    "ConnectionManager",
    "DB_PATH",
    # Repository functions
    "create_property",
    "update_property",
    "get_property",
    "list_properties",
    "delete_property",
    "create_inspection",
    "update_inspection_status",
    "get_inspection",
    "get_inspections_by_property",
    "delete_inspection",
    "save_inspection_image",
    "get_images_by_inspection",
    "save_report",
    "get_report",
    "list_reports",
    "delete_report",
    "get_dashboard_stats",
    "get_inspection_history",
    "get_history_stats",
]
