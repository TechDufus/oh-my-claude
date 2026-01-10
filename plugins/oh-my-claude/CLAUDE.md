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
| `/lsp` | Show LSP server and linter installation status |

## Auto-Invoked Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `git-commit-validator` | Any commit request | Full commit workflow with validation |

## Hooks (Automatic)

| Hook | Purpose |
|------|---------|
| **SessionStart** | Context Guardian + LSP auto-detection |
| **UserPromptSubmit** | Keyword detection + pattern-based context tips |
| **PostToolUse** | LSP diagnostics after Edit/Write operations |
| **Stop** | Prevent stopping with incomplete todos + auto-validation + completion summary |
| **PreCompact** | Preserve context before compaction |

## LSP Support

Real-time code diagnostics via Claude Code's native LSP integration, with CLI linter fallbacks.

### Native LSP Servers

Claude Code manages LSP server lifecycle automatically. Install the server and it just works.

| Language | Server | Install |
|----------|--------|---------|
| TypeScript/JS | typescript-language-server | `npm i -g typescript-language-server typescript` |
| Python | pyright-langserver | `npm i -g pyright` |
| Bash | bash-language-server | `npm i -g bash-language-server` |
| Go | gopls | `go install golang.org/x/tools/gopls@latest` |
| Rust | rust-analyzer | `rustup component add rust-analyzer` |
| C/C++ | clangd | `brew install llvm` or package manager |
| Java | jdtls | Eclipse JDT Language Server |
| PHP | intelephense | `npm i -g intelephense` |
| Ruby | solargraph | `gem install solargraph` |
| Lua | lua-language-server | `brew install lua-language-server` |
| Zig | zls | `brew install zls` or from source |
| Swift | sourcekit-lsp | Included with Xcode |
| Kotlin | kotlin-language-server | `brew install kotlin-language-server` |
| C# | OmniSharp | `brew install omnisharp` |
| Terraform | terraform-ls | `brew install hashicorp/tap/terraform-ls` |
| YAML | yaml-language-server | `npm i -g yaml-language-server` |
| Dockerfile | docker-langserver | `npm i -g dockerfile-language-server-nodejs` |

### CLI Linter Fallbacks

If an LSP server isn't installed, the PostToolUse hook falls back to CLI linters:

| Extension | Linter | What it checks |
|-----------|--------|----------------|
| `.sh`, `.bash` | shellcheck | Shell script issues, portability |
| `.ts`, `.tsx` | tsc | TypeScript type errors |
| `.js`, `.jsx` | eslint | JavaScript lint errors |
| `.py` | ruff/pyright | Python type and lint errors |
| `.go` | go vet | Go-specific issues |
| `.rs` | cargo check | Rust compile errors |
| `.json` | jq | JSON syntax |
| `.yaml`, `.yml` | yamllint | YAML syntax and style |
| `.tf`, `.tfvars` | tflint | Terraform issues |
| `.lua` | luacheck | Lua lint errors |
| `.md` | markdownlint | Markdown style |
| `.swift` | swiftlint | Swift style and errors |
| `.kt`, `.kts` | ktlint | Kotlin style |
| `.cs` | dotnet build | C# compile errors |
| `.zig` | zig ast-check | Zig syntax errors |
| `Dockerfile` | hadolint | Dockerfile best practices |

If neither LSP nor linter is installed, diagnostics are silently skipped.

## Execution Philosophy

1. **PROTECT CONTEXT** - Your context window is for reasoning, not storing raw code
2. **DELEGATE LIBERALLY** - Agents have isolated context; use them freely
3. **PARALLELIZE** - Launch ALL independent Tasks in ONE message
4. **TRACK** - TodoWrite is mandatory for non-trivial work
5. **COMPLETE** - Cannot stop until all todos are done and validation passes

## Development Guidelines

### Version Bumping

Claude Code caches plugins by version. **Any change to cached content requires a version bump** in both `.claude-plugin/plugin.json` AND `.claude-plugin/marketplace.json`:

| Change Type | Requires Version Bump |
|-------------|----------------------|
| Agents (add/modify/remove) | YES |
| Hooks | YES |
| Commands | YES |
| Skills | YES |
| CLAUDE.md | NO (not cached) |
| README.md | NO |

Forgetting to bump the version means users won't see your changes until they manually clear their cache.

### Plugin Structure Gotchas

These will save you hours of debugging:

1. **Plugins MUST live in a subdirectory** - `marketplace.json` at repo root, plugin files in `plugins/your-plugin/`

2. **NEVER use `../` paths in plugin.json** - When installed, files are copied to cache. Paths escaping the plugin directory don't exist.
   ```json
   // WRONG: "hooks": "../hooks/hooks.json"
   // RIGHT: "hooks": "./hooks/hooks.json" (or omit - see #3)
   ```

3. **hooks/hooks.json is AUTO-DISCOVERED** - Don't reference it in plugin.json or you get "Duplicate hooks file detected"

4. **Use ${CLAUDE_PLUGIN_ROOT} in hooks.json** - For script paths inside hook definitions

5. **marketplace.json source** must point to the plugin subdirectory: `"source": "./plugins/oh-my-claude"`

See `/PLUGIN-STRUCTURE.md` in this repo for the full guide.
