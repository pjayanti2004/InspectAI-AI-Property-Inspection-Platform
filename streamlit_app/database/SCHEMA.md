# InspectAI — SQLite Schema Diagram

## Entity-Relationship Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           properties                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ PK  property_id         TEXT          (PROP-XXXXXXXXXXXX)         │  │
│  │     property_type       TEXT          [residential|commercial|...]│  │
│  │     address             TEXT                                      │  │
│  │     city                TEXT                                      │  │
│  │     state               TEXT                                      │  │
│  │     pincode             TEXT                                      │  │
│  │     year_built          INTEGER                                  │  │
│  │     area_sqft           INTEGER                                  │  │
│  │     floors              INTEGER                                  │  │
│  │     construction_type   TEXT                                      │  │
│  │     inspector_name      TEXT                                      │  │
│  │     notes               TEXT                                      │  │
│  │     created_at          TEXT        (ISO 8601 datetime)          │  │
│  │     updated_at          TEXT        (ISO 8601 datetime)          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│        │                                                                 │
│        │ 1:N                                                             │
│        ▼                                                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                           inspections                               │  │
│  │  ┌───────────────────────────────────────────────────────────────┐ │  │
│  │  │ PK  inspection_id      TEXT     (INSP-XXXXXXXXXXXX)           │ │  │
│  │  │ FK  property_id        TEXT     → properties.property_id      │ │  │
│  │  │     inspection_date    TEXT     (ISO 8601 date)               │ │  │
│  │  │     inspector_name     TEXT                                   │ │  │
│  │  │     weather_condition  TEXT                                   │ │  │
│  │  │     notes              TEXT                                   │ │  │
│  │  │     status             TEXT     [processing|completed|failed] │ │  │
│  │  │     total_images       INTEGER   DEFAULT 0                   │ │  │
│  │  │     processing_time    REAL      DEFAULT 0.0                 │ │  │
│  │  │     created_at         TEXT     (ISO 8601 datetime)           │ │  │
│  │  └───────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│        │                                                                 │
│        │ 1:N                                                             │
│        ▼                                                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        inspection_images                            │  │
│  │  ┌───────────────────────────────────────────────────────────────┐ │  │
│  │  │ PK  image_id           TEXT     (IMG-XXXXXXXXXXXX)            │ │  │
│  │  │ FK  inspection_id      TEXT     → inspections.inspection_id   │ │  │
│  │  │     file_name          TEXT     Original file name            │ │  │
│  │  │     file_path          TEXT     Full disk path (optional)     │ │  │
│  │  │     file_size_kb       REAL     File size in KB               │ │  │
│  │  │     width_px           INTEGER  Image width                    │ │  │
│  │  │     height_px          INTEGER  Image height                   │ │  │
│  │  │     damage_pct         REAL     AI-detected damage %           │ │  │
│  │  │     severity           TEXT     [Critical|High|Medium|Low|""] │ │  │
│  │  │     confidence         REAL     AI confidence (0-100)         │ │  │
│  │  │     damage_types       TEXT     JSON array of strings         │ │  │
│  │  │     rank_order         INTEGER  1 = most damaged              │ │  │
│  │  │     created_at         TEXT     (ISO 8601 datetime)           │ │  │
│  │  └───────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                           reports                                   │  │
│  │  ┌───────────────────────────────────────────────────────────────┐ │  │
│  │  │ PK  report_id          TEXT     (RPT-XXXXXXXXXXXX)            │ │  │
│  │  │ FK  inspection_id      TEXT     → inspections.inspection_id   │ │  │
│  │  │     (UNIQUE — 1:1 with inspection)                             │ │  │
│  │  ├───────────────────────────────────────────────────────────────┤ │  │
│  │  │  AI CORE RESULTS                                                │ │  │
│  │  │     overall_damage_pct      REAL                               │ │  │
│  │  │     overall_confidence      REAL                               │ │  │
│  │  │     overall_severity        TEXT                               │ │  │
│  │  │     overall_health_score    INTEGER  (0-100)                   │ │  │
│  │  │     overall_estimated_cost_min INTEGER                        │ │  │
│  │  │     overall_estimated_cost_max INTEGER                        │ │  │
│  │  │     total_repair_area_px    INTEGER                           │ │  │
│  │  │     avg_crack_width_px      REAL                              │ │  │
│  │  ├───────────────────────────────────────────────────────────────┤ │  │
│  │  │  JSON COLUMNS (complex nested data)                             │ │  │
│  │  │     findings_json           TEXT    list of FusedFinding       │ │  │
│  │  │     image_rankings_json     TEXT    list of ImageRank          │ │  │
│  │  │     executive_summary       TEXT    8-sentence AI summary      │ │  │
│  │  │     property_summary        TEXT    Property overview          │ │  │
│  │  │     inspection_conclusion   TEXT    Final verdict paragraph     │ │  │
│  │  │     timeline_json           TEXT    list of TimelineEntry      │ │  │
│  │  │     maintenance_tips_json   TEXT    list of strings            │ │  │
│  │  │     health_report_json      TEXT    PropertyHealthReport dict  │ │  │
│  │  │     comparison_report_json  TEXT    ComparisonReport dict      │ │  │
│  │  │     raw_reports_json        TEXT    Serialised source reports  │ │  │
│  │  ├───────────────────────────────────────────────────────────────┤ │  │
│  │  │  METADATA                                                       │ │  │
│  │  │     processing_time_sec   REAL                                │ │  │
│  │  │     ai_model_version      TEXT    "opencv-1.0"                 │ │  │
│  │  │     created_at            TEXT    (ISO 8601 datetime)          │ │  │
│  │  └───────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        schema_migrations                           │  │
│  │  ┌───────────────────────────────────────────────────────────────┐ │  │
│  │  │ PK  version   INTEGER      Applied migration version           │ │  │
│  │  │     applied_at TEXT        (ISO 8601 datetime)                 │ │  │
│  │  └───────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Relationship Summary

```
properties (1) ──────► (N) inspections (1) ──────► (1) reports
                              │
                              │ (1) ──────► (N) inspection_images
```

| Relationship | Cardinality | Notes |
|---|---|---|
| property → inspection | 1:N | One property can have many inspections over time |
| inspection → image | 1:N | Each inspection captures multiple images |
| inspection → report | 1:1 | Each completed inspection produces exactly one report |
| property → report | 1:N | Through inspection: property has many reports |

## Indexes

| Table | Index | Columns | Purpose |
|---|---|---|---|
| properties | idx_properties_type | property_type | Filter by property type |
| properties | idx_properties_city | city | Search by city |
| inspections | idx_inspections_property | property_id | Lookup all inspections for a property |
| inspections | idx_inspections_date | inspection_date DESC | Timeline queries, newest first |
| inspection_images | idx_images_inspection | inspection_id | Get all images for an inspection |
| inspection_images | idx_images_rank | inspection_id, rank_order | Ordered image retrieval |
| reports | idx_reports_severity | overall_severity | Filter reports by damage severity |
| reports | idx_reports_health | overall_health_score | Filter by health score |
