# Changelog

All notable changes to InspectAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-16

### Added
- Initial public release
- 5-step inspection wizard (Property Details → Upload → Review → Processing → Results)
- AI-powered damage detection using OpenCV contour analysis
- Semantic damage classification using Google Gemini 1.5 Pro
- Property health scoring with grade badges (A+ to D)
- Risk assessment engine with composite scoring
- Executive summary generation
- Severity-ranked finding cards with damage overlays
- Repair timeline (Immediate / 7 Days / 30 Days / Future Monitoring)
- Inspection checklist with category mapping
- PDF report export via ReportLab
- Multi-inspection comparison with trend analysis
- Analytics dashboard with history and statistics
- Batch image processing with retry logic
- Image validation (format, size, resolution)
- Image optimization (auto-downsampling to 1024px)
- Session state management
- Performance tracking with stage timing
- Custom exception hierarchy
- Structured logging

### Technical
- Python 3.10+ with type hints throughout
- Streamlit 1.55 frontend
- SQLite persistence layer with repository pattern
- Frozen dataclass models for immutability
- 322 passing tests (pytest) covering unit and integration tests
- Custom CSS styling

## [0.9.0] — 2026-07-01

### Added
- Beta release with core AI pipeline
- Gemini Vision integration
- OpenCV damage detection
- Basic report generation
- Internal testing

## [0.1.0] — 2026-06-15

### Added
- Project initialization
- Core module structure
- Image validation utilities
- Basic Streamlit UI scaffolding
