"""Data-access layer for InspectAI.

All persistence operations go through this module.  No ORM — raw SQL
with the sqlite3 stdlib.  Functions accept and return plain Python
objects (dicts, dataclasses, etc.) so callers stay decoupled from
the database schema.

Serialisation:
  Complex objects (dataclasses, enums, lists) are converted to/from
  JSON using ``dataclasses.asdict()`` and custom encoders/decoders.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from streamlit_app.database.database import get_connection, init_db
from streamlit_app.utils.exceptions import DatabaseError, ValidationError
from streamlit_app.utils.logger import get_logger

# ── Logging ──────────────────────────────────────────────────────────────────

_logger = get_logger(__name__)

class _InspectAIEncoder(json.JSONEncoder):
    """Custom JSON encoder for InspectAI data types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)


def _to_json(obj: Any) -> str:
    """Serialize any Python object to a JSON string."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, cls=_InspectAIEncoder, ensure_ascii=False)


def _from_json(text: str, default: Any = None) -> Any:
    """Deserialize a JSON string back to Python objects."""
    if not text or not text.strip():
        return default if default is not None else {}
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


# ── ID generation ─────────────────────────────────────────────────────────────

def _new_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix (e.g. 'PROP-', 'INSP-')."""
    raw = uuid.uuid4().hex[:12].upper()
    return f"{prefix}{raw}" if prefix else raw


# ── Properties ────────────────────────────────────────────────────────────────

def create_property(
    property_type: str,
    address: str = "",
    city: str = "",
    state: str = "",
    pincode: str = "",
    year_built: int | None = None,
    area_sqft: int | None = None,
    floors: int | None = None,
    construction_type: str = "",
    inspector_name: str = "",
    notes: str = "",
) -> str:
    """Insert a new property and return its ID."""
    init_db()
    prop_id = _new_id("PROP-")
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO properties (
                property_id, property_type, address, city, state, pincode,
                year_built, area_sqft, floors, construction_type,
                inspector_name, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                prop_id, property_type, address, city, state, pincode,
                year_built, area_sqft, floors, construction_type,
                inspector_name, notes,
            ),
        )
        conn.commit()
        _logger.info("Created property %s (%s, %s).", prop_id, property_type, address)
    except sqlite3.Error as exc:
        conn.rollback()
        _logger.exception("Failed to create property.")
        raise DatabaseError(
            "Could not create property in database.",
            details={"error": str(exc)},
        ) from exc
    finally:
        conn.close()
    return prop_id


def update_property(property_id: str, **kwargs: Any) -> None:
    """Update fields of an existing property.

    Only the keyword arguments passed will be updated.
    Raises ValueError if the property does not exist.
    """
    init_db()
    if not kwargs:
        return

    allowed = {
        "property_type", "address", "city", "state", "pincode",
        "year_built", "area_sqft", "floors", "construction_type",
        "inspector_name", "notes",
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [datetime.now().isoformat(), property_id]

    conn = get_connection()
    try:
        cursor = conn.execute(
            f"UPDATE properties SET {set_clause}, updated_at = ? WHERE property_id = ?",
            values,
        )
        conn.commit()
        if cursor.rowcount == 0:
            _logger.warning("update_property: property %s not found.", property_id)
        else:
            _logger.debug("Updated property %s: %s.", property_id, list(updates.keys()))
    except sqlite3.Error as exc:
        conn.rollback()
        _logger.exception("Failed to update property %s.", property_id)
        raise DatabaseError(
            f"Could not update property '{property_id}'.",
            details={"property_id": property_id, "error": str(exc)},
        ) from exc
    finally:
        conn.close()


def get_property(property_id: str) -> dict[str, Any] | None:
    """Fetch a single property by ID.  Returns None if not found."""
    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM properties WHERE property_id = ?", (property_id,)
        ).fetchone()
        if row:
            _logger.debug("Fetched property %s.", property_id)
        else:
            _logger.debug("Property %s not found.", property_id)
        return dict(row) if row else None
    finally:
        conn.close()


def list_properties(
    property_type: str = "",
    city: str = "",
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List properties with optional filters.

    Returns:
        List of property dicts, ordered by most recently updated first.
    """
    init_db()
    conn = get_connection()
    try:
        query = "SELECT * FROM properties WHERE 1=1"
        params: list[Any] = []

        if property_type:
            query += " AND property_type = ?"
            params.append(property_type)
        if city:
            query += " AND city LIKE ?"
            params.append(f"%{city}%")

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        _logger.debug("list_properties returned %d rows (city=%r, type=%r).", len(rows), city, property_type)
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        _logger.exception("Failed to list properties.")
        raise DatabaseError(
            "Could not retrieve properties from database.",
            details={"error": str(exc)},
        ) from exc
    finally:
        conn.close()


def delete_property(property_id: str) -> bool:
    """Delete a property and all related data (cascades).  Returns True if deleted."""
    init_db()
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM properties WHERE property_id = ?", (property_id,)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            _logger.info("Deleted property %s.", property_id)
        return deleted
    except sqlite3.Error as exc:
        conn.rollback()
        _logger.exception("Failed to delete property %s.", property_id)
        raise DatabaseError(
            f"Could not delete property '{property_id}'.",
            details={"property_id": property_id, "error": str(exc)},
        ) from exc
    finally:
        conn.close()


# ── Inspections ───────────────────────────────────────────────────────────────

def create_inspection(
    property_id: str,
    inspection_date: str = "",
    inspector_name: str = "",
    weather_condition: str = "",
    notes: str = "",
) -> str:
    """Create a new inspection record linked to a property.

    Returns:
        The generated inspection_id.
    """
    init_db()
    insp_id = _new_id("INSP-")
    today = date.today().isoformat() if not inspection_date else inspection_date

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO inspections (
                inspection_id, property_id, inspection_date,
                inspector_name, weather_condition, notes
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (insp_id, property_id, today, inspector_name, weather_condition, notes),
        )
        conn.commit()
        _logger.info("Created inspection %s for property %s.", insp_id, property_id)
    except sqlite3.Error as exc:
        conn.rollback()
        _logger.exception("Failed to create inspection.")
        raise DatabaseError(
            "Could not create inspection in database.",
            details={"property_id": property_id, "error": str(exc)},
        ) from exc
    finally:
        conn.close()
    return insp_id


def update_inspection_status(
    inspection_id: str,
    status: str,
    total_images: int = 0,
    processing_time_sec: float = 0.0,
) -> None:
    """Update inspection processing status after AI analysis completes."""
    init_db()
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE inspections
               SET status = ?, total_images = ?, processing_time_sec = ?
               WHERE inspection_id = ?""",
            (status, total_images, processing_time_sec, inspection_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_inspection(inspection_id: str) -> dict[str, Any] | None:
    """Fetch a single inspection by ID."""
    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM inspections WHERE inspection_id = ?", (inspection_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_inspections_by_property(property_id: str) -> list[dict[str, Any]]:
    """List all inspections for a given property, newest first."""
    init_db()
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM inspections
               WHERE property_id = ?
               ORDER BY inspection_date DESC""",
            (property_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_inspection(inspection_id: str) -> bool:
    """Delete an inspection and all related images + reports (cascades)."""
    init_db()
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM inspections WHERE inspection_id = ?", (inspection_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── Inspection Images ─────────────────────────────────────────────────────────

def save_inspection_image(
    inspection_id: str,
    file_name: str,
    file_path: str = "",
    file_size_kb: float = 0.0,
    width_px: int = 0,
    height_px: int = 0,
    damage_pct: float = 0.0,
    severity: str = "",
    confidence: float = 0.0,
    damage_types: list[str] | None = None,
    rank_order: int = 0,
) -> str:
    """Save metadata for a single inspection image.

    Args:
        inspection_id:  Parent inspection.
        file_name:      Original file name.
        file_path:      Full path on disk (if stored locally).
        file_size_kb:   File size in KB.
        width_px:       Image width in pixels.
        height_px:      Image height in pixels.
        damage_pct:     AI-detected damage percentage.
        severity:       Worst severity in this image.
        confidence:     AI confidence score (0-100).
        damage_types:   List of damage type strings detected.
        rank_order:     1-based rank (1 = most damaged).

    Returns:
        The generated image_id.
    """
    init_db()
    image_id = _new_id("IMG-")
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO inspection_images (
                image_id, inspection_id, file_name, file_path,
                file_size_kb, width_px, height_px, damage_pct,
                severity, confidence, damage_types, rank_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                image_id, inspection_id, file_name, file_path,
                file_size_kb, width_px, height_px, damage_pct,
                severity, confidence,
                _to_json(damage_types or []),
                rank_order,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return image_id


def get_images_by_inspection(inspection_id: str) -> list[dict[str, Any]]:
    """Get all images for an inspection, ordered by rank."""
    init_db()
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM inspection_images
               WHERE inspection_id = ?
               ORDER BY rank_order ASC""",
            (inspection_id,),
        ).fetchall()
        result = []
        for row in rows:
            r = dict(row)
            r["damage_types"] = _from_json(r.get("damage_types", "[]"), default=[])
            result.append(r)
        return result
    finally:
        conn.close()


# ── Reports ───────────────────────────────────────────────────────────────────

def save_report(
    inspection_id: str,
    fused: Any,  # FusedInspection — imported lazily to avoid circular deps
) -> str:
    """Persist a full FusedInspection result as a report.

    Complex nested objects (findings, health_report, comparison_report, etc.)
    are serialized to JSON columns.

    Args:
        inspection_id: The inspection this report belongs to.
        fused:         A FusedInspection dataclass instance.

    Returns:
        The generated report_id.
    """
    from streamlit_app.ai.fusion_engine import FusedInspection

    init_db()

    # Serialize the FusedInspection
    findings_json = _to_json([
        {
            "damage_type": f.damage_type,
            "severity": f.severity,
            "confidence": f.confidence,
            "damage_pct": f.damage_pct,
            "affected_images": f.affected_images,
            "image_count": f.image_count,
            "possible_causes": f.possible_causes,
            "repair_steps": f.repair_steps,
            "recommended_professional": f.recommended_professional,
            "estimated_cost_range": f.estimated_cost_range,
            "urgency": f.urgency,
            "prevention_tips": f.prevention_tips,
        }
        for f in fused.findings
    ])

    image_rankings_json = _to_json([
        {
            "rank": r.rank,
            "file_name": r.file_name,
            "damage_pct": r.damage_pct,
            "severity": r.severity,
            "damage_type": r.damage_type,
            "confidence": r.confidence,
        }
        for r in fused.image_rankings
    ])

    # Timeline entries — serialize each entry
    timeline_json = _to_json([
        asdict(t) if is_dataclass(t) else _serialize_timeline_entry(t)
        for t in fused.timeline
    ])

    # Health Report
    health_json = _to_json(
        _serialize_health_report(fused.health_report)
        if fused.health_report else {}
    )

    # Comparison Report
    comparison_json = _to_json(
        _serialize_comparison_report(fused.comparison_report)
        if fused.comparison_report else {}
    )

    # Raw reports (source InspectionReport objects)
    raw_reports_json = _to_json([
        _serialize_inspection_report(r) for r in fused.source_reports
    ])

    report_id = _new_id("RPT-")
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO reports (
                report_id, inspection_id,
                overall_damage_pct, overall_confidence, overall_severity,
                overall_health_score, overall_estimated_cost_min,
                overall_estimated_cost_max, total_repair_area_px,
                avg_crack_width_px,
                findings_json, image_rankings_json,
                executive_summary, property_summary, inspection_conclusion,
                timeline_json, maintenance_tips_json,
                health_report_json, comparison_report_json,
                raw_reports_json, processing_time_sec
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                report_id,
                inspection_id,
                fused.overall_damage_pct,
                fused.overall_confidence,
                fused.overall_severity,
                fused.overall_health_score,
                fused.overall_estimated_cost_min,
                fused.overall_estimated_cost_max,
                fused.total_repair_area_px,
                fused.avg_crack_width_px,
                findings_json,
                image_rankings_json,
                fused.executive_summary,
                fused.property_summary,
                fused.inspection_conclusion,
                timeline_json,
                _to_json(fused.maintenance_tips),
                health_json,
                comparison_json,
                raw_reports_json,
                fused.processing_time_sec,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return report_id


# ── Full Inspection Persistence ────────────────────────────────────────────────


def persist_full_inspection(
    inspection_data: dict,
    property_data: dict,
    image_rankings: list[dict] | None = None,
) -> str:
    """Persist a complete inspection (property + inspection + images + report).

    This is the single call used by the Results page "Save Inspection" button.
    It wraps the lower-level CRUD functions so callers don't have to orchestrate
    the transaction themselves.

    Args:
        inspection_data: Dict from session state with keys:
            - id (inspection_id)
            - status ("Completed" / "processing")
            - image_count
            - image_names
            - fused_inspection (serialised dict, optional)
            - results (list of serialised reports, optional)
        property_data: Dict from the Step 1 form with keys:
            - property_name, property_type, address, city, state,
              pincode, year_built, area_sqft, floors, construction_type,
              inspector_name, notes
        image_rankings: Optional list of dicts with file_name, damage_pct,
            severity, damage_type, confidence for each uploaded image.

    Returns:
        The inspection_id that was persisted.
    """
    init_db()
    insp_id = inspection_data.get("id") or _new_id("INSP-")
    status = inspection_data.get("status", "completed")
    image_count = inspection_data.get("image_count", 0)
    image_names = inspection_data.get("image_names", [])

    # Map property form fields to DB columns
    prop_type = (property_data.get("property_type") or "other").lower()
    valid_types = {"residential", "commercial", "industrial",
                   "institutional", "mixed_use", "other"}
    if prop_type not in valid_types:
        prop_type = "other"

    inspector_name = property_data.get("inspector_name", "") or ""
    address = property_data.get("address", "") or property_data.get("property_name", "") or ""

    city = property_data.get("city", "") or ""
    state_ = property_data.get("state", "") or ""

    conn = get_connection()
    try:
        conn.execute("BEGIN")

        # 1) Property
        prop_id = _new_id("PROP-")
        conn.execute(
            """INSERT INTO properties (
                property_id, property_type, address, city, state, pincode,
                year_built, area_sqft, floors, construction_type,
                inspector_name, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                prop_id,
                prop_type,
                address,
                city,
                state_,
                property_data.get("pincode", "") or "",
                property_data.get("year_built"),
                property_data.get("area_sqft"),
                property_data.get("floors"),
                property_data.get("construction_type", "") or "",
                inspector_name,
                property_data.get("notes", "") or "",
            ),
        )

        # 2) Inspection
        today = date.today().isoformat()
        conn.execute(
            """INSERT INTO inspections (
                inspection_id, property_id, inspection_date,
                inspector_name, weather_condition, notes,
                status, total_images
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                insp_id,
                prop_id,
                today,
                inspector_name,
                "",
                "",
                status.lower() if status else "completed",
                image_count,
            ),
        )

        # 3) Images (metadata only)
        for idx, fname in enumerate(image_names or []):
            img_id = _new_id("IMG-")
            ranking = None
            if image_rankings:
                ranking = next(
                    (r for r in image_rankings if r.get("file_name") == fname),
                    None,
                )
            conn.execute(
                """INSERT INTO inspection_images (
                    image_id, inspection_id, file_name,
                    damage_pct, severity, confidence, rank_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    img_id,
                    insp_id,
                    fname,
                    ranking.get("damage_pct", 0.0) if ranking else 0.0,
                    ranking.get("severity", "") if ranking else "",
                    ranking.get("confidence", 0.0) if ranking else 0.0,
                    idx + 1,
                ),
            )

        # 4) Report (if fused data available)
        fused_dict = inspection_data.get("fused_inspection")
        if fused_dict:
            _insert_report_from_dict(conn, insp_id, fused_dict)

        conn.execute("COMMIT")
        _logger.info("Persisted full inspection %s.", insp_id)
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()

    return insp_id


def _insert_report_from_dict(conn: Any, inspection_id: str, fused: dict) -> None:
    """Insert a reports row from a serialised FusedInspection dict."""
    from streamlit_app.ai.health_engine import PropertyHealthReport
    from streamlit_app.ai.comparison_engine import ComparisonReport

    report_id = _new_id("RPT-")
    risk = fused.get("risk_assessment") or {}
    health = fused.get("health_report")
    comparison = fused.get("comparison_report")

    def _health_report(obj):
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj
        if is_dataclass(obj):
            return asdict(obj)
        return {}

    def _comparison_report(obj):
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj
        if is_dataclass(obj):
            return asdict(obj)
        return {}

    conn.execute(
        """INSERT INTO reports (
            report_id, inspection_id,
            overall_damage_pct, overall_confidence, overall_severity,
            overall_health_score, overall_estimated_cost_min,
            overall_estimated_cost_max, total_repair_area_px,
            avg_crack_width_px,
            findings_json, image_rankings_json,
            executive_summary, property_summary, inspection_conclusion,
            timeline_json, maintenance_tips_json,
            health_report_json, comparison_report_json,
            raw_reports_json, processing_time_sec
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            report_id,
            inspection_id,
            fused.get("overall_damage_pct", 0.0),
            fused.get("overall_confidence", 0.0),
            fused.get("overall_severity", ""),
            fused.get("overall_health_score", 100),
            fused.get("overall_estimated_cost_min", 0),
            fused.get("overall_estimated_cost_max", 0),
            fused.get("total_repair_area_px", 0),
            fused.get("avg_crack_width_px", 0.0),
            _to_json(fused.get("findings", [])),
            _to_json(fused.get("image_rankings", [])),
            fused.get("executive_summary", ""),
            fused.get("property_summary", ""),
            fused.get("inspection_conclusion", ""),
            _to_json(fused.get("timeline", [])),
            _to_json(fused.get("maintenance_tips", [])),
            _to_json(_health_report(health)),
            _to_json(_comparison_report(comparison)),
            _to_json(fused.get("source_reports_serialised", [])),
            fused.get("processing_time_sec", 0.0),
        ),
    )


def get_report(inspection_id: str) -> dict[str, Any] | None:
    """Retrieve a report by inspection_id.

    Returns the raw dict from the database (with JSON deserialized).
    Returns None if not found.
    """
    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM reports WHERE inspection_id = ?", (inspection_id,)
        ).fetchone()
        if not row:
            return None

        result = dict(row)
        # Deserialize JSON columns
        result["findings"] = _from_json(result.pop("findings_json", "[]"), default=[])
        result["image_rankings"] = _from_json(
            result.pop("image_rankings_json", "[]"), default=[]
        )
        result["timeline"] = _from_json(result.pop("timeline_json", "[]"), default=[])
        result["maintenance_tips"] = _from_json(
            result.pop("maintenance_tips_json", "[]"), default=[]
        )
        result["health_report"] = _from_json(
            result.pop("health_report_json", "{}"), default={}
        )
        result["comparison_report"] = _from_json(
            result.pop("comparison_report_json", "{}"), default={}
        )
        result["raw_reports"] = _from_json(
            result.pop("raw_reports_json", "[]"), default=[]
        )
        return result
    finally:
        conn.close()


def list_reports(
    severity: str = "",
    min_health_score: int = 0,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List reports with optional filters.

    Args:
        severity:         Filter by overall_severity (empty = all).
        min_health_score: Only reports with health_score >= this value.
        limit:            Max rows.
        offset:           Pagination offset.

    Returns:
        List of report dicts, newest first.
    """
    init_db()
    conn = get_connection()
    try:
        query = "SELECT * FROM reports WHERE 1=1"
        params: list[Any] = []

        if severity:
            query += " AND overall_severity = ?"
            params.append(severity)
        if min_health_score > 0:
            query += " AND overall_health_score >= ?"
            params.append(min_health_score)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        results = []
        for row in rows:
            r = dict(row)
            r["findings"] = _from_json(r.pop("findings_json", "[]"), default=[])
            r["image_rankings"] = _from_json(
                r.pop("image_rankings_json", "[]"), default=[]
            )
            r["timeline"] = _from_json(r.pop("timeline_json", "[]"), default=[])
            r["maintenance_tips"] = _from_json(
                r.pop("maintenance_tips_json", "[]"), default=[]
            )
            r["health_report"] = _from_json(
                r.pop("health_report_json", "{}"), default={}
            )
            r["comparison_report"] = _from_json(
                r.pop("comparison_report_json", "{}"), default={}
            )
            r["raw_reports"] = _from_json(
                r.pop("raw_reports_json", "[]"), default=[]
            )
            results.append(r)
        return results
    finally:
        conn.close()


def delete_report(report_id: str) -> bool:
    """Delete a report by ID.  Returns True if deleted."""
    init_db()
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM reports WHERE report_id = ?", (report_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── Internal serialization helpers ────────────────────────────────────────────

def _serialize_inspection_report(report: Any) -> dict[str, Any]:
    """Convert an InspectionReport to a plain dict."""
    if report is None:
        return {}
    if is_dataclass(report):
        return asdict(report)
    return {}


def _serialize_health_report(health: Any) -> dict[str, Any]:
    """Convert a PropertyHealthReport to a plain dict."""
    if health is None:
        return {}
    if is_dataclass(health):
        data = asdict(health)
        # Convert enums to their values
        for key, val in data.items():
            if isinstance(val, Enum):
                data[key] = val.value
            elif isinstance(val, list) and val and isinstance(val[0], Enum):
                data[key] = [v.value for v in val]
        return data
    return {}


def _serialize_comparison_report(comparison: Any) -> dict[str, Any]:
    """Convert a ComparisonReport to a plain dict."""
    if comparison is None:
        return {}
    if is_dataclass(comparison):
        data = asdict(comparison)
        # Serialize nested dataclasses in findings
        if "findings" in data and data["findings"]:
            data["findings"] = [
                asdict(f) if is_dataclass(f) else f
                for f in data["findings"]
            ]
        # Serialize previous/current snapshots
        for snap_key in ("previous", "current"):
            if snap_key in data and is_dataclass(data[snap_key]):
                data[snap_key] = asdict(data[snap_key])
        return data
    return {}


def _serialize_timeline_entry(entry: Any) -> dict[str, Any]:
    """Convert a TimelineEntry to a plain dict."""
    if is_dataclass(entry):
        return asdict(entry)
    if isinstance(entry, dict):
        return entry
    return {"str": str(entry)}


# ── Statistics / Dashboard helpers ────────────────────────────────────────────

def get_dashboard_stats() -> dict[str, Any]:
    """Return aggregate stats for the dashboard."""
    init_db()
    conn = get_connection()
    try:
        # Property counts
        total_properties = conn.execute(
            "SELECT COUNT(*) as c FROM properties"
        ).fetchone()["c"]

        # Inspection counts
        total_inspections = conn.execute(
            "SELECT COUNT(*) as c FROM inspections"
        ).fetchone()["c"]
        completed_inspections = conn.execute(
            "SELECT COUNT(*) as c FROM inspections WHERE status = 'completed'"
        ).fetchone()["c"]
        processing_inspections = conn.execute(
            "SELECT COUNT(*) as c FROM inspections WHERE status = 'processing'"
        ).fetchone()["c"]

        # Report counts by severity
        severity_rows = conn.execute(
            """SELECT overall_severity, COUNT(*) as cnt
               FROM reports GROUP BY overall_severity"""
        ).fetchall()
        by_severity = {r["overall_severity"] or "unknown": r["cnt"] for r in severity_rows}

        # Average health score
        avg_health = conn.execute(
            "SELECT AVG(overall_health_score) as avg FROM reports"
        ).fetchone()["avg"] or 0

        # Recent inspections (last 5)
        recent = conn.execute(
            """SELECT i.inspection_id, i.inspection_date, i.status,
                      p.address, p.city
               FROM inspections i
               JOIN properties p ON i.property_id = p.property_id
               ORDER BY i.created_at DESC LIMIT 5"""
        ).fetchall()

        return {
            "total_properties": total_properties,
            "total_inspections": total_inspections,
            "completed_inspections": completed_inspections,
            "processing_inspections": processing_inspections,
            "by_severity": by_severity,
            "avg_health_score": round(avg_health, 1),
            "recent_inspections": [dict(r) for r in recent],
        }
    finally:
        conn.close()


# ── Inspection History (Joined Query for History Page) ────────────────────────

def get_inspection_history(
    search: str = "",
    property_type: str = "",
    severity: str = "",
    grade: str = "",
    date_from: str = "",
    date_to: str = "",
    sort_by: str = "newest",
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Return an enriched list of inspections for the History page.

    Joins properties + inspections + reports so the UI can render cards
    without making N additional queries.

    Args:
        search:        Free-text query across property address, city,
                       property_id, inspection_id, inspector_name.
        property_type: Filter by property type (empty = all).
        severity:      Filter by overall_severity (empty = all).
        grade:         Filter by overall_health_score grade:
                       "excellent" (>=85), "good" (70-84),
                       "fair" (55-69), "poor" (<55).
        date_from:     ISO date (inclusive).
        date_to:       ISO date (inclusive).
        sort_by:       "newest", "oldest", "highest_damage",
                       "lowest_damage", "highest_cost".
        limit:         Max rows.
        offset:        Pagination offset.

    Returns:
        List of dicts with combined inspection + property + report data,
        with severity counts derived from findings JSON.
    """
    import re

    init_db()
    conn = get_connection()
    try:
        # Base query — LEFT JOIN because inspections may have no report yet
        query = """
            SELECT
                i.inspection_id,
                i.property_id,
                i.inspection_date,
                i.inspector_name,
                i.weather_condition,
                i.status            AS inspection_status,
                i.total_images,
                i.processing_time_sec,
                i.created_at        AS inspection_created_at,
                p.property_type,
                p.address           AS property_address,
                p.city              AS property_city,
                p.state             AS property_state,
                p.year_built,
                p.area_sqft,
                p.floors,
                r.report_id,
                r.overall_damage_pct,
                r.overall_confidence,
                r.overall_severity,
                r.overall_health_score,
                r.overall_estimated_cost_min,
                r.overall_estimated_cost_max,
                r.findings_json,
                r.executive_summary,
                r.created_at        AS report_created_at
            FROM inspections i
            JOIN properties p ON i.property_id = p.property_id
            LEFT JOIN reports r ON r.inspection_id = i.inspection_id
            WHERE 1=1
        """
        params: list[Any] = []

        # Search (address / city / property_id / inspection_id / inspector)
        if search:
            query += """ AND (
                p.address LIKE ? OR
                p.city LIKE ? OR
                p.property_id LIKE ? OR
                i.inspection_id LIKE ? OR
                i.inspector_name LIKE ?
            )"""
            like = f"%{search}%"
            params.extend([like, like, like, like, like])

        # Property type filter
        if property_type:
            query += " AND p.property_type = ?"
            params.append(property_type)

        # Severity filter (only applies if report exists)
        if severity:
            query += " AND r.overall_severity = ?"
            params.append(severity)

        # Grade filter (translate to health score range)
        if grade:
            grade_ranges = {
                "excellent": (85, 101),
                "good":      (70, 85),
                "fair":      (55, 70),
                "poor":      (0,  55),
            }
            if grade in grade_ranges:
                lo, hi = grade_ranges[grade]
                query += " AND r.overall_health_score >= ? AND r.overall_health_score < ?"
                params.extend([lo, hi])

        # Date range
        if date_from:
            query += " AND i.inspection_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND i.inspection_date <= ?"
            params.append(date_to)

        # Sorting
        sort_clauses = {
            "newest":         "i.inspection_date DESC, i.created_at DESC",
            "oldest":         "i.inspection_date ASC, i.created_at ASC",
            "highest_damage": "COALESCE(r.overall_damage_pct, 0) DESC",
            "lowest_damage":  "COALESCE(r.overall_damage_pct, 0) ASC",
            "highest_cost":   "COALESCE(r.overall_estimated_cost_max, 0) DESC",
        }
        order_by = sort_clauses.get(sort_by, sort_clauses["newest"])
        query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()

        # Post-process — flatten findings into severity counts + repair cost avg
        results: list[dict[str, Any]] = []
        for row in rows:
            r = dict(row)

            # Parse findings JSON to derive per-severity counts
            findings = _from_json(r.pop("findings_json", "[]"), default=[])
            counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for f in findings:
                sev = (f.get("severity") or "").lower()
                if sev in counts:
                    counts[sev] += 1
            r["critical_count"] = counts["critical"]
            r["high_count"] = counts["high"]
            r["medium_count"] = counts["medium"]
            r["low_count"] = counts["low"]
            r["damages_found"] = sum(counts.values())

            # Average repair cost (midpoint)
            cost_min = r.get("overall_estimated_cost_min") or 0
            cost_max = r.get("overall_estimated_cost_max") or 0
            r["avg_repair_cost"] = (cost_min + cost_max) // 2 if cost_max else 0

            # Derive grade letter from health score
            score = r.get("overall_health_score") or 0
            if score >= 90:
                r["grade"] = "A+"
            elif score >= 80:
                r["grade"] = "A"
            elif score >= 70:
                r["grade"] = "B+"
            elif score >= 60:
                r["grade"] = "B"
            elif score >= 50:
                r["grade"] = "C"
            else:
                r["grade"] = "D"

            # Risk level derived from severity + health score
            severity_val = (r.get("overall_severity") or "").lower()
            if severity_val == "critical" or score < 50:
                r["risk_level"] = "Critical"
            elif severity_val == "high" or score < 70:
                r["risk_level"] = "High"
            elif severity_val == "medium" or score < 85:
                r["risk_level"] = "Medium"
            else:
                r["risk_level"] = "Low"

            # Image count fallback
            r["image_count"] = r.get("total_images") or 0

            results.append(r)
        return results
    finally:
        conn.close()


def get_history_stats() -> dict[str, Any]:
    """Return aggregate stats for the History page.

    Returns:
        Dict with total_inspections, avg_health_score,
        critical_count (properties with critical severity), avg_repair_cost.
    """
    init_db()
    conn = get_connection()
    try:
        total_inspections = conn.execute(
            "SELECT COUNT(*) AS c FROM inspections"
        ).fetchone()["c"]

        avg_health = conn.execute(
            """SELECT AVG(overall_health_score) AS avg
               FROM reports
               WHERE overall_health_score IS NOT NULL"""
        ).fetchone()["avg"] or 0

        critical_count = conn.execute(
            """SELECT COUNT(DISTINCT inspection_id) AS c
               FROM reports
               WHERE overall_severity = 'critical'"""
        ).fetchone()["c"]

        avg_cost = conn.execute(
            """SELECT AVG((overall_estimated_cost_min + overall_estimated_cost_max) / 2.0) AS avg
               FROM reports
               WHERE overall_estimated_cost_min > 0 OR overall_estimated_cost_max > 0"""
        ).fetchone()["avg"] or 0

        return {
            "total_inspections": total_inspections,
            "avg_health_score": round(avg_health, 1),
            "critical_count": critical_count,
            "avg_repair_cost": int(avg_cost),
        }
    finally:
        conn.close()
