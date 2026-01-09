<img width="1328" height="611" alt="oh-my-claude_hero" src="https://github.com/user-attachments/assets/ca862678-da89-45c3-8385-fb45415c1b6e" />

# oh-my-claude

Add **ultrawork** to any prompt. That's it.

```
ultrawork fix all the type errors
ultrawork refactor the entire auth system
ultrawork implement user analytics with tests
```

## Install

### From GitHub (recommended)
```bash
# In Claude Code:
/plugin marketplace add TechDufus/oh-my-claude
/plugin install oh-my-claude@oh-my-claude
```

### From Local Directory
```bash
git clone https://github.com/TechDufus/oh-my-claude /tmp/oh-my-claude
# In Claude Code:
/plugin marketplace add /tmp/oh-my-claude
/plugin install oh-my-claude@oh-my-claude
```

Restart Claude Code. Done.

## Update

```bash
# Refresh marketplace
claude plugin marketplace update oh-my-claude

# Update to latest version
claude plugin update oh-my-claude@oh-my-claude
```

Restart Claude Code to apply changes.

## Magic Keywords

| Keyword | What Happens |
|---------|--------------|
| **ultrawork** / **ulw** | Maximum parallel execution, won't stop until done |
| **ultrathink** | Extended reasoning before any action |
| **ultradebug** | Systematic debugging with evidence-based diagnosis |
| **analyze** | Deep analysis with parallel context gathering |
| **search for** | Multiple parallel search agents |

### Alternate Triggers
These also activate ultrawork mode:
- `just work`, `don't stop`, `until done`
- `keep going`, `finish everything`, `relentless`, `get it done`

## What Happens in Ultrawork Mode

1. **PARALLELIZE** - Launches independent tasks simultaneously (multiple in ONE message)
2. **DELEGATE** - Large files (>100 lines) go to subagents, not your context
3. **TRACK** - Creates todos immediately, updates them in real-time
4. **WON'T STOP** - Cannot stop until ALL todos complete AND validation passes
5. **VALIDATE** - Auto-detects project type and runs appropriate tests/lints
6. **ZERO TOLERANCE** - No partial implementations, no "simplified versions"

## LSP Support (Auto-Detected)

On session start, oh-my-claude **detects** your project languages and **checks** for LSP servers. It does NOT auto-install anything - you install the servers you need.

### What You Get
- **Auto-detection** of TypeScript, Python, Go, Rust, Java, C/C++, PHP, Ruby, Kotlin, Swift
- **Status report** showing which LSP servers are available vs missing
- **Installation guidance** with commands for missing servers

### Enable LSP Tools
```bash
# Add to your shell profile (.zshrc, .bashrc, etc.)
export ENABLE_LSP_TOOL=1
```

### Install LSP Servers (Your Responsibility)

LSP servers must be installed and **in your PATH**. Use the helper script or install manually:

```bash
# Helper script (auto-detects best package manager)
./scripts/install-lsp.sh typescript  # bun > npm > yarn > pnpm
./scripts/install-lsp.sh python      # uv > pipx > pip
./scripts/install-lsp.sh go          # go install
./scripts/install-lsp.sh rust        # rustup > brew
./scripts/install-lsp.sh all --check # Check what's installed

# Or install manually - just ensure it's in PATH:
bun install -g typescript-language-server typescript
uv tool install pyright
go install golang.org/x/tools/gopls@latest
rustup component add rust-analyzer
gem install solargraph
```

**Important:** After installing, verify the server is in your PATH:
```bash
which typescript-language-server  # Should return a path
which gopls                       # Should return a path
```

### LSP Tools Available
When enabled, Claude Code gets IDE-level code intelligence:
- `goToDefinition` - Jump to where a symbol is defined
- `findReferences` - Find all usages of a symbol
- `hover` - Get type info and documentation
- `documentSymbol` - Get file outline
- `getDiagnostics` - Get errors and warnings

## Included Components

### Hooks (Automatic)
| Hook | Purpose |
|------|---------|
| **lsp-auto-config** | Detect languages, check/report LSP status |
| **ultrawork-detector** | Detect keywords, inject execution directives |
| **todo-continuation-enforcer** | Prevent stopping with incomplete todos |
| **context-preserver** | Preserve state before compaction |

### Agent Team
Use via `Task(subagent_type="oh-my-claude:agent-name")`:

| Agent | Model | Purpose |
|-------|-------|---------|
| `scout` | haiku | Find files, locate definitions |
| `librarian` | sonnet | Smart file reading, summarize large files |
| `architect` | opus | Task decomposition and planning |
| `worker` | opus | Focused single-task implementation |
| `scribe` | opus | Documentation writing |
| `validator` | haiku | Run tests, linters, type checks |

### Commands
| Command | Description |
|---------|-------------|
| `/do <task>` | Smart task router with mode detection |
| `/commit` | Validated conventional commits |
| `/prime` | Context recovery after /clear |

## Philosophy

> Your context is for reasoning, not storage.

- Delegate bulk reads to subagents
- Launch parallel tasks in single messages
- Track everything with TodoWrite
- Never stop until done
- No partial solutions, no asking for permission

## Uninstall

```bash
/plugin uninstall oh-my-claude@oh-my-claude
```

## Credits

Inspired by [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode).

## Sources

LSP implementation informed by:
- [Claude Code native LSP support](https://news.ycombinator.com/item?id=46355165)
- [boostvolt/claude-code-lsps](https://github.com/boostvolt/claude-code-lsps)
- [Piebald-AI/claude-code-lsps](https://github.com/Piebald-AI/claude-code-lsps)
- [ktnyt/cclsp](https://github.com/ktnyt/cclsp)
