"""Gemini Vision API integration for InspectAI.

Sends property images to Google Gemini 1.5 Pro with structured prompts
to produce semantic defect descriptions, severity classifications, and
repair recommendations.

Public API
----------
- ``analyze_image_with_gemini``  — single image, returns structured dict.
- ``analyze_batch``              — multiple images with back-off retry.
- ``build_prompt``               — assemble the inspection prompt.
- ``parse_gemini_response``      — normalise the raw API response.
- ``get_safety_settings``        — return Gemini safety filters.
- ``GeminiAnalysis``             — dataclass wrapping parsed results.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from PIL import Image

from streamlit_app.utils.exceptions import (
    AIServiceError,
    ConfigurationError,
    GeminiParseError,
)
from streamlit_app.utils.logger import get_logger
from streamlit_app.utils.validators import validate_processing_params


# ── GeminiAnalysis dataclass ───────────────────────────────────────────────────
# Backwards-compatible wrapper around parsed Gemini response dicts.
# Used by inspection_engine, fusion_engine, report_builder, and others.

@dataclass
class GeminiAnalysis:
    """Wraps a parsed Gemini response for downstream consumption."""
    raw_response: str = ""
    damage_type: str = "N/A"
    severity: str = "Low"
    confidence: int = 0
    possible_causes: list[str] = field(default_factory=list)
    repair_steps: list[str] = field(default_factory=list)
    recommended_professional: str = "N/A"
    estimated_cost_range: str = "N/A"
    urgency: str = "Low"
    prevention_tips: list[str] = field(default_factory=list)
    has_damage: bool = False
    health_score: int = 100

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> "GeminiAnalysis":
        """Build a GeminiAnalysis from a parsed API response dict."""
        findings = response.get("findings", [])
        has_damage = len(findings) > 0
        primary = findings[0] if findings else {}

        damage_types = [f.get("damage_type", f.get("title", "Unknown")) for f in findings]
        primary_damage = damage_types[0] if damage_types else "N/A"

        severities = [f.get("severity", "Low") for f in findings]
        primary_severity = severities[0] if severities else "Low"

        confidences = [f.get("confidence", 0) for f in findings]
        avg_confidence = int(sum(confidences) / len(confidences)) if confidences else 0

        all_causes = []
        all_steps = []
        all_tips = []
        for f in findings:
            desc = f.get("description", "")
            if desc:
                all_causes.append(desc)
            all_steps.extend(f.get("repair_steps", []))
            all_tips.extend(f.get("prevention_tips", []))

        cost_min = sum(f.get("cost_min", 0) for f in findings)
        cost_max = sum(f.get("cost_max", 0) for f in findings)
        if cost_min or cost_max:
            cost_range = f"₹{cost_min:,} – ₹{cost_max:,}"
        else:
            cost_range = "N/A"

        health = response.get("overall_health_score", 100)

        urgency = "Low"
        if primary_severity in ("Critical",):
            urgency = "Immediate"
        elif primary_severity in ("High",):
            urgency = "Urgent"
        elif primary_severity in ("Medium",):
            urgency = "Moderate"

        return cls(
            raw_response=str(response),
            damage_type=primary_damage,
            severity=primary_severity,
            confidence=avg_confidence,
            possible_causes=all_causes[:5],
            repair_steps=list(dict.fromkeys(all_steps))[:10],
            recommended_professional="Licensed contractor",
            estimated_cost_range=cost_range,
            urgency=urgency,
            prevention_tips=all_tips[:5],
            has_damage=has_damage,
            health_score=int(health),
        )

# ── Backwards-compat shim ──────────────────────────────────────────────────────

def analyze_damage(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Deprecated: use :func:`analyze_image_with_gemini` instead.

    Legacy shim kept for backwards compatibility with code that
    imports ``analyze_damage`` from this module.
    """
    _logger.warning("analyze_damage() is deprecated — use analyze_image_with_gemini().")
    if args:
        return analyze_image_with_gemini(args[0], build_prompt())
    if "image" in kwargs:
        return analyze_image_with_gemini(kwargs["image"], build_prompt())
    raise TypeError("analyze_damage() requires an image argument.")


# ── Logging ────────────────────────────────────────────────────────────────────

_logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_MODEL_NAME: str = "gemini-2.5-flash-lite"
_DEFAULT_TIMEOUT: int = 120  # seconds
_RETRYABLE_CODES: set[str] = {
    "DEADLINE_EXCEEDED",
    "UNAVAILABLE",
    "INTERNAL",
    "RESOURCE_EXHAUSTED",
}
_MAX_RETRIES: int = 3
_RETRY_BACKOFF_BASE: float = 2.0


# ── Configuration ─────────────────────────────────────────────────────────────


def get_gemini_api_key() -> str:
    """Return the Gemini API key from the environment.

    Priority order:
      1. ``os.environ["GEMINI_API_KEY"]``
      2. ``st.secrets["GEMINI_API_KEY"]`` (Streamlit Cloud)

    Raises:
        ConfigurationError: ``GEMINI_API_KEY`` is not set or is empty.
    """
    # Try environment variable first
    key = os.getenv("GEMINI_API_KEY", "").strip()

    # Fall back to Streamlit secrets (used on Streamlit Community Cloud)
    if not key:
        try:
            import streamlit as _st
            key = str(_st.secrets.get("GEMINI_API_KEY", "")).strip()
        except Exception:
            key = ""

    if not key:
        raise ConfigurationError(
            "GEMINI_API_KEY is not set. "
            "Add it to your .env file, environment variables, or Streamlit secrets.",
            field="gemini_api_key",
        )
    return key


def configure_gemini() -> None:
    """Configure the Gemini SDK with the current API key.

    Raises:
        ConfigurationError: Key is missing or SDK raises an error.
    """
    api_key = get_gemini_api_key()
    try:
        genai.configure(api_key=api_key)
        _logger.info("Gemini SDK configured successfully (model=%s).", _MODEL_NAME)
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to configure Gemini SDK: {exc}.",
            field="gemini_api_key",
        ) from exc


def get_safety_settings() -> list[dict[str, str]]:
    """Return per-category safety settings for Gemini requests.

    All categories are set to ``BLOCK_NONE`` because inspection images
    may contain construction imagery that would otherwise be over-filtered.
    """
    return [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]


# ── Prompt Construction ───────────────────────────────────────────────────────


def build_prompt(property_type: str = "House", inspection_focus: str = "") -> str:
    """Build the Gemini inspection prompt.

    Args:
        property_type:    Kind of property (House, Apartment, …).
        inspection_focus: Optional additional focus area.

    Returns:
        Complete prompt string.
    """
    base = (
        "You are a certified building inspector. "
        "Analyse the following property image carefully.\n\n"
        f"Property type: {property_type}.\n"
    )
    if inspection_focus:
        base += f"Specific focus: {inspection_focus}.\n"

    base += """
For each defect you identify, provide:
1. Title (short)
2. Severity — one of: Critical, High, Medium, Low
3. Confidence percentage (0-100)
4. Description of what you see
5. Location in the property
6. Step-by-step repair instructions
7. Estimated cost range (min and max in USD)

Respond in the following JSON format:
{
  "findings": [
    {
      "title": "...",
      "severity": "...",
      "confidence": 85,
      "description": "...",
      "location": "...",
      "repair_steps": ["step1", "step2"],
      "cost_min": 500,
      "cost_max": 1500
    }
  ],
  "overall_health_score": 75,
  "summary": "..."
}

If no defects are found, return an empty findings array.
"""
    return base


# ── Response Parsing ──────────────────────────────────────────────────────────


def parse_gemini_response(response_text: str) -> dict[str, Any]:
    """Parse the raw text response from Gemini into a structured dict.

    Handles both JSON and JSON-within-markdown-code-fence responses.

    Args:
        response_text: Raw text returned by Gemini.

    Returns:
        Parsed dict, or a fallback error dict on failure.
    """
    import json
    import re

    text = response_text.strip()

    # Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Response is not a JSON object.")
        return data
    except (json.JSONDecodeError, ValueError) as exc:
        _logger.warning("Failed to parse Gemini response as JSON: %s", exc)
        raise GeminiParseError(
            f"Gemini returned non-JSON response: {exc}.",
            raw_response=response_text,
        ) from exc


# ── Core Analysis ─────────────────────────────────────────────────────────────


def analyze_image_with_gemini(
    image: Any,
    prompt: str,
    model_name: str = _MODEL_NAME,
) -> dict[str, Any]:
    """Send a single image to Gemini Vision and return structured results.

    Args:
        image:       PIL Image, numpy array, or file-like object.
        prompt:      Inspection prompt (see :func:`build_prompt`).
        model_name:  Gemini model identifier.
        timeout:     Request timeout in seconds.

    Returns:
        Parsed response dict with ``findings`` list.

    Raises:
        ConfigurationError: API key is missing/invalid or SDK misconfigured.
        AIServiceError:      API call fails (may be retryable).
        GeminiParseError:    Response was received but could not be parsed.
        ValidationError:     Input image is not usable.
    """
    # Configuration is checked first so callers can catch a ConfigurationError
    # separately from transient API errors.
    configure_gemini()

    # Validate prompt
    if not prompt or not prompt.strip():
        raise ValidationError("Empty prompt provided to Gemini.", field="prompt")

    # Convert to PIL if needed
    if isinstance(image, np.ndarray):
        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))  # type: ignore[name-defined]
    elif isinstance(image, Image.Image):
        pil_img = image
    else:
        raise ValidationError(
            f"Unsupported image type for Gemini: {type(image).__name__}.",
            field="image",
        )

    _logger.info(
        "Sending image to Gemini (model=%s, size=%dx%d).",
        model_name, pil_img.width, pil_img.height,
    )

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            [prompt, pil_img],
            safety_settings=get_safety_settings(),
            generation_config={"temperature": 0.3, "max_output_tokens": 2048},
        )

        result_text = response.text or ""
        result = parse_gemini_response(result_text)
        return result

    except GeminiParseError:
        raise  # never retry parse errors; let caller decide
    except google_exceptions.GoogleAPIError as exc:
        code_name = exc.code.name if hasattr(exc, "code") else "UNKNOWN"
        retryable = code_name in _RETRYABLE_CODES
        _logger.error("Gemini API error [%s]: %s", code_name, exc)
        raise AIServiceError(
            f"Gemini API error ({code_name}): {exc}.",
            provider="gemini",
            retryable=retryable,
        ) from exc

    except Exception as exc:
        _logger.exception("Unexpected error during Gemini call.")
        raise AIServiceError(
            f"Unexpected Gemini error: {exc}.",
            provider="gemini",
        ) from exc


def analyze_batch(
    images: list[Any],
    prompt: str,
    max_images: int = 20,
) -> dict[str, Any]:
    """Analyze multiple images, merging results.

    Retries individually failed images up to ``_MAX_RETRIES`` times with
    exponential back-off.

    Args:
        images:     List of PIL Images or file-like objects.
        prompt:     Inspection prompt.
        max_images: Safety cap on the number of images processed.

    Returns:
        Merged result dict with all findings combined.

    Raises:
        ValidationError: ``images`` is empty or exceeds ``max_images``.
        AIServiceError:  All retries for every image fail.
    """
    validate_processing_params(max_images=max_images)

    if not images:
        raise ValidationError("No images provided for batch analysis.", field="images")

    if len(images) > max_images:
        raise ValidationError(
            f"Too many images ({len(images)}) — the limit is {max_images}.",
            field="images",
        )

    _logger.info("Starting batch Gemini analysis on %d images.", len(images))

    all_findings: list[dict[str, Any]] = []
    health_scores: list[int] = []
    total_cost_min = 0
    total_cost_max = 0

    for idx, image in enumerate(images):
        last_exc = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                result = analyze_image_with_gemini(image, prompt)
                findings = result.get("findings", [])
                all_findings.extend(findings)

                score = result.get("overall_health_score")
                if score is not None:
                    health_scores.append(int(score))

                for f in findings:
                    total_cost_min += f.get("cost_min", 0)
                    total_cost_max += f.get("cost_max", 0)

                _logger.info("Image %d/%d processed successfully.", idx + 1, len(images))
                break

            except AIServiceError as exc:
                last_exc = exc
                retryable = exc.details.get("retryable", False)
                if retryable and attempt < _MAX_RETRIES:
                    wait = _RETRY_BACKOFF_BASE ** attempt
                    _logger.warning(
                        "Image %d attempt %d/%d failed (retryable, code=%s). "
                        "Retrying in %.1fs.",
                        idx + 1, attempt, _MAX_RETRIES, exc.error_code, wait,
                    )
                    time.sleep(wait)
                else:
                    _logger.error(
                        "Image %d failed after %d attempt(s) [%s]: %s",
                        idx + 1, attempt, exc.error_code, exc,
                    )
                    break
            except GeminiParseError as exc:
                _logger.error(
                    "Image %d: Gemini parse error — skipping (not retryable): %s",
                    idx + 1, exc,
                )
                break  # parsing failures are never retried

        if last_exc is not None:
            _logger.warning("Image %d skipped after all retries.", idx + 1)

    avg_score = int(sum(health_scores) / len(health_scores)) if health_scores else 0

    summary = {
        "findings": all_findings,
        "overall_health_score": avg_score,
        "estimated_cost_min": total_cost_min,
        "estimated_cost_max": total_cost_max,
        "images_analyzed": len(images),
        "status": "Completed",
        "provider": "gemini",
    }

    _logger.info(
        "Batch analysis complete — %d findings, avg health %d%%, "
        "cost estimate $%d–$%d.",
        len(all_findings), avg_score, total_cost_min, total_cost_max,
    )
    return summary
