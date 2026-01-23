# Claude Code Task Tools Research

## Executive Summary

Claude Code v2.1.16 (released January 22, 2026) introduced a new **Task Management System** that replaces the simpler `TodoWrite` tool with a more sophisticated set of tools: `TaskCreate`, `TaskGet`, `TaskUpdate`, and `TaskList`. This document analyzes the differences and recommends a migration strategy for oh-my-claude.

---

## Tool Comparison

### Old System: TodoWrite

**Single tool** that manages a flat list of todos.

```typescript
interface TodoWriteInput {
  todos: Array<{
    content: string;                              // Task description
    status: 'pending' | 'in_progress' | 'completed';
    activeForm: string;                           // Present tense ("Running tests")
  }>;
}
```

**Characteristics:**
- Overwrites entire todo list on each call
- No task IDs
- No dependencies between tasks
- No task ownership
- No metadata support
- Simple but limited

---

### New System: Task* Tools

**Four separate tools** for CRUD operations on tasks with advanced features.

#### TaskCreate
Creates individual tasks (does NOT overwrite existing tasks).

```typescript
interface TaskCreateInput {
  subject: string;          // Brief title (imperative: "Run tests")
  description: string;      // Detailed requirements
  activeForm?: string;      // Spinner text when in_progress ("Running tests")
  metadata?: Record<string, any>;  // Arbitrary data
}
// Returns: { taskId: string }
```

#### TaskGet
Retrieves a specific task with full details.

```typescript
interface TaskGetInput {
  taskId: string;
}
// Returns: { subject, description, status, blocks, blockedBy, owner, metadata }
```

#### TaskUpdate
Updates task properties and manages dependencies.

```typescript
interface TaskUpdateInput {
  taskId: string;
  status?: 'pending' | 'in_progress' | 'completed';
  subject?: string;
  description?: string;
  activeForm?: string;
  owner?: string;           // Agent name for multi-agent work
  metadata?: Record<string, any>;
  addBlocks?: string[];     // Tasks that cannot start until this completes
  addBlockedBy?: string[];  // Tasks that must complete before this starts
}
```

#### TaskList
Lists all tasks with summary information.

```typescript
// Returns: Array<{
//   id: string;
//   subject: string;
//   status: 'pending' | 'in_progress' | 'completed';
//   owner?: string;
//   blockedBy?: string[];
// }>
```

---

## Feature Comparison Matrix

| Feature | TodoWrite | Task* Tools |
|---------|-----------|-------------|
| Create tasks | Overwrite entire list | Add individual tasks |
| Update tasks | Overwrite entire list | Update specific task by ID |
| Task IDs | No | Yes |
| Dependencies | No | Yes (blocks/blockedBy) |
| Task ownership | No | Yes (owner field) |
| Metadata | No | Yes (arbitrary data) |
| Get single task | No (only full list) | Yes (TaskGet) |
| Parallel workflows | Manual tracking | Built-in dependency graph |
| Multi-agent support | No | Yes (owner + dependencies) |
| Backwards compatible | N/A | No (different API) |

---

## Key Benefits of Task* Tools

### 1. Atomic Operations
- **Before:** Updating one todo required rewriting the entire list
- **After:** Update a single task without touching others

### 2. Task Dependencies
```
TaskCreate: "Set up database schema"     → Task #1
TaskCreate: "Create API endpoints"       → Task #2
TaskCreate: "Write integration tests"    → Task #3

TaskUpdate: taskId=#2, addBlockedBy=["1"]  // API depends on schema
TaskUpdate: taskId=#3, addBlockedBy=["2"]  // Tests depend on API
```
Claude Code can now understand that Task #3 cannot start until #2 completes, which cannot start until #1 completes.

### 3. Multi-Agent Orchestration
```
TaskUpdate: taskId=#1, owner="worker-1"
TaskUpdate: taskId=#2, owner="worker-2"  // Parallel work
```
The orchestrator can assign tasks to specific sub-agents and track who is working on what.

### 4. Rich Task Context
```
TaskCreate:
  subject: "Implement authentication middleware"
  description: "Create JWT validation middleware following pattern in src/middleware/cors.ts..."
  metadata: { priority: "high", estimatedComplexity: "medium", relatedFiles: ["auth.ts"] }
```

### 5. Better Progress Tracking
- TaskList shows which tasks are blocked and by what
- Can identify parallelizable work (tasks with no blockedBy)
- Clear ownership for team coordination

---

## Impact on oh-my-claude

### Files Requiring Updates

| File | Current Usage | Required Changes |
|------|--------------|------------------|
| `hooks/todo_enforcer.py` | Checks `TodoWrite` tool_result | Check Task* tools, handle `tasks` data structure |
| `hooks/ultrawork_detector.py` | Injects `TodoWrite` instructions | Update instructions for Task tools |
| `hooks/precompact_context.py` | Extracts `todos` list | Extract task list, new format |
| `agents/orchestrator.md` | Lists `TodoWrite` as tool | Update tools, state management section |
| `skills/ralph-loop/SKILL.md` | References `TodoWrite` | Update for Task tools |
| `skills/ralph-plan/SKILL.md` | References `TodoWrite` | Update for Task tools |
| `CLAUDE.md` (plugin) | Ultrawork table mentions `TodoWrite` | Update terminology |

### Hook Data Structure Changes

**Old format (TodoWrite):**
```json
{
  "tool": "TodoWrite",
  "todos": [
    { "content": "Task 1", "status": "completed", "activeForm": "..." },
    { "content": "Task 2", "status": "in_progress", "activeForm": "..." }
  ]
}
```

**New format (Task tools):**
```json
{
  "tasks": [
    { "id": "1", "subject": "Task 1", "status": "completed", "owner": "...", "blockedBy": [] },
    { "id": "2", "subject": "Task 2", "status": "in_progress", "owner": "...", "blockedBy": ["1"] }
  ]
}
```

---

## Migration Strategy

### Phase 1: Dual Support (Recommended)
Support both TodoWrite and Task* tools during transition:
- Detect which tool type was used
- Extract status from either format
- Allow gradual adoption

### Phase 2: Prefer Task Tools
Update documentation and instructions to recommend Task tools:
- Update ultrawork instructions to use TaskCreate/TaskUpdate
- Keep TodoWrite detection as fallback
- Monitor adoption

### Phase 3: Full Migration (Optional)
Once Task tools are stable and widely adopted:
- Deprecate TodoWrite references
- Remove fallback code
- Update all documentation

---

## Recommended Implementation Order

1. **todo_enforcer.py** - Critical path, must detect both formats
2. **precompact_context.py** - Context preservation needs new format
3. **ultrawork_detector.py** - Update injected instructions
4. **orchestrator.md** - Update agent capabilities
5. **ralph-loop/SKILL.md** - Update skill instructions
6. **CLAUDE.md** - Update documentation

---

## Testing Considerations

1. **Backwards Compatibility**
   - Ensure hooks still work if TodoWrite is used
   - Test with both old and new tool formats

2. **Edge Cases**
   - Empty task list
   - Tasks with complex dependency chains
   - Tasks with different owners

3. **Integration Testing**
   - Full ultrawork flow with Task tools
   - PreCompact preserves task state correctly
   - Stop hook enforces completion properly

---

## Sources

- [Claude Code v2.1.16 Release Notes](https://github.com/anthropics/claude-code/releases) - Task management system with dependency tracking
- [Claude Agent SDK - Todo Tracking](https://platform.claude.com/docs/en/agent-sdk/todo-tracking) - Original TodoWrite documentation
- [Claude Code Common Workflows](https://code.claude.com/docs/en/common-workflows) - Official workflow documentation
- Claude Code CLI v2.1.17 - Direct tool inspection

---

## Conclusion

The new Task* tools represent a significant improvement over TodoWrite:

1. **Better for complex work** - Dependencies prevent starting work before prerequisites complete
2. **Better for multi-agent** - Ownership tracking enables parallel delegation
3. **Better for context** - Rich metadata and descriptions
4. **Better for UX** - Incremental updates vs full list rewrites

**Recommendation:** Implement dual support immediately, then transition to Task-first approach over time.
