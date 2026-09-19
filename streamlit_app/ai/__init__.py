"""InspectAI — AI Inspection Engine.

Modules:
    image_validator    — Pre-flight validation for uploaded images.
    opencv_engine      — Classical CV pipeline (preprocess, edges, contours).
    gemini_engine      — Gemini Vision API integration (semantic analysis).
    inspection_engine  — Orchestrates the full pipeline and merges results.
    measurement_engine — Professional damage measurement & annotation.
    fusion_engine      — Multi-image fusion and deduplication.
    health_engine      — Property health scoring.
    comparison_engine  — Inspection vs. reference comparison.
    repair_planner     — Actionable repair timelines.
"""

__all__ = [
    "image_validator",
    "opencv_engine",
    "gemini_engine",
    "inspection_engine",
    "measurement_engine",
    "fusion_engine",
    "health_engine",
    "comparison_engine",
    "repair_planner",
]