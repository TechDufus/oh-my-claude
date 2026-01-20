---
name: ralph-loop
description: "Start a Ralph Loop - an autonomous iteration pattern for completing complex tasks. Triggers on: '/ralph-loop <prompt>', 'ralph loop', 'start ralph'. Creates state in .claude/ralph/, injects ultrawork mode, and iterates until completion or max iterations reached."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - TodoWrite
---

# Ralph Loop Skill

Autonomous iteration pattern for completing complex tasks without intervention.

## What is a Ralph Loop?

A Ralph Loop is a self-driving execution pattern where Claude:
1. Receives a task prompt
2. Creates persistent state files
3. Works autonomously through iterations
4. Tracks progress in state files
5. Continues until completion or max iterations

Named after the concept of "wreck-it-ralph" - just keep smashing through the work.

## When This Skill Activates

| Category | Trigger Phrases |
|----------|-----------------|
| **Start loop** | `/ralph-loop <prompt>`, `ralph loop`, `start ralph` |
| **Check status** | `ralph status`, `loop status` |
| **Resume loop** | `resume ralph`, `continue ralph` |
| **Stop loop** | `stop ralph`, `end ralph`, `ralph stop` |

## CLI Syntax

```
/ralph-loop <prompt> [--max-iterations=N] [--completion-promise=WORD]
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `prompt` | (required) | The task to complete autonomously |
| `--max-iterations` | 20 | Maximum iterations before stopping |
| `--completion-promise` | DONE | Word to output when complete |

## Examples

```
/ralph-loop refactor all API endpoints to use the new validation pattern
/ralph-loop implement user authentication --max-iterations=30
/ralph-loop fix all linting errors --completion-promise=FINISHED
```

---

## Robustness Features

### Session Isolation

Each Ralph Loop is bound to the session that started it:

- State includes a `sessionId` field matching the originating session
- Loop only triggers for the session that started it
- Prevents cross-session interference when multiple sessions exist
- Other sessions can read state but won't trigger iterations

### Abort Handling

User interrupts (Ctrl+C) are handled gracefully:

- State is cleaned up when the user aborts
- No orphan state files left behind
- Loop can be cleanly restarted after abort
- Prevents stuck loops requiring manual cleanup

### Cooldown Mechanism

Prevents rapid re-triggering after errors:

- 5-second cooldown after any error occurs
- Avoids tight error loops consuming resources
- Cooldown tracked in state as `lastErrorAt` timestamp
- Normal iterations proceed without cooldown

### Orphan Detection

Stale state is automatically cleaned:

- Detects state from crashed or terminated sessions
- Auto-cleans orphaned loops on next activation
- Handles ungraceful exits (crashes, network loss)
- Logs cleanup actions for transparency

---

## Workflow

### Phase 1: Initialization

When triggered with a prompt:

1. Create `.claude/ralph/` directory if it doesn't exist
2. Write state files:

**`.claude/ralph/config.json`:**
```json
{
  "prompt": "<user's prompt>",
  "maxIterations": 20,
  "completionPromise": "DONE",
  "startedAt": "<ISO timestamp>",
  "ultraworkEnabled": true,
  "sessionId": "<session ID>"
}
```

**`.claude/ralph/state.json`:**
```json
{
  "iteration": 1,
  "status": "active",
  "lastUpdated": "<ISO timestamp>",
  "completedTasks": [],
  "currentTask": null,
  "blockers": []
}
```

**`.claude/ralph/prompt.txt`:**
```
<user's original prompt verbatim>
```

3. Initialize TodoWrite with the task breakdown
4. Begin first iteration

### Phase 2: Iteration Loop

Each iteration follows this pattern:

```
1. Read current state from .claude/ralph/state.json
2. Check if status is "active" and iteration <= maxIterations
3. Plan next action based on remaining work
4. Execute the action
5. Update state:
   - Increment iteration
   - Update completedTasks
   - Set currentTask
   - Update lastUpdated
6. Check completion criteria
7. If complete: set status to "complete", output promise
8. If not complete: continue to next iteration
```

### Phase 3: Completion

Loop ends when ANY of these occur:

| Condition | Action |
|-----------|--------|
| All todos complete | Set status="complete", output `<promise>{completionPromise}</promise>` |
| Max iterations reached | Set status="max_iterations", report progress |
| Blocker encountered | Set status="blocked", describe blocker |
| User interrupts | Set status="paused", preserve state for resume |

---

## Injected Prompt Template

When starting a Ralph Loop, the user's prompt is wrapped with these instructions:

```markdown
## Ralph Loop Active

**Original Task:** {prompt}

**Mode:** Ultrawork (automatic)

**Iteration Rules:**
1. Work autonomously - do not ask questions
2. Make reasonable decisions and document them
3. Use TodoWrite to track all subtasks
4. Update .claude/ralph/state.json after each major action
5. Delegate to agents when appropriate (scout, librarian, worker, etc.)
6. Continue until ALL work is complete or blocked

**Completion Criteria:**
- All TodoWrite items marked complete
- No remaining work items
- Code compiles/passes linting
- Changes are coherent and complete

**On Completion:**
Output: <promise>{completionPromise}</promise>

**On Blocker:**
- Document in state.json blockers array
- Set status to "blocked"
- Explain what's blocking and what's needed

**Begin iteration {iteration} of {maxIterations}**
```

---

## State File Formats

### config.json Schema

```json
{
  "prompt": "string - original user prompt",
  "maxIterations": "number - default 20",
  "completionPromise": "string - default DONE",
  "startedAt": "string - ISO timestamp",
  "ultraworkEnabled": "boolean - always true",
  "sessionId": "string - ID of session that started the loop"
}
```

### state.json Schema

```json
{
  "iteration": "number - current iteration (starts at 1)",
  "status": "string - active|complete|blocked|paused|max_iterations",
  "lastUpdated": "string - ISO timestamp",
  "completedTasks": ["array of completed task descriptions"],
  "currentTask": "string|null - what's being worked on now",
  "blockers": ["array of blocker descriptions if any"]
}
```

### prompt.txt

Plain text file containing the original prompt exactly as provided.

---

## Resuming a Loop

When user says "resume ralph" or "continue ralph":

1. Check if `.claude/ralph/state.json` exists
2. Read current state
3. If status is "active" or "paused":
   - Set status to "active"
   - Continue from current iteration
4. If status is "complete":
   - Report: "Ralph Loop already complete. Start a new one?"
5. If status is "blocked":
   - Show blockers
   - Ask: "Blockers resolved? Resume or start fresh?"

---

## Checking Status

When user says "ralph status" or "loop status":

Output current state summary:

```
Ralph Loop Status
-----------------
Prompt: {first 100 chars of prompt}...
Status: {status}
Iteration: {iteration}/{maxIterations}
Started: {startedAt}
Last Updated: {lastUpdated}

Completed Tasks: {count}
- {task1}
- {task2}
...

Current Task: {currentTask or "None"}

Blockers: {count or "None"}
```

---

## Stopping a Loop

When user says "stop ralph" or "end ralph":

1. Update state.json: `status = "paused"`
2. Save current progress
3. Report: "Ralph Loop paused at iteration {n}. Resume with 'resume ralph'."

---

## Integration with Ultrawork

Ralph Loop automatically enables ultrawork mode behaviors:

| Behavior | Setting |
|----------|---------|
| TodoWrite | Mandatory |
| Parallelization | Aggressive |
| Questions | Never (decide and document) |
| Validation | Required before completion |
| Stopping | Only when complete or blocked |

---

## Error Handling

### State Files Missing

If `.claude/ralph/` doesn't exist when checking status:
- Report: "No active Ralph Loop. Start one with `/ralph-loop <prompt>`"

### Corrupted State

If state.json is malformed:
1. Backup corrupted file as `state.json.corrupted`
2. Reset to iteration 1 with status "active"
3. Report: "State was corrupted. Restarting from iteration 1."

### Max Iterations Reached

When iteration > maxIterations:
1. Set status to "max_iterations"
2. Report progress made
3. Ask: "Max iterations ({n}) reached. Continue with more iterations?"

---

## Behavior Rules

### MUST DO

- Create all three state files before starting work
- Update state.json after each significant action
- Use TodoWrite to track all subtasks
- Output completion promise when ALL work is done
- Document decisions made autonomously
- Delegate to agents for appropriate tasks

### MUST NOT

- Ask questions during iteration (decide and document)
- Stop before completion unless blocked or max iterations
- Delete state files without user confirmation
- Skip state updates between iterations
- Ignore blockers (must document and report)

### SHOULD DO

- Break large tasks into manageable subtasks
- Use parallel agent execution when possible
- Validate work before marking complete
- Preserve state for resumability

---

## Example Session

**User:** `/ralph-loop migrate all API routes from Express to Fastify`

**Claude creates:**
- `.claude/ralph/config.json`
- `.claude/ralph/state.json` (iteration: 1, status: active)
- `.claude/ralph/prompt.txt`

**Claude initializes TodoWrite:**
```
[ ] Analyze current Express routes
[ ] Set up Fastify server
[ ] Migrate /api/users routes
[ ] Migrate /api/auth routes
[ ] Migrate /api/products routes
[ ] Update middleware
[ ] Update error handling
[ ] Test all endpoints
[ ] Remove Express dependencies
```

**Claude works through iterations 1-15...**

**Iteration 15 completes final task**

**Claude updates state:**
```json
{
  "iteration": 15,
  "status": "complete",
  "completedTasks": ["Analyzed routes", "Set up Fastify", ...],
  "currentTask": null,
  "blockers": []
}
```

**Claude outputs:**
```
<promise>DONE</promise>
```

---

## Post-Completion Summary

After outputting the completion promise, provide a summary:

```
Ralph Loop Complete
-------------------
Iterations: {final} of {max}
Duration: {time elapsed}
Tasks Completed: {count}

Summary:
{brief description of what was accomplished}

Files Modified:
- {file1}
- {file2}
...
```
