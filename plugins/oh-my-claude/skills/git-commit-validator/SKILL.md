---
name: git-commit-validator
description: "MUST be used for ANY git workflow that involves committing code. This includes explicit commit requests AND implicit ones like 'ship it', 'wrap it up', or finishing implementation work. Handles staging, message generation, validation, and commit execution with conventional commit format."
allowed-tools:
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git add:*)
  - Bash(git log:*)
  - Read
  - Grep
---

# Git Commit Validator

This skill MUST be invoked whenever you are about to create a git commit. It handles the complete workflow and enforces commit message standards.

## When This Skill Activates

**Auto-invoke this skill when the user implies code should be committed:**

| Category | Trigger Phrases |
|----------|-----------------|
| **Explicit commit** | "commit", "make a commit", "commit this" |
| **Ship intent** | "ship it", "send it" |
| **Finalization** | "wrap it up", "finalize this", "we're done", "that's it" |
| **After implementation** | When you complete work and there are uncommitted changes |

**Key insight:** If the user's intent results in `git commit` being run, this skill MUST be used first.

**Do NOT run `git commit` without this skill.**

## Complete Commit Workflow

### Step 1: Gather Context

```bash
git status                    # See what's changed
git diff HEAD                 # See all changes (staged + unstaged)
git log --oneline -5          # Recent commit style reference
```

### Step 1.5: Handle No Changes

If `git status --porcelain` returns empty AND nothing is staged:
- **Do not attempt to commit** - there's nothing to commit
- Inform the user: "No changes to commit"
- Exit the workflow

This prevents errors from running `git commit` with nothing staged.

### Step 2: Stage Changes

**Default behavior** - stage all changes:
```bash
git add -A
```

**If user specifies `--staged`** - skip staging, use only what's already staged.

**If user gives instructions** - follow them:
- "ignore the docs" → don't stage doc files
- "only the src folder" → stage selectively

### Step 3: Analyze and Generate Message

Based on the diff, determine:
1. **Type**: feat, fix, docs, refactor, test, chore, perf, ci, build, style, revert
2. **Scope** (optional): module or area affected
3. **Description**: concise, imperative mood, lowercase
4. **Body**: see decision matrix below

**Message Format:**
```
<type>[optional scope]: <description>

[body - required for non-trivial changes]

[optional footer - breaking changes, issue refs]
```

## Commit Body Decision Matrix

**The body is NOT optional for most real work.** Use this matrix:

| Change Type | Body Required? | Body Content |
|-------------|---------------|--------------|
| Typo fix, single-line change | No | Subject is sufficient |
| Config tweak, version bump | No | Subject is sufficient |
| Bug fix | **YES** | What caused it, how you fixed it |
| New feature | **YES** | What it does, why it's needed, key design choices |
| Refactor | **YES** | What changed structurally, why this approach |
| Multiple files changed | **YES** | What each area of change accomplishes |
| Breaking change | **YES** | What breaks, migration path |
| Performance improvement | **YES** | What was slow, what's faster, by how much |

### Body Quality Standards

**Good body content includes:**
- **Context**: Why this change is needed (the problem)
- **Approach**: How you solved it (key decisions)
- **Impact**: What this enables or fixes
- **Caveats**: Limitations, follow-up work, edge cases

**Use bullet points** when listing multiple changes:
```
- Add validation for email format
- Refactor user service to async
- Update tests for new behavior
```

**Wrap at 72 characters** - hard requirement for git tooling compatibility.

### Sizing Your Commit Message

| Diff Size | Expected Message |
|-----------|-----------------|
| 1-10 lines | Subject only (if truly trivial) |
| 10-50 lines | Subject + 1-2 sentence body |
| 50-200 lines | Subject + paragraph or bullets |
| 200+ lines | Subject + detailed body with sections |

**When in doubt, write more.** A detailed commit message is a gift to future developers (including yourself).

### Step 4: Validation (Automatic)

**Validation runs automatically** when you execute `git commit`. The `commit_quality_enforcer` hook intercepts the command and validates:

1. **Subject line <= 50 chars**
2. **Body lines <= 72 chars** (if body present)
3. **Format check** - Must match conventional commit format: `<type>[scope]: <description>`
4. **No AI attribution** - Rejects "generated with", "co-authored-by.*claude", "ai-generated"
5. **Body quality** - Requires appropriate detail based on diff size

If validation fails, the commit is blocked with a clear error message. Fix the issues and retry.

### Step 5: Commit

Use HEREDOC for proper formatting:
```bash
git commit -m "$(cat <<'EOF'
type: description here
EOF
)"
```

## Validation Rules

### Subject Line (Required)
- **Max 50 characters**
- **Format**: `<type>[scope]: <description>`
- **Type**: lowercase (feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert)
- **Description**: lowercase start, no period at end, imperative mood

### Body Lines (Required for non-trivial changes)
- Max 72 characters per line
- Blank line between subject and body
- Explain "why" not just "what"
- See decision matrix above for when body is required

### Forbidden Content
- NO AI attribution ("Generated with Claude", "Created by AI")
- NO AI co-authors ("Co-authored-by: Claude")
- NO branding phrases

## Type Reference

| Type | Use For |
|------|---------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code restructuring (no behavior change) |
| `perf` | Performance improvement |
| `test` | Test additions/fixes |
| `chore` | Maintenance, deps |
| `ci` | CI/CD changes |
| `build` | Build system changes |
| `style` | Formatting (no logic change) |
| `revert` | Reverting previous commit |

## Examples

### Minimal (only for truly trivial changes)

```
docs: fix typo in readme
```

```
chore: bump lodash to 4.17.21
```

### Standard (most commits should look like this)

```
fix(api): resolve timeout on large file uploads

Requests over 10MB were hitting the default 30s timeout.
Increased timeout to 5 minutes for upload endpoints and added
progress tracking to prevent connection drops.
```

```
feat(auth): add password reset via email

Users can now request a password reset link sent to their
registered email. Link expires after 1 hour.

- Add /auth/forgot-password endpoint
- Add /auth/reset-password endpoint with token validation
- Integrate SendGrid for transactional emails
- Add rate limiting (3 requests per hour per email)
```

### Detailed (for large or complex changes)

```
refactor(database): migrate from callbacks to async/await

The callback-based database layer was causing pyramid-of-doom
issues and making error handling inconsistent across services.

Changes:
- Convert all db methods to return Promises
- Update 47 call sites across 12 service files
- Add connection pool management with proper cleanup
- Standardize error types (DbConnectionError, DbQueryError)

This unblocks the upcoming transaction support work.
```

```
feat(hooks): add pre-delegation context injection

Problem: Agents were receiving prompts without project context,
leading to inconsistent code style and missed conventions.

Solution: SessionStart hook now injects a delegation template
into Claude's context that gets included with every Task() call.

Template includes:
- 7 sections covering task, context, expected output
- MUST DO / MUST NOT constraints
- Verification checklist

This standardizes agent output quality across all delegations.
```

## Why No AI Attribution?

Commit messages reflect intent and ownership of the change. AI attribution:
- Clutters git history
- Dilutes accountability
- Adds no useful information

The human owns the commit. The tool is irrelevant.

---

**Note:** This skill handles COMMIT only. Push must be requested separately.
