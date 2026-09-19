# InspectAI — Product Requirement Document

**Version:** 1.0  
**Date:** 2026-07-15  
**Status:** Active Development  
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
15. [Database Requirements](#15-database-requirements)
16. [AI Workflow](#16-ai-workflow)
17. [Image Processing Workflow](#17-image-processing-workflow)
18. [Report Generation Workflow](#18-report-generation-workflow)
19. [Development Roadmap](#19-development-roadmap)
20. [GitHub Milestone Roadmap](#20-github-milestone-roadmap)
21. [MVP Features](#21-mvp-features)
22. [Version 2 Features](#22-version-2-features)
23. [Version 3 Features](#23-version-3-features)
24. [Interview Value of Each Feature](#24-interview-value-of-each-feature)
25. [Resume Value](#25-resume-value)
26. [What Should NOT Be Added](#26-what-should-not-be-added)

---

## 1. Product Vision

InspectAI is an AI-powered property inspection platform that helps homeowners, property inspectors, civil engineers, builders, and real-estate professionals inspect buildings using images and artificial intelligence.

The application analyses uploaded property images, identifies damage types (cracks, dampness, mould, structural deformations, water damage, etc.), estimates severity levels, generates structured inspection reports with repair recommendations, and maintains a complete inspection history over time.

The vision is to make property inspection faster, cheaper, and more data-driven — replacing manual checklist-based inspections with intelligent visual analysis.

**Key Principles:**
- Simple enough for a homeowner to use, powerful enough for a professional inspector
- Offline-first: runs entirely locally without requiring cloud services
- Transparent AI: every detection comes with a confidence score and explanation
- Practical and realistic: focuses on what computer vision can actually detect reliably

---

## 2. Problem Statement

### The Problem

Traditional property inspection is:

- **Subjective**: Two inspectors can look at the same wall and give different severity ratings
- **Time-consuming**: A full building inspection takes 2–4 hours on-site plus hours of report writing
- **Inconsistent**: No standardised format — reports vary wildly between inspectors
- **Expensive**: Professional inspectors charge INR 2,000–10,000 per inspection in India
- **Historical tracking is manual**: Previous inspection reports are PDFs stored in folders — impossible to compare
- **Accessibility**: Many homeowners skip professional inspections due to cost

### What InspectAI Solves

| Pain Point | InspectAI Solution |
|---|---|
| Subjective damage assessment | AI provides consistent, repeatable severity scoring |
| Hours of report writing | Automated report generation in under 2 minutes |
| No standard format | Structured reports with severity grades, cost estimates, and repair steps |
| Cannot track deterioration | Inspection history with before/after comparison |
| Cost of professional inspection | DIY inspection with AI assistance for under INR 500 |
| Late detection of structural issues | Regular scans catch problems early |

### Why Now

- Smartphone cameras have reached 48MP+ with computational photography — good enough for damage detection
- OpenCV and classical CV techniques are mature, free, and run locally
- Computer vision libraries (YOLO, SAM) are accessible to individual developers
- Post-COVID, there is increased awareness of building health and indoor air quality
- The Indian real estate market (INR 3.2 lakh crore) lacks tech-enabled inspection tools

---

## 3. Target Users

### Primary Users

| Segment | Description | Approximate Size |
|---|---|---|
| Homeowners | Apartment/villa owners who want to check for damage before buying, after floods/earthquakes, or periodically | Large — 100M+ urban households in India |
| Property Inspectors | Freelance or agency inspectors looking to digitise and speed up their workflow | Medium — ~10,000 in India |
| Civil Engineers | Structural engineers and consultants who need to document site conditions | Medium — ~50,000 in India |
| Builders & Contractors | Construction companies tracking pre-handover defects and post-construction snags | Medium — ~20,000 companies |
| Real Estate Agents | Agents who want to provide inspection reports to buyers for credibility | Small-Medium |
| Facility Managers | Managing society/common area maintenance in residential complexes | Medium |

### Secondary Users

- Architects doing condition surveys
- Insurance assessors for damage claims
| Students/researchers in civil engineering and AI

---

## 4. User Personas

### Persona 1: Ramesh — The Homeowner

- **Age:** 38
- **Occupation:** Software Engineer, Bangalore
- **Tech Comfort:** High (uses smartphones daily, comfortable with apps)
- **Goal:** Wants to check his 10-year-old apartment for water damage and cracks before renovating
- **Pain Point:** Doesn't trust contractors to give honest assessments. Can't afford a structural engineer (INR 15,000+).
- **How he uses InspectAI:** Takes photos of his walls with his phone, uploads to InspectAI, gets a damage report with severity ratings and repair cost estimates. Uses the report to negotiate with contractors.

### Persona 2: Priya — The Property Inspector

- **Age:** 29
- **Occupation:** Freelance property inspector, Mumbai
- **Tech Comfort:** Medium (uses laptop and phone for work)
- **Goal:** Wants to inspect 5 properties per week but currently spends 3+ hours writing reports after each inspection.
- **Pain Point:** Report writing eats into her billable hours. Clients want PDFs but her current process is screenshots in Word.
- **How she uses InspectAI:** Takes 30–50 photos per property, uploads them to InspectAI, reviews the AI-generated report, makes minor edits, and exports a professional PDF. Saves ~2 hours per inspection.

### Persona 3: Arvind — The Civil Engineer

- **Age:** 45
- **Occupation:** Structural engineer, government consultancy
- **Tech Comfort:** Medium
- **Goal:** Needs to document building conditions after a flood for a municipal report.
- **Pain Point:** Takes 200+ photos. Manually categorising them is tedious. Needs severity grading for his official report.
- **How he uses InspectAI:** Uploads batches of images, gets severity-graded findings with location tags, exports the report for submission to the municipal corporation.

### Persona 4: Vikram — The Builder

- **Age:** 35
- **Occupation:** Construction company project manager, Pune
- **Tech Comfort:** Medium
- **Goal:** Tracks defects in ongoing construction projects. Needs to hand over snag-free buildings.
- **Pain Point:** Site supervisors send WhatsApp photos with no context or severity. Hard to prioritise fixes.
- **How he uses InspectAI:** Site supervisors upload photos to InspectAI. Vikram reviews the severity dashboard to prioritise critical issues first. Tracks improvement across weekly inspections.

---

## 5. User Journey

### New User Journey (First-Time)

```
1. Discovery
   └─ Finds InspectAI on GitHub / hears from a friend
   
2. Onboarding
   └─ Clones repo / downloads app
   └─ Runs: pip install -r requirements.txt && streamlit run app.py
   └─ Lands on Dashboard — sees key stats and a "New Inspection" button
   
3. First Inspection
   └─ Clicks "New Inspection"
   └─ Step 1: Enters property details (type, address, year built)
   └─ Step 2: Uploads 3–5 images of walls, ceilings, corners
   └─ Step 3: Reviews uploaded images, removes unwanted ones
   └─ Step 4: Clicks "Analyze" → sees processing screen with progress
   └─ Step 5: Views results — damage maps, severity scores, findings
   
4. First Report
   └─ Reviews the auto-generated report
   └─ Exports as PDF or views on-screen
   
5. Retention
   └─ Returns for next inspection
   └─ Checks history to see past inspections
   └─ Compares current condition with previous
```

### Returning User Journey

```
1. Opens app → sees Dashboard with stats
2. Clicks "New Inspection"
3. Selects an existing property OR creates a new one
4. Uploads images → reviews → analyzes
5. Views results → compares with last inspection of same property
6. Exports report for client/record
```

### Inspector Workflow (Power User)

```
1. Opens app → Dashboard shows all recent inspections
2. Clicks "New Inspection"
3. Selects property from dropdown (previously created)
4. Uploads 30–50 images from site visit
5. Reviews — removes blurry/invalid images
6. Runs AI analysis (takes 30–60 seconds for 50 images)
7. Reviews findings — adjusts severity if needed (manual override)
8. Adds personal notes/observations
9. Exports professional PDF report
10. Logs out — data persists locally in SQLite
```

---

## 6. Core Features

### F1: Dashboard

- Overview cards: total properties, inspections, completion rate, avg health score
- Recent inspections list with status badges
- Severity distribution chart (critical/high/medium/low counts)
- Quick action buttons: New Inspection, View History
- Processing queue status

### F2: Property Management

- Create property with metadata (type, address, year built, area, floors, construction type)
- View property list with search and filter
- Edit property details
- Delete property (cascades to inspections and reports)
- Property details page with linked inspections

### F3: Image Upload & Validation

- Drag-and-drop multi-image upload
- Supported formats: JPG, PNG, WEBP
- Pre-flight validation: format check, file size, minimum resolution, blur detection
- Image preview grid with remove/reorder options
- File metadata display (size, dimensions)

### F4: AI Damage Detection

**Two-engine pipeline:**

**Engine A — Classical CV (OpenCV):**
- Pre-processing: resize, denoise, contrast enhancement
- Crack detection: Canny edge detection + contour analysis → crack length, width, density
- Water damage: colour space analysis (HSV) for brown/yellow discolouration
- Surface texture: Gabor filter + LBP for roughness/peeling detection
- Structural deformation: perspective correction + corner/line detection for wall bowing

**Engine B — Gemini Vision API (optional, fallback):**
- Semantic analysis of images for damage description
- Damage type classification with natural language
- Severity estimation with reasoning

**Fusion Layer:**
- Merges results from both engines
- Resolves conflicts (e.g., OpenCV says "medium crack", Gemini says "severe crack" → weighted average with confidence scoring)
- Produces unified `FusedInspection` result

### F5: Image-Level Analysis

Per-image results:
- Damage percentage (how much of the image area is damaged)
- Severity grade (critical / high / medium / low / none)
- Confidence score (0–100%)
- Damage types detected (list)
- Visual annotation (overlay on the image)

### F6: Inspection-Level Fusion

Aggregates all image results into a comprehensive inspection report:
- Overall damage percentage across all images
- Overall severity (worst severity found)
- Overall confidence
- Health score (0–100)
- Estimated repair cost range (INR min/max)
- Priority findings (most critical damages)
- Repair timeline estimate
- Maintenance tips

### F7: Report Generation

**Inspection Report:**
- Executive summary (AI-generated paragraph)
- Property summary
- Inspection details (date, inspector, weather)
- Findings table with severity, confidence, damage type, cost estimate
- Image rankings (most damaged to least)
- Repair recommendations per finding
- Maintenance tips

**Health Report:**
- Overall health grade (A+ to D)
- Severity breakdown chart
- Component-wise health (if applicable)
- Risk assessment

**Comparison Report** (when previous inspection exists):
- Before vs after damage percentage
- Deterioration or improvement delta
- New damages since last inspection
- Critical changes flagged

**Timeline Report:**
- Chronological list of findings with dates
- Progression of damage over time
- Recommended next inspection date

### F8: Inspection History

- List view of all inspections with search, filter, sort
- Filters: property type, severity, grade, date range
- Sort by: newest, oldest, highest damage, lowest damage, highest cost
- Statistics: total inspections, avg health score, critical count, avg repair cost
- Pagination support

### F9: Reports Dashboard

- List of all generated reports
- Filter by severity
- Quick view of key metrics per report
- Navigate to full report detail

### F10: Report Detail View

- Full report display with all sections
- Tabs: Overview | Findings | Health | Comparison | Timeline
- Image gallery with damage annotations
- Print-friendly layout

### F11: PDF Export

- Professional multi-page PDF
- Cover page with property info
- Table of contents
- Findings with severity badges and cost estimates
- Image thumbnails with annotations
- Health grade summary
- Signature/review section

### F12: Analytics Dashboard

- Damage trend over time (line chart)
- Severity distribution (pie/donut chart)
- Cost estimation trends
- Property type comparison
- Most common damage types (bar chart)
- Heatmap of damage locations (if location metadata available)

### F13: Settings

- AI engine toggle (OpenCV only / Gemini fallback / both)
- Confidence threshold slider
- Severity classification sensitivity
- Cost estimation model (basic / detailed)
- Clear all data option
- About / version info

### F14: Session Management

- Session state persistence across page reruns
- Inspection wizard state machine (5 steps)
- Navigation breadcrumbs
- Confirmation dialogs for destructive actions

---

## 7. Future Features

### F15: Gemini Vision API Integration (Optional)

- Full semantic analysis of images
- Natural language damage descriptions
- Context-aware severity estimation
- Repair suggestion generation via LLM

### F16: Supabase Backend (Optional)

- User authentication (email/password)
- Cloud storage for images
- Multi-device sync
- Shared inspections (team collaboration)
- API for third-party integrations

### F17: Advanced AI Models (Optional)

- YOLOv8 for object-level damage detection
- Segment Anything Model (SAM) for precise damage mask generation
- Custom trained model on property damage dataset
- Multi-class damage classifier

### F18: Map View

- Geospatial display of inspected properties
- Colour-coded pins by severity
- Cluster view for bulk inspections

### F19: Notification System

- Reminder for periodic re-inspection
- Alert when damage severity increases
- Email/PDF report delivery

### F20: Mobile-First PWA

- Responsive design for mobile browsers
- Camera integration for direct capture
- Offline mode with sync

### F21: Third-Party Integrations

- Export to Google Docs
- Share via WhatsApp/Email
- Integration with property management software

---

## 8. Functional Requirements

### FR-1: Dashboard Display

| ID | Requirement | Priority |
|---|---|---|
| FR-1.1 | Display total properties count | Must |
| FR-1.2 | Display total inspections count | Must |
| FR-1.3 | Display completed vs processing inspections | Must |
| FR-1.4 | Display average health score | Must |
| FR-1.5 | Display recent inspections list (last 5) | Must |
| FR-1.6 | Display severity distribution | Must |
| FR-1.7 | Quick action buttons for common tasks | Should |

### FR-2: Property CRUD

| ID | Requirement | Priority |
|---|---|---|
| FR-2.1 | Create property with all metadata fields | Must |
| FR-2.2 | List properties with search and filter | Must |
| FR-2.3 | Edit property details | Must |
| FR-2.4 | Delete property with cascade | Must |
| FR-2.5 | Property type validation (6 types) | Must |
| FR-2.6 | View property details with linked inspections | Should |

### FR-3: Image Upload

| ID | Requirement | Priority |
|---|---|---|
| FR-3.1 | Multi-file drag-and-drop upload | Must |
| FR-3.2 | Accept JPG, PNG, WEBP | Must |
| FR-3.3 | Validate file format | Must |
| FR-3.4 | Validate minimum resolution (200x200) | Must |
| FR-3.5 | Validate maximum file size (20MB) | Should |
| FR-3.6 | Blur detection and warning | Should |
| FR-3.7 | Image preview grid | Must |
| FR-3.8 | Remove individual images | Must |
| FR-3.9 | File metadata display | Should |

### FR-4: AI Analysis

| ID | Requirement | Priority |
|---|---|---|
| FR-4.1 | Classical CV analysis via OpenCV | Must |
| FR-4.2 | Crack detection with measurements | Must |
| FR-4.3 | Water damage / discolouration detection | Must |
| FR-4.4 | Surface texture analysis | Should |
| FR-4.5 | Structural deformation detection | Should |
| FR-4.6 | Per-image damage percentage | Must |
| FR-4.7 | Per-image severity classification | Must |
| FR-4.8 | Per-image confidence score | Must |
| FR-4.9 | Per-image damage types list | Must |
| FR-4.10 | Per-image visual annotation | Should |
| FR-4.11 | Gemini Vision optional integration | Optional |
| FR-4.12 | Fusion of multiple engine results | Must |
| FR-4.13 | Overall inspection severity | Must |
| FR-4.14 | Overall damage percentage | Must |
| FR-4.15 | Health score (0–100) | Must |
| FR-4.16 | Estimated repair cost range | Must |
| FR-4.17 | Maintenance tips generation | Should |
| FR-4.18 | Executive summary generation | Should |

### FR-5: Inspection History

| ID | Requirement | Priority |
|---|---|---|
| FR-5.1 | List all inspections with details | Must |
| FR-5.2 | Search by address, city, ID, inspector | Must |
| FR-5.3 | Filter by property type | Must |
| FR-5.4 | Filter by severity | Must |
| FR-5.5 | Filter by health grade | Must |
| FR-5.6 | Filter by date range | Should |
| FR-5.7 | Sort by newest, oldest, damage, cost | Must |
| FR-5.8 | Pagination (50 per page) | Should |
| FR-5.9 | Severity counts per inspection | Must |
| FR-5.10 | Grade derivation (A+ to D) | Must |

### FR-6: Report Generation & Display

| ID | Requirement | Priority |
|---|---|---|
| FR-6.1 | Generate inspection report | Must |
| FR-6.2 | Generate health report | Must |
| FR-6.3 | Generate comparison report (with history) | Should |
| FR-6.4 | Generate timeline report | Should |
| FR-6.5 | Display full report with tabs | Must |
| FR-6.6 | Image gallery in report | Must |
| FR-6.7 | Findings table with all details | Must |
| FR-6.8 | PDF export | Should |
| FR-6.9 | Report list page | Must |

### FR-7: Analytics

| ID | Requirement | Priority |
|---|---|---|
| FR-7.1 | Damage trend over time chart | Should |
| FR-7.2 | Severity distribution chart | Should |
| FR-7.3 | Cost estimation trends | Should |
| FR-7.4 | Most common damage types | Should |
| FR-7.5 | Property type comparison | Should |

### FR-8: Data Persistence

| ID | Requirement | Priority |
|---|---|---|
| FR-8.1 | SQLite database with 4 tables | Must |
| FR-8.2 | CRUD for properties | Must |
| FR-8.3 | CRUD for inspections | Must |
| FR-8.4 | CRUD for inspection images | Must |
| FR-8.5 | CRUD for reports | Must |
| FR-8.6 | Cascade delete (property → inspection → images/reports) | Must |
| FR-8.7 | Database auto-initialisation on first run | Must |
| FR-8.8 | Indexed queries for performance | Should |
| FR-8.9 | Dashboard statistics queries | Must |
| FR-8.10 | Inspection history joined query | Must |

### FR-9: Session & Navigation

| ID | Requirement | Priority |
|---|---|---|
| FR-9.1 | Session state persistence across reruns | Must |
| FR-9.2 | 5-step inspection wizard state machine | Must |
| FR-9.3 | Sidebar navigation | Must |
| FR-9.4 | Breadcrumb navigation | Should |
| FR-9.5 | Confirmation dialogs for destructive actions | Must |
| FR-9.6 | Reset inspection flow | Must |

---

## 9. Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|---|---|---|
| NFR-1 | App startup time | < 3 seconds |
| NFR-2 | AI analysis for 10 images | < 30 seconds |
| NFR-3 | AI analysis for 50 images | < 2 minutes |
| NFR-4 | Page navigation | < 1 second |
| NFR-5 | Report generation | < 5 seconds |
| NFR-6 | Database query (history list) | < 500ms for 1000 records |
| NFR-7 | Memory usage | < 500MB for 50 images |

### Reliability

| ID | Requirement | Target |
|---|---|---|
| NFR-8 | Graceful degradation if OpenCV fails | Must |
| NFR-9 | Graceful degradation if Gemini API fails | Should |
| NFR-10 | Data persistence across app restarts | Must |
| NFR-11 | No data loss during analysis | Must |
| NFR-12 | Error messages are user-friendly | Must |

### Usability

| ID | Requirement | Target |
|---|---|---|
| NFR-13 | No manual configuration needed to run | Must |
| NFR-14 | Works on 1080p screens | Must |
| NFR-15 | Responsive on tablets | Should |
| NFR-16 | No technical knowledge required | Must |
| NFR-17 | Clear error messages with suggestions | Must |
| NFR-18 | Consistent UI across all pages | Must |

### Security

| ID | Requirement | Target |
|---|---|---|
| NFR-19 | No sensitive data in Git | Must |
| NFR-20 | .env.example provided, .env gitignored | Must |
| NFR-21 | SQL injection prevention (parameterised queries) | Must |
| NFR-22 | No hardcoded credentials | Must |

### Maintainability

| ID | Requirement | Target |
|---|---|---|
| NFR-23 | Separation of concerns (DB, AI, UI) | Must |
| NFR-24 | Type hints on all functions | Should |
| NFR-25 | Docstrings on all public functions | Should |
| NFR-26 | Consistent naming conventions | Must |
| NFR-27 | No circular imports | Must |

---

## 10. Screen-by-Screen Breakdown

### Screen 1: Dashboard (`pages/dashboard.py`)

**Purpose:** Landing page. Give users an at-a-glance overview of their inspection activity.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Header: InspectAI logo + title                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Properties│ │Inspections│ │Completed │ │Avg Health│       │
│  │    Count  │ │  Count   │ │   Rate   │ │  Score   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  Severity Distribution  │  Recent Inspections                │
│  ┌──────────────────┐   │  ┌────────────────────────┐       │
│  │ Critical: 2      │   │  │ INSP-xxx  │ 2024-01-15 │       │
│  │ High: 5          │   │  │ INSP-yyy  │ 2024-01-14 │       │
│  │ Medium: 8        │   │  │ INSP-zzz  │ 2024-01-13 │       │
│  │ Low: 3           │   │  └────────────────────────┘       │
│  └──────────────────┘   │                                    │
│                         │  [New Inspection] [View History]   │
└─────────────────────────────────────────────────────────────┘
```

**Components used:**
- `render_dashboard()` in `pages/dashboard.py`
- `get_dashboard_stats()` from `database/repository.py`
- CSS cards in `styles/main.css`

**Session state needed:**
- None (read-only page)

---

### Screen 2: New Inspection — Step 1 — Property Details (`pages/new_inspection.py`)

**Purpose:** Collect property information before uploading images.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back          New Inspection — Step 1 of 5               │
│  ████░░░░░░░░░░░░░░░░░░                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Property Type *                                            │
│  [Dropdown: Residential | Commercial | Industrial | ...]     │
│                                                              │
│  Address                                                    │
│  [Text input]                                               │
│                                                              │
│  City                    State              Pincode         │
│  [____]                  [____]             [____]           │
│                                                              │
│  Year Built               Area (sqft)        Floors          │
│  [____]                   [____]             [____]           │
│                                                              │
│  Construction Type                                          │
│  [Dropdown: RCC | Brick | Stone | Mixed | Other]            │
│                                                              │
│  Inspector Name                                             │
│  [Text input]                                               │
│                                                              │
│  Notes                                                      │
│  [Text area]                                                │
│                                                              │
│                                    [Cancel]  [Continue →]    │
└─────────────────────────────────────────────────────────────┘
```

**Components used:**
- `render_property_details()` in `pages/new_inspection.py`
- `create_property()` from `database/repository.py`
- Form widgets from Streamlit

**Session state needed:**
- `inspection_step`: 1
- `property_data`: dict with form values
- `current_page`: "new_inspection"

---

### Screen 3: New Inspection — Step 2 — Upload Images (`pages/upload.py`)

**Purpose:** Upload and validate inspection images.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back          New Inspection — Step 2 of 5               │
│  ████████████░░░░░░░░░░                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Upload Inspection Images                                   │
│  Drag & drop images here, or click to browse                │
│  ┌─────────────────────────────────────────┐                 │
│  │                                         │                 │
│  │         📁 Drop zone area               │                 │
│  │                                         │                 │
│  │    Supports: JPG, PNG, WEBP             │                 │
│  │    Max size: 20MB per image             │                 │
│  │                                         │                 │
│  └─────────────────────────────────────────┘                 │
│                                                              │
│  Uploaded Images (5)                   [Clear All]          │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                       │
│  │ 🖼️ │ │ 🖼️ │ │ 🖼️ │ │ 🖼️ │ │ 🖼️ │                       │
│  │img1│ │img2│ │img3│ │img4│ │img5│                       │
│  │ [×]│ │ [×]│ │ [×]│ │ [×]│ │ [×]│                       │
│  └────┘ └────┘ └────┘ └────┘ └────┘                       │
│                                                              │
│  Image 1: 1920x1080, 1.2 MB   [OK]                         │
│  Image 2: 800x600, 450 KB     [OK]                         │
│  Image 3: 400x300, 120 KB     [WARNING: Low resolution]     │
│                                                              │
│                                    [← Back]  [Continue →]    │
└─────────────────────────────────────────────────────────────┘
```

**Components used:**
- `render_image_upload()` in `pages/upload.py`
- `validate_image()` from `ai/image_validator.py`
- `process_uploaded_images()` from `utils/image_helpers.py`
- Streamlit file uploader

**Session state needed:**
- `inspection_step`: 2
- `uploaded_images`: list of dicts with image data

---

### Screen 4: New Inspection — Step 3 — Review (`pages/review.py`)

**Purpose:** Review uploaded images before analysis. Remove unwanted images.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back          New Inspection — Step 3 of 5               │
│  ████████████████████░░                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Review Uploaded Images                                      │
│  Remove any images that are blurry, irrelevant, or duplicate │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │                │  │                │  │                │  │
│  │   [Image 1]    │  │   [Image 2]    │  │   [Image 3]    │  │
│  │                │  │                │  │                │  │
│  │  ✅ Good quality│  │ ⚠️  Slight blur │  │ ✅ Good quality │  │
│  │                │  │                │  │                │  │
│  │     [Remove]   │  │     [Remove]   │  │     [Remove]   │  │
│  └────────────────┘  └────────────────┘  └────────────────┘  │
│                                                              │
│  Summary: 5 images uploaded, 0 removed                       │
│                                                              │
│                                    [← Back]  [Analyze →]    │
└─────────────────────────────────────────────────────────────┘
```

**Components used:**
- `render_review()` in `pages/review.py`
- Image display from Streamlit

**Session state needed:**
- `inspection_step`: 3
- `uploaded_images`: list of dicts (may be modified)

---

### Screen 5: New Inspection — Step 4 — Processing (`pages/processing.py`)

**Purpose:** Show analysis progress. This is a full-screen page without sidebar.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│                                                              │
│              🔍 InspectAI is Analyzing...                    │
│                                                              │
│              ┌──────────────────────────┐                   │
│              │  ████████████████░░░░   │                   │
│              │  Progress: 68%           │                   │
│              └──────────────────────────┘                   │
│                                                              │
│  Processing Image 4 of 6...                                 │
│                                                              │
│  Detecting cracks...         ✅ Complete                     │
│  Analysing discolouration... ✅ Complete                     │
│  Fusing results...           ⏳ In progress                  │
│  Generating summary...       ⏳ Pending                      │
│                                                              │
│  ┌─────────────────────────────────────────┐                 │
│  │                                         │                 │
│  │         Image preview with              │                 │
│  │         overlay annotations             │                 │
│  │                                         │                 │
│  └─────────────────────────────────────────┘                 │
│                                                              │
│  Please wait, do not close this page...                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Components used:**
- `render_processing()` in `pages/processing.py`
- `InspectionEngine.run_full_analysis()` from `ai/inspection_engine.py`
- Progress bar from Streamlit

**Session state needed:**
- `inspection_step`: 4
- Full analysis result stored after completion

---

### Screen 6: New Inspection — Step 5 — Results (`pages/results.py`)

**Purpose:** Display comprehensive analysis results.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back          New Inspection — Results                   │
│  ██████████████████████████                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Damage   │ │Severity  │ │  Health  │ │Est. Cost │       │
│  │  23.5%   │ │  HIGH    │ │  Grade B │ │ INR 15K  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  Image Rankings (Most Damaged → Least)                      │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐               │
│  │ #1 │ │ #2 │ │ #3 │ │ #4 │ │ #5 │ │ #6 │               │
│  │CRIT│ │HIGH│ │MED │ │MED │ │LOW │ │OK  │               │
│  │45% │ │28% │ │19% │ │15% │ │ 8% │ │ 2% │               │
│  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘               │
│                                                              │
│  Key Findings                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 🚨 Critical: Structural crack — Wall B, 2.3mm wide     │   │
│  │ ⚠️  High: Water damage — Ceiling, east corner         │   │
│  │ ⚠️  High: Mould growth — Bathroom wall                │   │
│  │ ℹ️  Medium: Surface peeling — Balcony railing          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Repair Recommendations                                     │
│  • Fill and seal structural crack with epoxy               │
│  • Investigate water source, treat with anti-damp coating   │
│  • ...                                                      │
│                                                              │
│                                    [New Inspection]  [PDF]   │
└─────────────────────────────────────────────────────────────┘
```

**Components used:**
- `render_results()` in `pages/results.py`
- `FusedInspection` dataclass from `ai/fusion_engine.py`
- Image display with damage overlays

**Session state needed:**
- `inspection_step`: 5
- `analysis_result`: FusedInspection object
- `property_data`: dict
- `inspection_id`: string

---

### Screen 7: History (`pages/history.py`)

**Purpose:** Browse all past inspections.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Inspection History                          [New Inspection]│
├─────────────────────────────────────────────────────────────┤
│  🔍 Search...     [Type ▾] [Severity ▾] [Grade ▾]  [Reset] │
│                                                              │
│  Stats: 12 inspections | Avg health: 72 | 3 critical        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 🏠 123 Main Street, Bangalore                         │   │
│  │ INSP-abc123  │  2024-01-15  │  Grade B  │  HIGH       │   │
│  │ 5 images     │  ₹18,000 est  │  View Report           │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 🏢 45 Tech Park, Pune                                │   │
│  │ INSP-def456  │  2024-01-14  │  Grade A  │  MEDIUM     │   │
│  │ 12 images    │  ₹8,500 est   │  View Report           │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ ... (paginated)                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  [← Previous]  Page 1 of 3  [Next →]                        │
└─────────────────────────────────────────────────────────────┘
```

**Components used:**
- `render_history()` in `pages/history.py`
- `get_inspection_history()` from `database/repository.py`
- `get_history_stats()` from `database/repository.py`

**Session state needed:**
- `current_page`: "history"
- Filter state in local variables

---

### Screen 8: Reports (`pages/reports.py`)

**Purpose:** List all generated reports.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Reports                                    [New Inspection] │
├─────────────────────────────────────────────────────────────┤
│  [All] [Critical] [High] [Medium] [Low]                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Report: 123 Main Street Inspection                    │   │
│  │ Generated: 2024-01-15  │  Health: B (72/100)           │   │
│  │ Severity: HIGH  │  Damage: 23.5%  │  Cost: ₹15,000    │   │
│  │ [View Full Report]  [Download PDF]                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

**Components used:**
- `render_reports()` in `pages/reports.py`
- `list_reports()` from `database/repository.py`

---

### Screen 9: Report Detail (`pages/report.py`)

**Purpose:** Full report display with tabs.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back          Inspection Report — INSP-abc123             │
├─────────────────────────────────────────────────────────────┤
│  [Overview] [Findings] [Health] [Comparison] [Timeline]     │
│                                                              │
│  (Tab content changes based on selection)                    │
│                                                              │
│  Overview tab:                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Damage   │ │Severity  │ │  Health  │ │Est. Cost │       │
│  │  23.5%   │ │  HIGH    │ │  Grade B │ │ INR 15K  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  Executive Summary:                                          │
│  "The inspection reveals significant structural concerns..."  │
│                                                              │
│  Property Summary:                                           │
│  Residential building, 10 years old, RCC construction...     │
│                                                              │
│  [Export PDF]  [Print]                                       │
└─────────────────────────────────────────────────────────────┘
```

---

### Screen 10: Analytics (`pages/analytics.py`)

**Purpose:** Data visualisation for inspection trends.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Analytics                                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Damage Trend Over Time                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [Line chart: damage % over inspection dates]         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Severity Distribution    │  Most Common Damage Types        │
│  ┌──────────────────┐    │  ┌──────────────────────────┐    │
│  │   [Pie chart]    │    │  │  [Bar chart]             │    │
│  └──────────────────┘    │  └──────────────────────────┘    │
│                                                              │
│  Cost Estimation Trends                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [Bar chart: estimated cost per inspection]           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

### Screen 11: Settings (`pages/settings.py`)

**Purpose:** Configure application behaviour.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Settings                                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  AI Engine Configuration                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Analysis Engine:                                      │   │
│  │ [●] OpenCV (Classical CV)                             │   │
│  │ [ ] Gemini Vision API (requires API key)              │   │
│  │                                                       │   │
│  │ Confidence Threshold: [█████████░] 85%                 │   │
│  │ Severity Sensitivity:   [██████░░░░] Medium            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Data Management                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ [Clear All Inspection Data]                           │   │
│  │ [Export Database]                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  About                                                      │
│  InspectAI v1.0.0  │  Built with Streamlit + OpenCV         │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. Navigation Flow

### Primary Navigation (Sidebar)

```
┌──────────────────────────────┐
│  🏠 InspectAI                │  ← App title + logo
│                              │
│  📊 Dashboard                 │  ← Home/overview
│  🔍 New Inspection            │  ← Starts wizard (Step 1)
│  📋 History                   │  ← Past inspections list
│  📄 Reports                   │  ← Generated reports list
│  📈 Analytics                 │  ← Charts and trends
│  ⚙️  Settings                  │  ← Configuration
│  ℹ️  About                     │  ← App info
└──────────────────────────────┘
```

### Wizard Flow (5 Steps)

```
Dashboard
  │
  ▼
[New Inspection] button clicked
  │
  ▼
Step 1: Property Details
  │  (user fills form, clicks Continue)
  ▼
Step 2: Upload Images
  │  (user uploads images, clicks Continue)
  ▼
Step 3: Review
  │  (user reviews/removes images, clicks Analyze)
  ▼
Step 4: Processing (full-screen, no sidebar)
  │  (AI runs, progress shown, auto-advances)
  ▼
Step 5: Results
  │  (user reviews results)
  ▼
  ├─→ [New Inspection] → back to Step 1
  ├─→ [View History] → History page
  ├─→ [Download PDF] → exports report
  └─→ [View Full Report] → Report Detail page
```

### Cross-Page Navigation

```
Dashboard
  ├─→ New Inspection → Wizard → Results → Report Detail
  ├─→ History → (click inspection) → Report Detail
  ├─→ Reports → (click report) → Report Detail
  ├─→ Analytics
  ├─→ Settings
  └─→ About

Any page
  └─→ Sidebar → jump to any page
```

### Navigation State Machine

```
States: DASHBOARD | STEP_1 | STEP_2 | STEP_3 | PROCESSING | RESULTS
         | HISTORY | REPORTS | REPORT_DETAIL | ANALYTICS | SETTINGS | ABOUT

Valid transitions:
  DASHBOARD       → STEP_1 (new inspection)
  DASHBOARD       → HISTORY
  DASHBOARD       → REPORTS
  DASHBOARD       → ANALYTICS
  DASHBOARD       → SETTINGS
  DASHBOARD       → ABOUT
  
  STEP_1          → STEP_2 (continue)
  STEP_1          → DASHBOARD (cancel)
  
  STEP_2          → STEP_3 (continue)
  STEP_2          → STEP_1 (back)
  
  STEP_3          → PROCESSING (analyze)
  STEP_3          → STEP_2 (back)
  
  PROCESSING      → RESULTS (auto on completion)
  PROCESSING      → DASHBOARD (cancel mid-process)
  
  RESULTS         → STEP_1 (new inspection)
  RESULTS         → REPORT_DETAIL
  RESULTS         → HISTORY
  
  HISTORY         → REPORT_DETAIL (click inspection)
  HISTORY         → DASHBOARD
  
  REPORTS         → REPORT_DETAIL (click report)
  REPORTS         → DASHBOARD
  
  REPORT_DETAIL   → HISTORY
  REPORT_DETAIL   → DASHBOARD
  REPORT_DETAIL   → REPORTS
```

---

## 12. Folder Structure

```
InspectAI/
│
├── README.md                          # Project overview, setup, features
├── requirements.txt                   # Python dependencies
├── .env.example                       # Template for environment variables
├── .gitignore                         # Git ignore rules
├── LICENSE                            # MIT License
├── PRD.md                             # This document
│
├── streamlit_app/                     # Main application package
│   ├── __init__.py                    # Package init
│   │
│   ├── app.py                         # Entry point — page routing & config
│   │
│   ├── database/                      # Data persistence layer
│   │   ├── __init__.py
│   │   ├── schema.py                  # SQL DDL statements (table definitions)
│   │   ├── database.py                # Connection management (get_connection, init_db)
│   │   └── repository.py              # Data-access functions (CRUD operations)
│   │
│   ├── ai/                            # AI/ML engine
│   │   ├── __init__.py
│   │   ├── image_validator.py         # Pre-flight image validation
│   │   ├── opencv_engine.py           # Classical CV detection pipeline
│   │   ├── gemini_engine.py           # Gemini Vision API integration (optional)
│   │   ├── inspection_engine.py       # Orchestrator — runs full pipeline
│   │   ├── fusion_engine.py           # Multi-engine result fusion
│   │   └── cost_estimator.py          # Repair cost estimation logic
│   │
│   ├── report/                        # Report generation
│   │   ├── __init__.py
│   │   ├── report_generator.py        # Assembles report data structures
│   │   ├── report_templates.py        # Text/template generation for each section
│   │   └── pdf_generator.py           # PDF export (ReportLab / FPDF2)
│   │
│   ├── components/                    # Reusable UI components
│   │   ├── __init__.py
│   │   └── ui_components.py            # inject_custom_css, render_sidebar, etc.
│   │
│   ├── pages/                         # Page render functions
│   │   ├── __init__.py
│   │   ├── dashboard.py               # Dashboard page
│   │   ├── new_inspection.py          # Step 1: Property details form
│   │   ├── upload.py                  # Step 2: Image upload
│   │   ├── review.py                  # Step 3: Review images
│   │   ├── processing.py              # Step 4: Processing/progress
│   │   ├── results.py                 # Step 5: Results display
│   │   ├── history.py                 # Inspection history
│   │   ├── reports.py                 # Reports list
│   │   ├── report.py                  # Single report detail view
│   │   ├── analytics.py               # Analytics dashboard
│   │   ├── settings.py                # Settings page
│   │   └── about.py                   # About page
│   │
│   ├── utils/                         # Utility modules
│   │   ├── __init__.py
│   │   ├── session_manager.py         # Session state init, navigation helpers
│   │   ├── image_helpers.py           # Image processing utilities
│   │   ├── export_manager.py          # PDF/text export utilities
│   │   └── validators.py              # Form validation helpers
│   │
│   ├── styles/                        # CSS and styling
│   │   ├── custom.css                 # Main custom styles
│   │   └── theme.css                  # Colour scheme / theme
│   │
│   └── uploads/                       # Temporary image storage
│       └── (auto-created, .gitignored)
│
├── assets/                            # Static assets
│   ├── logo.svg                       # App logo
│   ├── favicon.png                    # Browser favicon
│   └── sample_images/                 # Sample images for demo/testing
│       ├── crack_wall_1.jpg
│       ├── water_damage_1.jpg
│       └── ...
│
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md                # Architecture overview
│   ├── AI_PIPELINE.md                 # AI engine documentation
│   └── API_REFERENCE.md               # Internal API reference
│
└── tests/                             # Unit tests
    ├── __init__.py
    ├── test_validators.py
    ├── test_image_processor.py
    ├── test_repository.py
    └── test_fusion.py
```

---

## 13. Python Module Structure

### Module Dependency Graph

```
app.py
  ├── components/ui_components.py
  │     └── styles/custom.css
  │
  ├── pages/*.py
  │     ├── database/repository.py
  │     │     └── database/database.py
  │     │     └── database/schema.py
  │     │
  │     ├── ai/inspection_engine.py
  │     │     ├── ai/image_validator.py
  │     │     ├── ai/opencv_engine.py
  │     │     ├── ai/gemini_engine.py (optional)
  │     │     ├── ai/fusion_engine.py
  │     │     └── ai/cost_estimator.py
  │     │
  │     ├── report/report_generator.py
  │     │     ├── report/report_templates.py
  │     │     └── report/pdf_generator.py
  │     │
  │     └── utils/session_manager.py
  │           ├── utils/image_helpers.py
  │           └── utils/validators.py
  │
  └── utils/session_manager.py
```

### Module Responsibilities

| Module | Responsibility | Dependencies |
|---|---|---|
| `app.py` | Entry point, page routing, session init | All pages, components, utils |
| `database/schema.py` | SQL DDL constants | None |
| `database/database.py` | SQLite connection management | sqlite3 (stdlib) |
| `database/repository.py` | All database CRUD operations | database.py, schema.py, json |
| `ai/image_validator.py` | Pre-flight image validation | OpenCV, NumPy, Pillow |
| `ai/opencv_engine.py` | Classical CV detection pipeline | OpenCV, NumPy |
| `ai/gemini_engine.py` | Gemini Vision API wrapper | google.generativeai (optional) |
| `ai/inspection_engine.py` | Full pipeline orchestrator | All AI modules |
| `ai/fusion_engine.py` | Multi-engine result merging | All AI modules |
| `ai/cost_estimator.py` | Repair cost estimation logic | None (pure Python) |
| `report/report_generator.py` | Assembles report data structures | ai/fusion_engine.py, database/repository.py |
| `report/report_templates.py` | Text generation for report sections | None (pure Python) |
| `report/pdf_generator.py` | PDF export | FPDF2 / ReportLab |
| `components/ui_components.py` | Shared UI elements | Streamlit |
| `pages/*.py` | Page render functions | Streamlit, database, AI, report, utils |
| `utils/session_manager.py` | Session state management | Streamlit |
| `utils/image_helpers.py` | Image loading/resizing/annotation | OpenCV, Pillow |
| `utils/validators.py` | Form and data validation | None (pure Python) |

---

## 14. Recommended Coding Architecture

### Architecture Pattern: Layered / Clean Architecture (Lightweight)

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│  (pages/*.py, components/ui_components.py)               │
│  - Streamlit pages, forms, charts, navigation            │
│  - NO business logic, ONLY rendering and user input      │
└────────────────────────┬────────────────────────────────┘
                         │ calls
┌────────────────────────▼────────────────────────────────┐
│                   SERVICE LAYER                          │
│  (ai/inspection_engine.py, report/report_generator.py)   │
│  - Orchestrates workflows                                │
│  - Combines data from multiple sources                   │
│  - Returns processed results to presentation             │
└──────────┬──────────────────────────┬────────────────────┘
           │                          │
┌──────────▼──────────┐   ┌──────────▼────────────────────┐
│   AI LAYER           │   │   DATA LAYER                  │
│  (ai/*.py)           │   │  (database/*.py)              │
│  - Image analysis    │   │  - SQLite operations          │
│  - Damage detection  │   │  - Repository pattern         │
│  - Fusion logic      │   │  - JSON serialization         │
│  - Cost estimation   │   │  - Schema management          │
└──────────────────────┘   └───────────────────────────────┘
```

### Key Architectural Rules

1. **No circular imports**: AI modules never import from pages. Pages import from AI.
2. **Repository pattern**: All DB access goes through `repository.py`. Pages never call `sqlite3` directly.
3. **Dataclasses for data transfer**: AI results are `@dataclass` objects. Serialization happens at the repository layer.
4. **Session state as the single source of truth**: During a wizard flow, session state holds all intermediate data. DB writes happen only on completion.
5. **Pure functions for business logic**: Cost estimation, severity classification, grade derivation are pure functions — easy to test.
6. **Optional imports**: Gemini API imports are wrapped in try/except. App works without it.

### Data Flow for a Single Inspection

```
User uploads images
    │
    ▼
Session state stores: uploaded_images list
    │
    ▼
User clicks "Analyze"
    │
    ▼
InspectionEngine.run_full_analysis(images)
    │
    ├──► image_validator.validate() → filter invalid images
    ├──► opencv_engine.analyze() → per-image CV results
    ├──► gemini_engine.analyze() → per-image LLM results (optional)
    ├──► fusion_engine.fuse() → merged per-image results
    ├──► fusion_engine.aggregate() → inspection-level summary
    └──► cost_estimator.estimate() → cost ranges
    │
    ▼
FusedInspection dataclass (all results in memory)
    │
    ▼
User views Results page (reads from session state)
    │
    ▼
User clicks "Save" / "Export"
    │
    ├──► repository.save_report() → writes to SQLite
    └──► pdf_generator.generate() → creates PDF file
```

---

## 15. Database Requirements

### Technology: SQLite (via stdlib `sqlite3`)

No external database server needed. SQLite is file-based, zero-configuration, and perfect for a single-user desktop app.

### Database File

- Location: `streamlit_app/data/inspectai.db` (auto-created on first run)
- Managed by `database/database.py`

### Schema

**4 tables + 1 migration tracking table:**

```
┌──────────────────┐       ┌──────────────────┐
│    properties     │       │   inspections    │
├──────────────────┤       ├──────────────────┤
│ property_id  PK  │──┐    │ inspection_id PK │
│ property_type    │  │    │ property_id  FK  │──┐
│ address          │  │    │ inspection_date  │  │
│ city             │  │    │ inspector_name   │  │
│ state            │  └───►│ weather_condition│  │
│ pincode          │       │ notes            │  │
│ year_built       │       │ status           │  │
│ area_sqft        │       │ total_images     │  │
│ floors           │       │ processing_time  │  │
│ construction_type│       │ created_at       │  │
│ inspector_name   │       └──────────────────┘  │
│ notes            │              │               │
│ created_at       │              │               │
│ updated_at       │              ▼               │
└──────────────────┘       ┌──────────────────┐  │
                            │ inspection_images│  │
                            ├──────────────────┤  │
                            │ image_id      PK │  │
                            │ inspection_id FK│──┘
                            │ file_name        │
                            │ file_path        │
                            │ file_size_kb     │
                            │ width_px         │
                            │ height_px        │
                            │ damage_pct       │
                            │ severity         │
                            │ confidence       │
                            │ damage_types     │
                            │ rank_order       │
                            │ created_at       │
                            └──────────────────┘

┌──────────────────┐
│     reports      │
├──────────────────┤
│ report_id      PK│
│ inspection_id FK │──┐ (UNIQUE — one report per inspection)
│ overall_damage_pct│  │
│ overall_confidence│  │
│ overall_severity │  │
│ overall_health_score││
│ overall_est_cost_min││
│ overall_est_cost_max││
│ findings_json    │  │
│ image_rankings_json││
│ executive_summary│  │
│ ... more JSON cols│  │
└──────────────────┘  │
         │            │
         ▼            ▼
    (references same inspection)
```

### Design Decisions

| Decision | Rationale |
|---|---|
| SQLite over PostgreSQL | No server needed, single-user app, file-based |
| No ORM (raw SQL) | Keeps dependencies minimal, SQLite3 is stdlib |
| UUIDs as primary keys | Globally unique, no collisions, prefixed (PROP-, INSP-, IMG-, RPT-) |
| JSON columns for complex data | Avoids N+1 table joins for nested report data. SQLite has native JSON support. |
| Foreign keys with CASCADE | Deleting a property auto-deletes all inspections, images, and reports |
| Indexed columns | `idx_inspections_property`, `idx_images_inspection`, `idx_reports_severity` for query performance |
| Migration tracking table | `schema_migrations` for versioned schema updates |
| No connection pooling | SQLite doesn't need it. Each operation opens/closes a connection. |

### Migration Strategy

- Schema version tracked in `schema_migrations` table
- `init_db()` applies all statements from `ALL_SCHEMA_STATEMENTS` with `IF NOT EXISTS`
- For future schema changes: add new `CREATE TABLE IF NOT EXISTS` or `ALTER TABLE` with version check

---

## 16. AI Workflow

### Overview

The AI workflow is a multi-stage pipeline that takes uploaded images and produces a comprehensive inspection report. It uses a **dual-engine** approach with a fusion layer.

```
                    ┌─────────────────────┐
                    │   Uploaded Images    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Image Validator    │
                    │  (pre-flight check) │
                    └──────────┬──────────┘
                               │ valid images
                    ┌──────────▼──────────┐
                    │  Per-Image Analysis  │
                    │  ┌───────┐ ┌──────┐ │
                    │  │OpenCV │ │Gemini│ │ (parallel)
                    │  │Engine │ │Engine│ │
                    │  └───┬───┘ └──┬──┘ │
                    │      └────┬───┘    │
                    │           ▼        │
                    │    Fusion Layer     │
                    │  (merge + resolve)  │
                    └──────────┬──────────┘
                               │ fused per-image results
                    ┌──────────▼──────────┐
                    │  Inspection Aggregate│
                    │  (combine all images)│
                    │  + Cost Estimation   │
                    │  + Summary Generation│
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  FusedInspection    │
                    │  (final result)      │
                    └─────────────────────┘
```

### Stage 1: Image Validation

**Module:** `ai/image_validator.py`

**Purpose:** Filter out unusable images before expensive analysis.

**Checks:**
1. **Format validation**: Must be JPG, PNG, or WEBP
2. **File size**: Must be > 10KB and < 20MB
3. **Minimum resolution**: At least 200x200 pixels
4. **Blur detection**: Laplacian variance check — reject images with variance < 100
5. **Brightness check**: Not too dark (mean brightness > 20) or too bright (mean < 235)
6. **Colour image**: Must have 3 channels (not grayscale)

**Output:** List of valid images with metadata, list of rejected images with reasons.

### Stage 2a: Classical CV Analysis (OpenCV Engine)

**Module:** `ai/opencv_engine.py`

**Purpose:** Detect damage using classical computer vision techniques. No ML model needed — runs fast, offline, no API keys.

**Pipeline per image:**

```
Input Image
    │
    ▼
Pre-processing
    ├── Resize to max 1024px (maintain aspect ratio)
    ├── Denoise (bilateral filter)
    ├── Contrast enhancement (CLAHE)
    └── Convert to grayscale for edge detection
    │
    ▼
Crack Detection
    ├── Canny edge detection
    ├── Morphological operations (close gaps)
    ├── Contour extraction
    ├── Filter by aspect ratio (long/thin = crack candidate)
    ├── Measure: length (pixels), width (pixels), count, density (% of image)
    └── Output: CrackReport(damage_pct, crack_count, avg_width_px, max_width_px)
    │
    ▼
Water Damage / Discolouration
    ├── Convert to HSV colour space
    ├── Detect brown/yellow/rust hues
    ├── Detect uniform discolouration patches
    ├── Measure: affected area (%), colour deviation score
    └── Output: DiscolourationReport(damage_pct, severity_hue, patch_count)
    │
    ▼
Surface Texture Analysis
    ├── Gabor filter bank (multiple orientations + frequencies)
    ├── Local Binary Pattern (LBP) analysis
    ├── Measure: roughness score, peeling score
    └── Output: TextureReport(roughness_score, peeling_score)
    │
    ▼
Structural Deformation (optional)
    ├── Perspective correction
    ├── Line detection (Hough transform) for corners/edges
    ├── Measure: deviation from expected geometry
    └── Output: DeformationReport(deviation_score)
    │
    ▼
OpenCVImageResult(damage_pct, severity, confidence, damage_types, measurements)
```

**Damage Type Classification (from OpenCV results):**

| Damage Type | Detection Method | Key Metrics |
|---|---|---|
| Crack | Canny + Contours | Length, width, density |
| Water Damage | HSV analysis | Brown/yellow area %, deviation score |
| Mould | Colour + texture | Dark spot count, texture roughness |
| Surface Peeling | LBP + texture | Peeling score, affected area |
| Structural Deformation | Line detection | Geometric deviation |
| Efflorescence | White salt detection | White area %, crystalline pattern |
| Rust Staining | Red-brown detection | Rust area % |

### Stage 2b: Gemini Vision Analysis (Optional)

**Module:** `ai/gemini_engine.py`

**Purpose:** Provide semantic, context-aware damage analysis using LLM vision capabilities.

**Prompt to Gemini:**
```
Analyze this property image for signs of damage or deterioration.
Identify:
1. Damage types visible (crack, water damage, mould, peeling, etc.)
2. Severity level (critical/high/medium/low/none)
3. Confidence in your assessment (0-100%)
4. Affected area estimate (percentage of image)
5. Possible causes
6. Recommended repair actions

Respond in JSON format.
```

**Output:** `GeminiImageResult(damage_types, severity, confidence, damage_pct, description, possible_causes, repair_suggestions)`

**Fallback:** If Gemini API is unavailable or returns an error, this stage is skipped and only OpenCV results are used.

### Stage 3: Fusion Engine

**Module:** `ai/fusion_engine.py`

**Purpose:** Combine results from OpenCV and Gemini (if available) into a unified assessment.

**Fusion Strategy:**

```
For each image:
    opencv_result = OpenCV result
    gemini_result = Gemini result (or None)
    
    if gemini_result is None:
        fused = opencv_result  (use as-is)
    else:
        # Weighted combination
        # OpenCV is trusted for: crack detection, measurements, area %
        # Gemini is trusted for: damage type naming, semantic severity
        
        fused.severity = gemini_result.severity  # Gemini's severity
        fused.confidence = weighted_avg(
            opencv.confidence * 0.6,  # CV is more objective
            gemini.confidence * 0.4   # LLM adds context
        )
        fused.damage_pct = max(opencv.damage_pct, gemini.damage_pct)
        fused.damage_types = merge(opencv.damage_types, gemini.damage_types)
        fused.measurements = opencv.measurements  # CV provides measurements
        fused.description = gemini.description    # LLM provides description
```

**Conflict Resolution Rules:**
1. If OpenCV says "no crack" but Gemini says "crack visible" → trust Gemini for type, OpenCV for measurement (if any)
2. If severity differs → take the higher severity (conservative approach)
3. If confidence differs → weighted average with OpenCV at 0.6 weight
4. If damage types differ → union of both lists

### Stage 4: Inspection Aggregation

**Module:** `ai/fusion_engine.py`

**Purpose:** Combine all per-image results into an inspection-level summary.

**Aggregation Logic:**

```
Input: List of FusedImageResult (one per image)

1. Overall Damage %:
   overall_damage_pct = average of all image damage_pct values
                       (weighted by image area if available)

2. Overall Severity:
   overall_severity = worst severity across all images
   (critical > high > medium > low > none)

3. Overall Confidence:
   overall_confidence = average of all image confidence values

4. Health Score:
   health_score = 100 - (overall_damage_pct * 2) - severity_penalty
   where severity_penalty:
       critical: -30, high: -20, medium: -10, low: -5

5. Priority Findings:
   Sort images by damage_pct descending
   Take top 3 as "priority findings"
   For each: generate description, possible causes, repair steps

6. Repair Cost Estimation:
   For each damage type, estimate cost per sqft
   Total = sum of (damage_area * cost_per_sqft)
   Provide min/max range

7. Maintenance Tips:
   Based on damage types found
   Generate relevant tips (e.g., if cracks found: "Monitor cracks for expansion")
```

### Stage 5: Report Assembly

**Module:** `report/report_generator.py`, `report/report_templates.py`

**Purpose:** Convert `FusedInspection` dataclass into human-readable report sections.

**Sections generated:**
1. Executive summary (3-4 sentences)
2. Property summary (from property metadata)
3. Inspection details (date, inspector, images count)
4. Findings table (severity, confidence, type, cost, repair steps)
5. Image rankings (sorted by damage)
6. Repair recommendations (per finding)
7. Maintenance tips
8. Health report (grade, breakdown)
9. Comparison report (if previous inspection exists)
10. Timeline (chronological findings)

---

## 17. Image Processing Workflow

### Complete Flow from Upload to Analysis

```
1. UPLOAD (pages/upload.py)
   ├── User selects/drag-drops files
   ├── Streamlit file_uploader returns UploadedFile objects
   └── Store in session_state["uploaded_images"] as list of:
       {
           "name": "photo1.jpg",
           "data": bytes,
           "type": "image/jpeg",
           "size_kb": 1250
       }

2. VALIDATION (ai/image_validator.py)
   ├── Load image with Pillow
   ├── Check format, size, dimensions
   ├── Convert to numpy array for OpenCV
   ├── Laplacian variance for blur detection
   ├── Brightness check
   └── Return: valid_images[], rejected_images[] with reasons

3. PRE-PROCESSING (utils/image_helpers.py)
   ├── Load with OpenCV (cv2.imdecode)
   ├── Resize to max 1024px (maintain aspect ratio)
   ├── Denoise (fastNlMeansDenoisingColored or bilateralFilter)
   ├── CLAHE contrast enhancement
   └── Return: processed_images[] (numpy arrays)

4. PER-IMAGE ANALYSIS (ai/opencv_engine.py)
   └── For each processed image:
       ├── Crack detection (Canny + contours)
       ├── Discolouration detection (HSV analysis)
       ├── Texture analysis (Gabor + LBP)
       └── Return: OpenCVImageResult

5. OPTIONAL: GEMINI ANALYSIS (ai/gemini_engine.py)
   └── For each processed image:
       ├── Encode image to base64
       ├── Send to Gemini Vision API with prompt
       ├── Parse JSON response
       └── Return: GeminiImageResult

6. FUSION (ai/fusion_engine.py)
   └── For each image pair:
       ├── Merge OpenCV + Gemini results
       ├── Apply conflict resolution rules
       └── Return: FusedImageResult

7. ANNOTATION (utils/image_helpers.py)
   ├── For each FusedImageResult:
   │   ├── Draw bounding boxes around damage regions
   │   ├── Add severity label and confidence score
   │   ├── Colour code: red (critical), orange (high), yellow (medium)
   │   └── Return: annotated_image (numpy array, then bytes for display)
   └── Store annotated images for display in results page

8. AGGREGATION (ai/fusion_engine.py)
   ├── Combine all FusedImageResults into FusedInspection
   ├── Calculate overall metrics
   ├── Generate findings, tips, recommendations
   └── Return: FusedInspection dataclass

9. STORAGE (database/repository.py)
   ├── Save inspection record
   ├── Save each image record with results
   ├── Save full report
   └── All in a single transaction
```

### Image Annotation Specifications

```
Annotation overlay on each image:
- Red rectangles around detected cracks
- Orange highlight over water-damaged areas
- Yellow overlay for surface peeling
- Text label: "CRITICAL: Crack 2.3mm" or "HIGH: Water damage 15%"
- Confidence badge: "92% confidence"
- Legend in corner: damage type colour key

Annotation format:
- OpenCV drawing: cv2.rectangle(), cv2.putText()
- Save as JPEG bytes for Streamlit display
- Also save annotated version for PDF report
```

---

## 18. Report Generation Workflow

### Report Data Assembly

```
Input: FusedInspection dataclass + Property data + Inspection data

Step 1: Generate executive_summary
    Template: "The inspection of {property_type} at {address} reveals...
              {overall_damage_pct}% damage across {total_images} images.
              Overall health score: {health_score}/100 ({grade}).
              {critical_count} critical issues identified..."
    
Step 2: Generate property_summary
    From property metadata: type, year_built, area, floors, construction_type
    
Step 3: Generate findings list
    For each priority finding:
        {damage_type}, {severity}, {confidence}%, {damage_pct}%
        Possible causes: [...]
        Repair steps: [...]
        Estimated cost: INR {min} – {max}
        Recommended professional: {yes/no and type}

Step 4: Generate image_rankings
    Sort images by damage_pct descending
    Format: rank, file_name, damage_pct, severity, confidence

Step 5: Generate maintenance_tips
    Based on damage types found:
        cracks → "Monitor for expansion. Consider epoxy filling."
        water_damage → "Fix water source. Apply anti-damp coating."
        mould → "Improve ventilation. Use mould-resistant paint."
        peeling → "Scrape and repaint with quality exterior paint."

Step 6: Generate health_report
    Health grade (A+ to D)
    Component scores (walls, ceiling, structural)
    Risk assessment
    Recommendations

Step 7: Generate comparison_report (if previous exists)
    Before/after damage percentages
    Delta (positive = deterioration, negative = improvement)
    New damages since last inspection
    Critical changes

Step 8: Generate timeline
    Chronological list of all findings across inspections
    Progression markers
```

### Report Output Formats

| Format | Module | Use Case |
|---|---|---|
| Structured dict | `report_generator.py` | In-app display |
| HTML (Streamlit) | Pages render directly | Interactive viewing |
| PDF | `pdf_generator.py` | Export, sharing, printing |
| JSON | `repository.py` | Database storage |

### PDF Report Structure

```
Page 1: Cover
  - InspectAI logo
  - "Property Inspection Report"
  - Property address, date, inspector
  - Overall health grade with colour badge
  - Summary stats (damage %, severity, cost estimate)

Page 2: Executive Summary
  - AI-generated summary paragraph
  - Key findings at a glance (table)
  - Health score with gauge/meter

Pages 3-N: Detailed Findings
  - For each finding:
    - Damage type with severity badge
    - Affected images with thumbnails
    - Measurements (crack width, area %, etc.)
    - Possible causes
    - Repair recommendations
    - Cost estimate

Final Page: Recommendations & Signature
  - Maintenance tips
  - Recommended timeline for next inspection
  - Disclaimer (AI-assisted, consult professional for critical issues)
```

---

## 19. Development Roadmap

### Phase 0: Foundation (Weeks 1–2)

**Goal:** Set up project structure and core infrastructure.

- [x] Create project structure
- [x] Set up Streamlit app with routing
- [x] Implement SQLite database layer (schema, connection, repository)
- [x] Create sidebar navigation component
- [x] Implement custom CSS theming
- [x] Session state management
- [x] Image upload component with validation

### Phase 1: AI Core (Weeks 3–4)

**Goal:** Build the AI analysis pipeline.

- [x] Image validator (format, size, blur, brightness)
- [x] OpenCV engine — crack detection
- [x] OpenCV engine — water damage detection
- [x] OpenCV engine — surface texture analysis
- [x] Per-image result dataclasses
- [ ] Gemini Vision API integration
- [x] Fusion engine for combining results
- [x] Cost estimation module

### Phase 2: Wizard & Results (Weeks 5–6)

**Goal:** Complete the 5-step inspection wizard.

- [x] Step 1: Property details form
- [x] Step 2: Image upload with drag-and-drop
- [x] Step 3: Image review with removal
- [x] Step 4: Processing screen with progress
- [x] Step 5: Results display with rankings
- [x] Image annotation overlay
- [x] Findings display with severity badges

### Phase 3: Reports & History (Weeks 7–8)

**Goal:** Persistent data and report generation.

- [x] Inspection history page with search/filter/sort
- [x] Reports list page
- [x] Report detail view with tabs
- [ ] PDF export (FPDF2)
- [ ] Report templates for each section

### Phase 4: Polish & Analytics (Weeks 9–10)

**Goal:** Make it portfolio-worthy.

- [ ] Analytics dashboard with charts
- [ ] Settings page with AI engine toggle
- [ ] About page
- [ ] Error handling and user-friendly messages
- [ ] Loading states and animations
- [ ] Demo data / sample images
- [ ] README with screenshots and demo GIF
- [ ] GitHub repository cleanup

---

## 20. GitHub Milestone Roadmap

### Milestone 1: Foundation (Current)

```
✅ Project structure created
✅ Database layer (schema, connection, repository)
✅ Basic routing and navigation
✅ Custom CSS theming
✅ Session state management
✅ Image upload component
📋 Goal: Runnable app with navigation and empty dashboard
```

### Milestone 2: AI Pipeline

```
📋 Crack detection (OpenCV)
📋 Water damage detection (OpenCV)
📋 Surface texture analysis
📋 Image validator
📋 Per-image result dataclasses
📋 Fusion engine
📋 Cost estimation
📋 Goal: Upload images → get damage analysis results
```

### Milestone 3: Complete Wizard

```
📋 Property details form
📋 Image upload & review
📋 Processing screen with progress
📋 Results display
📋 Image annotations
📋 Goal: Full 5-step inspection flow works end-to-end
```

### Milestone 4: Reports & Persistence

```
📋 Inspection history page
📋 Report generation
📋 PDF export
📋 Reports list page
📋 Report detail view
📋 Goal: Complete inspection → persistent report → exportable PDF
```

### Milestone 5: Polish & Portfolio

```
📋 Analytics dashboard
📋 Settings page
📋 Demo data
📋 README with screenshots
📋 Error handling
📋 GitHub release (v1.0.0)
📋 Goal: Portfolio-ready, interview-ready project
```

### GitHub Labels

| Label | Colour | Purpose |
|---|---|---|
| `enhancement` | #a2eeef | New features |
| `bug` | #d73a4a | Bug fixes |
| `ai` | #7057ff | AI/ML related changes |
| `ui` | #0075ca | UI/UX changes |
| `database` | #008672 | Database/schema changes |
| `docs` | #0075ca | Documentation |
| `good first issue` | #7057ff | Beginner-friendly tasks |
| `help wanted` | #008672 | Needs community input |

### Branch Strategy

```
main          — stable, deployable code
dev           — integration branch (merge PRs here first)
feature/*     — feature branches (one per feature)
fix/*         — bug fix branches
```

### Commit Convention

```
feat: add crack detection in OpenCV engine
fix: handle empty image list in fusion engine
docs: update README with setup instructions
style: format CSS with consistent spacing
refactor: extract cost estimation to separate module
test: add unit tests for image validator
chore: update requirements.txt
```

---

## 21. MVP Features

The Minimum Viable Product includes only the features needed for a working, impressive demo.

### Must Have (MVP)

| Feature | Description |
|---|---|
| Dashboard | Stats cards + recent inspections |
| New Inspection Wizard | 5-step flow: property → upload → review → analyze → results |
| Property CRUD | Create, list, edit, delete properties |
| Image Upload | Multi-file upload with validation |
| OpenCV Analysis | Crack detection + water damage detection |
| Fusion Engine | Combine results into unified assessment |
| Results Display | Damage %, severity, health score, findings list |
| SQLite Persistence | All data saved locally |
| History Page | List of past inspections with search/filter |
| Report Generation | Structured report from analysis results |

### MVP Scope Summary

- **No Gemini API** — classical CV only
- **No PDF export** — display-only reports
- **No analytics dashboard** — basic charts if time permits
- **No settings page** — hardcoded sensible defaults
- **No user authentication** — single-user desktop app

**Estimated timeline:** 6–8 weeks at 10–15 hours/week

---

## 22. Version 2 Features

Features for the second iteration after MVP is complete.

| Feature | Description | Complexity |
|---|---|---|
| Gemini Vision Integration | Optional LLM-based image analysis | Medium |
| PDF Export | FPDF2-based professional PDF reports | Medium |
| Analytics Dashboard | Charts for damage trends, severity distribution | Medium |
| Comparison Reports | Before/after comparison between inspections | Medium |
| Settings Page | AI engine toggle, confidence threshold, cost model | Low |
| Improved CV Pipeline | Surface peeling, efflorescence, rust detection | Medium |
| Image Annotation | Draw bounding boxes and labels on damage regions | Medium |
| Demo Data | Sample images and pre-built demo inspections | Low |
| Better Error Handling | User-friendly messages, graceful fallbacks | Low |

**Estimated timeline:** 4–6 weeks

---

## 23. Version 3 Features

Features for the third iteration, closer to a real product.

| Feature | Description | Complexity |
|---|---|---|
| Supabase Backend | User auth, cloud storage, multi-device sync | High |
| YOLOv8 Integration | Object-level damage detection with bounding boxes | High |
| Map View | Geospatial display of properties on a map | Medium |
| Notification System | Re-inspection reminders, severity change alerts | Medium |
| Mobile PWA | Responsive design, camera capture, offline mode | High |
| Multi-language Support | English + Hindi + regional languages | Medium |
| Team Collaboration | Shared inspections, role-based access | High |
| Third-party Integrations | Google Docs, WhatsApp, email sharing | Medium |
| Advanced AI Models | Custom trained model on property damage dataset | High |

**Estimated timeline:** 8–12 weeks (if pursued)

---

## 24. Interview Value of Each Feature

### How to Talk About Each Feature in Interviews

| Feature | What to Say in Interviews |
|---|---|
| **SQLite Database** | "I designed a relational schema with 4 normalized tables and foreign key constraints. I used the repository pattern to keep database logic separate from business logic. The schema supports cascade deletes and has indexed columns for query performance." |
| **Classical CV Pipeline** | "I built a computer vision pipeline using OpenCV that detects cracks via Canny edge detection and contour analysis, water damage via HSV colour space analysis, and surface texture via Gabor filters and LBP. No pre-trained models needed — pure signal processing." |
| **Multi-Engine Fusion** | "I designed a dual-engine architecture where classical CV and an optional LLM vision model run in parallel. A fusion layer resolves conflicts using weighted confidence scoring. OpenCV gets 60% weight for objectivity, Gemini gets 40% for semantic context." |
| **Session State Management** | "I built a state machine for the 5-step inspection wizard using Streamlit's session state. The wizard persists data across page reruns and supports back-navigation without data loss." |
| **Report Generation** | "I designed a report generation system that converts structured analysis results into human-readable reports. Reports include executive summaries, findings tables, health grades, cost estimates, and maintenance tips — all generated programmatically from the AI results." |
| **History with Search/Filter** | "I built a complex joined query across 3 tables (properties, inspections, reports) with full-text search, multi-criteria filtering, and sorting. The query derives severity counts and grade letters from JSON columns." |
| **Cost Estimation** | "I built a cost estimation module that maps damage types to per-square-foot repair costs in INR. It provides min/max ranges based on material quality and labour estimates." |
| **Image Validation** | "I implemented pre-flight image validation checking format, resolution, file size, blur (Laplacian variance), and brightness. This prevents wasting compute on unusable images." |
| **Dual CV + LLM Architecture** | "I architected a hybrid AI system because classical CV excels at geometric measurements (crack width, area %) but lacks semantic understanding. LLM vision adds context (damage naming, cause analysis). The fusion layer combines both for the best of both worlds." |

### Key Technical Talking Points

1. **No ML models required**: "The core AI runs on classical CV — no GPU, no training data, no cloud API needed. This makes it truly offline and accessible."
2. **Graceful degradation**: "If any component fails (OpenCV, Gemini, PDF library), the app degrades gracefully. Users always get some result."
3. **Practical constraints**: "I didn't use a deep learning model because (a) I don't have labelled training data, (b) the user needs offline capability, (c) classical CV achieves 70–80% of what a CNN can do for this domain."
4. **Architecture decisions**: "I chose raw SQL over an ORM because SQLite is the stdlib and an ORM would add unnecessary abstraction. The repository pattern keeps the data layer clean without being over-engineered."
5. **Fusion strategy**: "The fusion layer is the most interesting part. It resolves disagreements between two AI engines using domain-specific rules — higher severity always wins, OpenCV wins on measurements, Gemini wins on semantic labels."

---

## 25. Resume Value

### How to Present This Project on a Resume

**Project Title:** InspectAI — AI-Powered Property Inspection Platform

**One-line description:**
> Full-stack AI application that analyses property images using classical computer vision to detect structural damage, estimate repair costs, and generate professional inspection reports.

**Bullet points for resume:**

```
• Designed and built an AI-powered property inspection platform using Python, 
  Streamlit, and OpenCV — analyses uploaded building images to detect cracks, 
  water damage, and surface deterioration with severity classification

• Engineered a dual-engine AI pipeline combining classical CV (Canny edge 
  detection, HSV colour analysis, Gabor filters) with optional Gemini Vision 
  API integration, fused via a confidence-weighted merging layer

• Architected a SQLite-backed data layer with 4 normalized tables, repository 
  pattern, and JSON columns for complex nested report data — handles full 
  inspection lifecycle from property creation to report generation

• Built a 5-step inspection wizard with session state management, image 
  validation, real-time progress tracking, and comprehensive results display 
  with severity badges and damage annotations

• Implemented report generation system producing structured findings, health 
  grades, cost estimates in INR, repair recommendations, and maintenance tips
  from AI analysis results

• Developed inspection history with multi-criteria search, filtering, sorting, 
  and severity aggregation across joined property-inspection-report queries
```

**Technologies section:**
```
Python, Streamlit, OpenCV, NumPy, Pillow, SQLite, 
Gemini Vision API (optional), FPDF2 (optional)
```

### What Recruiters/Interviewers Notice

| Aspect | Why It Impresses |
|---|---|
| **Full-stack thinking** | Not just AI — complete product with UI, data layer, reports |
| **Practical AI** | Classical CV, not just calling an API. Shows understanding of how CV works. |
| **Architecture** | Clean separation of concerns, repository pattern, dataclass usage |
| **Real-world applicability** | Solves an actual problem with real users (homeowners, inspectors) |
| **Completeness** | From upload to PDF export — end-to-end workflow |
| **Honest tech choices** | Uses the right tool for each job — no over-engineering |
| **Portfolio-ready** | Professional UI, real data flow, impressive demo |

### Resume Placement

- **Students (0–2 yrs):** Featured project at the top of projects section
- **Internship applications:** Primary project to discuss in technical interviews
- **AI/ML roles:** Emphasise the CV pipeline, fusion architecture, and data handling
- **Full-stack roles:** Emphasise the complete product architecture and UI

---

## 26. What Should NOT Be Added

To keep the project practical, understandable, and impressive — not overwhelming.

### Do NOT Add

| Feature | Why NOT |
|---|---|
| **Docker / Docker Compose** | Overkill for a single-user desktop app. Adds complexity without value. |
| **Kubernetes / Helm** | Zero relevance. This is not a cloud service. |
| **Microservices** | A single Streamlit app with ~15 modules is already well-structured. Splitting into services would make local development painful. |
| **Kafka / RabbitMQ / Redis** | No message queue needed. No caching layer needed. No pub/sub. |
| **AWS / GCP / Azure** | The app runs locally. Cloud deployment is unnecessary overhead. |
| **React / Next.js frontend** | Streamlit IS the frontend. Adding a separate frontend framework doubles the codebase for no benefit. |
| **FastAPI / Flask backend** | Streamlit handles both backend logic and frontend rendering. Adding a separate API server is unnecessary. |
| **PostgreSQL / MySQL** | SQLite is perfect. A separate database server is setup overhead. |
| **ORM (SQLAlchemy / Django ORM)** | Raw SQL with the stdlib `sqlite3` is simpler and more educational. |
| **pytest / unittest (extensive)** | Add a few unit tests for critical functions. Don't spend 30% of the project on testing infrastructure. |
| **Celery / Task queues** | Analysis runs synchronously in Streamlit. A task queue is unnecessary. |
| **Jupyter notebooks** | This is an application, not research. Notebooks don't ship. |
| **GraphQL** | REST is fine. But actually, there's no API — it's all in-process. |
| **TypeScript / JSX** | No JavaScript needed. |
| **Mobile app (Flutter / React Native)** | Streamlit works on mobile browsers. A native app is unnecessary. |
| **Authentication system** | Single-user desktop app. No login needed for MVP. |
| **Payment integration** | Not a commercial product. |
| **Complex CI/CD** | Maybe a simple GitHub Actions for linting. Nothing more. |
| **Swagger / OpenAPI docs** | No REST API to document. |
| **Load balancers / CDN** | Single user, local app. |
| **Custom neural network training** | The student doesn't have labelled data or GPU resources. Classical CV is the right choice. |

### Instead, Focus On

| Priority | Focus Area |
|---|---|
| P0 | Making the existing code clean, well-documented, and working |
| P0 | Completing the OpenCV analysis pipeline |
| P0 | Getting the 5-step wizard working end-to-end |
| P1 | PDF report export |
| P1 | Analytics dashboard |
| P1 | Polishing the UI |
| P2 | Gemini Vision integration |
| P2 | Demo data and README |
| P2 | Unit tests for key functions |

### The "Too Much" Threshold

If adding a feature requires:
- More than 3 new dependencies
- More than 500 lines of new code
- External infrastructure (servers, databases, APIs)
- Knowledge the developer doesn't have yet

**Then it's probably too much for this project.** The goal is a portfolio piece that demonstrates solid engineering, not a production system.

---

## Appendix A: Current Codebase Status

### Completed Modules

| Module | Status | Notes |
|---|---|---|
| `database/schema.py` | ✅ Complete | 4 tables + migration tracking + indexes |
| `database/database.py` | ✅ Complete | Connection management, thread-local connections |
| `database/repository.py` | ✅ Complete | Full CRUD for all entities, JSON serialization, complex queries |
| `ai/__init__.py` | ✅ Complete | Module exports |
| `app.py` | ✅ Partial | Routing, session init, sidebar setup |
| `components/ui_components.py` | ✅ Partial | CSS injection, sidebar rendering |
| `utils/session_manager.py` | ✅ Partial | Session state init, navigation helpers |
| `pages/dashboard.py` | ✅ Partial | Basic dashboard rendering |
| `pages/new_inspection.py` | ✅ Partial | Property details form |
| `pages/upload.py` | ✅ Partial | Image upload UI |
| `pages/review.py` | ✅ Partial | Image review grid |
| `pages/processing.py` | ✅ Partial | Processing screen |
| `pages/results.py` | ✅ Partial | Results display |
| `pages/history.py` | ✅ Partial | History list with search/filter |
| `pages/reports.py` | ✅ Partial | Reports list |
| `pages/report.py` | ✅ Partial | Report detail view |
| `pages/analytics.py` | ✅ Partial | Analytics page |
| `pages/settings.py` | ✅ Partial | Settings page |
| `pages/about.py` | ✅ Partial | About page |

### Remaining Work

| Priority | Task | Module |
|---|---|---|
| P0 | Complete OpenCV engine (crack, water damage, texture) | `ai/opencv_engine.py` |
| P0 | Complete image validator | `ai/image_validator.py` |
| P0 | Complete fusion engine | `ai/fusion_engine.py` |
| P0 | Complete inspection engine orchestrator | `ai/inspection_engine.py` |
| P0 | Complete cost estimator | `ai/cost_estimator.py` |
| P1 | Complete report generator | `report/report_generator.py` |
| P1 | Complete report templates | `report/report_templates.py` |
| P1 | PDF export (FPDF2) | `report/pdf_generator.py` |
| P1 | Wire all pages to real data | `pages/*.py` |
| P1 | Image annotation overlay | `utils/image_helpers.py` |
| P1 | Error handling throughout | All modules |
| P2 | Gemini Vision integration | `ai/gemini_engine.py` |
| P2 | Unit tests | `tests/` |
| P2 | Demo data | `assets/sample_images/` |
| P2 | README with screenshots | Root |

---

## Appendix B: Technology Justification

| Technology | Why Chosen | Why NOT Alternatives |
|---|---|---|
| **Python** | AI/ML ecosystem, CV libraries, student's primary language | JavaScript (no CV ecosystem), Java (too verbose) |
| **Streamlit** | Rapid prototyping, pure Python, built-in widgets, fast to build | Flask (too much boilerplate), React (separate frontend needed), Gradio (less flexible) |
| **OpenCV** | Industry standard for CV, classical techniques, no GPU needed | scikit-image (less documentation), PIL-only (no edge detection) |
| **SQLite** | File-based, zero config, stdlib, perfect for single-user | PostgreSQL (overkill), JSON files (no queries, no relations) |
| **FPDF2** | Pure Python PDF generation, lightweight | ReportLab (more complex), WeasyPrint (needs external deps) |
| **Gemini Vision** (optional) | Free tier available, good vision model, easy API | GPT-4 Vision (paid), Claude Vision (paid) |
| **NumPy** | Array operations for CV, stdlib-adjacent | Pure Python (too slow for image processing) |

---

*End of Product Requirement Document*
