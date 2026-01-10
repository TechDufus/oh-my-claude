#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""
context_guardian.py
SessionStart hook: Establishes context protection as STANDARD OPERATING PROCEDURE
This runs every session - context protection is not optional
"""

import json
import sys

# Consume stdin (hook input) - not needed for this hook
sys.stdin.read()

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

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": CONTEXT
    }
}

print(json.dumps(output), end="")
