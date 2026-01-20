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

# Ultrawork mode triggers
PATTERNS.add(
    "ultrawork",
    r"\b(ultrawork|ulw)\b",
    re.IGNORECASE,
)

# Ultraresearch mode triggers - maximize online research
PATTERNS.add(
    "ultraresearch",
    r"\b(ultraresearch|ulr)\b",
    re.IGNORECASE,
)

# Ultradebug mode triggers
PATTERNS.add(
    "ultradebug",
    r"\b(ultradebug|uld)\b",
    re.IGNORECASE,
)

# Trivial request patterns - simple tasks that don't need full orchestration
TRIVIAL_PATTERNS = [
    r"^fix (the )?typo",
    r"^change .* to .*",
    r"^what (is|does|are)",
    r"^show me",
    r"^list\b",
    r"^how do I",
    r"^explain\b",
    r"^run (the )?(tests?|build|lint)",
]


def is_trivial_request(prompt: str) -> bool:
    """Check if prompt matches trivial patterns.

    Strips the ultrawork/ulw keyword prefix before matching.
    """
    prompt_lower = prompt.lower().strip()
    # Strip the ultrawork/ulw prefix to match the actual request
    prompt_lower = re.sub(r"^(ultrawork|ulw)\s+", "", prompt_lower)
    for pattern in TRIVIAL_PATTERNS:
        if re.match(pattern, prompt_lower, re.IGNORECASE):
            return True
    return False


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
        # Check if this is a trivial request
        trivial_note = ""
        if is_trivial_request(prompt):
            trivial_note = """## TRIVIAL TASK DETECTED

This appears to be a simple task (typo fix, quick question, simple command).
Ultrawork mode acknowledged, but full orchestration overhead is unnecessary.
**Direct action is fine** - skip heavy delegation for this one.

---

"""

        context = f"""{trivial_note}[ULTRAWORK MODE ACTIVE]

This is RELENTLESS MODE. You will work until COMPLETE, not until tired.
You will find problems before the user does. You will not cut corners.
Every task spawns consideration of the next task. Momentum is everything.

## ORCHESTRATOR PROTOCOL (MANDATORY)

You are an ORCHESTRATOR. You PLAN and DELEGATE. You do NOT implement.

### Pre-Delegation Declaration (MANDATORY)
Before EVERY Task() call, you MUST declare your intent:
- **Agent**: [which agent]
- **Task**: [one-line summary]
- **Why**: [brief justification]
- **Expected**: [what you will get back]

Example:
```
Agent: oh-my-claude:scout
Task: Find all authentication-related files
Why: Need to understand auth architecture before implementing changes
Expected: List of file paths with line references to auth logic
```

### Delegation Prompt Structure
Every worker prompt MUST include:
1. TASK: Atomic goal (one sentence)
2. CONTEXT: Files, patterns, constraints
3. EXPECTED OUTPUT: Specific deliverables
4. MUST DO: Non-negotiable requirements
5. MUST NOT: Forbidden actions
6. ACCEPTANCE CRITERIA: How to verify done
7. RELEVANT CODE: Key snippets or file references

Example worker delegation:
```
TASK: Add validation to the login form

CONTEXT:
- File: src/components/LoginForm.tsx
- Using zod for validation (see src/lib/validators.ts)
- Must match existing validation patterns

EXPECTED OUTPUT:
- Updated LoginForm.tsx with email/password validation
- Error messages displayed below fields

MUST DO:
- Use zod schema validation
- Show inline error messages
- Validate on blur and submit

MUST NOT:
- Change form layout
- Add new dependencies

ACCEPTANCE CRITERIA:
- Invalid email shows "Invalid email format"
- Empty password shows "Password required"
- Form doesn't submit until valid

RELEVANT CODE:
- src/lib/validators.ts:15-30 (existing patterns)
```

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
| Analyze PDFs/images/diagrams | looker | sonnet | **inherits your model** |
| Git recon (tags, commits, branches) | scout | haiku | **inherits your model** |
| Git analysis (diffs, changelogs) | librarian | sonnet | **inherits your model** |
| Plan complex work | architect | opus | **inherits your model** |
| Review plans critically | critic | opus | **inherits your model** |
| Implement code changes | worker | opus | **inherits your model** |
| Write documentation | scribe | opus | **inherits your model** |
| Run tests/linters | validator | haiku | **inherits your model** |
| Diagnose failures (2+ attempts) | debugger | opus | **inherits your model** |

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
- **Multi-file impl:** architect plans -> critic reviews -> multiple workers (parallel)
- **Single task:** worker alone (if well-defined)

### Escalation Patterns
- **Complex plans:** architect -> critic (review BEFORE execution)
- **Failed 2+ times:** debugger (diagnose root cause, then retry with guidance)
- **Visual content:** looker (PDFs, images, diagrams)

## Execution Rules
1. PARALLELIZE EVERYTHING - Launch ALL independent Task subagents in ONE message. Sequential is failure.
2. TODOWRITE IMMEDIATELY - Minimum 3 todos for any non-trivial work. Update status in real-time.
3. NEVER STOP - Stopping requires passing the MANDATORY STOPPING CHECKLIST. Partial completion = failure. "Good enough" = failure. Only DONE is acceptable.
4. NO QUESTIONS - Make reasonable decisions. Document them. Keep moving.
5. DELEGATE EVERYTHING - You plan, agents implement. Direct implementation = failure.

## AUTONOMOUS EXECUTION (NO UNNECESSARY QUESTIONS)

You have been given a task. Execute it.

### Permission Decision Matrix

| Situation | Action |
|-----------|--------|
| Single valid interpretation | **Proceed** - no questions |
| Multiple approaches, similar effort | **Proceed** with reasonable default, note assumption |
| Multiple approaches, 2x+ effort difference | **MUST ask** for clarification |
| Missing critical info (file path, error text) | **MUST ask** |
| User's approach seems flawed | **Raise concern**, then proceed if user confirms |

### NEVER Ask When:
- User said "do it", "fix it", "ship it", "yes" - JUST DO IT
- Task is clear but you want validation - JUST DO IT
- You finished and want to ask "anything else?" - STOP, you're done
- You want to summarize what you're about to do - JUST DO IT

### ALWAYS Ask When:
- Genuinely ambiguous with significant effort difference (2x+)
- Missing critical context you cannot infer
- About to do something destructive/irreversible user didn't request

### Anti-Patterns (NEVER DO THESE)
- "Would you like me to proceed?" - NO, just proceed
- "Should I continue?" - NO, just continue
- "Want me to fix this?" - NO, just fix it
- "Ready when you are" - NO, just start
- "Let me know if you want..." - NO, just do the reasonable thing

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
    # ULTRARESEARCH MODE - Maximum online research
    # ==========================================================================
    if PATTERNS.match("ultraresearch", prompt):
        context = """[ULTRARESEARCH MODE ACTIVE]

MAXIMIZE RESEARCH. Exhaust every available source before synthesizing.
This is not casual browsing. This is systematic intelligence gathering.

## Research Protocol
1. IDENTIFY ANGLES - Determine 3-5 distinct search perspectives
2. PARALLEL SEARCH - Launch ALL WebSearch queries in ONE message
3. DEEP FETCH - WebFetch promising results (minimum 3-5 sources)
4. CROSS-REFERENCE - Verify claims across multiple sources
5. SYNTHESIZE - Combine findings with citations

## CRITICAL: Parallelization

You MUST launch multiple WebSearch calls in a SINGLE message.

```
# CORRECT - All searches in one message
WebSearch("topic official documentation 2024")
WebSearch("topic github examples")
WebSearch("topic best practices blog")
WebSearch("topic common problems stackoverflow")

# WRONG - Sequential searches
WebSearch("topic") ... wait ... WebSearch("another angle")
```

Sequential searches = research failure. Parallel = thorough coverage.

## Search Strategy Matrix

| Angle | Query Pattern | Why |
|-------|--------------|-----|
| Official | "{topic} official documentation" | Authoritative source |
| Code | "{topic} github example implementation" | Working code |
| Community | "{topic} best practices blog 2024" | Real-world usage |
| Problems | "{topic} common issues stackoverflow" | Pitfalls to avoid |
| Recent | "{topic} latest updates news 2024" | Current state |

Always include current year for time-sensitive topics.

## Fetch Depth Requirements

After searching, WebFetch at minimum:
- 2+ official sources (docs, specs, RFCs)
- 2+ community sources (blogs, tutorials)
- 1+ code examples (GitHub, gists)
- 1+ problem discussions (issues, SO answers)

Do NOT stop at first result. Depth beats speed.

## Quality Standards
- Cite EVERY claim with `[source](url)`
- Prefer official docs over blog posts
- Note publication dates for time-sensitive info
- Flag conflicting information explicitly
- Distinguish facts vs opinions vs speculation

## Anti-Patterns (NEVER DO)
- Single search query then synthesize - TOO SHALLOW
- Trusting first result without verification - CONFIRMATION BIAS
- Ignoring contradictory information - CHERRY PICKING
- Presenting uncertain claims as facts - MISINFORMATION
- Skipping official docs for blogs - UNRELIABLE
- Omitting sources from output - UNVERIFIABLE

## Output Format

```markdown
## Summary
{3-5 bullet points of key findings}

## Detailed Findings

### {Topic 1}
{Content with inline citations [source](url)}

### {Topic 2}
{Content with inline citations}

## Conflicts/Uncertainties
{Any contradictions found across sources}

## Sources
- [Source Title](url) - {brief description}
- [Source Title](url) - {brief description}
```

## Completion Criteria
- [ ] Minimum 4 WebSearch queries launched in parallel
- [ ] Minimum 5 sources WebFetched and analyzed
- [ ] All claims have citations
- [ ] Conflicting information acknowledged
- [ ] Sources section with all URLs"""

        output_context("UserPromptSubmit", context)
        output_empty()

    # ==========================================================================
    # ULTRADEBUG MODE - Systematic debugging protocol
    # ==========================================================================
    if PATTERNS.match("ultradebug", prompt):
        context = """[ULTRADEBUG MODE ACTIVE]

Systematic debugging with evidence-based diagnosis.
This is forensic investigation, not trial-and-error guessing.

## Debug Protocol

1. **REPRODUCE** - Understand exact failure (error message, conditions, frequency)
2. **ISOLATE** - Narrow to smallest failing case
3. **TRACE** - Follow execution path via scout + librarian
4. **HYPOTHESIZE** - Form 3+ theories ranked by likelihood
5. **VERIFY** - Test EACH hypothesis with evidence before fixing
6. **FIX** - Apply MINIMAL fix addressing ROOT CAUSE
7. **VALIDATE** - Confirm fix works AND no regression

## CRITICAL: Evidence-Based Diagnosis

You MUST have evidence before attempting fixes.

| Action | Required Evidence |
|--------|-------------------|
| Claim root cause | File:line reference + explanation |
| Propose fix | Hypothesis verified by code reading |
| Apply fix | Understanding of WHY it works |
| Mark resolved | Tests passing + manual verification |

No guessing. No "try this and see." Evidence first.

## Hypothesis Tracking

Track ALL hypotheses with likelihood and evidence:

```markdown
## Hypotheses (Ranked)

### H1: {Most likely cause} [LIKELIHOOD: High]
- **Evidence for**: {What supports this}
- **Evidence against**: {What contradicts}
- **Test**: {How to verify}
- **Status**: {Untested/Verified/Disproven}

### H2: {Second theory} [LIKELIHOOD: Medium]
...

### H3: {Long shot} [LIKELIHOOD: Low]
...
```

Do NOT fix based on H1 until you've considered H2 and H3.

## Investigation Strategy

Launch parallel investigations:

```
# CORRECT - Parallel investigation
scout: "Find all usages of {failing function}"
librarian: "Read the error handling in {module}"
scout: "Check git log for recent changes to {file}"

# WRONG - Sequential guessing
"Let me try adding a null check..." → fails → "Maybe it's async..." → fails
```

## Git Forensics

Always check recent changes:
- `git log -10 --oneline {file}` - Recent commits
- `git diff HEAD~5 {file}` - Recent changes
- `git blame {file}` - Who changed what

Recent changes are statistically likely to contain bugs.

## Anti-Patterns (NEVER DO)
- Add try/catch without understanding cause - HIDING not fixing
- Fix symptoms instead of root cause - WILL RECUR
- Assume first hypothesis is correct - CONFIRMATION BIAS
- Skip reproduction step - CAN'T VERIFY FIX
- Make multiple changes at once - CAN'T ISOLATE
- Ignore "it works on my machine" - ENVIRONMENT MATTERS
- Give up after 2 attempts - USE DEBUGGER AGENT

## Escalation Path

If stuck after 2+ failed fix attempts, delegate to debugger agent:

```
Task(subagent_type="oh-my-claude:debugger", prompt="
PROBLEM: {exact error and conditions}

ATTEMPTED FIXES:
1. {What you tried} - {Why it failed}
2. {What you tried} - {Why it failed}

HYPOTHESES TESTED:
- H1: {hypothesis} - {result}
- H2: {hypothesis} - {result}

REQUEST: Deep analysis of root cause
")
```

Debugger agent provides strategic diagnosis, not more guessing.

## Output Format

```markdown
## Bug Report

### Symptoms
- Error: {exact error message}
- Conditions: {when it occurs}
- Frequency: {always/sometimes/rare}

### Reproduction
{Minimal steps to reproduce}

### Investigation

#### Hypotheses
{Ranked list with evidence}

#### Evidence Gathered
- {file:line}: {what you found}
- {git diff}: {relevant change}

### Root Cause
{Confirmed cause with evidence}

### Fix Applied
{Minimal change with rationale}

### Verification
- [ ] Error no longer occurs
- [ ] Related functionality works
- [ ] Tests pass
- [ ] No regression in related areas
```

## Completion Criteria
- [ ] Root cause identified with evidence (not guessed)
- [ ] Fix addresses root cause (not symptoms)
- [ ] Hypothesis that led to fix is documented
- [ ] Tests pass after fix
- [ ] No related regressions"""

        output_context("UserPromptSubmit", context)
        output_empty()

    # No trigger - pass through (context-guardian already provided baseline rules at SessionStart)
    log_debug("no mode trigger detected")
    output_empty()


if __name__ == "__main__":
    main()
