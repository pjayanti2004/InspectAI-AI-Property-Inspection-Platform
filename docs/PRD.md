# InspectAI — Product Requirement Document (PRD)

**Version:** 1.0  
**Date:** July 2026  
**Author:** Product / Engineering Design  
**Tagline:** *Inspect Smarter. Repair Faster.*

---

## Table of Contents

1. [Product Vision](#1-product-vision)
2. [Problem Statement](#2-problem-statement)
3. [Target Users](#3-target-users)
4. [User Personas](#4-user-personas)
5. [User Journey](#5-user-journey)
6. [Core Features](#6-core-features)
7. [Future Features](#7-future-features)
8. [Functional Requirements](#8-functional-requirements)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Screen-by-Screen Breakdown](#10-screen-by-screen-breakdown)
11. [Navigation Flow](#11-navigation-flow)
12. [Folder Structure](#12-folder-structure)
13. [Python Module Structure](#13-python-module-structure)
14. [Recommended Coding Architecture](#14-recommended-coding-architecture)
15. [Database Requirement (Future)](#15-database-requirement-future)
16. [AI Workflow](#16-ai-workflow)
17. [Image Processing Workflow](#17-image-processing-workflow)
18. [Report Generation Workflow](#18-report-generation-workflow)
19. [Development Roadmap](#19-development-roadmap)
20. [GitHub Milestone Roadmap](#20-github-milestone-roadmap)
21. [MVP Features](#21-mvp-features)
22. [Version 2 Features](#22-version-2-features)
23. [Version 3 Features](#23-version-3-features)
24. [Interview Value of Each Feature](#24-interview-value-of-each-feature)
25. [Resume Value of the Project](#25-resume-value-of-the-project)
26. [What Should NOT Be Added](#26-what-should-not-be-added)

---

## 1. Product Vision

InspectAI is an **AI-powered property inspection platform** that transforms how buildings are inspected. A user uploads photographs of a property, and InspectAI automatically:

- Detects and localizes damage (cracks, water damage, mold, structural issues, etc.)
- Measures the extent of each damage region in pixels and percentages
- Assesses severity and generates a health score (0–100)
- Produces professional, detailed repair plans with materials, costs, timelines, and safety requirements
- Generates a downloadable inspection report with findings, recommendations, and checklists
- Maintains inspection history so users can compare current condition against past inspections

The vision is to make professional-grade property inspection accessible to everyone — from a homeowner checking their walls to a civil engineer documenting a building's structural health.

---

## 2. Problem Statement

### The Problem

Property inspection is currently:

- **Expensive:** Hiring a professional inspector costs INR 2,000–10,000+ per visit.
- **Subjective:** Two inspectors may report different severity levels for the same damage.
- **Time-consuming:** A full inspection can take 2–4 hours, plus report writing time.
- **Inconsistent:** No standardized health scoring or measurement methodology.
- **Unmaintainable:** Historical inspection data is scattered across PDFs and emails, making trend tracking impossible.

### Why This Matters

- Homeowners discover damage too late, leading to exponentially higher repair costs.
- Property inspectors spend more time writing reports than analyzing.
- Civil engineers and builders lack quick, repeatable assessment tools for progress tracking.
- Real-estate companies need objective, data-backed documentation for property valuations and handovers.

### How InspectAI Solves This

InspectAI provides instant, objective, measurable damage analysis with professional reporting — reducing inspection time from hours to minutes and cost from thousands to near-zero.

---

## 3. Target Users

| User Segment | Description | Primary Need |
|---|---|---|
| **Homeowners** | Individuals who own or rent residential property | Quick, affordable damage checks without hiring professionals |
| **Property Inspectors** | Certified inspectors performing routine assessments | Faster report generation, objective measurements, professional output |
| **Civil Engineers** | Engineers assessing structural integrity of buildings | Precise damage quantification, historical tracking, data export |
| **Builders / Contractors** | Construction professionals monitoring work quality | Progress documentation, defect tracking, repair planning |
| **Real Estate Companies** | Agencies managing property portfolios | Bulk inspection support, standardized reporting, comparison views |

---

## 4. User Personas

### Persona 1: Ravi — The Homeowner

- **Age:** 32
- **Occupation:** Software engineer
- **Tech comfort:** High
- **Scenario:** Noticed water stains on his apartment ceiling. He takes photos with his phone and uploads them to InspectAI. Within minutes he gets a severity assessment, estimated repair cost, and a recommendation for which professional to call. He saves the report for his insurance claim.

### Persona 2: Priya — The Property Inspector

- **Age:** 38
- **Occupation:** Certified home inspector, runs her own business
- **Tech comfort:** Medium
- **Scenario:** Priya visits a 20-year-old apartment complex. She photographs every unit and uploads all images to InspectAI. The platform auto-detects cracks, water damage, and mold, generates health scores per unit, and produces a professional PDF-ready report. She reviews and adjusts, then delivers the report to the property management company in 30 minutes instead of 3 days.

### Persona 3: Vikram — The Civil Engineer

- **Age:** 45
- **Occupation:** Structural engineer at a construction firm
- **Tech comfort:** Medium
- **Scenario:** Vikram's firm is building a 12-story residential tower. He inspects the structure at each floor using InspectAI to detect cracks and measure their growth over time. He compares current inspection reports with previous ones to track structural health trends and ensure compliance with safety standards.

---

## 5. User Journey

### Homeowner Journey (Simplest Path)

```
1. Lands on InspectAI home page
2. Enters name and property details (address, type, size)
3. Uploads 1–10 images of the property
4. Clicks "Analyze"
5. Watches AI processing progress (real-time status updates)
6. Views results: damage heatmaps, severity labels, health score, findings
7. Reads repair plan with materials, costs, and timeline
8. Views detailed inspection report
9. Exports/downloads the report
10. Returns later to re-inspect and compare with history
```

### Inspector Journey (Professional Path)

```
1. Sets inspector profile name
2. Creates a new inspection session with property details
3. Uploads multiple images (batch mode)
4. AI processes all images, detects damage, generates measurements
5. Reviews findings — filters by severity, views annotated heatmaps
6. Edits/adds notes to findings
7. Generates comprehensive inspection report with all sections
8. Reviews health score, risk assessment, repair timeline
9. Compares with previous inspection (if available)
10. Exports report (PDF or print)
```

### Engineer Journey (Comparison-Focused)

```
1. Logs in (future — currently session-based)
2. Navigates to inspection history
3. Selects property to inspect again
4. Uploads new images
5. Reviews AI analysis
6. Clicks "Compare with Previous"
7. Views side-by-side comparison: score delta, grade change, new vs. resolved damage, cost trends
8. Sees improvement recommendations
9. Exports comparative report
```

---

## 6. Core Features

### Feature 1: Image Upload & Validation

Upload property images through a drag-and-drop interface. System validates format, size, resolution, and readability before processing.

### Feature 2: AI-Powered Damage Detection

Uses Gemini Vision API to analyze uploaded images and identify damage types with confidence scores. Supports detection of: cracks, water damage, mold, structural damage, paint peeling, moisture stains, roof damage, electrical issues, plumbing problems, termite/pest damage, and more.

### Feature 3: Computer Vision Measurements

OpenCV-based pipeline processes each image to: threshold damage regions, find contours, measure area percentages, calculate bounding boxes, determine shape complexity, estimate crack dimensions, and locate damage position (wall quadrant).

### Feature 4: Severity Classification & Health Scoring

Each finding is classified as Critical / High / Medium / Low. A composite health score (0–100) is computed from damage percentage, severity distribution, and contour count. Risk level is assigned (Low / Medium / High / Critical).

### Feature 5: Interactive Results Dashboard

Users view annotated images with heatmap overlays, damage bounding boxes, severity-coded findings, measurement statistics, and confidence scores in a unified dashboard.

### Feature 6: Professional Repair Planning

Generates detailed repair plans including: prioritized task lists, materials with quantities and costs, labour estimates by professional type, safety requirements, step-by-step repair sequences, tools needed, and maintenance schedules (1-month, 3-month, 6-month, 12-month).

### Feature 7: Inspection Report

A complete, professional inspection report rendered in the browser with sections: executive summary, health score, risk level, findings cards, repair timeline, property health dashboard, recommendations, and inspection checklist.

### Feature 8: Inspection History

All inspections are tracked with timestamps, property names, health scores, and findings counts. Users can review past inspections.

### Feature 9: Inspection Comparison

Compare current inspection against a previous one. Shows: health score delta, grade change, risk trend, improvement score, cost changes, new vs. resolved damage, and days between inspections.

### Feature 10: Session State Management

Multi-page navigation using Streamlit's session state. Users can move between home, results, report, and history pages without losing data.

---

## 7. Future Features

| Feature | Description | Priority |
|---|---|---|
| **PDF Report Export** | Generate and download professional PDF reports using reportlab or weasyprint | High |
| **Supabase Authentication** | User login/signup, persistent storage, multi-device access | High |
| **Batch Property Inspection** | Inspect multiple properties in one session with comparison across properties | Medium |
| **Historical Trend Charts** | Time-series graphs showing property health over months/years | Medium |
| **Multi-language Support** | Support for regional languages (Hindi, Tamil, etc.) | Low |
| **Email Report Delivery** | Send reports directly to clients via email | Medium |
| **Mobile-Responsive Design** | Optimized layout for mobile devices | Medium |
| **API Endpoints** | REST API for third-party integrations | Low |
| **IoT Sensor Integration** | Connect with moisture meters, thermal cameras for enhanced data | Low |
| **Collaborative Inspections** | Multiple inspectors working on the same property, shared annotations | Low |

---

## 8. Functional Requirements

### FR-1: Property Registration

- User enters property name, type (Residential / Commercial / Industrial), address, and construction year
- Property data is stored in session state for the duration of the session
- Pre-filled defaults for quick inspection

### FR-2: Image Upload

- Accept multiple images simultaneously (drag-and-drop and file picker)
- Supported formats: JPEG, PNG, WEBP, BMP
- Maximum file size: 15 MB per image
- Minimum resolution: 200×200 pixels
- Real-time validation with clear error messages
- Image preview before upload

### FR-3: AI Analysis Pipeline

- Process images through OpenCV preprocessing → Gemini Vision API analysis → measurement engine
- Return structured results for each image: damage type, severity, confidence, measurements, repair suggestions
- Support batch processing with progress indication
- Handle API failures gracefully with retry logic

### FR-4: Results Display

- Display each image with: original, annotated overlay, heatmap, and findings
- Summary statistics: total findings, avg confidence, processing time
- Filterable/sortable findings table
- Severity color coding throughout the UI

### FR-5: Health Score Calculation

- Compute health score (0–100) based on damage extent and severity
- Display risk level with color-coded indicators
- Show score breakdown components

### FR-6: Repair Plan Generation

- Generate prioritized repair tasks from findings
- Include materials, costs, timelines, safety requirements
- Categorize into repair phases (Immediate / Preparation / Repair / Finishing / Inspection)
- Provide before/during/after checklists
- Generate maintenance schedule

### FR-7: Report Generation

- Render a complete professional inspection report
- Sections: Executive Summary, Health Score, Risk Level, Findings, Timeline, Recommendations, Checklist
- Support navigation back to dashboard
- Clear, print-friendly layout

### FR-8: Inspection History

- Track all inspection sessions with metadata (date, property, score, findings count)
- Allow users to navigate to history from any page
- Provide inspection details on demand

### FR-9: Inspection Comparison

- Allow selection of a previous inspection for comparison
- Compute and display: score delta, grade change, risk trend, improvement score, cost changes, damage changes
- Highlight improvements or deteriorations

### FR-10: Navigation

- Multi-page flow: Home → Processing → Results → Report → History
- Back navigation from any page
- Session state preservation across pages

---

## 9. Non-Functional Requirements

### NFR-1: Performance

- Single image analysis: < 30 seconds
- Batch of 10 images: < 5 minutes
- Report rendering: < 2 seconds
- Dashboard load: < 1 second

### NFR-2: Usability

- No training required — intuitive enough for non-technical users
- Clear error messages for all failure scenarios
- Loading indicators during AI processing
- Responsive layout that works on common screen sizes (1024px+)

### NFR-3: Reliability

- Handle Gemini API downtime gracefully with meaningful error messages
- Validate all inputs before processing
- Never crash on empty or invalid data
- Retry logic for transient API failures (3 retries with exponential backoff)

### NFR-4: Code Quality

- Type hints on all functions
- Dataclasses for data structures
- Docstrings on all public functions
- Separation of concerns (AI logic separate from UI rendering)
- No side effects in core logic modules

### NFR-5: Maintainability

- Modular architecture — each engine is independently testable
- Constants centralized in a single file
- Session state managed through dedicated utility functions
- Clear naming conventions (snake_case for Python, PascalCase for dataclasses)

### NFR-6: Extensibility

- Easy to add new damage types to the repair knowledge base
- Easy to add new analysis metrics to the measurement engine
- Easy to add new report sections
- Easy to swap or upgrade the AI backend (Gemini → local model → another API)

---

## 10. Screen-by-Screen Breakdown

### Screen 1: Home Page (Landing)

**File:** `streamlit_app/pages/01_Home.py`  
**Purpose:** First screen. Entry point for new inspections.

**Components:**

- **Hero section:** App name, tagline "Inspect Smarter. Repair Faster.", brief description
- **Inspector name input:** Text field to set the inspector's name (stored in session state)
- **Property form:**
  - Property Name (text input, default: "My Property")
  - Property Type (select: Residential, Commercial, Industrial, Other)
  - Address (text input)
  - Construction Year (number input)
- **Quick-start tips:** 3–4 bullet points explaining how to use the app
- **Image upload zone:** Drag-and-drop multi-file uploader
- **Start Inspection button:** Triggers the analysis pipeline
- **Navigation links:** View History, About

**User actions on this screen:**
- Fill property details
- Upload images
- Click "Start Inspection"
- Navigate to History

---

### Screen 2: Processing Screen

**File:** `streamlit_app/pages/02_Processing.py`  
**Purpose:** Show real-time progress during AI analysis.

**Components:**

- **Status header:** "Analyzing your property..."
- **Progress bar:** Overall batch progress
- **Image cards:** For each image being processed, show thumbnail, filename, and current status (Validating → Processing → Analyzing → Complete / Failed)
- **Status messages:** Human-readable text describing current step
- **Error display:** If any image fails, show error with retry option
- **Auto-navigation:** When all images are processed, redirect to Results

**User actions on this screen:**
- Wait for processing
- View intermediate results as they complete
- Retry failed images

---

### Screen 3: Results Dashboard

**File:** `streamlit_app/pages/03_Results.py`  
**Purpose:** Display AI analysis results with interactive visualizations.

**Components:**

- **Top bar:** Inspection ID, property name, inspector name, back button
- **Summary cards row:**
  - Total Findings count
  - Average Confidence %
  - Processing Time
  - Health Score (large, color-coded)
- **Risk Assessment card:** Risk level (Low/Medium/High/Critical) with color, risk description
- **Findings section:**
  - Filter tabs: All / Critical / High / Medium / Low
  - Cards for each finding with: thumbnail, damage type, severity badge, confidence bar, damage %, contour count
  - Expandable cards showing: possible causes, repair steps, recommended professional, estimated cost range, urgency
- **Annotated images gallery:** Grid of images with overlay heatmaps, bounding boxes, labels
- **Action buttons:** View Full Report, Start New Inspection, Go to History

**User actions on this screen:**
- Filter findings by severity
- Expand findings for details
- View annotated images
- Navigate to full report

---

### Screen 4: Inspection Report

**File:** `streamlit_app/pages/04_Report.py`  
**Purpose:** Display the complete professional inspection report.

**Components:**

- **Navigation:** Back to Dashboard button
- **Report header:** "Inspection Report" title, date, inspection ID
- **Section 1 — Executive Summary:**
  - Property details, inspector name, inspection date
  - Key stats: findings count, health score, risk level, estimated cost range
  - AI confidence assessment text
- **Section 2 — Health Score & Risk Level:**
  - Large health score circle/badge
  - Risk level with color coding
  - Score interpretation text
- **Section 3 — Stat Cards:**
  - Total Findings
  - Avg Confidence
  - Est. Repair Cost (range)
  - Processing Time
- **Section 4 — Findings Cards:**
  - Detailed cards for each finding with all measurements
  - Severity-coded left borders
  - Image thumbnails with overlay
  - Measurement statistics (area %, contour count, shape complexity)
- **Section 5 — Repair Timeline:**
  - Visual timeline showing repair phases
  - Duration estimates per phase
  - Phase descriptions
- **Section 6 — Property Health Dashboard (optional):**
  - Strengths, Weaknesses, Priority Actions
  - Health summary narrative
- **Section 7 — Inspection Comparison (optional):**
  - Only shown when comparing with a previous inspection
  - Score delta, grade change, risk trend, improvement score
  - Cost change, damage changes, time between inspections
- **Section 8 — Recommendations:**
  - Immediate Actions (red)
  - Repair Priority (amber)
  - Professional Help needed
  - Maintenance Tips (green)
- **Section 9 — Inspection Checklist:**
  - Progress bar showing completion %
  - Grid of checklist categories with status icons

**User actions on this screen:**
- Scroll through report sections
- Navigate back to dashboard
- (Future) Print or export as PDF

---

### Screen 5: Inspection History

**File:** `streamlit_app/pages/05_History.py`  
**Purpose:** Show all past inspection sessions with summary data.

**Components:**

- **Header:** "Inspection History" title, total inspections count
- **History cards grid:**
  - Each card shows: inspection ID, date, property name, property type, health score, risk level, findings count, estimated repair cost
  - Color-coded risk badges
  - Click to view details
- **Empty state:** When no inspections exist, show friendly message with link to start first inspection
- **Actions per card:**
  - "View Report" — navigates to report view
  - "Re-inspect" — pre-fills property data and starts new inspection session
  - "Delete" — removes from history (with confirmation)

**User actions on this screen:**
- Browse past inspections
- Click to view a previous report
- Start a new inspection from history
- Delete old inspections

---

### Screen 6: Property Health Dashboard (Integrated into Report)

**Components:**

- **Strengths section:** Green-highlighted positive observations
- **Weaknesses section:** Red-highlighted problem areas
- **Priority Actions section:** Amber-highlighted recommended actions
- **Health Summary:** AI-generated narrative summary of property condition

---

### Screen 7: Inspection Comparison (Modal/Section within Report)

**Components:**

- **Previous inspection selector:** Dropdown to choose which past inspection to compare against
- **Comparison metrics grid:**
  - Health Score Change (with arrow and delta)
  - Grade Change (e.g., B → C)
  - Risk Trend (Improving / Stable / Declining)
  - Improvement Score (%)
  - Repair Cost Change (INR delta)
  - Damage Changes (+new / -resolved)
  - Days Between Inspections
- **Interpretation text:** AI-generated summary of what changed and what it means

---

## 11. Navigation Flow

```
                        ┌──────────────────┐
                        │   HOME PAGE      │
                        │  (01_Home.py)    │
                        └────────┬─────────┘
                                 │
                    Upload images + Fill form
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  PROCESSING      │
                        │ (02_Processing.py)│
                        └────────┬─────────┘
                                 │
                         All images processed
                                 │
                                 ▼
              ┌──────────────────────────────────┐
              │       RESULTS DASHBOARD           │
              │     (03_Results.py)               │
              │                                   │
              │  ┌──────────┐  ┌──────────────┐  │
              │  │  View    │  │   History    │  │
              │  │  Report  │  │   (05_Hist)  │  │
              │  └──────────┘  └──────────────┘  │
              └──────────────────────────────────┘
                         │              │
                         ▼              ▼
              ┌──────────────────┐  ┌───────────────┐
              │  INSPECTION      │  │  COMPARISON   │
              │  REPORT          │  │  (integrated  │
              │  (04_Report.py)  │  │   into report)│
              └──────────────────┘  └───────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  BACK TO         │
              │  DASHBOARD       │
              │  (loop back)     │
              └──────────────────┘

              ┌──────────────────┐
              │  INSPECTION      │
              │  HISTORY         │
              │  (05_History.py) │
              │                   │
              │  → View Report   │
              │  → Re-inspect    │
              │  → Delete        │
              └──────────────────┘
```

### Session State Flow

The application uses Streamlit's `st.session_state` to maintain state across page navigation:

```
session_state:
  ├── page              → "home" | "processing" | "results" | "report" | "history"
  ├── inspector_name    → str
  ├── property_data     → dict (name, type, address, year)
  ├── uploaded_images   → list[dict] (file_name, bytes, preview)
  ├── inspection_reports → list[InspectionReport]
  ├── fused_report      → FusedInspection (aggregated across images)
  ├── measurement_reports → list[MeasurementReport]
  ├── repair_plan       → RepairPlan
  ├── history           → list[InspectionSession]
  ├── current_inspection_id → str
  └── previous_page     → str (for back navigation)
```

Navigation is handled via `set_page()` / `go_back()` utility functions in `session_manager.py` that update `session_state.page` and trigger `st.rerun()`.

---

## 12. Folder Structure

```
InspectAI/
│
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore rules
│
├── streamlit_app/
│   ├── __init__.py
│   │
│   ├── app.py                   # Main entry point (page config, routing)
│   │
│   ├── pages/                   # Streamlit pages (navigation screens)
│   │   ├── __init__.py
│   │   ├── 01_Home.py          # Landing page + image upload
│   │   ├── 02_Processing.py    # AI processing progress screen
│   │   ├── 03_Results.py       # Results dashboard
│   │   ├── 04_Report.py        # Full inspection report
│   │   └── 05_History.py       # Inspection history
│   │
│   ├── ai/                      # AI & computer vision engines
│   │   ├── __init__.py
│   │   ├── inspection_engine.py       # Gemini Vision API integration
│   │   ├── image_validator.py         # Pre-flight image validation
│   │   ├── measurement_engine.py      # OpenCV measurement & annotation
│   │   ├── repair_planner.py          # Repair plan generation
│   │   ├── risk_engine.py             # Risk assessment & health scoring
│   │   ├── health_engine.py           # Property health analysis
│   │   ├── comparison_engine.py       # Inspection comparison logic
│   │   └── prompt_templates.py        # Gemini prompt templates
│   │
│   ├── components/              # Reusable UI components
│   │   ├── __init__.py
│   │   ├── cards.py            # Finding cards, stat cards, result cards
│   │   ├── heatmap.py          # Damage heatmap overlay rendering
│   │   ├── progress.py         # Progress indicators, loading spinners
│   │   └── forms.py            # Property form, inspector form
│   │
│   ├── report/                  # Report generation engines
│   │   ├── __init__.py
│   │   ├── report_builder.py   # Main report rendering (Streamlit UI)
│   │   ├── summary_engine.py   # Executive summary, findings, timeline
│   │   ├── risk_engine.py      # Risk assessment (shared with AI)
│   │   └── checklist_builder.py # Inspection checklist generation
│   │
│   ├── utils/                   # Shared utilities
│   │   ├── __init__.py
│   │   ├── constants.py        # All constants (colors, thresholds, rates)
│   │   ├── session_manager.py  # Session state navigation helpers
│   │   ├── file_helpers.py     # File I/O, image loading, temp files
│   │   └── cost_helpers.py     # Cost calculation utilities
│   │
│   ├── styles/                  # CSS and theming
│   │   ├── __init__.py
│   │   └── custom.css          # Custom Streamlit theme CSS
│   │
│   ├── uploads/                 # Temporary image storage during session
│   │   └── .gitkeep
│   │
│   └── output/                  # Generated reports and exports
│       └── .gitkeep
│
├── tests/                       # (Future) Unit tests
│   ├── __init__.py
│   ├── test_image_validator.py
│   ├── test_measurement_engine.py
│   └── test_repair_planner.py
│
└── docs/                        # Documentation
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    └── SETUP_GUIDE.md
```

---

## 13. Python Module Structure

### `streamlit_app/app.py`

**Responsibility:** Application entry point and page routing.

```
- Configure Streamlit page settings (title, icon, layout)
- Initialize session state defaults
- Route to appropriate page based on session_state.page
- Define top-level CSS injection
```

### `streamlit_app/pages/*.py`

**Responsibility:** Each file is a Streamlit page. Contains only UI logic for that screen.

```
01_Home.py      → Property form, image upload, start button
02_Processing.py → Progress display, status updates, error handling
03_Results.py   → Results dashboard, findings display, navigation
04_Report.py    → Report rendering entry point (calls report_builder)
05_History.py   → History listing, inspection details
```

### `streamlit_app/ai/inspection_engine.py`

**Responsibility:** Core AI analysis pipeline. Orchestrates the entire inspection process.

```
Key exports:
  InspectionReport (dataclass)     → Per-image AI result
  FusedInspection (dataclass)      → Aggregated multi-image results
  analyze_image()                  → Single image analysis
  run_inspection()                 → Full inspection on one image
  run_batch()                      → Batch analysis on multiple images
  fuse_reports()                   → Merge multiple reports into one
```

### `streamlit_app/ai/image_validator.py`

**Responsibility:** Pre-flight validation of uploaded images.

```
Key exports:
  ValidationResult (dataclass)
  validate_image()                 → Validate any image input
```

### `streamlit_app/ai/measurement_engine.py`

**Responsibility:** Computer vision measurements and annotation generation.

```
Key exports:
  DamageRegion (dataclass)
  MeasurementReport (dataclass)
  measure_damage_regions()         → Analyze contours → measurements
  annotate_damage()                → Generate annotated image, mask, overlay, legend
```

### `streamlit_app/ai/repair_planner.py`

**Responsibility:** Generate repair plans from inspection findings.

```
Key exports:
  RepairMaterial (dataclass)
  RepairTask (dataclass)
  RepairPhase (dataclass)
  RepairPlan (dataclass)
  generate_repair_plan()           → Full repair plan from findings
  repair_plan_to_dict()            → Serialize for session state
```

### `streamlit_app/ai/risk_engine.py`

**Responsibility:** Compute risk assessment and health scores.

```
Key exports:
  RiskAssessment (dataclass)
  assess_risk()                    → Compute health score, risk level, cost estimates
```

### `streamlit_app/ai/health_engine.py`

**Responsibility:** Generate property health narratives and analysis.

```
Key exports:
  PropertyHealthReport (dataclass)
  analyze_property_health()        → Generate health summary, strengths, weaknesses, actions
```

### `streamlit_app/ai/comparison_engine.py`

**Responsibility:** Compare two inspections and generate diff analysis.

```
Key exports:
  ComparisonReport (dataclass)
  compare_inspections()            → Compare current vs. previous inspection
```

### `streamlit_app/report/report_builder.py`

**Responsibility:** Render the complete professional inspection report in Streamlit UI.

```
Key exports:
  render_report()                  → Single entry point for report rendering
  _render_executive_summary()
  _render_health_section()
  _render_findings_section()
  _render_timeline_section()
  _render_recommendations_section()
  _render_checklist_section()
  _render_health_dashboard()
  _render_comparison_section()
```

### `streamlit_app/report/summary_engine.py`

**Responsibility:** Transform AI results into structured data for report rendering.

```
Key exports:
  FindingRecord (dataclass)
  TimelineEntry (dataclass)
  ExecutiveSummary (dataclass)
  build_executive_summary()
  build_findings()
  build_timeline()
  build_recommendations()
  build_checklist()
```

### `streamlit_app/utils/session_manager.py`

**Responsibility:** Manage Streamlit session state and navigation.

```
Key exports:
  init_session_state()             → Initialize all session state defaults
  set_page()                       → Navigate to a page
  go_back()                        → Navigate to previous page
  get_inspection_history()         → Retrieve history from session state
  save_inspection()                → Save current inspection to history
```

### `streamlit_app/utils/constants.py`

**Responsibility:** All application constants in one place.

```
Key exports:
  Colors: TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BG_PRIMARY, BG_SECONDARY, BG_CARD, BORDER_COLOR
  Severity colors: SEVERITY_COLORS (Critical → EF4444, High → F97316, etc.)
  Risk colors: RISK_COLORS
  Thresholds: MIN_CONFIDENCE, HEALTH_SCORE_RANGES
  Labour rates, cost estimates, damage type mappings
```

---

## 14. Recommended Coding Architecture

### Architectural Pattern: **Layered Architecture with Pure Logic Modules**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  (Streamlit Pages + Components)                             │
│  • Pages (01_Home through 05_History)                       │
│  • UI Components (cards, heatmaps, forms)                   │
│  • Report Builder (report_builder.py)                       │
│                                                             │
│  Responsibilities:                                          │
│  - User interaction, input collection                       │
│  - Rendering results, charts, reports                       │
│  - Navigation between screens                               │
│  - NO business logic, NO AI calls, NO file I/O              │
└──────────────────────┬──────────────────────────────────────┘
                       │ calls
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                        │
│  (Orchestration & State Management)                         │
│  • app.py (routing, session init)                           │
│  • session_manager.py (navigation, state)                   │
│  • utils/ (file helpers, cost helpers)                      │
│                                                             │
│  Responsibilities:                                          │
│  - Coordinate between UI and engines                        │
│  - Manage session state                                     │
│  - Handle file I/O (uploads, temp files)                    │
│  - Error handling and user feedback                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ calls
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      AI ENGINE LAYER                         │
│  (Core Business Logic — Pure Python, No Streamlit)          │
│  • inspection_engine.py  (orchestrator)                     │
│  • image_validator.py    (validation)                       │
│  • measurement_engine.py (CV measurements)                  │
│  • repair_planner.py     (repair logic)                     │
│  • risk_engine.py        (scoring)                          │
│  • health_engine.py      (health analysis)                  │
│  • comparison_engine.py  (comparison logic)                 │
│                                                             │
│  Responsibilities:                                          │
│  - All AI/ML logic                                          │
│  - Computer vision processing                               │
│  - Business rule computation                                │
│  - Data transformation                                      │
│  - Return pure dataclass outputs                            │
│  - NO Streamlit, NO UI code                                 │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

**1. Separation of Concerns**

- AI engines have zero Streamlit imports. They can be unit-tested independently.
- UI pages have minimal logic — they call engines and render results.
- Report builder separates rendering (Streamlit) from data preparation (summary_engine).

**2. Pure Functions Where Possible**

- `assess_risk()`: Takes list[InspectionReport], returns RiskAssessment. No side effects.
- `build_findings()`: Takes list[InspectionReport], returns list[FindingRecord]. No side effects.
- `generate_repair_plan()`: Takes list[InspectionReport], returns RepairPlan. No side effects.

**3. Dataclass-First Data Model**

Every data structure is a frozen or mutable dataclass with full type annotations:

```python
@dataclass(frozen=True)
class InspectionReport:
    file_name: str
    damage_type: str
    severity: str
    confidence: int
    damage_percentage: float
    contour_count: int
    # ... more fields
```

This makes data flow explicit, enables IDE autocomplete, and prevents accidental mutation.

**4. Constants Centralization**

All magic numbers, colors, thresholds, rates, and mappings live in `utils/constants.py`. Changing a color or threshold requires editing one file.

**5. Pipeline Pattern for Image Processing**

```
Input Image
    → Validate (image_validator.py)
    → Preprocess (measurement_engine.py: blur, threshold, morphology)
    → AI Analysis (inspection_engine.py: Gemini Vision)
    → Measure (measurement_engine.py: contours, areas, shapes)
    → Fuse (inspection_engine.py: combine all image results)
    → Score (risk_engine.py: health score, risk level)
    → Plan (repair_planner.py: tasks, costs, timeline)
    → Render (report_builder.py: UI output)
```

Each stage is independently testable and replaceable.

**6. Error Resilience**

- Every AI call is wrapped in try/except with meaningful error messages
- Failed images are logged but don't block the batch
- Default/fallback values ensure the app never crashes on missing data
- Validation happens at every boundary (input → AI → output → UI)

---

## 15. Database Requirement (Future)

### Current State: Session-Only Storage

The MVP uses Streamlit's `st.session_state` for all data persistence within a single session. Inspection history is stored in memory and lost when the app restarts. This is sufficient for demo and portfolio purposes.

### Future: Supabase Integration

When moving beyond MVP, integrate Supabase for persistent storage:

**Tables needed:**

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'homeowner',  -- homeowner | inspector | engineer | admin
    created_at TIMESTAMP DEFAULT NOW()
);

-- Properties table
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    address TEXT,
    construction_year INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Inspections table
CREATE TABLE inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID REFERENCES properties(id),
    user_id UUID REFERENCES users(id),
    inspector_name TEXT,
    inspection_date DATE DEFAULT CURRENT_DATE,
    health_score INT,
    risk_level TEXT,
    total_findings INT,
    estimated_cost_min INT,
    estimated_cost_max INT,
    avg_confidence FLOAT,
    processing_time_sec FLOAT,
    report_data JSONB,  -- Full InspectionReport + FusedInspection
    created_at TIMESTAMP DEFAULT NOW()
);

-- Images table
CREATE TABLE inspection_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inspection_id UUID REFERENCES inspections(id),
    file_name TEXT,
    image_data BYTEA,  -- Or store in Supabase Storage with URL reference
    annotation_data JSONB,
    measurements JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Repair Plans table
CREATE TABLE repair_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inspection_id UUID REFERENCES inspections(id),
    plan_data JSONB,  -- Full RepairPlan
    total_material_cost INT,
    total_labour_cost INT,
    total_equipment_cost INT,
    total_repair_cost INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Benefits of Supabase:**

- Persistent storage across sessions
- User authentication
- Multi-device access
- Real-time subscriptions (future: collaborative inspection)
- File storage for images
- Row-level security for multi-tenant data

**Implementation approach:**

- Use Supabase Python client (`supabase` package)
- Replace `session_manager.py` storage functions with Supabase calls
- Keep the same data models — just swap the storage backend
- Use Supabase Storage for images, Postgres for structured data

---

## 16. AI Workflow

### Overview

The AI workflow is the core intelligence of InspectAI. It transforms raw images into structured, actionable inspection data.

### Pipeline Stages

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Upload  │────▶│  Validate    │────▶│  Preprocess  │────▶│  AI Analyze  │
│  Images  │     │  (validator) │     │  (OpenCV)    │     │  (Gemini)    │
└──────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                 │
                                                                 ▼
                                                        ┌──────────────────┐
                                                        │   Parse Response  │
                                                        │  → InspectionReport│
                                                        └────────┬─────────┘
                                                                 │
                                                                 ▼
                                                        ┌──────────────────┐
                                                        │  Measure (CV)    │
                                                        │  → contours,     │
                                                        │  measurements    │
                                                        └────────┬─────────┘
                                                                 │
                                                                 ▼
                                                        ┌──────────────────┐
                                                        │  Fuse Results    │
                                                        │  → FusedInspection│
                                                        └────────┬─────────┘
                                                                 │
                          ┌──────────────────────────────────────┼────────┐
                          ▼                                      ▼        ▼
                   ┌──────────────┐                    ┌──────────┐ ┌──────────┐
                   │ Risk Engine   │                    │  Repair  │ │  Health  │
                   │ → Risk        │                    │  Planner │ │  Engine  │
                   │   Assessment  │                    │ → Repair │ │ → Health │
                   └──────────────┘                    │   Plan   │ │  Report  │
                                                        └──────────┘ └──────────┘
```

### Stage 1: Image Validation (`image_validator.py`)

**Purpose:** Ensure uploaded images are processable before spending AI credits.

**Checks:**
- Format support (JPEG, PNG, WEBP, BMP)
- File size ≤ 15 MB
- Minimum resolution 200×200 pixels
- Image is decodable (not corrupt)
- Color mode is convertible to RGB

**Output:** `ValidationResult` (is_valid, error, code)

### Stage 2: OpenCV Preprocessing (`measurement_engine.py`)

**Purpose:** Prepare the image for contour detection.

**Steps:**
1. Load image as BGR numpy array
2. Convert to grayscale
3. Apply Gaussian blur (reduce noise)
4. Adaptive thresholding (handle varying lighting)
5. Morphological operations (close gaps, remove noise)
6. Generate binary damage mask

**Output:** Binary mask + preprocessed grayscale image

### Stage 3: Gemini Vision API Analysis (`inspection_engine.py`)

**Purpose:** Use AI to understand what damage is present.

**Input to Gemini:**
- The original image (base64 encoded)
- A structured prompt asking for: damage type, severity, confidence, possible causes, repair steps, recommended professional, estimated cost, urgency, prevention tips

**Prompt structure:**
```
You are a professional property inspection AI. Analyze this image and identify any
property damage. Respond in the following JSON format:
{
    "damage_type": "...",
    "severity": "Critical|High|Medium|Low",
    "confidence": 0-100,
    "damage_percentage": 0-100,
    "possible_causes": ["..."],
    "repair_steps": ["..."],
    "recommended_professional": "...",
    "estimated_cost_range": "₹X — ₹Y",
    "urgency": "...",
    "prevention_tips": ["..."]
}
```

**Output:** `InspectionReport` dataclass populated from AI response

### Stage 4: Computer Vision Measurements (`measurement_engine.py`)

**Purpose:** Quantify damage geometrically.

**Steps:**
1. Find contours on the binary mask
2. Filter by minimum area (remove noise)
3. For each contour:
   - Calculate area in pixels and as % of image
   - Compute bounding box (x, y, w, h)
   - Calculate perimeter
   - Compute shape complexity (circularity-based)
   - Estimate crack length and width
   - Determine wall quadrant
   - Calculate damage coverage (% of bbox that is actual damage)
4. Generate annotated image with bounding boxes, labels, and measurements
5. Generate heatmap overlay
6. Generate color legend

**Output:** `MeasurementReport` + annotated images (numpy arrays)

### Stage 5: Result Fusion (`inspection_engine.py` → `fuse_reports()`)

**Purpose:** Combine results from multiple images into a single aggregated view.

**Aggregation:**
- Total findings across all images
- Average confidence
- Total damage percentage
- Combined estimated cost range
- Overall severity distribution
- Combined processing time

**Output:** `FusedInspection` dataclass

### Stage 6: Risk Assessment (`risk_engine.py`)

**Purpose:** Compute property health score and risk level.

**Algorithm:**
```
health_score = 100
  - (total_damage_pct × 2)        # Each % of damage costs 2 points
  - (critical_count × 15)         # Each critical finding costs 15 points
  - (high_count × 10)             # Each high finding costs 10 points
  - (medium_count × 5)            # Each medium finding costs 5 points
  - (low_count × 2)               # Each low finding costs 2 points
  - (contour_complexity_avg × 10) # Complex shapes indicate worse damage
Clamped to [0, 100]

risk_level = "Critical" if score < 20
           = "High"      if score < 40
           = "Medium"    if score < 60
           = "Low"       if score >= 60
```

**Output:** `RiskAssessment` dataclass

### Stage 7: Repair Planning (`repair_planner.py`)

**Purpose:** Generate actionable repair plans from findings.

**Process:**
1. For each finding, look up the damage type in the repair knowledge base
2. Scale costs by severity and damage percentage
3. Organize tasks into phases (Immediate → Preparation → Repair → Finishing → Inspection)
4. Calculate total material, labour, and equipment costs
5. Generate before/during/after checklists
6. Generate maintenance schedule based on worst severity

**Output:** `RepairPlan` dataclass

### Stage 8: Health Analysis (`health_engine.py`)

**Purpose:** Generate human-readable property health narrative.

**Process:**
1. Analyze findings for positive patterns (strengths)
2. Identify concerning patterns (weaknesses)
3. Prioritize actions based on severity
4. Generate narrative summary

**Output:** `PropertyHealthReport` dataclass

---

## 17. Image Processing Workflow

### Detailed OpenCV Pipeline

```
Original Image (BGR, uint8)
        │
        ▼
┌───────────────────────────────────────────────┐
│ Step 1: Grayscale Conversion                  │
│ gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)│
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ Step 2: Gaussian Blur (noise reduction)       │
│ blurred = cv2.GaussianBlur(gray, (5, 5), 0)   │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ Step 3: Adaptive Thresholding                 │
│ binary = cv2.adaptiveThreshold(               │
│     blurred, 255,                              │
│     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,            │
│     cv2.THRESH_BINARY_INV,                     │
│     blockSize=11, C=2                          │
│ )                                              │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ Step 4: Morphological Closing                 │
│ kernel = np.ones((3,3), np.uint8)             │
│ closed = cv2.morphologyEx(binary,              │
│     cv2.MORPH_CLOSE, kernel, iterations=2)     │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ Step 5: Morphological Opening                 │
│ opened = cv2.morphologyEx(closed,              │
│     cv2.MORPH_OPEN, kernel, iterations=1)      │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ Step 6: Contour Detection                     │
│ contours, _ = cv2.findContours(               │
│     opened, cv2.RETR_EXTERNAL,                 │
│     cv2.CHAIN_APPROX_SIMPLE                    │
│ )                                              │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ Step 7: Filter by Minimum Area                │
│ valid = [c for c in contours                   │
│     if cv2.contourArea(c) > MIN_AREA]          │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│ Step 8: Compute Bounding Boxes                │
│ bboxes = [cv2.boundingRect(c) for c in valid] │
└───────────────────────────────────────────────┘
        │
        ▼
        ┌──────────────────┐
        │ Measurement      │
        │ Engine           │
        │ (per contour)    │
        └──────────────────┘
```

### Annotation Generation

```
Original Image (BGR)
        │
        ├──▶ Draw bounding boxes (green rectangles)
        │         │
        │         ├──▶ Add labels (damage type + severity)
        │         │         │
        │         │         ├──▶ Add measurements (area %, dimensions)
        │         │         │
        │         │         └──▶ Add confidence scores
        │         │
        │         └──▶ Draw centroids (red circles)
        │
        ├──▶ Generate heatmap overlay
        │         │
        │         ├──▶ Color mask by severity
        │         │         Critical → Red
        │         │         High → Orange
        │         │         Medium → Yellow
        │         │         Low → Green
        │         │
        │         └──▶ Apply transparency (alpha blending)
        │
        ├──▶ Generate standalone mask (binary → colored)
        │
        └──▶ Generate color legend
                    │
                    └──▶ Severity → Color mapping
                          + Count per severity
```

### Key Parameters

| Parameter | Value | Purpose |
|---|---|---|
| `BLUR_KERNEL` | (5, 5) | Gaussian blur kernel size |
| `BLUR_SIGMA` | 0 | Auto-computed from kernel |
| `THRESH_BLOCK_SIZE` | 11 | Adaptive threshold neighborhood |
| `THRESH_C` | 2 | Constant subtracted from mean |
| `MORPH_KERNEL` | (3, 3) | Morphological operation kernel |
| `CLOSE_ITERATIONS` | 2 | Morphological close iterations |
| `OPEN_ITERATIONS` | 1 | Morphological open iterations |
| `MIN_CONTOUR_AREA` | 100 px | Minimum area to consider as damage |
| `HEATMAP_ALPHA` | 0.4 | Transparency of overlay |

---

## 18. Report Generation Workflow

### Data Flow

```
Inspection Results (session_state)
        │
        ├──▶ risk_engine.assess_risk()
        │         │
        │         └──▶ RiskAssessment
        │
        ├──▶ summary_engine.build_executive_summary()
        │         │
        │         └──▶ ExecutiveSummary
        │
        ├──▶ summary_engine.build_findings()
        │         │
        │         └──▶ list[FindingRecord]
        │
        ├──▶ summary_engine.build_timeline()
        │         │
        │         └──▶ list[TimelineEntry]
        │
        ├──▶ summary_engine.build_recommendations()
        │         │
        │         └──▶ dict[str, list[str]]
        │
        ├──▶ summary_engine.build_checklist()
        │         │
        │         └──▶ list[dict]
        │
        ├──▶ health_engine.analyze_property_health() (optional)
        │         │
        │         └──▶ PropertyHealthReport
        │
        └──▶ comparison_engine.compare_inspections() (optional)
                  │
                  └──▶ ComparisonReport
                        │
                        ▼
                  report_builder.render_report()
                        │
                        ├──▶ Section 1: Executive Summary
                        ├──▶ Section 2: Health Score + Risk
                        ├──▶ Section 3: Stat Cards
                        ├──▶ Section 4: Findings
                        ├──▶ Section 5: Repair Timeline
                        ├──▶ Section 6: Health Dashboard (if available)
                        ├──▶ Section 7: Comparison (if available)
                        ├──▶ Section 8: Recommendations
                        └──▶ Section 9: Inspection Checklist
```

### Report Sections Detail

**Section 1 — Executive Summary**

- Inspection ID, date, inspector name
- Property name, type, address
- Health score, risk level, risk color
- Total findings, average confidence
- Estimated repair cost range
- Processing time
- AI-generated assessment narrative

**Section 2 — Health Score & Risk Level**

- Large circular health score badge (0–100)
- Color gradient: Red (0) → Orange (30) → Yellow (60) → Green (100)
- Risk level card with icon and description
- Score interpretation text

**Section 3 — Stat Cards**

Four cards in a row:
- 🏠 Total Findings (count)
- 🎯 Avg Confidence (%)
- 💰 Est. Repair Cost (INR range)
- ⏱️ Processing Time (seconds)

**Section 4 — Findings**

For each finding:
- Severity badge (color-coded)
- Damage type
- Confidence bar
- Damage area %
- Contour count
- Possible causes
- Repair steps
- Recommended professional
- Estimated cost range
- Urgency level
- Prevention tips
- Image thumbnail with overlay

**Section 5 — Repair Timeline**

Visual timeline with phases:
- 🔴 Immediate (Critical findings)
- 🟠 Preparation
- 🟡 Repair
- 🔵 Finishing
- ✅ Inspection

Each phase shows duration, tasks, and descriptions.

**Section 6 — Property Health Dashboard**

- Strengths (green)
- Weaknesses (red)
- Priority Actions (amber)
- Health Summary narrative

**Section 7 — Inspection Comparison**

Only rendered when comparing:
- Score delta with arrow
- Grade change
- Risk trend
- Improvement score
- Cost change
- Damage changes (new/resolved)
- Days between inspections

**Section 8 — Recommendations**

Four subsections:
- 🚨 Immediate Actions (critical issues to address now)
- 📋 Repair Priority (ordered repair steps)
- 👷 Professional Help (who to call)
- 🛡️ Maintenance Tips (long-term prevention)

**Section 9 — Inspection Checklist**

- Progress bar (% complete)
- Grid of categories with check/uncheck status
- Categories: Structural, Electrical, Plumbing, Roofing, Foundation, Walls, Flooring, Windows/Doors, HVAC, Exterior, Interior, Ventilation, Insulation, Drainage, Safety

---

## 19. Development Roadmap

### Phase 1: Foundation (Week 1–2)

**Goal:** Set up project structure, basic UI, and image upload.

- Initialize Git repository
- Create folder structure
- Set up `requirements.txt`
- Build home page with property form and image upload
- Implement image validation
- Create session state management
- Apply custom CSS theme

**Deliverable:** Users can upload images and see validation feedback.

### Phase 2: AI Integration (Week 3–4)

**Goal:** Connect Gemini Vision API and display basic results.

- Set up Gemini API integration
- Build prompt templates
- Implement `inspection_engine.py` with `analyze_image()` and `run_inspection()`
- Create `InspectionReport` dataclass
- Build results dashboard
- Display findings with severity badges
- Show annotated images

**Deliverable:** Users upload images → AI detects damage → results displayed.

### Phase 3: Measurement Engine (Week 5)

**Goal:** Add computer vision measurements and visualizations.

- Implement OpenCV preprocessing pipeline
- Build contour detection and filtering
- Create measurement calculations (area, perimeter, shape complexity)
- Implement annotated image generation
- Generate heatmap overlays
- Build `MeasurementReport` dataclass
- Integrate measurements into results display

**Deliverable:** Results include heatmaps, bounding boxes, and precise measurements.

### Phase 4: Scoring & Risk (Week 6)

**Goal:** Add health scoring and risk assessment.

- Implement `risk_engine.py` with `assess_risk()`
- Build health score algorithm
- Create risk level classification
- Integrate scoring into results display
- Add risk visualization

**Deliverable:** Results display health scores and risk levels.

### Phase 5: Repair Planning (Week 7)

**Goal:** Generate professional repair plans.

- Build repair knowledge base
- Implement `repair_planner.py`
- Create repair task and phase generation
- Add cost estimation (materials, labour, equipment)
- Generate repair timelines
- Create checklists and maintenance schedules
- Display repair plan in results

**Deliverable:** Results include detailed repair plans with costs and timelines.

### Phase 6: Report & Polish (Week 8)

**Goal:** Complete report generation and polish the UI.

- Build `summary_engine.py`
- Implement `report_builder.py` with all sections
- Add property health dashboard
- Implement inspection history
- Add inspection comparison
- Polish CSS and responsiveness
- Add loading states and error handling
- Write README with setup instructions

**Deliverable:** Complete, polished application with all features.

### Phase 7: Documentation & Deployment (Week 9)

**Goal:** Prepare for portfolio and interviews.

- Write comprehensive README
- Add architecture documentation
- Create demo screenshots/GIFs
- Record demo video
- Deploy to Streamlit Community Cloud or Hugging Face Spaces
- Write blog post / LinkedIn article about the project
- Prepare talking points for interviews

**Deliverable:** Live deployed project with documentation.

---

## 20. GitHub Milestone Roadmap

### Milestone 1: Project Setup ✅ (Completed / In Progress)

- [x] Initialize Git repository
- [x] Create folder structure
- [x] Set up `requirements.txt`
- [x] Create `.gitignore`
- [x] Create `.env.example`
- [x] Implement custom CSS theme
- [x] Build session state management
- [x] Create home page with property form

### Milestone 2: Image Upload & Validation

- [ ] Implement multi-file upload with drag-and-drop
- [ ] Complete image validation (format, size, resolution)
- [ ] Add image previews
- [ ] Implement processing screen with progress
- [ ] Add error handling for invalid images

### Milestone 3: AI Integration

- [ ] Set up Gemini API connection
- [ ] Build prompt templates
- [ ] Implement `inspection_engine.py`
- [ ] Create `InspectionReport` and `FusedInspection` dataclasses
- [ ] Build results dashboard
- [ ] Display findings with severity coding

### Milestone 4: Computer Vision

- [ ] Implement OpenCV preprocessing pipeline
- [ ] Build contour detection
- [ ] Create measurement calculations
- [ ] Implement annotated image generation
- [ ] Generate heatmap overlays
- [ ] Integrate measurements into results

### Milestone 5: Scoring & Intelligence

- [ ] Implement `risk_engine.py`
- [ ] Build health score algorithm
- [ ] Create `health_engine.py`
- [ ] Implement `repair_planner.py`
- [ ] Build repair knowledge base
- [ ] Integrate scoring and planning into results

### Milestone 6: Report Generation

- [ ] Build `summary_engine.py`
- [ ] Implement `report_builder.py`
- [ ] Create all report sections
- [ ] Implement inspection history
- [ ] Add inspection comparison
- [ ] Polish navigation flow

### Milestone 7: Polish & Documentation

- [ ] Comprehensive README with screenshots
- [ ] Architecture documentation
- [ ] Demo video recording
- [ ] Deploy to Streamlit Community Cloud
- [ ] LinkedIn/blog post
- [ ] Final testing and bug fixes

### Milestone 8: Portfolio Enhancement (Post-MVP)

- [ ] PDF report export
- [ ] Supabase authentication
- [ ] User accounts
- [ ] Persistent storage
- [ ] Enhanced visualizations
- [ ] Mobile responsiveness

---

## 21. MVP Features

These are the features that must be complete for the MVP:

1. **Image Upload & Validation** — Multi-image upload with format, size, and resolution validation
2. **AI Damage Detection** — Gemini Vision API integration with structured JSON output
3. **Computer Vision Measurements** — OpenCV pipeline for contour detection, area measurement, and annotation
4. **Severity Classification** — Automatic classification of findings as Critical/High/Medium/Low
5. **Health Score** — Composite 0–100 health score with risk level
6. **Results Dashboard** — Interactive display of findings with filters, annotations, and measurements
7. **Repair Planning** — Detailed repair plans with materials, costs, timelines, and safety requirements
8. **Inspection Report** — Professional report with all sections (summary, findings, timeline, recommendations, checklist)
9. **Inspection History** — Session-based history with inspection metadata
10. **Navigation** — Multi-page flow between Home, Processing, Results, Report, and History

---

## 22. Version 2 Features

Features for the second iteration after MVP is live:

1. **PDF Report Export** — Download professional PDF reports using reportlab or weasyprint
2. **Supabase Authentication** — User login/signup with email/password
3. **Persistent Storage** — All data stored in Supabase, survives app restarts
4. **User Dashboard** — Personal dashboard showing all properties and inspections
5. **Property Management** — Add, edit, delete properties; assign inspections to properties
6. **Batch Property Inspection** — Inspect multiple properties, compare across properties
7. **Email Report Delivery** — Send reports to clients via email directly from the app
8. **Enhanced Visualizations** — Chart-based health trends over time using Plotly
9. **Dark/Light Theme Toggle** — User-selectable theme
10. **Image Annotation Editor** — Allow users to draw on images, add notes, circle specific areas

---

## 23. Version 3 Features

Features for the third iteration:

1. **Mobile App** — React Native or Flutter mobile app for on-site inspection
2. **Offline Mode** — Inspect images without internet, sync when connected
3. **Multi-language Support** — Hindi, Tamil, Telugu, and other regional languages
4. **Collaborative Inspections** — Multiple inspectors on the same property, shared annotations
5. **IoT Integration** — Connect with moisture meters, thermal cameras via Bluetooth
6. **API for Third-Party Integration** — REST API for property management software
7. **Advanced Analytics Dashboard** — Portfolio-level analytics for real estate companies
8. **AI Model Fine-Tuning** — Custom damage detection model trained on regional damage types
9. **AR Overlay** — Augmented reality view showing damage overlays on camera feed
10. **Insurance Integration** — Generate insurance claim documents directly from reports

---

## 24. Interview Value of Each Feature

### Image Upload & Validation
**Talking point:** "I built a robust file validation system that checks format, size, resolution, and readability before processing. This prevents wasted API calls and gives users clear, actionable error messages."

**Skills demonstrated:** File handling, input validation, user experience design, error handling.

### AI Damage Detection (Gemini Vision)
**Talking point:** "I integrated a multimodal AI model (Gemini Vision) to analyze property images. I designed structured JSON prompts that extract specific damage metadata — type, severity, confidence, causes, repair steps, costs. The AI output is parsed and validated into strongly-typed dataclasses."

**Skills demonstrated:** AI API integration, prompt engineering, structured output parsing, JSON schema design, multimodal AI.

### Computer Vision Pipeline (OpenCV)
**Talking point:** "I built a complete computer vision pipeline: grayscale conversion, Gaussian blur, adaptive thresholding, morphological operations, and contour detection. For each detected region, I calculate area percentages, bounding boxes, shape complexity, crack dimensions, and wall quadrant positions."

**Skills demonstrated:** Computer vision, image processing, OpenCV, numpy, geometric analysis, algorithm design.

### Health Scoring Algorithm
**Talking point:** "I designed a weighted scoring algorithm that computes a property health score from 0–100 based on damage extent, severity distribution, and contour complexity. The score maps to risk levels (Low/Medium/High/Critical) that non-technical users can understand."

**Skills demonstrated:** Algorithm design, weighted scoring, data aggregation, UX-oriented metric design.

### Repair Planning Engine
**Talking point:** "I built a rule-based repair planning engine with a comprehensive knowledge base covering 10+ damage types. It generates prioritized task lists, material quantities with costs, labour estimates by professional type, safety requirements, step-by-step sequences, and maintenance schedules."

**Skills demonstrated:** Knowledge base design, rule-based systems, cost estimation, workflow design, domain knowledge application.

### Report Generation
**Talking point:** "I architected a report generation system that transforms raw AI outputs into a professional, multi-section inspection report. The summary engine converts dataclass outputs into display-ready records, and the report builder renders them with custom CSS styling."

**Skills demonstrated:** Data transformation, report design, UI/UX, content structuring, separation of concerns.

### Inspection History & Comparison
**Talking point:** "I implemented inspection history tracking with session-based persistence, and a comparison engine that diffs two inspections to show score deltas, grade changes, risk trends, new vs. resolved damage, and cost changes over time."

**Skills demonstrated:** Data comparison algorithms, diff analysis, trend computation, time-series thinking.

### Architecture & Code Quality
**Talking point:** "I designed a layered architecture with pure logic modules that have zero UI dependencies. All AI engines are independently testable with no Streamlit imports. I use frozen dataclasses for all data structures, centralized constants, and type hints throughout."

**Skills demonstrated:** Software architecture, clean code, testability, design patterns, Python best practices.

---

## 25. Resume Value of the Project

### How to Present This Project on a Resume

```
PROJECT: InspectAI — AI-Powered Property Inspection Platform
Tech Stack: Python, Streamlit, OpenCV, NumPy, Pillow, Gemini Vision API

• Architected and built an AI-powered property inspection platform that analyzes
  uploaded images to detect damage, measure severity, and generate professional
  inspection reports with repair plans and cost estimates.

• Designed and implemented a 7-stage AI pipeline: image validation → OpenCV
  preprocessing → Gemini Vision analysis → contour measurement → risk scoring →
  repair planning → report generation.

• Built a computer vision module using OpenCV that processes images through
  Gaussian blur, adaptive thresholding, morphological operations, and contour
  detection, calculating damage area percentages, shape complexity, and crack
  dimensions.

• Engineered a rule-based repair planning system with a knowledge base of 10+
  damage types, generating prioritized task lists, material costs, labour estimates,
  safety requirements, and maintenance schedules.

• Designed a composite health scoring algorithm (0–100) based on damage extent,
  severity distribution, and contour complexity, mapped to actionable risk levels.

• Architected a layered software design with pure logic modules (zero UI coupling),
  frozen dataclass data models, centralized constants, and full type annotations
  for maintainability and testability.
```

### Key Resume Bullets by Category

**AI/ML Skills:**
- Multimodal AI integration (Gemini Vision API)
- Prompt engineering for structured JSON output
- Confidence scoring and result validation
- Rule-based AI systems (repair planning knowledge base)

**Computer Vision Skills:**
- Image preprocessing pipeline (blur, threshold, morphology)
- Contour detection and analysis
- Shape complexity computation
- Heatmap and annotation generation
- Damage area quantification

**Software Engineering Skills:**
- Layered architecture with separation of concerns
- Pure function design for testability
- Dataclass-based data modeling
- Session state management
- Error handling and resilience
- Pipeline pattern implementation

**Full-Stack Skills:**
- Streamlit web application development
- Custom CSS theming and responsive design
- Multi-page navigation
- File upload and validation
- Interactive data visualization

**Domain Skills:**
- Property inspection domain knowledge
- Cost estimation methodology
- Risk assessment frameworks
- Report generation and professional formatting

### Interview Talking Points

1. **"Why did you choose Streamlit over Flask/Django?"**
   → "Streamlit let me focus on the AI and CV logic instead of boilerplate. For a portfolio project demonstrating ML/AI skills, it's the fastest way to get a polished UI."

2. **"How do you handle AI output reliability?"**
   → "I validate the AI response against expected schemas, use fallback defaults when fields are missing, and have a validation layer before any data reaches the UI."

3. **"What's the most challenging part?"**
   → "Designing the measurement engine to work reliably across different image qualities. I had to tune threshold parameters and add morphological operations to handle varying lighting conditions."

4. **"How would you scale this?"**
   → "Replace session storage with Supabase for persistence, add user authentication, implement a task queue for batch processing, and consider a lightweight local model for offline detection."

5. **"What would you improve?"**
   → "Add PDF export, implement user accounts, fine-tune the prompt for better accuracy on regional damage types, and add a feedback loop where users can correct AI classifications."

---

## 26. What Should NOT Be Added

To keep the project practical, focused, and impressive without over-engineering:

### Infrastructure (Do NOT Add)
- ❌ Docker / Docker Compose — Adds deployment complexity without demonstrating AI skills
- ❌ Kubernetes — Overkill for a single-container app
- ❌ Microservices — Single Streamlit app is the right scope
- ❌ Redis / RabbitMQ / Kafka — No messaging needs in the current architecture
- ❌ AWS / GCP / Azure cloud architecture — Deploy to Streamlit Community Cloud (free, one-click)
- ❌ Nginx / Gunicorn / uWSGI — Streamlit handles serving
- ❌ CI/CD pipelines — Not needed until the project is mature

### Complexity (Do NOT Add)
- ❌ Custom ML model training — Gemini API is sufficient; training a model adds weeks without proportional portfolio value
- ❌ Fine-tuning YOLO / Faster R-CNN — Same reasoning; API-based approach is more impressive for the time invested
- ❌ WebSocket real-time updates — Polling or simple progress bars are sufficient
- ❌ Complex caching layers — Session state is enough
- ❌ Rate limiting / API gateway — Not needed for a portfolio project
- ❌ Complex authentication (OAuth, SSO, JWT) — Supabase email auth (v2) is sufficient
- ❌ Payment processing — Not a commercial product yet

### Features (Do NOT Add to MVP)
- ❌ Multi-language support — Adds translation burden; demonstrate English proficiency first
- ❌ Mobile app — Web app works on mobile browsers; native apps are a separate project
- ❌ Real-time collaboration — Google Docs-style editing is out of scope
- ❌ AR/VR features — Cool but not practical for a fresher portfolio
- ❌ Blockchain integration — No legitimate use case here
- ❌ Social features (comments, likes, shares) — Not relevant to property inspection
- ❌ Marketplace (finding contractors, booking services) — Out of scope

### Code Quality Traps (Do NOT Do)
- ❌ Over-abstract everything — Some duplication is fine if it makes the code more readable
- ❌ Premature optimization — Profile before optimizing; Python + OpenCV is fast enough
- ❌ Gold-plating the UI — Professional and clean is enough; you're not a frontend engineer
- ❌ Writing tests before features work — Get it working first, then add tests
- ❌ Refactoring in circles — Make it work, make it right, make it fast — in that order

### The Golden Rule

> **Every feature you add should either (a) demonstrate a technical skill you want to highlight in interviews, or (b) make the product noticeably better for users. If it does neither, skip it.**

---

## Appendix: Key Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **UI Framework** | Streamlit | Fastest path to polished UI; lets you focus on AI/CV |
| **AI Backend** | Gemini Vision API | Multimodal (understands images), structured JSON output, generous free tier |
| **CV Library** | OpenCV | Industry standard, well-documented, powerful |
| **Data Format** | Python dataclasses | Type-safe, IDE-friendly, serializable, no boilerplate |
| **Storage (MVP)** | Streamlit session state | Zero setup, perfect for demo/portfolio |
| **Storage (Future)** | Supabase | Free tier, PostgreSQL, auth, file storage — all in one |
| **Deployment** | Streamlit Community Cloud | Free, one-click deploy from GitHub, auto-updates on push |
| **Report Format (MVP)** | In-browser HTML | No PDF dependency needed for MVP |
| **Report Format (Future)** | PDF via reportlab | Professional output for client delivery |
| **Language** | Python | Team's primary language, best AI/CV ecosystem |

---

*End of Product Requirement Document*

*This document is a living artifact. Update it as the project evolves and requirements change.*
