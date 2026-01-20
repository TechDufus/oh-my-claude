# Agents

Specialized subagent definitions for Task tool delegation.

## Structure

Each agent is a markdown file with YAML frontmatter:

```markdown
---
model: inherit
description: "Role phrase. Capability summary."
tools:
  - ToolName
  - Bash(command:pattern)
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

## Required Fields

| Field | Value | Notes |
|-------|-------|-------|
| `model` | `inherit` | Uses session's model |
| `description` | string | 1-2 sentences, quoted |
| `tools` | list | Permissions array |

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
| Execution | worker, validator | Full |
| Advisory | debugger, scribe | Varies |

## Adding New Agent

1. Create `agents/{name}.md`
2. Add YAML frontmatter (model, description, tools)
3. Document purpose, use cases, output format
4. Define explicit scope boundaries

## Anti-Patterns

- Don't give read-only agents write tools
- Don't omit "What Agent Does NOT Do" section
- Don't use vague descriptions
- Don't grant Bash without scoping when possible
