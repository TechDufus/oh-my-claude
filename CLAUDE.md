# oh-my-claude Development

Claude Code plugin providing ultrawork mode, context protection, and specialized agent workflows.

## Structure

```
├── .claude-plugin/marketplace.json    # Marketplace registry (version x2)
├── .github/workflows/validate-plugin.yml
├── PLUGIN-STRUCTURE.md               # Detailed architecture guide
└── plugins/oh-my-claude/             # The actual plugin
    ├── .claude-plugin/plugin.json    # Plugin metadata (version x1)
    ├── agents/                       # 6 agents (auto-discovered)
    ├── hooks/                        # Python hooks with inline uv deps
    ├── commands/                     # /prime (auto-discovered)
    ├── skills/                       # git-commit-validator (in plugin.json)
    └── CLAUDE.md                     # Plugin instructions for Claude
```

## Development Workflow

### Prerequisites
- `jq` - JSON validation
- Python 3.11+ - Hooks auto-install deps via `uv`

### Version Bumping (CRITICAL)

Claude Code caches plugins. **Any change requires bumping version in BOTH**:
1. `.claude-plugin/marketplace.json` - `metadata.version` AND `plugins[0].version`
2. `plugins/oh-my-claude/.claude-plugin/plugin.json`

Then: `/plugin update oh-my-claude` and start new session.

### CI/CD

GitHub Actions validates: JSON syntax, version sync across files, no `../` paths, hook scripts exist and executable, shellcheck, skill files exist.

## Hook Development

Python with inline uv dependencies (PEP 723):
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["some-package"]
# ///
```
Read JSON from stdin, output JSON to stdout.

## Rules

1. Plugins MUST be in `plugins/your-plugin/` subdirectory
2. NEVER use `../` paths - files outside source do not exist in cache
3. `hooks/hooks.json` auto-discovered - do NOT reference in plugin.json
4. Use `${CLAUDE_PLUGIN_ROOT}` for hook script paths
5. Skills must be explicitly listed in plugin.json

See `/PLUGIN-STRUCTURE.md` for complete guide.
