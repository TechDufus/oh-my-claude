---
name: ralph-loop-init
description: "Transform approved plans into ralph loop infrastructure. Triggers on: '/ralph-loop-init', '/ralph-init', 'setup ralph loop', 'generate ralph loop'. Creates .ralph/ directory with prd.json, loop.sh, CLAUDE.md, and supporting files."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
---

# Ralph Loop Init Skill

Transform approved plans into executable ralph loop infrastructure.

## What is Ralph Loop?

Ralph Loop is an autonomous execution system that runs Claude (or compatible tools) in a loop to complete multi-step implementation work. It transforms a PRD into:

1. **prd.json** - Machine-readable stories with progress tracking
2. **loop.sh** - Shell script that orchestrates iterations
3. **CLAUDE.md** - Per-iteration instructions for the AI
4. **progress.txt** - Human-readable execution log
5. **guardrails.md** - Quality gates and constraints

Each iteration: read one story, implement it, run quality gates, commit, update progress, exit. The loop script handles the next iteration.

## When This Skill Activates

| Category | Trigger Phrases |
|----------|-----------------|
| **Initialize** | `/ralph-loop-init <plan-path>`, `/ralph-init <plan-path>` |
| **Setup** | `setup ralph loop`, `generate ralph loop` |
| **From plan** | `create ralph loop from .claude/plans/...` |

---

## Workflow

### Phase 1: Plan Selection

Identify the approved plan to transform.

**If path provided:**
```
/ralph-loop-init .claude/plans/user-authentication.md
```
Read the plan at the specified path.

**If no path provided:**
```
/ralph-loop-init
```
List available plans in `.claude/plans/` (excluding drafts/) and ask user to select one.

**Validation:**
- Plan file must exist
- Plan must have "## Implementation Steps" section
- Plan should be in `.claude/plans/` (not drafts/)

---

### Phase 2: Pre-flight Check

Before generating files, check for existing ralph loop infrastructure.

```bash
if [ -d ".ralph" ]; then
    # Existing ralph loop detected
fi
```

**If .ralph/ exists:**

Present options to user:
```
Existing ralph loop detected at .ralph/

Options:
1. "overwrite" - Delete existing .ralph/ and create fresh
2. "resume" - Keep existing, show current progress
3. "cancel" - Abort initialization

Which would you like?
```

**Handle response:**

| User Says | Action |
|-----------|--------|
| "overwrite", "fresh", "start over" | Delete .ralph/, proceed with generation |
| "resume", "continue", "keep" | Show progress from existing prd.json, do not regenerate |
| "cancel", "abort", "stop" | Exit skill |

---

### Phase 3: Story Extraction

Parse the plan's "## Implementation Steps" section into structured stories.

**Input format (from plan):**
```markdown
## Implementation Steps

1. Create the auth middleware in src/middleware/auth.ts with JWT validation logic
2. Add login endpoint to src/routes/auth.ts that validates credentials and returns tokens
3. Add logout endpoint that invalidates the current token
4. Create token refresh endpoint for extending sessions
5. Update User model with password hashing using bcrypt
```

**Extraction rules:**

1. Find the "## Implementation Steps" section
2. Parse numbered list items (1., 2., 3., etc.)
3. For each item:
   - **id**: `story-{N}` where N is the step number
   - **title**: First sentence or line of the step (truncated at 80 chars if needed)
   - **description**: Full step text
   - **priority**: Sequential (1, 2, 3...) based on order
   - **passes**: `false` (all stories start incomplete)

**Output structure:**
```json
{
  "stories": [
    {
      "id": "story-1",
      "title": "Create auth middleware with JWT validation",
      "description": "Create the auth middleware in src/middleware/auth.ts with JWT validation logic",
      "priority": 1,
      "passes": false
    }
  ]
}
```

---

### Phase 4: Quality Detection

Detect project quality gates by scanning for common configuration files.

**Detection Logic:**

| File/Pattern | Quality Gate Command |
|--------------|---------------------|
| `package.json` with `scripts.test` | `npm test` |
| `package.json` with `scripts.lint` | `npm run lint` |
| `tsconfig.json` | `npx tsc --noEmit` |
| `.eslintrc*` or `eslint.config.*` | `npx eslint .` |
| `pytest.ini` or `pyproject.toml` with pytest | `pytest` |
| `Makefile` with `test` target | `make test` |
| `Makefile` with `lint` target | `make lint` |
| `.github/workflows/*.yml` | Note: "CI will run on push" |

**Detection process:**

1. Check for `package.json`:
   ```bash
   if [ -f "package.json" ]; then
       # Check for test/lint scripts
   fi
   ```

2. Check for TypeScript:
   ```bash
   if [ -f "tsconfig.json" ]; then
       # Add tsc --noEmit
   fi
   ```

3. Check for ESLint:
   ```bash
   if ls .eslintrc* eslint.config.* 2>/dev/null; then
       # Add eslint
   fi
   ```

4. Check for Python testing:
   ```bash
   if [ -f "pytest.ini" ] || grep -q "pytest" pyproject.toml 2>/dev/null; then
       # Add pytest
   fi
   ```

5. Check for Makefile targets:
   ```bash
   if [ -f "Makefile" ]; then
       grep -q "^test:" Makefile && # Add make test
       grep -q "^lint:" Makefile && # Add make lint
   fi
   ```

**Output:** List of quality gate commands for CLAUDE.md template.

---

### Phase 5: File Generation

Generate all ralph loop files in `.ralph/` directory.

#### Create Directory Structure

```bash
mkdir -p .ralph
```

#### File 1: prd.json

```json
{
  "plan_source": ".claude/plans/{topic-slug}.md",
  "created_at": "{ISO-8601-timestamp}",
  "stories": [
    {
      "id": "story-1",
      "title": "{extracted title}",
      "description": "{full step description}",
      "priority": 1,
      "passes": false
    },
    {
      "id": "story-2",
      "title": "{extracted title}",
      "description": "{full step description}",
      "priority": 2,
      "passes": false
    }
  ]
}
```

#### File 2: progress.txt

```
Ralph Loop Progress
===================
Plan: {plan title}
Source: {plan path}
Started: {timestamp}

Stories: 0/{total} complete

---

[Execution log will appear below]
```

#### File 3: CLAUDE.md

```markdown
# Ralph Loop Task

You are executing ONE iteration of a ralph loop. Complete ONE story, then exit.

## Your Task

1. Read `.ralph/prd.json` to find the next incomplete story (passes: false, lowest priority)
2. Implement ONLY that story
3. Run quality gates
4. Commit your changes
5. Update progress
6. Exit

## Quality Gates

Run these commands before committing. ALL must pass:

{detected quality gate commands, one per line with backticks}

If any gate fails, fix the issue before committing.

## Story Completion Protocol

When you complete a story:

1. **Stage changes:**
   ```bash
   git add -A
   ```

2. **Commit with story reference:**
   ```bash
   git commit -m "feat(ralph): {story-title}

   Story-Id: {story-id}"
   ```

3. **Update prd.json:**
   - Set `passes: true` for the completed story

4. **Append to progress.txt:**
   ```
   [{timestamp}] Completed: {story-id} - {story-title}
   ```

5. **Exit immediately** - Do not start another story

## Guardrails

See `.ralph/guardrails.md` for constraints and boundaries.

## Important

- Complete exactly ONE story per iteration
- Do not skip quality gates
- Do not modify stories you are not implementing
- If blocked, document in progress.txt and exit
- Trust the loop script to handle the next iteration
```

#### File 4: loop.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

# Ralph Loop Runner
# Executes AI iterations until all stories complete

TOOL="${TOOL:-claude}"
MAX_ITERATIONS="${MAX_ITERATIONS:-10}"
RALPH_DIR=".ralph"
PRD_FILE="$RALPH_DIR/prd.json"
PROGRESS_FILE="$RALPH_DIR/progress.txt"

# Verify ralph directory exists
if [ ! -d "$RALPH_DIR" ]; then
    echo "Error: $RALPH_DIR directory not found"
    echo "Run ralph-loop-init first"
    exit 1
fi

# Verify prd.json exists
if [ ! -f "$PRD_FILE" ]; then
    echo "Error: $PRD_FILE not found"
    exit 1
fi

# Function to count incomplete stories
count_incomplete() {
    if command -v jq &> /dev/null; then
        jq '[.stories[] | select(.passes == false)] | length' "$PRD_FILE"
    else
        grep -c '"passes": false' "$PRD_FILE" || echo "0"
    fi
}

# Function to show progress
show_progress() {
    if command -v jq &> /dev/null; then
        local total=$(jq '.stories | length' "$PRD_FILE")
        local complete=$(jq '[.stories[] | select(.passes == true)] | length' "$PRD_FILE")
        echo "Progress: $complete/$total stories complete"
    else
        echo "Progress: check $PRD_FILE for details"
    fi
}

echo "==================================="
echo "Ralph Loop Runner"
echo "==================================="
echo "Tool: $TOOL"
echo "Max iterations: $MAX_ITERATIONS"
show_progress
echo "==================================="
echo ""

iteration=0
while [ $iteration -lt $MAX_ITERATIONS ]; do
    iteration=$((iteration + 1))

    # Check if all stories complete
    incomplete=$(count_incomplete)
    if [ "$incomplete" -eq 0 ]; then
        echo ""
        echo "==================================="
        echo "All stories complete!"
        echo "==================================="
        show_progress
        exit 0
    fi

    echo "--- Iteration $iteration/$MAX_ITERATIONS ---"
    echo "Remaining stories: $incomplete"
    echo ""

    # Run the AI tool
    case "$TOOL" in
        claude)
            claude --print "Execute ralph loop iteration per .ralph/CLAUDE.md"
            ;;
        amp)
            amp --print "Execute ralph loop iteration per .ralph/CLAUDE.md"
            ;;
        codex)
            codex "Execute ralph loop iteration per .ralph/CLAUDE.md"
            ;;
        *)
            echo "Unknown tool: $TOOL"
            echo "Supported: claude, amp, codex"
            exit 1
            ;;
    esac

    echo ""
    show_progress
    echo ""
done

echo ""
echo "==================================="
echo "Max iterations reached ($MAX_ITERATIONS)"
echo "==================================="
show_progress
incomplete=$(count_incomplete)
if [ "$incomplete" -gt 0 ]; then
    echo "Warning: $incomplete stories still incomplete"
    exit 1
fi
```

#### File 5: guardrails.md

```markdown
# Ralph Loop Guardrails

Constraints and boundaries for this ralph loop execution.

## Scope Boundaries

This loop implements the plan at: `{plan_source}`

### In Scope
- Stories defined in prd.json
- Files mentioned in the original plan
- Quality gates listed in CLAUDE.md

### Out of Scope
- Features not in the plan
- Refactoring unrelated code
- Dependency upgrades (unless specified)
- Documentation beyond code comments

## Quality Requirements

All changes must:
1. Pass defined quality gates
2. Include appropriate tests (if test infrastructure exists)
3. Follow existing code patterns
4. Not break existing functionality

## Commit Standards

- One commit per story
- Conventional commit format: `feat(ralph): {description}`
- Include `Story-Id: {story-id}` in commit body
- No unrelated changes in commits

## Blocking Conditions

Stop and document in progress.txt if:
- Quality gates fail after 3 attempts
- Story requires clarification not in plan
- External dependency is unavailable
- Circular dependency detected

## Recovery

If the loop fails:
1. Check progress.txt for last successful story
2. Check git log for committed work
3. Review prd.json for story states
4. Resume with: `./loop.sh`

## Manual Override

To skip a problematic story:
```bash
# Edit prd.json, set passes: true for the story
# Add note to progress.txt explaining skip
# Run loop.sh to continue
```
```

---

### Phase 6: Completion Report

After generating all files, report to user:

```
Ralph Loop Initialized
======================

Directory: .ralph/

Files created:
  - prd.json      ({N} stories extracted)
  - progress.txt  (execution log)
  - CLAUDE.md     (per-iteration instructions)
  - loop.sh       (loop runner script)
  - guardrails.md (constraints)

Quality gates detected:
  - {list of detected gates}

To start the loop:
  chmod +x .ralph/loop.sh
  .ralph/loop.sh

Or with a different tool:
  TOOL=amp .ralph/loop.sh

Plan source: {plan_path}
```

---

## Examples

### Example 1: Initialize with Plan Path

```
/ralph-loop-init .claude/plans/user-authentication.md
```

**Output:**
```
Ralph Loop Initialized
======================

Directory: .ralph/

Files created:
  - prd.json      (6 stories extracted)
  - progress.txt  (execution log)
  - CLAUDE.md     (per-iteration instructions)
  - loop.sh       (loop runner script)
  - guardrails.md (constraints)

Quality gates detected:
  - npm test
  - npm run lint
  - npx tsc --noEmit

To start the loop:
  chmod +x .ralph/loop.sh
  .ralph/loop.sh

Plan source: .claude/plans/user-authentication.md
```

### Example 2: Initialize Without Path

```
/ralph-init
```

**Output:**
```
Available plans:

1. .claude/plans/user-authentication.md
2. .claude/plans/api-refactor.md
3. .claude/plans/test-coverage.md

Which plan should I use for the ralph loop?
```

User: "2"

**Proceeds with:** `.claude/plans/api-refactor.md`

### Example 3: Existing .ralph/ Directory

```
setup ralph loop
```

**Output:**
```
Existing ralph loop detected at .ralph/

Current progress: 3/8 stories complete
Last activity: 2024-01-15 14:30

Options:
1. "overwrite" - Delete existing .ralph/ and create fresh
2. "resume" - Keep existing, show current progress
3. "cancel" - Abort initialization

Which would you like?
```

User: "overwrite"

**Proceeds with:** Fresh initialization, deleting old .ralph/

---

## Error Handling

### Plan Not Found

```
Error: Plan not found at {path}

Check that:
1. The file path is correct
2. The plan has been approved (not in drafts/)
3. The file has .md extension

Available plans:
{list .claude/plans/*.md}
```

### No Implementation Steps

```
Error: No implementation steps found in plan

The plan must have a "## Implementation Steps" section with numbered items:

## Implementation Steps

1. First step description
2. Second step description
...

Please update the plan and try again.
```

### Existing .ralph/ with Active Work

```
Warning: Existing ralph loop has uncommitted progress

Last completed: story-3 (2024-01-15 14:30)
Uncommitted changes detected in working directory

Options:
1. "commit-and-overwrite" - Commit current work, then reinitialize
2. "discard-and-overwrite" - Discard changes, reinitialize
3. "resume" - Continue existing loop
4. "cancel" - Abort

Which would you like?
```

### Quality Gate Detection Failed

```
Note: No quality gates detected

The loop will run without automated checks.
Consider adding:
- package.json with test/lint scripts
- Makefile with test/lint targets
- pytest configuration

Proceeding with generation...
```

---

## Behavior Rules

### MUST DO

- Read and validate the plan before generating files
- Extract ALL implementation steps as stories
- Detect quality gates from project configuration
- Generate ALL 5 files (prd.json, progress.txt, CLAUDE.md, loop.sh, guardrails.md)
- Make loop.sh executable
- Report completion with next steps
- Handle existing .ralph/ gracefully

### MUST NOT

- Generate partial file sets
- Skip story extraction validation
- Overwrite .ralph/ without user confirmation
- Modify the source plan file
- Start executing the loop (only initialize)
- Hardcode quality gates without detection
- Create .ralph/ outside project root

### SHOULD DO

- Preserve original plan reference in prd.json
- Include timestamps in generated files
- Provide clear error messages with recovery steps
- Detect as many quality gates as possible
- Format generated files for readability
- Include comments in loop.sh for clarity
