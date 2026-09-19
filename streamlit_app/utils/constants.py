"""InspectAI constants, theme colors, and static data."""

# ── Color Palette ────────────────────────────────────────────────────────────
PRIMARY = "#4F46E5"  # Indigo
ACCENT = "#06B6D4"  # Cyan
SUCCESS = "#10B981"  # Green
WARNING = "#F59E0B"  # Amber
DANGER = "#EF4444"  # Red

BG_DARK = "#0F172A"  # Dark background
BG_CARD = "#1E293B"  # Card background
BG_CARD_HOVER = "#263348"  # Card hover
BG_SIDEBAR = "#0B1120"  # Sidebar background
BG_INPUT = "#1E293B"  # Input field background

TEXT_PRIMARY = "#F1F5F9"  # Primary text
TEXT_SECONDARY = "#94A3B8"  # Secondary text
TEXT_MUTED = "#64748B"  # Muted text
BORDER_COLOR = "#334155"  # Border color

# ── Severity Colors ──────────────────────────────────────────────────────────
SEVERITY_COLORS = {
    "Critical": DANGER,
    "High": "#F97316",
    "Medium": WARNING,
    "Low": SUCCESS,
    "Very High": "#DC2626",  # Added for missing severity level
}

SEVERITY_BG = {
    "Critical": "rgba(239, 68, 68, 0.15)",
    "High": "rgba(249, 115, 22, 0.15)",
    "Medium": "rgba(245, 158, 11, 0.15)",
    "Low": "rgba(16, 185, 129, 0.15)",
    "Very High": "rgba(220, 38, 38, 0.15)",  # Added for missing severity level
}

# ── Grade Colors & Thresholds ───────────────────────────────────────────────
GRADE_COLORS = {
    "A+": "#10B981",
    "A": "#34D399",
    "B+": "#6EE7B7",
    "B": "#FBBF24",
    "C": "#F97316",
    "D": "#EF4444",
}

GRADE_BG = {
    "A+": "rgba(16, 185, 129, 0.15)",
    "A": "rgba(52, 211, 153, 0.15)",
    "B+": "rgba(110, 231, 183, 0.15)",
    "B": "rgba(251, 191, 36, 0.15)",
    "C": "rgba(249, 115, 22, 0.15)",
    "D": "rgba(239, 68, 68, 0.15)",
}

GRADE_THRESHOLDS = {
    "A+": 90,
    "A": 80,
    "B+": 70,
    "B": 60,
    "C": 50,
}

GRADE_RANGES = {
    "A+": (90, 101),
    "A": (80, 90),
    "B+": (70, 80),
    "B": (60, 70),
    "C": (50, 60),
    "D": (0, 50),
}

# ── Severity Metadata ──────────────────────────────────────────────────────
SEVERITY_LABELS = ("Critical", "High", "Medium", "Low")
SEVERITY_RANKS = {
    "Critical": 0,
    "High": 1,
    "Medium": 2,
    "Low": 3,
    "N/A": 4,
    "": 5,
}
SEVERITY_WEIGHTS = {
    "Critical": 1.0,
    "High": 0.75,
    "Medium": 0.5,
    "Low": 0.25,
    "N/A": 0.0,
    "": 0.0,
}

# ── Risk Colors ─────────────────────────────────────────────────────────────
RISK_COLORS = {
    "Critical": "#EF4444",
    "High": "#F97316",
    "Medium": "#F59E0B",
    "Low": "#10B981",
}

# ── Image Validation Limits ─────────────────────────────────────────────────
MIN_IMAGE_WIDTH = 200
MIN_IMAGE_HEIGHT = 200
MAX_FILE_SIZE_MB = 15.0

# ── OpenCV Defaults ────────────────────────────────────────────────────────
DEFAULT_MIN_CONTOUR_AREA = 100
DEFAULT_CANNY_LOW = 50
DEFAULT_CANNY_HIGH = 150
DEFAULT_BLUR_KERNEL = (5, 5)
DEFAULT_RESIZE_MAX = 1024

# ── Application Defaults ────────────────────────────────────────────────────
NA_SENTINEL = "N/A"
DEFAULT_HEALTH_SCORE = 100
DEFAULT_CONFIDENCE = 0
DEFAULT_SCHEMA_VERSION = 1
MIN_CONFIDENCE_THRESHOLD = 30
MIN_HEALTH_SCORE_THRESHOLD = 30

# ── Property Types ────────────────────────────────────────────────────────────
PROPERTY_TYPES = [
    "House",
    "Apartment",
    "Office",
    "Warehouse",
    "Factory",
]

# ── Navigation Configuration ──────────────────────────────────────────────────
NAV_ITEMS = [
    ("🏠", "Dashboard",  "dashboard"),
    ("📊", "Analytics",  "analytics"),
    ("➕", "New Inspection", "new_inspection"),
    ("📋", "History",    "history"),
    ("📑", "Reports",    "reports"),
    ("⚙️", "Settings",   "settings"),
    ("ℹ️", "About",      "about"),
]

# ── Inspection Wizard Steps ───────────────────────────────────────────────────
WIZARD_STEPS = [
    {"key": "details", "label": "Property Details", "icon": "📋"},
    {"key": "upload", "label": "Upload Images", "icon": "📤"},
    {"key": "review", "label": "Review", "icon": "👁️"},
    {"key": "processing", "label": "Processing", "icon": "⚙️"},
    {"key": "results", "label": "Results", "icon": "📊"},
]

# ── Processing Stages ─────────────────────────────────────────────────────────
PROCESSING_STAGES = [
    "Preparing inspection...",
    "Validating images...",
    "Analyzing property...",
    "Generating findings...",
    "Finalizing report...",
]

# ── Dummy Inspection Results (used as fallback when no AI is connected) ───────
DUMMY_RESULTS = {
    "health_score": 87,
    "issues_found": 2,
    "severity": "Medium",
    "estimated_cost_min": 2000,
    "estimated_cost_max": 5000,
    "status": "Completed",
    "inspection_id": "INS-2026-0043",
    "findings": [
        {
            "title": "Minor Wall Crack",
            "severity": "Medium",
            "confidence": 87,
            "description": "Hairline crack (approx. 0.5mm) on the interior wall near the window frame. Non-structural. Appears to be from thermal expansion.",
            "location": "Living room, north wall",
            "repair_steps": [
                "Clean the crack area thoroughly",
                "Apply flexible acrylic caulk",
                "Sand smooth once dry",
                "Repaint to match existing finish",
            ],
            "cost_min": 1000,
            "cost_max": 3000,
        },
        {
            "title": "Paint Peeling",
            "severity": "Low",
            "confidence": 91,
            "description": "Small patches of paint peeling (approx. 10x15cm) on the exterior wall. Likely due to moisture and UV exposure over time.",
            "location": "Exterior, east-facing wall",
            "repair_steps": [
                "Scrape off loose paint",
                "Sand the surface smooth",
                "Apply primer before repainting",
                "Repaint with weather-resistant paint",
            ],
            "cost_min": 1000,
            "cost_max": 2000,
        },
    ],
}

# ── Stat Cards Configuration ──────────────────────────────────────────────────
STAT_CARDS = [
    {"label": "Total Inspections", "value": "128", "icon": "📋", "color": PRIMARY, "trend": "+12%", "trend_up": True},
    {"label": "Properties", "value": "45", "icon": "🏠", "color": ACCENT, "trend": "+3", "trend_up": True},
    {"label": "Critical Issues", "value": "8", "icon": "⚠️", "color": DANGER, "trend": "-2", "trend_up": False},
    {"label": "Reports Generated", "value": "96", "icon": "📑", "color": SUCCESS, "trend": "+18%", "trend_up": True},
]

# ── Quick Actions ────────────────────────────────────────────────────────────
QUICK_ACTIONS = [
    {"label": "Start New Inspection", "icon": "➕", "page": "new_inspection", "color": PRIMARY, "description": "Upload property images for AI analysis"},
    {"label": "View History", "icon": "📋", "page": "history", "color": ACCENT, "description": "Browse past inspection reports"},
    {"label": "Reports", "icon": "📑", "page": "reports", "color": SUCCESS, "description": "Generate and export inspection reports"},
    {"label": "Settings", "icon": "⚙️", "page": "settings", "color": WARNING, "description": "Manage your preferences and account"},
]

# ── Recent Inspections (Dummy Data for History Page) ──────────────────────────
RECENT_INSPECTIONS = [
    {
        "id": "INS-2026-0042",
        "address": "42 Maple Street, Apt 3B",
        "property_type": "Apartment",
        "date": "2026-07-14",
        "damages_found": 5,
        "critical_count": 1,
        "high_count": 1,
        "medium_count": 2,
        "low_count": 1,
        "status": "Completed",
        "image_count": 3,
        "health_score": 68,
    },
    {
        "id": "INS-2026-0041",
        "address": "18 Oak Avenue, Villa 7",
        "property_type": "Villa",
        "date": "2026-07-12",
        "damages_found": 3,
        "critical_count": 0,
        "high_count": 2,
        "medium_count": 1,
        "low_count": 0,
        "status": "Completed",
        "image_count": 5,
        "health_score": 82,
    },
    {
        "id": "INS-2026-0040",
        "address": "120 Pine Road, Unit 12",
        "property_type": "Commercial",
        "date": "2026-07-10",
        "damages_found": 7,
        "critical_count": 2,
        "high_count": 2,
        "medium_count": 2,
        "low_count": 1,
        "status": "Review",
        "image_count": 8,
        "health_score": 45,
    },
    {
        "id": "INS-2026-0039",
        "address": "5 Cedar Lane, House 3",
        "property_type": "House",
        "date": "2026-07-08",
        "damages_found": 2,
        "critical_count": 0,
        "high_count": 0,
        "medium_count": 1,
        "low_count": 1,
        "status": "Completed",
        "image_count": 4,
        "health_score": 91,
    },
    {
        "id": "INS-2026-0038",
        "address": "77 Birch Street, Office 5B",
        "property_type": "Commercial",
        "date": "2026-07-05",
        "damages_found": 4,
        "critical_count": 1,
        "high_count": 1,
        "medium_count": 1,
        "low_count": 1,
        "status": "Completed",
        "image_count": 6,
        "health_score": 58,
    },
]
