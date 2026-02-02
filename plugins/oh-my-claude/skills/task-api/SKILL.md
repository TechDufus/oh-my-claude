# Task API Reference

Coordination layer for multi-agent orchestration. Track progress, model dependencies, enable agent self-discovery.

## Core Operations

### TaskCreate

```python
TaskCreate(
  subject="Implement auth middleware",        # Required: brief title (imperative)
  description="Add JWT validation to...",    # Required: detailed requirements
  activeForm="Implementing auth middleware", # Optional: spinner text
  metadata={"priority": "high", "tags": []}  # Optional: custom key-values
)
```

### TaskUpdate

```python
TaskUpdate(
  taskId="3",
  status="in_progress",        # pending | in_progress | completed
  owner="scout-1",             # Agent assignment for self-discovery
  addBlockedBy=["1", "2"],     # Tasks that must complete BEFORE this one
  addBlocks=["4"]              # Tasks that CANNOT start until this completes
)
```

### TaskGet / TaskList

```python
TaskGet(taskId="3")   # Full details: subject, description, status, blocks, blockedBy
TaskList()            # Summary: id, subject, status, owner, blockedBy for all tasks
```

## Dependencies

| Direction | Meaning | Example |
|-----------|---------|---------|
| `addBlockedBy` | "I wait for these" | Task 3 waits for 1,2 to complete |
| `addBlocks` | "These wait for me" | Task 1 must finish before 3 starts |

```python
# These are equivalent:
TaskUpdate(taskId="3", addBlockedBy=["1"])
TaskUpdate(taskId="1", addBlocks=["3"])
```

## Status Flow

```
pending -> in_progress    (before execution)
in_progress -> completed  (after verification)
in_progress -> pending    (if retry needed)
```

## Agent Self-Discovery Pattern

Assign tasks to agents via owner, let them find their work:

```python
# 1. Create and assign
TaskCreate(subject="Validate auth changes", description="...")
TaskUpdate(taskId="1", owner="validator-1")

# 2. Agent discovers its tasks
Task(
  subagent_type="oh-my-claude:validator",
  prompt="You are validator-1. Call TaskList, find tasks where owner='validator-1', complete them."
)
```

## Best Practices

- **One in_progress at a time** unless parallel delegation
- **Never mark completed without verification**
- **Update status immediately** when transitioning
- **Keep descriptions atomic** and verifiable
- **Use metadata** for priority, tags, estimates
