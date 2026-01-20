#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
ralph_loop.py - Ralph Loop iteration controller.

Hook type: Stop
Manages automatic re-prompting for long-running tasks across multiple
Claude sessions. Tracks iterations, detects completion, and re-injects
the original prompt until the task is complete or max iterations reached.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    hook_main,
    log_debug,
    output_block,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# =============================================================================
# Constants
# =============================================================================

RALPH_DIR_NAME = ".claude/ralph"
COOLDOWN_SECONDS = 5
ABORT_STOP_REASONS = frozenset({
    "user_interrupt",
    "user_cancelled",
    "abort",
    "explicit_stop",
})

# =============================================================================
# Ralph directory structure
# =============================================================================


def get_ralph_dir(cwd: str) -> Path:
    """Get the ralph directory path."""
    return Path(cwd) / RALPH_DIR_NAME


def is_ralph_active(cwd: str) -> bool:
    """Check if ralph mode is active (config.json exists)."""
    config_path = get_ralph_dir(cwd) / "config.json"
    return config_path.is_file()


# =============================================================================
# Cooldown mechanism
# =============================================================================


def get_cooldown_path(cwd: str) -> Path:
    """Get the cooldown file path."""
    return get_ralph_dir(cwd) / ".cooldown"


def is_cooldown_active(cwd: str) -> bool:
    """Check if cooldown period is active."""
    cooldown_path = get_cooldown_path(cwd)
    try:
        if not cooldown_path.is_file():
            return False
        content = cooldown_path.read_text(encoding="utf-8").strip()
        cooldown_time = float(content)
        elapsed = time.time() - cooldown_time
        if elapsed < COOLDOWN_SECONDS:
            log_debug(f"cooldown active: {COOLDOWN_SECONDS - elapsed:.1f}s remaining")
            return True
        return False
    except (OSError, ValueError) as e:
        log_debug(f"error checking cooldown: {e}")
        return False


def set_cooldown(cwd: str) -> None:
    """Set the cooldown timestamp."""
    cooldown_path = get_cooldown_path(cwd)
    try:
        cooldown_path.parent.mkdir(parents=True, exist_ok=True)
        cooldown_path.write_text(str(time.time()), encoding="utf-8")
        log_debug("cooldown set")
    except OSError as e:
        log_debug(f"error setting cooldown: {e}")


def clear_cooldown(cwd: str) -> None:
    """Clear the cooldown file."""
    cooldown_path = get_cooldown_path(cwd)
    try:
        if cooldown_path.is_file():
            cooldown_path.unlink()
            log_debug("cooldown cleared")
    except OSError as e:
        log_debug(f"error clearing cooldown: {e}")


# =============================================================================
# Abort handling
# =============================================================================


def is_user_abort(data: dict[str, Any]) -> bool:
    """Check if the stop was triggered by user abort."""
    stop_reason = data.get("stopReason", "")
    if stop_reason in ABORT_STOP_REASONS:
        log_debug(f"user abort detected: {stop_reason}")
        return True
    return False


# =============================================================================
# Session isolation
# =============================================================================


def check_session_match(config: dict[str, Any], data: dict[str, Any]) -> bool:
    """
    Check if session IDs match.

    Returns True if:
    - No sessionId in config (backwards compatibility)
    - sessionIds match

    Returns False if sessionIds don't match.
    """
    config_session = config.get("sessionId")
    if not config_session:
        # Backwards compat: no session ID in config means any session can use it
        log_debug("no sessionId in config - allowing any session")
        return True

    # Try multiple places where session ID might be
    input_session = data.get("sessionId") or data.get("session_id")

    if not input_session:
        # No session ID in input - allow for backwards compat
        log_debug("no sessionId in input - allowing")
        return True

    if config_session == input_session:
        log_debug(f"session match: {config_session}")
        return True

    log_debug(f"session mismatch: config={config_session}, input={input_session}")
    return False


# =============================================================================
# Orphan detection
# =============================================================================


def check_orphan_state(cwd: str, config: dict[str, Any]) -> bool:
    """
    Check for orphaned ralph state.

    Returns True if state is orphaned and was cleaned up.
    """
    ralph_dir = get_ralph_dir(cwd)
    state_path = ralph_dir / "state.json"

    # Check if config exists but state doesn't
    if not state_path.is_file():
        log_debug("orphan detected: config.json exists but state.json missing")
        remove_ralph_dir(cwd)
        return True

    # Check if iteration exceeds max
    state = read_json_safe(state_path)
    max_iterations = config.get("maxIterations", 20)
    current_iteration = state.get("iteration", 1)

    if current_iteration > max_iterations:
        log_debug(f"orphan detected: iteration {current_iteration} > max {max_iterations}")
        remove_ralph_dir(cwd)
        return True

    return False


# =============================================================================
# File operations with graceful error handling
# =============================================================================


def read_json_safe(path: Path) -> dict[str, Any]:
    """Read a JSON file safely, returning empty dict on error."""
    try:
        if not path.is_file():
            log_debug(f"file not found: {path}")
            return {}
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        if not isinstance(data, dict):
            log_debug(f"JSON is not a dict: {path}")
            return {}
        return data
    except (OSError, json.JSONDecodeError) as e:
        log_debug(f"error reading {path}: {e}")
        return {}


def write_json_safe(path: Path, data: dict[str, Any]) -> bool:
    """Write JSON file safely, returning success status."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return True
    except OSError as e:
        log_debug(f"error writing {path}: {e}")
        return False


def read_text_safe(path: Path) -> str:
    """Read a text file safely, returning empty string on error."""
    try:
        if not path.is_file():
            log_debug(f"file not found: {path}")
            return ""
        return path.read_text(encoding="utf-8")
    except OSError as e:
        log_debug(f"error reading {path}: {e}")
        return ""


def remove_ralph_dir(cwd: str) -> bool:
    """Remove the ralph directory to deactivate ralph mode."""
    ralph_dir = get_ralph_dir(cwd)
    try:
        if ralph_dir.is_dir():
            shutil.rmtree(ralph_dir)
            log_debug(f"removed ralph directory: {ralph_dir}")
        return True
    except OSError as e:
        log_debug(f"error removing ralph directory: {e}")
        return False


# =============================================================================
# Transcript analysis
# =============================================================================


def find_completion_promise(
    transcript: list[dict[str, Any]],
    promise: str,
    max_entries: int = 1000,
) -> bool:
    """
    Scan transcript for the completion promise in assistant messages.

    Searches for the pattern <promise>{promise}</promise> in the transcript.

    Args:
        transcript: List of transcript entries.
        promise: The completion promise value (e.g., "DONE").
        max_entries: Maximum entries to scan (safety limit).

    Returns:
        True if completion promise found in any assistant message.
    """
    if not promise:
        return False

    # Build the full promise pattern to search for
    promise_pattern = f"<promise>{promise}</promise>"

    for i, entry in enumerate(transcript):
        if i >= max_entries:
            log_debug(f"transcript scan truncated at {max_entries} entries")
            break

        if entry.get("role") == "assistant":
            content = entry.get("content") or ""
            if promise_pattern in content:
                log_debug(f"completion promise found at entry {i}")
                return True

    return False


# =============================================================================
# Re-injection prompt
# =============================================================================


def build_reinjection_prompt(
    iteration: int,
    max_iterations: int,
    original_prompt: str,
    completion_promise: str,
) -> str:
    """Build the re-injection prompt for continuing work."""
    # Build the full promise tag for display
    promise_tag = f"<promise>{completion_promise}</promise>"
    return f"""[RALPH LOOP - ITERATION {iteration} of {max_iterations}]

You are continuing a long-running task. This is iteration {iteration}.

## Original Task
{original_prompt}

## Recovery Instructions
1. Check `git log --oneline -20` to see what work has been committed
2. Check `git status` to see any uncommitted changes
3. Review relevant files to understand current state
4. Continue from where you left off - do NOT restart from scratch

## Completion
When the task is fully complete, output this exact string:
{promise_tag}

## Important
- You have {max_iterations - iteration} iteration(s) remaining after this one
- Make meaningful progress each iteration
- Commit work frequently to preserve progress
- Do NOT output the completion promise until ALL work is done

CONTINUE WORKING NOW."""


# =============================================================================
# Main hook
# =============================================================================


@hook_main("Stop")
def main() -> None:
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        output_empty()
        return

    # Get working directory
    cwd = data.get("cwd") or "."

    # ==========================================================================
    # ABORT HANDLING (before checking if ralph is active)
    # ==========================================================================
    if is_user_abort(data):
        # User aborted - clean up ralph state if it exists
        if is_ralph_active(cwd):
            log_debug("user abort - cleaning up ralph state")
            remove_ralph_dir(cwd)
            clear_cooldown(cwd)
        output_empty()
        return

    # ==========================================================================
    # CHECK IF RALPH IS ACTIVE
    # ==========================================================================
    if not is_ralph_active(cwd):
        log_debug("ralph mode not active")
        output_empty()
        return

    ralph_dir = get_ralph_dir(cwd)

    # ==========================================================================
    # COOLDOWN CHECK
    # ==========================================================================
    if is_cooldown_active(cwd):
        log_debug("cooldown active - skipping")
        output_empty()
        return

    # ==========================================================================
    # READ CONFIGURATION
    # ==========================================================================
    config = read_json_safe(ralph_dir / "config.json")
    if not config:
        log_debug("failed to read config - setting cooldown")
        set_cooldown(cwd)
        output_empty()
        return

    max_iterations = config.get("maxIterations", 20)
    completion_promise = config.get("completionPromise", "DONE")

    # ==========================================================================
    # SESSION ISOLATION
    # ==========================================================================
    if not check_session_match(config, data):
        log_debug("session mismatch - skipping")
        output_empty()
        return

    # ==========================================================================
    # ORPHAN DETECTION
    # ==========================================================================
    if check_orphan_state(cwd, config):
        log_debug("orphan state cleaned up")
        output_empty()
        return

    # ==========================================================================
    # READ STATE
    # ==========================================================================
    state = read_json_safe(ralph_dir / "state.json")
    current_iteration = state.get("iteration", 1)

    # Read original prompt
    original_prompt = read_text_safe(ralph_dir / "prompt.txt")
    if not original_prompt:
        original_prompt = "(Original prompt not found - check git history for context)"

    # ==========================================================================
    # CHECK COMPLETION
    # ==========================================================================
    transcript = data.get("transcript") or []
    is_complete = find_completion_promise(transcript, completion_promise)

    log_debug(f"ralph state: iteration={current_iteration}, max={max_iterations}, complete={is_complete}")

    # Check if we should stop
    if is_complete:
        log_debug("task completed - deactivating ralph mode")
        remove_ralph_dir(cwd)
        clear_cooldown(cwd)
        output_empty()
        return

    if current_iteration >= max_iterations:
        log_debug("max iterations reached - deactivating ralph mode")
        remove_ralph_dir(cwd)
        clear_cooldown(cwd)
        output_empty()
        return

    # ==========================================================================
    # CONTINUE LOOP
    # ==========================================================================
    next_iteration = current_iteration + 1
    state["iteration"] = next_iteration

    if not write_json_safe(ralph_dir / "state.json", state):
        log_debug("failed to write state - setting cooldown")
        set_cooldown(cwd)
        output_empty()
        return

    # Build and output the re-injection prompt
    reinjection_prompt = build_reinjection_prompt(
        iteration=next_iteration,
        max_iterations=max_iterations,
        original_prompt=original_prompt.strip(),
        completion_promise=completion_promise,
    )

    # Clear cooldown on successful continuation
    clear_cooldown(cwd)

    output_block(
        "Stop",
        f"Ralph Loop iteration {next_iteration}/{max_iterations}",
        reinjection_prompt,
    )


if __name__ == "__main__":
    main()
