#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
PreToolUse hook that enforces commit message quality based on diff size.

Intercepts `git commit` commands and validates that the commit message
is appropriately detailed for the size of the changes being committed.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# Add parent directory for hook_utils import
sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    hook_main,
    log_debug,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)


def output_deny(reason: str) -> None:
    """Output denial response for PreToolUse hook."""
    response = {"decision": "deny", "reason": reason}
    print(json.dumps(response))
    sys.exit(0)


def get_staged_diff_stats() -> tuple[int, int]:
    """
    Get statistics about staged changes.

    Returns:
        Tuple of (lines_changed, files_changed)
    """
    try:
        # Get number of lines changed
        result = subprocess.run(
            ["git", "diff", "--cached", "--numstat"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return 0, 0

        lines_added = 0
        lines_deleted = 0
        files_changed = 0

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                files_changed += 1
                # Handle binary files (shown as -)
                if parts[0] != "-":
                    lines_added += int(parts[0])
                if parts[1] != "-":
                    lines_deleted += int(parts[1])

        return lines_added + lines_deleted, files_changed

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
        return 0, 0


def extract_commit_message(command: str) -> str | None:
    """
    Extract commit message from a git commit command.

    Handles:
    - git commit -m "message"
    - git commit -m 'message'
    - git commit -m "$(cat <<'EOF'\nmessage\nEOF\n)"
    """
    # Pattern for -m "message" or -m 'message'
    simple_pattern = r'-m\s+["\'](.+?)["\']'
    match = re.search(simple_pattern, command, re.DOTALL)
    if match:
        return match.group(1)

    # Pattern for HEREDOC: -m "$(cat <<'EOF' ... EOF )"
    heredoc_pattern = r'-m\s+"\$\(cat\s+<<[\'"]?EOF[\'"]?\s*\n(.+?)\nEOF\s*\)"'
    match = re.search(heredoc_pattern, command, re.DOTALL)
    if match:
        return match.group(1)

    # Alternative HEREDOC without quotes
    heredoc_pattern2 = r"-m\s+'\$\(cat\s+<<['\"]?EOF['\"]?\s*\n(.+?)\nEOF\s*\)'"
    match = re.search(heredoc_pattern2, command, re.DOTALL)
    if match:
        return match.group(1)

    return None


def count_message_body_lines(message: str) -> int:
    """Count non-empty lines in the commit message body (after subject)."""
    lines = message.strip().split("\n")

    if len(lines) <= 1:
        return 0

    # Skip subject line and blank line after it
    body_lines = []
    in_body = False

    for i, line in enumerate(lines[1:], start=1):
        if not in_body:
            if line.strip() == "":
                in_body = True
            continue
        if line.strip():
            body_lines.append(line)

    return len(body_lines)


def evaluate_message_quality(
    message: str,
    lines_changed: int,
    files_changed: int
) -> tuple[bool, str]:
    """
    Evaluate if commit message quality matches the change size.

    Returns:
        Tuple of (is_acceptable, reason_if_not)
    """
    body_lines = count_message_body_lines(message)
    subject = message.strip().split("\n")[0] if message else ""

    log_debug(
        f"Evaluating: {lines_changed} lines, {files_changed} files, "
        f"{body_lines} body lines, subject: '{subject[:50]}...'"
    )

    # Trivial changes (< 10 lines, 1-2 files): subject-only is fine
    if lines_changed < 10 and files_changed <= 2:
        return True, ""

    # Small changes (10-50 lines): need at least some context
    if lines_changed < 50:
        if body_lines == 0:
            return False, (
                f"This commit changes {lines_changed} lines across {files_changed} file(s). "
                f"Add a commit body explaining WHY these changes were made. "
                f"Example:\n\n"
                f"{subject}\n\n"
                f"Brief explanation of the problem and solution approach."
            )
        return True, ""

    # Medium changes (50-200 lines): need proper body
    if lines_changed < 200:
        if body_lines < 2:
            return False, (
                f"This commit changes {lines_changed} lines across {files_changed} file(s). "
                f"The commit body should have at least 2-3 lines explaining:\n"
                f"- What problem this solves\n"
                f"- How you approached it\n"
                f"- Any notable decisions or tradeoffs"
            )
        return True, ""

    # Large changes (200+ lines): need detailed explanation
    if body_lines < 4:
        return False, (
            f"This commit changes {lines_changed} lines across {files_changed} file(s). "
            f"Large changes require detailed commit messages. Include:\n"
            f"- Context: What problem does this solve?\n"
            f"- Approach: How did you solve it?\n"
            f"- Changes: List the key modifications (use bullet points)\n"
            f"- Impact: What does this enable or fix?\n\n"
            f"Use bullet points to organize multiple changes."
        )

    return True, ""


@hook_main("PreToolUse")
def main() -> None:
    """Main hook entry point."""
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    tool_name = data.get("tool_name", "")

    # Only intercept Bash commands
    if tool_name != "Bash":
        output_empty()
        return

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    # Only intercept git commit commands
    if not re.search(r"\bgit\s+commit\b", command):
        output_empty()
        return

    log_debug(f"Intercepted git commit: {command[:100]}...")

    # Skip if this is --amend without a new message (editing existing)
    if "--amend" in command and "-m" not in command:
        log_debug("Skipping --amend without -m (interactive edit)")
        output_empty()
        return

    # Extract the commit message
    message = extract_commit_message(command)

    if not message:
        log_debug("Could not extract commit message, allowing through")
        output_empty()
        return

    # Get diff statistics
    lines_changed, files_changed = get_staged_diff_stats()

    if lines_changed == 0 and files_changed == 0:
        log_debug("No staged changes detected, allowing through")
        output_empty()
        return

    # Evaluate message quality
    is_acceptable, reason = evaluate_message_quality(
        message, lines_changed, files_changed
    )

    if not is_acceptable:
        log_debug(f"Denying commit: {reason[:100]}...")
        output_deny(
            f"[Commit Quality Check Failed]\n\n{reason}\n\n"
            f"Rewrite the commit message with more detail and try again."
        )

    log_debug("Commit message quality acceptable")
    output_empty()


if __name__ == "__main__":
    main()
