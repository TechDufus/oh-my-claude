#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
todo_enforcer.py
Stop hook: Prevents stopping when todos are incomplete

Called when Claude tries to stop. Returns continuation prompt if work remains.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


def get_incomplete_todos_from_todos(data: dict) -> int:
    """Count incomplete todos from .todos field."""
    todos = data.get("todos") or []
    return sum(1 for t in todos if t.get("status") in ("pending", "in_progress"))


def get_incomplete_todos_from_transcript(data: dict) -> int:
    """Count incomplete todos from last TodoWrite in transcript."""
    transcript = data.get("transcript") or []
    todo_writes = [
        entry for entry in transcript
        if entry.get("type") == "tool_result" and entry.get("tool") == "TodoWrite"
    ]
    if not todo_writes:
        return 0
    last_todos = todo_writes[-1].get("todos") or []
    return sum(1 for t in last_todos if t.get("status") in ("pending", "in_progress"))


def get_completed_todos_from_todos(data: dict) -> int:
    """Count completed todos from .todos field."""
    todos = data.get("todos") or []
    return sum(1 for t in todos if t.get("status") == "completed")


def get_completed_todos_from_transcript(data: dict) -> int:
    """Count completed todos from last TodoWrite in transcript."""
    transcript = data.get("transcript") or []
    todo_writes = [
        entry for entry in transcript
        if entry.get("type") == "tool_result" and entry.get("tool") == "TodoWrite"
    ]
    if not todo_writes:
        return 0
    last_todos = todo_writes[-1].get("todos") or []
    return sum(1 for t in last_todos if t.get("status") == "completed")


def get_last_assistant_message(data: dict) -> str:
    """Extract the last assistant message from transcript."""
    transcript = data.get("transcript") or []
    assistant_messages = [
        entry for entry in transcript
        if entry.get("role") == "assistant"
    ]
    if not assistant_messages:
        return ""
    return assistant_messages[-1].get("content") or ""


def has_uncommitted_changes(cwd: str) -> bool:
    """Check if git repo has uncommitted changes."""
    git_dir = Path(cwd) / ".git"
    if not git_dir.is_dir():
        return False
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return bool(result.stdout.strip())
    except (subprocess.SubprocessError, OSError):
        return False


def validation_ran(data: dict) -> bool:
    """Check if validation was triggered in recent transcript."""
    transcript = data.get("transcript") or []
    for entry in transcript:
        entry_type = entry.get("type", "")
        # Check for Task tool with validator
        if entry_type == "tool_use" and entry.get("tool") == "Task":
            input_data = entry.get("input") or {}
            input_str = str(input_data).lower()
            if "validator" in input_str:
                return True
        # Check for assistant messages mentioning validation
        if entry_type == "assistant":
            content = (entry.get("content") or "").lower()
            if re.search(r"validator|validation|oh-my-claude:validator", content, re.IGNORECASE):
                return True
    return False


def output_block(reason: str, context: str) -> None:
    """Output a block decision with context."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "decision": "block",
            "reason": reason,
            "additionalContext": context
        }
    }
    print(json.dumps(output))


def main() -> None:
    # Read input from stdin
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    # Extract stop reason
    stop_reason = data.get("stopReason") or data.get("stop_reason") or "unknown"

    # Allow explicit user interrupts
    if stop_reason in ("user_interrupt", "explicit_stop", "user_cancelled", "abort"):
        sys.exit(0)

    # Check for incomplete todos
    incomplete_todos = get_incomplete_todos_from_todos(data)
    if incomplete_todos == 0:
        incomplete_todos = get_incomplete_todos_from_transcript(data)

    # If incomplete todos exist, inject strong continuation
    if incomplete_todos > 0:
        context = f"""[TODO CONTINUATION - CANNOT STOP]

You have {incomplete_todos} incomplete task(s) in your todo list.

## Rules
- You CANNOT stop until ALL todos are marked 'completed'
- Review your TodoWrite list immediately
- Continue with the next 'pending' or 'in_progress' item
- Do NOT ask for permission - just continue working

## Next Action
Use TodoWrite to review your current tasks, then proceed with the next incomplete item.

CONTINUE WORKING NOW."""
        output_block("Incomplete todos remain", context)
        sys.exit(0)

    # Check for incomplete work patterns in last message
    last_message = get_last_assistant_message(data)

    # Patterns suggesting premature stopping
    premature_patterns = [
        "let me know if you",
        "feel free to ask",
        "if you want me to",
        "would you like me to continue",
        "I can continue if",
        "shall I proceed",
        "want me to",
    ]

    for pattern in premature_patterns:
        if pattern.lower() in last_message.lower():
            # Check if there's uncommitted work suggesting incomplete task
            cwd = data.get("cwd") or "."
            if has_uncommitted_changes(cwd):
                context = """[INCOMPLETE WORK DETECTED]

Your message suggests you're waiting for permission, but there appear to be uncommitted changes.

If you were in ULTRAWORK mode or working on a task:
1. Check if all requested work is complete
2. Run validation if applicable
3. Complete the task fully before stopping

Do NOT ask - just finish the work."""
                output_block("Uncommitted changes with incomplete work pattern", context)
                sys.exit(0)

    # Check if todos existed (work was done) - count completed todos
    completed_todos = get_completed_todos_from_todos(data)
    if completed_todos == 0:
        completed_todos = get_completed_todos_from_transcript(data)

    # If work was done (completed todos exist), check validation status
    if completed_todos > 0:
        if not validation_ran(data):
            # Validation hasn't run yet - inject prompt to run validator
            context = f"""[AUTO-VALIDATION REQUIRED]

All {completed_todos} todo(s) are marked completed. Before stopping, you MUST run validation.

## Required Action
Use Task with subagent_type="oh-my-claude:validator" to verify the work:
- Run relevant tests
- Check for linting errors
- Verify the implementation matches requirements

Do NOT stop until validation passes. Run the validator now."""
            output_block("Validation required before completion", context)
            sys.exit(0)
        else:
            # Validation already ran - inject completion summary prompt
            context = """[COMPLETION SUMMARY REQUIRED]

Work is complete and validated. Before stopping, provide a brief completion summary:

## Summary Format
1. **What was accomplished** - List the main changes/features implemented
2. **Files modified** - Key files that were changed
3. **Validation results** - Brief note on test/lint status

Provide this summary now, then you may stop."""
            output_block("Completion summary required", context)
            sys.exit(0)

    # No intervention needed - allow stop
    sys.exit(0)


if __name__ == "__main__":
    main()
