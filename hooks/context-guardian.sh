#!/bin/bash
# context-guardian.sh
# SessionStart hook: Injects always-on context protection rules for every session
# This is the "batteries included" baseline that makes Claude feel better automatically

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')

# Always inject context protection guidance
CONTEXT='[oh-my-claude: Context Guardian Active]

## Always-On Context Protection

These rules help preserve your context window for reasoning. Follow them by DEFAULT.

### File Reading Rules
- **<100 lines**: Read directly with Read tool
- **>100 lines**: Delegate to Task(subagent_type="oh-my-claude:librarian")
- **Unknown size**: Delegate to be safe - subagent context is free
- **Multiple files**: ALWAYS delegate to subagent

### Search & Exploration Rules
- **Finding files**: Use Task(subagent_type="oh-my-claude:scout")
- **Reading files**: Use Task(subagent_type="oh-my-claude:librarian")
- **Understanding architecture**: Scout to find, Librarian to read

### Your Agent Team
- `oh-my-claude:scout` - Find files, locate definitions, quick recon
- `oh-my-claude:librarian` - Smart file reading, summarizes large files
- `oh-my-claude:architect` - Plan complex tasks, decompose work
- `oh-my-claude:worker` - Focused single-task implementation
- `oh-my-claude:scribe` - Write documentation
- `oh-my-claude:validator` - Run tests, linters, checks

### When in Doubt
- Delegate to an agent (their context is isolated from yours)
- Scout finds → Librarian reads → You reason
- Use Glob/Grep for quick searches before delegating

TIP: Use /context command to check context-saving advice anytime.'

CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}' "$CONTEXT_ESCAPED"

exit 0
