# Contributing to oh-my-claude

Guidelines for contributing to the oh-my-claude Claude Code plugin.

## Getting Started

```
git clone https://github.com/TechDufus/oh-my-claude.git
cd oh-my-claude
```

### Project Structure

```
oh-my-claude/
├── .claude-plugin/marketplace.json    # Marketplace registry
├── plugins/oh-my-claude/              # The actual plugin
│   ├── .claude-plugin/plugin.json     # Plugin metadata
│   ├── agents/                        # Agent definitions (auto-discovered)
│   ├── hooks/                         # Python hooks
│   ├── commands/                      # Slash commands (auto-discovered)
│   └── skills/                        # Skills (must list in plugin.json)
└── PLUGIN-STRUCTURE.md                # Detailed architecture guide
```

See [PLUGIN-STRUCTURE.md](PLUGIN-STRUCTURE.md) for complete architecture details.

## Development Setup

- **uv** - Handles Python automatically
- **jq** - JSON validation (optional, for local testing)

## Making Changes

### Version Bumping (Required)

Claude Code caches plugins aggressively. **Every change requires bumping version in BOTH files:**

1. `.claude-plugin/marketplace.json` - Update `metadata.version` AND `plugins[0].version`
2. `plugins/oh-my-claude/.claude-plugin/plugin.json` - Update `version`

### Testing Locally

After making changes:

1. Bump the version in both files
2. Run `/plugin update oh-my-claude` in Claude Code
3. Start a new session to pick up changes

### Path Rules

- Never use `../` paths in plugin.json - files outside `source` directory are not cached
- Use `${CLAUDE_PLUGIN_ROOT}` for hook script paths in hooks.json
- hooks/hooks.json is auto-discovered - do NOT reference it in plugin.json

## Running Validation Locally

Before submitting a PR, validate your changes:

```bash
# JSON syntax validation
jq . .claude-plugin/marketplace.json
jq . plugins/oh-my-claude/.claude-plugin/plugin.json

# Shell script linting (if applicable)
shellcheck plugins/oh-my-claude/hooks/*.sh

# Python syntax check
python -m py_compile plugins/oh-my-claude/hooks/*.py

# Python linting
ruff check plugins/oh-my-claude/hooks/
```

## Real Runtime Plugin Load Test

Unit tests are necessary but not sufficient. Run a real Claude Code smoke test
to confirm the plugin loads from the local directory and hooks execute without
runtime errors.

```bash
LOG=$(mktemp /tmp/claude-omc-runtime.XXXXXX)

claude --setting-sources project \
  --plugin-dir "$(pwd)/plugins/oh-my-claude" \
  -p "ultrawork runtime smoke test: reply exactly OK" \
  -d --debug-file "$LOG" --output-format text
```

Quick verification:

```bash
rg -n "Loaded inline plugin from path|Loaded hooks from standard location for plugin oh-my-claude|Skill prompt: showing \"oh-my-claude|Hook UserPromptSubmit .* success|Hook .* failed|unhandled exception|Traceback" "$LOG"
```

Pass criteria:

- Prompt returns successfully (non-error exit code)
- Log contains plugin load lines (`Loaded inline plugin from path`, hooks loaded)
- Log contains at least one hook success line
- Log contains no hook failure/exception lines

Important note on MCP stderr:

- Lines like `MCP server ... Server stderr: ... running on stdio` may be logged
  as `[ERROR]` even when startup is healthy.
- Treat this as non-fatal if followed by `Successfully connected` and
  `Connection established` for the same MCP server.

## Pull Request Guidelines

1. **Create PRs as drafts** - Mark ready when CI passes
2. **Use conventional commit messages** - `feat:`, `fix:`, `refactor:`, `docs:`, etc.
3. **Ensure CI passes** - GitHub Actions validates JSON, versions, hooks, and linting
4. **Keep PRs focused** - One feature or fix per PR

## Code Style

### Python Hooks

- Use stdlib only in shared utilities (like `hook_utils.py`)
- Hooks use uv script format with PEP 723 inline dependencies:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["some-package"]  # if needed
# ///
```

- Read JSON from stdin, output JSON to stdout
- Keep hooks focused and minimal

### Agent Definitions

Follow the existing template structure:

```markdown
---
model: inherit
description: "Brief description"
tools:
  - ToolName
---

# Agent Name

## Purpose
## When Main Claude Should Use [Agent]
## Decision Table
## Input
## Output Format
## Rules
## What [Agent] Does NOT Do
```

### General

- Prefer concise implementations
- No unnecessary abstractions
- Code should be human-readable
