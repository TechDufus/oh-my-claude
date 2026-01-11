---
name: plan
description: "Structured planning with draft management. Use this skill when the user wants to plan a feature, task, or project before implementation. Triggers on: '/plan <topic>', 'let's plan', 'plan for', 'help me plan'. Creates draft at .claude/plans/drafts/, conducts interview, generates final plan on confirmation."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Task
  - AskUserQuestion
---

# Plan Skill

Structured planning through interview and draft management.

## When This Skill Activates

| Category | Trigger Phrases |
|----------|-----------------|
| **Start planning** | `/plan <topic>`, `let's plan`, `plan for`, `help me plan` |
| **Continue draft** | `continue planning`, `back to plan`, `resume plan` |
| **Finalize** | `make it a plan`, `finalize plan`, `generate plan`, `create the plan` |
| **Abandon** | `cancel plan`, `abandon planning`, `forget the plan` |

## Planning Workflow

### Phase 1: Initiation

When triggered with a topic:

1. Create draft file at `.claude/plans/drafts/{topic-slug}.md`
2. Initialize with template structure
3. Begin interview

**Draft location:** `.claude/plans/drafts/{topic-slug}.md`
**Final plan location:** `.claude/plans/{topic-slug}.md`

### Phase 2: Interview

Ask focused questions to gather requirements. Keep it to 3-5 core questions:

**Core Questions:**
1. "What problem does this solve?" (understand context)
2. "What's the scope - minimal viable vs complete?" (set boundaries)
3. "Any constraints, non-goals, or things to avoid?" (define exclusions)

**Follow-up Questions (as needed):**
- Technical approach preferences
- Dependencies on other work
- Priority/timeline considerations

After each answer, update the draft file with new information.

Use `AskUserQuestion` tool for structured multi-choice questions when options are clear.

### Phase 3: Research

Before finalizing, research the codebase:

```
Agent: oh-my-claude:scout
Task: Find relevant files for {topic}
Why: Need to understand existing code before planning changes
Expected: List of files that will be affected
```

```
Agent: oh-my-claude:librarian
Task: Read and summarize key files
Why: Need context for implementation planning
Expected: Summary of current implementation patterns
```

Add findings to draft under "## Research Findings".

### Phase 4: Confirmation

When user says "make it a plan" or similar:
1. Review draft completeness
2. Transform draft into final plan
3. Write to `.claude/plans/{topic-slug}.md`
4. Delete draft file (optional - can keep for reference)

## Draft Structure

```markdown
# Planning Draft: {topic}

## Status
Phase: Interview | Research | Ready for Plan
Started: {timestamp}

## Requirements
- [captured from interview]

## Decisions
- [choices made during interview]

## Research Findings
- [results from scout/librarian]

## Open Questions
- [unanswered items]
```

## Final Plan Structure

```markdown
# Plan: {topic}

## Context
[Why this plan exists, what problem it solves]

## Objectives

### Must Have
- [required outcomes]

### Must NOT Have
- [explicit exclusions]

## Implementation Steps
1. [Step with file references and details]
2. [Step with file references and details]

## Files to Modify
| File | Changes |
|------|---------|
| `path/to/file.ts` | [what changes] |

## Acceptance Criteria
- [ ] [Testable criterion]
- [ ] [Testable criterion]
```

## Behavior Rules

### MUST DO
- Create draft file before starting interview
- Update draft after each user response
- Research codebase before finalizing plan
- Include file references in final plan
- Keep interview focused (3-5 questions max)

### MUST NOT
- Auto-generate plan without user confirmation
- Delete draft without user confirmation
- Skip the interview phase
- Generate vague plans without concrete steps

## Handling Existing Drafts

If `/plan <topic>` is called and a draft already exists:

1. Ask user: "Found existing draft for '{topic}'. Resume or start fresh?"
2. If resume: continue from current phase
3. If start fresh: backup old draft as `{topic}-{timestamp}.md.bak`, create new

## Abandoning Plans

When user says "cancel plan" or "abandon planning":
1. Confirm: "Abandon planning for '{topic}'? Draft will be deleted."
2. If confirmed: delete draft file
3. If declined: continue planning

---

**Note:** This skill handles PLANNING only. Implementation is separate - use ultrawork or direct work after plan is approved.
