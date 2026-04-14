# Agents

Specialized subagent definitions for Claude Code agent delegation.

## Structure

Each agent is a markdown file with YAML frontmatter:

```markdown
---
model: inherit
description: "Role phrase. Capability summary."
disallowedTools: Write, Edit      # Optional: enforce read-only behavior
maxTurns: 10                      # Optional: cap long-running delegation
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

**Example (from general-purpose delegation):**
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

## Model Inheritance (CRITICAL)

**NEVER pass `model: "haiku"` or `model: "sonnet"` when spawning agents.**

The Agent tool's default description suggests "prefer haiku for quick tasks" - IGNORE THIS.
This plugin overrides that guidance. All oh-my-claude agents are defined with `model: inherit`
in their frontmatter, and the parent session should NEVER override this with a downgrade.

**Why this matters:**
- The user pays for their model tier (opus, sonnet, etc.) and expects that intelligence level
- Downgrading to haiku "to save tokens" defeats the purpose of using a premium tier
- Agent quality directly impacts task success - use maximum available intelligence

**When spawning agents:**
```yaml
# CORRECT - inherits parent model
Agent(subagent_type="oh-my-claude:critic", prompt="...")

# CORRECT - explicit inherit
Agent(subagent_type="oh-my-claude:librarian", model="inherit", prompt="...")

# WRONG - NEVER DO THIS
Agent(subagent_type="oh-my-claude:critic", model="haiku", prompt="...")
Agent(subagent_type="oh-my-claude:validator", model="sonnet", prompt="...")
```

Claude Code renamed `Task(...)` to `Agent(...)` in `v2.1.63`. Use `Agent(...)` in new examples. `Task(...)` remains an alias on modern builds.

## Plugin Agent Limits

Plugin-provided agents are not full project agents. Current Claude Code ignores some frontmatter fields when an agent comes from a plugin.

Ignored on plugin agents:
- `permissionMode`
- agent-local `hooks`
- agent-local `mcpServers`

Use supported fields instead:
- `tools` / `disallowedTools` to control capabilities
- `model` to pin or inherit model choice
- `memory`, `skills`, `maxTurns`, `color` when needed

If you need `permissionMode` or agent-local hooks, copy the agent into `.claude/agents/` or `~/.claude/agents/`.

```yaml
---
model: inherit
description: "Read-only reconnaissance agent."
disallowedTools: Write, Edit
---
```

## Turn Limits

Control long-running delegation with `maxTurns` in frontmatter.

| Agent Type | Recommended Limit | Rationale |
|------------|-------------------|-----------|
| Explore | 4-8 | Search, summarize, stop |
| Librarian | 6-12 | Read several files, return concise summary |
| Critic | 4-8 | Focused feedback, not rewrites |
| Validator | 6-12 | Run checks, report verdict |
| Advisor | 4-8 | Surface gaps without sprawling |

**When to use turn limits:**
- Agents that can spiral on wide searches
- Validators that might keep retrying failing commands
- Review agents that should return findings, not over-investigate

```yaml
---
model: inherit
maxTurns: 8
description: "Concise reconnaissance agent."
---
```

## Tool Permissions

**Default: Omit `tools` entirely.** Agents inherit the parent session's tool access,
which is governed by Claude Code's built-in permission system (settings.json,
permission modes, PermissionRequest hooks). This avoids a redundant restriction
layer that causes unnecessary permission prompts.

For plugin agents, prefer `disallowedTools: Write, Edit` for read-only roles.
Only add explicit `tools` if you need to narrow capabilities further than that.

## Description Pattern

Format: `"{Adjective} {role} agent. {Action verbs} {capabilities}. {Limitations}."`

Examples:
- "Quick reconnaissance agent. Finds files, locates definitions. Returns locations, not content."
- "Focused implementation agent. Executes ONE specific task completely."

## Agent Tiers

| Tier | Agents | Runtime guardrail |
|------|--------|------------------|
| Read-only | librarian | `disallowedTools: Write, Edit` |
| Review | critic, code-reviewer, advisor, risk-assessor, security-auditor | `disallowedTools: Write, Edit` |
| Execution | validator | `disallowedTools: Write, Edit` plus prompt-level "report only" rules |

**Note:** Use Claude Code's built-in agents for common tasks:
- **Explore** - File/definition discovery
- **Plan** - Complex task decomposition
- **general-purpose** - Implementation tasks

## Team Context

Agents work the same whether spawned by a team lead, a teammate, or a solo session. When native agent teams are enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`):

- **Team leads** should use specialist agents (librarian, advisor, risk-assessor, critic, validator) for focused analysis/verification, and teammates for implementation work
- **Teammates** can also spawn specialist agents as subagents for their own analysis needs
- Agent identity and tool constraints are unchanged regardless of caller

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

Skip Task integration for advisory agents (advisor, risk-assessor, critic) that are called on-demand.

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

**Read agents (librarian):**
- Report findings (summaries, extracted content, observations)
- May spawn follow-up tasks based on discoveries

**Review agents (advisor, risk-assessor, critic):**
- Provide analysis and feedback
- Do not make changes directly

**Validation agents (validator):**
- Run checks/tests as described
- Report pass/fail with specific results

### Edge Case Handling

Instruct agents to handle:
- No tasks found: Report "No tasks assigned to {role}" and exit
- Task already in_progress: Skip (another agent may have claimed it)
- Task blocked: Skip and check for unblocked tasks

Claude Code has built-in Task API documentation. Focus on small, validateable tasks.

## Anti-Patterns

- Don't add unsupported plugin-only expectations like `permissionMode` or agent-local `hooks`
- Don't omit "What Agent Does NOT Do" section
- Don't use vague descriptions
- Don't duplicate Claude Code's permission system with sprawling tool allowlists unless you need them
