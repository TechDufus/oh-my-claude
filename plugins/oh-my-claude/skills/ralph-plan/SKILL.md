---
name: ralph-plan
description: "Plan-then-execute workflow combining structured planning with autonomous Ralph Loop execution. Triggers on: '/ralph-plan <topic>', 'plan and execute', 'plan then execute', 'smart ralph'. Creates plan via interview and research, requires explicit user approval, then executes via Ralph Loop."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - TodoWrite
  - AskUserQuestion
---

# Ralph Plan Skill

Structured planning with autonomous execution. Plan first, approve, then let Ralph handle it.

## What is Ralph Plan?

Ralph Plan combines the deliberate planning of `/plan` with the autonomous execution of `/ralph-loop`:

1. **Plan Phase** - Interview, research, create structured plan
2. **Approval Gate** - User reviews and approves the plan
3. **Execute Phase** - Ralph Loop executes the approved plan autonomously

This prevents the "ready, fire, aim" problem where autonomous execution starts without clear direction.

## When This Skill Activates

| Category | Trigger Phrases |
|----------|-----------------|
| **Start planning** | `/ralph-plan <topic>`, `plan and execute`, `plan then execute`, `smart ralph` |
| **Check status** | `ralph-plan status` |
| **Resume** | `resume ralph-plan` |

---

## Workflow

### Phase 1: Planning

Create a structured plan before any execution begins.

#### Step 1: Initialize Draft

Create draft at `.claude/plans/drafts/{topic-slug}.md` with template:

```markdown
# Planning Draft: {topic}

## Status
Phase: Interview
Started: {timestamp}
Target: Ralph Plan Execution

## Requirements
- [to be captured from interview]

## Decisions
- [choices made during interview]

## Research Findings
- [results from scout/librarian]

## Open Questions
- [unanswered items]
```

#### Step 2: Interview

Conduct focused interview (3-5 questions based on complexity):

**Core Questions:**
1. "What problem does this solve?" (understand context)
2. "What's the scope - minimal viable vs complete?" (set boundaries)
3. "Any constraints, non-goals, or things to avoid?" (define exclusions)

**Follow-up Questions (as needed):**
- Technical approach preferences
- Dependencies on other work
- Success criteria

Update draft after each answer.

#### Step 3: Research

Research the codebase before finalizing:

```
Agent: oh-my-claude:scout
Task: Find relevant files for {topic}
Expected: List of files that will be affected
```

```
Agent: oh-my-claude:librarian
Task: Read and summarize key files
Expected: Summary of current implementation patterns
```

Add findings to draft under "## Research Findings".

#### Step 4: Generate Plan

Transform draft into structured plan with these sections:

```markdown
# Plan: {topic}

## Context
[Why this plan exists, what problem it solves]

## Objectives

### Must Have
- [required outcomes]

### Must NOT
- [explicit exclusions and constraints]

## Implementation Steps
1. [Step with specific file references]
2. [Step with specific file references]
3. ...

## Files to Modify
| File | Changes |
|------|---------|
| `path/to/file.ts` | [what changes] |

## Acceptance Criteria
- [ ] [Testable criterion]
- [ ] [Testable criterion]
- [ ] [Testable criterion]
```

---

### Phase 2: Approval Gate

**CRITICAL: Execution MUST NOT begin without explicit user approval.**

#### Present the Plan

Display the complete plan to the user with:

```
## Plan Ready for Review

[Full plan content]

---

**Ready to execute this plan?**

Reply with:
- "execute", "run it", "looks good", "approved" - to begin execution
- "change step N", "add criterion", etc. - to modify the plan
- "cancel", "stop" - to abort without executing
```

#### Handle User Response

| User Says | Action |
|-----------|--------|
| "execute", "run it", "looks good", "approved", "go", "do it" | Proceed to Phase 3 |
| "change step 3", "modify...", "add...", "remove..." | Update plan, re-present |
| "cancel", "stop", "abort", "nevermind" | Abort without executing, keep draft |
| Asks a question | Answer, then re-prompt for approval |

**Do NOT interpret ambiguous responses as approval.** If unclear, ask: "Should I execute this plan?"

---

### Phase 3: Execution

Once approved, transition to Ralph Loop execution.

#### Step 1: Finalize Plan

Move plan from draft to final location:

```
.claude/plans/drafts/{topic-slug}.md  -->  .claude/plans/{topic-slug}.md
```

#### Step 2: Create Ralph State

Create Ralph Loop state files in `.claude/ralph/`:

**`.claude/ralph/config.json`:**
```json
{
  "prompt": "Execute plan: {topic}",
  "planPath": ".claude/plans/{topic-slug}.md",
  "maxIterations": 20,
  "completionPromise": "DONE",
  "startedAt": "<ISO timestamp>",
  "ultraworkEnabled": true,
  "sessionId": "<session ID>",
  "mode": "ralph-plan"
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
  "blockers": [],
  "acceptanceCriteria": {
    "total": 0,
    "passed": 0,
    "items": []
  }
}
```

**`.claude/ralph/prompt.txt`:**
```markdown
## Ralph Loop: Executing Plan

**Plan File:** .claude/plans/{topic-slug}.md

Read the plan file and execute it step by step.

### Execution Protocol
1. Read `.claude/plans/{topic-slug}.md` for the full plan
2. Convert "Implementation Steps" to TodoWrite items
3. Execute each step in order
4. After each step, verify against "Acceptance Criteria"
5. Respect all "Must NOT" constraints
6. When ALL acceptance criteria pass, output <promise>DONE</promise>

### Recovery (if resuming)
- Check git log for completed work
- Check TodoWrite for remaining items
- Continue from where you left off

### Constraints from Plan
[Extract "Must NOT" section from plan and list here]

ultrawork
```

#### Step 3: Begin Execution

Ralph Loop hook takes over. Each iteration:

1. Read plan from `.claude/plans/{topic-slug}.md`
2. Check current TodoWrite status
3. Execute next incomplete step
4. Update state.json with progress
5. Check acceptance criteria
6. Continue until all criteria pass

---

## Status Checking

When user says `ralph-plan status`:

```
Ralph Plan Status
=================

**Plan:** {topic}
**Phase:** Planning | Awaiting Approval | Executing | Complete

--- Plan Status ---
Location: .claude/plans/{topic-slug}.md
Steps: {total} ({completed} complete)

--- Execution Status ---
Iteration: {n}/{max}
Status: {active|complete|blocked|paused}
Last Updated: {timestamp}

--- Acceptance Criteria ---
[ ] Criterion 1
[x] Criterion 2
[ ] Criterion 3

Progress: {passed}/{total} criteria met
```

---

## Examples

### Example 1: Feature Implementation

```
/ralph-plan implement user authentication with JWT
```

**Planning Phase:**
- Interview: scope, token expiration, refresh tokens needed?
- Research: find existing auth patterns, user model
- Plan: 6 implementation steps, 4 acceptance criteria

**Approval:**
```
Plan ready. Includes: JWT middleware, login/logout routes,
token refresh, password hashing. 6 steps, estimated 4 files.

Execute this plan? (execute/modify/cancel)
```

**Execution:**
- Ralph Loop creates all auth components
- Validates each criterion
- Outputs `<promise>DONE</promise>`

---

### Example 2: Refactoring

```
/ralph-plan refactor the API to use dependency injection
```

**Planning Phase:**
- Interview: which services? testing implications?
- Research: current service instantiation patterns
- Plan: 12 steps across core services

**Approval:** User says "change step 5 to use factory pattern"

**Updated Plan:** Step 5 modified, re-presented for approval

**Execution:** Proceeds with updated plan

---

### Example 3: Test Coverage

```
/ralph-plan add comprehensive test coverage to src/services/
```

**Planning Phase:**
- Interview: unit tests only? integration? coverage target?
- Research: existing test patterns, what's untested
- Plan: test file for each service, mocking strategy

**Approval:** User approves

**Execution:** Creates tests, runs them, verifies coverage

---

## Decision Matrices

### Complexity Detection

| Signal | Complexity | Interview Depth |
|--------|------------|-----------------|
| "just", "simple", "quick" | Simple | 2-3 questions |
| Specific file mentioned | Standard | 3-4 questions |
| "redesign", "overhaul" | Complex | 5-6 questions |
| Multiple systems involved | Complex | 6+ questions |

### When to Skip Research

| Scenario | Skip? |
|----------|-------|
| User provides full context and file paths | Yes |
| Simple config change | Yes |
| New feature in unfamiliar area | **No** |
| Refactoring existing code | **No** |

---

## Error Handling

### User Cancels During Planning

1. Confirm: "Cancel planning for '{topic}'?"
2. If confirmed: Keep draft at `.claude/plans/drafts/{topic-slug}.md`
3. Report: "Planning cancelled. Draft saved for later."

### User Cancels at Approval Gate

1. Do NOT create Ralph state files
2. Keep plan at draft location
3. Report: "Execution cancelled. Plan saved at `.claude/plans/drafts/{topic-slug}.md`"

### Execution Blocked

1. Update state: `status = "blocked"`
2. Document blocker in state.json
3. Report: "Execution blocked: {reason}. Plan preserved for retry."

### Max Iterations Without Completion

1. Report progress made
2. Show remaining acceptance criteria
3. Ask: "Continue with more iterations?"

---

## Behavior Rules

### MUST DO

- Complete full planning phase before approval gate
- Display complete plan to user before execution
- Wait for explicit approval ("execute", "approved", etc.)
- Move plan from drafts/ to final location on approval
- Create all Ralph state files before execution begins
- Track acceptance criteria during execution
- Output `<promise>DONE</promise>` only when ALL criteria pass

### MUST NOT

- Begin execution without explicit user approval
- Interpret silence or ambiguous responses as approval
- Skip the planning phase
- Execute with incomplete or vague plans
- Delete plan files without confirmation
- Violate "Must NOT" constraints from the plan

### SHOULD DO

- Keep interview concise (3-5 questions)
- Research codebase before finalizing plan
- Break complex plans into clear steps
- Include testable acceptance criteria
- Preserve state for resumability

---

## Integration Notes

### Relationship to /plan

Ralph Plan uses the same planning methodology as `/plan`:
- Same draft structure
- Same interview approach
- Same research phase
- Same final plan format

The difference: Ralph Plan continues to execution after approval.

### Relationship to /ralph-loop

Ralph Plan creates standard Ralph Loop state files with one addition:
- `config.json` includes `planPath` pointing to the plan
- `prompt.txt` contains plan-aware execution instructions

The Ralph Loop hook handles iteration as normal.

### State Files Location

```
.claude/
  plans/
    drafts/
      {topic-slug}.md      # During planning
    {topic-slug}.md        # After approval
  ralph/
    config.json            # Ralph config with planPath
    state.json             # Iteration state
    prompt.txt             # Plan-aware prompt
```
