---
name: ralph-plan
description: "Structured PRD generation with interview, research, and approval workflow. Triggers on: '/ralph-plan <topic>', 'create prd', 'generate prd', 'plan this'. Creates comprehensive Product Requirements Document via interview and research."
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

Structured PRD generation. Interview, research, plan, approve.

## What is Ralph Plan?

Ralph Plan creates comprehensive Product Requirements Documents through a deliberate process:

1. **Interview Phase** - Understand requirements through focused questions
2. **Research Phase** - Analyze codebase via Explore/librarian
3. **Planning Phase** - Generate structured plan with clear steps
4. **Approval Gate** - User reviews, modifies, and approves the final PRD

The result is a battle-tested plan ready for implementation by any method the user chooses.

## When This Skill Activates

| Category | Trigger Phrases |
|----------|-----------------|
| **Start planning** | `/ralph-plan <topic>`, `create prd`, `generate prd`, `plan this` |
| **Check status** | `ralph-plan status` |
| **Resume** | `resume ralph-plan` |

---

## Workflow

### Phase 1: Planning

Create a structured plan through interview and research.

#### Step 1: Initialize Draft

Create draft at `.claude/plans/drafts/{topic-slug}.md` with template:

```markdown
# Planning Draft: {topic}

## Status
Phase: Interview
Started: {timestamp}

## Requirements
- [to be captured from interview]

## Decisions
- [choices made during interview]

## Research Findings
- [results from Explore/librarian]

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
Agent: Explore
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

**User must review and approve the plan before finalization.**

#### Present the Plan

1. Display the complete plan summary to the user
2. Use `AskUserQuestion` tool for approval:

```json
{
  "questions": [{
    "question": "How would you like to proceed with this PRD?",
    "header": "PRD Status",
    "options": [
      {"label": "Approve", "description": "Finalize and save the PRD"},
      {"label": "Request Changes", "description": "Modify specific sections"},
      {"label": "Cancel", "description": "Abort and keep draft"}
    ],
    "multiSelect": false
  }]
}
```

**CRITICAL**: You MUST use the `AskUserQuestion` tool for approval. Do NOT output text prompts asking the user to "reply with" something.

#### Handle User Response

| User Response | Action |
|---------------|--------|
| "Approve" | Finalize PRD (move to final location) |
| "Request Changes" | Ask what to change, update plan, re-present with `AskUserQuestion` |
| "Cancel" | Keep draft, do not finalize |
| "Other" (custom text) | Interpret and act accordingly, then re-prompt if needed |

**Do NOT interpret ambiguous responses as approval.** If unclear, re-prompt with `AskUserQuestion`.

#### On Approval

1. Move plan from draft to final location:
   ```
   .claude/plans/drafts/{topic-slug}.md  -->  .claude/plans/{topic-slug}.md
   ```

2. Delete the draft file

3. Report completion:
   ```
   PRD finalized at .claude/plans/{topic-slug}.md

   Next steps:
   - Review the plan at your convenience
   - Implement manually, or use your preferred automation
   - Reference the acceptance criteria to track progress
   ```

---

## Status Checking

When user says `ralph-plan status`:

```
Ralph Plan Status
=================

**Plan:** {topic}
**Phase:** Interview | Research | Draft Complete | Awaiting Approval | Finalized

--- Plan Location ---
Draft: .claude/plans/drafts/{topic-slug}.md
Final: .claude/plans/{topic-slug}.md (if finalized)

--- Plan Contents ---
Steps: {total}
Acceptance Criteria: {total}
Files Affected: {count}
```

---

## Examples

### Example 1: Feature Implementation PRD

```
/ralph-plan implement user authentication with JWT
```

**Interview Phase:**
- Q: "What problem does this solve?"
- A: "Users need to log in securely"
- Q: "What's the scope?"
- A: "Basic login/logout with token refresh"
- Q: "Any constraints?"
- A: "Must use existing user model, no OAuth"

**Research Phase:**
- Explore finds: `src/models/User.ts`, `src/routes/index.ts`
- Librarian summarizes: Uses Express, no existing auth middleware

**Plan Generated:**
- 6 implementation steps
- 4 files to modify
- 4 acceptance criteria

**Approval:**

Plan presented to user with `AskUserQuestion` tool.
User selects: "Approve"

**Output:**
```
PRD finalized at .claude/plans/user-authentication-jwt.md
```

---

### Example 2: Refactoring PRD with Modifications

```
/ralph-plan refactor the API to use dependency injection
```

**Interview Phase:**
- Q: "Which services should use DI?"
- A: "All services in src/services/"
- Q: "Testing implications?"
- A: "Should make mocking easier"

**Research Phase:**
- Explore finds: 8 service files, current instantiation patterns
- Librarian summarizes: Direct instantiation, no DI container

**Plan Generated:**
- 12 implementation steps
- Container setup, service refactoring

**Approval:** User selects "Request Changes" via `AskUserQuestion`, specifies "change step 5 to use factory pattern"

**Updated Plan:** Step 5 modified, re-presented with `AskUserQuestion`

**Second Approval:** User selects "Approve"

**Output:**
```
PRD finalized at .claude/plans/api-dependency-injection.md
```

---

### Example 3: Test Coverage PRD

```
create prd for adding test coverage to src/services/
```

**Interview Phase:**
- Q: "Unit tests only, or integration too?"
- A: "Both"
- Q: "Coverage target?"
- A: "80% minimum"

**Research Phase:**
- Explore finds: 6 service files, existing test patterns
- Librarian summarizes: Jest setup exists, 2 services have tests

**Plan Generated:**
- Test file for each untested service
- Integration test suite
- Coverage configuration

**Approval:** User approves

**Output:**
```
PRD finalized at .claude/plans/service-test-coverage.md
```

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

1. Keep plan at draft location
2. Report: "PRD not finalized. Draft preserved at `.claude/plans/drafts/{topic-slug}.md`"

---

## Behavior Rules

### MUST DO

- Complete full planning phase before approval gate
- Display complete plan to user before finalization
- Use `AskUserQuestion` tool for approval (NEVER use text prompts)
- Wait for explicit approval via tool response
- Move plan from drafts/ to final location on approval
- Delete draft after successful finalization

### MUST NOT

- Finalize PRD without explicit user approval
- Use text prompts for approval (ALWAYS use `AskUserQuestion` tool)
- Interpret silence or ambiguous responses as approval
- Skip the interview or research phases
- Finalize with incomplete or vague plans
- Delete draft files without confirmation
- Proceed to any implementation/execution

### SHOULD DO

- Keep interview concise (3-5 questions)
- Research codebase before finalizing plan
- Break complex plans into clear steps
- Include testable acceptance criteria
- Preserve drafts for resumability

---

## Integration Notes

### Relationship to /plan

Ralph Plan uses an enhanced version of the `/plan` methodology:
- Same draft structure
- Same interview approach
- Same research phase
- Same final plan format

The difference: Ralph Plan has a formal approval gate and structured workflow.

### State Files Location

```
.claude/
  plans/
    drafts/
      {topic-slug}.md      # During planning (before approval)
    {topic-slug}.md        # After approval (final PRD)
```
