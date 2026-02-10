# oh-my-claude Development

Claude Code plugin providing ultrawork mode, context protection, and specialized agent workflows.

## Structure

```
├── .claude-plugin/marketplace.json    # Marketplace registry (version x2)
├── .github/workflows/validate-plugin.yml
├── PLUGIN-STRUCTURE.md               # Detailed architecture guide
├── tests/oh-my-claude/hooks/         # Hook unit tests
│   └── CLAUDE.md                     # Testing conventions
└── plugins/oh-my-claude/             # The actual plugin
    ├── .claude-plugin/plugin.json    # Plugin metadata (version x1)
    ├── agents/                       # 6 specialized agents
    │   └── CLAUDE.md                 # Agent authoring guide
    ├── hooks/                        # Python hooks (PEP 723)
    │   └── CLAUDE.md                 # Hook development patterns
    ├── commands/                     # /prime (auto-discovered)
    ├── skills/                       # Skills (in plugin.json)
    └── CLAUDE.md                     # Plugin runtime instructions
```

Nested CLAUDE.md files load automatically when working in those directories.

## Development Workflow

### Prerequisites
- `jq` - JSON validation
- Python 3.11+ - Hooks auto-install deps via `uv`

### Version Bumping (CRITICAL)

Claude Code caches plugins. **Any change requires bumping version in BOTH**:
1. `.claude-plugin/marketplace.json` - `metadata.version` AND `plugins[0].version`
2. `plugins/oh-my-claude/.claude-plugin/plugin.json`

Then: `/plugin update oh-my-claude` and start new session.

### Testing

Run hook unit tests:
```bash
cd tests/oh-my-claude/hooks
uv run --with pytest pytest . -v
```

### CI/CD

GitHub Actions validates: JSON syntax, version sync across files, no `../` paths, hook scripts exist and executable, shellcheck, ruff linting, pytest, skill directories exist.

## Hook Development

See `plugins/oh-my-claude/hooks/CLAUDE.md` for patterns and templates.
Key: PEP 723 inline deps, JSON stdin/stdout, `@hook_main` decorator.

## Rules

1. Plugins MUST be in `plugins/your-plugin/` subdirectory
2. NEVER use `../` paths - files outside source do not exist in cache
3. `hooks/hooks.json` auto-discovered - do NOT reference in plugin.json
4. Use `${CLAUDE_PLUGIN_ROOT}` for hook script paths
5. Skills must be explicitly listed in plugin.json

See `/PLUGIN-STRUCTURE.md` for complete guide.

## Site Sync

The `site/` landing page hardcodes plugin component names and counts. When you change any of these, update the site too:

| Change | Update |
|--------|--------|
| Add/remove agent | `site/src/components/AgentGrid.astro` |
| Add/remove skill | `site/src/content/copy.ts` stats |
| Add/remove hook | `site/src/content/copy.ts` stats |
| Change agent descriptions | `AgentGrid.astro` + relevant components |
| Change workflow/features | Relevant component in `site/src/components/` |

## Claude Code Update Sources

Official sources for researching Claude Code features and release notes.

### Primary (Most Stable)
| Source | URL |
|--------|-----|
| GitHub Releases | https://github.com/anthropics/claude-code/releases |
| CHANGELOG.md | https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md |

### Documentation
| Doc | URL |
|-----|-----|
| Claude Code Docs | https://docs.anthropic.com/en/docs/claude-code/overview |
| Hooks Reference | https://docs.anthropic.com/en/docs/claude-code/hooks |
| Agent SDK | https://docs.anthropic.com/en/docs/claude-code/sdk |

### Announcements
| Source | URL |
|--------|-----|
| Anthropic News | https://www.anthropic.com/news |
| Engineering Blog | https://www.anthropic.com/engineering |
| Discord | https://discord.gg/anthropic |
| @AnthropicAI | https://x.com/AnthropicAI |
