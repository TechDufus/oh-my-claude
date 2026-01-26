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
# Plan execution prompt detection
# =============================================================================
# Claude Code injects this exact prefix when user clicks "Accept and clear"
PLAN_EXECUTION_PREFIX = "Implement the following plan:"

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

# Trivial request patterns - simple questions that don't need heavy orchestration
# These still GET ultrawork, just with a note to act directly
TRIVIAL_PATTERNS = [
    r"^what (is|does|are|was|were)\b",
    r"^how do I\b",
    r"^explain\b",
    r"^show me\b",
    r"^where (is|are|do|does)\b",
]

# Action verbs that indicate real work (NOT trivial even if starts with question word)
ACTION_VERBS = [
    r"\b(fix|implement|refactor|update|change|modify|rewrite|create|add|build|write|develop|make|configure|integrate|migrate|set up)\b",
]

# =============================================================================
# ULTRAPLAN CONTEXT - Planning-focused guidance for plan mode
# =============================================================================
ULTRAPLAN_CONTEXT = """[ULTRAPLAN MODE ACTIVE]

Strategic planning mode. Research BEFORE designing.

## RESEARCH PROTOCOL (MANDATORY)

| Step | Agent | Action |
|------|-------|--------|
| 1 | scout | Find ALL relevant files, patterns, precedents |
| 2 | librarian | Read architecture, understand constraints |
| 3 | scout | Map dependencies, integration points |
| 4 | YOU | Synthesize into design options |

DO NOT write plan until research complete.

## MULTI-PERSPECTIVE ANALYSIS

Every significant decision: compare 2+ approaches.

| Lens | Ask |
|------|-----|
| Simplicity | Minimal change that works? |
| Performance | Scaling implications? |
| Maintainability | Future change impact? |
| Consistency | Matches existing patterns? |

Document tradeoffs. Explain WHY, not just WHAT.

## CRITIC REVIEW

**Required if plan touches 3+ files.** Skip for smaller changes.

```
Task(subagent_type="oh-my-claude:critic", prompt=\"\"\"
Review plan: {summary}
Check: edge cases, integration risks, scope creep, unclear reqs
Respond: APPROVED or NEEDS_REVISION with concerns
\"\"\")
```

If NEEDS_REVISION: address concerns, re-submit, repeat until APPROVED.

## PLAN REQUIREMENTS

Write to `.claude/plans/{name}.md`. Must include:

| Element | Detail |
|---------|--------|
| Files | Exact paths with line numbers |
| Decisions | Rationale (why this over alternatives) |
| Risks | Known issues + mitigations |
| Verification | How to test changes |
| Order | Execution dependencies |

## SWARM EXECUTION

For 3+ independent tasks, use native parallel execution:

```
ExitPlanMode:
  launchSwarm: true
  teammateCount: {independent task count}
```

| Use Swarm | Skip Swarm |
|-----------|------------|
| 3+ independent tasks | Sequential dependencies |
| Different file sets | Complex coordination |
| Clear boundaries | Shared state |

Structure for parallel: self-contained tasks, specify file boundaries, no overlapping edits.

## ANTI-PATTERNS

| Don't | Do |
|-------|-----|
| Plan without research | Scout + librarian first |
| Skip critic (3+ files) | Mandatory review |
| Vague paths | Exact file:line |
| Single approach | Compare 2+ |
| "Straightforward" | Investigate until certain |
"""

# =============================================================================
# PLAN EXECUTION CONTEXT - Injected when plan marker is found
# =============================================================================
PLAN_EXECUTION_CONTEXT = """[ULTRAWORK MODE ACTIVE - PLAN EXECUTION]

You have an APPROVED PLAN to execute. The plan content is already in your context.

## EXECUTION PROTOCOL

1. **Create tasks** - Convert plan checkboxes to TaskCreate calls with dependencies
2. **Execute in order** - Follow the plan's execution order exactly
3. **Verify each step** - Run validator after each significant change
4. **Do NOT deviate** - The plan was researched and approved. Follow it.

### Task Creation from Plan
```
TaskCreate(subject="Implement auth middleware", description="Full context from plan")
TaskCreate(subject="Add validation tests", description="Test coverage for new middleware")
TaskUpdate(taskId="2", addBlockedBy=["1"])  # Tests depend on middleware
```

### Task Sizing (CRITICAL)

Tasks should be **small and atomic**. If a task touches multiple concerns, split it.

| Good Task | Bad Task |
|-----------|----------|
| "Add email validation to signup form" | "Implement user registration" |
| "Create UserService.getById method" | "Build the user module" |
| "Write tests for auth middleware" | "Add tests" |
| "Fix null check in parseConfig" | "Fix bugs in config system" |

**Sizing heuristics:**
- Single file or tightly coupled pair
- One logical change (add, fix, refactor - not all three)
- Completable in one agent turn
- Clear done/not-done criteria

**When to split:**
- Task description uses "and" → two tasks
- Multiple files in different domains → split by domain
- Mix of implementation + testing → separate tasks
- Uncertainty about approach → research task first, then implement task

## PLAN COMPLIANCE

| Allowed | NOT Allowed |
|---------|-------------|
| Following plan steps exactly | Adding features not in plan |
| Minor implementation details | Changing architecture decisions |
| Bug fixes discovered during work | Scope expansion |
| Asking about ambiguous plan items | Ignoring plan requirements |

If you discover the plan has a flaw:
1. STOP implementation
2. Explain the issue to the user
3. Get approval before changing approach

## COMPLETION

When ALL plan items are done:
1. Run full validation (tests, lints, type checks)
2. Summarize what was implemented
3. Note any deviations from plan (with reasons)
"""


def check_plan_execution_prompt(prompt: str) -> bool:
    """Check if prompt indicates plan execution (from Accept and clear)."""
    if not prompt:
        return False
    # Claude Code injects this exact prefix when user clicks "Accept and clear"
    return prompt.strip().startswith(PLAN_EXECUTION_PREFIX)


def is_trivial_request(prompt: str) -> bool:
    """Check if prompt is a simple question without action verbs.

    Returns True ONLY if:
    - Matches a trivial pattern (question word at start)
    - AND has NO action verbs anywhere in the prompt

    This is very conservative - we'd rather overwork than underwork.
    """
    prompt_lower = prompt.lower().strip()
    # Strip the ultrawork/ulw prefix
    prompt_lower = re.sub(r"^(ultrawork|ulw)\s+", "", prompt_lower)

    # If ANY action verb exists, NOT trivial
    for pattern in ACTION_VERBS:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            return False

    # Check if it starts with a trivial pattern
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
    permission_mode = data.get("permission_mode", "")

    # ==========================================================================
    # PLAN EXECUTION - Check prompt content (handles Accept and clear)
    # This takes priority over all other modes
    # ==========================================================================
    if check_plan_execution_prompt(prompt):
        log_debug("Plan execution detected from prompt prefix")
        output_context("UserPromptSubmit", PLAN_EXECUTION_CONTEXT)
        output_empty()
        return  # Early return - don't also inject ultrawork

    # ==========================================================================
    # ULTRAPLAN MODE - Auto-inject when in native plan mode
    # No keyword needed - detected from permission_mode
    # ==========================================================================
    if permission_mode == "plan":
        log_debug("plan mode detected via permission_mode, injecting ultraplan")
        output_context("UserPromptSubmit", ULTRAPLAN_CONTEXT)
        output_empty()

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
        # Check if this is a trivial request (simple question without action verbs)
        # Still inject ultrawork, but add a note that direct action is fine
        trivial_note = ""
        if is_trivial_request(prompt):
            log_debug("trivial request detected, adding light-touch note")
            trivial_note = """## SIMPLE TASK DETECTED

This appears to be a simple question or command.
Ultrawork mode acknowledged, but full orchestration overhead is unnecessary.
**Direct action is fine** - answer directly without heavy delegation.

---

"""

        context = f"""[ULTRAWORK MODE ACTIVE]

{trivial_note}RELENTLESS MODE. Work until COMPLETE. Find problems first. No corners cut.

## CERTAINTY PROTOCOL (Before ANY Code)

| Step | Agent | Action |
|------|-------|--------|
| 1 | scout | Find ALL relevant files |
| 2 | librarian | Understand patterns, constraints |
| 3 | scout | Map dependencies, call sites, tests |
| 4 | YOU | Plan with file:line specifics |

**Plan MUST include:** files (exact paths), functions (line numbers), changes per location, tests to update, execution order.

**NOT READY if:** "probably", "maybe", "I think", no file:line refs, "straightforward".

## ORCHESTRATOR PROTOCOL

You PLAN and DELEGATE. You do NOT implement.

### Pre-Delegation Declaration (Required)
```
Agent: oh-my-claude:{{agent}}
Task: {{one-line summary}}
Why: {{justification}}
Expected: {{deliverable}}
```

**Examples:**
- `scout`: "Find all files implementing rate limiting"
- `librarian`: "Summarize the auth flow in src/auth/"
- `critic`: "Review this migration plan for edge cases"
- `looker`: "Analyze the ERD diagram in docs/schema.png"
- `worker`: "Implement the retry logic per spec above"
- `validator`: "Run tests and lint on changed files"
- `debugger`: "Investigate auth failure after 2 failed fix attempts"
- `architect`: "Decompose this feature into parallel work streams"
- `scribe`: "Document the API endpoints in src/api/"
- `orchestrator`: "Coordinate 3 workers for parallel implementation"

### Delegation Prompt Structure
1. TASK - atomic goal
2. CONTEXT - files, patterns, constraints
3. EXPECTED OUTPUT - specific deliverables
4. MUST DO / MUST NOT - requirements & constraints
5. ACCEPTANCE CRITERIA - verification checks
6. RELEVANT CODE - file:line references

| Task Type | Min Lines |
|-----------|-----------|
| Simple | 20 |
| Standard | 30-50 |
| Complex | 50+ |

**<20 lines = TOO SHORT. Verbose beats vague.**

## VERIFICATION (Trust Nothing)

After EVERY delegation:
- [ ] Run validator on changed files
- [ ] Read files directly (confirm changes exist)
- [ ] Match output to original request
- [ ] Run full test suite

| Claim | Evidence Required |
|-------|-------------------|
| File edit | Validator clean + Read confirms |
| Build | Exit code 0 in output |
| Tests | PASS with test names visible |
| Lint | Zero errors in output |

**No evidence = not done.**

## ZERO TOLERANCE

| Violation | Response |
|-----------|----------|
| Partial implementation | UNACCEPTABLE - finish or don't start |
| Simplified version | UNACCEPTABLE - build what was asked |
| Skipped tests | UNACCEPTABLE - untested = broken |
| Scope reduction | UNACCEPTABLE - deliver EXACTLY what was asked |
| "Good enough" | UNACCEPTABLE - only DONE is acceptable |

## AGENT SELECTION

NEVER downgrade models. Omit `model` param or use `model="inherit"`.

| Task | Agent |
|------|-------|
| Find files/definitions | scout |
| Read/summarize files | librarian |
| Analyze images/PDFs | looker |
| Git recon (tags, branches) | scout |
| Git analysis (diffs) | librarian |
| Plan complex work | architect |
| Review plans | critic |
| Implement changes | worker |
| Write docs | scribe |
| Run tests/lints | validator |
| Debug (2+ failures) | debugger |
| Coordinate agents | orchestrator |

**Parallel patterns:** scout+librarian (research) -> architect->critic->workers (impl) -> validator (verify)

## TASK TRACKING (3+ Tasks Required)

```
TaskCreate(subject="Action verb: description", description="Full context")
TaskUpdate(taskId="2", addBlockedBy=["1"])  # Dependencies
TaskUpdate(taskId="1", owner="scout-1")     # Agent assignment
TaskUpdate(taskId="1", status="completed")  # Status flow: pending->in_progress->completed
```

Launch assigned agents in ONE message for parallelism.

## TASK SIZING (CRITICAL)

Tasks should be **small and atomic**. If a task touches multiple concerns, split it.

| Good Task | Bad Task |
|-----------|----------|
| "Add email validation to signup form" | "Implement user registration" |
| "Create UserService.getById method" | "Build the user module" |
| "Write tests for auth middleware" | "Add tests" |
| "Fix null check in parseConfig" | "Fix bugs in config system" |

**Sizing heuristics:**
- Single file or tightly coupled pair
- One logical change (add, fix, refactor - not all three)
- Completable in one agent turn
- Clear done/not-done criteria

**When to split:**
- Task description uses "and" → two tasks
- Multiple files in different domains → split by domain
- Mix of implementation + testing → separate tasks
- Uncertainty about approach → research task first, then implement task

## EXECUTION RULES

1. PARALLELIZE - Multiple Task() calls in ONE message
2. TRACK - 3+ tasks minimum, update status real-time
3. NEVER STOP - Stopping requires passing checklist
4. NO QUESTIONS - Decide and document
5. DELEGATE - You plan, agents implement

## FAILURE RECOVERY (3-Strike Rule)

| Strike | Action |
|--------|--------|
| 1st | Adjust, retry |
| 2nd | Re-examine assumptions, retry |
| 3rd | STOP -> REVERT -> DOCUMENT -> ESCALATE to debugger |

After debugger guidance: reset counter, new approach.

## AUTONOMOUS EXECUTION

| Situation | Action |
|-----------|--------|
| Single valid interpretation | Proceed |
| Multiple approaches, similar effort | Proceed, note assumption |
| 2x+ effort difference | MUST ask |
| Missing critical info | MUST ask |

**NEVER ask:** "proceed?", "continue?", "fix this?", "anything else?"

## Validation: {validation}

## STOPPING CHECKLIST

CANNOT stop until ALL true:
- [ ] ALL tasks "completed" (verify via TaskList)
- [ ] Validation passed (lints, tests, types)
- [ ] No TODO/FIXME in changed code
- [ ] Changes verified with direct tools
- [ ] Original request FULLY addressed

Before concluding: re-read request, check every requirement, TaskList, validate again.

## COMPLETION

When TRULY done: `<promise>DONE</promise>`

## EXTERNAL MEMORY

| Notepad | Purpose |
|---------|---------|
| `.claude/notepads/learnings.md` | Patterns, gotchas |
| `.claude/notepads/decisions.md` | Design decisions |
| `.claude/notepads/issues.md` | Blockers |

Write BEFORE context fills. Read when resuming.

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

Forensic investigation, not trial-and-error. Evidence before fixes.

## 7-Step Protocol

| Step | Action |
|------|--------|
| 1. REPRODUCE | Exact failure: error, conditions, frequency |
| 2. ISOLATE | Narrow to smallest failing case |
| 3. TRACE | Follow execution via scout + librarian |
| 4. HYPOTHESIZE | Form 3+ theories ranked by likelihood |
| 5. VERIFY | Test EACH hypothesis with evidence |
| 6. FIX | MINIMAL change addressing ROOT CAUSE |
| 7. VALIDATE | Confirm fix + no regression |

## Evidence Requirements

| Action | Required |
|--------|----------|
| Claim root cause | file:line + explanation |
| Propose fix | Hypothesis verified by code reading |
| Apply fix | Understanding of WHY it works |
| Mark resolved | Tests pass + manual verification |

## Hypothesis Tracking

Track 3+ hypotheses. Do NOT fix on H1 alone.

```
H1: {cause} [HIGH] - Evidence: {for/against} - Test: {how} - Status: {Untested|Verified|Disproven}
H2: {cause} [MED]  - Evidence: {for/against} - Test: {how} - Status: {Untested|Verified|Disproven}
H3: {cause} [LOW]  - Evidence: {for/against} - Test: {how} - Status: {Untested|Verified|Disproven}
```

## Git Forensics

| Command | Purpose |
|---------|---------|
| `git log -10 --oneline {file}` | Recent commits |
| `git diff HEAD~5 {file}` | Recent changes |
| `git blame {file}` | Change attribution |

Recent changes statistically likely to contain bugs.

## Anti-Patterns

| Pattern | Problem |
|---------|---------|
| try/catch without understanding | Hiding, not fixing |
| Fix symptoms not cause | Will recur |
| Assume H1 correct | Confirmation bias |
| Skip reproduction | Cannot verify fix |
| Multiple changes at once | Cannot isolate cause |
| Give up after 2 attempts | Use debugger agent |

## Escalation (After 2+ Failed Attempts)

```
Task(subagent_type="oh-my-claude:debugger", prompt="
PROBLEM: {error + conditions}
ATTEMPTED: 1. {tried} - {failed why}  2. {tried} - {failed why}
HYPOTHESES: H1: {hyp} - {result}  H2: {hyp} - {result}
REQUEST: Deep root cause analysis
")
```

## Bug Report Format

```
## Symptoms
Error: {message} | Conditions: {when} | Frequency: {always/sometimes/rare}

## Reproduction
{minimal steps}

## Investigation
Hypotheses: {ranked with evidence}
Evidence: {file:line findings, git diffs}

## Resolution
Root Cause: {confirmed with evidence}
Fix: {minimal change + rationale}
Verified: [ ] Error gone [ ] Related works [ ] Tests pass [ ] No regression
```

## Done When
- Root cause proven (not guessed)
- Fix targets cause (not symptoms)
- Winning hypothesis documented
- Tests pass, no regressions"""

        output_context("UserPromptSubmit", context)
        output_empty()

    # No trigger - pass through (context-guardian already provided baseline rules at SessionStart)
    log_debug("no mode trigger detected")
    output_empty()


if __name__ == "__main__":
    main()
