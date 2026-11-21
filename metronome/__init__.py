"""metronome：单文件、离线可用的网页节拍器。"""

from __future__ import annotations

from .model import (
    MAX_BEATS,
    MAX_BPM,
    MAX_MINUTES,
    MAX_TITLE_LENGTH,
    MIN_BEATS,
    MIN_BPM,
    MIN_MINUTES,
    MetronomeConfig,
    MetronomeError,
    format_clock,
)
from .render import render_html

__version__ = "0.1.0"

__all__ = [
    "MAX_BEATS",
    "MAX_BPM",
    "MAX_MINUTES",
    "MAX_TITLE_LENGTH",
    "MIN_BEATS",
    "MIN_BPM",
    "MIN_MINUTES",
    "MetronomeConfig",
    "MetronomeError",
    "format_clock",
    "render_html",
    "__version__",
]
