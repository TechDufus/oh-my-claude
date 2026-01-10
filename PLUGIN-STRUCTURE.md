# Claude Code Plugin Structure Guide

Hard-won lessons from building this plugin. Read this before you waste hours debugging.

## The Correct Structure

```
your-marketplace-repo/
├── .claude-plugin/
│   └── marketplace.json        # ONLY the marketplace catalog
├── plugins/
│   └── your-plugin/            # Plugin lives in subdirectory
│       ├── .claude-plugin/
│       │   └── plugin.json     # Plugin metadata
│       ├── hooks/
│       │   └── hooks.json      # AUTO-DISCOVERED (don't reference in plugin.json!)
│       ├── agents/
│       ├── commands/
│       ├── skills/
│       └── CLAUDE.md
└── README.md
```

## Critical Rules

### 1. Plugins MUST be in a subdirectory

**Wrong:**
```
repo-root/
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json          # NO! Don't put plugin.json here
├── hooks/
└── agents/
```

**Right:**
```
repo-root/
├── .claude-plugin/
│   └── marketplace.json     # Marketplace only
└── plugins/your-plugin/
    ├── .claude-plugin/
    │   └── plugin.json      # Plugin metadata here
    ├── hooks/
    └── agents/
```

### 2. NEVER use `../` paths in plugin.json

When Claude Code installs a plugin, it copies files from the `source` path. Paths referencing outside that directory **don't exist in the cache**.

**Wrong:**
```json
{
  "hooks": "../hooks/hooks.json",
  "skills": ["../skills/my-skill/SKILL.md"]
}
```

**Right:**
```json
{
  "skills": ["./skills/my-skill/SKILL.md"]
}
```

### 3. hooks/hooks.json is AUTO-DISCOVERED

Do NOT reference it in plugin.json. Claude Code automatically loads `hooks/hooks.json` if it exists.

**Wrong:**
```json
{
  "hooks": "./hooks/hooks.json"
}
```

**Right:**
```json
{
  // No hooks field needed - auto-discovered
}
```

If you reference it explicitly, you get: `Duplicate hooks file detected`

### 4. marketplace.json source must point to plugin directory

```json
{
  "plugins": [
    {
      "name": "your-plugin",
      "source": "./plugins/your-plugin",
      "version": "1.0.0"
    }
  ]
}
```

### 5. Use ${CLAUDE_PLUGIN_ROOT} in hooks.json

For hook script paths, use the environment variable:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/hooks/my-hook.sh"
      }]
    }]
  }
}
```

## What Gets Auto-Discovered

| Directory/File | Auto-Discovered? | Notes |
|----------------|------------------|-------|
| `hooks/hooks.json` | Yes | Don't reference in plugin.json |
| `agents/*.md` | Yes | Agent definitions |
| `commands/*.md` | Yes | Slash commands |
| `skills/*/SKILL.md` | No | Must list in plugin.json |
| `.mcp.json` | Yes | MCP server config |
| `CLAUDE.md` | Yes | Instructions for Claude |

## Debugging Tips

1. **Plugin not showing in `/plugin`?** Check for JSON syntax errors in plugin.json
2. **Hooks not loading?** Verify ${CLAUDE_PLUGIN_ROOT} paths are correct
3. **"Duplicate hooks file" error?** Remove `hooks` field from plugin.json
4. **Files missing after install?** Your `source` path is wrong or you used `../`

## Version Bumping

Always bump version in BOTH files when making changes:
- `.claude-plugin/marketplace.json` (two places: metadata.version and plugins[].version)
- `plugins/your-plugin/.claude-plugin/plugin.json`

Then run `/plugin update your-plugin` to pick up changes.
