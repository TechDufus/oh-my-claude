# Agents

Specialized subagent definitions for Task tool delegation.

## Structure

Each agent is a markdown file with YAML frontmatter:

```markdown
---
model: inherit
permissionMode: default           # Optional: default, plan, acceptEdits, dontAsk, bypassPermissions
maxTokens: 4000                   # Optional: limit output length
description: "Role phrase. Capability summary."
tools:
  - ToolName
  - Bash(command:pattern)
hooks:                            # Optional: inject prompts at execution points
  Stop:
    - matcher: "*"
      hooks:
        - type: prompt
          prompt: "Final validation prompt"
---

# AgentName

{Tagline}

## Purpose
## When Main Claude Should Use {AgentName}
## Decision Table
## Input
## Output Format
## Rules
## What {AgentName} Does NOT Do
```

## Input Format Section

The `## Input` section should clearly specify what the agent expects to receive.

**Template:**
```markdown
## Input

You'll receive a specific {task type}. Examples:
- "{Example input 1}"
- "{Example input 2}"
- "{Example input 3}"

**Required context:**
- {What must be provided}
- {Paths, specs, constraints}

**Optional context:**
- {Nice-to-have information}
```

**Good input specifications:**
- Concrete examples showing expected format
- Clear distinction between required and optional context
- Explicit about what makes a task well-formed vs poorly-formed

**Example (from worker.md):**
```markdown
## Input

You'll receive a specific implementation task. Examples:
- "Create the UserAuth class in src/auth/UserAuth.ts with login, logout, and validateSession methods"
- "Fix the race condition in src/api/cache.ts by adding mutex locks"
- "Add input validation to all POST endpoints in src/routes/users.ts"
```

## Required Fields

| Field | Value | Notes |
|-------|-------|-------|
| `model` | `inherit` | Uses session's model |
| `description` | string | 1-2 sentences, quoted |
| `tools` | list | Permissions array |

## Model Inheritance (CRITICAL)

**NEVER pass `model: "haiku"` or `model: "sonnet"` when spawning agents.**

The Task tool's default description suggests "prefer haiku for quick tasks" - IGNORE THIS.
This plugin overrides that guidance. All oh-my-claude agents are defined with `model: inherit`
in their frontmatter, and the parent session should NEVER override this with a downgrade.

**Why this matters:**
- The user pays for their model tier (opus, sonnet, etc.) and expects that intelligence level
- Downgrading to haiku "to save tokens" defeats the purpose of using a premium tier
- Agent quality directly impacts task success - use maximum available intelligence

**When spawning agents:**
```yaml
# CORRECT - inherits parent model
Task(subagent_type="oh-my-claude:scout", prompt="...")

# CORRECT - explicit inherit
Task(subagent_type="oh-my-claude:worker", model="inherit", prompt="...")

# WRONG - NEVER DO THIS
Task(subagent_type="oh-my-claude:scout", model="haiku", prompt="...")
Task(subagent_type="oh-my-claude:validator", model="sonnet", prompt="...")
```

## Permission Modes

Control how the agent handles permission prompts via the `permissionMode` frontmatter field.

| Mode | Behavior | Use Case |
|------|----------|----------|
| `default` | Standard permission checking | General-purpose agents, balanced safety |
| `plan` | Read-only exploration mode | Scout, architect - information gathering only |
| `acceptEdits` | Auto-accept file edits | Worker, scribe - trusted implementation agents |
| `dontAsk` | Auto-deny permission prompts | Strict read-only agents, reviewers |
| `bypassPermissions` | Skip all permission checks | Dangerous - use only for fully trusted automation |

**Guidelines:**
- Read-only agents (scout, librarian, looker): use `plan` or `dontAsk`
- Implementation agents (worker): use `acceptEdits` for efficiency
- Review agents (critic, validator): use `plan` to prevent accidental changes
- Never use `bypassPermissions` unless explicitly required by workflow

```yaml
---
model: inherit
permissionMode: plan
description: "Read-only reconnaissance agent."
tools:
  - Read
  - Glob
  - Grep
---
```

## Hooks Patterns

Agents can define hooks to inject prompts or validation at specific execution points.

### Hook Types

| Hook | Trigger | Purpose |
|------|---------|---------|
| `PreToolUse` | Before tool execution | Validate inputs, inject guidance |
| `PostToolUse` | After tool execution | Process results, extract data |
| `Stop` | Agent completion | Enforce output format, final validation |

### PreToolUse Example

Inject verification before file modifications:

```yaml
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: prompt
          prompt: "Verify this change aligns with the task scope before proceeding."
```

### PostToolUse Example

Process tool output for specific patterns:

```yaml
hooks:
  PostToolUse:
    - matcher: "Bash"
      hooks:
        - type: prompt
          prompt: "Check for errors in command output. If errors found, document them."
```

### Stop Example

Enforce structured output format:

```yaml
hooks:
  Stop:
    - matcher: "*"
      hooks:
        - type: prompt
          prompt: |
            Before completing, ensure your response includes:
            1. A VERDICT line (PASS/FAIL/NEEDS_REVIEW)
            2. Summary of findings
            3. Specific file paths for any issues found
```

### Matcher Patterns

| Pattern | Matches |
|---------|---------|
| `*` | All tools |
| `Edit` | Edit tool only |
| `Edit\|Write` | Edit OR Write tools |
| `Bash` | Bash tool |

## Output Constraints

Control token limits via `maxTokens` in frontmatter for agents with specific output requirements.

| Agent Type | Recommended Limit | Rationale |
|------------|-------------------|-----------|
| Scout | 2000-4000 | Returns locations, not content |
| Librarian | 4000-8000 | Summaries should be concise |
| Critic | 4000-6000 | Focused feedback, not rewrites |
| Worker | No limit | Implementation varies widely |
| Validator | 4000-6000 | Results + brief explanation |

**When to use output constraints:**
- Agents that tend to over-explain or dump content
- Read-only agents returning locations instead of content
- Review agents that should give feedback, not implementations

```yaml
---
model: inherit
maxTokens: 4000
description: "Concise reconnaissance agent."
tools:
  - Glob
  - Grep
---
```

## Tool Permissions

**Unrestricted:**
```yaml
- Read
- Glob
- Grep
```

**Restricted Bash:**
```yaml
- Bash(git log:*)    # Only git log
- Bash(find:*)       # Only find
- Bash(wc:*)         # Only wc
```

**Full access:**
```yaml
- Bash              # Unrestricted shell
```

## Description Pattern

Format: `"{Adjective} {role} agent. {Action verbs} {capabilities}. {Limitations}."`

Examples:
- "Quick reconnaissance agent. Finds files, locates definitions. Returns locations, not content."
- "Focused implementation agent. Executes ONE specific task completely."

## Agent Tiers

| Tier | Agents | Bash Access |
|------|--------|-------------|
| Read-only | scout, librarian, looker | Restricted |
| Planning | architect, critic | Restricted |
| Coordination | orchestrator | Restricted |
| Execution | worker, validator | Full |
| Advisory | debugger, scribe | Varies |

**Note:** Orchestrator is coordination-only (opus-tier by default). It delegates to other agents but cannot implement directly - no Edit, Write, or Bash for builds.

## Adding New Agent

1. Create `agents/{name}.md`
2. Add YAML frontmatter (model, description, tools)
3. Document purpose, use cases, output format
4. Define explicit scope boundaries

## Task System Integration (Optional)

Agents can participate in Task-based orchestration workflows. This is optional - agents work fine standalone.

### When to Add Task Integration

Add Task integration to agents that:
- Run long-running discovery or implementation work
- Can be parallelized (multiple instances of same agent type)
- Benefit from self-discovery via owner field

Skip Task integration for advisory agents (architect, critic, debugger) that are called on-demand.

### Standard Pattern

Add this section to agent system prompts that should support Task workflows:

```markdown
## Task System Integration (Optional)

If assigned via owner field in a task workflow:
1. Call TaskList to find tasks where owner matches your role
2. TaskUpdate(status='in_progress') when starting
3. Perform your work
4. TaskUpdate(status='completed') when done
5. Check TaskList for newly unblocked tasks
```

### Category-Specific Templates

**Discovery agents (scout, librarian, looker):**
- Report findings (file paths, summaries, observations)
- May spawn follow-up tasks based on discoveries

**Implementation agents (worker, scribe):**
- Implement changes described in task
- Verify before marking complete

**Validation agents (validator):**
- Run checks/tests as described
- Report pass/fail with specific results

### Edge Case Handling

Instruct agents to handle:
- No tasks found: Report "No tasks assigned to {role}" and exit
- Task already in_progress: Skip (another agent may have claimed it)
- Task blocked: Skip and check for unblocked tasks

See `orchestrator.md` for full Task API reference and coordination patterns.

## Teammate Mode (Swarm Integration)

When agents operate as teammates in a Team/Swarm, they follow additional protocols.

### Agent → Teammate Mapping

oh-my-claude agents are designed to work as persistent teammates:

| Agent | Teammate Role | Swarm Behavior |
|-------|---------------|----------------|
| scout | Finder | Claims search/locate tasks |
| librarian | Reader | Claims file analysis tasks |
| architect | Planner | Claims design/decomposition tasks |
| worker | Implementer | Claims code change tasks |
| validator | Tester | Claims verification tasks |
| critic | Reviewer | Claims review/feedback tasks |
| scribe | Documenter | Claims documentation tasks |

### Swarm Worker Protocol

When spawned as a swarm worker, agents self-organize:

1. `TaskList()` → Find pending task with no owner
2. `TaskUpdate(taskId, owner="my-name", status="in_progress")`
3. Execute the work
4. `TaskUpdate(taskId, status="completed")`
5. `Teammate(operation="write", target="team-lead", value="findings...")`
6. Repeat until no tasks remain
7. Request shutdown when work exhausted

### Task Claiming Etiquette

- **Check owner first** - Never claim a task that has an owner
- **Check blockedBy** - Don't claim blocked tasks
- **Match specialization** - Scout takes search tasks, worker takes implementation
- **Report results** - Always write findings back to team lead

### Inbox Patterns

```
# After completing work, notify team lead
Teammate(operation="write", target="team-lead", value={
    "type": "task_complete",
    "taskId": "...",
    "summary": "...",
    "files_changed": [...]
})

# Request help from specialist
Teammate(operation="write", target="librarian-1", value={
    "type": "read_request",
    "files": ["path/to/large/file.py"]
})
```

## Anti-Patterns

- Don't give read-only agents write tools
- Don't omit "What Agent Does NOT Do" section
- Don't use vague descriptions
- Don't grant Bash without scoping when possible
