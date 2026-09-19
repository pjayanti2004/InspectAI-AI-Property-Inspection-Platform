"""SQLite schema definitions for InspectAI.

All DDL statements are defined here as module-level constants.
Kept separate from database.py and repository.py so the migration
history lives in one place and the connection layer stays thin.
"""
from __future__ import annotations

# ── Table: properties ─────────────────────────────────────────────────────────

CREATE_TABLE_PROPERTIES = """\
CREATE TABLE IF NOT EXISTS properties (
    property_id      TEXT PRIMARY KEY,
    property_type    TEXT NOT NULL CHECK (property_type IN (
                         'residential', 'commercial', 'industrial',
                         'institutional', 'mixed_use', 'other'
                     )),
    address          TEXT,
    city             TEXT DEFAULT '',
    state            TEXT DEFAULT '',
    pincode          TEXT DEFAULT '',
    year_built       INTEGER,
    area_sqft        INTEGER,
    floors           INTEGER,
    construction_type TEXT,
    inspector_name   TEXT DEFAULT '',
    notes            TEXT DEFAULT '',
    created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""

CREATE_INDEX_PROPERTIES_TYPE = """\
CREATE INDEX IF NOT EXISTS idx_properties_type ON properties(property_type);
"""

CREATE_INDEX_PROPERTIES_CITY = """\
CREATE INDEX IF NOT EXISTS idx_properties_city ON properties(city);
"""

# ── Table: inspections ────────────────────────────────────────────────────────

CREATE_TABLE_INSPECTIONS = """\
CREATE TABLE IF NOT EXISTS inspections (
    inspection_id    TEXT PRIMARY KEY,
    property_id      TEXT NOT NULL REFERENCES properties(property_id)
                         ON DELETE CASCADE,
    inspection_date  TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    inspector_name   TEXT DEFAULT '',
    weather_condition TEXT DEFAULT '',
    notes            TEXT DEFAULT '',
    status           TEXT NOT NULL DEFAULT 'processing'
                         CHECK (status IN (
                             'processing', 'completed', 'failed'
                         )),
    total_images     INTEGER DEFAULT 0,
    processing_time_sec REAL DEFAULT 0.0,
    created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""

CREATE_INDEX_INSPECTIONS_PROPERTY = """\
CREATE INDEX IF NOT EXISTS idx_inspections_property
    ON inspections(property_id);
"""

CREATE_INDEX_INSPECTIONS_DATE = """\
CREATE INDEX IF NOT EXISTS idx_inspections_date
    ON inspections(inspection_date DESC);
"""

# ── Table: inspection_images ──────────────────────────────────────────────────

CREATE_TABLE_INSPECTION_IMAGES = """\
CREATE TABLE IF NOT EXISTS inspection_images (
    image_id         TEXT PRIMARY KEY,
    inspection_id    TEXT NOT NULL REFERENCES inspections(inspection_id)
                         ON DELETE CASCADE,
    file_name        TEXT NOT NULL,
    file_path        TEXT,
    file_size_kb     REAL DEFAULT 0.0,
    width_px         INTEGER DEFAULT 0,
    height_px        INTEGER DEFAULT 0,
    damage_pct       REAL DEFAULT 0.0,
    severity         TEXT DEFAULT '',
    confidence       REAL DEFAULT 0.0,
    damage_types     TEXT DEFAULT '[]',   -- JSON array of strings
    rank_order       INTEGER DEFAULT 0,   -- 1 = most damaged
    created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""

CREATE_INDEX_IMAGES_INSPECTION = """\
CREATE INDEX IF NOT EXISTS idx_images_inspection
    ON inspection_images(inspection_id);
"""

CREATE_INDEX_IMAGES_RANK = """\
CREATE INDEX IF NOT EXISTS idx_images_rank
    ON inspection_images(inspection_id, rank_order);
"""

# ── Table: reports ────────────────────────────────────────────────────────────

CREATE_TABLE_REPORTS = """\
CREATE TABLE IF NOT EXISTS reports (
    report_id        TEXT PRIMARY KEY,
    inspection_id    TEXT NOT NULL UNIQUE REFERENCES inspections(inspection_id)
                         ON DELETE CASCADE,
    -- Core AI results
    overall_damage_pct      REAL DEFAULT 0.0,
    overall_confidence      REAL DEFAULT 0.0,
    overall_severity        TEXT DEFAULT '',
    overall_health_score    INTEGER DEFAULT 100,
    overall_estimated_cost_min INTEGER DEFAULT 0,
    overall_estimated_cost_max INTEGER DEFAULT 0,
    total_repair_area_px    INTEGER DEFAULT 0,
    avg_crack_width_px      REAL DEFAULT 0.0,
    -- Rich data as JSON (single write, avoids N+1 tables)
    findings_json       TEXT DEFAULT '[]',   -- list of FusedFinding dicts
    image_rankings_json TEXT DEFAULT '[]',   -- list of ImageRank dicts
    executive_summary   TEXT DEFAULT '',
    property_summary    TEXT DEFAULT '',
    inspection_conclusion TEXT DEFAULT '',
    timeline_json       TEXT DEFAULT '[]',   -- list of TimelineEntry dicts
    maintenance_tips_json TEXT DEFAULT '[]', -- list of strings
    -- Health Report as JSON
    health_report_json  TEXT DEFAULT '{}',
    -- Comparison Report as JSON
    comparison_report_json TEXT DEFAULT '{}',
    -- Raw data for re-processing
    raw_reports_json    TEXT DEFAULT '[]',   -- serialised source InspectionReport list
    -- Metadata
    processing_time_sec REAL DEFAULT 0.0,
    ai_model_version    TEXT DEFAULT 'opencv-1.0',
    created_at          TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""

CREATE_INDEX_REPORTS_SEVERITY = """\
CREATE INDEX IF NOT EXISTS idx_reports_severity
    ON reports(overall_severity);
"""

CREATE_INDEX_REPORTS_HEALTH = """\
CREATE INDEX IF NOT EXISTS idx_reports_health
    ON reports(overall_health_score);
"""

# ── Indexes ───────────────────────────────────────────────────────────────────

CREATE_INDEX_PROPERTIES_UPDATED = """\
CREATE INDEX IF NOT EXISTS idx_properties_updated ON properties(updated_at DESC);
"""

CREATE_INDEX_INSPECTIONS_STATUS = """\
CREATE INDEX IF NOT EXISTS idx_inspections_status ON inspections(status, created_at DESC);
"""

CREATE_INDEX_REPORTS_CREATED = """\
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at DESC);
"""

# ── Migration tracking ────────────────────────────────────────────────────────

CREATE_TABLE_MIGRATIONS = """\
CREATE TABLE IF NOT EXISTS schema_migrations (
    version   INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""

# ── Full schema as a list (applied in order) ──────────────────────────────────

ALL_SCHEMA_STATEMENTS: list[str] = [
    CREATE_TABLE_PROPERTIES,
    CREATE_INDEX_PROPERTIES_TYPE,
    CREATE_INDEX_PROPERTIES_CITY,
    CREATE_INDEX_PROPERTIES_UPDATED,
    CREATE_TABLE_INSPECTIONS,
    CREATE_INDEX_INSPECTIONS_PROPERTY,
    CREATE_INDEX_INSPECTIONS_DATE,
    CREATE_INDEX_INSPECTIONS_STATUS,
    CREATE_TABLE_INSPECTION_IMAGES,
    CREATE_INDEX_IMAGES_INSPECTION,
    CREATE_INDEX_IMAGES_RANK,
    CREATE_TABLE_REPORTS,
    CREATE_INDEX_REPORTS_SEVERITY,
    CREATE_INDEX_REPORTS_HEALTH,
    CREATE_INDEX_REPORTS_CREATED,
    CREATE_TABLE_MIGRATIONS,
]
