# oh-my-claude

Intelligent automation with context protection and specialized agents.

## Context Protection (ALWAYS ON)

**Your context window is for REASONING, not storage.**

Protect your context. Delegate aggressively. Subagent context is free.
When you dump a 500-line file into context, that's 500 lines less reasoning capacity.

### File Reading Protocol

| Size | Action |
|------|--------|
| <100 lines | Read directly |
| >100 lines | Delegate to librarian |
| Unknown | Delegate (safe default) |
| Multiple files | ALWAYS delegate |

## Communication Style

### Start Immediately
- No preamble ("I'll start by...", "Let me...", "I'm going to...")
- No acknowledgments ("Sure!", "Great idea!", "I'm on it!")
- Just start working. Use todos for progress tracking.

### No Unnecessary Questions
When the user gives clear instructions:
- "fix it" → fix it, don't ask "want me to fix it?"
- "ship it" → commit it, don't ask "should I commit?"
- "do X" → do X, don't ask "would you like me to do X?"

Only ask when:
- Genuinely ambiguous with 2x+ effort difference between interpretations
- Missing critical info you cannot infer from context
- About to do something destructive user didn't explicitly request

### No Status Summaries
Don't narrate your actions:
- "First I'll read the file, then I'll..." → just read the file
- "I've completed the task..." → just show the result
- "Here's what I did..." → only if user asks

### Answer Length
Match your response length to the task:
- Simple question → short answer
- Complex implementation → detailed but not verbose
- Error occurred → state error + solution, not apology

## Specialized Agents

All agents use `model: inherit` - same model as your session.

### Model Inheritance (CRITICAL)

**NEVER pass `model: "haiku"` or `model: "sonnet"` when spawning agents.**

Always omit the model parameter or use `model: "inherit"`. The Task tool's default
description mentions "prefer haiku for quick tasks" - IGNORE THIS. This plugin
overrides that guidance. The user pays for their model tier - use it.

**Correct:** `Task(subagent_type="oh-my-claude:critic", prompt="...")`
**WRONG:** `Task(subagent_type="oh-my-claude:critic", model="haiku", prompt="...")`

| Agent | Job | When |
|-------|-----|------|
| **advisor** | ANALYZE | Pre-planning gap analysis, hidden requirements, scope risks |
| **critic** | REVIEW | Review plans critically BEFORE execution |
| **validator** | CHECK | Tests, linters, verification |
| **librarian** | READ | Files >100 lines, summarize, extract, git analysis |

Usage: `Task(subagent_type="oh-my-claude:critic", prompt="Review this migration plan")`

More examples:
- `Task(subagent_type="oh-my-claude:advisor", prompt="Analyze scope risks for this refactor")`
- `Task(subagent_type="oh-my-claude:validator", prompt="Run tests and verify the changes")`
- `Task(subagent_type="oh-my-claude:librarian", prompt="Summarize the auth module")`

### Built-in Agents (Claude Code)

Use Claude Code's native agents for common tasks:

| Agent | Job | When |
|-------|-----|------|
| **Explore** | FIND | Locate files, definitions (use thoroughness: quick/medium/very thorough) |
| **Plan** | PLAN | Complex tasks needing decomposition |
| **general-purpose** | BUILD | Implementation tasks |

Usage: `Task(subagent_type="Explore", prompt="Find auth files", thoroughness="medium")`

More examples:
- `Task(subagent_type="Plan", prompt="Design the migration strategy")`
- `Task(subagent_type="general-purpose", prompt="Implement the UserAuth class")`

## Task System (Coordination Layer)

The Task system is your **scratchpad for orchestrating multi-agent work**.

Use `TaskCreate`/`TaskUpdate`/`TaskList`/`TaskGet` to:
- Track progress on multi-step work
- Model dependencies between tasks
- Enable agent self-discovery via owner field
- Persist state across parallel delegations

Task tools are built-in to Claude Code (TaskCreate, TaskUpdate, TaskList, TaskGet).

### Quick Reference

```python
# Create with metadata
TaskCreate(subject="Find auth files", description="...", metadata={"priority": "high"})

# Dependencies: addBlockedBy (I wait) vs addBlocks (others wait for me)
TaskUpdate(taskId="2", addBlockedBy=["1"])

# Agent self-discovery via owner
TaskUpdate(taskId="1", owner="explore-1")
Task(subagent_type="Explore", prompt="Find auth-related files...")
```

### Task System: Tracking vs Execution

**Key distinction:** `Task()` = spawn agent NOW. `TaskCreate()` = track work for later.

```python
# TRACKING: Create items to track progress
TaskCreate(subject="Implement auth", description="Add JWT middleware to API routes")
TaskCreate(subject="Write tests", description="Unit tests for auth middleware")
TaskUpdate(taskId="2", addBlockedBy=["1"])  # Tests blocked by implementation

# EXECUTION: Spawn agents to do work (parallel when independent)
Task(subagent_type="general-purpose", prompt="Implement JWT middleware...")
Task(subagent_type="oh-my-claude:validator", prompt="Run auth tests...")

# UPDATE: Mark complete after verification
TaskUpdate(taskId="1", status="completed")
```

**Parallelization:** Launch multiple `Task()` calls in ONE message for parallel execution.

**Escape hatch:** Add `[NO-DELEGATE]` for tasks main agent handles directly.

## Orchestrator Protocol

You are the conductor. Agents play the music.

- **Explore finds** -> **Librarian reads** -> **Plan designs** -> **Critic reviews** -> **general-purpose implements** -> **Validator checks**
- Launch independent agents in parallel (one message, multiple Task calls)
- Sequential when dependent: wait for Explore paths before librarian reads them
- Declare intent before delegating: which agent, what task, expected output
- Trust but verify: spot-check critical claims from agents

| Situation | Do This |
|-----------|---------|
| Find files | Task(Explore) |
| Understand code | Task(librarian) |
| Git recon (tags, branches, commits) | Task(Explore) |
| Git analysis (diffs, changelogs) | Task(librarian) |
| Implement feature | Task(general-purpose) with spec |
| Verify work | Task(validator) |
| Gap analysis before planning | Task(advisor) |
| Complex task | Task(Plan) first |
| Review plan before execution | Task(critic) |

## Ultrawork Mode

Context protection is always on. Ultrawork adds execution intensity.

### Triggers

`ultrawork` or `ulw`

### Behaviors

| Aspect | Default | Ultrawork |
|--------|---------|-----------|
| Parallelization | When sensible | AGGRESSIVE |
| Task Tracking | When helpful | Recommended |
| Stopping | After milestones | NEVER until ALL complete |
| Questions | When unclear | NEVER - decide and document |
| Validation | When appropriate | REQUIRED before stopping |
| Completion | End normally | Must output `<promise>DONE</promise>` |

### External Memory (Notepad System)

For complex tasks, persist learnings to avoid losing context:

| Notepad | Purpose | When to Use |
|---------|---------|-------------|
| `.claude/notepads/learnings.md` | Patterns discovered, gotchas found | After discovering something non-obvious |
| `.claude/notepads/decisions.md` | Design decisions with rationale | After making architectural choices |
| `.claude/notepads/issues.md` | Problems encountered, blockers | When hitting blockers or finding bugs |
| `.claude/notepads/context.md` | Project-specific context | Key info for /prime recovery |

**Entry Format:**
```markdown
## [YYYY-MM-DD HH:MM] {title}
Source: {agent-name or "user"}

{content}
```

**Protocol:**
- Write to notepads BEFORE context fills up
- Read notepads when resuming work or after /prime
- Include notepad wisdom in agent delegations
- Agents should append findings, not overwrite

## Ultra Plan Mode

Auto-activates when entering native plan mode (no keyword needed).

### What It Does

| Phase | Behavior |
|-------|----------|
| Research | Mandatory Explore + librarian before designing |
| Analysis | Must consider 2+ approaches with tradeoffs |
| Review | Critic agent MUST approve before ExitPlanMode |
| Handoff | Plan path saved for execution session |

### Plan→Execution Transition

When you approve a plan (ExitPlanMode):
1. Claude Code preserves the plan content
2. "Accept and clear" prefixes your next session with "Implement the following plan:"
3. ultrawork_detector injects execution context based on this prefix

## Agent Teams

Coordinate multiple Claude Code sessions working together.

### When to Use Teams vs Subagents

| Use Subagents (default) | Use Agent Teams |
|------------------------|-----------------|
| Focused tasks where only results matter | Tasks needing inter-agent discussion |
| Sequential work | Independent modules in parallel |
| Same-file edits | Research/review from multiple angles |
| Dependency chains | Competing hypotheses or cross-layer work |

Subagents are cheaper and simpler. Use teams only when parallel collaboration adds real value.

### How It Works

Create teams with natural language - there is no tool-based API:
- "Create an agent team with 3 teammates to implement these modules in parallel"
- "Spawn a team: one for security review, one for performance, one for tests"

Key properties:
- Each teammate is a full Claude Code session with its own context window
- Teammates communicate via **shared task list** and **mailbox messaging**
- The lead session coordinates; teammates self-claim unblocked tasks
- Teammates load project CLAUDE.md but NOT the lead's conversation history
- Use **delegate mode** (Shift+Tab) to keep the lead coordination-only

### Rules

- Avoid assigning the same file to multiple teammates (causes overwrites)
- Include task-specific context in spawn prompts (teammates don't inherit history)
- Size tasks appropriately: self-contained units with clear deliverables
- Monitor progress and redirect approaches that aren't working
- Shut down teammates before cleaning up the team

See [official docs](https://code.claude.com/docs/en/agent-teams) for full reference.

## Other Keywords

| Keyword | Shortcut | Effect |
|---------|----------|--------|
| **ultraresearch** | `ulr` | Maximum online research — parallel WebSearch, cross-reference sources |
| **ultradebug** | `uld` | Systematic 7-step debugging with evidence |

## Commands

| Command | Purpose |
|---------|---------|
| `/prime` | Context recovery after /clear |

## Skills

| Skill | Description | Trigger |
|-------|-------------|---------|
| `git-commit-validator` | Commit message validation and conventional commit format enforcement | "commit", "ship it", "push this", "let's merge", finishing work |
| `pr-creation` | PR creation with conventional format, context gathering, draft by default | "create PR", "open PR", "ready for review", "push for PR" |
| `worktree` | Git worktree automation for isolated feature development | `/worktree create`, `/worktree list`, `/worktree remove` |
| `init-deep` | Initialize or migrate to nested CLAUDE.md structure for progressive disclosure | `/init-deep`, "deep init", "migrate claude.md", "nested claude" |
| `ralph-plan` | Structured PRD generation with interview, research, and approval workflow | `/ralph-plan <topic>`, "create prd", "generate prd", "plan this" |
| `ralph-loop-init` | Transform approved plans into executable ralph loop infrastructure | `/ralph-loop-init`, `/ralph-init`, "setup ralph loop" |
| `debugger` | Systematic debugging methodology for diagnosing failures and root cause analysis | 2+ failed fix attempts, "ultradebug", "uld", debugging in circles |

## Hooks (Automatic)

| Hook | Event | Matcher | Description |
|------|-------|---------|-------------|
| **Context Guardian** | SessionStart | `*` | Injects context protection rules at session start |
| **CLAUDE.md Health** | SessionStart | `*` | Checks CLAUDE.md health, warns about size/staleness issues |
| **OpenKanban Status** | SessionStart, PreToolUse, PermissionRequest, UserPromptSubmit, Stop | `*` | Writes agent status when in OpenKanban terminal (via OPENKANBAN_SESSION) |
| **Ultrawork Detector** | UserPromptSubmit | `*` | Detects ultrawork/ultradebug/ultraresearch keywords, adjusts intensity |
| **Context Protector** | PreToolUse | `Read` | Blocks large file reads (>100 lines), forces librarian delegation |
| **Danger Blocker** | PreToolUse | `Bash` | Blocks catastrophic commands (rm -rf /, fork bombs), warns on risky patterns |
| **Commit Quality Enforcer** | PreToolUse | `Bash` | Enforces commit message quality and conventional commit format |
| **TDD Enforcer** | PreToolUse | `Edit\|Write` | Enforces TDD by requiring test files before source edits (via OMC_TDD_MODE) |
| **Delegation Enforcer** | PreToolUse | `Edit\|Write` | Context guidance encouraging delegation to specialized agents |
| **Safe Permissions** | PermissionRequest | `Bash`, `Read\|Glob\|Grep` | Auto-approves safe commands (tests, linters, readonly git) |
| **Plan Execution Injector** | PostToolUse | `ExitPlanMode` | Injects execution context and agent teams guidance after plan approval |
| **Context Monitor** | PostToolUse | `*` | Warns at 70%+ context usage, critical at 85% |
| **Edit Error Recovery** | PostToolUse | `*` | Detects Edit tool failures, injects recovery guidance |
| **Agent Usage Reminder** | PostToolUse | `*` | Reminds to delegate to agents instead of using search tools directly |
| **Verification Reminder** | PostToolUse | `*` | Reminds to verify agent claims after Task completion |
| **Todo Enforcer** | Stop | `*` | Prevents stopping when todos are incomplete |
| **Notification Alert** | Stop, Notification | `*`, `permission_prompt\|idle_prompt` | Desktop notifications, opt-in via OMC_NOTIFICATIONS=1 |
| **PreCompact Context** | PreCompact | `*` | Preserves session state + semantic patterns before compaction |

## Configuration

Customize behavior via environment variables in your `settings.json`:

```json
{
  "env": {
    "OMC_LARGE_FILE_THRESHOLD": "100"
  }
}
```

| Variable | Default | Description |
|----------|---------|-------------|
| `OMC_LARGE_FILE_THRESHOLD` | `100` | Lines before Read is blocked |
| `OMC_ALLOW_LARGE_READS` | `0` | Set to `1` to disable large file blocking |
| `OMC_CONTEXT_WARN_PCT` | `70` | Context % to trigger warning |
| `OMC_CONTEXT_CRITICAL_PCT` | `85` | Context % for critical warning |
| `OMC_SAFE_PERMISSIONS` | `1` | Set to `0` to disable auto-approvals |
| `OMC_TDD_MODE` | `off` | TDD enforcement: `off`, `guided`, `enforced` |
| `OMC_DANGER_BLOCK` | `1` | Set to `0` to disable catastrophic command blocking |
| `OMC_NOTIFICATIONS` | `0` | Set to `1` to enable desktop notifications on Stop |
| `OMC_USE_TASK_SYSTEM` | `1` | Enable Task system checking for incomplete todos on Stop |
| `OMC_STOP_CHECK_GIT` | `0` | Set to `1` to check for uncommitted git changes on Stop |
| `OMC_STOP_CHECK_PLANS` | `1` | Check for incomplete plans on Stop |
| `OPENKANBAN_SESSION` | (unset) | OpenKanban terminal session ID for status integration |
| `HOOK_DEBUG` | (unset) | Set to `1` to enable hook debug logging to stderr |
