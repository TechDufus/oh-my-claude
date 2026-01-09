---
name: git-commit-validator
description: "MUST be used whenever creating git commits. Handles full commit workflow: staging, message generation, validation, and commit execution. Enforces conventional commit format."
allowed-tools:
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Bash(git log:*)
  - Bash(${CLAUDE_PLUGIN_ROOT}/skills/git-commit-validator/scripts/*:*)
  - Read
  - Grep
---

# Git Commit Validator

This skill MUST be invoked whenever you are about to create a git commit. It handles the complete workflow and enforces commit message standards.

## When This Skill Activates

**Auto-invoke this skill when:**
- User asks to "commit" changes
- User says "commit this", "make a commit", "create a commit"
- After completing implementation work when a commit is needed
- Any request involving `git commit`

**Do NOT commit without this skill.**

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

Run the validation script:
```bash
${CLAUDE_PLUGIN_ROOT}/skills/git-commit-validator/scripts/git-commit-helper.sh "<commit-message>"
```

- Exit 0 = valid, proceed
- Exit 1 = invalid, fix and retry

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
