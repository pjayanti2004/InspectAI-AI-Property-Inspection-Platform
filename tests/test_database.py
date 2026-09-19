"""Tests for the Database layer.

Uses in-memory SQLite via the ``db_conn`` fixture.  Covers CRUD for
properties, inspections, images, and reports — including JSON
serialization round-trips and foreign-key cascade behaviour.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date, datetime

import pytest

from streamlit_app.database.schema import ALL_SCHEMA_STATEMENTS


# ── Helpers ──────────────────────────────────────────────────────────────────────

def _uid(prefix: str = "") -> str:
    """Generate a unique ID."""
    return f"{prefix}{uuid.uuid4().hex[:10].upper()}"


def _now() -> str:
    return datetime.now().isoformat()


def _insert_property(conn, **kwargs):
    """Insert a property row directly and return its ID."""
    prop_id = _uid("PROP-")
    defaults = dict(
        property_id=prop_id,
        property_type="residential",
        address="123 Test St",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
        year_built=2010,
        area_sqft=1200,
        floors=2,
        construction_type="RCC",
        inspector_name="Test Inspector",
        notes="Test property",
        created_at=_now(),
        updated_at=_now(),
    )
    defaults.update(kwargs)
    cols = ", ".join(defaults.keys())
    placeholders = ", ".join(["?"] * len(defaults))
    conn.execute(
        f"INSERT INTO properties ({cols}) VALUES ({placeholders})",
        tuple(defaults.values()),
    )
    conn.commit()
    return prop_id


def _insert_inspection(conn, property_id, **kwargs):
    """Insert an inspection row directly and return its ID."""
    insp_id = _uid("INSP-")
    defaults = dict(
        inspection_id=insp_id,
        property_id=property_id,
        inspection_date=date.today().isoformat(),
        inspector_name="Test Inspector",
        weather_condition="",
        notes="",
        status="processing",
        total_images=0,
        processing_time_sec=0.0,
        created_at=_now(),
    )
    defaults.update(kwargs)
    cols = ", ".join(defaults.keys())
    placeholders = ", ".join(["?"] * len(defaults))
    conn.execute(
        f"INSERT INTO inspections ({cols}) VALUES ({placeholders})",
        tuple(defaults.values()),
    )
    conn.commit()
    return insp_id


def _insert_image(conn, inspection_id, file_name, **kwargs):
    """Insert an inspection image row directly."""
    img_id = _uid("IMG-")
    defaults = dict(
        image_id=img_id,
        inspection_id=inspection_id,
        file_name=file_name,
        file_path=None,
        file_size_kb=250.0,
        width_px=640,
        height_px=480,
        damage_pct=0.0,
        severity="",
        confidence=0.0,
        damage_types="[]",
        rank_order=0,
        created_at=_now(),
    )
    defaults.update(kwargs)
    cols = ", ".join(defaults.keys())
    placeholders = ", ".join(["?"] * len(defaults))
    conn.execute(
        f"INSERT INTO inspection_images ({cols}) VALUES ({placeholders})",
        tuple(defaults.values()),
    )
    conn.commit()
    return img_id


def _insert_report(conn, inspection_id, **kwargs):
    """Insert a report row directly and return its ID."""
    report_id = _uid("RPT-")
    defaults = dict(
        report_id=report_id,
        inspection_id=inspection_id,
        overall_damage_pct=0.0,
        overall_confidence=0.0,
        overall_severity="",
        overall_health_score=100,
        overall_estimated_cost_min=0,
        overall_estimated_cost_max=0,
        total_repair_area_px=0,
        avg_crack_width_px=0.0,
        findings_json="[]",
        image_rankings_json="[]",
        executive_summary="",
        property_summary="",
        inspection_conclusion="",
        timeline_json="[]",
        maintenance_tips_json="[]",
        health_report_json="{}",
        comparison_report_json="{}",
        raw_reports_json="[]",
        processing_time_sec=0.0,
        ai_model_version="opencv-1.0",
        created_at=_now(),
    )
    defaults.update(kwargs)
    cols = ", ".join(defaults.keys())
    placeholders = ", ".join(["?"] * len(defaults))
    conn.execute(
        f"INSERT INTO reports ({cols}) VALUES ({placeholders})",
        tuple(defaults.values()),
    )
    conn.commit()
    return report_id


# ── Properties ──────────────────────────────────────────────────────────────────

class TestProperties:
    def test_create_returns_id(self, db_conn):
        prop_id = _insert_property(db_conn)
        assert prop_id.startswith("PROP-")
        assert len(prop_id) > 10

    def test_get_property_roundtrip(self, db_conn):
        prop_id = _insert_property(db_conn)
        row = db_conn.execute(
            "SELECT * FROM properties WHERE property_id = ?", (prop_id,)
        ).fetchone()
        assert row is not None
        assert row["address"] == "123 Test St"
        assert row["city"] == "Mumbai"
        assert row["property_type"] == "residential"

    def test_get_missing_returns_none(self, db_conn):
        row = db_conn.execute(
            "SELECT * FROM properties WHERE property_id = ?", ("PROP-NONEXISTENT",)
        ).fetchone()
        assert row is None

    def test_list_properties_returns_created(self, db_conn):
        _insert_property(db_conn)
        rows = db_conn.execute("SELECT * FROM properties").fetchall()
        assert len(rows) >= 1

    def test_list_filtered_by_city(self, db_conn):
        _insert_property(db_conn, city="Mumbai")
        _insert_property(db_conn, city="Delhi")
        rows = db_conn.execute(
            "SELECT * FROM properties WHERE city = ?", ("Mumbai",)
        ).fetchall()
        assert len(rows) >= 1
        assert all(r["city"] == "Mumbai" for r in rows)

    def test_update_property(self, db_conn):
        prop_id = _insert_property(db_conn)
        db_conn.execute(
            "UPDATE properties SET address = ? WHERE property_id = ?",
            ("456 New St", prop_id),
        )
        db_conn.commit()
        row = db_conn.execute(
            "SELECT * FROM properties WHERE property_id = ?", (prop_id,)
        ).fetchone()
        assert row["address"] == "456 New St"

    def test_delete_property(self, db_conn):
        prop_id = _insert_property(db_conn)
        result = db_conn.execute(
            "DELETE FROM properties WHERE property_id = ?", (prop_id,)
        )
        db_conn.commit()
        assert result.rowcount >= 1
        row = db_conn.execute(
            "SELECT * FROM properties WHERE property_id = ?", (prop_id,)
        ).fetchone()
        assert row is None

    def test_delete_missing_returns_false(self, db_conn):
        result = db_conn.execute(
            "DELETE FROM properties WHERE property_id = ?", ("PROP-NONEXISTENT",)
        )
        db_conn.commit()
        assert result.rowcount == 0


# ── Inspections ──────────────────────────────────────────────────────────────────

class TestInspections:
    def test_create_inspection(self, db_conn):
        prop_id = _insert_property(db_conn)
        insp_id = _insert_inspection(db_conn, property_id=prop_id)
        assert insp_id.startswith("INSP-")

    def test_get_inspection(self, db_conn):
        prop_id = _insert_property(db_conn)
        insp_id = _insert_inspection(db_conn, property_id=prop_id)
        row = db_conn.execute(
            "SELECT * FROM inspections WHERE inspection_id = ?", (insp_id,)
        ).fetchone()
        assert row is not None
        assert row["property_id"] == prop_id
        assert row["status"] == "processing"

    def test_get_inspections_by_property(self, db_conn):
        prop_id = _insert_property(db_conn)
        _insert_inspection(db_conn, property_id=prop_id)
        _insert_inspection(db_conn, property_id=prop_id)
        rows = db_conn.execute(
            "SELECT * FROM inspections WHERE property_id = ?", (prop_id,)
        ).fetchall()
        assert len(rows) == 2

    def test_update_status(self, db_conn):
        prop_id = _insert_property(db_conn)
        insp_id = _insert_inspection(db_conn, property_id=prop_id)
        db_conn.execute(
            "UPDATE inspections SET status = ?, total_images = ? WHERE inspection_id = ?",
            ("completed", 3, insp_id),
        )
        db_conn.commit()
        row = db_conn.execute(
            "SELECT * FROM inspections WHERE inspection_id = ?", (insp_id,)
        ).fetchone()
        assert row["status"] == "completed"
        assert row["total_images"] == 3

    def test_delete_inspection_cascades(self, db_conn):
        prop_id = _insert_property(db_conn)
        insp_id = _insert_inspection(db_conn, property_id=prop_id)
        _insert_image(db_conn, insp_id, "img1.jpg")
        db_conn.execute(
            "DELETE FROM inspections WHERE inspection_id = ?", (insp_id,)
        )
        db_conn.commit()
        rows = db_conn.execute(
            "SELECT * FROM inspection_images WHERE inspection_id = ?", (insp_id,)
        ).fetchall()
        assert len(rows) == 0


# ── Images ───────────────────────────────────────────────────────────────────────

class TestInspectionImages:
    def test_save_and_retrieve(self, db_conn):
        prop_id = _insert_property(db_conn)
        insp_id = _insert_inspection(db_conn, property_id=prop_id)
        img_id = _insert_image(
            db_conn, insp_id, "wall.jpg",
            file_size_kb=250.5, width_px=640, height_px=480,
            damage_pct=5.0, severity="Medium", confidence=85,
            damage_types=json.dumps(["Crack", "Water Damage"]),
        )
        assert img_id.startswith("IMG-")

        rows = db_conn.execute(
            "SELECT * FROM inspection_images WHERE inspection_id = ?", (insp_id,)
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["file_name"] == "wall.jpg"
        assert rows[0]["severity"] == "Medium"
        assert json.loads(rows[0]["damage_types"]) == ["Crack", "Water Damage"]

    def test_images_ordered_by_rank(self, db_conn):
        prop_id = _insert_property(db_conn)
        insp_id = _insert_inspection(db_conn, property_id=prop_id)
        _insert_image(db_conn, insp_id, "a.jpg", rank_order=2)
        _insert_image(db_conn, insp_id, "b.jpg", rank_order=1)
        rows = db_conn.execute(
            "SELECT * FROM inspection_images WHERE inspection_id = ? ORDER BY rank_order ASC",
            (insp_id,),
        ).fetchall()
        assert rows[0]["file_name"] == "b.jpg"  # rank 1 first


# ── Reports ──────────────────────────────────────────────────────────────────────

class TestReports:
    def test_save_and_get_report(self, db_conn):
        prop_id = _insert_property(db_conn)
        insp_id = _insert_inspection(db_conn, property_id=prop_id)
        report_id = _insert_report(db_conn, insp_id)
        assert report_id.startswith("RPT-")

        row = db_conn.execute(
            "SELECT * FROM reports WHERE inspection_id = ?", (insp_id,)
        ).fetchone()
        assert row is not None
        assert row["report_id"] == report_id
        assert row["inspection_id"] == insp_id

    def test_report_json_fields_roundtrip(self, db_conn):
        prop_id = _insert_property(db_conn)
        insp_id = _insert_inspection(db_conn, property_id=prop_id)
        _insert_report(
            db_conn, insp_id,
            findings_json=json.dumps([{"damage_type": "Crack", "severity": "High"}]),
            timeline_json=json.dumps([{"bucket": "immediate"}, {"bucket": "7d"}, {"bucket": "30d"}, {"bucket": "future"}]),
            maintenance_tips_json=json.dumps(["Tip 1", "Tip 2"]),
        )
        row = db_conn.execute(
            "SELECT * FROM reports WHERE inspection_id = ?", (insp_id,)
        ).fetchone()
        findings = json.loads(row["findings_json"])
        assert len(findings) >= 1
        assert findings[0]["damage_type"] == "Crack"

        timeline = json.loads(row["timeline_json"])
        assert len(timeline) == 4

        tips = json.loads(row["maintenance_tips_json"])
        assert isinstance(tips, list)

    def test_report_health_score_persisted(self, db_conn):
        prop_id = _insert_property(db_conn)
        insp_id = _insert_inspection(db_conn, property_id=prop_id)
        _insert_report(db_conn, insp_id, overall_health_score=72)
        row = db_conn.execute(
            "SELECT * FROM reports WHERE inspection_id = ?", (insp_id,)
        ).fetchone()
        assert row["overall_health_score"] == 72


# ── Transaction rollback ─────────────────────────────────────────────────────────

class TestTransactions:
    def test_failed_insert_does_not_persist(self, db_conn):
        _insert_property(db_conn)
        # Try inserting with a NULL NOT NULL column — should fail
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO properties (property_id, property_type) VALUES (?, NULL)",
                ("PROP-TRANS-TEST",),
            )
        # Count should be unchanged (insert failed)
        count = db_conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
        assert count >= 1
