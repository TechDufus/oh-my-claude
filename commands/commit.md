---
description: "Quick commit workflow: /commit [instructions] [--staged]"
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

# /commit - Streamlined Git Commit

## Usage

```
/commit                           # Stage all, generate message
/commit --staged                  # Commit only staged files
/commit ignore the docs file      # Stage all except docs, generate message
/commit --staged focus on auth    # Commit staged, message emphasizes auth changes
```

## Arguments: $ARGUMENTS

---

## Behavior

**Default (no --staged flag):**
- Stage all changes (`git add -A`)
- Generate commit message via git-commit-validator skill
- Commit

**With --staged flag:**
- Do NOT stage anything - commit only what's already staged
- Generate commit message from staged diff only
- Commit

**Instructions (optional):**
Pass any additional context from `$ARGUMENTS` to influence the commit message:
- "ignore the docs file" -> exclude from staging
- "this is a breaking change" -> factors into message
- "focus on the API changes" -> emphasizes in message

---

## Commit Message Standards

### Format Requirements

**Conventional Commit Structure:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

### Validation Rules

1. **Subject line (first line):**
   - Max 50 characters
   - Format: `<type>[optional scope]: <description>`
   - Type: lowercase (feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert)
   - Description: starts with lowercase, no period at end

2. **Body lines:**
   - Max 72 characters per line
   - Blank line between subject and body
   - Use body to explain "why" not "what"

3. **Forbidden content:**
   - No AI attribution (e.g., "Generated with Claude")
   - No AI co-authors
   - No emojis or decorative symbols

### Common Type Usage

- `feat`: New feature or capability
- `fix`: Bug fix or correction
- `docs`: Documentation changes only
- `refactor`: Code restructuring without behavior change
- `perf`: Performance improvement
- `test`: Test additions or corrections
- `chore`: Maintenance tasks, dependency updates
- `ci`: CI/CD configuration changes
- `build`: Build system or dependency changes
- `style`: Code formatting (no logic change)

---

## Execution

1. Gather context:
   - `git status` - see what's changed
   - `git diff HEAD` - see all changes
   - `git log --oneline -5` - recent commit style

2. If not `--staged`:
   - Stage appropriate files (`git add -A` or selective based on instructions)

3. Analyze changes:
   - Determine appropriate type (feat/fix/docs/etc.)
   - Identify scope if applicable
   - Draft concise description

4. Validate message:
   - Run `${CLAUDE_PLUGIN_ROOT}/skills/git-commit-validator/scripts/git-commit-helper.sh "<message>"`
   - Fix any validation errors

5. Commit:
   - Use HEREDOC for proper formatting:
   ```bash
   git commit -m "$(cat <<'EOF'
   type: description here
   EOF
   )"
   ```

---

## Best Practices

**Subject Line:**
- Use imperative mood ("add feature" not "added feature")
- No capitalization after type prefix
- Be specific but concise

**Body (when needed):**
- Explain motivation for change
- Describe behavior differences
- Reference issue numbers (e.g., "Closes #123")
- Skip body for trivial changes
