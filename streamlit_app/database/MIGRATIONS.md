# InspectAI — Database Migration Guide

## Current Version: 1.0

The database schema is version 1.0 (initial release). This document describes
how to manage migrations as the schema evolves.

---

## How Migrations Work

1. Every schema change gets a new version number.
2. Each migration is an idempotent SQL statement.
3. Applied versions are tracked in `schema_migrations` table.
4. `init_db()` runs automatically on first use — no manual setup needed.

---

## Version History

### Version 1.0 — Initial Schema

**Date:** 2024-07-15
**Tables created:**
- `properties` — Property master data
- `inspections` — Inspection sessions
- `inspection_images` — Per-image metadata
- `reports` — AI analysis results
- `schema_migrations` — Migration tracking

**Migration SQL:**
```sql
-- All schema statements in schema.py applied in order
-- Version 1 recorded in schema_migrations
```

---

## How to Add a New Migration

### Step 1: Add the SQL to `schema.py`

```python
# In streamlit_app/database/schema.py

# Version 2: Add inspector credentials table
CREATE_TABLE_INSPECTOR_CREDENTIALS = """\
CREATE TABLE IF NOT EXISTS inspector_credentials (
    inspector_id    TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE,
    license_number  TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""

# Add to ALL_SCHEMA_STATEMENTS
ALL_SCHEMA_STATEMENTS.append(CREATE_TABLE_INSPECTOR_CREDENTIALS)
```

### Step 2: Bump the version in `database.py`

```python
# In streamlit_app/database/database.py, update init_db():
conn.execute(
    "INSERT OR IGNORE INTO schema_migrations(version) VALUES(2)"  # was 1
)
```

### Step 3: (Optional) Backfill existing data

```python
# In streamlit_app/database/database.py or a separate migration script:
# Backfill inspector names into a new table, etc.
```

---

## Rollback Procedure

If a migration causes issues:

```python
from streamlit_app.database.database import reset_db

# WARNING: Destroys all data. Use only in development.
reset_db()
```

For production, write explicit down migrations:

```python
DOWN_MIGRATION_2 = "DROP TABLE IF EXISTS inspector_credentials"
```

---

## Development Workflow

### First time setup
```bash
python -c "from streamlit_app.database.database import init_db; init_db()"
```

### Reset database (development only)
```python
python -c "from streamlit_app.database.database import reset_db; reset_db()"
```

### Check current version
```python
python -c "from streamlit_app.database.database import get_db_version; print(get_db_version())"
```

### Run tests
```bash
python test_db.py
```

---

## Schema Evolution Plan (Future Versions)

### Version 2.0 — Inspector Management
```sql
CREATE TABLE inspector_credentials (
    inspector_id    TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE,
    phone           TEXT,
    license_number  TEXT,
    specialization  TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

ALTER TABLE inspections ADD COLUMN inspector_id TEXT
    REFERENCES inspector_credentials(inspector_id);
```

### Version 3.0 — Repair Tracking
```sql
CREATE TABLE repair_tasks (
    task_id         TEXT PRIMARY KEY,
    inspection_id   TEXT NOT NULL REFERENCES inspections(inspection_id),
    finding_id      TEXT NOT NULL,
    status          TEXT DEFAULT 'pending',
    assigned_to     TEXT,
    estimated_cost  INTEGER,
    actual_cost     INTEGER,
    started_at      TEXT,
    completed_at    TEXT,
    notes           TEXT DEFAULT ''
);
```

### Version 4.0 — User Accounts (Optional)
```sql
CREATE TABLE users (
    user_id         TEXT PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT DEFAULT 'user',
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
```

---

## Notes

- **No ALTER TABLE for production data** — create new tables and migrate data in Python.
- **Use IF NOT EXISTS** — all CREATE TABLE statements are idempotent.
- **Foreign keys** — SQLite enforces FK constraints with `PRAGMA foreign_keys=ON`.
- **JSON columns** — complex nested data is stored as JSON strings, not separate tables. This is intentional: the data is read/written as a unit and never queried individually.
- **UUIDs** — IDs use `uuid.uuid4().hex[:12].upper()` with prefixes (PROP-, INSP-, IMG-, RPT-).
- **Timestamps** — all timestamps use ISO 8601 format with local timezone.
