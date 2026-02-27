#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
context_monitor.py
PostToolUse hook: Monitors context window usage and injects warnings when
usage exceeds thresholds.

Uses Claude Code's native context_window.used_percentage when available,
falls back to transcript-based estimation.

Configuration via environment variables:
- OMC_CONTEXT_WARN_PCT: Warning threshold percentage (default: 70)
- OMC_CONTEXT_CRITICAL_PCT: Critical threshold percentage (default: 85)
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    get_nested,
    hook_main,
    log_debug,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# Defaults
CONTEXT_LIMIT = 200_000
DEFAULT_WARNING_PCT = 70
DEFAULT_CRITICAL_PCT = 85

# Filesystem-based dedup directory
_DEDUP_DIR = Path("/tmp")


def get_warning_threshold() -> float:
    """Get warning threshold from env var or default (as decimal 0.0-1.0)."""
    try:
        pct = int(os.environ.get("OMC_CONTEXT_WARN_PCT", DEFAULT_WARNING_PCT))
        return max(0, min(100, pct)) / 100.0
    except ValueError:
        return DEFAULT_WARNING_PCT / 100.0


def get_critical_threshold() -> float:
    """Get critical threshold from env var or default (as decimal 0.0-1.0)."""
    try:
        pct = int(os.environ.get("OMC_CONTEXT_CRITICAL_PCT", DEFAULT_CRITICAL_PCT))
        return max(0, min(100, pct)) / 100.0
    except ValueError:
        return DEFAULT_CRITICAL_PCT / 100.0


def has_warned(session_id: str, threshold: str) -> bool:
    """Check if a warning has already been issued for this session/threshold."""
    marker = _DEDUP_DIR / f"omc_context_{session_id}_{threshold}"
    return marker.exists()


def mark_warned(session_id: str, threshold: str) -> None:
    """Record that a warning was issued for this session/threshold."""
    marker = _DEDUP_DIR / f"omc_context_{session_id}_{threshold}"
    try:
        marker.touch()
    except OSError:
        pass


def estimate_tokens(transcript: list) -> int:
    """Approximate tokens from character count (~4 chars per token)."""
    total_chars = sum(len(str(entry)) for entry in transcript)
    return total_chars // 4


def get_usage_percentage(data: dict) -> float:
    """Get context usage as a decimal 0.0-1.0.

    Prefers native context_window.used_percentage, falls back to
    transcript-based estimation with a log_debug() call.
    """
    native_pct = get_nested(data, "context_window", "used_percentage")
    if native_pct is not None:
        try:
            return float(native_pct) / 100.0
        except (TypeError, ValueError):
            log_debug(f"invalid context_window.used_percentage: {native_pct}, falling back to estimation")

    # Fallback to transcript-based estimation
    log_debug("context_window.used_percentage not available, using transcript estimation")
    transcript = get_nested(data, "transcript", default=[])
    if not transcript:
        return 0.0
    estimated_tokens = estimate_tokens(transcript)
    return estimated_tokens / CONTEXT_LIMIT


@hook_main("PostToolUse")
def main() -> None:
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        return output_empty()

    session_id = get_nested(data, "session_id", default="unknown")
    usage_pct = get_usage_percentage(data)

    # Get thresholds from env vars
    warning_threshold = get_warning_threshold()
    critical_threshold = get_critical_threshold()
    log_debug(f"thresholds: warn={warning_threshold:.0%}, critical={critical_threshold:.0%}")

    # Check thresholds (critical first, then warning)
    if usage_pct >= critical_threshold:
        if has_warned(session_id, "critical"):
            return output_empty()
        mark_warned(session_id, "critical")
        warning = (
            f"[CONTEXT CRITICAL: ~{usage_pct*100:.0f}% used]\n"
            f"Delegate large file reads and searches to preserve remaining context.\n"
            f"Consider: (1) Delegate to subagents (2) Use /memory for key context (3) Summarize before continuing\n\n"
            f"\"I'm almost done\" \u2192 70% full means context tax on every operation. Delegate now."
        )
        output_context("PostToolUse", warning)

    elif usage_pct >= warning_threshold:
        if has_warned(session_id, "warning"):
            return output_empty()
        mark_warned(session_id, "warning")
        warning = (
            f"[Context: ~{usage_pct*100:.0f}% used - consider delegating to preserve context]\n"
            f"Delegate large file reads and searches to preserve remaining context.\n\n"
            f"\"I'm almost done\" \u2192 70% full means context tax on every operation. Delegate now."
        )
        output_context("PostToolUse", warning)

    else:
        return output_empty()


if __name__ == "__main__":
    main()
