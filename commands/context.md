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
- >100 lines: Delegate to oh-my-claude:deep-explorer or oh-my-claude:context-summarizer
- Unknown size: Delegate to be safe

### Search Strategy
- Use Glob for file patterns (minimal context cost)
- Use Grep with files_with_matches first
- Delegate exploration to Task(subagent_type="Explore")

### Subagent Delegation
Your context is for REASONING. Subagents handle:
- Large file reads → deep-explorer returns <800 token summaries
- Codebase exploration → Explore agent
- Multi-file operations → parallel-implementer (one task each)
- Validation → validator agent

### Quick Reference
| Operation | Tool/Agent |
|-----------|------------|
| Find files | Glob |
| Search content | Grep (files_with_matches) |
| Read small file | Read |
| Read large file | Task(deep-explorer) |
| Explore codebase | Task(Explore) |
| Implement feature | Task(parallel-implementer) |
| Run tests/lint | Task(validator) |

### Pro Tips
- Launch multiple Tasks in ONE message = parallelism
- Subagents have isolated context windows
- When in doubt, delegate
```

## Notes
- This is a quick reference, not a comprehensive guide
- These practices are automatically suggested by the Context Guardian
- For maximum context efficiency, consider ultrawork mode
