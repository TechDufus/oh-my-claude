---
name: git-commit-validator
description: "MUST be used for ANY git workflow that involves committing code. This includes explicit commit requests AND implicit ones like 'ship it', 'push this', 'let's merge', or finishing implementation work. Handles staging, message generation, validation, and commit execution with conventional commit format."
allowed-tools:
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Bash(git log:*)
  - Bash(git push:*)
  - Read
  - Grep
---

# Git Commit Validator

This skill MUST be invoked whenever you are about to create a git commit. It handles the complete workflow and enforces commit message standards.

## When This Skill Activates

**Auto-invoke this skill when the user implies code should be committed or pushed:**

| Category | Trigger Phrases |
|----------|-----------------|
| **Explicit commit** | "commit", "make a commit", "commit this" |
| **Ship/push intent** | "ship it", "push this", "let's push", "push it up", "send it" |
| **Finalization** | "wrap it up", "finalize this", "we're done", "that's it" |
| **Merge intent** | "get this merged", "ready for PR", "let's merge" |
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

**Message Format:**
```
<type>[optional scope]: <description>

[optional body - explain WHY, not WHAT]
```

### Step 4: Validate Message

**Inline validation (no external script needed):**

1. **Subject line <= 50 chars** - Count characters, reject if over
2. **Body lines <= 72 chars** - If body present
3. **Format check** - Must match: `^[a-z]+(\([a-z0-9\-]+\))?!?: .+$`
   - Starts with lowercase type (feat, fix, etc.)
   - Optional scope in parentheses
   - Colon and space
   - Description text
4. **No AI attribution** - Reject if contains: "generated with", "co-authored-by.*claude", "ai-generated"

If validation fails, fix and retry. Do NOT proceed with invalid messages.

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

### Body Lines (Optional)
- Max 72 characters per line
- Blank line between subject and body
- Explain "why" not "what"

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

**Simple feature:**
```
feat: add user authentication
```

**Bug fix with scope:**
```
fix(api): resolve timeout on large requests
```

**With body for complex changes:**
```
refactor(auth): simplify token validation

Previous implementation checked tokens in three places.
Consolidated to single middleware for consistency.
```

## Why No AI Attribution?

Commit messages reflect intent and ownership of the change. AI attribution:
- Clutters git history
- Dilutes accountability
- Adds no useful information

The human owns the commit. The tool is irrelevant.
