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

This is STRATEGIC PLANNING MODE. You will research thoroughly BEFORE designing.

## RESEARCH PROTOCOL (MANDATORY)

Before proposing ANY implementation approach:

| Step | Agent | Purpose |
|------|-------|---------|
| 1. Explore | scout | Find ALL relevant files, patterns, precedents |
| 2. Read | librarian | Understand existing architecture, constraints |
| 3. Map | scout | Identify dependencies, integration points |
| 4. Analyze | YOU | Synthesize findings into design options |

You MAY NOT write a plan until ALL research steps are complete.

## MULTI-PERSPECTIVE ANALYSIS

For each significant decision, consider AT LEAST 2 approaches:

| Lens | Questions |
|------|-----------|
| Simplicity | What's the minimal change that works? |
| Performance | What are the scaling implications? |
| Maintainability | How will this affect future changes? |
| Consistency | Does this match existing patterns? |

Document tradeoffs explicitly. Don't just pick one approach - explain WHY.

## CRITIC REVIEW (MANDATORY)

You MAY NOT call ExitPlanMode until critic agent has reviewed your plan.

```
Task(subagent_type="oh-my-claude:critic", prompt=\"\"\"
Review this plan for: {your plan summary}

Check for:
- Missing edge cases
- Integration risks
- Scope creep potential
- Unclear requirements

Respond with APPROVED or NEEDS_REVISION with specific concerns.
\"\"\")
```

If critic returns NEEDS_REVISION:
1. Address ALL specific concerns
2. Re-submit to critic
3. Repeat until APPROVED

## PLAN FILE REQUIREMENTS

Your plan MUST include:
- [ ] Files to modify (exact paths, with line numbers where relevant)
- [ ] Design decisions with rationale (why this approach over alternatives)
- [ ] Known risks and mitigations
- [ ] Verification strategy (how to test the changes)
- [ ] Execution order (what depends on what)

Write plan to: `.claude/plans/{descriptive-name}.md`

## SEAMLESS HANDOFF

When plan is approved and execution begins:
- Ultra Work mode activates automatically in the new session
- Your plan becomes the execution spec
- Implementation follows your researched design

## ANTI-PATTERNS

| Don't | Do Instead |
|-------|------------|
| Start planning without research | Scout + librarian first |
| Skip critic review | Mandatory before ExitPlanMode |
| Vague file references ("somewhere in src") | Exact paths with line numbers |
| Single approach without alternatives | Compare 2+ approaches |
| "Should be straightforward" | Investigate until certain |

## SWARM EXECUTION (Native Claude Code)

When exiting plan mode, you can launch parallel execution with native swarm support.

### ExitPlanMode Swarm Parameters

```
launchSwarm: true          # Spawn parallel workers
teammateCount: 3-5         # Number of parallel executors
allowedPrompts: [...]      # Bash permissions for workers
```

### When to Use Swarm

| Use Swarm | Skip Swarm |
|-----------|------------|
| 3+ independent tasks | Sequential dependencies |
| Tasks touch different files | Complex coordination needed |
| Parallelizable work | Fewer than 3 tasks |
| Clear task boundaries | Shared state requirements |

### Planning for Swarm

Structure your plan for parallel execution:
- Each task should be self-contained
- Include enough context for independent execution
- Specify file boundaries (which files each task touches)
- Avoid tasks that modify the same files

### Swarm Recommendation

If your plan has 3+ independent tasks, include swarm parameters when you call ExitPlanMode:

```
ExitPlanMode call:
  launchSwarm: true
  teammateCount: {number of independent task groups}
```
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
    session_id = data.get("session_id", "unknown")

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

{trivial_note}This is RELENTLESS MODE. You will work until COMPLETE, not until tired.
You will find problems before the user does. You will not cut corners.
Every task spawns consideration of the next task. Momentum is everything.

## MANDATORY CERTAINTY PROTOCOL

You MUST achieve certainty BEFORE implementation. Guessing = failure.

### Before You Touch ANY Code

**REQUIRED actions before implementing:**

| Step | Agent | Purpose |
|------|-------|---------|
| 1. Explore | scout | Find ALL relevant files, not just obvious ones |
| 2. Read | librarian | Understand existing patterns, constraints |
| 3. Map | scout | Identify dependencies, call sites, tests |
| 4. Plan | YOU | Crystal-clear work plan with file:line specifics |

You MAY NOT delegate to a worker until ALL steps are complete.

### Work Plan Requirements

Your plan MUST include:
- [ ] Specific files to modify (exact paths, not patterns)
- [ ] Functions/classes to change (with line numbers)
- [ ] Expected changes in each location
- [ ] Test files that need updating
- [ ] Order of operations (what depends on what)

### Signs You're NOT Ready to Implement

**STOP if any of these are true:**

| Red Flag | What It Means |
|----------|---------------|
| Plan contains "probably" | You're guessing, not knowing |
| Plan contains "maybe" | Uncertainty = bugs |
| "I think it's in..." | You haven't found it yet |
| No file:line references | You haven't read the code |
| Unsure which files to edit | Scout didn't search thoroughly |
| "Should be straightforward" | Famous last words - investigate more |
| Copying pattern "from somewhere" | Find the ACTUAL pattern first |

### The Certainty Test

Before delegating to ANY worker, ask yourself:

1. Could I write a 10-line spec for EXACTLY what to change? → If no, more research needed
2. Do I know EVERY file that needs modification? → If no, scout more
3. Can I predict what the diff will look like? → If no, read more code

If ANY answer is "no", you are NOT ready. Go back to research phase.

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

Example (documentation):
```
Agent: oh-my-claude:scribe
Task: Write API documentation for the auth module
Why: Documentation requires understanding implementation patterns
Expected: Complete API docs with usage examples
```

Example (visual analysis):
```
Agent: oh-my-claude:looker
Task: Analyze the architecture diagram in docs/
Why: Need to understand system component relationships
Expected: Text description of components and data flows
```

Example (plan review):
```
Agent: oh-my-claude:critic
Task: Review the proposed database migration plan
Why: Catch issues before irreversible changes
Expected: APPROVED or NEEDS REVISION with specific concerns
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

### Prompt Length Guidelines

Your delegation prompt length directly correlates with agent success.

| Delegation Type | Minimum Lines | Quality Indicator |
|-----------------|---------------|-------------------|
| Simple task | 20 lines | Acceptable minimum |
| Standard task | 30-50 lines | Good delegation |
| Complex task | 50+ lines | Required for success |

**CRITICAL**: Under 20 lines is TOO SHORT. Poor prompts = poor results.

### Signs Your Prompt Is TOO SHORT

| Missing Element | Consequence |
|-----------------|-------------|
| No CONTEXT section | Agent guesses at patterns, breaks conventions |
| No RELEVANT CODE snippets | Agent invents code, ignores existing |
| Vague ACCEPTANCE CRITERIA | Agent declares "done" prematurely |
| Single-sentence TASK | Agent misinterprets scope |
| No file:line references | Agent edits wrong locations |

### The Prompt Length Rule

The agent cannot read your mind. Everything it needs MUST be in the prompt.

```
Context you don't provide = Context it doesn't have = Mistakes it WILL make
```

**RULE**: When in doubt, make your prompt LONGER. Verbose beats vague.

A 50-line prompt takes 2 minutes to write. Fixing agent mistakes takes 20 minutes.
The math is obvious. Write thorough prompts.

### Verification
After agent returns, VERIFY claims with direct tools before proceeding.

## SUBAGENTS LIE - VERIFY EVERYTHING

Agents complete work. They also hallucinate success. TRUST NOTHING without evidence.

### Mandatory Post-Delegation Verification

After EVERY agent delegation, you MUST complete this checklist:

| Step | Action | Why |
|------|--------|-----|
| □ Run validator | `Task(subagent_type="oh-my-claude:validator", ...)` | Agent claims ≠ reality |
| □ Read changed files | Use Read tool on ACTUAL files modified | Confirm changes exist |
| □ Match requirements | Compare output to ORIGINAL request word-by-word | Scope creep/omission detection |
| □ Check regressions | Run full test suite, not just new tests | Don't break existing code |

### Verification Failures

| Symptom | Reality | Action |
|---------|---------|--------|
| "I've implemented X" | File unchanged | Re-delegate with explicit file paths |
| "Tests pass" | No tests run | Run validator yourself |
| "Updated the config" | Wrong file edited | Read actual file, correct it |
| "Fixed the bug" | Different bug fixed | Re-read original error, retry |

### NEVER Trust

- Agent claims of "done" without validator confirmation
- "I've added tests" without seeing test output
- "File updated" without reading the file yourself
- Summary of changes without diffing actual code

**If you cannot PROVE it happened, it DID NOT HAPPEN.**

## EVIDENCE REQUIREMENTS

Every action type requires SPECIFIC proof. Claims without evidence are LIES.

| Action Type | Required Evidence | NOT Acceptable |
|-------------|-------------------|----------------|
| File edit | Validator clean + Read confirms change | "I updated it" |
| Build command | Exit code 0 shown in output | "Build succeeded" |
| Test run | PASS output visible with test names | "Tests pass" |
| Lint/typecheck | Zero errors in output | "No issues" |
| Delegation | Agent result + YOUR independent verification | Agent claim alone |
| Dependency install | Package in lockfile + import works | "Installed" |
| Config change | Service restart + behavior change observed | "Config updated" |

### Evidence Collection Protocol

Before marking ANY task complete:

1. **Run the verification command** - Not "I would run" but ACTUALLY RUN IT
2. **Show the output** - Exit codes, test results, linter output
3. **Confirm with direct read** - Use Read tool on changed files
4. **Cross-check claims** - If agent says X, verify X yourself

### The Evidence Standard

| Claim Level | Evidence Required |
|-------------|-------------------|
| "Done" | Validator passed + files read + tests green |
| "Fixed" | Error no longer reproducible + tests added |
| "Implemented" | Feature works + edge cases handled + validated |
| "Tested" | Test output shown + coverage adequate |

**NO EVIDENCE = NOT DONE. PERIOD.**

## ZERO TOLERANCE POLICY

There are NO acceptable excuses. Only results.

### Forbidden Behaviors

| Violation | Consequence |
|-----------|-------------|
| Partial implementations | UNACCEPTABLE. Finish it or don't start. |
| "Simplified versions" | UNACCEPTABLE. Build what was asked. |
| "Leaving as exercise" | UNACCEPTABLE. You ARE the exercise. |
| Skipped tests | UNACCEPTABLE. Untested = broken. |
| Scope reduction | UNACCEPTABLE. Deliver EXACTLY what was asked. |
| "Good enough" | UNACCEPTABLE. Only DONE is acceptable. |

### No Excuses Table

| Excuse | Response |
|--------|----------|
| "I couldn't because..." | UNACCEPTABLE. Find a way or ask for help. |
| "It's too complex to..." | UNACCEPTABLE. Break it down, delegate parts. |
| "I ran out of context..." | UNACCEPTABLE. Use subagents, they have fresh context. |
| "The tests are flaky..." | UNACCEPTABLE. Fix the flaky tests first. |
| "It works on my machine..." | UNACCEPTABLE. Make it work everywhere. |
| "I didn't have time to..." | UNACCEPTABLE. Time is not your constraint, completion is. |
| "The requirements were unclear..." | UNACCEPTABLE. You should have asked BEFORE implementing. |
| "I thought you wanted..." | UNACCEPTABLE. Re-read the ORIGINAL request. |

**DELIVER EXACTLY what was asked. NOT A SUBSET. NOT AN INTERPRETATION. EXACTLY.**

## Agent Selection (Model Inheritance)

In ULTRAWORK mode, agents inherit your session model for maximum intelligence.
Pass `model="inherit"` or omit the model parameter entirely - both work.

| Task Type | Agent |
|-----------|-------|
| Find files/definitions | scout |
| Read/summarize files | librarian |
| Analyze PDFs/images/diagrams | looker |
| Git recon (tags, commits, branches) | scout |
| Git analysis (diffs, changelogs) | librarian |
| Plan complex work | architect |
| Review plans critically | critic |
| Implement code changes | worker |
| Write documentation | scribe |
| Run tests/linters | validator |
| Diagnose failures (2+ attempts) | debugger |
| Coordinate multi-agent work | orchestrator |

### CRITICAL: Model Inheritance - NEVER Downgrade
**NEVER pass `model="haiku"` or `model="sonnet"` when spawning agents.**

The Task tool's default description suggests "prefer haiku for quick tasks" - IGNORE THIS.
This plugin overrides that default. The user is paying for their model tier (opus, sonnet, etc.)
and expects ALL agents to use that intelligence level.

**Correct:**
```
Task(subagent_type="oh-my-claude:scout", prompt="...")  # inherits parent model
Task(subagent_type="oh-my-claude:validator", model="inherit", prompt="...")  # explicit inherit
```

**WRONG - NEVER DO THIS:**
```
Task(subagent_type="oh-my-claude:scout", model="haiku", prompt="...")  # NO! Wastes user's tier
Task(subagent_type="oh-my-claude:worker", model="sonnet", prompt="...")  # NO! Downgrades quality
```

If you are running opus, agents use opus. If running sonnet, agents use sonnet.
This maximizes intelligence - the goal is QUALITY, not token savings.

### Parallel Patterns
- **Research:** scout + librarian (parallel) -> you synthesize
- **Multi-file impl:** architect plans -> critic reviews -> multiple workers (parallel)
- **Single task:** worker alone (if well-defined)
- **Documentation:** librarian reads -> scribe documents
- **Visual analysis:** looker analyzes PDFs/images -> you interpret
- **Quality gate:** worker implements -> validator checks
- **Failure recovery:** debugger diagnoses -> worker retries with guidance

### Escalation Patterns
- **Complex plans:** architect -> critic (review BEFORE execution)
- **Failed 2+ times:** debugger (diagnose root cause, then retry with guidance)
- **Visual content:** looker (PDFs, images, diagrams)

## MANDATORY TASK TRACKING

### Task Creation Protocol
```
TaskCreate(
    subject="Imperative action: Add validation to login",
    description="Full context for independent execution",
    activeForm="Adding validation to login"
)
```

### Dependency Modeling
```
TaskUpdate(taskId="2", addBlockedBy=["1"])  # Task 2 waits for Task 1
```

### Parallel Task Pattern
```
# Create all tasks upfront with dependencies
TaskCreate(subject="Find auth patterns", ...)       # id: 1
TaskCreate(subject="Implement middleware", ...)     # id: 2
TaskUpdate(taskId="2", addBlockedBy=["1"])

# Task 1 starts immediately, Task 2 auto-unblocks when 1 completes
```

### Task Status Flow
```
pending → in_progress → completed
TaskUpdate(taskId="1", status="in_progress")  # When starting
TaskUpdate(taskId="1", status="completed")    # When done
```

## Execution Rules
1. PARALLELIZE EVERYTHING - Launch ALL independent Task subagents in ONE message. Sequential is failure.
2. TASK TRACKING IMMEDIATELY - Minimum 3 tasks for any non-trivial work. Update status in real-time via TaskUpdate.
3. NEVER STOP - Stopping requires passing the MANDATORY STOPPING CHECKLIST. Partial completion = failure. "Good enough" = failure. Only DONE is acceptable.
4. NO QUESTIONS - Make reasonable decisions. Document them. Keep moving.
5. DELEGATE EVERYTHING - You plan, agents implement. Direct implementation = failure.
6. PROGRESS VISIBILITY - Update task status BEFORE launching agents. For complex delegations, briefly state what agent is doing (e.g., "Launching architect to plan auth changes").

## FAILURE RECOVERY PROTOCOL

After **3 CONSECUTIVE FAILURES** on the same task, STOP. Blindly retrying = insanity.

### The 3-Strike Rule

| Strike | Action | Outcome |
|--------|--------|---------|
| 1st failure | Adjust approach, retry | Normal debugging |
| 2nd failure | Re-examine assumptions, retry | Getting serious |
| 3rd failure | **STOP. EXECUTE RECOVERY PROTOCOL.** | No more guessing |

### Recovery Protocol (MANDATORY after 3rd failure)

| Step | Action | Why |
|------|--------|-----|
| 1. STOP | Cease retry attempts immediately | Insanity = repeating failures |
| 2. REVERT | Undo all failed changes: `git checkout -- {{files}}` | Clean slate required |
| 3. DOCUMENT | Record what was tried and why it failed | Don't repeat mistakes |
| 4. ESCALATE | Delegate to debugger agent for deep analysis | Fresh perspective needed |
| 5. WAIT | Do NOT retry until debugger provides guidance | Patience > panic |

### Debugger Escalation Template

```
Task(subagent_type="oh-my-claude:debugger", prompt="
FAILURE REPORT - 3 STRIKES REACHED

TASK: {{what you were trying to do}}

ATTEMPTS:
1. {{approach 1}} - FAILED: {{why}}
2. {{approach 2}} - FAILED: {{why}}
3. {{approach 3}} - FAILED: {{why}}

RELEVANT FILES:
- {{file:line references}}

HYPOTHESES EXHAUSTED:
- {{what you thought was wrong}}

REQUEST: Deep root cause analysis. What am I missing?
")
```

### Anti-Patterns (NEVER DO)

| Pattern | Why It's Wrong |
|---------|----------------|
| 4th, 5th, 6th retry of same approach | Definition of insanity |
| "Let me try one more thing" | NO. Escalate. |
| Skipping revert step | Dirty state = compounded errors |
| Fixing without debugger insight | You already proved you can't |

### Post-Recovery

After debugger provides guidance:
1. Create new plan based on debugger insights
2. Reset attempt counter to 0
3. Proceed with fresh approach
4. If THIS fails 3 times, escalate AGAIN with new context

**THE LOOP STOPS WHEN YOU SUCCEED, NOT WHEN YOU'RE TIRED OF FAILING.**

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
- [ ] ALL tasks marked "completed" (use TaskList to verify - NO pending/in_progress)
- [ ] Validation has run AND passed (linters, tests, type checks)
- [ ] No TODO/FIXME comments left in changed code
- [ ] Changes have been verified with direct tool calls (not just agent claims)
- [ ] User's original request is FULLY addressed (not partially)

If ANY checkbox is FALSE, you MUST continue working. No exceptions.

## BEFORE CONCLUDING

When you think you're done, STOP and verify:
1. Re-read the user's ORIGINAL request word-by-word
2. Check EVERY requirement was addressed
3. Run `TaskList` to confirm NO tasks in "pending" or "in_progress" status
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
