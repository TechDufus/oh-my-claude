#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
context_monitor.py
PostToolUse hook: Approximates context usage from transcript length and injects
warnings when usage exceeds thresholds.

Configuration via environment variables:
- OMC_CONTEXT_WARN_PCT: Warning threshold percentage (default: 70)
- OMC_CONTEXT_CRITICAL_PCT: Critical threshold percentage (default: 85)
"""

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

# Track sessions that have been warned (avoid spam)
_warned_sessions: set[str] = set()


def estimate_tokens(transcript: list) -> int:
    """Approximate tokens from character count (~4 chars per token)."""
    total_chars = sum(len(str(entry)) for entry in transcript)
    return total_chars // 4


@hook_main("PostToolUse")
def main() -> None:
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        return output_empty()

    transcript = get_nested(data, "transcript", default=[])
    if not transcript:
        return output_empty()

    # Estimate usage
    estimated_tokens = estimate_tokens(transcript)
    usage_pct = estimated_tokens / CONTEXT_LIMIT

    # Only warn once per session
    session_id = get_nested(data, "session_id", default="unknown")

    # Check if we've already warned this session
    if session_id in _warned_sessions:
        return output_empty()

    # Get thresholds from env vars
    warning_threshold = get_warning_threshold()
    critical_threshold = get_critical_threshold()
    log_debug(f"thresholds: warn={warning_threshold:.0%}, critical={critical_threshold:.0%}")

    # Check thresholds
    if usage_pct >= critical_threshold:
        _warned_sessions.add(session_id)
        warning = f"""[CONTEXT CRITICAL: ~{usage_pct*100:.0f}% used ({estimated_tokens:,}~/{CONTEXT_LIMIT:,} tokens)]
Consider: (1) Delegate to subagents (2) Write to notepads (3) Summarize before continuing"""
        output_context("PostToolUse", warning)

    elif usage_pct >= warning_threshold:
        _warned_sessions.add(session_id)
        warning = f"[Context: ~{usage_pct*100:.0f}% used - consider delegating to preserve context]"
        output_context("PostToolUse", warning)

    else:
        return output_empty()


if __name__ == "__main__":
    main()
