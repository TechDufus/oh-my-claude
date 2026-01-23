#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
plan_execution_injector.py - Inject execution context after plan approval.

Hook type: PostToolUse (matcher: ExitPlanMode)

When ExitPlanMode completes successfully, this hook injects execution context
into the same session. This provides immediate guidance for swarm execution
or manual execution without requiring a new session.

The marker file (created by plan_approved.py) serves as a safety net for
cross-session recovery if the user /clear or restarts before completion.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    get_nested,
    hook_main,
    log_debug,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# =============================================================================
# SWARM EXECUTION CONTEXT - When launchSwarm=true
# =============================================================================
SWARM_EXECUTION_CONTEXT = """[PLAN APPROVED - SWARM EXECUTION ACTIVE]

Your plan is being executed by {teammateCount} parallel workers.

## SWARM COORDINATION PROTOCOL

Workers operate independently. Your role is orchestration:

1. **Monitor progress** - Use TaskList to track teammate work
2. **Handle escalations** - Workers may need decisions or clarification
3. **Verify completion** - When all teammates finish, validate results
4. **Aggregate results** - Ensure all plan items were addressed

## TEAMMATE BEHAVIOR

Each teammate:
- Executes assigned plan tasks independently
- Uses own isolated context window
- Reports completion via task status updates
- Cannot see other teammates' work directly

## IF SWARM FAILS

Marker file exists as safety net. If teammates fail:
1. New session will detect marker
2. Execution context re-injected
3. Continue with subagent orchestration pattern
"""

# =============================================================================
# MANUAL EXECUTION CONTEXT - When no swarm (user will click "Accept and clear")
# =============================================================================
MANUAL_EXECUTION_CONTEXT = """[PLAN APPROVED - READY FOR EXECUTION]

Your plan has been approved. When you return to execute:

## EXECUTION PROTOCOL

1. **Create todos** - Convert plan checkboxes to TaskCreate items
2. **Execute in order** - Follow the plan's execution sequence
3. **Delegate to agents** - Use specialized workers for implementation
4. **Verify each step** - Run validation after significant changes
5. **Do NOT deviate** - The plan was researched and approved

## AGENT DELEGATION TABLE

| Task Type | Agent | When to Use |
|-----------|-------|-------------|
| Find files | oh-my-claude:scout | Locating code, definitions |
| Read content | oh-my-claude:librarian | Summarizing, understanding |
| Implement | oh-my-claude:worker | Writing actual code changes |
| Validate | oh-my-claude:validator | Running tests, linters |
| Debug | oh-my-claude:debugger | When stuck after 2+ attempts |

## PLAN COMPLIANCE

| Allowed | NOT Allowed |
|---------|-------------|
| Following plan exactly | Adding unplanned features |
| Minor implementation details | Changing architecture |
| Asking about ambiguities | Scope expansion |
"""


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

    tool_input = get_nested(data, "tool_input", default={})
    swarm_launched = tool_input.get("launchSwarm", False)
    teammate_count = tool_input.get("teammateCount", 0)

    log_debug(f"launchSwarm: {swarm_launched}, teammateCount: {teammate_count}")

    if swarm_launched and teammate_count > 0:
        # Swarm teammates will execute - provide coordination guidance
        context = SWARM_EXECUTION_CONTEXT.format(teammateCount=teammate_count)
        log_debug("Injecting SWARM_EXECUTION_CONTEXT")
        output_context("PostToolUse", context)
    else:
        # No swarm - user will likely "Accept and clear"
        # This context appears before the dialog, can influence Claude's summary
        # Primary execution context comes from marker file in next session
        log_debug("Injecting MANUAL_EXECUTION_CONTEXT")
        output_context("PostToolUse", MANUAL_EXECUTION_CONTEXT)

    log_debug("=== plan_execution_injector.py EXIT ===")


if __name__ == "__main__":
    main()
