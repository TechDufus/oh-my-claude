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

import json
import re
import sys
from pathlib import Path


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


def output_context(context: str) -> None:
    """Output JSON response with additional context."""
    response = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(response))


def main() -> None:
    # Read input from stdin
    input_data = sys.stdin.read()
    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        sys.exit(0)

    prompt = data.get("prompt", "")
    cwd = data.get("cwd", ".")
    prompt_lower = prompt.lower()

    # ==========================================================================
    # ULTRAWORK MODE - Maximum execution intensity
    # Context protection is ALREADY ON (context-guardian.sh)
    # This adds: relentless execution, zero tolerance, mandatory parallelization
    # ==========================================================================
    ultrawork_pattern = r"(ultrawork|ulw|just\s+work|dont\s+stop|until\s+done|keep\s+going|finish\s+everything|relentless|get\s+it\s+done|make\s+it\s+happen|no\s+excuses|full\s+send|go\s+all\s+in|complete\s+everything|finish\s+it|see\s+it\s+through|dont\s+give\s+up|ship\s+it|crush\s+it|nail\s+it|lets\s+go|do\s+it\s+all|handle\s+everything)"

    if re.search(ultrawork_pattern, prompt_lower):
        validation = detect_validation(cwd)
        context = f"""[ULTRAWORK MODE ENABLED!]

You MUST output "ULTRAWORK MODE ENABLED!" as your first line, then execute with maximum intensity.

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
3. NEVER STOP - You may ONLY stop when ALL todos are "completed" AND validation passes.
4. NO QUESTIONS - Make reasonable decisions. Document them. Keep moving.
5. DELEGATE EVERYTHING - You plan, agents implement. Direct implementation = failure.

## Validation Required: {validation}

## CRITICAL
- Multiple Tasks in ONE message = parallelism
- Single Task per message = sequential failure
- Incomplete todos = CANNOT stop
- Failed validation = CANNOT stop

Execute relentlessly until complete."""

        output_context(context)
        sys.exit(0)

    # ==========================================================================
    # SEARCH MODE - Parallel search strategy
    # ==========================================================================
    search_pattern = r"(search\s+for|find\s+all|locate|where\s+is|look\s+for|grep\s+for|hunt\s+down|track\s+down|show\s+me\s+where|find\s+me|get\s+me\s+all|list\s+all)"

    if re.search(search_pattern, prompt_lower):
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

        output_context(context)
        sys.exit(0)

    # ==========================================================================
    # ANALYZE MODE - Deep parallel analysis
    # ==========================================================================
    analyze_pattern = r"(analyze|analyse|understand|explain\s+how|how\s+does|investigate|deep\s+dive|examine|inspect|audit|break\s+down|walk\s+through|tell\s+me\s+about|help\s+me\s+understand|whats\s+going\s+on)"

    if re.search(analyze_pattern, prompt_lower):
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

        output_context(context)
        sys.exit(0)

    # ==========================================================================
    # ULTRATHINK MODE - Extended reasoning before action
    # ==========================================================================
    ultrathink_pattern = r"(ultrathink|think\s+deeply|deep\s+analysis|think\s+hard|careful\s+analysis|thoroughly\s+analyze)"

    if re.search(ultrathink_pattern, prompt_lower):
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

        output_context(context)
        sys.exit(0)

    # ==========================================================================
    # ULTRADEBUG MODE - Systematic debugging protocol
    # ==========================================================================
    ultradebug_pattern = r"(ultradebug|debug\s+this|fix\s+this\s+bug|troubleshoot|diagnose|why\s+is\s+this\s+failing|root\s+cause|whats\s+wrong|whats\s+broken|figure\s+out\s+why|fix\s+the\s+issue|whats\s+causing)"

    if re.search(ultradebug_pattern, prompt_lower):
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

        output_context(context)
        sys.exit(0)

    # No trigger - pass through (context-guardian already provided baseline rules at SessionStart)
    sys.exit(0)


if __name__ == "__main__":
    main()
