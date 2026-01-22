"""
hook_utils.py - Shared utilities for oh-my-claude hooks.

Provides safe stdin handling, structured output, caching, and error handling.
Uses only Python stdlib - no external dependencies.
"""

from __future__ import annotations

import functools
import json
import os
import re
import select
import shutil
import signal
import sys
from typing import Any, Callable, TypeVar

# =============================================================================
# Constants
# =============================================================================

MAX_STDIN_BYTES: int = 1_000_000  # 1MB
STDIN_TIMEOUT_SECONDS: int = 5

# =============================================================================
# Logging (stderr only)
# =============================================================================

DEBUG: bool = os.environ.get("HOOK_DEBUG", "").lower() in ("1", "true", "yes")


def log_debug(msg: str) -> None:
    """Log debug message to stderr if DEBUG is enabled."""
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)


def log_error(msg: str) -> None:
    """Log error message to stderr."""
    print(f"[ERROR] {msg}", file=sys.stderr)


# =============================================================================
# Safe stdin reading
# =============================================================================


class StdinTimeoutError(Exception):
    """Raised when stdin read times out."""

    pass


class StdinSizeError(Exception):
    """Raised when stdin exceeds max allowed size."""

    pass


def _alarm_handler(
    _signum: int,  # pyright: ignore[reportUnusedParameter]
    _frame: Any,  # pyright: ignore[reportUnusedParameter]
) -> None:
    """Signal handler for SIGALRM timeout."""
    raise StdinTimeoutError("stdin read timed out via SIGALRM")


def read_stdin_safe(
    timeout: int = STDIN_TIMEOUT_SECONDS,
    max_bytes: int = MAX_STDIN_BYTES,
) -> str:
    """
    Safely read from stdin with timeout and size limits.

    Uses select() for non-blocking check with SIGALRM as backup.
    Returns empty string on timeout for graceful degradation.

    Args:
        timeout: Maximum seconds to wait for input.
        max_bytes: Maximum bytes to read.

    Returns:
        Content read from stdin, or empty string on timeout.

    Raises:
        StdinSizeError: If input exceeds max_bytes.
    """
    # Check if stdin has data available using select
    try:
        readable, _, _ = select.select([sys.stdin], [], [], timeout)
        if not readable:
            log_debug("stdin not readable within timeout (select)")
            return ""
    except (ValueError, OSError) as e:
        # stdin might not be selectable (e.g., redirected file)
        log_debug(f"select() failed: {e}, falling back to SIGALRM")
        readable = True  # Proceed with SIGALRM backup

    # Set up SIGALRM as backup timeout mechanism
    old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(timeout)

    try:
        content = sys.stdin.read(max_bytes + 1)

        if len(content) > max_bytes:
            raise StdinSizeError(f"stdin exceeds {max_bytes} bytes")

        log_debug(f"read {len(content)} bytes from stdin")
        return content

    except StdinTimeoutError:
        log_debug("stdin read timed out via SIGALRM")
        return ""

    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# =============================================================================
# Input validation
# =============================================================================


def parse_hook_input(raw: str) -> dict[str, Any]:
    """
    Parse JSON hook input.

    Args:
        raw: Raw JSON string from stdin.

    Returns:
        Parsed dictionary, or empty dict on error.
    """
    if not raw or not raw.strip():
        log_debug("empty input, returning {}")
        return {}

    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            log_debug(f"parsed JSON is not a dict: {type(data)}")
            return {}
        return data
    except json.JSONDecodeError as e:
        log_debug(f"JSON parse error: {e}")
        return {}


def get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Safely access nested dictionary values.

    Args:
        data: Dictionary to traverse.
        *keys: Sequence of keys to follow.
        default: Value to return if any key is missing.

    Returns:
        Value at the nested path, or default if not found.

    Example:
        >>> get_nested({"a": {"b": 1}}, "a", "b")
        1
        >>> get_nested({"a": {}}, "a", "b", "c", default="missing")
        'missing'
    """
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


# =============================================================================
# Output helpers
# =============================================================================


def output_empty() -> None:
    """Exit with no output (hook pass-through)."""
    sys.exit(0)


def output_context(hook_event: str, context: str) -> None:
    """
    Output standard hook response with additional context.

    Args:
        hook_event: The hook event name (e.g., "UserPromptSubmit").
        context: Additional context to inject.
    """
    response = {
        "hookSpecificOutput": {
            "hookEventName": hook_event,
            "additionalContext": context,
        }
    }
    print(json.dumps(response))


def output_block(hook_event: str, reason: str, context: str) -> None:
    """
    Output blocking hook response (for Stop hooks).

    Args:
        hook_event: The hook event name (e.g., "Stop").
        reason: Why the action is being blocked.
        context: Additional context explaining the block.
    """
    response = {
        "hookSpecificOutput": {
            "hookEventName": hook_event,
            "blocked": True,
            "reason": reason,
            "additionalContext": context,
        }
    }
    print(json.dumps(response))


def output_stop_block(reason: str, context: str | None = None) -> None:
    """
    Output blocking response for Stop hooks.

    Stop hooks use 'decision: block' to prevent Claude from stopping.
    The reason field tells Claude why it must continue working.

    Args:
        reason: Why the stop is being blocked.
        context: Optional additional context (appended to reason).
    """
    stop_reason = f"{reason}\n\n{context}" if context else reason
    response = {
        "decision": "block",
        "reason": stop_reason,
    }
    print(json.dumps(response))


def output_permission(decision: str, reason: str | None = None) -> None:
    """
    Output permission decision for PermissionRequest hooks.

    Args:
        decision: One of "allow", "deny", or "ask".
        reason: Optional reason explaining the decision.
    """
    response: dict[str, Any] = {"permissionDecision": decision}
    if reason:
        response["reason"] = reason
    print(json.dumps(response))


def output_subagent_decision(decision: str, reason: str | None = None) -> None:
    """
    Output decision for SubagentStop hooks.

    Args:
        decision: One of "block" or "approve".
        reason: When blocking, explains why the subagent should continue.
                Required when decision is "block".
    """
    response: dict[str, Any] = {"decision": decision}
    if reason:
        response["reason"] = reason
    print(json.dumps(response))


def output_pretooluse_modify(updated_input: dict[str, Any], reason: str | None = None) -> None:
    """
    Output modified tool input for PreToolUse hooks.

    Allows transparent modification of tool parameters before execution.
    The tool will run with the updated input instead of the original.
    Requires Claude Code v2.0.10+.

    Args:
        updated_input: Modified tool input parameters to use instead of original.
        reason: Optional reason explaining why the input was modified.
    """
    hook_output: dict[str, Any] = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": updated_input,
    }
    if reason:
        hook_output["permissionDecisionReason"] = reason
    response = {"hookSpecificOutput": hook_output}
    print(json.dumps(response))


# =============================================================================
# Exception wrapper decorator
# =============================================================================

F = TypeVar("F", bound=Callable[..., Any])


def hook_main(hook_event: str) -> Callable[[F], F]:
    """
    Decorator for hook main functions with error handling.

    Sets DEBUG from HOOK_DEBUG env var, wraps function with try/except,
    and calls output_empty() on any unhandled exception.

    Args:
        hook_event: The hook event name for error context.

    Example:
        @hook_main("UserPromptSubmit")
        def main() -> None:
            data = parse_hook_input(read_stdin_safe())
            # ... hook logic ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            global DEBUG
            DEBUG = os.environ.get("HOOK_DEBUG", "").lower() in ("1", "true", "yes")

            try:
                return func(*args, **kwargs)
            except SystemExit:
                # Let sys.exit() pass through
                raise
            except Exception as e:
                log_error(f"unhandled exception in {hook_event}: {e}")
                output_empty()

        return wrapper  # type: ignore

    return decorator


# =============================================================================
# Caching utilities
# =============================================================================


class RegexCache:
    """
    Cache for compiled regular expressions.

    Avoids recompiling the same patterns repeatedly.
    """

    def __init__(self) -> None:
        self._patterns: dict[str, re.Pattern[str]] = {}

    def add(self, name: str, pattern: str, flags: int = 0) -> None:
        """
        Add a named pattern to the cache.

        Args:
            name: Unique name for the pattern.
            pattern: Regular expression string.
            flags: re module flags (e.g., re.IGNORECASE).
        """
        self._patterns[name] = re.compile(pattern, flags)

    def match(self, name: str, text: str) -> re.Match[str] | None:
        """
        Search for a named pattern in text.

        Args:
            name: Name of the pattern to use.
            text: Text to search.

        Returns:
            Match object if found, None otherwise.

        Raises:
            KeyError: If pattern name not found.
        """
        if name not in self._patterns:
            raise KeyError(f"pattern '{name}' not in cache")
        return self._patterns[name].search(text)

    def has(self, name: str) -> bool:
        """Check if a pattern is cached."""
        return name in self._patterns


class WhichCache:
    """
    Cache for shutil.which() results.

    Avoids repeated filesystem lookups for command availability.
    """

    def __init__(self) -> None:
        self._cache: dict[str, str | None] = {}

    def which(self, cmd: str) -> str | None:
        """
        Find full path to a command, with caching.

        Args:
            cmd: Command name to find.

        Returns:
            Full path to command, or None if not found.
        """
        if cmd not in self._cache:
            self._cache[cmd] = shutil.which(cmd)
        return self._cache[cmd]

    def available(self, cmd: str) -> bool:
        """
        Check if a command is available.

        Args:
            cmd: Command name to check.

        Returns:
            True if command exists on PATH.
        """
        return self.which(cmd) is not None

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()


# Global WhichCache instance for convenience
WHICH = WhichCache()
