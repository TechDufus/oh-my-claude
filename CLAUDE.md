# oh-my-claude

Maximum execution through intelligent automation. Just add a keyword to any prompt.

## Magic Keywords

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
You install LSP servers yourself. Ensure they're in your PATH.
```bash
./scripts/install-lsp.sh typescript  # bun > npm
./scripts/install-lsp.sh python      # uv > pipx > pip
./scripts/install-lsp.sh all --check # Check status
```

## Available Agents

Use via `Task(subagent_type="oh-my-claude:agent-name")`:

| Agent | Use For |
|-------|---------|
| `deep-explorer` | Thorough codebase exploration, architecture understanding |
| `parallel-implementer` | Focused single-task implementation |
| `validator` | Run all validation checks before completion |
| `context-summarizer` | Summarize large files without consuming main context |

## Commands

| Command | Description |
|---------|-------------|
| `/do <task>` | Smart task execution with automatic mode detection |
| `/commit` | Validated git commits (conventional format) |
| `/prime` | Context recovery after /clear |

## Hooks (Automatic)

| Hook | Purpose |
|------|---------|
| **SessionStart** | Auto-detect languages, check LSP servers |
| **UserPromptSubmit** | Detect keywords, inject execution directives |
| **Stop** | Prevent stopping with incomplete todos |
| **PreCompact** | Preserve context before compaction |

## Execution Philosophy

1. **PARALLELIZE** - Launch ALL independent Tasks in ONE message
2. **DELEGATE** - Files >100 lines go to subagents, not main context
3. **TRACK** - TodoWrite is mandatory for non-trivial work
4. **COMPLETE** - Cannot stop until all todos are done and validation passes
5. **NO QUESTIONS** - Make reasonable decisions and document them
