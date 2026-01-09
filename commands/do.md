---
description: "Smart task execution: /do <task>"
allowed-tools:
  - Bash
  - Task
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - TodoWrite
---

# /do - Execute Tasks Intelligently

## Task: $ARGUMENTS

---

## Quick Decision

| Task Type | What To Do |
|-----------|------------|
| Typo, single file, <3 steps | Just do it directly |
| Research, "where is", "how does" | `Task(subagent_type=Explore)` |
| Multiple independent pieces | Launch parallel Tasks in ONE message |
| Complex, multi-step | Use TodoWrite, delegate to subagents |

## Default Behavior

1. **Analyze** - Is this trivial or complex?
2. **Decompose** - Can it be split into independent pieces?
3. **Execute** - Parallel if independent, sequential if dependent
4. **Validate** - Run tests/checks before declaring done

## For Maximum Power

Just add "ultrawork" to any prompt:
```
ultrawork fix all the type errors
ultrawork refactor the auth system
```

This activates:
- Aggressive parallelization
- Context preservation (delegate large reads)
- Relentless completion (don't stop until done)
- Automatic validation

## Context Rule

Files >100 lines? Don't read directly. Use:
```
Task(subagent_type=Explore, prompt="Summarize [file] focusing on [what you need]")
```

Your context is for reasoning, not storage.
