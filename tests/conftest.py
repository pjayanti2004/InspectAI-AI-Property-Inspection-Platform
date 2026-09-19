"""Shared fixtures for the InspectAI test suite.

Provides synthetic images, contours, masks, and in-memory database
connections so every test module can build realistic inputs without
duplicating setup code.

Also provides a ``mock_streamlit`` fixture that injects a fake
``streamlit`` module so session-manager and page code can be tested
without a real Streamlit runtime.
"""
from __future__ import annotations

import io
import sqlite3
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image


# ── Paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ── Streamlit mock ──────────────────────────────────────────────────────────────

class _FakeRerun:
    def __call__(self):
        pass


class _FakeSessionState(dict):
    """Dict-like stand-in for st.session_state."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __contains__(self, item):
        return super().__contains__(item)


class _FakeStreamlit:
    """Minimal stand-in for the ``streamlit`` package."""
    session_state = _FakeSessionState()
    sidebar = type("Sidebar", (), {})()

    def rerun(self):
        pass

    # Provide st.rerun as callable attribute
    rerun = _FakeRerun()


@pytest.fixture(autouse=False)
def mock_streamlit(monkeypatch):
    """Install a fake ``streamlit`` module in sys.modules."""
    fake = _FakeStreamlit()
    import types
    mod = types.ModuleType("streamlit")
    mod.session_state = fake.session_state
    mod.rerun = fake.rerun
    mod.sidebar = fake.sidebar
    monkeypatch.setitem(sys.modules, "streamlit", mod)
    return mod

# ── Paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ── Synthetic image factory ────────────────────────────────────────────────────

def _make_synthetic_image(
    width: int = 640,
    height: int = 480,
    damage_regions: list | None = None,
) -> np.ndarray:
    """Create a synthetic BGR image with optional damage regions."""
    img = np.full((height, width, 3), 210, dtype=np.uint8)

    if damage_regions:
        for x, y, w, h, color in damage_regions:
            x2 = min(x + w, width)
            y2 = min(y + h, height)
            img[y:y2, x:x2] = color

    noise = np.random.randint(-10, 10, (height, width, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return img


def _make_contour(x: int, y: int, w: int, h: int) -> np.ndarray:
    """Create a simple rectangular contour (cv2-style)."""
    return np.array([
        [[x, y]],
        [[x + w, y]],
        [[x + w, y + h]],
        [[x, y + h]],
    ], dtype=np.int32)


def _make_mask(
    width: int = 640,
    height: int = 480,
    regions: list | None = None,
) -> np.ndarray:
    """Create a binary damage mask with filled rectangles."""
    mask = np.zeros((height, width), dtype=np.uint8)
    if regions:
        for x, y, w, h in regions:
            x2 = min(x + w, width)
            y2 = min(y + h, height)
            mask[y:y2, x:x2] = 255
    return mask


# ── Database schema ────────────────────────────────────────────────────────────

def _init_test_db(conn: sqlite3.Connection) -> None:
    """Create all tables on a given connection."""
    ddl = [
        """CREATE TABLE IF NOT EXISTS properties (
            property_id      TEXT PRIMARY KEY,
            property_type    TEXT NOT NULL,
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
        );""",
        """CREATE TABLE IF NOT EXISTS inspections (
            inspection_id    TEXT PRIMARY KEY,
            property_id      TEXT NOT NULL REFERENCES properties(property_id)
                                 ON DELETE CASCADE,
            inspection_date  TEXT NOT NULL DEFAULT (date('now', 'localtime')),
            inspector_name   TEXT DEFAULT '',
            weather_condition TEXT DEFAULT '',
            notes            TEXT DEFAULT '',
            status           TEXT NOT NULL DEFAULT 'processing'
                                 CHECK (status IN ('processing', 'completed', 'failed')),
            total_images     INTEGER DEFAULT 0,
            processing_time_sec REAL DEFAULT 0.0,
            created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );""",
        """CREATE TABLE IF NOT EXISTS inspection_images (
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
            damage_types     TEXT DEFAULT '[]',
            rank_order       INTEGER DEFAULT 0,
            created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );""",
        """CREATE TABLE IF NOT EXISTS reports (
            report_id        TEXT PRIMARY KEY,
            inspection_id    TEXT NOT NULL UNIQUE REFERENCES inspections(inspection_id)
                                 ON DELETE CASCADE,
            overall_damage_pct      REAL DEFAULT 0.0,
            overall_confidence      REAL DEFAULT 0.0,
            overall_severity        TEXT DEFAULT '',
            overall_health_score    INTEGER DEFAULT 100,
            overall_estimated_cost_min INTEGER DEFAULT 0,
            overall_estimated_cost_max INTEGER DEFAULT 0,
            total_repair_area_px    INTEGER DEFAULT 0,
            avg_crack_width_px      REAL DEFAULT 0.0,
            findings_json       TEXT DEFAULT '[]',
            image_rankings_json TEXT DEFAULT '[]',
            executive_summary   TEXT DEFAULT '',
            property_summary    TEXT DEFAULT '',
            inspection_conclusion TEXT DEFAULT '',
            timeline_json       TEXT DEFAULT '[]',
            maintenance_tips_json TEXT DEFAULT '[]',
            health_report_json  TEXT DEFAULT '{}',
            comparison_report_json TEXT DEFAULT '{}',
            raw_reports_json    TEXT DEFAULT '[]',
            processing_time_sec REAL DEFAULT 0.0,
            ai_model_version    TEXT DEFAULT 'opencv-1.0',
            created_at          TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );""",
        """CREATE TABLE IF NOT EXISTS schema_migrations (
            version   INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );""",
    ]
    for stmt in ddl:
        conn.execute(stmt)
    conn.commit()


# ── Pytest fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root directory."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def synthetic_image() -> np.ndarray:
    """A 640x480 synthetic BGR image with one simulated damage region."""
    damage = [(100, 100, 120, 80, (60, 60, 200))]
    return _make_synthetic_image(640, 480, damage_regions=damage)


@pytest.fixture(scope="session")
def synthetic_image_rgb(synthetic_image) -> np.ndarray:
    """Same image in RGB order."""
    return cv2.cvtColor(synthetic_image, cv2.COLOR_BGR2RGB)


@pytest.fixture(scope="session")
def synthetic_mask() -> np.ndarray:
    """A 640x480 binary mask with one damage region."""
    return _make_mask(640, 480, regions=[(100, 100, 120, 80)])


@pytest.fixture(scope="session")
def synthetic_contours() -> list:
    """Two simple rectangular contours."""
    return [
        _make_contour(100, 100, 120, 80),
        _make_contour(350, 200, 80, 60),
    ]


@pytest.fixture(scope="session")
def synthetic_bounding_boxes() -> list:
    """Two bounding boxes matching the contours."""
    return [(100, 100, 120, 80), (350, 200, 80, 60)]


@pytest.fixture(scope="session")
def pil_image(synthetic_image_rgb) -> Image.Image:
    """Convert the synthetic image to a PIL Image."""
    return Image.fromarray(synthetic_image_rgb)


@pytest.fixture(scope="session")
def jpeg_bytes(pil_image) -> bytes:
    """Compress the PIL image to JPEG bytes."""
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@pytest.fixture
def db_conn():
    """Yield a fresh in-memory SQLite connection with full schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _init_test_db(conn)
    yield conn
    conn.close()
