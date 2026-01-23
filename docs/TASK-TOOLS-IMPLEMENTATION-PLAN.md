# Task Tools Migration Implementation Plan

## Overview

Migrate oh-my-claude from TodoWrite to the new Task* tools while maintaining backwards compatibility.

---

## Phase 1: Hook Updates (Critical Path)

### 1.1 todo_enforcer.py

**Current behavior (line 78):**
```python
if entry_type == "tool_result" and entry.get("tool") == "TodoWrite":
    todos = entry.get("todos")
```

**Required changes:**

1. Add detection for Task* tool results:
```python
# Track TodoWrite results (legacy)
if entry_type == "tool_result" and entry.get("tool") == "TodoWrite":
    todos = entry.get("todos")
    if todos is not None:
        result["last_todo_write"] = todos

# Track Task tool results (new system)
if entry_type == "tool_result" and entry.get("tool") in ("TaskCreate", "TaskUpdate", "TaskList"):
    # TaskList returns task array, TaskUpdate/Create return single task
    tasks = entry.get("tasks") or entry.get("result", {}).get("tasks")
    if tasks is not None:
        result["last_task_list"] = tasks
```

2. Update `get_incomplete_todos_from_todos()` to handle both formats:
```python
def get_incomplete_items(data: dict[str, Any]) -> int:
    """Count incomplete items from either todos or tasks field."""
    # Try new Task system first
    tasks = data.get("tasks") or []
    if tasks:
        return sum(1 for t in tasks if t.get("status") in ("pending", "in_progress"))

    # Fall back to legacy TodoWrite
    todos = data.get("todos") or []
    return sum(1 for t in todos if t.get("status") in ("pending", "in_progress"))
```

3. Update main enforcement logic to check both `last_todo_write` and `last_task_list`

**Files to modify:**
- `plugins/oh-my-claude/hooks/todo_enforcer.py` (lines 77-81, 101-124, 200-218)

---

### 1.2 precompact_context.py

**Current behavior (lines 120-127):**
```python
for todo in todos[:5]:
    status = todo.get("status", "pending")
    content = todo.get("content", "")[:80]
    todo_str += f"  - [{status}] {content}\n"
```

**Required changes:**

1. Handle both data formats:
```python
def format_task_items(items: list[dict], is_tasks: bool = False) -> str:
    """Format todo/task items for display."""
    if not items:
        return "  (none)\n"

    result = ""
    for item in items[:5]:
        status = item.get("status", "pending")
        # Tasks use 'subject', Todos use 'content'
        content = item.get("subject") or item.get("content") or ""
        content = content[:80]

        # Show task dependencies if present
        blocked = ""
        if is_tasks and item.get("blockedBy"):
            blocked = f" [blocked by: {', '.join(item['blockedBy'])}]"

        result += f"  - [{status}] {content}{blocked}\n"
    return result
```

2. Update section title and extraction:
```python
# Try new Task system first, fall back to todos
tasks = get_nested(data, "tasks", default=[])
todos = get_nested(data, "todos", default=[])

if tasks:
    task_str = format_task_items(tasks, is_tasks=True)
    section_title = "Active Tasks"
else:
    task_str = format_task_items(todos, is_tasks=False)
    section_title = "Active Todos"
```

**Files to modify:**
- `plugins/oh-my-claude/hooks/precompact_context.py` (lines 110-146, 176)

---

### 1.3 ultrawork_detector.py

**Current behavior (lines 266, 337):**
```
2. TODOWRITE IMMEDIATELY - Minimum 3 todos for any non-trivial work.
...
3. Run `TodoWrite` to confirm zero incomplete items
```

**Required changes:**

Update injected instructions to reference Task tools:

```python
# Old
"2. TODOWRITE IMMEDIATELY - Minimum 3 todos for any non-trivial work."

# New
"2. CREATE TASKS IMMEDIATELY - Use TaskCreate for minimum 3 tasks for any non-trivial work. Use TaskUpdate to track progress."

# Old
"3. Run `TodoWrite` to confirm zero incomplete items"

# New
"3. Run `TaskList` to confirm zero incomplete tasks (all status=completed)"
```

Also update:
- Line 318: "Incomplete todos = CANNOT stop" → "Incomplete tasks = CANNOT stop"
- Line 324: "ALL todos marked completed" → "ALL tasks marked completed"

**Files to modify:**
- `plugins/oh-my-claude/hooks/ultrawork_detector.py` (lines 266, 318, 324, 337)

---

## Phase 2: Agent Updates

### 2.1 orchestrator.md

**Current behavior:**
- Line 9: Lists `TodoWrite` in tools
- Lines 240-288: "Todo State Management" section
- Lines 269-288: TodoWrite example flow

**Required changes:**

1. Update tools list:
```yaml
tools:
  - TaskCreate
  - TaskGet
  - TaskUpdate
  - TaskList
  # ... other tools
```

2. Rename section: "Todo State Management" → "Task State Management"

3. Update state transition examples to use Task tools:
```markdown
TaskCreate: subject="Find auth patterns"
  → Task #1 created (pending)

TaskUpdate: taskId=1, status="in_progress"
  → Task #1 now active

Delegate to scout...
Verify result...

TaskUpdate: taskId=1, status="completed"
  → Task #1 done, move to next
```

4. Add dependency documentation:
```markdown
### Task Dependencies

Use `addBlockedBy` for sequential work:
- TaskCreate: "Implement API" → #2
- TaskUpdate: taskId=2, addBlockedBy=["1"]  // Waits for #1

Use parallel tasks when independent:
- TaskCreate: "Write tests for module A" → #3
- TaskCreate: "Write tests for module B" → #4
- Both can be worked simultaneously
```

**Files to modify:**
- `plugins/oh-my-claude/agents/orchestrator.md` (lines 9, 52, 87, 240-288, 348-381)

---

## Phase 3: Skill Updates

### 3.1 ralph-loop/SKILL.md

**Current behavior (line 139):**
```
3. Initialize TodoWrite with the task breakdown
```

**Required changes:**

1. Update initialization:
```markdown
3. Create tasks with TaskCreate for each work item in the breakdown
```

2. Update completion criteria (line 193):
```markdown
- All tasks marked completed (TaskList shows no pending/in_progress)
```

3. Update MUST DO rules (line 343):
```markdown
- Use TaskCreate/TaskUpdate to track all subtasks
```

4. Update example session (line 374):
```markdown
**Claude creates tasks:**
TaskCreate: "Analyze current Express routes"
TaskCreate: "Set up Fastify server"
TaskCreate: "Migrate /api/users routes"
...
```

**Files to modify:**
- `plugins/oh-my-claude/skills/ralph-loop/SKILL.md` (lines 12, 139, 189, 193, 306, 343, 374)

---

### 3.2 ralph-plan/SKILL.md

Similar updates to reference TaskCreate instead of TodoWrite for implementation tracking.

**Files to modify:**
- `plugins/oh-my-claude/skills/ralph-plan/SKILL.md` (lines 12, 234, 242, 256)

---

## Phase 4: Documentation Updates

### 4.1 Plugin CLAUDE.md

**Current behavior (line 103):**
```
| TodoWrite | When helpful | MANDATORY (3+ todos) |
```

**Required changes:**

```markdown
| Task Tools | When helpful | MANDATORY (3+ tasks via TaskCreate) |
```

Also update line 162:
```markdown
- **Task Enforcer** - Prevents stopping with incomplete tasks
```

**Files to modify:**
- `plugins/oh-my-claude/CLAUDE.md` (lines 26, 103, 162)

---

## Implementation Order

| Order | File | Priority | Risk |
|-------|------|----------|------|
| 1 | `hooks/todo_enforcer.py` | Critical | Medium - core enforcement |
| 2 | `hooks/precompact_context.py` | High | Low - display only |
| 3 | `hooks/ultrawork_detector.py` | High | Low - text changes |
| 4 | `agents/orchestrator.md` | Medium | Low - documentation |
| 5 | `skills/ralph-loop/SKILL.md` | Medium | Low - documentation |
| 6 | `skills/ralph-plan/SKILL.md` | Low | Low - documentation |
| 7 | `CLAUDE.md` | Low | Low - documentation |

---

## Testing Strategy

### Unit Tests

1. **todo_enforcer.py tests:**
   - Test with TodoWrite format (backwards compat)
   - Test with Task* format (new system)
   - Test with empty lists
   - Test mixed scenarios

2. **precompact_context.py tests:**
   - Test formatting with todos
   - Test formatting with tasks (including dependencies)
   - Test fallback behavior

### Integration Tests

1. Run full ultrawork flow with Task tools
2. Verify stop hook blocks when tasks incomplete
3. Verify precompact preserves task state
4. Test across context compaction

---

## Rollback Plan

If issues arise:
1. The dual-support approach means TodoWrite still works
2. Revert hook changes, keep documentation as-is
3. Wait for more Task tool stability

---

## Success Criteria

- [ ] todo_enforcer.py detects both TodoWrite and Task* tools
- [ ] precompact_context.py formats both formats correctly
- [ ] ultrawork instructions reference Task tools
- [ ] All existing tests pass
- [ ] New tests cover Task tool scenarios
- [ ] Documentation updated consistently
