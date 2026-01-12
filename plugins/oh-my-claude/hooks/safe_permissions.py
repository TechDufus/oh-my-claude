#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
safe_permissions.py - Auto-approve safe commands for smoother workflow.

PermissionRequest hook that auto-approves:
- Test commands (npm test, pytest, go test, cargo test)
- Lint commands (npm run lint, ruff, go vet, cargo check)
- Type check commands (npm run typecheck, mypy, tsc)
- Readonly git commands (status, diff, log, branch)
- Read/Glob/Grep operations within the project directory

All other commands defer to default behavior ("ask").

Configuration via environment variables:
- OMC_SAFE_PERMISSIONS: Set to "0" or "false" to disable auto-approvals
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Add parent directory for hook_utils import
sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    RegexCache,
    hook_main,
    log_debug,
    output_empty,
    output_permission,
    parse_hook_input,
    read_stdin_safe,
)


def is_enabled() -> bool:
    """Check if safe permissions auto-approval is enabled."""
    val = os.environ.get("OMC_SAFE_PERMISSIONS", "1").lower()
    return val not in ("0", "false", "no", "off")

# =============================================================================
# Safe command patterns
# =============================================================================

SAFE_PATTERNS = RegexCache()

# Node.js test/lint/typecheck commands
SAFE_PATTERNS.add("npm_test", r"^npm\s+(test|run\s+(test|lint|typecheck|check|format))", re.IGNORECASE)
SAFE_PATTERNS.add("npx_test", r"^npx\s+(jest|vitest|mocha|eslint|prettier|tsc)", re.IGNORECASE)
SAFE_PATTERNS.add("yarn_test", r"^yarn\s+(test|lint|typecheck|check|format)", re.IGNORECASE)
SAFE_PATTERNS.add("pnpm_test", r"^pnpm\s+(test|lint|typecheck|check|format)", re.IGNORECASE)

# Python test/lint commands
SAFE_PATTERNS.add("pytest", r"^(pytest|python\s+-m\s+pytest)", re.IGNORECASE)
SAFE_PATTERNS.add("ruff", r"^ruff\s+(check|format)", re.IGNORECASE)
SAFE_PATTERNS.add("mypy", r"^mypy\b", re.IGNORECASE)
SAFE_PATTERNS.add("black", r"^black\s+--check", re.IGNORECASE)
SAFE_PATTERNS.add("uv_pytest", r"^uv\s+run\s+(--with\s+\S+\s+)?pytest", re.IGNORECASE)

# Go test/lint commands
SAFE_PATTERNS.add("go_test", r"^go\s+(test|vet|fmt)", re.IGNORECASE)
SAFE_PATTERNS.add("golint", r"^(golint|staticcheck|golangci-lint)", re.IGNORECASE)

# Rust test/lint commands
SAFE_PATTERNS.add("cargo", r"^cargo\s+(test|check|clippy|fmt)", re.IGNORECASE)

# Git readonly commands (safe to run anytime)
SAFE_PATTERNS.add(
    "git_readonly",
    r"^git\s+(status|diff|log|branch|show|ls-files|rev-parse|describe|tag\s+-l|remote\s+-v)",
    re.IGNORECASE,
)

# Make targets that are typically safe
SAFE_PATTERNS.add("make_safe", r"^make\s+(test|lint|check|fmt|format)$", re.IGNORECASE)

# Shell utilities for inspection (readonly)
SAFE_PATTERNS.add("ls_cmd", r"^ls\b", re.IGNORECASE)
SAFE_PATTERNS.add("cat_cmd", r"^cat\b", re.IGNORECASE)
SAFE_PATTERNS.add("head_tail", r"^(head|tail)\b", re.IGNORECASE)
SAFE_PATTERNS.add("wc_cmd", r"^wc\b", re.IGNORECASE)
SAFE_PATTERNS.add("which_cmd", r"^which\b", re.IGNORECASE)
SAFE_PATTERNS.add("echo_cmd", r"^echo\b", re.IGNORECASE)

# All pattern names for iteration
SAFE_PATTERN_NAMES = [
    "npm_test",
    "npx_test",
    "yarn_test",
    "pnpm_test",
    "pytest",
    "ruff",
    "mypy",
    "black",
    "uv_pytest",
    "go_test",
    "golint",
    "cargo",
    "git_readonly",
    "make_safe",
    "ls_cmd",
    "cat_cmd",
    "head_tail",
    "wc_cmd",
    "which_cmd",
    "echo_cmd",
]


def is_plugin_internal_script(command: str) -> bool:
    """
    Check if command runs a script from within the plugin directory.

    This auto-approves plugin's own scripts regardless of version,
    preventing re-prompts when plugin version changes.

    Args:
        command: The bash command to check.

    Returns:
        True if command references a script within CLAUDE_PLUGIN_ROOT.
    """
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    log_debug(f"CLAUDE_PLUGIN_ROOT='{plugin_root}'")
    log_debug(f"command='{command[:200]}'")

    # Check if the command contains the plugin root path
    if plugin_root and plugin_root in command:
        log_debug(f"command references plugin path: {plugin_root}")
        return True

    # Fallback: check for oh-my-claude skill path pattern (handles cache paths)
    # This works even when CLAUDE_PLUGIN_ROOT isn't set
    # Pattern: .claude/plugins/cache/oh-my-claude/oh-my-claude/*/skills/
    if "oh-my-claude" in command and "/skills/" in command:
        log_debug("command matches oh-my-claude skill pattern")
        return True

    if not plugin_root:
        log_debug("CLAUDE_PLUGIN_ROOT not set and no fallback match")

    return False


def is_path_in_project(path: str) -> bool:
    """
    Check if a path is within the current working directory.

    Args:
        path: The file path to check.

    Returns:
        True if path is within cwd or is a relative path.
    """
    if not path:
        return False

    cwd = os.getcwd()
    log_debug(f"cwd={cwd}, path={path}")

    # Relative paths are always considered safe (they're relative to cwd)
    if not os.path.isabs(path):
        log_debug("relative path - safe")
        return True

    # Resolve to absolute and check if within cwd
    try:
        resolved = os.path.realpath(path)
        cwd_resolved = os.path.realpath(cwd)
        is_within = resolved.startswith(cwd_resolved + os.sep) or resolved == cwd_resolved
        log_debug(f"resolved={resolved}, is_within_cwd={is_within}")
        return is_within
    except (OSError, ValueError) as e:
        log_debug(f"path resolution error: {e}")
        return False


def is_safe_read_tool(tool_name: str, tool_input: dict | str) -> tuple[bool, str | None]:
    """
    Check if a Read/Glob/Grep operation is safe to auto-approve.

    Auto-approves operations within the project directory.

    Args:
        tool_name: The tool being used (Read, Glob, Grep).
        tool_input: The tool's input parameters.

    Returns:
        Tuple of (is_safe, reason_if_safe).
    """
    if tool_name not in ("Read", "Glob", "Grep"):
        return False, None

    # Extract path from tool_input
    if isinstance(tool_input, str):
        path = tool_input
    elif isinstance(tool_input, dict):
        # Read uses file_path, Glob/Grep use path
        path = tool_input.get("file_path") or tool_input.get("path") or ""
    else:
        path = ""

    # If no path specified, Glob/Grep default to cwd which is safe
    if not path and tool_name in ("Glob", "Grep"):
        log_debug(f"{tool_name} with no path defaults to cwd - safe")
        return True, f"{tool_name}_project_dir"

    if is_path_in_project(path):
        return True, f"{tool_name}_project_dir"

    return False, None


def is_safe_command(command: str) -> tuple[bool, str | None]:
    """
    Check if a command matches any safe pattern.

    Args:
        command: The bash command to check.

    Returns:
        Tuple of (is_safe, pattern_name_if_matched).
    """
    command = command.strip()

    # First check: plugin internal scripts (version-agnostic)
    if is_plugin_internal_script(command):
        return True, "plugin_internal_script"

    for pattern_name in SAFE_PATTERN_NAMES:
        if SAFE_PATTERNS.match(pattern_name, command):
            log_debug(f"command matched safe pattern: {pattern_name}")
            return True, pattern_name
    return False, None


@hook_main("PermissionRequest")
def main() -> None:
    """Main entry point for PermissionRequest hook."""
    # Check if hook is enabled
    if not is_enabled():
        log_debug("safe_permissions disabled via OMC_SAFE_PERMISSIONS")
        output_empty()
        return

    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        log_debug("no input data, passing through")
        output_empty()
        return

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Handle Read/Glob/Grep tools - auto-approve within project directory
    if tool_name in ("Read", "Glob", "Grep"):
        log_debug(f"checking {tool_name} tool for project path")
        is_safe, reason = is_safe_read_tool(tool_name, tool_input)
        if is_safe:
            log_debug(f"auto-approving {tool_name} (reason: {reason})")
            output_permission("allow", f"Auto-approved: {reason}")
        else:
            log_debug(f"{tool_name} path outside project, deferring to user")
            output_empty()
        return

    # Handle Bash tool
    if tool_name != "Bash":
        log_debug(f"tool is {tool_name}, not handled - passing through")
        output_empty()
        return

    # Get the command
    if isinstance(tool_input, str):
        # Sometimes tool_input is just the command string
        command = tool_input
    else:
        command = tool_input.get("command", "")

    if not command:
        log_debug("no command found in tool_input")
        output_empty()
        return

    log_debug(f"checking command: {command[:100]}...")

    # Check if command is safe
    is_safe, pattern = is_safe_command(command)
    if is_safe:
        log_debug(f"auto-approving safe command (pattern: {pattern})")
        output_permission("allow", f"Auto-approved: {pattern}")
    else:
        log_debug("command not in safe list, deferring to user")
        output_empty()


if __name__ == "__main__":
    main()
