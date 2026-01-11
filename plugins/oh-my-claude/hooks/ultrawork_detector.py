#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
ultrawork_detector.py
Detects mode keywords and injects EXECUTION INTENSITY directives.
Context protection is handled by context-guardian.sh (always-on).
This hook adds MODE-SPECIFIC behaviors on top.
"""

import re
from pathlib import Path

from hook_utils import (
    RegexCache,
    hook_main,
    log_debug,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# =============================================================================
# Pre-compiled regex patterns (module-level cache)
# =============================================================================
# Patterns simplified to reduce ReDoS risk:
# - Replaced \s+ with single space where possible
# - Kept alternation groups bounded

PATTERNS = RegexCache()

# Ultrawork mode triggers - simplified to just ultrawork/ulw for clarity
PATTERNS.add(
    "ultrawork",
    r"\b(ultrawork|ulw)\b",
    re.IGNORECASE,
)

# Search mode triggers
PATTERNS.add(
    "search",
    r"(search for|find all|locate|where is|look for|grep for|hunt down|"
    r"track down|show me where|find me|get me all|list all)",
    re.IGNORECASE,
)

# Analyze mode triggers
PATTERNS.add(
    "analyze",
    r"(analyze|analyse|understand|explain how|how does|investigate|deep dive|"
    r"examine|inspect|audit|break down|walk through|tell me about|"
    r"help me understand|whats going on)",
    re.IGNORECASE,
)

# Ultrathink mode triggers
PATTERNS.add(
    "ultrathink",
    r"(ultrathink|think deeply|deep analysis|think hard|careful analysis|"
    r"thoroughly analyze)",
    re.IGNORECASE,
)

# Ultradebug mode triggers
PATTERNS.add(
    "ultradebug",
    r"(ultradebug|debug this|fix this bug|troubleshoot|diagnose|"
    r"why is this failing|root cause|whats wrong|whats broken|"
    r"figure out why|fix the issue|whats causing)",
    re.IGNORECASE,
)


def detect_validation(cwd: str) -> str:
    """Detect project type for smart validation commands."""
    cwd_path = Path(cwd)

    if (cwd_path / "package.json").is_file():
        return "TypeScript/JS: npm run typecheck && npm run lint && npm test"
    elif (cwd_path / "pyproject.toml").is_file() or (cwd_path / "setup.py").is_file():
        return "Python: ruff check . && pytest"
    elif (cwd_path / "go.mod").is_file():
        return "Go: go vet ./... && go test ./..."
    elif (cwd_path / "Cargo.toml").is_file():
        return "Rust: cargo check && cargo test"
    elif (cwd_path / "Makefile").is_file():
        return "make test (or equivalent)"
    else:
        return "Run appropriate linters and tests for this project type."


@hook_main("UserPromptSubmit")
def main() -> None:
    # Read and parse input safely
    raw_input = read_stdin_safe()
    data = parse_hook_input(raw_input)

    if not data:
        log_debug("no valid input data, exiting")
        output_empty()

    prompt = data.get("prompt", "")
    cwd = data.get("cwd", ".")

    # Detect validation commands with graceful degradation
    try:
        validation = detect_validation(cwd)
    except Exception as e:
        log_debug(f"detect_validation failed: {e}")
        validation = "Run appropriate linters and tests for this project type."

    # ==========================================================================
    # ULTRAWORK MODE - Maximum execution intensity
    # Context protection is ALREADY ON (context-guardian.sh)
    # This adds: relentless execution, zero tolerance, mandatory parallelization
    # ==========================================================================
    if PATTERNS.match("ultrawork", prompt):
        context = f"""[ULTRAWORK MODE ACTIVE]

This is RELENTLESS MODE. You will work until COMPLETE, not until tired.
You will find problems before the user does. You will not cut corners.
Every task spawns consideration of the next task. Momentum is everything.

## ORCHESTRATOR PROTOCOL (MANDATORY)

You are an ORCHESTRATOR. You PLAN and DELEGATE. You do NOT implement.

### Pre-Delegation Declaration
Before EVERY Task() call, declare:
- Agent: [which agent]
- Task: [one-line summary]
- Why: [brief justification]
- Expected: [what you will get back]

### Delegation Prompt Structure
Every worker prompt MUST include:
1. TASK: Atomic goal
2. CONTEXT: Files, patterns, constraints
3. EXPECTED OUTPUT: Deliverables
4. MUST DO: Requirements
5. MUST NOT: Forbidden actions

### Verification
After agent returns, VERIFY claims with direct tools before proceeding.

## ZERO TOLERANCE POLICY
- NO partial implementations
- NO "simplified versions"
- NO "leaving as exercise"
- NO skipped tests
- NO scope reduction
- DELIVER EXACTLY what was asked. NOT A SUBSET.

## Agent Selection (Model Inheritance)

In ULTRAWORK mode, agents inherit your session model for maximum intelligence.
Pass `model="inherit"` or omit the model parameter entirely - both work.

| Task Type | Agent | Default | ULTRAWORK |
|-----------|-------|---------|-----------|
| Find files/definitions | scout | haiku | **inherits your model** |
| Read/summarize files | librarian | sonnet | **inherits your model** |
| Plan complex work | architect | opus | **inherits your model** |
| Implement code changes | worker | opus | **inherits your model** |
| Write documentation | scribe | opus | **inherits your model** |
| Run tests/linters | validator | haiku | **inherits your model** |

### CRITICAL: Model Inheritance
Agents inherit your session model automatically when you omit the model parameter,
or you can explicitly pass model="inherit":
```
Task(subagent_type="oh-my-claude:scout", prompt="...")  # inherits parent model
Task(subagent_type="oh-my-claude:validator", model="inherit", prompt="...")  # explicit inherit
```

If you are running opus, agents use opus. If running sonnet, agents use sonnet.
This maximizes intelligence relative to what the user is paying for.

### Parallel Patterns
- **Research:** scout + librarian (parallel) -> you synthesize
- **Multi-file impl:** architect plans -> multiple workers (parallel)
- **Single task:** worker alone (if well-defined)

## Execution Rules
1. PARALLELIZE EVERYTHING - Launch ALL independent Task subagents in ONE message. Sequential is failure.
2. TODOWRITE IMMEDIATELY - Minimum 3 todos for any non-trivial work. Update status in real-time.
3. NEVER STOP - Stopping requires passing the MANDATORY STOPPING CHECKLIST. Partial completion = failure. "Good enough" = failure. Only DONE is acceptable.
4. NO QUESTIONS - Make reasonable decisions. Document them. Keep moving.
5. DELEGATE EVERYTHING - You plan, agents implement. Direct implementation = failure.

## PROACTIVE CONTINUATION

After completing each task, ask yourself:
1. "What else could break?" -> Run more validation
2. "What did I miss?" -> Re-read the original request
3. "Are there edge cases?" -> Add handling
4. "Is the implementation complete or just working?" -> Complete it

DO NOT WAIT for the user to point out gaps. Find them yourself.

## Validation Required: {validation}

## CRITICAL
- Multiple Tasks in ONE message = parallelism
- Single Task per message = sequential failure
- Incomplete todos = CANNOT stop
- Failed validation = CANNOT stop

## MANDATORY STOPPING CHECKLIST

You CANNOT stop until ALL of these are TRUE:
- [ ] ALL todos marked "completed" (zero pending/in_progress)
- [ ] Validation has run AND passed (linters, tests, type checks)
- [ ] No TODO/FIXME comments left in changed code
- [ ] Changes have been verified with direct tool calls (not just agent claims)
- [ ] User's original request is FULLY addressed (not partially)

If ANY checkbox is FALSE, you MUST continue working. No exceptions.

## BEFORE CONCLUDING

When you think you're done, STOP and verify:
1. Re-read the user's ORIGINAL request word-by-word
2. Check EVERY requirement was addressed
3. Run `TodoWrite` to confirm zero incomplete items
4. Run validation ONE MORE TIME
5. Only then may you present results

If you skipped any of these steps, GO BACK and complete them.

## COMPLETION PROMISE (MANDATORY)

When you are TRULY DONE with ALL work, you MUST end your final message with:

<promise>DONE</promise>

This signals task completion. Without this tag, work is assumed to continue.
Do NOT output this tag until:
- ALL todos are marked completed
- ALL validation has passed
- You have verified your work

## EXTERNAL MEMORY (RECOMMENDED)

For complex tasks, persist learnings to avoid losing context:

| File | Purpose |
|------|---------|
| `.claude/notepads/learnings.md` | Patterns discovered, gotchas found |
| `.claude/notepads/decisions.md` | Design decisions with rationale |
| `.claude/notepads/issues.md` | Problems encountered, blockers |

**Protocol:**
- Write to notepads BEFORE context fills up
- Read notepads when resuming work
- Include notepad wisdom in agent delegations

Execute relentlessly until complete."""

        output_context("UserPromptSubmit", context)
        output_empty()

    # ==========================================================================
    # SEARCH MODE - Parallel search strategy
    # ==========================================================================
    if PATTERNS.match("search", prompt):
        context = """[SEARCH MODE ACTIVE]

MAXIMIZE SEARCH EFFORT. Launch multiple search agents IN PARALLEL.

## Search Strategy
- Launch 2-3 oh-my-claude:scout Tasks in ONE message with different strategies
- One for exact matches, one for fuzzy/related terms
- Use Grep for content, Glob for file patterns
- Combine results and deduplicate

## Report Format
- List all findings with file:line references
- Group by relevance or location
- Highlight most likely matches first"""

        output_context("UserPromptSubmit", context)
        output_empty()

    # ==========================================================================
    # ANALYZE MODE - Deep parallel analysis
    # ==========================================================================
    if PATTERNS.match("analyze", prompt):
        context = """[ANALYZE MODE ACTIVE]

Gather comprehensive context before providing analysis.

## Analysis Protocol
- Launch parallel agents: one for main component, one for dependencies, one for tests
- Trace data/control flow through the system
- Provide evidence for every claim (file:line references)

## Output Requirements
- No speculation without verification
- Explain the "why" not just the "what"
- Identify potential issues or edge cases"""

        output_context("UserPromptSubmit", context)
        output_empty()

    # ==========================================================================
    # ULTRATHINK MODE - Extended reasoning before action
    # ==========================================================================
    if PATTERNS.match("ultrathink", prompt):
        context = """[ULTRATHINK MODE ACTIVE]

Extended reasoning before any action.

## Thinking Protocol
1. Gather context via scout + librarian
2. Consider 3+ approaches before committing to one
3. List pros/cons of each approach
4. Identify edge cases and potential failure modes
5. Validate ALL assumptions by reading code

## Requirements
- No implementation until analysis is complete
- Document reasoning in detail
- Challenge your own assumptions
- Consider maintainability and future implications"""

        output_context("UserPromptSubmit", context)
        output_empty()

    # ==========================================================================
    # ULTRADEBUG MODE - Systematic debugging protocol
    # ==========================================================================
    if PATTERNS.match("ultradebug", prompt):
        context = """[ULTRADEBUG MODE ACTIVE]

Systematic debugging with evidence-based diagnosis.

## Debug Protocol
1. REPRODUCE - Understand the exact failure condition
2. ISOLATE - Narrow down to the smallest failing case
3. TRACE - Follow execution path via scout + librarian
4. HYPOTHESIZE - Form 2-3 theories about root cause
5. VERIFY - Test each hypothesis with evidence
6. FIX - Apply minimal fix to address root cause
7. VALIDATE - Confirm fix works and no regression

## Evidence Requirements
- Every hypothesis must have supporting evidence (file:line)
- Check recent changes (git log, git diff)
- Verify fix with tests

## Parallel Investigation
- Launch multiple agents: one for failing code path, one for similar code that works"""

        output_context("UserPromptSubmit", context)
        output_empty()

    # No trigger - pass through (context-guardian already provided baseline rules at SessionStart)
    log_debug("no mode trigger detected")
    output_empty()


if __name__ == "__main__":
    main()
