"""Performance monitoring for InspectAI.

Tracks timing metrics for every stage of the inspection pipeline.
Metrics are only collected in DEBUG mode to avoid overhead in production.

Usage::

    with PerformanceTracker.stage("opencv"):
        run_opencv_analysis(...)

    # Or manually:
    tracker = PerformanceTracker.get()
    tracker.start("gemini")
    # ... work ...
    tracker.stop("gemini")

    # Render in DEBUG mode:
    tracker.render_metrics()
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Optional

from streamlit_app.utils.logger import get_logger

_logger = get_logger(__name__)

# ── Enable/disable ────────────────────────────────────────────────────────────

# Set to True via config or env var to enable timing collection.
_enabled: bool = False


def enable() -> None:
    """Enable performance tracking."""
    global _enabled
    _enabled = True
    _logger.info("Performance tracking enabled.")


def disable() -> None:
    """Disable performance tracking."""
    global _enabled
    _enabled = False


def is_enabled() -> bool:
    """Return True if performance tracking is active."""
    return _enabled


# ── Stage timings ─────────────────────────────────────────────────────────────

@dataclass
class StageTiming:
    """Timing data for a single pipeline stage."""
    name: str
    total_sec: float = 0.0
    call_count: int = 0
    max_sec: float = 0.0
    min_sec: float = float("inf")


class PerformanceTracker:
    """Singleton-style performance tracker.

    Collects per-stage timings across the entire app lifecycle.
    """

    _instance: Optional["PerformanceTracker"] = None
    _lock: Any = None  # threading.Lock — imported lazily

    def __init__(self) -> None:
        self._stages: dict[str, StageTiming] = {}
        self._active: dict[str, float] = {}  # stage_name → start_time

    # ── Singleton access ────────────────────────────────────────────────────

    @classmethod
    def get(cls) -> "PerformanceTracker":
        """Return the global tracker instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the global tracker (for testing)."""
        cls._instance = None

    # ── Timing API ──────────────────────────────────────────────────────────

    def start(self, stage_name: str) -> None:
        """Mark the start of a timed stage."""
        if not _enabled:
            return
        self._active[stage_name] = time.perf_counter()

    def stop(self, stage_name: str) -> Optional[float]:
        """Mark the end of a timed stage and record the duration.

        Returns:
            Elapsed seconds, or None if tracking is disabled.
        """
        if not _enabled:
            return None
        start = self._active.pop(stage_name, None)
        if start is None:
            return None
        elapsed = time.perf_counter() - start

        if stage_name not in self._stages:
            self._stages[stage_name] = StageTiming(name=stage_name)
        timing = self._stages[stage_name]
        timing.total_sec += elapsed
        timing.call_count += 1
        timing.max_sec = max(timing.max_sec, elapsed)
        timing.min_sec = min(timing.min_sec, elapsed)

        return elapsed

    @contextmanager
    def stage(self, name: str):
        """Context manager for timing a block of code.

        Usage::

            with PerformanceTracker.get().stage("opencv"):
                ...
        """
        self.start(name)
        try:
            yield
        finally:
            self.stop(name)

    # ── Reporting ───────────────────────────────────────────────────────────

    def get_metrics(self) -> dict[str, dict[str, Any]]:
        """Return all collected timing metrics as a dict."""
        result: dict[str, dict[str, Any]] = {}
        for name, timing in self._stages.items():
            avg = timing.total_sec / timing.call_count if timing.call_count else 0.0
            result[name] = {
                "total_sec": round(timing.total_sec, 3),
                "calls": timing.call_count,
                "avg_sec": round(avg, 3),
                "min_sec": round(timing.min_sec, 3) if timing.min_sec != float("inf") else 0.0,
                "max_sec": round(timing.max_sec, 3),
            }
        return result

    def render_metrics(self) -> None:
        """Render timing metrics to the Streamlit UI (DEBUG mode only)."""
        if not _enabled:
            return
        try:
            import streamlit as st
        except ImportError:
            return

        metrics = self.get_metrics()
        if not metrics:
            st.caption("No timing data collected yet.")
            return

        with st.expander("⚡ Performance Metrics (DEBUG)", expanded=False):
            for name, data in metrics.items():
                cols = st.columns(5)
                cols[0].metric(f"{name} — total", f"{data['total_sec']:.2f}s")
                cols[1].metric("calls", data["calls"])
                cols[2].metric("avg", f"{data['avg_sec']:.3f}s")
                cols[3].metric("min", f"{data['min_sec']:.3f}s")
                cols[4].metric("max", f"{data['max_sec']:.3f}s")

    def log_metrics(self) -> None:
        """Log all timing metrics at INFO level."""
        if not _enabled:
            return
        metrics = self.get_metrics()
        if not metrics:
            _logger.info("No timing data collected.")
            return

        _logger.info("=== Performance Metrics ===")
        for name, data in metrics.items():
            _logger.info(
                "  %-20s  total=%6.3fs  calls=%d  avg=%6.3fs  min=%6.3fs  max=%6.3fs",
                name,
                data["total_sec"],
                data["calls"],
                data["avg_sec"],
                data["min_sec"],
                data["max_sec"],
            )
        _logger.info("==========================")


# ── Convenience context manager (module-level) ────────────────────────────────

@contextmanager
def track_stage(name: str):
    """Time a block of code.  Uses the global tracker.

    Usage::

        with track_stage("gemini"):
            result = analyze_image(...)
    """
    tracker = PerformanceTracker.get()
    with tracker.stage(name):
        yield
