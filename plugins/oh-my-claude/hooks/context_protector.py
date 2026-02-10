#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
context_protector.py - Enforce context protection at tool level.

PreToolUse hook that blocks large file reads, forcing delegation to librarian.
This prevents context bloat BEFORE it happens, not after.

Configuration via environment variables:
- OMC_LARGE_FILE_THRESHOLD: Lines before blocking (default: 100)
- OMC_ALLOW_LARGE_READS: Set to "1" to disable blocking entirely
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Add parent directory for hook_utils import
sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    hook_main,
    is_agent_session,
    log_debug,
    output_empty,
    parse_bool_env,
    parse_hook_input,
    read_stdin_safe,
)

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_THRESHOLD = 100


def get_threshold() -> int:
    """Get line threshold from env var or default."""
    try:
        return int(os.environ.get("OMC_LARGE_FILE_THRESHOLD", DEFAULT_THRESHOLD))
    except ValueError:
        return DEFAULT_THRESHOLD


def is_blocking_disabled() -> bool:
    """Check if large read blocking is disabled via env var."""
    # Note: inverted logic - default is False (blocking enabled), True means disabled
    return parse_bool_env("OMC_ALLOW_LARGE_READS", default=False)


ALLOWLISTED_FILENAMES = {
    "CLAUDE.md",
    "package.json",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
    ".gitignore",
    "tsconfig.json",
    "Makefile",
}


def is_allowlisted(file_path: str) -> bool:
    """Check if file is allowlisted and should bypass size check.

    CLAUDE.md files and common project metadata files are always allowed through
    as they're small config files that need to be read regardless of size.
    """
    return Path(file_path).name in ALLOWLISTED_FILENAMES


# =============================================================================
# File size detection
# =============================================================================


def get_line_count(file_path: str) -> int | None:
    """
    Get line count of a file using wc -l.

    Args:
        file_path: Path to the file.

    Returns:
        Line count, or None if file doesn't exist or can't be read.
    """
    try:
        # Check if file exists first
        path = Path(file_path)
        if not path.exists():
            log_debug(f"file does not exist: {file_path}")
            return None

        if not path.is_file():
            log_debug(f"path is not a file: {file_path}")
            return None

        # Use wc -l for fast line counting
        result = subprocess.run(
            ["wc", "-l", file_path],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            log_debug(f"wc -l failed: {result.stderr}")
            return None

        # Parse output: "  123 /path/to/file"
        parts = result.stdout.strip().split()
        if parts:
            return int(parts[0])

        return None

    except (subprocess.TimeoutExpired, ValueError, OSError) as e:
        log_debug(f"error getting line count: {e}")
        return None


# =============================================================================
# Output helpers for PreToolUse
# =============================================================================


def output_deny(reason: str) -> None:
    """Output denial response for PreToolUse hook."""
    import json

    response = {"decision": "block", "reason": reason}
    print(json.dumps(response))
    sys.exit(0)


def output_allow() -> None:
    """Output allow response (or just pass through)."""
    output_empty()


# =============================================================================
# Main hook logic
# =============================================================================


@hook_main("PreToolUse")
def main() -> None:
    """Main entry point for PreToolUse hook."""
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        log_debug("no input data, passing through")
        output_allow()
        return

    # Skip for agent sessions (subagents and teammates work freely)
    if is_agent_session(data):
        return output_empty()

    # Only handle Read tool
    tool_name = data.get("tool_name", "")
    if tool_name != "Read":
        log_debug(f"tool is {tool_name}, not Read - passing through")
        output_allow()
        return

    # Check if blocking is disabled
    if is_blocking_disabled():
        log_debug("large read blocking disabled via OMC_ALLOW_LARGE_READS")
        output_allow()
        return

    # Get file path from tool input
    tool_input = data.get("tool_input", {})
    if isinstance(tool_input, str):
        file_path = tool_input
    else:
        file_path = tool_input.get("file_path", "")

    if not file_path:
        log_debug("no file_path in tool_input")
        output_allow()
        return

    # Check if file is allowlisted (e.g., CLAUDE.md)
    if is_allowlisted(file_path):
        log_debug(f"file is allowlisted: {file_path}")
        output_allow()
        return

    log_debug(f"checking file: {file_path}")

    # Get line count
    line_count = get_line_count(file_path)

    if line_count is None:
        # Can't determine size - allow (file might not exist yet, or binary)
        log_debug("could not determine line count, allowing")
        output_allow()
        return

    threshold = get_threshold()
    log_debug(f"file has {line_count} lines, threshold is {threshold}")

    if line_count > threshold:
        # Block the read
        estimated_tokens = line_count * 4
        reason = (
            f"File has {line_count} lines (threshold: {threshold}). "
            f"Reading directly costs ~{estimated_tokens:,} tokens. Delegate to librarian.\n"
            f"Use Task(subagent_type=\"oh-my-claude:librarian\") to read large files. "
            f"This protects your context window for reasoning.\n\n"
            f"\"I'll just skim it\" → Skimming still costs full token count. Delegate.\n"
            f"\"I need the whole file\" → Librarian reads whole file, extracts semantics. "
            f"Same result, fraction of the cost."
        )
        log_debug(f"blocking read: {reason}")
        output_deny(reason)
    else:
        log_debug("file within threshold, allowing")
        output_allow()


if __name__ == "__main__":
    main()
