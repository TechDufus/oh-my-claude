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
# Known prefixes Claude Code uses when executing approved plans.
# Keep both old and new variants for cross-version compatibility.
PLAN_EXECUTION_PREFIXES = (
    "Implement the following plan:",  # Pre-v2.1.20
    "Plan to implement",              # v2.1.20+
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

STOP. Do NOT write a plan yet. Follow these steps IN ORDER.

## STEP 1: QUICK RECON

Understand the codebase context BEFORE asking questions. Launch Explore agents to gather
the lay of the land so you can ask INFORMED questions (not generic ones).

```
Task(subagent_type="Explore", prompt="Find files relevant to {request topic}", thoroughness="quick")
Task(subagent_type="oh-my-claude:librarian", prompt="Summarize architecture/patterns in {area}")
```

Goal: learn enough to ask smart questions. NOT enough to write a plan.

## STEP 2: INFORMED INTERVIEW

Now that you know the codebase, ask the user INFORMED questions using AskUserQuestion.
Reference specific files, patterns, or decisions you discovered in Step 1.

**Good questions** (informed by recon):
- "I found 3 patterns for X in your codebase — {A}, {B}, {C}. Which should this follow?"
- "This touches {file1} and {file2} which have different conventions. Align to which?"
- "There's an existing {thing} that does something similar. Extend it or build new?"
- "The test coverage in {area} is {sparse/good}. What test strategy for this?"

**Bad questions** (generic, uninformed):
- "What's your objective?" — you should already know from the request
- "What's out of scope?" — you should infer from recon and confirm
- "What patterns should I follow?" — you should have FOUND them already

**Intent types** (adapt depth):
- TRIVIAL → skip interview, go to Step 4
- REFACTORING → ask about safety: regression risk, rollback, breaking changes
- BUILD → ask about patterns found, integration points, deliverables
- MID-SIZED → ask about exact boundaries: "Does this include X? What about Y?"
- ARCHITECTURE → ask about scale, lifespan, constraints, trade-off preferences

**Clearance gate** — proceed to deep research only when you can answer:
1. What exactly are we building/changing?
2. What are we NOT changing?
3. Which existing patterns/conventions to follow?

Save interview outcomes to `.claude/plans/drafts/{name}.md`:
```
## Interview Notes - {name}
Intent: {classification}
Objective: {clear statement}
In Scope: {list}
Out of Scope: {list}
Constraints: {list}
Patterns to follow: {file:line references from recon}
Test Strategy: {TDD | tests-after | manual-only}
Effort Estimate: {Quick | Short | Medium | Large | XL}
```

## STEP 3: DEEP RESEARCH

Now do thorough research informed by both recon AND interview answers:

```
Task(subagent_type="Explore", prompt="Find ALL files, deps, call sites for {scope}", thoroughness="medium")
Task(subagent_type="oh-my-claude:librarian", prompt="Read {specific files} for {specific details}")
```

This round is targeted — you know what to look for from Steps 1-2.

## STEP 4: GAP ANALYSIS (MANDATORY before writing plan)

After deep research, MUST run the advisor before writing any plan:

```
Task(subagent_type="oh-my-claude:advisor", prompt=\"\"\"
Analyze for hidden requirements, scope risks, AI-slop patterns.
Interview notes: {summary from Step 2}
Research findings: {key discoveries from Step 3}
Flag: missing edge cases, unstated assumptions, over-engineering risk.
\"\"\")
```

If advisor finds CRITICAL gaps → ask user (back to Step 2).
If advisor finds MINOR gaps → note them and proceed.

## STEP 5: WRITE THE PLAN

Write to `.claude/plans/{name}.md`. Every plan MUST include:

```markdown
# Plan: {name}

## TL;DR
- **Summary:** {one sentence}
- **Deliverables:** {bullet list}
- **Effort:** {Quick | Short | Medium | Large | XL}
- **Critical Path:** {longest dependency chain}
- **Test Strategy:** {TDD | tests-after | manual-only}

## Big Picture Intent

> **When facing unexpected decisions during execution, align with this intent.**

- **Original Problem:** {summarize user's first message - what triggered this work}
- **Why This Matters:** {business/user impact if not done}
- **Key Constraints:** {non-negotiable requirements from interview}
- **Primary Driver:** {single most important factor guiding tradeoffs}

Populate the Big Picture Intent section by pulling from your interview notes (Original Problem from user's first message, Key Constraints from interview Constraints field).

## Must NOT (Guardrails)
- {thing explicitly excluded from scope}
- {constraint from interview}

## Task Tools (Quick Reference)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `Task()` | Spawn subagent | Research (Explore, librarian), implementation (general-purpose), validation (validator) |
| `TaskCreate()` | Create tracking item | Building the task list for multi-step work |
| `TaskUpdate()` | Update task state | Status changes, dependencies, ownership |
| `TaskList()` | View all tasks | Check progress, find unblocked work |
| `TaskGet()` | Get task details | Before starting work on a specific task |

**Key distinction:** `Task()` = spawn agent NOW. `TaskCreate()` = track work for later.

## Tasks

### Task {n}: {title}
- **Files:** {exact paths with line numbers}
- **Changes:** {what changes per location}
- **Validation:** {what to check} OR `N/A - research|docs`
- **Must NOT:** {per-task exclusions}
- **References:**
  - Pattern: {file:line of existing pattern to follow}
  - API: {file:line of relevant interfaces}
  - Tests: {file:line of related test files}
- **Commit:** {conventional commit message}
- **Acceptance:** runnable verification command:
  ```
  {e.g.: pytest tests/test_auth.py -v}
  ```

## Decisions
{rationale for each choice, why this over alternatives}

## Risks
{known issues + mitigations}

## Validation Protocol

Each implementation task SHOULD specify what to validate. The executor decides HOW (batch or per-task).

| Task Type | Validation Required? | Example |
|-----------|---------------------|---------|
| Implementation | YES | "Tests pass", "Lint clean", "Type check passes" |
| Refactoring | YES | "Existing tests still pass", "No behavior change" |
| Research (Explore/librarian) | NO - exempt | Mark as `N/A - research` |
| Documentation | NO - exempt | Mark as `N/A - docs` |

**If validation is unclear:** Split the task smaller until each piece has a clear validation criterion.

**Executor pattern (general-purpose + validator tasks with dependency):**

    TaskCreate(subject="Implement X", description="...")
    TaskCreate(subject="Validate X", description="...", addBlockedBy=["1"])

```

## STEP 6: CRITIC REVIEW (MANDATORY)

MUST submit plan to critic before ExitPlanMode:

```
Task(subagent_type="oh-my-claude:critic", prompt=\"\"\"
Review this plan for clarity, completeness, correctness, executability.
Interview decisions: {from Step 2}
Advisor findings: {from Step 4}
Plan: {plan content or path}
Respond: APPROVED or NEEDS_REVISION with specific items to fix.
\"\"\")
```

If NEEDS_REVISION: fix the items, resubmit. Loop until APPROVED.
Do NOT skip critic. Do NOT ExitPlanMode without critic approval.

## SWARM EXECUTION

For plans with independent parallel tasks, request a team:

```
ExitPlanMode:
  launchSwarm: true
  teammateCount: {number of parallel workers needed}
```

This triggers TeammateTool operations for team coordination.

### TeammateTool Operations (when available)

| Category | Operation | Purpose |
|----------|-----------|---------|
| **Lifecycle** | `spawnTeam` | Create team with name/description |
| | `discoverTeams` | List joinable teams |
| | `requestJoin` | Agent requests membership |
| | `approveJoin` | Leader accepts agent |
| | `cleanup` | Remove team resources |
| **Communication** | `write` | Message one teammate |
| | `broadcast` | Message all teammates |
| **Coordination** | `approvePlan` | Accept agent's proposed plan |
| | `rejectPlan` | Reject with feedback |
| | `requestShutdown` | Ask agent to exit when done |
| | `approveShutdown` | Confirm termination |

### Team Coordination

- **launchSwarm spawns the team** - ExitPlanMode handles team creation
- **Use write/broadcast for messaging** - Targeted vs all-teammates communication
- **Approve/reject teammate plans** - Review before they execute
- **Request shutdown when complete** - Clean team termination

## RULES

1. Recon FIRST (Step 1) — quick research to understand the landscape
2. Then INFORMED interview (Step 2) — ask smart questions referencing what you found
3. Then DEEP research (Step 3) — targeted by interview answers
4. Advisor is MANDATORY (Step 4) — run gap analysis before writing plan
5. Critic is MANDATORY (Step 6) — get approval before ExitPlanMode
6. Every task needs file:line refs and runnable acceptance commands
7. Compare 2+ approaches for significant decisions
"""

# =============================================================================
# PLAN EXECUTION CONTEXT - Injected when plan marker is found
# =============================================================================
PLAN_EXECUTION_CONTEXT = """[ULTRAWORK MODE ACTIVE - PLAN EXECUTION]

*** MANDATORY FIRST ACTION - CREATE TASKS ***

You have an approved plan. Before ANY implementation:

1. Use TaskCreate for EACH plan item
2. Use TaskUpdate to set blockedBy dependencies
3. Run TaskList to confirm tasks exist

**Key distinction:** `Task()` = spawn agent NOW. `TaskCreate()` = track work for later.

DO NOT spawn workers or start implementation until tasks are created.

Claude Code's task system handles execution order, dependencies, and progress tracking.
Your job is to CREATE the tasks - then execute them in order.

## EXECUTION PROTOCOL

1. **Create tasks** - Convert plan checkboxes to TaskCreate calls with dependencies
2. **Execute in order** - Follow the plan's execution order exactly
3. **Verify each step** - Run validator after each significant change
4. **Do NOT deviate** - The plan was researched and approved. Follow it.

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

## DECISION ALIGNMENT

When facing unexpected choices during execution, refer to the plan's "Big Picture Intent" section:
- Does this align with the original problem being solved?
- Does this respect the key constraints?
- Does this optimize for the stated primary driver?

## COMPLETION

When ALL tasks are done:
1. Run full validation (tests, lints, type checks)
2. Summarize what was implemented
3. Note any deviations from plan (with reasons)
"""


def check_plan_execution_prompt(prompt: str) -> bool:
    """Check if prompt indicates plan execution (from Accept and clear)."""
    if not prompt:
        return False
    stripped = prompt.strip()
    return any(stripped.startswith(prefix) for prefix in PLAN_EXECUTION_PREFIXES)


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

    log_debug(f"prompt starts with: {repr(prompt[:100])}")

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
| 1 | Explore (quick) | Find ALL relevant files |
| 2 | librarian | Understand patterns, constraints |
| 3 | Explore (medium) | Map dependencies, call sites, tests |
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
- `Explore (quick)`: "Find all files implementing rate limiting"
- `Explore (medium)`: "Map all call sites and dependencies for auth module"
- `librarian`: "Summarize the auth flow in src/auth/"
- `critic`: "Review this migration plan for edge cases"
- `general-purpose`: "Implement the retry logic per spec above"
- `validator`: "Run tests and lint on changed files"
- `advisor`: "Analyze for hidden requirements before planning"
- `Plan`: "Decompose this feature into parallel work streams"

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

| Task Type | Agent | Thoroughness |
|-----------|-------|--------------|
| Find files | Explore | quick |
| Code search | Explore | medium |
| Read/summarize files | librarian | N/A |
| Git analysis | librarian | N/A |
| Implementation | general-purpose | N/A |
| Planning | Plan | N/A |
| Gap analysis | advisor | N/A |
| Plan review | critic | N/A |
| Validation | validator | N/A |
| Large files (>100 lines) | librarian | N/A |

**Parallel patterns:** Explore+librarian (research) -> Plan->critic->general-purpose (impl) -> validator (verify)

## TASK TRACKING

**Key distinction:** `Task()` = spawn agent NOW. `TaskCreate()` = track work for later.

```
TaskCreate(subject="Action verb: description", description="Full context")
TaskUpdate(taskId="2", addBlockedBy=["1"])  # Dependencies
TaskUpdate(taskId="1", owner="explore-1")   # Agent assignment
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
2. TRACK - Use TaskCreate for multi-step work, update status real-time
3. NEVER STOP - Stopping requires passing checklist
4. NO QUESTIONS - Decide and document
5. DELEGATE - You plan, agents implement

## FAILURE RECOVERY (3-Strike Rule)

| Strike | Action |
|--------|--------|
| 1st | Adjust, retry |
| 2nd | Re-examine assumptions, retry |
| 3rd | STOP -> REVERT -> DOCUMENT -> ESCALATE to user |

After user guidance: reset counter, new approach.

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
| 3. TRACE | Follow execution via Explore + librarian |
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
| Give up after 2 attempts | Escalate to user |

## Escalation (After 2+ Failed Attempts)

```
Task(subagent_type="Explore", prompt="
PROBLEM: {error + conditions}
ATTEMPTED: 1. {tried} - {failed why}  2. {tried} - {failed why}
HYPOTHESES: H1: {hyp} - {result}  H2: {hyp} - {result}
REQUEST: Find additional evidence - related files, similar patterns, recent changes
", thoroughness="very thorough")
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
