# oh-my-claude

Maximum execution through intelligent automation. Batteries-included context protection with a specialized agent team.

## Architecture

Main Claude acts as the **orchestrator** - reasoning, planning, delegating to specialized agents, and synthesizing results. The hooks inject orchestrator behavior automatically.

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN CLAUDE                              │
│                  (Orchestrator)                             │
│                                                             │
│  Hooks inject behavior:                                     │
│  • Context Guardian → "delegate to your team"               │
│  • ultrawork mode → "parallelize, never stop"               │
│  • Pattern detection → "use the right agent"                │
│                                                             │
│  Job: REASON, PLAN, DELEGATE, SYNTHESIZE                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     THE TEAM                                │
│  scout, librarian, architect, worker, scribe, validator     │
└─────────────────────────────────────────────────────────────┘
```

## The Agent Team

Use via `Task(subagent_type="oh-my-claude:agent-name")`:

| Agent | Model | Role | When to Use |
|-------|-------|------|-------------|
| **scout** | haiku | FIND | "Where is X?", "Find files matching Y" |
| **librarian** | sonnet | READ | "Read file X", "Get the auth logic from Y" |
| **architect** | opus | PLAN | Complex tasks needing decomposition |
| **worker** | opus | IMPLEMENT | Focused single-task implementation |
| **scribe** | opus | DOCUMENT | Write docs, READMEs, comments |
| **validator** | haiku | CHECK | Run tests, linters, verify work |

### Agent Workflow

```
Scout finds → Librarian reads → Architect plans (if complex)
    → Workers implement in parallel → Scribe documents → Validator checks
```

### Agent Boundaries

| Agent | DOES | DOES NOT |
|-------|------|----------|
| **scout** | Find files, locate definitions | Read full content |
| **librarian** | Read smartly, summarize large files | Search for files |
| **architect** | Decompose tasks, plan parallelization | Implement code |
| **worker** | Implement ONE specific task completely | Decide what to build |
| **scribe** | Write documentation | Implement features |
| **validator** | Run checks, report results | Fix issues |

## Magic Keywords

| Keyword | Effect |
|---------|--------|
| **ultrawork** (+ natural variants like "ship it", "crush it", "finish it", etc.) | Maximum parallel execution, zero tolerance for incomplete work |
| **ultrathink** | Extended reasoning before action |
| **ultradebug** | Systematic debugging with evidence-based diagnosis |
| **analyze** / **investigate** | Deep analysis with parallel context gathering |
| **search for** / **find all** | Parallel search agents |

### ultrawork Example
```
ultrawork fix all the type errors
ultrawork implement user authentication with tests
```

Activates:
- ZERO TOLERANCE: No partial implementations, no "leaving as exercise"
- Parallel subagent execution (multiple Tasks in ONE message)
- Context-preserving file reads (delegate >100 lines to subagents)
- TodoWrite tracking (minimum 3 todos for non-trivial work)
- Relentless completion (cannot stop with incomplete todos)

## Context Protection Rules

### File Size Thresholds
| Size | Action |
|------|--------|
| <100 lines | Read directly |
| >100 lines | Delegate to `oh-my-claude:librarian` |
| Unknown | Delegate to be safe |

### Search Strategy
| Operation | Agent |
|-----------|-------|
| Find files by pattern | `oh-my-claude:scout` |
| Read file contents | `oh-my-claude:librarian` |
| Explore codebase | `oh-my-claude:scout` + `oh-my-claude:librarian` |
| Plan complex task | `oh-my-claude:architect` |

## Commands

| Command | Description |
|---------|-------------|
| `/prime` | Context recovery after /clear |

## Auto-Invoked Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `git-commit-validator` | Any commit request | Full commit workflow with validation |

## Hooks (Automatic)

| Hook | Purpose |
|------|---------|
| **SessionStart** | Context Guardian + LSP auto-detection |
| **UserPromptSubmit** | Keyword detection + pattern-based context tips |
| **Stop** | Prevent stopping with incomplete todos + auto-validation + completion summary |
| **PreCompact** | Preserve context before compaction |

## LSP Support (Auto-Detected)

On session start, oh-my-claude automatically:
1. Detects project languages from file extensions
2. Checks if corresponding LSP servers are installed
3. Reports status (does NOT auto-install)

### Supported Languages
TypeScript, Python, Go, Rust, Java, C/C++, PHP, Ruby, Kotlin, Swift

### LSP Tools Available (when enabled)
- `goToDefinition` - Jump to symbol definition
- `findReferences` - Find all usages
- `hover` - Get type info and docs
- `documentSymbol` - File outline
- `getDiagnostics` - Errors and warnings

### Enable LSP
```bash
export ENABLE_LSP_TOOL=1  # Add to shell profile
```

## Execution Philosophy

1. **PROTECT CONTEXT** - Your context window is for reasoning, not storing raw code
2. **DELEGATE LIBERALLY** - Agents have isolated context; use them freely
3. **PARALLELIZE** - Launch ALL independent Tasks in ONE message
4. **TRACK** - TodoWrite is mandatory for non-trivial work
5. **COMPLETE** - Cannot stop until all todos are done and validation passes

## Development Guidelines

### Version Bumping

Claude Code caches plugins by version. **Any change to cached content requires a version bump** in `.claude-plugin/plugin.json`:

| Change Type | Requires Version Bump |
|-------------|----------------------|
| Agents (add/modify/remove) | YES |
| Hooks | YES |
| Commands | YES |
| Skills | YES |
| CLAUDE.md | NO (not cached) |
| README.md | NO |

Forgetting to bump the version means users won't see your changes until they manually clear their cache.
