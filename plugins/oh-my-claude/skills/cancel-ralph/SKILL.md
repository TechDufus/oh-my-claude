---
name: cancel-ralph
description: "Cancel an active Ralph Loop and clean up state files. Triggers on: '/cancel-ralph', 'cancel ralph', 'stop ralph', 'kill ralph loop', 'abort ralph'."
allowed-tools:
  - Bash
  - Read
---

# Cancel Ralph Skill

Stop an active Ralph Loop and remove all state files.

## When This Skill Activates

| Category | Trigger Phrases |
|----------|-----------------|
| **Cancel** | `/cancel-ralph`, `cancel ralph`, `stop ralph` |
| **Abort** | `kill ralph loop`, `abort ralph`, `end ralph` |

## Workflow

### Step 1: Check for Active Ralph Loop

Check if `.claude/ralph/` directory exists:

```bash
if [ -d ".claude/ralph" ]; then
  echo "ACTIVE"
else
  echo "INACTIVE"
fi
```

### Step 2: Handle State

**If INACTIVE:**
```
No active Ralph Loop found. Nothing to cancel.
```

**If ACTIVE:**

1. Remove the ralph state directory:
```bash
rm -rf .claude/ralph
```

2. Confirm removal:
```
Ralph Loop cancelled.

Removed:
- .claude/ralph/ (all state files)

The loop will not continue on next session.
```

## State Directory Structure

The Ralph Loop stores state in `.claude/ralph/`:

| File | Purpose |
|------|---------|
| `state.json` | Current loop state and iteration |
| `tasks.md` | Pending tasks for the loop |
| `history.md` | Completed iterations log |

All files are removed on cancel.

## Behavior Rules

### MUST DO

- Check if ralph loop exists before attempting removal
- Remove only `.claude/ralph/` directory
- Confirm what was removed

### MUST NOT

- Delete anything outside `.claude/ralph/`
- Fail silently if directory doesn't exist
- Leave partial state behind

## Output Examples

### No Active Loop

```
No active Ralph Loop found. Nothing to cancel.
```

### Successfully Cancelled

```
Ralph Loop cancelled.

Removed: .claude/ralph/

The loop will not continue on next session.
```
