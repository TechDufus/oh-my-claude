#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
edit_error_recovery.py
PostToolUse hook: Detects Edit tool failures and injects recovery guidance.
"""

from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    get_nested,
    hook_main,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# Error patterns to detect (case insensitive)
ERROR_PATTERNS = [
    re.compile(r"old_string not found", re.IGNORECASE),
    re.compile(r"old_string found multiple times", re.IGNORECASE),
    re.compile(r"old_string and new_string must be different", re.IGNORECASE),
]

RECOVERY_MESSAGE = """[Edit Error Recovery]

The edit failed. Before retrying:

1. READ the file to see its current state
2. VERIFY the exact content you want to replace (copy from output)
3. Retry with the EXACT string from the file

Common causes:
- File was modified since you last read it
- Whitespace/indentation mismatch
- Content doesn't exist as expected"""


def has_edit_error(tool_output: str) -> bool:
    """Check if tool output contains any known edit error patterns."""
    for pattern in ERROR_PATTERNS:
        if pattern.search(tool_output):
            return True
    return False


@hook_main("PostToolUse")
def main() -> None:
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        return output_empty()

    # Only process Edit tool
    tool_name = get_nested(data, "tool_name", default="")
    if tool_name != "Edit":
        return output_empty()

    # Get tool output/result
    tool_output = get_nested(data, "tool_result", default="")
    if not tool_output:
        tool_output = get_nested(data, "tool_output", default="")
    if not tool_output:
        return output_empty()

    # Convert to string if needed
    if not isinstance(tool_output, str):
        tool_output = str(tool_output)

    # Check for error patterns
    if has_edit_error(tool_output):
        output_context("PostToolUse", RECOVERY_MESSAGE)
    else:
        return output_empty()


if __name__ == "__main__":
    main()
