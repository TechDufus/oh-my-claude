# oh-my-claude

Maximum execution through intelligent automation. Batteries-included context protection with optional maximum effort modes.

## Two-Tier Behavior System

### Tier 1: Always-On (Every Session)

The **Context Guardian** activates automatically on every session start, providing baseline context protection:

- **File Reading Rules**: Guidance on when to delegate large files to subagents
- **Search Strategy**: Best practices for using Glob/Grep efficiently
- **Subagent Awareness**: Available agents and when to use them
- **Pattern Detection**: Automatic tips when prompts suggest context-heavy operations

**Detected Patterns** (triggers gentle reminders):
- Large file requests: "read the entire file", "show me all of", "full implementation"
- Multi-file operations: "all files", "across the codebase", "throughout the project"
- Exploration requests: "how does X work", "explain the codebase", "architecture"

### Tier 2: Maximum Effort (Magic Keywords)

Add a keyword to activate intensive execution modes:

| Keyword | Effect |
|---------|--------|
| **ultrawork** / **ulw** | Maximum parallel execution, zero tolerance for incomplete work |
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
- Project-aware validation

## Context Protection Rules

### File Size Thresholds
| Size | Action |
|------|--------|
| <100 lines | Read directly |
| >100 lines | Delegate to `oh-my-claude:deep-explorer` or `oh-my-claude:context-summarizer` |
| Unknown | Delegate to be safe (subagent context is free) |

### Search Strategy
| Operation | Tool/Agent |
|-----------|------------|
| Find files by pattern | Glob |
| Search file contents | Grep (files_with_matches mode first) |
| Explore codebase | Task(subagent_type="Explore") |
| Deep architecture analysis | Task(subagent_type="oh-my-claude:deep-explorer") |

## Available Agents

Use via `Task(subagent_type="oh-my-claude:agent-name")`:

| Agent | Model | Use For |
|-------|-------|---------|
| `deep-explorer` | haiku | Thorough codebase exploration, returns <800 token summaries |
| `context-summarizer` | haiku | Compress large files without consuming main context |
| `parallel-implementer` | sonnet | Focused single-task implementation |
| `validator` | haiku | Run linters, tests, validation checks |

## Commands

| Command | Description |
|---------|-------------|
| `/do <task>` | Smart task execution with automatic mode detection |
| `/prime` | Context recovery after /clear |
| `/context` | Show context-saving advice and best practices |

## Auto-Invoked Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `git-commit-validator` | Any commit request | Full commit workflow with validation |

The `git-commit-validator` skill auto-activates when you ask to commit. No `/commit` command needed - just say "commit this" or "make a commit".

## Hooks (Automatic)

| Hook | Purpose |
|------|---------|
| **SessionStart** | Context Guardian + LSP auto-detection |
| **UserPromptSubmit** | Keyword detection + pattern-based context tips |
| **Stop** | Prevent stopping with incomplete todos |
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

### Install Missing Servers
```bash
./scripts/install-lsp.sh typescript  # bun > npm
./scripts/install-lsp.sh python      # uv > pipx > pip
./scripts/install-lsp.sh all --check # Check status
```

## Execution Philosophy

1. **PROTECT CONTEXT** - Your context window is for reasoning, not storing raw code
2. **DELEGATE LIBERALLY** - Subagents have isolated context; use them freely
3. **PARALLELIZE** - Launch ALL independent Tasks in ONE message
4. **TRACK** - TodoWrite is mandatory for non-trivial work
5. **COMPLETE** - Cannot stop until all todos are done and validation passes
