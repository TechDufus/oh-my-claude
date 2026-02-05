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

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from hook_utils import (
    RegexCache,
    hook_main,
    log_debug,
    output_empty,
    output_stop_block,
    parse_bool_env,
    parse_hook_input,
    read_stdin_safe,
)

# =============================================================================
# Pre-compiled patterns
# =============================================================================

PATTERNS = RegexCache()
PATTERNS.add("validator", r"validator|validation|oh-my-claude:validator", re.IGNORECASE)

# =============================================================================
# Transcript analysis
# =============================================================================


def analyze_transcript(transcript: list[dict[str, Any]], max_entries: int = 1000) -> dict[str, Any]:
    """
    Single-pass transcript analysis with safety limit.

    Collects:
    - last_assistant_message: Content of last assistant message
    - validation_ran: Whether validation was triggered
    - last_todo_write: Todos from the last TodoWrite tool result

    Args:
        transcript: List of transcript entries.
        max_entries: Maximum entries to process (safety guard).

    Returns:
        Dictionary with analysis results.
    """
    result: dict[str, Any] = {
        "last_assistant_message": "",
        "validation_ran": False,
        "last_todo_write": None,
        "last_task_list": None,  # Track TaskList tool results
    }

    for i, entry in enumerate(transcript):
        if i >= max_entries:
            log_debug(f"transcript truncated at {max_entries} entries")
            break

        entry_type = entry.get("type", "")
        entry_role = entry.get("role", "")

        # Track last assistant message
        if entry_role == "assistant":
            content = entry.get("content") or ""
            if content:
                result["last_assistant_message"] = content

        # Track TodoWrite results
        if entry_type == "tool_result" and entry.get("tool") == "TodoWrite":
            todos = entry.get("todos")
            if todos is not None:
                result["last_todo_write"] = todos

        # Track TaskList results (complete state snapshot)
        if entry_type == "tool_result" and entry.get("tool") == "TaskList":
            tasks = entry.get("tasks")
            if tasks is not None:
                result["last_task_list"] = tasks

        # Check for validation triggers
        if not result["validation_ran"]:
            # Check Task tool with validator
            if entry_type == "tool_use" and entry.get("tool") == "Task":
                input_data = entry.get("input") or {}
                input_str = str(input_data).lower()
                if "validator" in input_str:
                    result["validation_ran"] = True

            # Check assistant messages mentioning validation
            if entry_role == "assistant":
                content = (entry.get("content") or "")
                if PATTERNS.match("validator", content):
                    result["validation_ran"] = True

    return result


def get_incomplete_todos_from_todos(data: dict[str, Any]) -> int:
    """Count incomplete todos from .todos field."""
    todos = data.get("todos") or []
    return sum(1 for t in todos if t.get("status") in ("pending", "in_progress"))


def get_completed_todos_from_todos(data: dict[str, Any]) -> int:
    """Count completed todos from .todos field."""
    todos = data.get("todos") or []
    return sum(1 for t in todos if t.get("status") == "completed")


def count_todos_by_status(todos: list[dict[str, Any]] | None) -> tuple[int, int]:
    """
    Count incomplete and completed todos from a list.

    Returns:
        Tuple of (incomplete_count, completed_count).
    """
    if not todos:
        return 0, 0
    incomplete = sum(1 for t in todos if t.get("status") in ("pending", "in_progress"))
    completed = sum(1 for t in todos if t.get("status") == "completed")
    return incomplete, completed


def count_tasks_by_status(task_list: list[dict[str, Any]] | None) -> tuple[int, int]:
    """
    Count incomplete (pending/in_progress) and completed tasks.

    Returns:
        Tuple of (incomplete_count, completed_count).
    """
    if not task_list:
        return 0, 0
    incomplete = sum(1 for t in task_list if t.get("status") in ("pending", "in_progress"))
    completed = sum(1 for t in task_list if t.get("status") == "completed")
    return incomplete, completed


def should_use_task_system() -> bool:
    """Check if Task system is enabled (default: True)."""
    return parse_bool_env("OMC_USE_TASK_SYSTEM", default=True)


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


def check_git_uncommitted(cwd: str | None = None) -> bool:
    """Check if there are uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        return bool(result.stdout.strip()) if result.returncode == 0 else False
    except Exception:
        return False


def check_active_plans(cwd: str | None = None) -> list[str]:
    """Check for active plan drafts in .claude/plans/drafts/."""
    draft_dir = Path(cwd or ".") / ".claude" / "plans" / "drafts"
    if not draft_dir.exists():
        return []
    drafts = list(draft_dir.glob("*.md"))
    return [d.name for d in drafts]


def should_check_git() -> bool:
    """Check if git check is enabled via env var."""
    return parse_bool_env("OMC_STOP_CHECK_GIT", default=False)


def should_check_plans() -> bool:
    """Check if plan check is enabled via env var."""
    return parse_bool_env("OMC_STOP_CHECK_PLANS", default=True)


def do_output_block(reason: str, context: str) -> None:
    """Output a block decision for Stop hook."""
    output_stop_block(reason, context)


@hook_main("Stop")
def main() -> None:
    # Read input safely
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    # Extract stop reason
    stop_reason = data.get("stopReason") or data.get("stop_reason") or "unknown"

    # Allow explicit user interrupts
    if stop_reason in ("user_interrupt", "explicit_stop", "user_cancelled", "abort"):
        output_empty()

    # Analyze transcript once
    transcript = data.get("transcript") or []
    analysis = analyze_transcript(transcript)

    # 2-level detection: Task system preferred, TodoWrite fallback
    if should_use_task_system():
        task_incomplete, task_completed = count_tasks_by_status(analysis["last_task_list"])
    else:
        task_incomplete, task_completed = 0, 0

    # Fall back to TodoWrite if no Task data
    if task_incomplete == 0 and task_completed == 0:
        # First try .todos field from hook input
        todo_incomplete = get_incomplete_todos_from_todos(data)
        todo_completed = get_completed_todos_from_todos(data)

        # Then try transcript if no .todos field
        if todo_incomplete == 0 and todo_completed == 0:
            todo_incomplete, todo_completed = count_todos_by_status(
                analysis["last_todo_write"]
            )

        incomplete_todos = todo_incomplete
        completed_todos = todo_completed
    else:
        incomplete_todos = task_incomplete
        completed_todos = task_completed

    # Collect all issues that should prevent stopping
    cwd = data.get("cwd") or "."
    issues: list[str] = []

    # Check 1: Incomplete tasks/todos
    if incomplete_todos > 0:
        issues.append(f"Open tasks: {incomplete_todos} remaining")

    # Check 2: Active plan drafts (if enabled)
    if should_check_plans():
        active_drafts = check_active_plans(cwd)
        if active_drafts:
            issues.append(f"Active plan drafts: {', '.join(active_drafts)}")

    # Check 3: Uncommitted git changes (if enabled)
    if should_check_git():
        if check_git_uncommitted(cwd):
            issues.append("Uncommitted changes present")

    # If any issues exist, block with combined message
    if issues:
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        context = f"""[WORK INCOMPLETE - CANNOT STOP]

The following issues prevent stopping:
{issues_text}

## Rules
- You CANNOT stop until ALL issues are resolved
- For open tasks: Use TaskList to verify all tasks completed, then continue working
- For active plans: Complete or archive the plan drafts
- For uncommitted changes: Commit or stash the changes
- Do NOT ask for permission - just continue working

## Task System Patterns

If you have open tasks, consider these approaches:

**Sequential work:** Mark task in_progress, complete it, mark completed, move to next.

**Parallel work:** Delegate to agents with owner assignment:
```
TaskUpdate(taskId="1", owner="worker-a")
Task(subagent_type="general-purpose", prompt="You are worker-a. Find your tasks via TaskList...")
```

**Blocked tasks:** Check if blocking tasks are complete, then proceed with unblocked work.

## Next Action
Address the issues above, starting with the most critical.

CONTINUE WORKING NOW."""
        do_output_block("Work incomplete", context)
        output_empty()

    # Check for incomplete work patterns in last message
    last_message = analysis["last_assistant_message"]

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
            if has_uncommitted_changes(cwd):
                context = """[INCOMPLETE WORK DETECTED]

Your message suggests you're waiting for permission, but there appear to be uncommitted changes.

If you were in ULTRAWORK mode or working on a task:
1. Check if all requested work is complete
2. Run validation if applicable
3. Complete the task fully before stopping

Do NOT ask - just finish the work."""
                do_output_block("Uncommitted changes with incomplete work pattern", context)
                output_empty()

    # If work was done (completed todos exist), check validation status
    if completed_todos > 0:
        if not analysis["validation_ran"]:
            # Validation hasn't run yet - inject prompt to run validator
            context = f"""[AUTO-VALIDATION REQUIRED]

All {completed_todos} todo(s) are marked completed. Before stopping, you MUST run validation.

## Required Action
Use Task with subagent_type="oh-my-claude:validator" to verify the work:
- Run relevant tests
- Check for linting errors
- Verify the implementation matches requirements

Do NOT stop until validation passes. Run the validator now."""
            do_output_block("Validation required before completion", context)
            output_empty()
        else:
            # Validation already ran - inject completion summary prompt
            context = """[COMPLETION SUMMARY REQUIRED]

Work is complete and validated. Before stopping, provide a brief completion summary:

## Summary Format
1. **What was accomplished** - List the main changes/features implemented
2. **Files modified** - Key files that were changed
3. **Validation results** - Brief note on test/lint status

Provide this summary now, then you may stop."""
            do_output_block("Completion summary required", context)
            output_empty()

    # No intervention needed - allow stop
    output_empty()


if __name__ == "__main__":
    main()
