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
- **>100 lines**: Delegate to Task(subagent_type="oh-my-claude:deep-explorer") or Task(subagent_type="oh-my-claude:context-summarizer")
- **Unknown size**: Check with `wc -l <file>` first, or delegate to be safe
- **Multiple files**: ALWAYS delegate to subagent - your context is for reasoning, not storing raw code

### Search & Exploration Rules
- **Codebase exploration**: Use Task(subagent_type="Explore") or Task(subagent_type="oh-my-claude:deep-explorer")
- **Finding files**: Use Glob tool (fast, minimal context)
- **Searching content**: Use Grep tool with files_with_matches mode first, then targeted reads
- **Understanding architecture**: ALWAYS delegate to deep-explorer agent

### Subagent Strategy
- Subagents have their own context windows - use them liberally
- Raw content stays in subagent context, you receive only distilled summaries
- Launch multiple independent Tasks in ONE message for parallelism
- Available agents:
  - `oh-my-claude:deep-explorer` - Thorough exploration, returns <800 token summaries
  - `oh-my-claude:context-summarizer` - Compress large files/results
  - `oh-my-claude:parallel-implementer` - Focused single-task implementation
  - `oh-my-claude:validator` - Run linters, tests, checks

### When in Doubt
- Delegate to a subagent (costs nothing, preserves your context)
- Use Glob/Grep before Read (find first, read targeted)
- Summarize results before storing in memory

TIP: Use /context command to check context-saving advice anytime.'

CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}' "$CONTEXT_ESCAPED"

exit 0
