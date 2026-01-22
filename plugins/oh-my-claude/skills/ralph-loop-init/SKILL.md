---
name: ralph-loop-init
description: "Transform approved plans into ralph loop infrastructure. Triggers on: '/ralph-loop-init', '/ralph-init', 'setup ralph loop', 'generate ralph loop'. Creates .ralph/ directory with prd.json, loop.py, CLAUDE.md, and supporting files."
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
2. **loop.py** - Python UV script that orchestrates iterations with rich output
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

1. **Check for changes and commit if needed:**
   ```bash
   git status --porcelain
   ```

   If there ARE changes:
   - Stage changes: `git add -A`
   - Commit with a conventional commit message describing your implementation
   - The `commit_quality_enforcer` hook validates format automatically
   - If commit is rejected, read the error, fix the message, retry (max 3 attempts)
   - After 3 failures, log the error to progress.txt and exit

   If there are NO changes, proceed directly to step 2.

2. **Update prd.json:**
   - Set `passes: true` for the completed story

3. **Append to progress.txt:**
   ```
   [{timestamp}] Completed: {story-id} - {story-title}
   ```

4. **Exit immediately** - Do not start another story

## Guardrails

See `.ralph/guardrails.md` for constraints and boundaries.

## Important

- Complete exactly ONE story per iteration
- Do not skip quality gates
- Do not modify stories you are not implementing
- If blocked, document in progress.txt and exit
- Trust the loop script to handle the next iteration
```

#### File 4: loop.py

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich"]
# ///
"""
Ralph Loop Runner

Executes AI iterations until all stories complete.
Uses rich for beautiful terminal output with progress tracking.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()

RALPH_DIR = Path(".ralph")
PRD_FILE = RALPH_DIR / "prd.json"
PROGRESS_FILE = RALPH_DIR / "progress.txt"


def load_prd() -> dict:
    """Load and return the PRD JSON."""
    with open(PRD_FILE) as f:
        return json.load(f)


def count_stories(prd: dict) -> tuple[int, int]:
    """Return (complete, total) story counts."""
    stories = prd["stories"]
    complete = sum(1 for s in stories if s["passes"])
    return complete, len(stories)


def get_next_story(prd: dict) -> dict | None:
    """Get the next incomplete story by priority."""
    incomplete = [s for s in prd["stories"] if not s["passes"]]
    return min(incomplete, key=lambda s: s["priority"]) if incomplete else None


def run_claude() -> int:
    """Run claude and return exit code."""
    result = subprocess.run([
        "claude",
        "--dangerously-skip-permissions",
        "--print",
        "Execute ralph loop iteration per .ralph/CLAUDE.md"
    ])
    return result.returncode


def show_header(max_iterations: int, complete: int, total: int):
    """Display the header panel with autonomous mode warning."""
    console.print(Panel.fit(
        f"[bold cyan]Ralph Loop Runner[/]\n\n"
        f"[bold yellow]⚠️  AUTONOMOUS MODE ENABLED[/]\n"
        f"[dim]Commands execute without approval[/]\n\n"
        f"[dim]Max:[/] [yellow]{max_iterations}[/]  "
        f"[dim]Progress:[/] [green]{complete}[/]/[cyan]{total}[/]",
        border_style="blue",
        title="🔄 ralph",
        title_align="left"
    ))


def show_iteration(iteration: int, max_iterations: int, story: dict, remaining: int):
    """Display iteration info."""
    console.print()
    console.rule(f"[bold]Iteration {iteration}/{max_iterations}[/]", style="dim")
    console.print(f"[cyan]Next:[/] {story['id']} - {story['title']}")
    console.print(f"[dim]Remaining:[/] {remaining} stories")
    console.print()


def show_progress_bar(complete: int, total: int):
    """Display a simple progress indicator."""
    pct = (complete / total * 100) if total > 0 else 0
    filled = int(pct / 5)
    bar = "█" * filled + "░" * (20 - filled)
    console.print(f"[cyan]Progress:[/] [{bar}] {complete}/{total} ({pct:.0f}%)")


def show_completion():
    """Display completion panel."""
    console.print()
    console.print(Panel.fit(
        "[bold green]✓ All stories complete![/]",
        border_style="green"
    ))


def show_max_reached(max_iterations: int, incomplete: int):
    """Display max iterations panel."""
    console.print()
    console.print(Panel.fit(
        f"[bold yellow]Max iterations reached ({max_iterations})[/]\n"
        f"[red]{incomplete} stories still incomplete[/]",
        border_style="yellow"
    ))


def main():
    max_iterations = int(os.environ.get("MAX_ITERATIONS", "10"))

    # Verify ralph directory
    if not RALPH_DIR.exists():
        console.print("[red]Error:[/] .ralph directory not found")
        console.print("[dim]Run /ralph-loop-init first[/]")
        sys.exit(1)

    if not PRD_FILE.exists():
        console.print(f"[red]Error:[/] {PRD_FILE} not found")
        sys.exit(1)

    # Load PRD and show header
    prd = load_prd()
    complete, total = count_stories(prd)
    show_header(max_iterations, complete, total)

    # Main loop
    for iteration in range(1, max_iterations + 1):
        prd = load_prd()  # Reload each iteration
        complete, total = count_stories(prd)
        incomplete = total - complete

        if incomplete == 0:
            show_completion()
            sys.exit(0)

        next_story = get_next_story(prd)
        show_iteration(iteration, max_iterations, next_story, incomplete)

        # Run claude with visible output
        with console.status("[bold green]Starting claude...[/]", spinner="dots"):
            pass  # Brief status then let subprocess take over

        exit_code = run_claude()

        if exit_code != 0:
            console.print(f"[yellow]Warning:[/] claude exited with code {exit_code}")

        # Show updated progress
        prd = load_prd()
        complete, total = count_stories(prd)
        show_progress_bar(complete, total)

    # Max iterations reached
    prd = load_prd()
    complete, total = count_stories(prd)
    incomplete = total - complete
    show_max_reached(max_iterations, incomplete)
    sys.exit(1 if incomplete > 0 else 0)


if __name__ == "__main__":
    main()
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
4. Resume with: `uv run .ralph/loop.py`

## Manual Override

To skip a problematic story:
```bash
# Edit prd.json, set passes: true for the story
# Add note to progress.txt explaining skip
# Run: uv run .ralph/loop.py
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
  - loop.py       (Python UV script with rich output)
  - guardrails.md (constraints)

Quality gates detected:
  - {list of detected gates}

⚠️  AUTONOMOUS MODE
    This loop runs with --dangerously-skip-permissions
    Claude will execute commands without prompting for approval
    Review .ralph/guardrails.md before starting

To start the loop:
  uv run .ralph/loop.py

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
  - loop.py       (Python UV script with rich output)
  - guardrails.md (constraints)

Quality gates detected:
  - npm test
  - npm run lint
  - npx tsc --noEmit

⚠️  AUTONOMOUS MODE
    This loop runs with --dangerously-skip-permissions
    Claude will execute commands without prompting for approval
    Review .ralph/guardrails.md before starting

To start the loop:
  uv run .ralph/loop.py

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
- Generate ALL 5 files (prd.json, progress.txt, CLAUDE.md, loop.py, guardrails.md)
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
- Include docstrings in loop.py for clarity
