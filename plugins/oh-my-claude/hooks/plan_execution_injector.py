#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
plan_execution_injector.py - Inject execution context after plan approval.

Hook type: PostToolUse (matcher: ExitPlanMode)

When ExitPlanMode completes successfully, this hook:
1. Injects execution context into the active session
2. Includes Agent Teams guidance for when teams are available
3. Writes plan state to .claude/plans/.active-plan.json for cross-session continuity
4. Cleans up interview draft files that are no longer needed post-approval

The marker file (created by plan_approved.py) serves as a safety net for
cross-session recovery if the user /clear or restarts before completion.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    hook_main,
    is_teams_enabled,
    log_debug,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# =============================================================================
# AGENT TEAMS SECTION
# =============================================================================
AGENT_TEAMS_SECTION = """
## AGENT TEAMS

When agent teams are available, consider using them for plans with independent
parallel tasks that benefit from inter-agent discussion.

**Good fits:** research/review, new modules, competing hypotheses, cross-layer changes
**Bad fits:** sequential tasks, same-file edits, dependency chains

### How to Use

1. `TeamCreate(team_name="descriptive-name")` — create the team
2. `TaskCreate(subject, description, activeForm)` — create tasks for each work item
3. `Task(subagent_type="general-purpose", team_name="descriptive-name", name="role")` — spawn teammates
4. `TaskUpdate(taskId, owner="role")` — assign tasks to teammates
5. Monitor via `TaskList()` and communicate via `SendMessage(recipient="role")`

### Key Properties

- Each teammate is a full Claude Code session with its own context
- Teammates communicate via shared task list and mailbox messaging
- The lead coordinates; teammates self-claim unblocked tasks
- Teammates load project CLAUDE.md but NOT the lead's conversation history
- Token cost scales with teammate count - use only when parallel value justifies it

### Rules

- Avoid assigning the same file to multiple teammates (causes overwrites)
- Include task-specific context in spawn prompts (teammates don't inherit history)
- Monitor progress and redirect approaches that aren't working
- Use subagents (Task tool) for focused work that only needs results back
"""


def build_execution_context() -> str:
    """Build execution context, including Agent Teams guidance."""
    sections = []
    teams_active = is_teams_enabled()

    if teams_active:
        # Team-first: AGENT_TEAMS_SECTION is primary, no delegation table
        sections.append("""[PLAN APPROVED - READY FOR EXECUTION]

Your plan has been approved. When you return to execute:

## EXECUTION PROTOCOL

1. **Create team** - `TeamCreate(team_name="...")` with a descriptive name
2. **Create tasks** - `TaskCreate(...)` for EACH plan item with descriptions
3. **Spawn teammates** - `Task(subagent_type="general-purpose", team_name="...", name="role")` per role
4. **Assign work** - `TaskUpdate(taskId, owner="role")` to assign tasks to teammates
5. **Monitor + verify** - `TaskList()` to track progress, run validation after changes
6. **Do NOT deviate** - The plan was researched and approved""")

        sections.append(AGENT_TEAMS_SECTION)
    else:
        # Solo mode: delegation table with supplementary teams info
        sections.append("""[PLAN APPROVED - READY FOR EXECUTION]

Your plan has been approved. When you return to execute:

## EXECUTION PROTOCOL

1. **Create todos** - Convert plan checkboxes to TaskCreate items
2. **Execute in order** - Follow the plan's execution sequence
3. **Delegate to agents** - Use general-purpose agents for implementation
4. **Verify each step** - Run validation after significant changes
5. **Do NOT deviate** - The plan was researched and approved

## AGENT DELEGATION TABLE

| Task Type | Agent | When to Use |
|-----------|-------|-------------|
| Find files | Explore (built-in) | Locating code, definitions |
| Read content | oh-my-claude:librarian | Summarizing files >500 lines |
| Implement | general-purpose (built-in) | Writing actual code changes |
| Validate | oh-my-claude:validator | Running tests, linters |""")

        sections.append(AGENT_TEAMS_SECTION)

    sections.append("""## PLAN COMPLIANCE

| Allowed | NOT Allowed |
|---------|-------------|
| Following plan exactly | Adding unplanned features |
| Minor implementation details | Changing architecture |
| Asking about ambiguities | Scope expansion |

## STATE TRACKING

Plan state saved to `.claude/plans/.active-plan.json`.
If you `/clear` or start a new session, check this file for active plan context.
Draft interview notes in `.claude/plans/drafts/` have been cleaned up.""")

    return "\n".join(sections)


def track_plan_state(data: dict, cwd: str) -> None:
    """Write active plan state for cross-session continuity."""
    try:
        plans_dir = Path(cwd) / ".claude" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)

        state_file = plans_dir / ".active-plan.json"
        state = {
            "status": "executing",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "session_id": data.get("session_id", "unknown"),
        }
        state_file.write_text(json.dumps(state, indent=2) + "\n")
        log_debug(f"Wrote plan state to {state_file}")
    except Exception as e:
        log_debug(f"Failed to write plan state: {e}")


def cleanup_drafts(cwd: str) -> None:
    """Remove interview draft files after plan approval."""
    try:
        drafts_dir = Path(cwd) / ".claude" / "plans" / "drafts"
        if drafts_dir.is_dir():
            for draft in drafts_dir.glob("*.md"):
                draft.unlink()
                log_debug(f"Cleaned up draft: {draft}")
            # Remove drafts dir if empty
            if not any(drafts_dir.iterdir()):
                drafts_dir.rmdir()
                log_debug("Removed empty drafts directory")
    except Exception as e:
        log_debug(f"Draft cleanup failed: {e}")


@hook_main("ExitPlanMode")
def main() -> None:
    """Inject execution context immediately after plan approval."""
    log_debug("=== plan_execution_injector.py ENTRY ===")
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        log_debug("No data, exiting early")
        output_empty()
        return

    # PostToolUse only - check for tool_result
    # PreToolUse/PermissionRequest won't have tool_result
    if "tool_result" not in data:
        log_debug("No tool_result (not PostToolUse), skipping")
        output_empty()
        return

    context = build_execution_context()
    log_debug("Injecting execution context")
    output_context("PostToolUse", context)

    # Track plan state and clean up drafts
    cwd = data.get("cwd", ".")
    track_plan_state(data, cwd)
    cleanup_drafts(cwd)

    log_debug("=== plan_execution_injector.py EXIT ===")


if __name__ == "__main__":
    main()
