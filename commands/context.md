---
description: Show context-saving advice and best practices
allowed-tools:
  - Read
  - Glob
  - Grep
---

# /context - Context Awareness Command

Display context-saving best practices and current recommendations.

## Output

Provide a concise reminder of context-saving practices:

```
## Context Budget Reminder

### File Reading
- <100 lines: Read directly
- >100 lines: Delegate to oh-my-claude:librarian
- Unknown size: Delegate to be safe

### Search Strategy
- Use oh-my-claude:scout to find files and locate definitions
- Use Glob for file patterns (minimal context cost)
- Use Grep with files_with_matches first

### Subagent Delegation
Your context is for REASONING. Agents handle:
- Finding files → scout (haiku, fast)
- Large file reads → librarian returns smart summaries
- Complex planning → architect decomposes tasks
- Implementation → worker (one task each)
- Documentation → scribe writes docs
- Validation → validator runs checks

### Quick Reference
| Operation | Agent |
|-----------|-------|
| Find files | oh-my-claude:scout |
| Read large file | oh-my-claude:librarian |
| Plan complex task | oh-my-claude:architect |
| Implement feature | oh-my-claude:worker |
| Write documentation | oh-my-claude:scribe |
| Run tests/lint | oh-my-claude:validator |

### Pro Tips
- Launch multiple Tasks in ONE message = parallelism
- Subagents have isolated context windows
- When in doubt, delegate
```

## Notes
- This is a quick reference, not a comprehensive guide
- These practices are automatically suggested by the Context Guardian
- For maximum context efficiency, consider ultrawork mode
