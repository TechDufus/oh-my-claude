#!/usr/bin/env bash
# context-preserver.sh
# PreCompact hook: Injects reminder to preserve important context before compaction

set -euo pipefail

INPUT=$(cat)

# Extract session info
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId // .session_id // "unknown"')

# Inject context preservation reminder
CONTEXT="[PRE-COMPACTION NOTICE]

Context window is being compacted. To preserve important information:

## Auto-Preserved
- Todo list state (via TodoWrite)
- Recent file changes
- Current working directory state

## Recommended Actions Before Compaction
1. Ensure critical findings are in your todo list
2. Key decisions should be documented in code comments or commit messages
3. Complex state can be preserved via Task agents (they maintain separate context)

## Recovery After Compaction
- Use /prime command to restore context from project files
- Check TodoWrite for task continuity
- Review recent git commits for context

Compaction proceeding..."

CONTEXT_ESCAPED=$(printf '%s' "$CONTEXT" | jq -Rs .)
printf '{"hookSpecificOutput":{"hookEventName":"PreCompact","additionalContext":%s}}' "$CONTEXT_ESCAPED"
exit 0
