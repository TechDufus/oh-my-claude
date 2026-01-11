#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""
context_guardian.py
SessionStart hook: Establishes context protection as STANDARD OPERATING PROCEDURE
This runs every session - context protection is not optional

For subagents (when agent_type is set), we skip the SOP since:
- Subagents already run in isolated context
- They don't need orchestration instructions
- Their agent .md file provides specific guidance
"""

from hook_utils import (
    get_nested,
    hook_main,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

CONTEXT = """[oh-my-claude: Context Protection ACTIVE]

## Standard Operating Procedure

Your context window is for REASONING, not storage. This is how you operate.

### File Reading Protocol

| Size | Action |
|------|--------|
| **<100 lines** | Read directly |
| **>100 lines** | `Task(subagent_type="oh-my-claude:librarian")` |
| **Unknown** | Delegate to librarian |
| **Multiple files** | ALWAYS delegate |

### Search Protocol

| Task | Use |
|------|-----|
| Find files | `oh-my-claude:scout` |
| Read files | `oh-my-claude:librarian` |
| Explore | Scout finds → Librarian reads |

### Your Agent Team

| Agent | Use When | Model |
|-------|----------|-------|
| `scout` | Finding files, locating definitions | inherit |
| `librarian` | Reading files, summarizing content | inherit |
| `architect` | Planning complex multi-step work | inherit |
| `worker` | Implementing code changes | inherit |
| `scribe` | Writing documentation | inherit |
| `validator` | Running tests, linters, checks | inherit |

### The Pattern

```
Scout finds → Librarian reads → You reason → Workers implement
```

### Your Role

You are an **orchestrator**, not an implementer. You:
- PLAN what needs to happen
- DELEGATE to specialized agents
- VERIFY results before proceeding
- NEVER implement code yourself when workers can do it

Subagent context is ISOLATED from yours. Use them freely - it costs you nothing."""


@hook_main("SessionStart")
def main() -> None:
    """Inject context protection instructions at session start.

    Skips SOP for subagents (agent_type is set) since they:
    - Already run in isolated context
    - Have their own instructions in their agent .md file
    - Don't need to be told to delegate to themselves
    """
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    # Check if this is a subagent (agent_type is set when --agent is specified)
    agent_type = get_nested(data, "agent_type", default=None)
    if agent_type:
        # Subagent - skip SOP, they have their own instructions
        return output_empty()

    # Main session - inject full context protection SOP
    output_context("SessionStart", CONTEXT)


if __name__ == "__main__":
    main()
