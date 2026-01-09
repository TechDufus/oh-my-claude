---
name: git-commit-validator
description: Validates and generates git commit messages. Auto-invoked when creating commits. Enforces conventional commit format, character limits, and prohibits AI attribution.
---

# Git Commit Validator

## Overview

Validate and generate git commit messages that pass strict quality standards before committing. This skill enforces conventional commit format, character limits, and content policies to maintain clean git history.

## When to Use

This skill is auto-invoked for git commit operations:
- Before running `git commit` commands
- When drafting commit messages
- When regenerating rejected commit messages

## Commit Message Standards

### Format Requirements

**Conventional Commit Structure:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

**Examples:**
```
feat: add user authentication
fix(auth): resolve login timeout issue
docs: update API documentation
refactor(api): simplify error handling
```

### Validation Rules

1. **Subject line (first line):**
   - Max 50 characters
   - Format: `<type>[optional scope]: <description>`
   - Type: lowercase word (feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert)
   - Scope: optional, lowercase alphanumeric with hyphens in parentheses
   - Description: starts with lowercase, no period at end

2. **Body lines:**
   - Max 72 characters per line
   - Blank line between subject and body
   - Use body to explain "why" not "what"

3. **Forbidden content:**
   - No AI attribution (e.g., "Generated with Claude", "Created by AI")
   - No AI co-authors (e.g., "Co-authored-by: Claude")
   - No emojis or decorative symbols
   - No branding phrases

4. **Comment lines:**
   - Lines starting with `#` are ignored
   - Use for git commit template comments

## Workflow

### Before Committing

1. **Draft the commit message** based on the changes:
   - Analyze diff to understand the change type
   - Choose appropriate conventional type
   - Write concise description focused on "why"
   - Keep subject under 50 chars

2. **Validate using the script:**
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/git-commit-validator/scripts/git-commit-helper.sh "<commit-message>"
   ```

3. **Check validation output:**
   - Script exits 0 with "Commit message passes all checks" on success
   - Script exits 1 with specific ERROR messages on failure

4. **Fix any errors** before committing

### If Validation Fails

1. Read the specific error message
2. Adjust the commit message to fix the issue
3. Re-validate before committing

### Common Type Usage

| Type | When to Use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix or correction |
| `docs` | Documentation changes only |
| `refactor` | Code restructuring without behavior change |
| `perf` | Performance improvement |
| `test` | Test additions or corrections |
| `chore` | Maintenance tasks, dependency updates |
| `ci` | CI/CD configuration changes |
| `build` | Build system or dependency changes |
| `style` | Code formatting (no logic change) |
| `revert` | Reverting a previous commit |

## Best Practices

### Subject Line
- Use imperative mood ("add feature" not "added feature")
- No capitalization after type prefix
- Be specific but concise
- Omit obvious context

### Body (when needed)
- Explain motivation for change
- Describe behavior differences
- Reference issue numbers (e.g., "Closes #123")
- Skip body for trivial changes

### Scopes
- Use for large codebases with clear modules
- Keep scopes consistent across commits
- Skip for small projects or unclear boundaries

## Why No AI Attribution?

Commit messages should reflect the intent and ownership of the change, not the tool used to write them. AI attribution:
- Clutters git history
- Dilutes accountability
- Adds no useful information
- Makes logs harder to read

The human is responsible for the commit. The tool is irrelevant.
