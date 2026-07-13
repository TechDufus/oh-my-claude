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
    ├── agents/                       # 7 specialized agents
    ├── docs/                         # Authoring guides and compatibility notes
    ├── hooks/                        # Python hooks (PEP 723)
    │   └── CLAUDE.md                 # Hook development patterns
    ├── commands/                     # /prime (auto-discovered)
    ├── skills/                       # Skills (in plugin.json)
    │   └── oh-my-claude-runtime/     # Runtime workflow guidance skill
    └── .mcp.json                     # Plugin MCP servers
```

Plugin-root `CLAUDE.md` is not loaded as runtime context by current Claude Code. Ship runtime behavior through hooks, skills, agents, commands, MCP, and plugin settings instead.

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

GitHub Actions validates: JSON syntax, version sync across files, no `../` paths, shellcheck, ruff linting, pytest, and skill directories. Pytest covers structured hook args and hook script existence.

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
| Claude Code Docs | https://code.claude.com/docs/en/overview |
| Hooks Reference | https://code.claude.com/docs/en/hooks |
| Plugins Reference | https://code.claude.com/docs/en/plugins-reference |
| Agent Teams | https://code.claude.com/docs/en/agent-teams |

### Announcements
| Source | URL |
|--------|-----|
| Anthropic News | https://www.anthropic.com/news |
| Engineering Blog | https://www.anthropic.com/engineering |
| Discord | https://discord.gg/anthropic |
| @AnthropicAI | https://x.com/AnthropicAI |
